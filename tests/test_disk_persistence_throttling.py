# tests/test_disk_persistence_throttling.py
from pathlib import Path
import time
from src.application.workstation_state_service import WorkstationStateService


def test_disk_persistence_throttling_and_forced_flush(tmp_path):
    WorkstationStateService.reset_for_testing()
    WorkstationStateService.CACHE_DIR = tmp_path
    WorkstationStateService._allow_disk_cache_in_test = True

    cache_file = tmp_path / "session_history_2026-08-14.json"

    payload1 = {"marketContext": {"current_spot": 24350.0}}

    # 1. First build_from_legacy: creates dirty state, forces write if empty
    WorkstationStateService.build_from_legacy(payload1, broker_state="CONNECTED", market_state="OPEN")
    WorkstationStateService.flush_session_history("2026-08-14")

    assert cache_file.exists()
    mtime1 = cache_file.stat().st_mtime

    # 2. Immediate second call within 30s throttle window without force: should NOT write to disk
    payload2 = {"marketContext": {"current_spot": 24355.0}}
    WorkstationStateService.build_from_legacy(payload2, broker_state="CONNECTED", market_state="OPEN")

    mtime2 = cache_file.stat().st_mtime
    assert mtime2 == mtime1, "Disk write should be throttled within 30s window"

    # 3. Forced flush (e.g. on market close or shutdown): MUST write to disk
    WorkstationStateService.flush_session_history("2026-08-14")
    mtime3 = cache_file.stat().st_mtime
    assert mtime3 >= mtime1
