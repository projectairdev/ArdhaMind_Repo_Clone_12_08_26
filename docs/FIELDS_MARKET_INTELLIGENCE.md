# AIR Ardha Staging — Market Intelligence Data-Field Inventory

**Surface:** `Market Intelligence Workspace` (`MarketIntelligenceWorkspace.tsx`, `MorningPlanView.tsx`, `LiveGuideView.tsx`, `TomorrowPlanView.tsx`)  
**Environment:** Staging (`staging.ardhamind.projectair.in`)  
**Audit Date:** August 2026  
**Scope:** Complete visible data fields across Morning Plan (PRE), Live Guide (NOW), Tomorrow Plan (NEXT DAY), Decision Zones, Strategy Suitability, and Opportunity Pipeline.

---

## 1. PRE-MARKET SUB-TAB: MORNING PLAN (`MorningPlanView.tsx`)

| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| Best Plan Headline | Headline | String | Intelligence Resolver | `unified_intelligence.morning_plan.headline` | Pre-market | "Morning Structural Plan" |
| Carry-Forward Level | Carry-Forward | Number/INR | Technical Engine | `unified_intelligence.morning_plan.carry_forward_level` | Pre-market | "24,800.00" |
| Opening Range Estimate | Opening Range Est. | String | Pre-Market Model | `unified_intelligence.morning_plan.opening_range_est` | Pre-market | "24,780 – 24,860" |
| Preferred Bias | Bias Badge | Enum (BULLISH/BEARISH/NEUTRAL) | Scoring Engine | `unified_intelligence.morning_plan.preferred_bias` | Pre-market | "NEUTRAL" |
| Invalidation Condition | Invalidation | String | Decision Engine | `unified_intelligence.morning_plan.invalidation` | Pre-market | "Sustain below 24,750" |
| Morning Rationale | Rationale & Why | String/Markdown | Briefing Generator | `unified_intelligence.morning_plan.rationale` | Pre-market | Grounded multi-point rationale |
| Primary Scenario Name | PRIMARY SCENARIO | String | Scenario Engine | `trade_scenarios[0].name` | Pre-market | "Base Case Consolidation" |
| Primary Confidence | Confidence % | Percentage | Confidence Model | `trade_scenarios[0].confidence_score` | Pre-market | "75%" |
| Primary Action Plan | Action Plan | String | Scenario Engine | `trade_scenarios[0].plan` | Pre-market | Explicit execution directives |
| Primary Evidence Table | Evidence & Drivers | Array<Label, Value> | Unified State | `trade_scenarios[0].evidence` | Pre-market | 4-6 key metrics |
| Primary Historical Proof | Historical Proof | String | Backtest Engine | `trade_scenarios[0].historical_proof` | Pre-market | Historical win-rate & edge note |
| Alternate Scenario Name | ALTERNATE SCENARIO | String | Scenario Engine | `trade_scenarios[1].name` | Pre-market | "Breakout Continuation" |
| Alternate Confidence | Confidence % | Percentage | Confidence Model | `trade_scenarios[1].confidence_score` | Pre-market | "45%" |
| Alternate Action Plan | Action Plan | String | Scenario Engine | `trade_scenarios[1].plan` | Pre-market | Alternate contingency plan |
| Alternate Evidence Table | Evidence & Drivers | Array<Label, Value> | Unified State | `trade_scenarios[1].evidence` | Pre-market | 4-6 key metrics |
| Alternate Historical Proof | Historical Proof | String | Backtest Engine | `trade_scenarios[1].historical_proof` | Pre-market | Historical edge context |
| What to Watch First 15 Min | 5 Checklist Items | Array<Title, Condition, Status> | Temporal Engine | `unified_intelligence.first_15m_watch` | Session start | 5 discrete items |
| Strategy Name | Strategy Name | String | Strategy Evaluator | `strategy_suitability[].name` | Pre-market | Strategy label |
| Strategy Suitability Tag | Preferred / Alternate | Badge | Strategy Evaluator | `strategy_suitability[].tag` | Pre-market | "Preferred" / "Defensive" |
| Strategy Condition | When Condition | String | Strategy Evaluator | `strategy_suitability[].when_condition` | Pre-market | Setup trigger criteria |
| Strategy Trigger | Trigger Price / Event | String | Strategy Evaluator | `strategy_suitability[].trigger` | Pre-market | Entry trigger |
| Strategy Target | Target Area | String | Strategy Evaluator | `strategy_suitability[].target_area` | Pre-market | Price targets |
| Strategy Confidence | Strategy Confidence | Percentage | Strategy Evaluator | `strategy_suitability[].confidence` | Pre-market | "72%" |
| Strategy Historical Proof | Historical Proof Text | String | Strategy Evaluator | `strategy_suitability[].historical_proof` | Pre-market | Sample proof statistics |
| Yesterday Close | Close | Number/INR | Market Context | `marketContext.previous_close` | Static baseline | EOD close |
| Yesterday High / Low | High / Low | Number/INR | Market Context | `marketContext.previous_high` / `low` | Static baseline | EOD high/low |
| Yesterday Change & % | Change (Pts & %) | Number/Percentage | Market Context | `marketContext.previous_change` | Static baseline | EOD change |
| Yesterday Breadth | Advances / Declines | String | Breadth Archive | `marketContext.previous_breadth` | Static baseline | "32 / 18" |
| Yesterday VWAP | VWAP | Number/INR | Technical Archive | `technical_analysis.previous_vwap` | Static baseline | EOD VWAP |
| Yesterday FII Cash | FII Cash | Currency (Cr) | Macro Ingest | `macro_intelligence.institutional_flows.fii_net` | Daily EOD | "₹-450.0 Cr" |
| Yesterday DII Cash | DII Cash | Currency (Cr) | Macro Ingest | `macro_intelligence.institutional_flows.dii_net` | Daily EOD | "₹+980.0 Cr" |
| Today Open Snapshot (09:00-09:08) | Open, High, Low, VWAP | Immutable Numbers | Pre-Open Feed Bridge | `unified_intelligence.todays_open` | Frozen at 09:08 IST | Frozen immutable values |
| Decision Zone R2 | Resistance 2 | Number/INR | Technical Engine | `unified_intelligence.decision_zones.r2` | Pre-market | "25,050" |
| Decision Zone R1 | Resistance 1 | Number/INR | Technical Engine | `unified_intelligence.decision_zones.r1` | Pre-market | "24,950" |
| Central Pivot Zone | Pivot Decision Zone | Number/Range | Technical Engine | `unified_intelligence.decision_zones.pivot` | Pre-market | "24,850 – 24,870" |
| Decision Zone S1 | Support 1 | Number/INR | Technical Engine | `unified_intelligence.decision_zones.s1` | Pre-market | "24,780" |
| Decision Zone S2 | Support 2 | Number/INR | Technical Engine | `unified_intelligence.decision_zones.s2` | Pre-market | "24,700" |
| Bullish Above Trigger | Bullish Above | String | Technical Engine | `unified_intelligence.decision_zones.bullish_above` | Pre-market | "24,900" |
| Bearish Below Trigger | Bearish Below | String | Technical Engine | `unified_intelligence.decision_zones.bearish_below` | Pre-market | "24,800" |
| Invalidation Level | Invalidation | String | Technical Engine | `unified_intelligence.decision_zones.invalidation` | Pre-market | "24,740" |
| Trend Filter | Trend Filter | String | Technical Engine | `unified_intelligence.decision_zones.trend_filter` | Pre-market | "EMA 50 (24,810)" |
| Morning Global Cues | Global Cues | String | Macro Model | `macro_intelligence.global_cues_summary` | Pre-market | "Mildly Positive" |
| Morning VIX Risk | VIX Assessment | String | Volatility Model | `macro_intelligence.vix_risk_assessment` | Pre-market | "14.20 (Stable)" |
| Morning Event Risk | Event Risk | Enum (Low/Moderate/High) | Macro Calendar | `macro_intelligence.event_risk_level` | Pre-market | "Moderate" |
| Morning Overall Risk | Overall Risk | Badge | Risk Engine | `deterministic_risk.overall_risk` | Pre-market | "MODERATE RISK" |
| Value Suggestions Table | Zone, Upper, Lower, Conviction, Rationale | Array<Object> | Intelligence Engine | `unified_intelligence.value_suggestions[]` | Pre-market | Structured suggestion rows |

