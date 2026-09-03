from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import inspect
import time
import pytest

from src.analytics.market_analytics_engine import MarketAnalyticsEngine
from src.market_data.models.canonical_option_chain import (
    CanonicalOptionChainSnapshot,
    CanonicalOptionLeg,
    CanonicalOptionStrike,
)
from src.market_data.models.canonical_tick import CanonicalTick
from src.market_data.models.completed_session_snapshot import CompletedSessionSnapshot
from src.market_data.models.quality_enums import (
    DataQualityStatus,
    OptionType,
)
from src.market_data.providers.dhan.dhan_instrument_mapper import DhanInstrumentMapper
from src.market_data.services.candle_engine import CanonicalCandleEngine
from src.market_data.services.instrument_master_service import InstrumentMasterService
from src.market_data.session.session_authority import CanonicalSessionAuthority
from src.market_data.state.live_market_state import LiveMarketState
from src.prediction.calibration.calibration_engine import PredictionCalibrationEngine
from src.prediction.evaluation.prediction_evaluator import PredictionEvaluator
from src.prediction.models.prediction_models import (
    DirectionClass,
    PredictionPhase,
    PredictionSnapshot,
)
from src.prediction.prediction_engine import PredictionEngine


def _setup_pipeline():
    master = InstrumentMasterService()
    DhanInstrumentMapper(master).register_default_universe()

    state_store = LiveMarketState(master)
    candle_engine = CanonicalCandleEngine()
    session_auth = CanonicalSessionAuthority()

    t0 = datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)
    for i in range(30):
        t = t0 + timedelta(minutes=i)
        p = 24500.0 + i * 2.0
        tick = CanonicalTick(
            canonical_instrument_id="IDX:NSE:NIFTY_50",
            provider="DHAN",
            session_date=date(2026, 8, 28),
            exchange_timestamp=t,
            received_at=t,
            last_price=p,
            open=24500.0,
            high=p + 3.0,
            low=p - 2.0,
            previous_close=24450.0,
            volume=5000 + i * 100,
        )
        candle_engine.apply_tick(tick)
        if i == 29:
            from src.market_data.bus.events import MarketEvent, MarketEventType
            state_store.apply_tick_event(MarketEvent("e_nifty", MarketEventType.TICK, t, 1, tick))

    analytics_engine = MarketAnalyticsEngine(state_store, candle_engine, session_auth)
    return analytics_engine


def test_1_prediction_e2e_lifecycle():
    analytics_engine = _setup_pipeline()

    # Generate analytics snapshot
    analytics_snap = analytics_engine.generate_snapshot()

    # Generate prediction snapshot
    pred_snap = PredictionEngine.generate_prediction(
        snapshot=analytics_snap,
        target_session_date=date(2026, 8, 28),
        phase=PredictionPhase.PRE_MARKET,
    )

    assert isinstance(pred_snap, PredictionSnapshot)
    assert pred_snap.prediction_record.reference_price > 24500.0
    assert pred_snap.prediction_record.direction_prediction in (DirectionClass.BULLISH, DirectionClass.NEUTRAL, DirectionClass.BEARISH)
    assert pred_snap.prediction_record.magnitude_distribution.expected_magnitude > 0.0

    # Evaluate against completed session
    completed = CompletedSessionSnapshot(
        canonical_instrument_id="IDX:NSE:NIFTY_50",
        session_date=date(2026, 8, 28),
        open=24500.0,
        high=24600.0,
        low=24480.0,
        close=24580.0,
        previous_close=24450.0,
        absolute_change=130.0,
        percent_change=0.53,
        range=120.0,
        final_candle_timestamp=datetime.now(timezone.utc),
        quality=DataQualityStatus.VALID,
    )

    outcome = PredictionEvaluator.evaluate(pred_snap.prediction_record, completed)
    assert outcome.actual_session_move > 0
    assert isinstance(outcome.direction_correct, bool)

    # Calibration calculation
    metrics = PredictionCalibrationEngine.calculate_metrics([(pred_snap.prediction_record, outcome)])
    assert metrics.sample_count == 1


def test_2_performance_benchmark_1000_predictions():
    analytics_engine = _setup_pipeline()
    analytics_snap = analytics_engine.generate_snapshot()

    t0 = time.perf_counter()
    iterations = 1000
    for _ in range(iterations):
        _ = PredictionEngine.generate_prediction(
            snapshot=analytics_snap,
            target_session_date=date(2026, 8, 28),
        )
    elapsed_s = time.perf_counter() - t0
    ops_per_sec = iterations / elapsed_s

    print(f"\n[PREDICTION BENCHMARK] Computed {iterations} full prediction snapshots in {elapsed_s*1000:.2f} ms ({ops_per_sec:.0f} predictions/sec)")
    assert ops_per_sec >= 1000.0


def test_3_architectural_import_inspection():
    import src.prediction.prediction_engine as pe_mod
    import src.prediction.direction.direction_prediction_engine as dpe_mod
    import src.prediction.magnitude.magnitude_prediction_engine as mpe_mod
    import src.prediction.confidence.prediction_confidence_engine as pce_mod
    import src.prediction.evaluation.prediction_evaluator as ev_mod
    import src.prediction.calibration.calibration_engine as cal_mod

    for mod in (pe_mod, dpe_mod, mpe_mod, pce_mod, ev_mod, cal_mod):
        source = inspect.getsource(mod)
        forbidden = ["kiteconnect", "dhanhq", "src.broker", "src.frontend", "src.controlled_execution"]
        for f in forbidden:
            assert f"import {f}" not in source
            assert f"from {f}" not in source
