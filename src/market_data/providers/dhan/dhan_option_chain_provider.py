from __future__ import annotations

from datetime import date, datetime, timezone
import logging
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from src.market_data.interfaces.option_chain_provider import IOptionChainProvider
from src.market_data.models.canonical_instrument import CanonicalInstrument
from src.market_data.models.canonical_option_chain import (
    CanonicalOptionChainSnapshot,
    CanonicalOptionLeg,
    CanonicalOptionStrike,
)
from src.market_data.models.quality_enums import OptionType
from src.market_data.services.instrument_master_service import (
    InstrumentMasterService,
    normalize_strike,
)

logger = logging.getLogger(__name__)


class DhanOptionChainProvider(IOptionChainProvider):
    """
    DhanHQ Option Chain provider adapter.
    Enforces documented endpoint-aware 3-second rate throttling per (underlying, expiry).
    Exposes throttle metrics and next allowed execution times.
    """

    DEFAULT_ENDPOINT_THROTTLE_SECONDS: float = 3.0

    def __init__(
        self,
        client_id: Optional[str] = None,
        access_token: Optional[str] = None,
        instrument_master: Optional[InstrumentMasterService] = None,
        transport_fetcher: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
        min_request_interval_seconds: float = DEFAULT_ENDPOINT_THROTTLE_SECONDS,
    ) -> None:
        self.client_id = client_id or ""
        self._access_token = access_token or ""
        self.instrument_master = instrument_master or InstrumentMasterService()
        self.transport_fetcher = transport_fetcher
        self.min_request_interval_seconds = min_request_interval_seconds

        self._lock = threading.RLock()
        # Track request timestamps per endpoint key: (underlying, expiry) -> last_time
        self._endpoint_last_request_at: Dict[Tuple[str, str], float] = {}
        self.total_requests_count: int = 0
        self.throttled_requests_count: int = 0

    def provider_name(self) -> str:
        return "DHAN"

    def get_last_request_at(self, underlying: str, expiry: str) -> Optional[float]:
        """Returns the epoch timestamp of the last request for the underlying/expiry."""
        with self._lock:
            return self._endpoint_last_request_at.get((underlying.upper().strip(), expiry.strip()))

    def get_next_allowed_at(self, underlying: str, expiry: str) -> float:
        """Returns the monotonic timestamp when the next request for this underlying/expiry is allowed."""
        with self._lock:
            last_t = self._endpoint_last_request_at.get((underlying.upper().strip(), expiry.strip()), 0.0)
            return last_t + self.min_request_interval_seconds

    def _throttle_endpoint(self, underlying: str, expiry: str) -> None:
        """Enforces documented 3-second throttle per (underlying, expiry)."""
        key = (underlying.upper().strip(), expiry.strip())
        with self._lock:
            now = time.perf_counter()
            last_t = self._endpoint_last_request_at.get(key, 0.0)
            elapsed = now - last_t

            if elapsed < self.min_request_interval_seconds:
                sleep_time = self.min_request_interval_seconds - elapsed
                self.throttled_requests_count += 1
                time.sleep(sleep_time)

            self._endpoint_last_request_at[key] = time.perf_counter()
            self.total_requests_count += 1

    def get_available_expiries(self, underlying: CanonicalInstrument) -> Sequence[str]:
        """
        Retrieves sorted option expiry dates for the underlying from InstrumentMaster or provider.
        """
        sym = underlying.symbol or underlying.canonical_id.split(":")[-1]
        master_expiries = self.instrument_master.get_available_expiries(sym)
        if master_expiries:
            return master_expiries

        if self.transport_fetcher is not None:
            self._throttle_endpoint(sym, "EXPIRIES")
            res = self.transport_fetcher({"action": "expiries", "underlying": sym})
            if "data" in res and isinstance(res["data"], list):
                return sorted(list(set(str(e)[:10] for e in res["data"])))

        return []

    def fetch_option_chain(
        self,
        underlying: CanonicalInstrument,
        expiry: str,
    ) -> CanonicalOptionChainSnapshot:
        """
        Fetches option chain snapshot from Dhan with endpoint-aware 3-second rate throttling.
        """
        clean_exp = expiry.strip()[:10]
        sym = underlying.symbol or underlying.canonical_id.split(":")[-1]

        if self.transport_fetcher is not None:
            self._throttle_endpoint(sym, clean_exp)
            payload = self.transport_fetcher({
                "UnderlyingScrip": underlying.provider_ids.get("DHAN", "13"),
                "UnderlyingSeg": "NSE_IDX",
                "Expiry": clean_exp,
            })
            return self.normalize_option_chain_payload(underlying, clean_exp, payload)

        return CanonicalOptionChainSnapshot(
            underlying_instrument_id=underlying.canonical_id,
            underlying_price=24500.0,
            expiry=clean_exp,
            session_date=date.today(),
            captured_at=datetime.now(timezone.utc),
            provider="DHAN",
            strikes=[],
        )

    def normalize_option_chain_payload(
        self,
        underlying: CanonicalInstrument,
        expiry: str,
        payload: Dict[str, Any],
    ) -> CanonicalOptionChainSnapshot:
        """
        Normalizes Dhan option chain response structure into CanonicalOptionChainSnapshot.
        """
        data_block = payload.get("data", payload)
        und_price = float(data_block.get("last_price", data_block.get("spot_price", 24500.0)))
        oc_dict = data_block.get("oc", data_block.get("strikes", {}))

        strikes_list: List[CanonicalOptionStrike] = []
        now_dt = datetime.now(timezone.utc)
        sym = underlying.symbol or underlying.canonical_id.split(":")[-1]

        for strike_str, strike_data in oc_dict.items():
            try:
                strike_val = float(strike_str)
                strike_str_norm = normalize_strike(strike_val)
            except (ValueError, TypeError):
                continue

            call_leg: Optional[CanonicalOptionLeg] = None
            put_leg: Optional[CanonicalOptionLeg] = None

            ce_data = strike_data.get("ce", strike_data.get("CE"))
            if ce_data and isinstance(ce_data, dict):
                ce_price = float(ce_data["last_price"]) if ce_data.get("last_price") and float(ce_data["last_price"]) > 0 else None
                ce_cid = f"OPT:NFO:{sym}:{expiry}:{strike_str_norm}:CE"
                call_leg = CanonicalOptionLeg(
                    canonical_instrument_id=ce_cid,
                    strike=strike_val,
                    option_type=OptionType.CE,
                    last_price=ce_price,
                    oi=int(ce_data["oi"]) if ce_data.get("oi") is not None and int(ce_data["oi"]) >= 0 else None,
                    volume=int(ce_data["volume"]) if ce_data.get("volume") is not None and int(ce_data["volume"]) >= 0 else None,
                    iv=float(ce_data["iv"]) if ce_data.get("iv") is not None else None,
                    delta=float(ce_data["delta"]) if ce_data.get("delta") is not None else None,
                    gamma=float(ce_data["gamma"]) if ce_data.get("gamma") is not None else None,
                    theta=float(ce_data["theta"]) if ce_data.get("theta") is not None else None,
                    vega=float(ce_data["vega"]) if ce_data.get("vega") is not None else None,
                    bid=float(ce_data["bid"]) if ce_data.get("bid") and float(ce_data["bid"]) > 0 else None,
                    ask=float(ce_data["ask"]) if ce_data.get("ask") and float(ce_data["ask"]) > 0 else None,
                )

            pe_data = strike_data.get("pe", strike_data.get("PE"))
            if pe_data and isinstance(pe_data, dict):
                pe_price = float(pe_data["last_price"]) if pe_data.get("last_price") and float(pe_data["last_price"]) > 0 else None
                pe_cid = f"OPT:NFO:{sym}:{expiry}:{strike_str_norm}:PE"
                put_leg = CanonicalOptionLeg(
                    canonical_instrument_id=pe_cid,
                    strike=strike_val,
                    option_type=OptionType.PE,
                    last_price=pe_price,
                    oi=int(pe_data["oi"]) if pe_data.get("oi") is not None and int(pe_data["oi"]) >= 0 else None,
                    volume=int(pe_data["volume"]) if pe_data.get("volume") is not None and int(pe_data["volume"]) >= 0 else None,
                    iv=float(pe_data["iv"]) if pe_data.get("iv") is not None else None,
                    delta=float(pe_data["delta"]) if pe_data.get("delta") is not None else None,
                    gamma=float(pe_data["gamma"]) if pe_data.get("gamma") is not None else None,
                    theta=float(pe_data["theta"]) if pe_data.get("theta") is not None else None,
                    vega=float(pe_data["vega"]) if pe_data.get("vega") is not None else None,
                    bid=float(pe_data["bid"]) if pe_data.get("bid") and float(pe_data["bid"]) > 0 else None,
                    ask=float(pe_data["ask"]) if pe_data.get("ask") and float(pe_data["ask"]) > 0 else None,
                )

            if call_leg or put_leg:
                strikes_list.append(CanonicalOptionStrike(
                    strike=strike_val,
                    call=call_leg,
                    put=put_leg,
                ))

        strikes_list.sort(key=lambda s: s.strike)

        return CanonicalOptionChainSnapshot(
            underlying_instrument_id=underlying.canonical_id,
            underlying_price=und_price,
            expiry=expiry,
            session_date=now_dt.date(),
            captured_at=now_dt,
            provider="DHAN",
            strikes=strikes_list,
        )
