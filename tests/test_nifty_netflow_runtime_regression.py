"""
tests/test_nifty_netflow_runtime_regression.py

Regression test suite for AIR Ardha Staging:
Validates that NiftyLiveWorkspace contains no undeclared `netFlow`, `scenario`, or `invalidation`
references and that TypeScript typechecking passes with zero errors.
"""
import re
import subprocess
from pathlib import Path
import pytest


def test_nifty_workspace_netflow_declaration():
    """Verify that netFlow, fiiNet, and diiNet are properly declared in PreMarketDashboard and all scopes."""
    nifty_file = Path("/opt/ardhamind/staging/src/frontend/components/NiftyLiveWorkspace.tsx")
    assert nifty_file.exists(), "NiftyLiveWorkspace.tsx must exist"
    
    content = nifty_file.read_text(encoding="utf-8")
    
    # 1. PreMarketDashboard must declare netFlow
    pre_market_match = re.search(r"function PreMarketDashboard\([^)]*\)\s*\{([\s\S]*?)(?:function LiveDashboard|export)", content)
    assert pre_market_match is not None, "PreMarketDashboard function must be defined"
    pre_market_body = pre_market_match.group(1)
    
    assert "const netFlow =" in pre_market_body, "PreMarketDashboard must declare `const netFlow =`"
    assert "const scenario =" in pre_market_body, "PreMarketDashboard must declare `const scenario =`"
    assert "const invalidation =" in pre_market_body, "PreMarketDashboard must declare `const invalidation =`"
    assert "const fiiNet =" in pre_market_body, "PreMarketDashboard must declare `const fiiNet =`"
    assert "const diiNet =" in pre_market_body, "PreMarketDashboard must declare `const diiNet =`"


def test_nifty_workspace_null_safe_unavailable_fallbacks():
    """Verify that when netFlow / fiiNet / diiNet is null, UNAVAILABLE fallback is rendered instead of hardcoded numbers."""
    nifty_file = Path("/opt/ardhamind/staging/src/frontend/components/NiftyLiveWorkspace.tsx")
    content = nifty_file.read_text(encoding="utf-8")
    
    # Verify UNAVAILABLE fallbacks exist in PreMarketDashboard
    assert 'netFlow != null ? `${netFlow >= 0 ? "+" : ""}${formatNumber(netFlow, 1)} Cr` : "UNAVAILABLE"' in content, \
        "netFlow must render UNAVAILABLE when null"
    assert 'fiiNet != null ? `${fiiNet >= 0 ? "+" : ""}${formatNumber(fiiNet, 1)} Cr` : "UNAVAILABLE"' in content, \
        "fiiNet must render UNAVAILABLE when null"
    assert 'diiNet != null ? `${diiNet >= 0 ? "+" : ""}${formatNumber(diiNet, 1)} Cr` : "UNAVAILABLE"' in content, \
        "diiNet must render UNAVAILABLE when null"


def test_typescript_static_typecheck_zero_errors():
    """Run `npm run lint` (tsc --noEmit) and verify zero errors across the staging frontend."""
    res = subprocess.run(
        ["npm", "run", "lint"],
        cwd="/opt/ardhamind/staging",
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert res.returncode == 0, f"TypeScript check must pass with code 0. Error output:\n{res.stdout}\n{res.stderr}"


def test_frontend_build_zero_errors():
    """Run `npm run build` and verify bundle builds successfully with zero errors."""
    res = subprocess.run(
        ["npm", "run", "build"],
        cwd="/opt/ardhamind/staging",
        capture_output=True,
        text=True,
        timeout=90,
    )
    assert res.returncode == 0, f"Vite build must pass with code 0. Error output:\n{res.stdout}\n{res.stderr}"
