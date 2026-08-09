from __future__ import annotations

"""Official/free E4A specialized-data providers.

Every provider in this module either returns a validated primary-source record
or an explicit unavailable state.  No related instrument, guessed rate, or
licensed dataset is substituted.
"""

import csv
import html
import io
import json
import re
import tempfile
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.news_engine import safe_utils
from src.news_engine.macro_provider import BaseMacroProvider


NSE_PARTICIPANT_BASE = "https://archives.nseindia.com/content/nsccl"
RBI_CURRENT_RATES_URL = "https://www.rbi.org.in/"
NIFTY_RECONSTITUTION_URL = "https://www.niftyindices.com/resources/index-rebalancing-schedule"


def safe_url_fetch(*args: Any, **kwargs: Any):
    return safe_utils.safe_url_fetch(*args, **kwargs)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _atomic_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _load_json(path: Path) -> Dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


PARTICIPANT_COLUMNS: Tuple[Tuple[str, str, str], ...] = (
    ("INDEX_FUTURES", "Future Index Long", "Future Index Short"),
    ("STOCK_FUTURES", "Future Stock Long", "Future Stock Short"),
    ("INDEX_CALLS", "Option Index Call Long", "Option Index Call Short"),
    ("INDEX_PUTS", "Option Index Put Long", "Option Index Put Short"),
    ("STOCK_CALLS", "Option Stock Call Long", "Option Stock Call Short"),
    ("STOCK_PUTS", "Option Stock Put Long", "Option Stock Put Short"),
)


