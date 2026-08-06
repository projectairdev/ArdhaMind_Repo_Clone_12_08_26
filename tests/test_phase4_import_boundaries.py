from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.broker.models.trading_mode import TradingMode
from src.broker.services.broker_service import BrokerService


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
ACTIVE_RUNTIME = (
    SRC / "application", SRC / "broker" / "services", SRC / "broker" / "adapters",
    SRC / "data_engine", SRC / "options_engine", SRC / "scoring_engine",
    SRC / "strategy_engine", SRC / "risk_engine_v2", SRC / "pipeline",
    SRC / "workspace",
)
FORBIDDEN_IMPORTS = (
    "src.risk_engine", "src.broker_engine", "src.config_engine", "src.strategies",
    "src.paper_trading", "src.execution_engine", "src.broker.services.virtual_execution",
    "src.pipeline.market_pipeline", "src.pipeline.option_pipeline", "src.pipeline.planner_pipeline",
    "tests.support", "src.frontend.services.mockData",
)


def imports(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            yield node.module
        elif isinstance(node, ast.Import):
            yield from (alias.name for alias in node.names)


def test_active_runtime_obeys_canonical_import_boundaries():
    violations = []
    files = [SRC / "server_bridge.py"]
    for root in ACTIVE_RUNTIME:
        files.extend(p for p in root.rglob("*.py")
                     if "compat" not in p.parts and not p.name.startswith("legacy_"))
    for path in files:
        for module in imports(path):
            if any(module == item or module.startswith(item + ".") for item in FORBIDDEN_IMPORTS):
                violations.append(f"{path.relative_to(ROOT)} -> {module}")
    assert violations == []


@pytest.mark.parametrize("path", [
    "src/risk_engine", "src/broker_engine", "src/config_engine", "src/strategies",
    "src/pipeline/market_pipeline.py", "src/pipeline/option_pipeline.py",
    "src/pipeline/planner_pipeline.py", "src/broker/services/virtual_execution.py",
])
def test_retired_production_module_has_no_python_source(path):
    target = ROOT / path
    assert not target.is_file()
    assert not target.exists() or not any(target.glob("*.py"))


def test_canonical_broker_is_read_only_and_has_no_mock_registration():
    service = BrokerService.get_instance()
    assert service.trading_mode is TradingMode.LIVE_ZERODHA
    with pytest.raises(ValueError):
        service.set_mode(TradingMode.PAPER_TRADING)
    for method, args in ((service.place_order, {}), (service.modify_order, {}),
                         (service.cancel_order, {}), (service.exit_position, {"tradingsymbol": "NIFTY", "product": "MIS"})):
        with pytest.raises(PermissionError):
            method(**args)


def test_bridge_has_no_retired_command_or_mock_runtime():
    source = (SRC / "server_bridge.py").read_text(encoding="utf-8-sig")
    assert "MockKiteConnectClient" not in source
    assert "generate_dynamic_workspace_data" not in source
    assert 'args.action in {"place_order"' not in source
    assert "--quantity" not in source and "--transaction_type" not in source


def test_official_kite_resolution_and_optional_account_boundary():
    import kiteconnect
    assert "site-packages" in str(Path(kiteconnect.__file__).resolve()).lower()
    from src.application.runtime_input_builder import RuntimeInputBuilder
    snapshot = RuntimeInputBuilder.from_daemon(None, None, market_state="CLOSED", broker_state="DISCONNECTED")
    assert snapshot.account_summary is None