---

## 2. LIVE GUIDE SUB-TAB: LIVE INTRADAY (`LiveGuideView.tsx`)

| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| Best Action Now Status | Status Badge | Enum (WAIT/WATCH/QUALIFIED/etc.) | Opportunity Engine | `opportunity_intelligence.best_action.status` | 1s real-time re-eval | "WAIT" / "SETUP QUALIFIED" |
| Best Action Confidence | Score | Percentage | Opportunity Engine | `opportunity_intelligence.best_action.confidence` | Real-time | "82%" |
| Best Action Headline | Action Headline | String | Opportunity Engine | `opportunity_intelligence.best_action.headline` | Real-time | Descriptive guidance headline |
| Best Action Next Trigger | Next Trigger | String | Decision Engine | `opportunity_intelligence.best_action.next_trigger` | Real-time | "Break above 24,880 on 5m" |
| Best Action Invalidation | Invalidation | String | Decision Engine | `opportunity_intelligence.best_action.invalidation` | Real-time | "Close below VWAP (24,810)" |
| Best Action Rationale | Rationale Text | String | Opportunity Engine | `opportunity_intelligence.best_action.rationale` | Real-time | Multi-sentence evidence thesis |
| Market Structure State | Structure | Enum | Technical Analysis | `technical_analysis.market_structure` | Real-time | "Higher High / Higher Low" |
| Current Market Breadth | Breadth Bias | Badge | Breadth Engine | `market_score.breadth_bias` | 15s update | "POSITIVE (34 Adv / 16 Dec)" |
| VWAP Alignment | Price vs VWAP | Enum/String | Technical Engine | `technical_analysis.vwap_status` | Real-time | "ABOVE VWAP (+0.35%)" |
| Intraday Momentum | Momentum | Enum | Indicator Engine | `technical_analysis.momentum_state` | Real-time | "RSI Bullish Zone (62.4)" |
| Volatility State | Volatility / VIX | String | Macro Feed | `macro_intelligence.india_vix` | 1s update | "13.90 (-2.1%)" |
| Live Primary Scenario | Name, Confidence, Plan, Conditions, What To Do, Key Levels, Invalidation | Object | Scenario Engine | `trade_scenarios[0]` | Real-time update | Live scenario breakdown |
| Live Alternate Scenario | Name, Confidence, Plan, Conditions, What To Do, Key Levels, Invalidation | Object | Scenario Engine | `trade_scenarios[1]` | Real-time update | Live alternate breakdown |
| Real-Time Value Suggestions | Type, Level/Zone, Conviction, Why Level Matters, Data Basis | Array<Object> | Intelligence Engine | `unified_intelligence.live_value_suggestions[]` | 15s update | 4-6 decision rows |
| NIFTY Spot Hero | Spot & Change | Number/INR | Ticker Stream | `marketContext.current_spot` | 1s stream | Real-time spot |
| Bank Nifty Spot Hero | Bank Nifty Spot & Chg | Number/INR | Ticker Stream | `marketContext.bank_nifty_spot` | 1s stream | Real-time spot |
| RSI (14) Momentum | RSI | Number | Indicator Engine | `technical_analysis.rsi_14` | Real-time | "58.4 (Neutral-Bullish)" |
| Put-Call Ratio (PCR) | PCR | Float | Options Ingest | `option_intelligence.put_call_ratio` | 5s stream | "0.98" |
| Real-Time Leading Sectors | Leading Sectors | Array<String> | Sector Ingest | `market_data.leading_sectors` | 15s update | Top 3 sectors |
| Real-Time Lagging Sectors | Lagging Sectors | Array<String> | Sector Ingest | `market_data.lagging_sectors` | 15s update | Bottom 3 sectors |
| Real-Time Suitable Strategies | Strategy Name, Star Rating, When, Trigger, Target, R:R, Confidence | Array<Object> | Strategy Evaluator | `strategy_suitability[]` | Real-time re-ranking | 3-5 ranked strategies |
| Opportunity Qualification Pipeline | 5-Step Stage (Idea → Conditions → Confirm → Qualified → Action) | Pipeline Visual | Opportunity Engine | `opportunity_intelligence.qualification_stage` | Real-time state machine | Step highlighted in emerald |
| Opportunity Setup Name | Setup Name | String | Opportunity Engine | `opportunity_intelligence.best_opportunity.setup_type` | Real-time | "ORB_BULLISH_BREAKOUT" |
| Opportunity Summary & Link | Trade Proposal Summary | String & Button | Opportunity Engine | `opportunity_intelligence.best_opportunity.summary` | Real-time | Proposal link to Portfolio |
| Live Risk Context | Global, News, Volatility, Confirmations, Blockers | Object | Risk Model | `deterministic_risk` | Real-time | Live risk telemetry |

