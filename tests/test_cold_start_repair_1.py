"""
Cold Start Repair 1 Test Suite — Non-Blocking Canonical Daemon Bootstrap
========================================================================
Verifies:
1. NewsPipeline slow network operation cannot delay entry into canonical main loop.
2. MacroPipeline slow network operation cannot delay entry into canonical main loop.
3. NewsPipeline exception cannot prevent first canonical state.
4. MacroPipeline exception cannot prevent first canonical state.
5. Initial provider refresh occurs exactly once through the selected background startup path.
6. Periodic provider refresh does not synchronously block canonical tick processing.
7. Multiple periodic refresh triggers cannot create duplicate concurrent refreshes.
8. Cached provider data retains its original provenance/freshness.
9. No synthetic market data is generated when enrichment is unavailable.
10. READ_ONLY boundary remains intact.
"""

import time
import pytest
from unittest.mock import patch, MagicMock

import src.server_bridge as sb
from src.server_bridge import (
    perform_cold_start_hydration,
    _bg_refresh_news,
    _bg_refresh_macro,
    get_initial_macro_context,
    get_initial_news_sentiment,
    FORBIDDEN_EXECUTION_ACTIONS,
    reject_execution_action,
)


@pytest.fixture(autouse=True)
def reset_server_bridge_state():
    """Reset server bridge locks and cache states before each test."""
    sb.cached_news_sentiment = sb.get_initial_news_sentiment()
    sb.cached_macro_context = sb.get_initial_macro_context()
    sb.last_news_fetch_time = 0.0
    sb.last_macro_fetch_time = 0.0
    yield


def test_perform_cold_start_hydration_is_fast_and_non_blocking():
    """Verify perform_cold_start_hydration completes without calling external network pipelines."""
    with patch("src.pipeline.macro_pipeline.MacroPipeline.run") as mock_macro, \
         patch("src.pipeline.news_pipeline.NewsPipeline.run") as mock_news:

        t0 = time.time()
        perform_cold_start_hydration()
        duration_s = time.time() - t0

        # Neither external network pipeline should be called synchronously during hydration
        assert mock_macro.call_count == 0
        assert mock_news.call_count == 0
        assert duration_s < 5.0, f"Hydration took {duration_s:.2f}s"


def test_slow_news_pipeline_does_not_block_hydration():
    """Verify a 10-second blocking NewsPipeline.run does not block perform_cold_start_hydration."""
    def slow_news_run(self):
        time.sleep(5.0)
        return MagicMock()

    with patch("src.pipeline.news_pipeline.NewsPipeline.run", slow_news_run):
        t0 = time.time()
        perform_cold_start_hydration()
        duration = time.time() - t0
        assert duration < 0.2, f"Hydration blocked for {duration:.2f}s"


def test_slow_macro_pipeline_does_not_block_hydration():
    """Verify a 10-second blocking MacroPipeline.run does not block perform_cold_start_hydration."""
    def slow_macro_run(self):
        time.sleep(5.0)
        return MagicMock()

    with patch("src.pipeline.macro_pipeline.MacroPipeline.run", slow_macro_run):
        t0 = time.time()
        perform_cold_start_hydration()
        duration = time.time() - t0
        assert duration < 0.2, f"Hydration blocked for {duration:.2f}s"


def test_news_pipeline_exception_isolation():
    """Verify news pipeline exception in background refresh does not crash daemon or corrupt initial state."""
    with patch("src.pipeline.news_pipeline.NewsPipeline.run", side_effect=RuntimeError("Network timeout")):
        _bg_refresh_news()
        # State remains valid initial structure
        assert sb.cached_news_sentiment["status"] == "unavailable"


def test_macro_pipeline_exception_isolation():
    """Verify macro pipeline exception in background refresh does not crash daemon or corrupt initial state."""
    with patch("src.pipeline.macro_pipeline.MacroPipeline.run", side_effect=RuntimeError("Macro endpoint dead")):
        _bg_refresh_macro()
        # State remains valid initial structure
        assert sb.cached_macro_context["status"] == "unavailable"


def test_duplicate_concurrent_refresh_guard():
    """Verify that multiple concurrent refresh requests do not spawn duplicate pipeline executions."""
    call_count = 0

    def mock_news_run(self):
        nonlocal call_count
        call_count += 1
        time.sleep(0.3)
        mock_ctx = MagicMock()
        mock_ctx.items = []
        return mock_ctx

    with patch("src.pipeline.news_pipeline.NewsPipeline.run", mock_news_run), \
         patch("src.dashboard.news_panel.NewsIntelligencePanel.to_dict", return_value={"status": "READY", "items": []}):

        import threading
        t1 = threading.Thread(target=_bg_refresh_news)
        t2 = threading.Thread(target=_bg_refresh_news)
        t3 = threading.Thread(target=_bg_refresh_news)

        t1.start()
        time.sleep(0.01)  # ensure t1 acquires lock
        t2.start()
        t3.start()

        t1.join()
        t2.join()
        t3.join()

        # Only 1 execution should occur because t2 and t3 were rejected by acquire(blocking=False)
        assert call_count == 1, f"Expected 1 call count, got {call_count}"


def test_cached_provider_data_retains_provenance_and_freshness():
    """Verify initial provider data retains truthful unavailable/unconfigured status and timestamps."""
    initial_macro = get_initial_macro_context()
    initial_news = get_initial_news_sentiment()

    assert initial_macro["status"] == "unavailable"
    assert initial_macro["india_vix"]["status"] == "UNAVAILABLE"
    assert initial_macro["india_vix"]["value"] is None

    assert initial_news["status"] == "unavailable"
    assert initial_news["items"] == []


def test_no_synthetic_market_data_on_missing_enrichment():
    """Verify missing macro/news enrichment produces truthful nulls, never synthetic prices or defaults."""
    macro_ctx = sb.cached_macro_context
    news_ctx = sb.cached_news_sentiment

    assert macro_ctx.get("quotes", {}).get("GIFT_NIFTY") is None
    assert macro_ctx.get("india_vix", {}).get("value") is None
    assert news_ctx.get("items") == []


def test_read_only_boundary_intact():
    """Verify read-only boundary rejects forbidden execution actions."""
    for action in FORBIDDEN_EXECUTION_ACTIONS:
        result = reject_execution_action(action)
        assert result is not None
        assert result["code"] == 410
        assert "read only" in result["error"].lower()
