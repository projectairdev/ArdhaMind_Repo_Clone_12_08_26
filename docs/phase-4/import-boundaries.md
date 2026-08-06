# Canonical import boundaries

Active runtime code may import only:

- broker APIs from `src.broker` (compatibility managers are isolated under
  `src.broker.compat` and are not runtime-registered);
- risk behavior from `src.risk_engine_v2`;
- configuration from `src.configuration_engine`;
- strategy suitability from `src.strategy_engine`;
- analytical stages from the canonical `src.pipeline` exports and
  `src.application.AnalyticalPipelineService`;
- the installed `kiteconnect` package.

It must not import retired package names, paper/execution runtimes, virtual
execution, test support, legacy market/option/planner pipelines, or frontend mock
data. `tests/test_phase4_import_boundaries.py` enforces the policy with AST import
inspection and explicit removed-source checks.

Historical dashboard, paper, and execution fixtures are outside the active
runtime boundary. They are retained only for deterministic regression/future
extraction and cannot cross the read-only `BrokerService` boundary.
