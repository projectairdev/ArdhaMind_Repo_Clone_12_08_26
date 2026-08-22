# MARKET DECISION SUMMARY — FIELD SOURCE & LINEAGE MATRIX

**Document Version:** 1.0.0 — Authoritative Field Source Mapping  
**Design Target:** Canonical Field Provenance for Decision Summary Layer  
**Policy:** 100% Provider/Canonical-Backed (Zero Fabricated Placeholders)

---

## 1. FIELD-BY-FIELD CANONICAL PROVENANCE

| Decision Summary Field | Allowed Display Values | Canonical Engine Source | State Path / DTO Property | Fallback / Degraded Behavior |
|:---|:---|:---|:---|:---|
| **NIFTY Bias** | `BULLISH`, `BEARISH`, `NEUTRAL`, `MIXED`, `UNAVAILABLE` | `UnifiedNiftyIntelligenceBuilder` / `ScoringEngine` | `unified_intelligence.market_bias` | `UNAVAILABLE` |
| **Setup Type** | `PULLBACK_CONTINUATION`, `BREAKOUT_CONTINUATION`, `RANGE_REVERSAL`, `SUPPORT_BOUNCE`, `ORB`, `NO_VALID_SETUP` | `OpportunityRegistryService` / `StrategySuitability` | `opportunities[0].strategy_name` | `NO_VALID_SETUP` |
| **Target Strike** | E.g. `24,300 CE`, `24,200 PE`, `NOT_QUALIFIED`, `WAITING_OPTIONS` | `OpportunityQualification` / `OptionChainBuilder` | `opportunities[0].contract.symbol` | `NOT_QUALIFIED` |
| **Entry Condition** | Deterministic Trigger String (Price + Volume/Breadth) | `OpportunityDetectors` / `DecisionZones` | `opportunities[0].entry_trigger_statement`| `WAITING_FOR_TRIGGER` |
| **Confidence** | Range: `0% – 100%` (Formatted integer) | `OpportunityScoringEngine` | `opportunities[0].scores.confidence_score` | Stamped `DEGRADED` if inputs stale |
| **Liquidity Grade** | `EXCELLENT`, `GOOD`, `FAIR`, `POOR`, `UNAVAILABLE` | `OptionChainBuilder` (Spread + Volume + OI) | `optionContext.liquidity_grade` | `UNAVAILABLE` |
| **Data Quality** | `HIGH`, `MEDIUM`, `LOW`, `DEGRADED` | `DataQualityService` / `StreamHealthMonitor` | `data_quality.overall_status` | `DEGRADED` |
| **Risk Level** | `LOW`, `MODERATE`, `HIGH`, `VERY_HIGH`, `BLOCKED` | `DeterministicRiskEngine` | `deterministic_risk.overall_risk` | `BLOCKED` |
| **Decision Status** | `WAITING`, `WATCH`, `QUALIFYING`, `READY_FOR_APPROVAL`, `BLOCKED`, `INVALIDATED`, `EXPIRED`, `UNAVAILABLE` | `MarketDecisionStatusEvaluator` | `decision_summary.status` | `BLOCKED` / `UNAVAILABLE` |
| **Invalidation** | Level & Structural Condition | `OpportunityDetectors` / `DecisionZones` | `opportunities[0].invalidation_statement` | `STRUCTURAL_BREAK` |
| **Supporting Evidence** | 3–5 Compact Evidence Chips | `EvidenceSynthesis` / `UnifiedSignals` | `opportunities[0].supporting_evidence[]` | Empty array |
| **Blocking Reasons** | Discrete enum strings explaining non-readiness | `QualificationEngine` | `opportunities[0].blocking_reasons[]` | Explanatory labels |
