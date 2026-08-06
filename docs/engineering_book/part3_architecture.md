# Part 3: Complete System Architecture

This section documents the structural blueprint of the NIFTY Option Finder & Market Intelligence Workstation. It outlines how components are partitioned into layers, how dependencies flow, and how the various engines and pipelines interact.

---

## 🏛️ Layered Architectural Blueprint

The workstation is structured into four distinct, logical layers:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        1. PRESENTATION LAYER                           │
│     [ Unified CLI Dashboard ]  ◄──►  [ Interactive React Web UI ]       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Polling & Preferences
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          2. PIPELINE LAYER                             │
│     [ Market Scoring ]  ──►  [ Trade Planner ]  ──►  [ Risk Bounds ]   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ stateless execution runs
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          3. ENGINE LAYER                               │
│     [ Pricing & OI ]    ──►  [ Strategy Calc ]  ──►  [ Gemini AI ]     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ instantiates data models
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          4. DATA & CORE UTILS                          │
│     [ Frozen Dataclasses ]  ──►  [ IO Stateless ]  ──►  [ Loggers ]    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🌊 Core Dependency Flow Rules

To enforce modularity and prevent circular dependencies, the following direction-of-coupling rules are strictly maintained:

1. **Top-Down Invocation**: Presentation layers invoke Pipelines. Pipelines coordinate and execute individual calculation Engines. Engines leverage core Utility and Data Model libraries.
2. **Horizontal Decoupling**: Engines do not invoke each other. For example, the `RiskEngine` cannot instantiate the `ConfidenceEngine`. Pipelines must coordinate the flow of information between them, passing intermediate data as immutable frozen dataclasses.
3. **No Direct System Access**: Engines must never call standard operating system hooks or handle direct filesystem input/output. They must use the helper wrappers in `src/utils/` (e.g., `io_utils.py`, `logger.py`).

---

## 🔄 Engine & Pipeline Inter-Relationships

The trading workstation orchestrates multiple specialized engines during a single analysis and execution run. Below is an overview of how these modules fit together:

### 1. Ingestion and Assessment (Market + Option + News)
- Raw pricing feeds from standard files, mock loaders, or live brokers (via `BrokerEngine`) are processed by `MarketIntelligencePipeline` and `OptionIntelligencePipeline`.
- Simultaneously, news feeds from `NewsEngine` are compiled.
- These three pipelines produce three frozen contracts: `MarketContext`, `OptionContext`, and `NewsSentimentContext`.

### 2. Synthesizing Directional Score (Scoring + Opportunity)
- The `MarketScoringPipeline` consumes the `MarketContext` and `OptionContext` to evaluate trend direction and derivative confluences. It computes a unified score (0.0 to 100.0) and assigns an alphabetical grade.
- The `OpportunityPipeline` consumes this score alongside `NewsSentimentContext`. If news sentiment is bearish while technical scores are bullish, the news sentiment acts as a multiplier, pulling down the overall directional opportunity to prevent bullish execution. The final output is an `OpportunityContext` indicating directional bias.

### 3. Evaluating Options Strategies (Strategy + Planner)
- If an opportunity exists, the `StrategyPipeline` evaluates which trading style (e.g., Scalping, Swing, Momentum) is most appropriate for current conditions.
- The `TradePlannerPipeline` takes the suitable strategies and maps them to active call and put contracts found within the `OptionContext`. It outputs structured `TradePlan` contracts defining absolute entry, stop-loss, and exit target ranges.

### 4. Risk Defense & Execution (Confidence + Risk + Decision)
- The `ConfidencePipeline` assigns statistical weightings to each candidate contract in the `TradePlan`.
- The `RiskPipeline` takes these weightings and subjects them to strict capital sizing rules and drawdown limits.
- The final plans are resolved by the `DecisionPipeline` into an actionable `DecisionReport` (`BUY`, `SELL`, `WATCH`).

### 5. Transaction Lifecycle & Simulation (Paper Trading + Broker)
- If the overall decision action is `BUY`, the `ExecutionLifecycleManager` instantiates a new transaction state machine.
- If running in simulated mode, the transaction is processed by the `PaperTradingEngine`, which validates margins, simulates slippage, and writes to a double-entry ledger file (`cache/paper_ledger.json`).
- If running in manual live tracking mode, the trade plan's parameters are presented on the operator's **Manual Broker Panel** for physical entry, and position lifecycles are tracked against live prices.

### 6. Analytics and Explanations (Performance + Gemini AI)
- As positions close, the `PerformanceAnalyticsEngine` updates win-rates, maximum drawdowns, and Sharpe ratios.
- At the same time, the `ExplanationEngine` sends the decision payload to the Google Gemini API, generating clear natural-language justifications that explain the trading logic.

---

## ⚙️ Workstation Operations and Configuration Boundaries

- **Operations Manager (`src/operations_engine/`)**: Constantly monitors CPU utilization, memory allocations, directory access permissions, and required `.env` API keys. It outputs an operational health score to the CLI and React dashboards.
- **Configuration Manager (`src/configuration_engine/`)**: Handles loading and exporting workspace parameters. It validates that parameters are within mathematical limits, overlays preset profile settings (such as Aggressive, Conservative, or Expiry Day), and translates deprecated schema values.
