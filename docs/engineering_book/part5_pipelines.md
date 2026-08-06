# Part 5: Pipeline Orchestration & Execution

This section documents how individual pipelines execute, transition contexts, and handle failures within the NIFTY Option Finder & Market Intelligence Workstation.

---

## 🏃 Execution Order & Core Data Flows

Every execution cycle follows a deterministic, sequential order. This guarantees that data is processed in a structured manner:

```text
       [ START OF RUN ]
              │
              ▼
1. MarketIntelligencePipeline ─────► Produces: MarketContext
              │
              ▼
2. OptionIntelligencePipeline ─────► Produces: OptionContext
              │
              ▼
3. NewsPipeline               ─────► Produces: NewsSentimentContext
              │
              ▼
4. MarketScoringPipeline      ─────► Produces: MarketScore
              │
              ▼
5. OpportunityPipeline         ─────► Produces: OpportunityContext
              │
              ▼
6. StrategyPipeline           ─────► Produces: StrategyEvaluation
              │
              ▼
7. TradePlannerPipeline       ─────► Produces: TradePlan
              │
              ▼
8. ConfidencePipeline         ─────► Produces: ConfidenceReport
              │
              ▼
9. RiskPipeline               ─────► Produces: RiskReport
              │
              ▼
10. DecisionPipeline          ─────► Produces: DecisionReport
              │
              ▼
11. Paper / Broker Execution  ─────► Updates Local Ledgers / Live Position state
              │
              ▼
        [ END OF RUN ]
```

---

## 🔄 Detailed Context Transitions

As information flows through the pipeline, data is packaged into immutable structures. This section outlines how these models transition:

### 1. `MarketContext` Transition
- **From**: `MarketIntelligencePipeline`
- **To**: `MarketScoringPipeline`, `StrategyPipeline`
- **Purpose**: Carries technical data (current price, trend slope, support/resistance levels, ATR) to scoring and strategy suitability algorithms.

### 2. `OptionContext` Transition
- **From**: `OptionIntelligencePipeline`
- **To**: `MarketScoringPipeline`, `StrategyPipeline`, `TradePlannerPipeline`
- **Purpose**: Carries options data (ATM strike, Put-Call Ratio, Max Pain, contract list) to scoring, suitability, and planning algorithms.

### 3. `MarketScore` & `NewsSentimentContext` Transition
- **From**: `MarketScoringPipeline` & `NewsPipeline`
- **To**: `OpportunityPipeline`
- **Purpose**: Combines technical scoring with current news sentiment. Sentiment scores range from `-1.0` to `+1.0`, acts as a multiplier to technical scores, and evaluates the final trading opportunity.

### 4. `OpportunityContext` & `StrategyEvaluation` Transition
- **From**: `OpportunityPipeline` & `StrategyPipeline`
- **To**: `TradePlannerPipeline`
- **Purpose**: Matches directional bias (`BULLISH`, `BEARISH`, `NEUTRAL`) with suitable strategies to evaluate contract candidates.

### 5. `TradePlan` Transition
- **From**: `TradePlannerPipeline`
- **To**: `ConfidencePipeline`
- **Purpose**: Carries candidate trade plans to confidence evaluation algorithms, assigning statistical probability weightings.

### 6. `ConfidenceReport` Transition
- **From**: `ConfidencePipeline`
- **To**: `RiskPipeline`
- **Purpose**: Carries probability weightings to risk evaluation algorithms to calculate capital allocations and lot sizes.

### 7. `RiskReport` Transition
- **From**: `RiskPipeline`
- **To**: `DecisionPipeline`
- **Purpose**: Carries risk-approved candidates to decision algorithms for final status resolution (`BUY`, `SELL`, `WATCH`).

---

## 🛡️ Failure Handling & Graceful Degradation

To prevent system crashes during pipeline execution, three layers of failure defense are enforced:

### A. Non-Blocking Catch Blocks
Each pipeline step is wrapped in try-except-finally blocks. If a pipeline step encounters an exception (e.g., missing API key, network timeout), the pipeline catches the error, logs a detailed traceback, and falls back to safe default parameters.

```python
# Failure management pattern
try:
    context = self.market_engine.evaluate(raw_ticks)
except Exception as e:
    self.logger.error(f"Market evaluation failed: {e}. Falling back to default baseline.")
    context = MarketContext.get_fallback_baseline()
```

### B. Fallback Context Generation
Every immutable context model includes a classmethod constructor named `get_fallback_baseline()`. This provides a zero-risk default context state (e.g., neutral bias, zero positions) if an engine failure occurs, preventing downstream pipeline steps from failing.

### C. Immediate Alerts
If a pipeline step falls back to a baseline state, it generates a high-severity alert flag. This flag is sent to the terminal and web dashboards, alerting the operator to the failure.
