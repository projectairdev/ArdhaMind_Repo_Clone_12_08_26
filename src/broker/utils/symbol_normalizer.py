from __future__ import annotations
from typing import Any, Optional

CANONICAL_NIFTY = "NSE:NIFTY 50"
CANONICAL_VIX = "NSE:INDIA VIX"
CANONICAL_BANKNIFTY = "NSE:NIFTY BANK"
CANONICAL_FINNIFTY = "NSE:NIFTY FIN SERVICE"
CANONICAL_MIDCPNIFTY = "NSE:NIFTY MID SELECT"

CANONICAL_INDEX_MAP = {
    "NIFTY 50": "NSE:NIFTY 50",
    "NIFTY": "NSE:NIFTY 50",
    "NIFTY50": "NSE:NIFTY 50",
    "NSE:NIFTY 50": "NSE:NIFTY 50",
    "NSE:NIFTY50": "NSE:NIFTY 50",
    "IDX:NSE:NIFTY_50": "NSE:NIFTY 50",
    "IDX:NSE:NIFTY 50": "NSE:NIFTY 50",
    "INDIA VIX": "NSE:INDIA VIX",
    "INDIAVIX": "NSE:INDIA VIX",
    "NSE:INDIA VIX": "NSE:INDIA VIX",
    "NSE:INDIAVIX": "NSE:INDIA VIX",
    "IDX:NSE:INDIA_VIX": "NSE:INDIA VIX",
    "IDX:NSE:INDIA VIX": "NSE:INDIA VIX",
    "NIFTY BANK": "NSE:NIFTY BANK",
    "BANKNIFTY": "NSE:NIFTY BANK",
    "NSE:NIFTY BANK": "NSE:NIFTY BANK",
    "NSE:BANKNIFTY": "NSE:NIFTY BANK",
    "IDX:NSE:NIFTY_BANK": "NSE:NIFTY BANK",
    "NIFTY FIN SERVICE": "NSE:NIFTY FIN SERVICE",
    "FINNIFTY": "NSE:NIFTY FIN SERVICE",
    "NSE:NIFTY FIN SERVICE": "NSE:NIFTY FIN SERVICE",
    "NSE:FINNIFTY": "NSE:NIFTY FIN SERVICE",
    "IDX:NSE:FINNIFTY": "NSE:NIFTY FIN SERVICE",
    "NIFTY MID SELECT": "NSE:NIFTY MID SELECT",
    "MIDCPNIFTY": "NSE:NIFTY MID SELECT",
    "NSE:NIFTY MID SELECT": "NSE:NIFTY MID SELECT",
    "NSE:MIDCPNIFTY": "NSE:NIFTY MID SELECT",
    "IDX:NSE:MIDCPNIFTY": "NSE:NIFTY MID SELECT",
}

STATIC_TOKENS = {
    256265: "NSE:NIFTY 50",
    264969: "NSE:INDIA VIX",
    260105: "NSE:NIFTY BANK",
    257801: "NSE:NIFTY FIN SERVICE",
    258057: "NSE:NIFTY MID SELECT",
    13: "NSE:NIFTY 50", # Dhan Nifty index ID
    25: "NSE:NIFTY BANK", # Dhan BankNifty index ID
}


def normalize_instrument_key(symbol_or_token: Any) -> str:
    """
    Canonical symbol normalization boundary for ArdhaMind.
    Ensures all index spot and benchmark symbols follow canonical identifiers (e.g. 'NSE:NIFTY 50').
    Resolves dynamically via InstrumentMasterService / InstrumentService lookup, with STATIC_TOKENS as documented fallback.
    """
    if symbol_or_token is None:
        return ""
    if isinstance(symbol_or_token, int):
        # 1. Attempt dynamic resolution via InstrumentService
        try:
            from src.broker.services.instrument_service import InstrumentService
            inst = InstrumentService.get_instance().lookup_instrument_by_token(symbol_or_token)
            if inst:
                ts = inst.get("tradingsymbol") or inst.get("name") or ""
                upper_ts = str(ts).strip().upper()
                if upper_ts in CANONICAL_INDEX_MAP:
                    return CANONICAL_INDEX_MAP[upper_ts]
                if ts:
                    exch = inst.get("exchange", "NSE")
                    return f"{exch}:{ts}"
        except Exception:
            pass

        # 2. Documented static token map fallback
        return STATIC_TOKENS.get(symbol_or_token, f"TOKEN_{symbol_or_token}")

    s = str(symbol_or_token).strip()
    upper = s.upper()
    if upper in CANONICAL_INDEX_MAP:
        return CANONICAL_INDEX_MAP[upper]
    return s


def is_canonical_nifty(symbol: Optional[str]) -> bool:
    """Checks if symbol resolves canonically to NIFTY 50."""
    return normalize_instrument_key(symbol) == "NSE:NIFTY 50"


def is_canonical_vix(symbol: Optional[str]) -> bool:
    """Checks if symbol resolves canonically to INDIA VIX."""
    return normalize_instrument_key(symbol) == "NSE:INDIA VIX"
