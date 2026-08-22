# AIR Ardha Staging — Settings & Diagnostics Data-Field Inventory

**Surface:** `Settings Workspace` (`SettingsWorkspace.tsx`, `AdvancedDiagnosticsDrawer.tsx`, `DetectorHealthPanel.tsx`, `ArdhaPerformancePanel.tsx`, `SettingsDiagnostics.tsx`)  
**Environment:** Staging (`staging.ardhamind.projectair.in`)  
**Audit Date:** August 2026  
**Scope:** Complete visible data fields across General Preferences, Connections & Integrations, Alert Notifications, Advanced Diagnostics, Detector Telemetry, and Prediction Accuracy Records.

---

## 1. GENERAL PREFERENCES (`SettingsWorkspace.tsx`)

| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| Time Display Format | Time Format | Toggle (12-Hour / 24-Hour) | Local Storage | `localStorage.getItem("ardha_prefs")` | Instant | "12-Hour" default |
| Number Scaling Format | Number Format | Toggle (Indian Lakhs/Cr vs INTL M/B) | Local Storage | `localStorage.getItem("ardha_prefs")` | Instant | "Indian (Lakhs/Cr)" default |
| Default Landing Workspace | Default Landing Workspace | Selector (Market / Intelligence / News / Portfolio) | Local Storage | `localStorage.getItem("ardha_prefs")` | Instant | "Market" default |
| Default Market Sub-Tab | Default Market View | Selector (nifty / metrics / options) | Local Storage | `localStorage.getItem("ardha_prefs")` | Instant | "nifty" default |
| Preference Save Status | Preferences Saved Toast | String Banner | UI State | Local event | Event-driven (3s timeout) | Emerald banner |

---

## 2. CONNECTIONS & INTEGRATIONS (`SettingsWorkspace.tsx`)

| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| Zerodha KiteConnect Status | Zerodha KiteConnect | Enum (CONNECTED / DISCONNECTED) | Broker Engine | `broker_status.status` | 5s polling & auth callback | "CONNECTED" / "DISCONNECTED" |
| Authenticate / Manage Broker Action | Authenticate Broker / Manage Button | Interactive Button | OAuth Bridge | `/api/broker/login-url` | On click | Redirect to Zerodha OAuth |
| Market Data Ingest Status | Market Data | Enum (LIVE / READY) | Market Feed Bridge | `market_feed_status.status` | 1s stream | "LIVE" / "READY" |
| Options Data Stream Status | Options Data | Enum (HEALTHY / DEGRADED) | Option Pipeline | `operations_health.options_data` | 5s check | "HEALTHY" |
| News Engine Status | News Engine | Enum (HEALTHY / DEGRADED) | News Ingest Engine | `operations_health.news_engine` | 15s check | "HEALTHY" |
| Macro Calendar Pipeline Status | Macro Calendar | Enum (HEALTHY / DEGRADED) | Macro Pipeline | `operations_health.macro_calendar` | 60s check | "HEALTHY" |
| AI Assistant Engine Status | AI Assistant | Enum (READY / BUSY) | Reasoning Engine | `operations_health.ai_assistant` | Continuous | "READY" |

---

## 3. NOTIFICATIONS & ALERTS (`SettingsWorkspace.tsx`)

| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| Desktop Notification Permission Banner | Desktop Notification Permission Banner | Action Banner & Button | Browser Notification API | `Notification.permission` | On load | Amber banner if not granted |
| High Impact Market News Alerts | HIGH IMPACT MARKET NEWS | Switch Toggle | Local Storage | `notifs.highImpactNewsAlerts` | Instant | Enabled (true) |
| Market Open / Close Transitions | MARKET OPEN / CLOSE | Switch Toggle | Local Storage | `notifs.marketOpenCloseAlerts` | Instant | Enabled (true) |
| Broker Session Expiry Alerts | BROKER SESSION ALERTS | Switch Toggle | Local Storage | `notifs.brokerDisconnectAlerts` | Instant | Enabled (true) |
| Macro Event Reminders | MACRO EVENT REMINDERS | Switch Toggle | Local Storage | `notifs.economicEventReminders` | Instant | Enabled (true) |
| System Health & Telemetry Warnings | SYSTEM WARNINGS | Switch Toggle | Local Storage | `notifs.systemHealthWarnings` | Instant | Enabled (true) |

