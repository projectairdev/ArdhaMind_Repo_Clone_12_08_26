# Initial Dependency Map

This is the Checkpoint 1 high-level inventory. It is not the detailed field-level runtime provenance map, which remains a Checkpoint 2 prerequisite.

## Live runtime

```text
React components
  -> WorkstationStateContext and REST services
  -> Express routes / WebSocket in server.ts
  -> line-delimited JSON over Python stdin/stdout
  -> src/server_bridge.py
  -> BrokerService, streaming services, builders and selected pipelines
  -> Kite REST/WebSocket, Google News RSS, local JSON and SQLite caches
```

`server.ts` owns an in-memory workstation snapshot and starts `src/server_bridge.py --action daemon` with `PYTHONPATH=.`. Python emits `tick`, `state`, and `response` messages. Express merges state packets and broadcasts them to React.

## Frontend ownership and consumers

- `WorkstationStateContext.tsx` is the primary WebSocket-backed browser state owner.
- Market, score, opportunity, strategy, trade, confidence, risk, decision, portfolio, news, analytics and operations components mostly consume that context.
- Broker actions use REST services for login, order and exit commands.
- `TradingJournal.tsx` directly imports `mockTradeJournal`.
- `order_lifecycle.ts` maintains a browser-local mock lifecycle store.
- Some settings/operations components retain direct REST service imports alongside context consumption.

## Express endpoints

Major endpoint groups in `server.ts`:

- Workspace and runtime flags
- Broker login/logout/health
- Profile, funds, holdings, positions and orders
- Market and dashboard reports
- Planner, intraday, validation and optimization reports
- Order placement and position exit commands
- WebSocket state/tick broadcast

Express is not currently stateless: it stores active credentials, workspace mode, pending IPC requests and the latest workstation snapshot in memory.

## Python runtime responsibilities

`server_bridge.py` currently owns:

- IPC command routing and daemon loop
- Broker/session lifecycle
- Streaming subscription coordination
- Cached market, option and news contexts
- Market/scoring/opportunity/strategy report assembly
- Trade candidate, confidence, risk and decision synthesis
- Portfolio, analytics, news and operations assembly
- Compatibility serialization and standalone CLI actions

## Canonical and legacy import inventory

### Broker

- `broker/` is used by the live bridge, execution engine, workspace, operations, data services and modern broker tests.
- `broker_engine/` is used primarily by its own modules, `broker/adapters/mock_broker.py`, and `test_broker_integration.py`.
- Compatibility gap: the modern mock adapter imports legacy report models/managers.

### Risk

- `risk_engine_v2/` is directly consumed by `pipeline/risk_pipeline.py` and its tests.
- `risk_engine/` is still consumed by legacy `option_pipeline.py`, `planner_pipeline.py`, and `strategies/breakout_trend.py`.
- Compatibility work is required before legacy risk can be retired.

### Configuration

- `configuration_engine/` is used by the bridge and configuration-management tests.
- `config_engine/` remains widely imported by data, broker, option, scoring, risk, utility, workspace and legacy pipeline modules.
- `config_engine.Config` currently supplies runtime constants that the newer report-oriented configuration engine does not replace directly.

### Strategies

- `strategy_engine/` is consumed by `strategy_pipeline.py` and the live bridge.
- `strategies/` supplies the plugin registry and `BreakoutTrendStrategy` to older scripts and option/planner pipelines.
- The unique plugin/strategy execution behavior must be mapped before consolidation.

### Paper execution

- `paper_trading/` is consumed by `paper_trading_pipeline.py` and paper tests.
- `broker/services/virtual_execution.py` is used by the broker/runtime path.
- The frontend journal and order lifecycle also maintain mock/local state, creating three distinct paper-state mechanisms.

### Presentation

- React is the live visual presentation layer.
- Python `dashboard/` is used as report-to-dictionary/CLI serialization, especially for analytics and news.
- It must be classified as adapter code before any retirement.

## Pipeline inventory

Canonical orchestration exists for market intelligence, option intelligence, market scoring, opportunity, strategy, trade planning, confidence, risk, decision, news, intraday, paper trading, validation and optimization. The live bridge uses only part of this chain and directly constructs other reports.

## Initial data sources

| Source | Runtime role | Classification |
|---|---|---|
| Zerodha Kite REST | Account, instruments, quotes and historical candles | Live when authenticated |
| Kite WebSocket | Ticks and market streaming | Live when connected |
| Google News RSS | Headline ingestion | External best-effort |
| `.cache/session.json` | Broker session cache | Private local state |
| `cache/instruments.db` | Instrument metadata | Local reproducible cache |
| Virtual portfolio JSON | Paper execution state | Paper/local |
| `mockData.ts` and local lifecycle store | UI fallback/demo data | Mock |
| Root `kiteconnect.py` | Installed-package proxy or mock fallback | Ambiguous/high risk |

## Detailed mapping still required

Checkpoint 2 must map every major displayed field through component, context/service, endpoint, daemon state field, producer, source, timestamps, staleness, fallback and matching canonical pipeline output. No duplicate package is safe to delete before that work is complete.

