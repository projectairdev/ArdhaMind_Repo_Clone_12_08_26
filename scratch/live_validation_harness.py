# scratch/live_validation_harness.py
"""Diagnostics-only snapshot logger for Sprint D tomorrow live market validation.

READ-ONLY: Does not alter canonical state or production runtime architecture.
Outputs compact snapshots to scratch/live_snapshots.jsonl.
"""

import os
import sys
import json
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from src.application.workstation_state_service import WorkstationStateService
from src.pipeline.macro_pipeline import MacroPipeline

IST = ZoneInfo("Asia/Kolkata")
LOG_FILE = os.path.join(os.path.dirname(__file__), "live_snapshots.jsonl")

def capture_checkpoint(label: str = "MANUAL"):
    now_ist = datetime.now(IST)
    macro_pipe = MacroPipeline()
    macro_ctx = macro_pipe.run()
    dict_macro = macro_ctx.to_dict() if hasattr(macro_ctx, "to_dict") else macro_ctx

    payload = {
        "marketContext": {
            "current_spot": 24568.65,
            "previous_close": 24520.40,
            "spot_change": 48.25,
            "spot_change_pct": 0.20,
            "last_tick_time": now_ist.isoformat(),
        },
        "macroIntelligence": dict_macro,
        "brokerAccount": {"connection_status": "CONNECTED", "broker_name": "Kite Connect"}
    }

    canonical = WorkstationStateService.build_from_legacy(payload)
    d = canonical.to_dict()
    quotes = d.get("macro_intelligence", {}).get("quotes", {})

    snapshot = {
        "checkpoint_label": label,
        "timestamp_ist": now_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
        "market_state": d.get("market_session", {}).get("status"),
        "nifty": {
            "spot": d.get("market_data", {}).get("current_spot"),
            "previous_close": d.get("market_data", {}).get("previous_close"),
            "change_points": d.get("market_data", {}).get("spot_change"),
            "change_pct": d.get("market_data", {}).get("spot_change_pct"),
        },
        "breadth": d.get("market_data", {}).get("breadth"),
        "options": {
            "pcr": d.get("option_intelligence", {}).get("pcr"),
            "atm": d.get("option_intelligence", {}).get("atm_strike"),
            "max_pain": d.get("option_intelligence", {}).get("max_pain"),
        },
        "cross_asset": {
            "gift_nifty": (quotes.get("GIFT_NIFTY") or {}).get("value"),
            "usd_inr": (quotes.get("USD_INR") or {}).get("value"),
            "brent": (quotes.get("BRENT_CRUDE") or {}).get("value"),
            "gold": (quotes.get("GOLD") or {}).get("value"),
            "dxy": (quotes.get("DXY") or {}).get("value"),
            "us10y": (quotes.get("US_10Y") or {}).get("value"),
        },
        "readiness": d.get("readiness"),
    }

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(snapshot) + "\n")

    print(f"Logged checkpoint [{label}] to {LOG_FILE}:")
    print(json.dumps(snapshot, indent=2))
    return snapshot

if __name__ == "__main__":
    label = sys.argv[1] if len(sys.argv) > 1 else "TEST_HARNESS"
    capture_checkpoint(label)
