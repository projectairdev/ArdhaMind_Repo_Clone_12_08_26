# Phase 4 legacy dependency map

The map was produced with repository-wide import searches over `src/` and
`tests/`, followed by runtime entry-point inspection. A file existing was not
treated as runtime evidence.

| Family | Production/test/script consumers before | Unique capability | Classification and decision |
|---|---|---|---|
| `broker_engine/` vs `broker/` | canonical mock adapter and broker tests imported `broker_engine` | old manager/report compatibility | compatibility code moved under `broker/compat`; tests migrated; old package deleted |
| `risk_engine/` vs `risk_engine_v2/` | only old strategies and old option/planner pipelines used procedural risk | procedural scanner helpers | helpers retained as `risk_engine_v2.legacy_utilities`; old package deleted |
| `config_engine/` vs `configuration_engine/` | broad runtime, tests and scripts imported `Config` | environment constants and scoring YAML | runtime and YAML moved unchanged into `configuration_engine`; old package deleted |
| `strategies/` vs `strategy_engine/` | old scanners/pipelines only | registered `BreakoutTrendStrategy` plugin | unique plugin code retained with explicit `legacy_` names inside canonical package; old package deleted |
| old market/option/planner pipelines | package registration plus standalone scanners | scanner-oriented dataframes/signals | no live consumer and no required test; registration and files deleted |
| `dashboard/`, `ui/`, React | dashboard used by historical tests; `ui/` only by deleted scripts | deterministic report serializers remain useful to tests | React canonical; text UI deleted; dashboard retained compatibility/test-only |
| `paper_trading/` and paper pipeline | paper tests/dashboard only | extraction candidate and historical fixtures | no runtime registration; pipeline moved to test support; package retained for future extraction tests |
| `execution_engine/` | execution tests and legacy dashboard only | future execution interface fixtures | isolated from broker/bridge runtime; retained, but canonical broker blocks calls |
| planner legacy | old `planner_pipeline.py` only scripts | scanner selection | deleted; `TradePlannerPipeline` remains canonical |
| standalone scanners/reports | no imports; CLI-only | obsolete multi-product CLI behavior | verified dead for current NIFTY workstation and deleted |

`nifty_option_finder.py` was named in the brief but did not exist at the Phase 4
baseline. `nifty_tomorrow.py` was an additional dead consumer of the retired
option pipeline and text UI; it was deleted under the same evidence.
