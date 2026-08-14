# tests/test_provenance_contract.py
from src.application.workstation_state_service import WorkstationStateService


def test_snapshot_provenance_contract():
    WorkstationStateService.reset_for_testing()

    payload = {
        "marketContext": {
            "current_spot": 24366.0,
            "source_type": "WEBSOCKET_STREAM"
        }
    }

    state = WorkstationStateService.build_from_legacy(
        payload, broker_state="CONNECTED", market_state="OPEN"
    )

    snaps = WorkstationStateService._snapshots_history
    assert len(snaps) > 0

    last_snap = snaps[-1]
    assert "provenance" in last_snap
    prov = last_snap["provenance"]

    assert prov.get("source_type") in ("WEBSOCKET_STREAM", "REST_POLL", "LAST_VALID_SESSION")
    assert "observed_at" in prov
    assert "trading_date" in prov
    assert "freshness" in prov
