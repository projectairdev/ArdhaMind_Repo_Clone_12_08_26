# tests/test_market_intelligence_view_model.py
import pytest
import json
import subprocess
import tempfile
import os
from src.application.workstation_state_service import WorkstationStateService

def run_js_view_model_builder(canonical_dict, optional_evidence=None):
    """Helper to run buildMarketIntelligenceViewModel in Node using compiled builder."""
    os.makedirs("/opt/ardhamind/staging/dist_test", exist_ok=True)
    dist_path = "/opt/ardhamind/staging/dist_test/buildMarketIntelligenceViewModel.cjs"
    subprocess.run(
        ["npx", "esbuild", "src/frontend/viewmodels/buildMarketIntelligenceViewModel.ts",
         "--bundle", "--platform=node", "--format=cjs", f"--outfile={dist_path}"],
        check=True,
        capture_output=True
    )
    payload = {
        "state": canonical_dict,
        "evidence": optional_evidence or {}
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tf:
        json.dump(payload, tf)
        tmp_path = tf.name

    js_code = f"""
const fs = require('fs');
const {{ buildMarketIntelligenceViewModel }} = require('{dist_path}');
const payload = JSON.parse(fs.readFileSync('{tmp_path}', 'utf8'));
const vm = buildMarketIntelligenceViewModel(payload.state, payload.evidence);
console.log(JSON.stringify(vm));
"""
    try:
        cmd = ["node", "-e", js_code]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(res.stdout)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_full_healthy_state_mapping():
    mkt_ctx = {
        "current_spot": 24238.55,
        "spot_change": 56.40,
        "vwap": 24235.10,
        "breadth": {"advances": 20, "declines": 30, "unchanged": 0},
        "timestamp": "2026-08-21T10:00:00Z"
    }
    opt_ctx = {
        "vix": 13.85,
        "pcr": 1.15,
        "call_wall": 24300,
        "put_wall": 24100,
        "timestamp": "2026-08-21T10:00:00Z"
    }
    c_state = WorkstationStateService.build_from_legacy({'marketContext': mkt_ctx, 'optionContext': opt_ctx})
    vm = run_js_view_model_builder(c_state.to_dict())

    assert vm["corridor"]["spotPrice"] == 24238.55
    assert vm["corridor"]["vwap"] == 24235.10
    assert vm["corridor"]["status"] == "ABOVE_VWAP"
    assert vm["participation"]["advances"] == 20
    assert vm["participation"]["declines"] == 30
    assert vm["participation"]["breadthBias"] == "NEGATIVE"
    assert vm["derivatives"]["pcr"] == 1.15
    assert vm["derivatives"]["indiaVix"] == 13.85


def test_missing_breadth_returns_null_and_unavailable():
    mkt_ctx = {"current_spot": 24238.55}
    c_state = WorkstationStateService.build_from_legacy({'marketContext': mkt_ctx})
    vm = run_js_view_model_builder(c_state.to_dict())

    assert vm["participation"]["advances"] is None
    assert vm["participation"]["declines"] is None
    assert vm["participation"]["breadthBias"] == "UNAVAILABLE"


def test_missing_vwap_returns_corridor_unavailable():
    mkt_ctx = {"current_spot": 24238.55, "vwap": None}
    c_state = WorkstationStateService.build_from_legacy({'marketContext': mkt_ctx})
    c_dict = c_state.to_dict()
    c_dict["market_data"]["vwap"] = None
    c_dict["technical_analysis"]["vwap"] = None

    vm = run_js_view_model_builder(c_dict)

    assert vm["corridor"]["vwap"] is None
    assert vm["corridor"]["status"] == "UNAVAILABLE"


def test_opportunity_no_trade_standby():
    c_state = WorkstationStateService.build_from_legacy({})
    vm = run_js_view_model_builder(c_state.to_dict())

    assert vm["opportunity"]["hasQualifiedSetup"] is False
    assert vm["opportunity"]["status"] == "STANDBY"