class NseParticipantDerivativesProvider(BaseMacroProvider):
    """NSE Clearing participant-wise OI and volume reports."""

    CACHE_PATH = Path(".cache/nse_participant_derivatives.json")

    def __init__(
        self,
        provider_id: str = "nse_participant_derivatives_provider",
        refresh_interval: float = 1800.0,
        cache_path: Optional[Path] = None,
        fixture_reports: Optional[Dict[str, bytes | str]] = None,
        today: Optional[date] = None,
    ) -> None:
        super().__init__(provider_id, refresh_interval=refresh_interval)
        self.cache_path = cache_path or self.CACHE_PATH
        self.fixture_reports = fixture_reports
        self.today = today
        self.dataset_health: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def report_url(dataset_type: str, trade_date: date) -> str:
        suffix = "oi" if dataset_type == "OPEN_INTEREST" else "vol"
        return f"{NSE_PARTICIPANT_BASE}/fao_participant_{suffix}_{trade_date:%d%m%Y}.csv"

    @staticmethod
    def parse_report(raw: bytes | str, dataset_type: str, source_url: str, retrieved_at: str) -> Dict[str, Any]:
        text = raw.decode("utf-8-sig") if isinstance(raw, bytes) else str(raw)
        lines = [line for line in text.splitlines() if line.strip()]
        title = lines[0] if lines else ""
        date_match = re.search(r"as on\s+([A-Za-z]{3}\s+\d{1,2},\s+\d{4})", title, re.IGNORECASE)
        if not date_match:
            raise ValueError("participant report date is missing")
        trade_date = datetime.strptime(date_match.group(1), "%b %d, %Y").date().isoformat()
        header_index = next((i for i, line in enumerate(lines) if line.lstrip().startswith("Client Type,")), -1)
        if header_index < 0:
            raise ValueError("participant report header is missing")
        reader = csv.DictReader(io.StringIO("\n".join(lines[header_index:])), skipinitialspace=True)
        records: List[Dict[str, Any]] = []
        participant_names = {"CLIENT": "CLIENT", "DII": "DII", "FII": "FII", "PRO": "PRO"}
        for row in reader:
            normalized = {str(key or "").strip(): str(value or "").strip() for key, value in row.items()}
            participant = participant_names.get(normalized.get("Client Type", "").upper())
            if not participant:
                continue
            for category, long_column, short_column in PARTICIPANT_COLUMNS:
                try:
                    long_contracts = int(normalized[long_column].replace(",", ""))
                    short_contracts = int(normalized[short_column].replace(",", ""))
                except (KeyError, TypeError, ValueError) as exc:
                    raise ValueError(f"invalid participant {dataset_type} contract count") from exc
                records.append({
                    "dataset_type": dataset_type,
                    "trade_date": trade_date,
                    "participant_type": participant,
                    "instrument_category": category,
                    "long_contracts": long_contracts,
                    "short_contracts": short_contracts,
                    "net_position": long_contracts - short_contracts,
                    "unit": "CONTRACTS",
                    "source": "NSE Clearing Limited",
                    "source_name": "NSE Clearing Participant-wise Derivatives Reports",
                    "source_authority": "PRIMARY",
                    "source_url": source_url,
                    "retrieved_at": retrieved_at,
                    "record_timestamp": trade_date,
                    "freshness": "LAST_VALID_SESSION",
                    "status": "AVAILABLE",
                    "observation_mode": "LATEST_AVAILABLE_TRADING_SESSION",
                })
        if len(records) != 24:
            raise ValueError(f"expected 24 participant records, received {len(records)}")
        return {"dataset_type": dataset_type, "trade_date": trade_date, "records": records}

    def _download_latest(self, dataset_type: str) -> Dict[str, Any]:
        retrieved_at = _utc_now()
        if self.fixture_reports is not None:
            raw = self.fixture_reports.get(dataset_type)
            if raw is None:
                raise ValueError(f"fixture missing {dataset_type}")
            return self.parse_report(raw, dataset_type, f"fixture://{dataset_type.lower()}", retrieved_at)
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; AIR-ArdhaMind/1.0)",
            "Accept": "text/csv,*/*",
            "Referer": "https://www.nseindia.com/all-reports-derivatives",
        }
        anchor = self.today or datetime.now(timezone.utc).date()
        failures: List[str] = []
        for offset in range(0, 11):
            candidate = anchor - timedelta(days=offset)
            if candidate.weekday() >= 5:
                continue
            url = self.report_url(dataset_type, candidate)
            try:
                raw, response_headers, status = safe_url_fetch(url, headers=headers, timeout=20.0, max_size=128 * 1024)
                content_type = str(response_headers.get("Content-Type") or "").lower()
                if status != 200 or ("csv" not in content_type and not raw.lstrip().startswith(b'""Participant')):
                    raise ValueError(f"unusable HTTP response {status} {content_type}")
                parsed = self.parse_report(raw, dataset_type, url, retrieved_at)
                if parsed["trade_date"] != candidate.isoformat():
                    raise ValueError("participant report date does not match requested archive date")
                return parsed
            except Exception as exc:
                failures.append(str(exc))
        raise ConnectionError(f"no usable {dataset_type} report in lookback window: {failures[-1] if failures else 'unknown'}")

    @staticmethod
    def summarize_positioning(records: List[Dict[str, Any]]) -> Dict[str, Any]:
        summaries: Dict[str, Any] = {}
        for row in records:
            if row.get("dataset_type") != "OPEN_INTEREST":
                continue
            participant = str(row.get("participant_type"))
            category = str(row.get("instrument_category"))
            net = int(row.get("net_position") or 0)
            if category.endswith("FUTURES"):
                posture = "NET_LONG" if net > 0 else "NET_SHORT" if net < 0 else "BALANCED"
            else:
                posture = "LONG_EXCEEDS_SHORT" if net > 0 else "SHORT_EXCEEDS_LONG" if net < 0 else "BALANCED"
            summaries[f"{participant}_{category}"] = {
                "participant_type": participant,
                "instrument_category": category,
                "long_contracts": row.get("long_contracts"),
                "short_contracts": row.get("short_contracts"),
                "net_position": net,
                "positioning": posture,
                "reasoning": f"Official long contracts {row.get('long_contracts')}; short contracts {row.get('short_contracts')}; net {net} contracts.",
                "trade_date": row.get("trade_date"),
                "unit": "CONTRACTS",
            }
        return summaries

    def fetch_snapshot(self) -> Dict[str, Any]:
        persisted = _load_json(self.cache_path)
        datasets: Dict[str, Any] = {}
        usable_records: List[Dict[str, Any]] = []
        for dataset_type in ("OPEN_INTEREST", "VOLUME"):
            attempt = _utc_now()
            try:
                result = self._download_latest(dataset_type)
                datasets[dataset_type] = result
                self.dataset_health[dataset_type] = {
                    "status": "READY", "record_count": len(result["records"]),
                    "latest_session": result["trade_date"], "last_success": attempt,
                    "last_attempt": attempt, "freshness": "LAST_VALID_SESSION", "failure_reason": None,
                }
            except Exception as exc:
                cached = (persisted.get("datasets") or {}).get(dataset_type)
                if cached and len(cached.get("records") or []) == 24:
                    result = cached
                    for row in result["records"]:
                        row.update({"freshness": "LAST_VALID_SESSION", "status": "DEGRADED", "cache_restored": True})
                    datasets[dataset_type] = result
                    self.dataset_health[dataset_type] = {
                        "status": "DEGRADED", "record_count": len(result["records"]),
                        "latest_session": result.get("trade_date"), "last_success": persisted.get("saved_at"),
                        "last_attempt": attempt, "freshness": "LAST_VALID_SESSION", "failure_reason": str(exc)[:240],
                    }
                else:
                    self.dataset_health[dataset_type] = {
                        "status": "UNAVAILABLE", "record_count": 0, "latest_session": None,
                        "last_success": None, "last_attempt": attempt, "freshness": "UNAVAILABLE",
                        "failure_reason": str(exc)[:240],
                    }
                    continue
            usable_records.extend(datasets[dataset_type]["records"])
        if datasets:
            payload = {"saved_at": _utc_now(), "datasets": datasets}
            _atomic_json(self.cache_path, payload)
            self.cached_raw_data = list(usable_records)
            self.item_count = len(usable_records)
            self.last_attempted_fetch = _utc_now()
            self.last_successful_fetch = self.last_attempted_fetch
            self.status = "ready" if all(h["status"] == "READY" for h in self.dataset_health.values()) else "degraded"
            self.operational_error_reason = None if self.status == "ready" else "partial_provider_failure"
        else:
            self.record_failure(ConnectionError("participant OI and volume reports unavailable"))
        return {
            "status": "AVAILABLE" if usable_records else "UNAVAILABLE",
            "open_interest": datasets.get("OPEN_INTEREST"),
            "volume": datasets.get("VOLUME"),
            "records": usable_records,
            "positioning": self.summarize_positioning(usable_records),
            "dataset_health": dict(self.dataset_health),
            "source": "NSE Clearing Limited",
            "source_authority": "PRIMARY",
        }

    def fetch_raw_data(self) -> List[Dict[str, Any]]:
        return list(self.fetch_snapshot().get("records") or [])


