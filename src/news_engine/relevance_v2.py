"""Deterministic NIFTY relevance, transmission-channel and impact model."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

from src.news_engine.source_authority import authority_rank


STREAMS = (
    "INDIA", "US_MARKETS", "FED_US_MACRO", "CHINA_ASIA", "EUROPE",
    "CRUDE_ENERGY", "GEOPOLITICS", "CURRENCY_RATES", "GLOBAL_RISK", "NIFTY_CORPORATE",
)


def load_nifty_universe(cache_path: Path = Path(".cache/macro_cache.json")) -> Dict[str, str]:
    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
        state = (payload.get("providers") or {}).get("nifty_metadata_provider") or {}
        cached = state.get("cached_raw_data") or []
        constituents = (cached[0] if cached else {}).get("constituents") or []
        return {str(item.get("symbol") or "").upper(): str(item.get("company_name") or "") for item in constituents if item.get("symbol")}
    except Exception:
        return {}


def parse_timestamp(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except Exception:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except Exception:
            for pattern in ("%d %b, %Y %z", "%d %b %Y %z", "%Y-%m-%d %H:%M:%S"):
                try:
                    parsed = datetime.strptime(value, pattern)
                    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
            return None


def recency(value: str, now: datetime | None = None) -> Tuple[int, str, float]:
    observed = parse_timestamp(value)
    if observed is None:
        return 0, "UNAVAILABLE", 0.0
    current = now or datetime.now(timezone.utc)
    age = max(0, int((current - observed.astimezone(timezone.utc)).total_seconds()))
    if age <= 3600:
        return age, "BREAKING", 1.0
    if age <= 6 * 3600:
        return age, "RECENT", 0.85
    if age <= 36 * 3600:
        return age, "ACTIVE_EVENT", 0.65
    if age <= 72 * 3600:
        return age, "AGING", 0.35
    return age, "STALE", 0.1


CONSTITUENT_ALIASES: Dict[str, list[str]] = {
    "ADANIPORTS": ["adani ports", "adani port", "adani ports and sez", "adani ports & sez"],
    "ADANIENT": ["adani enterprises"],
    "ASIANPAINT": ["asian paints", "asian paint"],
    "AXISBANK": ["axis bank", "axisbank"],
    "BAJAJ-AUTO": ["bajaj auto"],
    "BAJFINANCE": ["bajaj finance"],
    "BAJAJFINSV": ["bajaj finserv"],
    "BEL": ["bharat electronics"],
    "BPCL": ["bharat petroleum"],
    "BHARTIARTL": ["bharti airtel", "airtel"],
    "BRITANNIA": ["britannia industries", "britannia"],
    "CIPLA": ["cipla"],
    "COALINDIA": ["coal india"],
    "DIVISLAB": ["divis laboratories", "divi's laboratories", "divis lab"],
    "DRREDDY": ["dr reddy", "dr. reddy", "dr reddys"],
    "EICHERMOT": ["eicher motors", "royal enfield"],
    "GRASIM": ["grasim industries", "grasim"],
    "HCLTECH": ["hcl technologies", "hcl tech"],
    "HDFCBANK": ["hdfc bank", "hdfcbank"],
    "HDFCLIFE": ["hdfc life"],
    "HEROMOTOCO": ["hero motocorp", "hero honda"],
    "HINDALCO": ["hindalco industries", "hindalco"],
    "HINDUNILVR": ["hindustan unilever", "unilever india", "hul"],
    "ICICIBANK": ["icici bank", "icicibank"],
    "INDUSINDBK": ["indusind bank"],
    "INFY": ["infosys", "infy"],
    "ITC": ["itc limited", "itc ltd", "itc"],
    "JIOFIN": ["jio financial services", "jio financial"],
    "JSWSTEEL": ["jsw steel"],
    "KOTAKBANK": ["kotak mahindra bank", "kotak bank"],
    "LT": ["larsen & toubro", "larsen and toubro", "l&t"],
    "M&M": ["mahindra & mahindra", "mahindra and mahindra", "mahindra motors"],
    "MARUTI": ["maruti suzuki", "maruti"],
    "NESTLEIND": ["nestle india"],
    "NTPC": ["ntpc limited", "ntpc"],
    "ONGC": ["oil and natural gas corporation", "ongc"],
    "POWERGRID": ["power grid corporation", "power grid"],
    "RELIANCE": ["reliance industries", "ril", "reliance ind"],
    "SBILIFE": ["sbi life"],
    "SBIN": ["state bank of india", "sbi", "sbin"],
    "SHRIRAMFIN": ["shriram finance"],
    "SUNPHARMA": ["sun pharma", "sun pharmaceutical"],
    "TATACONSUM": ["tata consumer products", "tata consumer"],
    "TATAMOTORS": ["tata motors"],
    "TATASTEEL": ["tata steel"],
    "TCS": ["tata consultancy services", "tcs"],
    "TECHM": ["tech mahindra"],
    "TITAN": ["titan company", "titan"],
    "TRENT": ["trent limited", "trent"],
    "ULTRACEMCO": ["ultratech cement", "ultratech"],
    "WIPRO": ["wipro limited", "wipro"],
}

GENERIC_COMPANY_STOPWORDS = {
    "economic", "consumer", "products", "services", "finance", "financial",
    "power", "enterprises", "industries", "holdings", "motor", "motors",
    "bank", "banking", "life", "general", "petroleum", "energy", "limited",
    "ltd", "india", "group", "ports", "zone", "special", "corporation",
    "corp", "company", "co", "national", "state", "bharat", "indian",
    "international", "capital", "technologies", "tech", "infrastructure",
    "infra", "pharma", "pharmaceuticals", "chemical", "chemicals", "steel",
    "cement", "metals", "auto", "automobile", "insurance", "housing", "gas",
    "oil", "mines", "mining", "securities", "mutual", "fund", "trust"
}

PUBLISHER_STRIP_REGEX = re.compile(
    r"\b(the economic times|economic times|times of india|hindustan times|moneycontrol|"
    r"livemint|mint|business standard|financial express|reuters|bloomberg|cnbc|firstpost|"
    r"ndtv|zeebiz|investing\.com|open magazine|samco|univest|rediff|news on air|the hindu|"
    r"indian express|fortune india|business today|financial times|wall street journal|wsj)\b",
    re.IGNORECASE,
)


class NiftyRelevanceEngineV2:
    RULE_VERSION = "2.1.0"

    @classmethod
    def assess(cls, headline: str, content: str, category: str, stream: str,
               source_tier: str, nifty_universe: Dict[str, str] | None = None) -> Dict[str, Any]:
        # Strip publisher signatures and metadata to avoid matching publisher name against companies
        raw_text = f"{headline} {content}"
        clean_text = PUBLISHER_STRIP_REGEX.sub(" ", raw_text).lower()
        clean_headline = PUBLISHER_STRIP_REGEX.sub(" ", headline).lower()
        text = clean_text

        universe = nifty_universe or {}
        symbols: list[str] = []

        # 1. High-precision constituent matching
        for symbol, company in universe.items():
            sym_clean = symbol.upper()
            sym_low = symbol.lower()

            # Rule A: Exact NSE ticker symbol with word boundary (e.g. \bHDFCBANK\b, \bINFY\b, \bTCS\b)
            if len(sym_clean) >= 3 and re.search(rf"\b{re.escape(sym_low)}\b", clean_text):
                symbols.append(sym_clean)
                continue

            # Rule B: Canonical high-confidence aliases
            aliases = CONSTITUENT_ALIASES.get(sym_clean, [])
            matched_alias = False
            for alias in aliases:
                if re.search(rf"\b{re.escape(alias)}\b", clean_text):
                    symbols.append(sym_clean)
                    matched_alias = True
                    break
            if matched_alias:
                continue

            # Rule C: Meaningful multi-word company phrase (never single stopwords)
            company_name_low = company.lower()
            company_cleaned = re.sub(r"\b(limited|ltd|corporation|corp|company|co|the|india)\b", "", company_name_low).strip()
            parts = [p for p in company_cleaned.split() if p not in GENERIC_COMPANY_STOPWORDS and len(p) >= 4]
            if len(parts) >= 2:
                phrase = " ".join(parts)
                if phrase in clean_text:
                    symbols.append(sym_clean)
            elif len(parts) == 1 and len(parts[0]) >= 6:
                # Single distinctive brand name (e.g., "Infosys", "Britannia", "Hindalco")
                if re.search(rf"\b{re.escape(parts[0])}\b", clean_text):
                    symbols.append(sym_clean)

        symbols = list(dict.fromkeys(symbols))

        countries = []
        country_terms = {
            "INDIA": ("india", "indian", "nifty", "rupee", "rbi"),
            "US": ("united states", "u.s.", "us ", "wall street", "federal reserve", "fed "),
            "CHINA": ("china", "chinese", "pboc", "hong kong"),
            "JAPAN": ("japan", "nikkei", "boj"),
            "EUROPE": ("europe", "eurozone", "ecb"),
            "RUSSIA": ("russia", "ukraine"),
            "MIDDLE_EAST": ("iran", "israel", "middle east", "hormuz", "red sea"),
        }
        for country, terms in country_terms.items():
            if any(term in text for term in terms):
                countries.append(country)

        score = 1.0
        reasons = []
        channels = []
        direction = "NOT_ASSESSED"

        if symbols:
            score = max(score, 8.5)
            channels.extend(["SPECIFIC_NIFTY_SYMBOLS", "INDEX"])
            reasons.append(f"Direct official NIFTY constituent match: {', '.join(symbols)}")
        elif category in ("Earnings", "Corporate Action", "NIFTY_CORPORATE") or stream == "NIFTY_CORPORATE" or any(term in text for term in ("q1", "q2", "q3", "q4", "net profit", "revenue", "earnings", "results", "dividend")):
            score = max(score, 8.0)
            channels.extend(["CORPORATE", "INDEX"])
            reasons.append("Official Indian corporate earnings or disclosure transmission")
        if any(term in text for term in ("india", "indian", "nifty", "sensex", "rupee", "rbi", "sebi")):
            policy_action = any(term in text for term in ("rate cut", "rate hike", "monetary policy", "repo rate", "policy rate", "gdp growth"))
            score = max(score, 7.5 if policy_action else 7.0)
            channels.extend(["INDEX", "INR"])
            reasons.append("Direct India market or policy transmission")

        crude_terms = any(term in text for term in ("brent", "crude", "oil", "opec", "hormuz", "energy price"))
        crude_shock = any(term in text for term in ("surge", "spike", "supply disruption", "closure", "attack", "sanction", "cut output", "shortage"))
        if crude_terms:
            score = max(score, 7.5 if crude_shock else 5.5)
            channels.extend(["CRUDE", "INR", "ENERGY", "INDEX"])
            reasons.append("India oil-import, inflation and INR transmission channel")
            if crude_shock:
                direction = "NEGATIVE"
            elif any(term in text for term in ("falls", "drop", "decline", "eases", "supply increase")):
                direction = "POSITIVE"

        fed_terms = any(term in text for term in ("federal reserve", "fed ", "fomc", "us cpi", "nonfarm payroll", "treasury yield", "us jobs"))
        if fed_terms:
            surprise = any(term in text for term in ("surprise", "emergency", "unexpected", "hotter", "cooler", "shock"))
            score = max(score, 7.5 if surprise else 6.0)
            channels.extend(["YIELDS", "GLOBAL_RISK", "IT", "INR"])
            reasons.append("US rates, dollar and global risk-asset transmission")
            if any(term in text for term in ("rate hike", "hawkish", "hotter", "yields surge")):
                direction = "NEGATIVE"
            elif any(term in text for term in ("rate cut", "dovish", "cooler", "yields fall")):
                direction = "POSITIVE"

        if any(term in text for term in ("china", "chinese economy", "pboc", "hang seng")):
            score = max(score, 5.5)
            channels.extend(["METALS", "AUTO", "GLOBAL_RISK"])
            reasons.append("China growth, commodity-demand and Asian risk transmission")

        geopolitical = category == "Geopolitics" or stream == "GEOPOLITICS"
        transmission = any(term in text for term in ("oil", "crude", "shipping", "trade", "tariff", "sanction", "hormuz", "red sea", "india", "market selloff", "currency"))
        if geopolitical:
            score = max(score, 6.5 if transmission else 2.0)
            if transmission:
                channels.append("GLOBAL_RISK")
                reasons.append("Credible trade, energy, shipping, currency or risk-asset transmission")
                if any(term in text for term in ("escalation", "attack", "closure", "sanction", "war")):
                    direction = "NEGATIVE"
            else:
                reasons.append("No specific NIFTY transmission mechanism identified")

        if stream == "US_MARKETS" and any(term in text for term in ("selloff", "rally", "futures", "s&p 500", "nasdaq", "dow")):
            score = max(score, 5.5)
            channels.extend(["GLOBAL_RISK", "IT", "INDEX"])
            reasons.append("Major US equity risk-on/risk-off transmission")
        if stream == "GLOBAL_RISK" and any(term in text for term in ("crisis", "default", "instability", "recession", "emergency", "bank failure")):
            score = max(score, 7.5)
            channels.extend(["GLOBAL_RISK", "BANKS", "INDEX"])
            reasons.append("Systemic financial-risk transmission")
            direction = "NEGATIVE"
        if stream == "CURRENCY_RATES":
            score = max(score, 5.5)
            channels.extend(["INR", "YIELDS", "IT"])
            reasons.append("Dollar, INR and rate-sensitive equity transmission")
        if stream == "EUROPE" and any(term in text for term in ("ecb", "eurozone", "european markets")):
            score = max(score, 4.5)
            channels.append("GLOBAL_RISK")

        # Crypto-centric content penalty (weak relevance to NIFTY)
        crypto_terms = ("crypto", "bitcoin", "btc", "ethereum", "eth", "altcoin", "memecoin", "solana", "binance", "coinbase", "dogecoin")
        is_crypto = any(term in text for term in crypto_terms) and not any(term in text for term in ("rbi", "sebi", "central bank digital currency", "cbdc"))
        if is_crypto:
            score = min(score, 2.0)
            reasons.append("Penalized: Crypto-centric commentary weakly relevant to NIFTY")

        # Sensational / Doom-mongering opinion penalty without authoritative transmission
        sensational_terms = ("crash coming", "great depression", "market apocalypse", "will collapse", "disaster ahead", "armageddon", "market crash 80%")
        is_sensational = any(term in text for term in sensational_terms) and not any(term in text for term in ("rbi", "sebi", "nse", "pib", "reuters", "bloomberg"))
        if is_sensational:
            score = min(score, 3.0)
            reasons.append("Penalized: Sensational/doom-mongering opinion without official source evidence")

        # Evergreen / Educational / Generic commentary penalty
        explainer_terms = (
            "how to", "what is", "understanding ", "guide to", "explainer:", "basics of",
            "beginner's guide", "everything you need to know", "top 10 ", "5 reasons", "why you should",
            "opinion:", "column:", "view:", "why investors need", "demystified", "explained:"
        )
        is_explainer = any(term in text for term in explainer_terms)
        if is_explainer:
            score = min(score, 3.0)
            reasons.append("Penalized: Educational, evergreen, or generic commentary content")

        score = min(10.0, round(score, 1))
        critical_terms = any(term in text for term in ("strait closure", "sovereign default", "banking crisis", "emergency rate", "market halt"))
        if is_crypto or is_sensational or is_explainer:
            impact = "LOW"
        elif critical_terms and score >= 8.5:
            impact = "CRITICAL"
        elif score >= 7.5:
            impact = "HIGH"
        elif score >= 5.0:
            impact = "MEDIUM"
        else:
            impact = "LOW"
        if direction == "NOT_ASSESSED" and any(term in text for term in ("rally", "stimulus", "rate cut", "eases", "falls")):
            direction = "POSITIVE"
        elif direction == "NOT_ASSESSED" and any(term in text for term in ("selloff", "crisis", "surge", "hike", "escalation", "attack")):
            direction = "NEGATIVE"
        if not reasons:
            reasons.append("No material deterministic NIFTY transmission channel identified")

        return {
            "nifty_relevance_score": score,
            "impact_level": impact,
            "expected_direction": direction,
            "affected_channels": list(dict.fromkeys(channels)),
            "related_symbols": symbols,
            "related_countries": countries,
            "why_it_matters": "; ".join(reasons[:3]),
            "assessment_reasons": reasons,
            "rule_version": cls.RULE_VERSION,
            "authority_rank": authority_rank(source_tier),
        }
