from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import pytest

from src.market_data.models.canonical_tick import CanonicalTick
from src.market_data.models.quality_enums import DataQualityStatus
from src.replay.clock.replay_clock import ReplayClock
from src.replay.engine.market_replay_engine import MarketReplayEngine
from src.replay.evaluation.replay_evaluator import ReplayEvaluator
from src.replay.models.replay_models import ReplayConfig, ReplayEvent, ReplaySpeed
from src.replay.source.replay_source import ReplaySource


def _build_recorded_session() -> list[ReplayEvent]:
    events = []
    sess_d = date(2026, 8, 28)
    t0 = datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)

    for i in range(50):
        t = t0 + timedelta(seconds=i * 2)
        p = 24500.0 + i * 1.5
        tick = CanonicalTick(
            canonical_instrument_id="IDX:NSE:NIFTY_50",
            provider="CANONICAL_REPLAY",
            exchange_timestamp=t,
            received_at=t,
            session_date=sess_d,
            last_price=p,
            open=24500.0,
            high=p + 2.0,
            low=24490.0,
            previous_close=24450.0,
            volume=5000 + i * 100,
        )
        events.append(
            ReplayEvent(
                sequence=i + 1,
                event_timestamp=t,
                event_type="TICK",
                canonical_instrument_id="IDX:NSE:NIFTY_50",
                payload=tick,
                session_date=sess_d,
            )
        )
    return events


def test_1_replay_clock_operations():
    t0 = datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)
    clock = ReplayClock(t0)
    assert clock.current_time == t0

    t1 = t0 + timedelta(minutes=5)
    clock.advance_to(t1)
    assert clock.current_time == t1

    clock.step(30.0)
    assert clock.current_time == t1 + timedelta(seconds=30)

    with pytest.raises(ValueError, match="backwards"):
        clock.advance_to(t0)


def test_2_replay_source_and_engine_full_pipeline():
    events = _build_recorded_session()
    source = ReplaySource(events)
    assert len(source) == 50

    config = ReplayConfig(
        session_date=date(2026, 8, 28),
        speed=ReplaySpeed.SPEED_MAX,
    )

    engine = MarketReplayEngine()
    report = engine.run_replay(source, config)

    assert report.total_events == 50
    assert report.processed_events == 50
    assert report.final_state_revision > 0
    assert report.final_nifty_price is not None
    assert report.final_nifty_price > 24500.0


def test_3_deterministic_replay_reproducibility_proof():
    """
    CRITICAL DETERMINISTIC REPRODUCIBILITY PROOF:
    Executes the exact same recorded market replay twice.
    Verifies that the final state revision, NIFTY price, decision state, and reproducibility hash are 100% identical.
    """
    events = _build_recorded_session()
    source = ReplaySource(events)
    config = ReplayConfig(session_date=date(2026, 8, 28))

    # Run 1
    engine_1 = MarketReplayEngine()
    rep_1 = engine_1.run_replay(source, config)

    # Run 2
    engine_2 = MarketReplayEngine()
    rep_2 = engine_2.run_replay(source, config)

    is_reproducible, diffs = ReplayEvaluator.verify_reproducibility([rep_1, rep_2])

    assert is_reproducible is True
    assert len(diffs) == 0
    assert rep_1.reproducibility_hash == rep_2.reproducibility_hash
    assert rep_1.final_state_revision == rep_2.final_state_revision
    assert rep_1.final_nifty_price == rep_2.final_nifty_price