---

## 3. POST-MARKET SUB-TAB: TOMORROW PLAN (`TomorrowPlanView.tsx`)

| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| Best Plan for Tomorrow Headline | Headline | String | EOD Synthesizer | `forward_outlook.headline` | EOD generation | "Tomorrow Tactical Outlook" |
| Tomorrow Plan Rationale | Rationale & Evidence | String/Markdown | EOD Synthesizer | `forward_outlook.rationale` | EOD generation | Structural rationale |
| Tomorrow Confidence Score | Confidence Score | Percentage | Scoring Engine | `forward_outlook.confidence_score` | EOD generation | "80%" |
| Carry-Forward Level | Carry-Forward Level | Number/INR | EOD Pivot Engine | `forward_outlook.carry_forward_level` | EOD generation | "24,850" |
| Tomorrow Opening Zone | Opening / Decision Zone | String | EOD Pivot Engine | `forward_outlook.opening_zone` | EOD generation | "24,830 – 24,890" |
| Tomorrow Directional Bias | Bias Badge | Enum (BULLISH/BEARISH/NEUTRAL) | EOD Profiler | `forward_outlook.directional_bias` | EOD generation | "BULLISH BIAS" |
| Tomorrow Bullish Trigger | Bullish Above | String | EOD Pivot Engine | `forward_outlook.bullish_trigger` | EOD generation | "24,920" |
| Tomorrow Bearish Trigger | Bearish Below | String | EOD Pivot Engine | `forward_outlook.bearish_trigger` | EOD generation | "24,780" |
| Tomorrow Invalidation Level | Invalidation Level | String | EOD Pivot Engine | `forward_outlook.invalidation_level` | EOD generation | "24,720" |
| Tomorrow Support 1 / Support 2 | S1 / S2 | Number/INR | EOD Pivot Engine | `forward_outlook.support_1` / `2` | EOD generation | "24,800" / "24,720" |
| Tomorrow Resistance 1 / Resistance 2 | R1 / R2 | Number/INR | EOD Pivot Engine | `forward_outlook.resistance_1` / `2` | EOD generation | "24,950" / "25,020" |
| Best Strike Suggestions | Call Strike Zone / Put Strike Zone | Array<Type, Strike, Rationale, Conf, Proof> | Derivatives Resolver | `forward_outlook.strike_suggestions[]` | EOD generation | 2 formatted strike zones |
| Night Preparation Checklist | 4-5 Actionable Preparation Items | Array<Checklist Item, Proof> | Daily Engine | `forward_outlook.night_checklist[]` | EOD generation | 4-5 checklist rows |
| Tomorrow Suitable Strategies | Name, Tag, When, Trigger, Target, Confidence, Proof | Array<Object> | Strategy Evaluator | `forward_outlook.suitable_strategies[]` | EOD generation | 3-4 overnight setups |
| Tomorrow Market Mood | Market Mood | Enum/Badge | Macro Profiler | `macro_intelligence.market_mood` | EOD generation | "RISK ON" / "CAUTIOUS" |
| Tomorrow Event Risk | Overnight / Event Risk | Enum | Macro Calendar | `macro_intelligence.event_risk_level` | EOD generation | "LOW" / "MODERATE" |
| Tomorrow Confirmations / Blockers | Confirmations (X/5) / Blockers (X) | Counts | Risk Model | `deterministic_risk.confirmations_count` | EOD generation | "4 Confirmations / 0 Blockers" |
| Today Overview Summary | Open, High, Low, Close, Range, Day Type, Breadth, VWAP, VIX, PCR, Leadership | 11-Cell Grid | EOD Market Context | `post_market_briefing.summary_grid` | EOD generation | 11 completed session metrics |
| Confidence & Structure Strip | Plan Conf, Data Quality, Score, Regime, Liquidity | 5-Cell Matrix | Quality Engine | `data_quality.summary` | EOD generation | 5 system quality indicators |
