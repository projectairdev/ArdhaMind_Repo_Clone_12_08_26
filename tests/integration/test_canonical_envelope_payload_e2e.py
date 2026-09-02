"""
Integration test for Canonical Envelope Payload End-to-End.
Asserts that when underlying market and option computations produce data,
build_live_canonical_envelope() wires VWAP, ATR(14), Options PCR, Greeks, Breadth,
and Decision confidence into the emitted payload without dropping data in transit.
"""
from datetime import datetime, timezone, timedelta
import pytest
from src.application.workstation_state_service import WorkstationStateService


def test_canonical_envelope_payload_wires_live_computations_end_to_end():
    # 1. Setup realistic market context computed by MarketContextBuilder & CandleEngine
    market_context = {
        "current_spot": 24150.50,
        "open": 24080.00,
        "high": 24185.00,
        "low": 24060.00,
        "previous_close": 24010.00,
        "spot_change": 140.50,
        "spot_change_pct": 0.585,
        "vwap": 24125.40,
        "twap": 24110.20,
        "atr": 118.60,
        "or_high": 24160.00,
        "or_low": 24075.00,
        "support_levels": [24050.0, 23980.0, 23900.0],
        "resistance_levels": [24200.0, 24280.0, 24350.0],
        "trend_direction": "BULLISH",
        "market_regime": "TRENDING_UP",
        "volatility_state": "NORMAL_VOLATILITY",
        "breadth": {
            "advances": 34,
            "declines": 15,
            "unchanged": 1,
            "total": 50,
            "ratio": 2.27,
            "advances_pct": 68.0,
        },
        "candles": [
            {"time": "09:15", "open": 24080.0, "high": 24100.0, "low": 24070.0, "close": 24095.0, "volume": 120000},
            {"time": "09:20", "open": 24095.0, "high": 24130.0, "low": 24090.0, "close": 24125.0, "volume": 145000},
        ],
    }

    # 2. Setup realistic option context computed by MarketFeedService / OptionChainAggregator
    option_context = {
        "spot": 24150.50,
        "atm_strike": 24150.0,
        "pcr": 1.18,
        "max_pain": 24100.0,
        "call_wall": 24300.0,
        "put_wall": 24000.0,
        "atm_iv": 13.65,
        "expiry": "2026-09-03",
        "total_call_oi": 4850000,
        "total_put_oi": 5723000,
        "total_call_volume": 1250000,
        "total_put_volume": 1480000,
        "strike_universe": [
            {"strike": 24100.0, "ce_oi": 150000, "pe_oi": 320000, "ce_ltp": 110.0, "pe_ltp": 45.0},
            {"strike": 24150.0, "ce_oi": 280000, "pe_oi": 290000, "ce_ltp": 78.0, "pe_ltp": 72.0},
            {"strike": 24200.0, "ce_oi": 420000, "pe_oi": 180000, "ce_ltp": 52.0, "pe_ltp": 105.0},
        ],
        "sentiment": "BULLISH_SUPPORTIVE",
    }

    # 3. Build canonical envelope
    envelope = WorkstationStateService.build_live_canonical_envelope(
        market_context=market_context,
        option_context=option_context,
    )

    # 4. Assertions on Price Structure (VWAP and ATR MUST be populated)
    ps = envelope.get("price_structure")
    assert ps is not None, "price_structure must be in envelope"
    assert ps.get("vwap") == 24125.40, f"Expected VWAP 24125.40, got {ps.get('vwap')}"
    assert ps.get("atr_14") == 118.60, f"Expected ATR 118.60, got {ps.get('atr_14')}"
    assert ps.get("or_high") == 24160.00, f"Expected OR High 24160.00, got {ps.get('or_high')}"
    assert ps.get("or_low") == 24075.00, f"Expected OR Low 24075.00, got {ps.get('or_low')}"
    assert len(ps.get("key_supports", [])) > 0, "Supports should not be empty"
    assert len(ps.get("key_resistances", [])) > 0, "Resistances should not be empty"

    # 5. Assertions on Breadth
    breadth = envelope.get("breadth")
    assert breadth is not None, "breadth must be in envelope"
    assert breadth.get("advances") == 34, f"Expected advances 34, got {breadth.get('advances')}"
    assert breadth.get("declines") == 15, f"Expected declines 15, got {breadth.get('declines')}"
    assert breadth.get("ratio") == 2.27, f"Expected ratio 2.27, got {breadth.get('ratio')}"

    # 6. Assertions on Options & Greeks
    options = envelope.get("options")
    assert options is not None, "options must be in envelope"
    assert options.get("pcr") == 1.18, f"Expected PCR 1.18, got {options.get('pcr')}"
    assert options.get("max_pain") == 24100.0, f"Expected Max Pain 24100.0, got {options.get('max_pain')}"
    assert options.get("call_wall") == 24300.0, f"Expected Call Wall 24300.0, got {options.get('call_wall')}"
    assert options.get("put_wall") == 24000.0, f"Expected Put Wall 24000.0, got {options.get('put_wall')}"
    assert options.get("atm_iv") == 13.65, f"Expected ATM IV 13.65, got {options.get('atm_iv')}"
    assert len(options.get("strike_universe", [])) == 3, "Strike universe must contain 3 strikes"

    # 7. Assertions on Decision & Strike Candidate Greeks
    decision = envelope.get("decision")
    assert decision is not None, "decision key must not be omitted from envelope"
    assert decision.get("confidence_score") is not None and decision.get("confidence_score") > 0, "Confidence score must be positive"
    candidates = decision.get("strike_candidates", [])
    assert len(candidates) > 0, "Must have at least one strike candidate"
    atm_cand = candidates[0]
    assert atm_cand.get("strike") == 24150.0, f"Expected ATM strike 24150.0, got {atm_cand.get('strike')}"
    assert atm_cand.get("delta") is not None, "Candidate Delta must not be null"
    assert atm_cand.get("theta") is not None, "Candidate Theta must not be null"
    assert atm_cand.get("vega") is not None, "Candidate Vega must not be null"
    assert atm_cand.get("iv") is not None, "Candidate IV must not be null"

    # 8. Assertions on Prediction & Candles
    prediction = envelope.get("prediction")
    assert prediction is not None, "prediction must be in envelope"
    assert prediction.get("confidence_score") is not None and prediction.get("confidence_score") > 0
    assert len(envelope.get("candles", {}).get("1m", [])) == 2, "1m candles must be preserved"
