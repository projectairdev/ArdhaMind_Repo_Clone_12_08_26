# tests/test_forward_outlook_persistence.py
from pathlib import Path
import json
from src.application.workstation_state_service import WorkstationStateService


def test_forward_outlook_snapshot_persistence(tmp_path):
    WorkstationStateService.reset_for_testing()
    WorkstationStateService.CACHE_DIR = tmp_path
    WorkstationStateService._allow_disk_cache_in_test = True

    try:
        payload = {
            "marketContext": {"current_spot": 24366.0, "previous_close": 24395.85},
            "optionContext": {"pcr": 1.14},
            "macroIntelligence": {"india_vix": {"value": 11.26}}
        }

        state = WorkstationStateService.build_from_legacy(
            payload, broker_state="CONNECTED", market_state="OPEN"
        )

        snaps = WorkstationStateService._snapshots_history
        assert len(snaps) > 0

        last_snap = snaps[-1]
        assert "forward_outlook" in last_snap
        fo = last_snap["forward_outlook"]
        assert "directional_bias" in fo
        assert "confidence" in fo
        assert "scenarios" in fo
    finally:
        WorkstationStateService.reset_for_testing()


def test_backward_compatibility_with_14_aug_history():
    hist_file = Path("data/cache/session_history_2026-08-14.json")
    if hist_file.exists():
        with open(hist_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        snaps = data.get("snapshots", [])
        # Older snapshots do not crash when missing forward_outlook
        for s in snaps:
            fo = s.get("forward_outlook")
            assert fo is None or isinstance(fo, dict)
