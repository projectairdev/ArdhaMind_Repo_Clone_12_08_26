# Part 4: Engine-by-Engine Reference Manual

This section provides technical specifications for all twenty-three core calculation and operational engines within the NIFTY Option Finder & Market Intelligence Workstation.

---

## 🧭 Ingestion & Assessment Engines

### 1. Market Intelligence Engine
- **Purpose**: Ingest index feeds and parse price structure.
- **Responsibilities**: Classify trend directions, compute support/resistance levels, and estimate volatility metrics.
- **Inputs**: Raw tick price, historical close sequences.
- **Outputs**: `MarketContext` dataclass.
- **Dependencies**: `PivotPointCalculator`, `LinearRegressionClassifier`.
- **Key Algorithms**: Pivot-Point S/R calculation and least-squares regression lines over rolling 15-minute intervals.
- **Future Extensibility**: Add support for concurrent multi-timeframe analysis (1-min, 5-min, 15-min).

### 2. Option Intelligence Engine
- **Purpose**: Structural parsing of NIFTY options chains.
- **Responsibilities**: Ingest contract listings, identify At-The-Money (ATM) strikes, and calculate Put-Call Ratio (PCR) and Max Pain levels.
- **Inputs**: Options chain contracts.
- **Outputs**: `OptionContext` dataclass.
- **Dependencies**: `PutCallRatioCalculator`, `MaxPainCalculator`.
- **Key Algorithms**: Total Call/Put open interest aggregation, and option pain minimization search algorithms.
- **Future Extensibility**: Integrate historical open interest change velocity analysis.

### 3. Indicator Engine
- **Purpose**: Calculate advanced technical indicators.
- **Responsibilities**: Compute RSI, ATR, Moving Average crossovers, and Pivot Point support/resistance.
- **Inputs**: OHLCV data sequences.
- **Outputs**: Technical indicators context.
- **Dependencies**: `math_utils.py`.
- **Key Algorithms**: Wilders smoothing for ATR/RSI, standard mathematical pivot calculations.
- **Future Extensibility**: Implement custom GARCH volatility modeling.

### 4. News Intelligence Engine
- **Purpose**: Macro event scraping and sentiment processing.
- **Responsibilities**: Ingest headlines from RSS/APIs, normalize contents, deduplicate, and calculate a unified sentiment score.
- **Inputs**: Raw headline strings, calendar events.
- **Outputs**: `NewsSentimentContext` dataclass.
- **Dependencies**: Stateless text sentiment analyzers.
- **Key Algorithms**: Cosine similarity for headline deduplication, and sentiment impact decay models.
- **Future Extensibility**: Add real-time scraping adapters for major financial news portals.

---

## 🎯 Scoring & Suitability Engines

### 5. Market Scoring Engine
- **Purpose**: Synthesize market indicators into a unified directional score.
- **Responsibilities**: Weigh technical indicators, apply news multipliers, and map scores to letter grades.
- **Inputs**: `MarketContext`, `OptionContext`, `ScoringWeights`.
- **Outputs**: `MarketScore` dataclass.
- **Dependencies**: `configuration_engine`.
- **Key Algorithms**: Weighted-sum matrix multiplication.
- **Future Extensibility**: Integrate dynamic, machine-learning-optimized scoring weights.

### 6. Opportunity Engine
- **Purpose**: Determine active market opportunities and directional bias.
- **Responsibilities**: Map market scores to distinct windows and recommend a trading bias.
- **Inputs**: `MarketScore`.
- **Outputs**: `OpportunityContext` dataclass.
- **Dependencies**: `ScoringProcessor`.
- **Key Algorithms**: Discrete threshold categorization mapping.
- **Future Extensibility**: Support multi-factor regime classifications.

### 7. Strategy Engine
- **Purpose**: Map market conditions to distinct trading strategies.
- **Responsibilities**: Score suitability for Scalping, Trend Following, Swing, and Mean Reversion.
- **Inputs**: `MarketContext`, `OptionContext`.
- **Outputs**: `StrategyEvaluation` dataclass.
- **Dependencies**: Strategy suitability rules.
- **Key Algorithms**: Fuzzy logic rule-checking.
- **Future Extensibility**: Integrate custom strategy scripts written in Python or YAML.

### 8. Trade Planner Engine
- **Purpose**: Generate trade plans for candidate contracts.
- **Responsibilities**: Set entry, stop-loss, and exit targets.
- **Inputs**: `OpportunityContext`, `OptionContext`, `StrategyEvaluation`.
- **Outputs**: `TradePlan` dataclass.
- **Dependencies**: ATR indicators.
- **Key Algorithms**: ATR-bracketed stop placement formulas.
- **Future Extensibility**: Integrate bracket orders with trailing stops.

---

## 🛡️ Risk & Decision Engines

### 9. Confidence Engine
- **Purpose**: Assign statistical weightings to trade candidates.
- **Responsibilities**: Combine historical win-rates, volume trends, and indicators confluence into a confidence score (0-100).
- **Inputs**: `TradePlan`.
- **Outputs**: `ConfidenceReport` dataclass.
- **Dependencies**: Historical win-rate database caches.
- **Key Algorithms**: Multi-factor weighted probability averaging.
- **Future Extensibility**: Integrate reinforcement-learning-based confidence weights.

