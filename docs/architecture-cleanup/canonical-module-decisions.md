# Canonical Module Decisions

Decisions are import- and runtime-verified; no duplicate package is deleted in Phase 2.

| Family | Verified use and unique capability | Canonical decision / compatibility | Retirement criteria and target |
|---|---|---|---|
| `broker/` vs `broker_engine/` | Live bridge, workspace and execution use `broker/`; `mock_broker.py` and broker integration tests still consume legacy report managers | `broker/` canonical. Port only required reporting DTO behavior; live order methods stay unavailable | No production/test imports and parity tests; Phase 3/4 |
| `risk_engine_v2/` vs `risk_engine/` | `risk_pipeline.py` uses V2; older option/planner pipelines and `BreakoutTrendStrategy` use legacy functions | V2 canonical. Compatibility adapter must preserve semantics without exporting executable quantity | Migrate legacy pipeline/strategy imports; Phase 3 |
| `configuration_engine/` vs `config_engine/` | New engine builds reports/profiles; global `Config` supplies constants across data, scoring, broker, risk and workspace | `configuration_engine/` canonical management; typed settings must replace global constants incrementally | No hidden global consumers; Phase 3/4 |
| `strategy_engine/` vs `strategies/` | Live bridge/canonical pipeline use suitability engine; older scripts use registry and `BreakoutTrendStrategy` | `strategy_engine/` canonical for product; preserve plugin behavior only as internal validation if needed | Import map clear and strategy parity captured; Phase 3 |
| pipelines vs bridge synthesis | Canonical pipelines exist; `generate_dynamic_workspace_data` directly constructs contexts/reports and candidates | `pipeline/` canonical. Phase 2 marks bridge values legacy and introduces one state service/serializer | Full live stage orchestration and no direct synthesis; Phase 3 |
| paper systems | `paper_trading/`, virtual execution and browser lifecycle are separate systems; Phase 1 UI disconnects them | Outside AIR ArdhaMind runtime; preserve for future extraction | No production imports; later separate product |
| React vs Python dashboard | React is user UI; Python panels are used as dictionary/CLI serializers, including news/analytics | React canonical presentation. Replace panel serialization through canonical serializer | No bridge imports; Phase 3/4 |
| official Kite vs root shim | Ordinary `import kiteconnect` resolves repository-root `kiteconnect.py`, which proxies/mocks; tests may depend indirectly | Official installed package canonical; mock moves to `tests/support` | Resolution test proves site-packages; root shim removed in Phase 2 |
| intelligence vs old market/option pipelines | New `*_intelligence_pipeline.py` produces rich contexts; older `market_pipeline.py`, `option_pipeline.py`, `planner_pipeline.py` support scripts/tests | Intelligence/canonical workflow pipelines are target; older flows are compatibility/validation only | Consumers migrated and regression coverage retained; Phase 3/4 |

## Import categories

- Production-critical duplicate consumers are enumerated in `dependency-map.md` and remain active until migration.
- Test imports protect legacy semantics but do not establish product ownership.
- Script-only entry points (`nifty_tomorrow.py`, signal generators and CLI) are not evidence of browser-runtime use.
- The modern mock broker’s legacy imports are the main broker compatibility seam.

