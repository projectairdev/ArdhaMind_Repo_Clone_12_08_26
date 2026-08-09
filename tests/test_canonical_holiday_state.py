import pytest
from datetime import datetime, timezone
from src.application.workstation_state_service import WorkstationStateService
from src.models.data_quality import FreshnessStatus

def test_holiday_market_closed_classification():
    payload = {
        "marketContext": {"current_spot": 24570.65, "timestamp": datetime.now(timezone.utc).isoformat()},
        "newsSentiment": {"status": "ready", "items": [{"title": "Test"}]},
        "macroIntelligence": {"quotes": {"GIFT_NIFTY": {"price": 24580.0}}}
    }
    state = WorkstationStateService.build_from_legacy(payload, broker_state="CONNECTED", market_state="HOLIDAY")
    assert state.market_session["is_closed"] is True
    assert state.data_quality["market_data"]["freshness_status"] == FreshnessStatus.MARKET_CLOSED.value
    assert state.data_quality["market_data"]["freshness_status"] != "FRESH"
    assert state.data_quality["market_data"]["freshness_status"] != "LIVE"
