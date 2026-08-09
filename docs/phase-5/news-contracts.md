# news_intelligence canonical contracts

This document outlines the canonical domain models defined in Phase 5.2 to isolate media news headlines from macro schedule events and corporate corporate filings.

## 1. NewsItem Contract

Represents standard media-sourced news stories (e.g. from Google News RSS search) or direct publisher stories.

| Field | Type | Description |
|---|---|---|
| `id` | `str` | Deterministic MD5 hash of `headline` and `discovery_url` |
| `headline` | `str` | Cleaned headline text |
| `summary_snippet` | `str` | Short descriptive summary snippet |
| `source_name` | `str` | Original author publisher (e.g. Economic Times) |
| `source_type` | `str` | `"official"` or `"media"` |
| `original_url` | `str` | Final destination URL after resolving redirects |
| `discovery_url` | `str` | The URL discovery route |
| `discovered_via` | `str` | The ingestion provider ID |
| `published_at` | `str` | Publication timestamp |
| `received_at` | `str` | Time of download |
| `age_seconds` | `int` | Time since publication |
| `freshness_status` | `str` | `"fresh"`, `"stale"`, or `"unavailable"` |
| `quality_status` | `str` | `"high"`, `"medium"`, or `"low"` |
| `verification_status`| `str` | `"confirmed"`, `"developing"`, `"unverified"` |
| `category` | `str` | EventClassifier category (e.g. RBI, Earnings) |
| `affected_symbols` | `list[str]`| Affected stock constituent symbols |
| `affected_sectors` | `list[str]`| Affected sectors |
| `nifty_relevance_score`| `float` | Relevance to NIFTY (0.0 to 10.0 scale) |
| `expected_direction` | `str` | `"positive"`, `"negative"`, `"mixed"`, `"uncertain"`, `"not_assessed"` |
| `impact_strength` | `str` | `"high"`, `"medium"`, or `"low"` |
| `impact_duration` | `str` | `"intraday"`, `"daily"`, or `"weekly"` |
| `confidence` | `float` | Heuristic confidence parameter |
| `duplicate_group_id` | `str \| None`| Group ID matching duplicate items |
| `warnings` | `list[str]`| Execution anomalies or duplicate notices |

---

## 2. ScheduledEvent Contract

Represents scheduled macroeconomic releases (CPI releases, Fed policy meetings).

| Field | Type | Description |
|---|---|---|
| `id` | `str` | Deterministic stable event ID |
| `event_name` | `str` | The macro metric name |
| `description` | `str` | Explanation of the event |
| `scheduled_at` | `str` | Execution time |
| `importance` | `str` | `"low"`, `"medium"`, `"high"`, or `"critical"` |
| `source_name` | `str` | Authoritative source publisher (e.g. MOSPI, Fed) |
| `verification_status`| `str` | `"confirmed"` or `"developing"` |
| `category` | `str` | Macro category |
| `expected_direction` | `str` | expected sentiment direction |
| `relevance_score` | `float` | NIFTY relevance scale |
| `status` | `str` | `"upcoming"` or `"completed"` |

---

## 3. CorporateAnnouncement Contract

Represents company-specific exchange filings, board meetings, and results.

| Field | Type | Description |
|---|---|---|
| `id` | `str` | Deterministic stable ID |
| `company_symbol` | `str` | stock ticker |
| `announcement_type` | `str` | `"earnings"`, `"dividend"`, `"board_meeting"`, `"action"` |
| `headline` | `str` | clean title |
| `description` | `str` | filing details |
| `published_at` | `str` | publication timestamp |
| `source_name` | `str` | Exchange platform (e.g. NSE, BSE) |
| `original_url` | `str` | direct PDF filing link |
| `verification_status`| `str` | `"confirmed"` |
| `nifty_relevance_score`| `float` | relevance scale |
| `expected_direction` | `str` | expected direction |