class RbiRiskFreeRateProvider(BaseMacroProvider):
    """Official RBI 91-day T-bill cut-off yield for INR option IV."""

    CACHE_PATH = Path(".cache/rbi_risk_free_rate.json")
    _instance: Optional["RbiRiskFreeRateProvider"] = None

    def __init__(self, cache_path: Optional[Path] = None, fixture_html: Optional[str] = None) -> None:
        super().__init__("rbi_risk_free_rate_provider", refresh_interval=21600.0)
        self.cache_path = cache_path or self.CACHE_PATH
        self.fixture_html = fixture_html

    @staticmethod
    def _is_fresh(record: Dict[str, Any], today: Optional[date] = None) -> bool:
        try:
            observed = date.fromisoformat(str(record.get("observation_date")))
            age_days = ((today or datetime.now(timezone.utc).date()) - observed).days
            return 0 <= age_days <= 14
        except (TypeError, ValueError):
            return False

    @classmethod
    def get_instance(cls) -> "RbiRiskFreeRateProvider":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @staticmethod
    def parse_current_rates(raw_html: str, retrieved_at: str) -> Dict[str, Any]:
        plain = html.unescape(re.sub(r"(?is)<[^>]+>", " ", raw_html))
        plain = re.sub(r"\s+", " ", plain)
        section_match = re.search(r"Government Securities Market(.{0,2500})Capital Market", plain, re.IGNORECASE)
        section = section_match.group(1) if section_match else plain
        rate_match = re.search(r"91\s*day\s*T-?bills?\s*:\s*([0-9]+(?:\.[0-9]+)?)%", section, re.IGNORECASE)
        date_matches = re.findall(r"(?:#\s*)?as on\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})", section, re.IGNORECASE)
        if not rate_match or not date_matches:
            raise ValueError("RBI 91-day T-bill rate or observation date is missing")
        observation_date = datetime.strptime(date_matches[-1], "%B %d, %Y").date().isoformat()
        rate_pct = float(rate_match.group(1))
        if not 0.0 < rate_pct < 25.0:
            raise ValueError("RBI 91-day T-bill yield is outside validation bounds")
        return {
            "status": "AVAILABLE", "rate": rate_pct / 100.0, "rate_pct": rate_pct,
            "tenor": "91_DAY_TBILL", "source": "Reserve Bank of India",
            "source_authority": "PRIMARY", "source_url": RBI_CURRENT_RATES_URL,
            "observation_date": observation_date, "retrieved_at": retrieved_at,
            "freshness": "LAST_VALID_OFFICIAL_OBSERVATION", "observation_mode": "LATEST_RBI_PUBLISHED_RATE",
        }

    def fetch_rate(self) -> Dict[str, Any]:
        retrieved_at = _utc_now()
        try:
            if self.fixture_html is not None:
                raw_html = self.fixture_html
            else:
                raw, _, status = safe_url_fetch(
                    RBI_CURRENT_RATES_URL,
                    headers={"User-Agent": "Mozilla/5.0 (compatible; AIR-ArdhaMind/1.0)", "Accept": "text/html,*/*"},
                    timeout=20.0, max_size=512 * 1024,
                )
                if status != 200:
                    raise ValueError(f"RBI current rates returned HTTP {status}")
                raw_html = raw.decode("utf-8", errors="replace")
            record = self.parse_current_rates(raw_html, retrieved_at)
            _atomic_json(self.cache_path, record)
            self.record_success([record])
            return record
        except Exception as exc:
            cached = _load_json(self.cache_path)
            if cached.get("status") == "AVAILABLE" and cached.get("rate") and self._is_fresh(cached):
                cached.update({"status": "DEGRADED", "cache_restored": True, "last_attempt": retrieved_at,
                               "failure_reason": str(exc)[:240], "freshness": "LAST_VALID_OFFICIAL_OBSERVATION"})
                self.status = "degraded"
                self.cached_raw_data = [cached]
                self.item_count = 1
                self.last_attempted_fetch = retrieved_at
                return cached
            self.record_failure(exc)
            return {"status": "UNAVAILABLE", "rate": None, "rate_pct": None, "tenor": "91_DAY_TBILL",
                    "source": "Reserve Bank of India", "source_url": RBI_CURRENT_RATES_URL,
                    "observation_date": None, "retrieved_at": retrieved_at, "freshness": "UNAVAILABLE",
                    "failure_reason": str(exc)[:240]}

    @classmethod
    def load_validated_rate(cls) -> Dict[str, Any]:
        cached = _load_json(cls.CACHE_PATH)
        if (cached.get("rate") and cached.get("source") == "Reserve Bank of India"
                and cls._is_fresh(cached)):
            return cached
        return cls.get_instance().fetch_rate()

    def fetch_raw_data(self) -> List[Dict[str, Any]]:
        record = self.fetch_rate()
        return [record] if record.get("status") in {"AVAILABLE", "DEGRADED"} else []


