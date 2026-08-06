# Deleted and relocated files

Deleted after import verification:

- retired package roots: `config_engine`, `risk_engine`, `strategies`,
  `broker_engine` (capabilities moved to canonical packages);
- legacy pipelines: `market_pipeline.py`, `option_pipeline.py`,
  `planner_pipeline.py`;
- production virtual execution: `broker/services/virtual_execution.py`;
- obsolete CLI presentation: `ui/__init__.py`, `ui/cli.py`;
- dead scripts: `options_signal_generator.py`, `stocks_signal_generator.py`,
  `evening_market_report.py`, `market_news.py`, `nifty_tomorrow.py`.

Relocated rather than deleted: broker compatibility managers to `broker/compat`,
procedural risk helpers to `risk_engine_v2`, unique old strategy plugin code to
`strategy_engine`, mock broker gateway and paper pipeline to `tests/support`.
