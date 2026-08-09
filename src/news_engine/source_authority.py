"""Deterministic source-authority classification for E2 news records."""
from __future__ import annotations

from urllib.parse import urlsplit


PRIMARY_NAMES = {
    "rbi", "reserve bank of india", "sebi", "nse", "nse india", "nifty indices limited",
    "federal reserve", "federal reserve board", "european central bank", "ecb",
    "u.s. bureau of labor statistics", "bureau of labor statistics", "bls", "pib",
}

TIER_B_NAMES = {
    "reuters", "bloomberg", "associated press", "ap news", "dow jones newswires",
    "financial times", "the wall street journal", "wall street journal", "nikkei asia",
}

TIER_C_NAMES = {
    "cnbc", "bbc", "the economic times", "economic times", "business standard",
    "businessline", "the hindu businessline", "moneycontrol", "ndtv profit", "fortune",
    "forbes", "marketwatch", "barron's", "yahoo finance", "hindustan times", "livemint",
}

PRIMARY_DOMAINS = {
    "rbi.org.in", "sebi.gov.in", "nseindia.com", "niftyindices.com", "federalreserve.gov",
    "ecb.europa.eu", "bls.gov", "pib.gov.in",
}


def _domain(url: str) -> str:
    try:
        host = (urlsplit(url).hostname or "").lower()
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return ""


def classify_source(source_name: str, source_url: str = "", source_type: str = "") -> str:
    name = " ".join(str(source_name or "").lower().split())
    domain = _domain(source_url)
    if source_type == "official" or name in PRIMARY_NAMES or any(domain == d or domain.endswith(f".{d}") for d in PRIMARY_DOMAINS):
        return "TIER_A_PRIMARY"
    if any(trusted in name for trusted in TIER_B_NAMES):
        return "TIER_B_HIGH_TRUST"
    if any(established in name for established in TIER_C_NAMES):
        return "TIER_C_ESTABLISHED_MEDIA"
    return "TIER_D_DISCOVERY"


def authority_rank(tier: str) -> int:
    return {
        "TIER_A_PRIMARY": 4,
        "TIER_B_HIGH_TRUST": 3,
        "TIER_C_ESTABLISHED_MEDIA": 2,
        "TIER_D_DISCOVERY": 1,
    }.get(str(tier), 0)