class NiftyReconstitutionProvider(BaseMacroProvider):
    CACHE_PATH = Path(".cache/nifty_reconstitution.json")

    def __init__(self, cache_path: Optional[Path] = None, fixture_html: Optional[str] = None) -> None:
        super().__init__("nifty_reconstitution_provider", refresh_interval=86400.0)
        self.cache_path = cache_path or self.CACHE_PATH
        self.fixture_html = fixture_html

    @staticmethod
    def parse_schedule(raw_html: str, retrieved_at: str) -> Dict[str, Any]:
        plain = html.unescape(re.sub(r"(?is)<[^>]+>", " ", raw_html))
        plain = re.sub(r"\s+", " ", plain)
        match = re.search(r"Nifty\s*50.{0,500}?Semi-annually\s*[-–]\s*Last working day of March and September", plain, re.IGNORECASE)
        if not match:
            raise ValueError("official NIFTY 50 reconstitution schedule not found")
        return {
            "status": "AVAILABLE", "index_name": "NIFTY 50", "review_frequency": "SEMI_ANNUAL",
            "review_schedule": "Last working day of March and September",
            "effective_change_date": "LAST_WORKING_DAY_OF_MARCH_AND_SEPTEMBER",
            "announcement_date": None, "source": "NSE Indices Limited",
            "source_authority": "PRIMARY", "source_url": NIFTY_RECONSTITUTION_URL,
            "retrieved_at": retrieved_at,
        }

    def fetch_metadata(self) -> Dict[str, Any]:
        retrieved_at = _utc_now()
        try:
            if self.fixture_html is not None:
                raw_html = self.fixture_html
            else:
                raw, _, status = safe_url_fetch(
                    NIFTY_RECONSTITUTION_URL,
                    headers={"User-Agent": "Mozilla/5.0 (compatible; AIR-ArdhaMind/1.0)", "Accept": "text/html,*/*"},
                    timeout=20.0, max_size=512 * 1024,
                )
                if status != 200:
                    raise ValueError(f"Nifty Indices schedule returned HTTP {status}")
                raw_html = raw.decode("utf-8", errors="replace")
            record = self.parse_schedule(raw_html, retrieved_at)
            _atomic_json(self.cache_path, record)
            self.record_success([record])
            return record
        except Exception as exc:
            cached = _load_json(self.cache_path)
            if cached.get("status") == "AVAILABLE":
                cached.update({"status": "DEGRADED", "cache_restored": True, "failure_reason": str(exc)[:240]})
                self.status = "degraded"
                self.cached_raw_data = [cached]
                self.item_count = 1
                return cached
            self.record_failure(exc)
            return {"status": "UNAVAILABLE", "index_name": "NIFTY 50", "source": "NSE Indices Limited",
                    "source_url": NIFTY_RECONSTITUTION_URL, "retrieved_at": retrieved_at,
                    "failure_reason": str(exc)[:240]}

    def fetch_raw_data(self) -> List[Dict[str, Any]]:
        record = self.fetch_metadata()
        return [record] if record.get("status") in {"AVAILABLE", "DEGRADED"} else []


