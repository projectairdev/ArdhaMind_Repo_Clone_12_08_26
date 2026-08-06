# Part 6: Immutable Data Models Spec

This section documents the immutable `@dataclass(frozen=True)` contracts that serve as the single source of truth for all pipeline communication.

---

## 🔒 Why Immutable Contracts?

In highly dynamic, multi-threaded trading environments, mutable state leads to bugs (e.g., downstream risk engines accidentally altering contract strike prices).

To prevent this, the workstation enforces three core constraints on all data structures inside `src/models/`:
1. **Absolute Immutability**: All dataclasses are decorated with `frozen=True`. Once created, no properties can be updated.
2. **Type Safety**: Properties are decorated with strict type hints (including enums and customized subtypes).
3. **Lossless Serialization**: Every data model supports translation to and from standard dictionary or JSON formats, ensuring simple transmission between the Python backend and React frontend.

---

## 📂 Core Data Models Specification

### 1. `MarketContext`
- **Location**: `src/models/market.py`
- **Purpose**: Represents the technical status of the underlying index asset (NIFTY).
- **Core Fields**:
  - `spot_price`: `float` - Current index tick price.
  - `trend_slope`: `float` - The 15-minute least-squares regression line slope.
  - `regime`: `RegimeType` (Enum: `TRENDING`, `SIDEWAYS`, `VOLATILE`).
  - `trend`: `TrendType` (Enum: `BULLISH`, `BEARISH`, `NEUTRAL`).
  - `support_levels`: `List[float]` - Major support price levels.
  - `resistance_levels`: `List[float]` - Major resistance price levels.
  - `atr`: `float` - Average True Range.

### 2. `OptionContext`
- **Location**: `src/models/options.py`
- **Purpose**: Represents the status of the options chain.
- **Core Fields**:
  - `atm_strike`: `float` - At-The-Money strike.
  - `put_call_ratio`: `float` - Overall Put-Call Open Interest Ratio.
  - `max_pain`: `float` - Options chain max pain strike.
  - `implied_volatilities`: `Dict[str, float]` - Implied volatilities for major strikes.
  - `contracts`: `List[OptionContract]` - Standard list of active contracts.

### 3. `MarketScore`
- **Location**: `src/models/scoring.py`
- **Purpose**: Represents the synthesized score of the index and options data.
- **Core Fields**:
  - `raw_score`: `float` - Cumulative technical scoring (0.0 to 100.0).
  - `grade`: `str` - Letter grade corresponding to score (`A+` to `F`).
  - `outlook`: `str` - Human-readable sentiment summary (`EXCELLENT`, `GOOD`, `FAIR`, `CAUTION`).

### 4. `OpportunityContext`
- **Location**: `src/models/opportunity.py`
- **Purpose**: Represents the active trade opportunity window.
- **Core Fields**:
  - `has_opportunity`: `bool` - True if market conditions support a trade.
  - `directional_bias`: `DirectionalBias` (Enum: `BULLISH`, `BEARISH`, `NEUTRAL`).
  - `strength`: `float` - Calculated probability confidence (0% to 100%).

### 5. `StrategyEvaluation`
- **Location**: `src/models/strategy.py`
- **Purpose**: Stores suitability scores for all strategic options approaches.
- **Core Fields**:
  - `best_strategy`: `StrategyType` (Enum: `SCALPING`, `TREND_FOLLOWING`, `MEAN_REVERSION`).
  - `suitability_scores`: `Dict[StrategyType, float]` - Suitability ratings (0.0 to 100.0).

### 6. `TradePlan`
- **Location**: `src/models/planner.py`
- **Purpose**: Stores entry, target, and exit levels for candidate contracts.
- **Core Fields**:
  - `plan_id`: `str` - Unique system identifier.
  - `strategy_type`: `StrategyType` - Selected strategy.
  - `candidate_contracts`: `List[TradeCandidate]` - Specific contracts with entry/exit/stop brackets.

### 7. `ConfidenceReport`
- **Location**: `src/models/confidence.py`
- **Purpose**: Adds statistical checks to trade plans.
- **Core Fields**:
  - `plan_id`: `str` - Reference Trade Plan ID.
  - `confidence_scores`: `Dict[str, float]` - Confidence scores per contract candidate.

### 8. `RiskReport`
- **Location**: `src/models/risk.py`
- **Purpose**: Stores risk-screened plans and allocations.
- **Core Fields**:
  - `report_id`: `str` - Unique system identifier.
  - `approved_candidates`: `List[ApprovedCandidate]` - Approved contracts with allocated lot sizes.
  - `total_capital_allocated`: `float` - Total capital allocated to this trade.

### 9. `DecisionReport`
- **Location**: `src/models/decision.py`
- **Purpose**: Represents the final, actionable trade decision.
- **Core Fields**:
  - `decision_id`: `str` - Unique system identifier.
  - `action`: `DecisionAction` (Enum: `BUY`, `SELL`, `WATCH`).
  - `candidates_to_execute`: `List[ApprovedCandidate]` - Confirmed trade plans.
  - `rejection_reasons`: `List[str]` - Detailed reasons if candidates were rejected.

---

## 🔄 Dynamic Context Transitions

These dataclasses act as standard contracts during pipeline execution. An engine reads properties from one dataclass, applies its internal calculations, and returns a fresh, immutable dataclass to the pipeline.

```text
[Engine Ingests Dataclass] ──► [Stateless Execution (Calculations)] ──► [Engine Returns Fresh Dataclass]
```

This pattern guarantees that data flows in a clean, predictable, and fully auditable manner across the system.
