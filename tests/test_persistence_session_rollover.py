# tests/test_persistence_session_rollover.py
"""
Test suite for Data Persistence, Session Rollover, and Recovery Verification.
"""

from pathlib import Path
import json
import pytest

from src.intelligence_engine.post_market_briefing_engine import PostMarketBriefingEngine
from src.broker.services.market_feed_service import MarketFeedService
from src.broker.services.session_manager import SessionManager


def test_persistence_audit_documents_exist():
    docs = [
        "docs/DATA_PERSISTENCE_MATRIX.md",
        "docs/SESSION_ROLLOVER_MATRIX.md",
        "docs/PERSISTENCE_BLOCKERS_AND_RISKS.md",
        "docs/PERSISTENCE_RESTART_RECOVERY_TEST.md",
    ]
    for d in docs:
        p = Path(d)
        assert p.exists(), f"Missing audit document: {d}"
        content = p.read_text(encoding="utf-8")
        assert len(content) > 100, f"Document {d} is empty"


def test_post_market_briefing_storage_dir_exists():
    storage_dir = PostMarketBriefingEngine.get_storage_dir()
    assert storage_dir.exists()


def test_market_feed_snapshot_path_defined():
    snap_path = MarketFeedService.SNAPSHOT_PATH
    assert snap_path == Path(".cache/kite_nifty_option_snapshot.json")


def test_session_manager_cache_path_defined():
    cache_path = SessionManager.get_cache_path()
    assert ".cache/session.json" in cache_path or "session.json" in cache_path