class GiftNiftyProvider(BaseMacroProvider):
    """Official NSE IX near-month GIFT NIFTY futures snapshot provider."""

    SNAPSHOT_URL = "https://www.nseix.com/api/market-rate?type=derivatives"
    STATUS_URL = "https://www.nseix.com/api/derivatives-market-status"
    CACHE_PATH = Path(".cache/gift_nifty_snapshot.json")

    def __init__(self, cache_path: Optional[Path] = None, fixture_payload: Optional[Dict[str, Any]] = None,
                 fixture_status: Optional[Dict[str, Any]] = None) -> None:
        super().__init__("gift_nifty_provider", refresh_interval=60.0)
        self.cache_path = cache_path or self.CACHE_PATH
        self.fixture_payload = fixture_payload
        self.fixture_status = fixture_status

    @staticmethod
    def parse_snapshot(payload: Dict[str, Any], status_payload: Dict[str, Any], retrieved_at: str) -> Dict[str, Any]:
        rows = payload.get("data") or []
        unique: Dict[Tuple[str, str, int], Dict[str, Any]] = {}
        for row in rows:
            if str(row.get("INSTRUMENTTYPE") or "").upper() != "FUTIDX" or str(row.get("SYMBOL") or "").upper() != "NIFTY":
                continue
            try:
                token = int(row.get("TOKEN_NMBR"))
                expiry = datetime.strptime(str(row.get("EXPIRYDATE")), "%d-%b-%Y").date()
                observed = datetime.strptime(str(row.get("TIMESTMP")), "%d-%b-%Y %H:%M:%S").replace(
                    tzinfo=timezone(timedelta(hours=5, minutes=30)))
                price = float(row.get("LASTPRICE"))
                change = float(row.get("DAYCHANGE_1", row.get("DAYCHANGE")))
            except (TypeError, ValueError) as exc:
                raise ValueError("invalid official NSE IX GIFT NIFTY futures row") from exc
            if price <= 0:
                continue
            unique[(expiry.isoformat(), observed.isoformat(), token)] = {
                "expiry": expiry, "observed": observed, "price": price, "change": change,
                "token": token, "volume": int(row.get("CONTRACTSTRADED") or 0),
            }
        if not unique:
            raise ValueError("official NSE IX response contained no usable GIFT NIFTY future")
        active = sorted(unique.values(), key=lambda row: (row["expiry"], -row["volume"]))[0]
        reference = active["price"] - active["change"]
        if reference <= 0:
            raise ValueError("official NSE IX GIFT NIFTY reference close is invalid")
        status_text = str(status_payload.get("marketstatus") or "UNKNOWN")
        session = "MARKET_CLOSED" if "CLOSED" in status_text.upper() else "MARKET_OPEN" if "OPEN" in status_text.upper() else "UNKNOWN"
        return {
            "symbol": "GIFT_NIFTY", "name": "GIFT Nifty Near-Month Future", "category": "GLOBAL_INDEX",
            "price": active["price"], "change": active["change"],
            "change_pct": round(active["change"] / reference * 100.0, 4), "currency": "USD",
            "source_name": "NSE International Exchange", "source_attribution": "Official NSE IX public market snapshot",
            "source_url": GiftNiftyProvider.SNAPSHOT_URL, "source_authority": "PRIMARY",
            "source_symbol": "NSEIX:NIFTY", "provider_symbol": "NSEIX:NIFTY",
            "exchange": "NSEIX", "exchange_timezone": "Asia/Kolkata", "instrument_type": "INDEX_FUTURE",
            "contract_expiry": active["expiry"].isoformat(), "instrument_token": active["token"],
            "observation_timestamp": active["observed"].isoformat(), "published_at": active["observed"].isoformat(),
            "retrieved_at": retrieved_at, "reference_value": reference, "reference_type": "PREVIOUS_CLOSE",
            "reference_timestamp": "", "source_session": session, "source_session_detail": status_text,
            "observation_mode": "OFFICIAL_NEAR_MONTH_FUTURE_SNAPSHOT", "volume_contracts": active["volume"],
        }

    def fetch_raw_data(self) -> List[Dict[str, Any]]:
        retrieved_at = _utc_now()
        try:
            if self.fixture_payload is not None:
                payload, status_payload = self.fixture_payload, self.fixture_status or {}
            else:
                raw, _, status = safe_url_fetch(self.SNAPSHOT_URL, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"}, timeout=20.0, max_size=256 * 1024)
                if status != 200:
                    raise ConnectionError(f"official NSE IX snapshot returned HTTP {status}")
                status_raw, _, status_code = safe_url_fetch(self.STATUS_URL, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"}, timeout=20.0, max_size=32 * 1024)
                payload = json.loads(raw.decode("utf-8"))
                status_payload = json.loads(status_raw.decode("utf-8")) if status_code == 200 else {}
            record = self.parse_snapshot(payload, status_payload, retrieved_at)
            _atomic_json(self.cache_path, record)
            self.record_success([record])
            return [record]
        except Exception as exc:
            cached = _load_json(self.cache_path)
            if cached.get("source_symbol") == "NSEIX:NIFTY" and cached.get("observation_timestamp"):
                cached.update({"cache_restored": True, "latest_fetch_failure": str(exc)[:240]})
                self.cached_raw_data = [cached]
                self.item_count = 1
                self.record_failure(exc)
                return [cached]
            self.record_failure(exc)
            return []


class NiftyWeightsProvider:
    """Disabled future official/licensed weights provider contract."""

    provider_name = "nifty_weights_provider"

    @staticmethod
    def get_health() -> Dict[str, Any]:
        return {
            "provider_name": "nifty_weights_provider", "status": "LICENSE_REQUIRED",
            "item_count": 0, "last_successful_fetch": None, "last_attempted_fetch": None,
            "freshness": "UNAVAILABLE", "failure_reason": "OFFICIAL_NIFTY_WEIGHTS_LICENSE_REQUIRED",
            "is_enabled": False,
        }
