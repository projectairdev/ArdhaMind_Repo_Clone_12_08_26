# MARKET INTELLIGENCE — TRADER DECISION SUMMARY LAYER ARCHITECTURE

**Document Version:** 1.0.0 — Authoritative Design Specification  
**Subsystem:** Market Intelligence Composition Layer  
**Target Surface:** `MarketIntelligenceWorkspace.tsx` (`MorningPlanView.tsx`, `LiveGuideView.tsx`, `TomorrowPlanView.tsx`)  
**Design Principle:** *Decision First $\rightarrow$ Evidence Second $\rightarrow$ Deep Telemetry Last*  
**Implementation Policy:** Design Only (Zero code changes / Zero new analytical pipelines)

---

## 1. ARCHITECTURAL OVERVIEW

The **Trader Decision Summary Layer** is a deterministic composition and distillation layer that sits immediately above the existing deep telemetry views in the Market Intelligence workspace.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              EXISTING CANONICAL ENGINE SOURCES                         │
├────────────────────────┬──────────────────────────┬────────────────────────────────────┤
│ Unified Nifty Intel    │ Opportunity Registry     │ Data Quality & Freshness Monitor   │
│ (Regime, Bias, Pivots) │ (Detectors, Qualify, RR) │ (SectionStatus, Latency, Gaps)     │
└────────────────────────┴──────────────────────────┴────────────────────────────────────┘
                                           │
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                 DETERMINISTIC DECISION COMPOSER (MarketDecisionSummaryComposer)        │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ • Validates mandatory input freshness (Spot <15s, Options <30s, Breadth <60s)          │
│ • Evaluates 8-point safety contract for status transition                              │
│ • Resolves deterministic trade parameters (Bias, Setup, Strike, Entry, Risk)           │
│ • Generates stable decision identity and compact evidence chips                        │
│ • Emits typed MarketDecisionSummary DTO                                                │
└────────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        MARKET INTELLIGENCE DECISION SUMMARY STRIP                      │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ [BULLISH]  PULLBACK CONTINUATION  [READY FOR APPROVAL]                                 │
│ 24,300 CE | Trigger: Break above 24,310 with Breadth >30                               │
│ Confidence 78% | Liquidity Good | Data Quality High | Risk Moderate                    │
│ Invalidation: Close below 24,270 | Evidence: Above VWAP • Put Wall Support • VIX Stable │
└────────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                EXISTING DEEP TELEMETRY & STRATEGY SUITABILITY PANELS                   │
│ (Morning Plan / Live Guide / Tomorrow Plan / Decision Zones / Evidence Tables)         │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. NON-NEGOTIABLE DESIGN INVARIANTS

1. **Zero New Analytical Engines:** The summary layer never computes new market direction, RSI, MACD, or synthetic indicators. It strictly consumes approved canonical outputs.
2. **Zero Fabricated Values:** When data is unavailable (e.g. options stream offline or market closed), values are stamped `NOT QUALIFIED`, `WAITING`, or `UNAVAILABLE`.
3. **No LLM Decision Authority:** LLM natural language models may phrase or summarize text, but can **never** determine bias, setup, strike, entry level, confidence, or execution readiness.
4. **Idempotent Decision Identity:** Decision IDs are deterministically derived from `(session_date, setup_type, direction, target_strike, trigger_price_bin)`.
5. **Phase-Aware Adaptation:** The summary automatically adjusts its schema representation across `MORNING_PLAN` (Pre-market watchlist), `LIVE_GUIDE` (Active trading candidate), and `TOMORROW_PLAN` (Carry-forward posture).
