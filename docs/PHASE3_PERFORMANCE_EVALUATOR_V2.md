# PHASE 3 — PERFORMANCE EVALUATOR V2 SPECIFICATION

**Document Version:** 1.0.0 — Authoritative Performance Evaluation Specification  
**Component:** `PerformanceEvaluatorV2` (`src/analytics_engine/performance_evaluator_v2.py`)  
**Scope:** Attribution Separation (Analytical Quality vs Execution Quality), Multi-Horizon MFE/MAE Scoring, No-Trade Value  
**Target Environment:** AIR Ardha Staging (`/opt/ardhamind/staging`)  
**Status:** DESIGN COMPLETE (Staging Only — Production Untouched)

---

## 1. MULTI-LAYER ATTRIBUTION FRAMEWORK

To prevent conflating market prediction quality with execution latency or trader discretion, Performance V2 separates evaluation into **five discrete attribution layers**:

```
1. DECISION QUALITY: Did the structural setup, bias, and direction prove accurate in the market?
2. PROPOSAL QUALITY: Was the strike, trigger level, and invalidation boundary well-calibrated?
3. APPROVAL LATENCY: Did the trader review promptly or delay until the trigger moved?
4. EXECUTION QUALITY: What was the slippage between approved limit price and broker fill price?
5. POSITION MANAGEMENT: Did the trader follow trailing exit recommendations or exit prematurely?
```

---

## 2. COMPREHENSIVE OUTCOME METRICS INVENTORY

For every decision in the `DecisionLedger`, the evaluator calculates:
1. **Trigger Activation:** Did market price reach the specified entry trigger? (`TRIGGERED` | `UNTRIGGERED`)
2. **Directional Accuracy:** Maximum Favorable Excursion (**MFE**) vs Maximum Adverse Excursion (**MAE**) within 15m, 30m, 60m, and session close horizons.
3. **Target Achievement:** $T_1$ reached, $T_2$ reached, or Invalidation hit first.
4. **Time-to-Target / Time-to-Invalidation:** Duration in minutes from trigger activation.
5. **Confidence Calibration:** Brier score assessing whether $80\%$ confidence setups had higher empirical win rates than $60\%$ setups.
6. **Execution Slippage:** Difference in INR between `reference_option_ltp` and `average_fill_price`.

---

## 3. VALUATION OF NO-TRADE & BLOCKED DECISIONS

Performance V2 explicitly scores **No-Trade, Wait, and Blocked decisions**:
- **Correct Block:** Market reversed or chopped into a loss $\rightarrow$ **Positive Risk Capital Preserved Score**.
- **False Negative / Missed Opportunity:** Setup was blocked but subsequently rallied $\rightarrow$ **Calibrated Tuning Feedback**.
- **Zero Overtrading Incentive:** Ardha is rewarded for discipline during low-conviction or choppy market regimes.
