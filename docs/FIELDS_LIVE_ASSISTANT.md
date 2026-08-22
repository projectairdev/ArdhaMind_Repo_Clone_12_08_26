# AIR Ardha Staging — Live Assistant & Intraday Narrator Data-Field Inventory

**Surface:** `Live Assistant Copilot Drawer` (`LiveAssistantPanel.tsx`) & `Intraday Assistant Workspace` (`IntradayAssistant.tsx`)  
**Environment:** Staging (`staging.ardhamind.projectair.in`)  
**Audit Date:** August 2026  
**Scope:** Complete visible data fields, conversational grounding metadata, user prompts, assistant structured responses, session context badges, and hidden context injection streams.

---

## 1. LIVE ASSISTANT COPILOT DRAWER (`LiveAssistantPanel.tsx`)

| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| Copilot Title & Badge | ARDHAMIND LIVE ASSISTANT [COPILOT] | Text & Badge | App Shell | Static | Static | "COPILOT" (Violet badge) |
| Grounding Telemetry Status | GROUNDED | Pulsing Status | Intelligence Grounding Engine | Real-time state connection | 1s stream | Green pulse indicator |
| Context Workspace Badge | CONTEXT: [MODULE] | Badge | Navigation Context | `activeModule` | Instant on tab navigation | "CONTEXT: MARKET NIFTY" |
| Window Size Toggle | Maximize / Minimize Button | Interactive Icon | UI State | `assistantExpanded` | Instant | Expands drawer from 440px to 50vw |
| Message Sender Tag | TRADER / ARDHAMIND | Label & Avatar | Chat State | `chatMessages[].sender` | On message | Distinct sender badge |
| Message Timestamp | Time IST | Time String | Local Clock | `chatMessages[].timestamp` | On message | "18:07" |
| Message Formatted Content | Response Text | Markdown String | AI Reasoning Engine | `/api/live-assistant/query` response | On query | Formatted bullet points & bold terms |
| Grounding Sources Count | Grounded • X sources | Dropdown Trigger | Query Meta | `chatMessages[].metadata.evidence_used.length` | On query | Shield icon + sources count |
| Freshness Tag | LIVE / PRE_MARKET / POST_MARKET | Tag | Query Meta | `chatMessages[].metadata.freshness` | On query | Session freshness string |
| Answer Speech Act | Act: [ACT] | String | Query Meta | `chatMessages[].metadata.answer_act` | On query | "SUMMARY", "FACTUAL_ANSWER", "DIAGNOSTIC" |
| Data Sufficiency State | Sufficiency: [STATE] | Enum | Query Meta | `chatMessages[].metadata.data_sufficiency` | On query | "SUFFICIENT" / "PARTIAL" |
| Cited Canonical Sources | Sources: [LIST] | Comma-Separated | Query Meta | `chatMessages[].metadata.evidence_used` | On query | "Market State, Option Chain, Breadth" |
| Underlying Provider Tag | Provider: [PROVIDER] | String | Query Meta | `chatMessages[].metadata.provider` | On query | "Canonical Engine" / "GPT-4o Grounded" |
| Fallback Active Tag | [Fallback Active] | String Tag | Query Meta | `chatMessages[].metadata.fallback_used` | On query | Displayed if fallback was used |
| Ranked Drivers Summary | Ranked Drivers: [LIST] | Bulleted String | Query Meta | `chatMessages[].metadata.drivers` | On query | Key causal factors cited |
| Detected User Intents | Intents: [LIST] | Comma-Separated | Query Meta | `chatMessages[].metadata.intent` | On query | "MARKET_STATUS", "PCR_QUERY" |
| Loading Telemetry Spinner | Retrieving canonical evidence... | Pulsing Bar | UI State | `loading` | During inference | Cyan loading indicator |
| Suggested Contextual Questions | Dynamic Quick Pills | Array<String> | Session Engine | Context-aware questions (Pre vs Live) | On load / session change | 4 quick clickable pill prompts |
| User Input Composer | Text Input Box & Send Button | Interactive Input | Chat State | `inputPrompt` | Instant | Placeholder: "Ask ArdhaMind about session..." |

---

## 2. INTRADAY ASSISTANT WORKSPACE (`IntradayAssistant.tsx`)

| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| Workspace Header Status | INTRADAY INTELLIGENCE TIMELINE | Header & Status Badge | Session Monitor | `market_session.status` | Real-time | "MARKET MONITORING ACTIVE" / "SESSION COMPLETE" |
| Spot Price Hero | SPOT | Currency (INR) | Ticker Stream | `marketContext.current_spot` | 1s stream | "24,850.00" |
| Spot Change & % | Change (Pts & %) | Points & % | Ticker Stream | `marketContext.change_points` / `pct` | 1s stream | "+45.20 (+0.18%)" (Emerald/Rose) |
| Current Market State & Read | CURRENT MARKET STATE & READ | String/Markdown | Briefing Generator | `unified_intelligence.live_decision.current_read` | Continuous re-evaluation | 2-3 sentence grounded narrative |
| 15-Minute Window Timeline | Window Start–End, Price Change, Volume, Headline | Array<Object> | Temporal Windows Ingest | `live_assistant_temporal_state.windows[]` | Every 15 minutes | Historical 15m window cards |
| Significant Events Stream | Event Timestamp, Severity, Family, Narrative | Array<Object> | Event Detector | `live_assistant_temporal_state.significant_events[]` | Event-driven | Immediate event cards |
| Confirmation Families Matrix | Price, Breadth, Options, Volatility, Heavyweights, Macro | Multi-Family Grid | Temporal Evaluator | `live_assistant_temporal_state.confirmation_families[]` | 15s update | Trend arrows (↑ / → / ↓) & Stance |
| Structural Bias Badge | Bias Badge | Enum (BULLISH/BEARISH/NEUTRAL) | Decision Engine | `live_decision.structural_bias` | Real-time | "NEUTRAL" |
| Short-Term Momentum | Momentum Badge | Enum | Indicator Engine | `live_decision.short_term_momentum` | Real-time | "STABLE" / "ACCELERATING" |

---

## 3. ASSISTANT HIDDEN CANONICAL CONTEXT INJECTION (Non-Visual Ingestion)

| Canonical Context Stream | Data Payload Structure | Provider / Engine | Purpose in Assistant Synthesis |
|:---|:---|:---|:---|
| `MarketContext` | Spot, Open, High, Low, Prev Close, VWAP, Change %, Breadth Adv/Dec | Ingestion Bridge | Injected into system prompt for numerical exactness |
| `OptionContext` | PCR, Max Pain, ATM Strike, ATM IV, Call Wall, Put Wall, OI Skew | Option Pipeline | Grounding option queries & wall inquiries |
| `MacroContext` | FII/DII Cash Net, Global Cues (10 assets), India VIX, Scheduled Events | Macro Pipeline | Cross-asset & institutional context answering |
| `OpportunityContext` | Active Proposals, Qualification Stage, Setup Type, Entry, Stop, Target | Opportunity Engine | Grounding "is there a trade?" questions |
| `DeterministicRisk` | Blockers, Confirming Factors, Market Score, Risk Regime | Risk Engine | Grounding risk & hesitation questions |
| `TemporalWindows` | Last 8 x 15-minute OHLC & Event delta snapshots | Temporal Accumulator | Answering "what happened in the last 15/30 minutes?" |