### 10. Risk Engine (v2)
- **Purpose**: Protect trading capital.
- **Responsibilities**: Enforce maximum drawdown limits, compute position sizes, and validate margin requirements.
- **Inputs**: `ConfidenceReport`, `RiskParameters`.
- **Outputs**: `RiskReport` dataclass.
- **Dependencies**: `PortfolioManager`.
- **Key Algorithms**: Kelly Criterion fraction allocation and absolute stop-loss bounds.
- **Future Extensibility**: Implement portfolio correlation-based risk limits.

### 11. Decision Engine
- **Purpose**: Resolve remaining plans into definitive actions.
- **Responsibilities**: Output final execution statuses (`BUY`, `SELL`, `WATCH`).
- **Inputs**: `RiskReport`.
- **Outputs**: `DecisionReport` dataclass.
- **Dependencies**: `ExecutionLifecycleManager`.
- **Key Algorithms**: Non-contradicting action state logic.
- **Future Extensibility**: Support multi-leg option strategy executions (spreads, straddles).

---

## 📈 Paper Trading & Broker Engines

### 12. Paper Trading Engine
- **Purpose**: Risk-free trading simulation.
- **Responsibilities**: Manage paper accounts, model slippage, and maintain double-entry transaction ledgers.
- **Inputs**: `DecisionReport`.
- **Outputs**: Simulated ledger update.
- **Dependencies**: Local ledger file cache.
- **Key Algorithms**: Double-entry accounting validations.
- **Future Extensibility**: Add support for multiple simulated paper accounts.

### 13. Manual Broker Integration
- **Purpose**: Verify broker connections and session tokens.
- **Responsibilities**: Authenticate Kite API keys, validate session tokens, and track account margins.
- **Inputs**: Broker API credentials.
- **Outputs**: Session validation status.
- **Dependencies**: Kite Connect libraries.
- **Key Algorithms**: Token-bucket rate-limiting.
- **Future Extensibility**: Integrate OAuth2 secure login flows.

### 14. Execution & Position Lifecycle Manager
- **Purpose**: Track live positions from initiation to closure.
- **Responsibilities**: Manage position states (`INITIATED`, `PLACED`, `EXECUTED`, `CLOSED`), track open P&L, and monitor exit targets.
- **Inputs**: Real-time tick feeds, active positions.
- **Outputs**: Position updates.
- **Dependencies**: Local database caches.
- **Key Algorithms**: State-transition validation rules.
- **Future Extensibility**: Integrate trailing stops with automatic notification alerts.

### 15. Performance Analytics Engine
- **Purpose**: Calculate trading performance metrics.
- **Responsibilities**: Compute Sharpe ratio, win rate, maximum drawdown, and profit/loss distributions.
- **Inputs**: Closed transaction histories.
- **Outputs**: Analytics report.
- **Dependencies**: Double-entry ledger data.
- **Key Algorithms**: Standard Sharpe calculations over annualized periods.
- **Future Extensibility**: Add Monte Carlo simulation forecasting tools.

---

## ⚙️ Operations & Configuration Engines

### 16. Workstation Health & Operations Manager
- **Purpose**: System-level self-diagnostics.
- **Responsibilities**: Check directory structures, verify Python/Node modules, monitor hardware utilization, and output overall readiness score.
- **Inputs**: Environment keys, directory maps, system resource monitors.
- **Outputs**: Overall readiness rating (`READY`, `READY_WITH_WARNINGS`, `NOT_READY`).
- **Dependencies**: `psutil` system libraries.
- **Key Algorithms**: Multi-point diagnostic scoring matrices.
- **Future Extensibility**: Support background process auto-recovery.

### 17. Configuration & Workspace Profile Manager
- **Purpose**: Profile and workspace customization.
- **Responsibilities**: Load scoring and risk files, overlay active profile presets, and handle schema migrations.
- **Inputs**: `config.yaml`, preference JSON schemas.
- **Outputs**: Unified active workspace configurations.
- **Dependencies**: `pyyaml`.
- **Key Algorithms**: Multi-level inheritance configuration merges.
- **Future Extensibility**: Dynamic runtime UI profile editing.

### 18. AI Explanation Layer
- **Purpose**: Explain workstation decisions in plain language.
- **Responsibilities**: Formulate prompt payloads and parse response text into clear reasoning.
- **Inputs**: `DecisionReport`.
- **Outputs**: `ExplanationReport` dataclass.
- **Dependencies**: Google Gemini API.
- **Key Algorithms**: Prompt templating and structural markdown parsing.
- **Future Extensibility**: Support custom explanation templates.

### 19. Evening Planner Engine
- **Purpose**: Generate post-market reports and forecasts.
- **Responsibilities**: Analyze day's trades, compile market summaries, and generate forecasts.
- **Inputs**: Live trading history, daily price arrays.
- **Outputs**: Post-market planning archive.
- **Dependencies**: `PerformanceProcessor`.
- **Key Algorithms**: Day-end summary formulas.
- **Future Extensibility**: Automated report delivery via email or Slack.

### 20. Intraday Assistant Engine
- **Purpose**: Compare live actions against pre-market evening plans.
- **Responsibilities**: Check trade parameters against limits, flag deviations, and issue warning alerts.
- **Inputs**: Current market context, active evening plan.
- **Outputs**: Alignment check status.
- **Dependencies**: `IntradayPipeline`.
- **Key Algorithms**: Limit checking algorithms.
- **Future Extensibility**: Integration with voice-assistant notifications.