---

## 4. ADVANCED DIAGNOSTICS & SYSTEM TELEMETRY (`AdvancedDiagnosticsDrawer.tsx`, `SettingsDiagnostics.tsx`)

| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| Overall System Health | Overall Health | Enum (HEALTHY / DEGRADED) | Operations Monitor | `operations_health.overall` | Real-time | "HEALTHY" (Emerald badge) |
| Canonical Runtime ID | Runtime ID | UUID String | Runtime Process | `runtime_id` | Static per process lifetime | e.g. "8a7c2b3e-..." |
| State Sequence Number | State Sequence | Integer Counter | Workstation Sync | `state_sequence` | Incrementing counter | "#18420" |
| Active Market Session State | Market Session | Enum (OPEN/CLOSED/PRE/POST) | Session Clock | `market_session.status` | Real-time | "OPEN" / "CLOSED" |
| System Last Sync IST | Last Sync | Timestamp String | Workstation Context | `generated_at` (IST converted) | 1s stream | "18:07:15 IST" |
| App Version & Environment | Version / Environment | String Badges | Build Config | `version` / `environment` | Static | "v1.3.1-STAGING" / "STAGING" |
| Ingestion Pipeline Readiness Matrix (8 components) | Market Feed, Options, News, Macro, Broker, Scenarios, AI, Opportunities | Multi-Cell Grid | Pipeline Monitors | `workspace_readiness` | 5s check | "ready" / "connected" / "live" |
| Post-Auth Startup Latency Trace (5 metrics) | Token Exchange, Session Save, Broker Connect, Feed Subscribe, Total Post-Auth | Integer (ms) | Startup Benchmark Logger | `diagnostics.postAuthMetrics` | On auth completion | e.g. "124 ms / 450 ms Total" |
| Dataset Integrity Row (Dataset, Provider, Count, Status) | Telemetry Counts Table | Array<Object> | Data Validator | `data_quality.datasets[]` | 15s check | "50/50 Valid" |
| Export Diagnostics Action | Export Diagnostics JSON Button | Action Button | Local Diagnostics Builder | Generates JSON Blob | On demand | Downloads `ardhamind-diagnostics-*.json` |
| Staging QA Session Override Controls | AUTO, PRE-MARKET, LIVE, POST-MARKET | 4-Button Matrix | Staging Session Override State | `niftyModeOverride` | Instant | Highlights active mode (Staging only) |
| Reset UI Preferences Action | Reset Defaults Button | Action & Confirmation | Local Storage Clearer | Resets `ardha_prefs` | On confirm | Restores defaults |

---

## 5. OPPORTUNITY DETECTOR HEALTH (`DetectorHealthPanel.tsx`)

| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| Opportunity Engine Scan Duration | SCAN DURATION | Integer (ms) | Opportunity Engine | `opportunity_intelligence.scan_metrics.scan_duration_ms` | 8s scan cycle | e.g. "42 ms" |
| Detector Evaluation Duration | DETECTORS DURATION | Integer (ms) | Opportunity Engine | `opportunity_intelligence.scan_metrics.detector_duration_ms` | 8s scan cycle | e.g. "18 ms" |
| Evaluated Candidates Today | EVALUATED TODAY | Integer Count | Opportunity Engine | `opportunity_intelligence.scan_metrics.candidates_evaluated` | Daily count | e.g. 1420 |
| Detector Identifier & Version | Detector Name & Version | String (e.g. ORB Detector v1.2) | Engine Config | `opportunity_intelligence.detector_health[].detector_id` | Static | Name & version tag |
| Detector Health Status | HEALTHY / BLOCKED / ERROR | Badge | Health Monitor | `opportunity_intelligence.detector_health[].status` | 8s scan cycle | "HEALTHY" (Emerald) |
| Detected Opportunities Count | DETECTED | Integer Count | Detector Tracker | `opportunity_intelligence.detector_health[].detections_today` | Daily counter | Integer count |
| Qualified Opportunities Count | QUALIFIED | Integer Count | Detector Tracker | `opportunity_intelligence.detector_health[].qualified_today` | Daily counter | Integer count |
| Blocked Candidates Count | BLOCKED | Integer Count | Detector Tracker | `opportunity_intelligence.detector_health[].blocked_today` | Daily counter | Integer count |
| Rejected Candidates Count | REJECTED | Integer Count | Detector Tracker | `opportunity_intelligence.detector_health[].rejected_today` | Daily counter | Integer count |
| Input Blocker Warnings | Input Blocker | String | Data Validator | `opportunity_intelligence.detector_health[].data_blockers` | Real-time | Warning banner if blocked |

---

## 6. ARDHA PERFORMANCE & PREDICTION ACCURACY (`ArdhaPerformancePanel.tsx`)

| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| Date Selector & Historical Archives | TODAY & Historical Dates Dropdown | Selector | Performance History API | `/api/performance/history` | On load | Today's date selected |
| Total Hits Count Pill | HITS: X | Integer & Tone | Evaluation Engine | `records.filter(r => r.result === 'HIT').length` | On date change | Emerald pill count |
| Total Near Hits Count Pill | NEAR: X | Integer & Tone | Evaluation Engine | `records.filter(r => r.result === 'NEAR').length` | On date change | Amber pill count |
| Total Misses Count Pill | MISSES: X | Integer & Tone | Evaluation Engine | `records.filter(r => r.result === 'MISS').length` | On date change | Rose pill count |
| Total Pending Count Pill | PENDING: X | Integer & Tone | Evaluation Engine | `records.filter(r => r.result === 'PENDING').length` | On date change | Cyan pill count |
| Total Not Evaluable Pill | N/A: X | Integer & Tone | Evaluation Engine | `records.filter(r => r.result === 'NOT_EVALUABLE').length` | On date change | Gray pill count |
| Phase Filter Tabs | ALL, PRE-MARKET, OPEN/15M, LIVE, CLOSE | 5-Tab Selector | Frontend State | `phaseFilter` | Instant | Filtered table rows |
| Prediction Capture Time | Time | Time String | Evaluation Ledger | `evaluation_records[].captured_at` | Historical | "09:08 IST" |
| Session Phase | Phase | Enum Badge | Evaluation Ledger | `evaluation_records[].phase` | Historical | "PRE_MARKET", "LIVE_INTRADAY" |
| Metric & Field Name | Metric & Field | String | Evaluation Ledger | `evaluation_records[].metric` | Historical | "Expected Open", "Support 1", "PCR" |
| Ardha Predicted Value | Ardha Value | String / Number | Evaluation Ledger | `evaluation_records[].ardha_value` | Historical | "24,850.00" |
| Real Market Outcome Value | Real Value | String / Number | Market Ingest Reconciler | `evaluation_records[].real_value` | EOD evaluation | "24,848.20" / "--" |
| Evaluation Outcome Badge | HIT / NEAR / MISS / PENDING | Enum Badge | Verification Rule | `evaluation_records[].result` | EOD evaluation | Color-coded status badge |
| Error Delta Points / % | Error Delta | Float / Points | Verification Rule | `evaluation_records[].error_value` | EOD evaluation | "1.80 pts (0.01%)" |
| Evaluation Notes & Verification Rule | Notes & Rule | String | Verification Rule | `evaluation_records[].notes` | EOD evaluation | Explicit tolerance rule applied |
