# tests/test_legacy_intelligence_stability.py
import pytest
import json
import subprocess
import tempfile
import os
from src.application.workstation_state_service import WorkstationStateService

def test_legacy_intelligence_adapter_diagnostics_safety():
    """Verify that adaptIntelligenceSnapshot provides safe array defaults for diagnostics."""
    mkt_ctx = {"current_spot": 24238.55}
    c_state = WorkstationStateService.build_from_legacy({"marketContext": mkt_ctx})
    c_dict = c_state.to_dict()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tf:
        json.dump(c_dict, tf)
        tmp_path = tf.name

    js_code = f"""
const fs = require('fs');
const payload = JSON.parse(fs.readFileSync('{tmp_path}', 'utf8'));
const diagRaw = payload.opportunity_intelligence?.qualification_diagnostics || {{}};
const result = {{
    hardBlockers: Array.isArray(diagRaw.hard_blockers) ? diagRaw.hard_blockers : [],
    softOpposingEvidence: Array.isArray(diagRaw.soft_opposing_evidence) ? diagRaw.soft_opposing_evidence : [],
    supportingEvidence: Array.isArray(diagRaw.supporting_evidence) ? diagRaw.supporting_evidence : [],
    qualificationStatus: diagRaw.qualification_status || "STANDBY",
    policyVersion: diagRaw.policy_version || "1.0.0"
}};
console.log(JSON.stringify(result));
"""
    try:
        cmd = ["node", "-e", js_code]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        diag = json.loads(res.stdout)

        assert isinstance(diag["hardBlockers"], list)
        assert isinstance(diag["softOpposingEvidence"], list)
        assert isinstance(diag["supportingEvidence"], list)
        assert diag["qualificationStatus"] == "STANDBY"
        assert diag["policyVersion"] == "1.0.0"
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_v2_view_model_array_invariants():
    """Verify buildMarketIntelligenceViewModel always returns empty arrays (never undefined/null) for collection fields."""
    c_state = WorkstationStateService.build_from_legacy({})
    c_dict = c_state.to_dict()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tf:
        json.dump(c_dict, tf)
        tmp_path = tf.name

    js_code = f"""
const fs = require('fs');
const {{ buildMarketIntelligenceViewModel }} = require('/opt/ardhamind/staging/dist_test/buildMarketIntelligenceViewModel.cjs');
const payload = JSON.parse(fs.readFileSync('{tmp_path}', 'utf8'));
const vm = buildMarketIntelligenceViewModel(payload);
console.log(JSON.stringify({{
    blockersIsArray: Array.isArray(vm.riskContext.blockers),
    confirmationsIsArray: Array.isArray(vm.riskContext.confirmations),
    keyEventsIsArray: Array.isArray(vm.sessionStory.keyEvents)
}}));
"""
    try:
        cmd = ["node", "-e", js_code]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)

        assert data["blockersIsArray"] is True
        assert data["confirmationsIsArray"] is True
        assert data["keyEventsIsArray"] is True
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
