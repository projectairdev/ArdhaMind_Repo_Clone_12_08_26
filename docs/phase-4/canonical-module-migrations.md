# Canonical module migrations

- Configuration: `Config` and `scoring.yaml` moved into
  `configuration_engine`; all production/tests and operations health paths now
  use the canonical location without changing values.
- Risk: legacy procedural scanner helpers moved into `risk_engine_v2`; canonical
  runtime continues through `RiskPipeline` and `RiskBuilder` unchanged.
- Strategy: the only unique old plugin implementation was retained under
  `strategy_engine` for explicit compatibility; canonical suitability still uses
  `StrategyPipeline`/`StrategyEvaluationBuilder`.
- Broker: old manager compatibility modules moved under `broker/compat`; the
  runtime registers only `KiteBrokerGateway`. The mock gateway moved to test
  support.
- Pipelines: removed `MarketPipeline`, `OptionPipeline`, and `PlannerPipeline`.
  The application analytical service remains the only live orchestrator.
- Presentation: removed the standalone text UI and its dead scripts; React is the
  product presentation.

No scoring weights, thresholds, or analytical builder logic changed.
