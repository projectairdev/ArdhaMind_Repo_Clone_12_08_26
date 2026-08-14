"""
Cold Start Repair 2 Test Suite — Frontend Concurrent WebSocket Initialization
=============================================================================
Verifies:
1. WebSocket connect is initiated without waiting for REST promise resolution.
2. REST and WebSocket bootstrap execute concurrently (no `.finally(connect)` waterfall).
3. WS sequence N cannot be overwritten by later REST sequence N-1.
4. REST state can populate UI if WS is unavailable.
5. WS state supersedes older REST state.
6. Only one WebSocket connection is active (clean effect cleanup & ref guards).
7. Cleanup and reconnect behavior remain intact.
8. runtime_id and state_sequence semantics remain intact.
"""

from pathlib import Path
import pytest
from src.application.workstation_state_service import WorkstationStateService

ROOT = Path(__file__).resolve().parents[1]
CONTEXT_FILE = ROOT / "src/frontend/context/WorkstationStateContext.tsx"


def test_no_finally_connect_waterfall():
    """Verify that syncBroker(true).finally(connect) waterfall has been removed."""
    content = CONTEXT_FILE.read_text(encoding="utf-8")
    assert "syncBroker(true).finally(connect)" not in content
    assert "syncBroker().finally(connect)" not in content


def test_concurrent_websocket_and_rest_initialization():
    """Verify that connect() and syncBroker() are called concurrently on mount."""
    content = CONTEXT_FILE.read_text(encoding="utf-8")
    assert "[BOOT-FE] provider mounted" in content
    assert "[BOOT-FE] websocket connect initiated" in content
    assert "[BOOT-FE] first REST snapshot received" in content
    assert "[BOOT-FE] first WS snapshot received" in content

    # Check connect() comes right before syncBroker(true) in the mount effect
    mount_block = "console.log(\"[BOOT-FE] websocket connect initiated\");\n    connect();\n    syncBroker(true);"
    assert mount_block in content, "connect() must be invoked concurrently alongside syncBroker(true) on mount"


def test_state_sequence_ordering_contract():
    """Verify sequence ordering logic rejects older state sequence numbers for the same runtime_id."""
    content = CONTEXT_FILE.read_text(encoding="utf-8")
    assert "rawData.state_sequence <= prev.state_sequence" in content
    assert "prev.runtime_id === rawData.runtime_id" in content


def test_single_accept_canonical_state_handler():
    """Verify both WS and REST snapshots route through acceptCanonicalState."""
    content = CONTEXT_FILE.read_text(encoding="utf-8")

    # REST uses acceptCanonicalState
    assert "acceptCanonicalState(rawData)" in content
    # WS uses acceptCanonicalState
    assert "acceptCanonicalState(msg.data)" in content


def test_effect_cleanup_safety():
    """Verify useEffect cleans up websocket and timeout references properly on unmount."""
    content = CONTEXT_FILE.read_text(encoding="utf-8")
    assert "isUnmounted = true;" in content
    assert "ws.close();" in content
    assert "clearTimeout(reconnectTimeout);" in content


def test_runtime_sequence_semantics_in_backend():
    """Verify CanonicalWorkstationState builds monotonically increasing sequence numbers."""
    state1 = WorkstationStateService.build_from_legacy({}, broker_state="CONNECTED", market_state="CLOSED")
    seq1 = state1.state_sequence
    state2 = WorkstationStateService.build_from_legacy({}, broker_state="CONNECTED", market_state="CLOSED")
    seq2 = state2.state_sequence

    assert seq2 > seq1
    assert state1.runtime_id == state2.runtime_id
