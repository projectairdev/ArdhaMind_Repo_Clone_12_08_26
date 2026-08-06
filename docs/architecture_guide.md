# Architecture Guide

The **NIFTY Option Finder & Market Intelligence Workstation** is structured around a highly decoupled, stateless pipeline architecture. It separates raw data ingestion, mathematical filter calculations, tactical strategy checks, risk bounds evaluation, AI explanations, and presentation views.

---

## 🏛️ Core Design Principles

1. **Stateless Pipelines**: Engines do not maintain persistent, internal mutable state. They accept input models, execute pure mathematical transformations, and return structured output models. This makes execution highly predictable, threadsafe, and simple to unit-test.
2. **Immutable Data Contracts**: All data transfer objects are defined as standard Python `@dataclass(frozen=True)` models located in `src/models/`. This guarantees that once a pipeline component evaluates a piece of data, it cannot be mutated downstream.
3. **Builder Pattern for Reports**: End-of-pipeline reports are built step-by-step using functional builders, integrating multiple component sub-reports (such as confidence, risk, and decisions).
4. **Zero-Noise Presentation**: The presentation layers (CLI dashboards) accept clean models and output text-blocks directly, decoupling visual layout choices from business logic.

---

## 🧭 Ingestion & Evaluation Pipeline Flow

When the workstation is triggered (or loops on an interval), data flows sequentially through the pipelines:

```text
  [ Raw Market Quotes ]
           │
           ▼
[ Market Intelligence Pipeline ]  ──►  [ MarketContext Model ]
           │
           ▼
[ Option Intelligence Pipeline ]  ──►  [ OptionContext Model ]
           │
           ▼
[ Market Scoring Pipeline ]       ──►  [ MarketScore Model ]
           │
           ▼
[ Opportunity Pipeline ]          ──►  [ OpportunityContext Model ]
           │
           ▼
[ Strategy Evaluation Pipeline ]  ──►  [ StrategyEvaluation Model ]
           │
           ▼
[ Trade Planner Pipeline ]        ──►  [ TradePlan Model ]
           │
           ▼
[ Confidence Pipeline ]           ──►  [ ConfidenceReport Model ]
           │
           ▼
[ Risk Pipeline ]                 ──►  [ RiskReport Model ]
           │
           ▼
[ Decision Pipeline ]             ──►  [ DecisionReport Model ]
           │
           ▼
[ AI Explanation Layer ]          ──►  [ ExplanationReport Model ]
           │
           ▼
[ Paper / Broker Execution ]      ──►  [ Position Ledger Update ]
```

---

## 🧩 Engine Modules

### 1. Market & Option Intelligence Engines
- **Market Intelligence**: Standardizes ticker and index data into a unified `MarketContext` defining price regimes, trend slopes, and support/resistance boundaries.
- **Option Intelligence**: Ingests Option Chains, determines ATM strikes, and calculates Put-Call Ratio (PCR) and Max Pain levels to form an `OptionContext`.

### 2. Market Scoring & Opportunity Engines
- **Market Scoring**: Performs a weighted sum of market-context features (using configuration coefficients) to score market health on a scale of `0.0` to `100.0`. Assigns grades from `F` to `A+`.
- **Opportunity Engine**: Evaluates if current scores represent viable trading window setups (recommends directional biases like `BULLISH`, `BEARISH`, or `NEUTRAL`).

### 3. Strategy & Planner Engines
- **Strategy Evaluation**: Evaluates suitability for distinct strategy types (e.g. Scalping, Mean Reversion) on selected option contracts.
- **Trade Planner**: Formulates a structural `TradePlan` comprising buy/sell entry, stop loss, and exit targets.

### 4. Confidence & Risk Engines
- **Confidence Engine**: Analyzes historic performance, volume profiles, and trend confluences to assign statistical confidence ratings (`0.0` to `100.0`) to candidates.
- **Risk Engine**: Screens candidates against capital limitations, max drawdown rules, and margin specifications. Reduces sizes or rejects plans violating risk thresholds.

### 5. Decision & Execution Engines
- **Decision Engine**: Resolves remaining candidates into definitive actionable calls (`BUY`, `SELL`, `WATCH`).
- **Execution & Position Manager**: Handles active state lifecycles for positions, tracks actual paper executions, and models transaction slippage and broker fees.

### 6. Operations & Configuration Engines
- **Operations Manager**: Audits workstation health, folder setups, required environment keys, and CPU/memory resources.
- **Configuration Manager**: Supports loading, parsing, and validating workspace preferences and active profiles.

---

## 🔁 Thread Safety & Concurrency
Because all core pipeline steps are stateless and receive parameters as functional inputs, the workstation is natively suited for multi-threaded historical backtesting and high-frequency live scanning without data races or memory deadlocks.
