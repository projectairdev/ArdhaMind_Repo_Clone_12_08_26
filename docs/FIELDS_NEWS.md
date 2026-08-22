# AIR Ardha Staging — News & Updates Data-Field Inventory

**Surface:** `News & Updates Workspace` (`NewsWorkspace.tsx`, `LiveNewsTab.tsx`, `CatalystsTab.tsx`, `CalendarTab.tsx`)  
**Environment:** Staging (`staging.ardhamind.projectair.in`)  
**Audit Date:** August 2026  
**Scope:** Complete visible data fields across Top Secondary Sub-tab Bar, Summary Strip, Live News Feed (Top Story, Feed Items, Modals), Catalysts View (Drivers, Positive/Negative/Regulatory/Carry-Forward), and Economic & Corporate Calendar.

---

## 1. TOP SUMMARY STRIP & ALERT BANNER (`NewsWorkspace.tsx` & `LiveNewsTab.tsx`)

| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| Market News Tone | MARKET NEWS TONE | Enum/Badge | Sentiment Pipeline | `pres.marketTone` | Continuous evaluation | "POSITIVE" / "NEUTRAL" |
| High Impact Stories Count | HIGH IMPACT | Integer | News Ingestion Pipeline | `pres.highImpactCount` | Real-time stream | "4 Active" |
| Direction Breakdown: Positive | POS | Integer | Sentiment Pipeline | `pres.positiveCount` | Real-time stream | "12 POS" |
| Direction Breakdown: Negative | NEG | Integer | Sentiment Pipeline | `pres.negativeCount` | Real-time stream | "4 NEG" |
| Direction Breakdown: Neutral | NEU | Integer | Sentiment Pipeline | `pres.neutralCount` | Real-time stream | "8 NEU" |
| Direction Segmented Fill Bar | News Sentiment Bar | Visual Bar | Sentiment Pipeline | Segmented ratio bar | Real-time stream | Colored percentage bar |
| Most Affected Sector | MOST AFFECTED SECTOR | String | Categorization Engine | `pres.mostAffectedSector` | Real-time stream | "BANKING" / "IT" |
| Next Major Event: Time & Region | NEXT MAJOR EVENT | String | Macro Calendar | `pres.nextMajorEvent.timeIST` | Real-time schedule | "17:30 (INDIA)" / "—" |
| Next Major Event: Name | Event Name | String | Macro Calendar | `pres.nextMajorEvent.eventName` | Real-time schedule | "India CPI Inflation YoY" |
| Overall News Risk Level | NEWS RISK | Enum/Badge | Risk Model | `pres.newsRisk` | Continuous evaluation | "ELEVATED" / "LOW" |
| Bottom Alert Banner Event | NEWS ALERT | String | News Engine | `pres.nextMajorEvent.eventName` | Continuous evaluation | "Next High Impact: ..." |

---

## 2. LIVE NEWS FEED SUB-TAB (`LiveNewsTab.tsx`)

### Feed Filters & Controls
| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| Filter Button Group | ALL / HIGH IMPACT / POSITIVE / NEGATIVE / OFFICIAL / EARNINGS / MACRO | Filter Buttons | Frontend State | `filterType` | User click | "ALL" default |
| Search Input Box (Modal) | Search headlines... | Search Input | Frontend State | `searchQuery` | User input | Real-time client filter |

### Top Story Card (Lead Anchor)
| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| Top Story: Headline | Headline Text | String | News Ingestion Engine | `pres.topStory.headline` | Real-time stream | Highest impact headline |
| Top Story: Publisher | Publisher Name | String | News Ingestion Engine | `pres.topStory.publisher` | Real-time stream | "Reuters" / "Bloomberg" |
| Top Story: Published Time | Published Time IST | Time String | News Ingestion Engine | `pres.topStory.publishedTimeIST` | Real-time stream | "10:14 IST" |
| Top Story: Discovery Time | Discovery Latency | String | News Ingestion Engine | `pres.topStory.displayRowTime` | Real-time stream | "Discovered 2m ago" |
| Top Story: Impact Badge | IMPACT STRENGTH | Enum/Badge | Impact Scorer | `pres.topStory.impactStrength` | Real-time stream | "HIGH IMPACT" |
| Top Story: Expected Direction | DIRECTION | Enum/Badge | Sentiment Scorer | `pres.topStory.expectedDirection` | Real-time stream | "POSITIVE ↑" / "NEGATIVE ↓" |
| Top Story: Why It Matters | WHY THIS MATTERS | String | AI/Deterministic Synthesis | `pres.topStory.whyItMatters` | Real-time stream | Grounded rationale text |
| Top Story: Affected Sectors | AFFECTED SECTORS | Array<String> | Entity Extraction | `pres.topStory.affectedSectors[]` | Real-time stream | Sector badges |
| Top Story: Affected Companies | AFFECTED EQUITIES | Array<String> | Entity Extraction | `pres.topStory.affectedCompanies[]` | Real-time stream | Equity badges |
| Top Story: Official Verification | VERIFIED SOURCE | Badge | Source Verifier | `pres.topStory.isOfficialSource` | Real-time stream | Shield badge / "OFFICIAL" |

### News Items Feed (Chronological Stream)
| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| Feed Item: Rank / ID | # | Integer | Feed Pipeline | `story.id` | Stream order | List index |
| Feed Item: Headline | Headline | String | Feed Pipeline | `story.headline` | Real-time stream | Headline text |
| Feed Item: Publisher | Publisher | String | Feed Pipeline | `story.publisher` | Real-time stream | Source publisher |
| Feed Item: Timestamp | Time IST / Ago | String | Feed Pipeline | `story.displayRowTime` | Real-time stream | "4m ago" / "09:42 IST" |
| Feed Item: Impact Strength | Impact | Enum/Badge | Impact Scorer | `story.impactStrength` | Real-time stream | "HIGH" / "MEDIUM" / "LOW" |
| Feed Item: Direction | Tone | Enum/Arrow | Sentiment Scorer | `story.expectedDirection` | Real-time stream | "POSITIVE" / "NEGATIVE" |
| Feed Item: Category | Category | Enum | Categorization Engine | `story.category` | Real-time stream | "RBI_MONETARY" / "CORPORATE" |
| Feed Item: Source Link | Original URL | URL Link | News Pipeline | `story.sourceUrl` | Real-time stream | External link icon |
| Feed Item: Summary Snippet | Summary | String | News Pipeline | `story.summary` | Real-time stream | Brief description |

---

## 3. CATALYSTS SUB-TAB (`CatalystsTab.tsx`)

| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| Top Driver: Rank Number | Rank Badge | Integer | Catalyst Engine | `driver.rank` | Continuous | 1, 2, 3... |
| Top Driver: Impact Badge | IMPACT | Enum/Badge | Catalyst Engine | `driver.impact` | Continuous | "HIGH IMPACT" |
| Top Driver: Catalyst Name | Driver Title | String | Catalyst Engine | `driver.name` | Continuous | "US Fed Rate Trajectory" |
| Top Driver: Active State | STATE | String | Catalyst Engine | `driver.state` | Continuous | "ACTIVE_ACCELERATING" |
| Top Driver: Direction | DIRECTION | Enum/Badge | Catalyst Engine | `driver.direction` | Continuous | "POSITIVE" / "NEGATIVE" |
| Top Driver: Why It Matters | Why It Matters Text | String | Catalyst Engine | `driver.whyItMatters` | Continuous | Structured impact text |
| Positive Catalysts: Publisher | Publisher | String | News Engine | `story.publisher` | Real-time stream | Publisher name |
| Positive Catalysts: Headline | Headline | String | News Engine | `story.headline` | Real-time stream | Catalyst headline |
| Positive Catalysts: Why It Matters | Why It Matters | String | News Engine | `story.whyItMatters` | Real-time stream | Upside rationale |
| Negative Catalysts: Publisher | Publisher | String | News Engine | `story.publisher` | Real-time stream | Publisher name |
| Negative Catalysts: Headline | Headline | String | News Engine | `story.headline` | Real-time stream | Catalyst headline |
| Negative Catalysts: Why It Matters | Why It Matters | String | News Engine | `story.whyItMatters` | Real-time stream | Downside vulnerability text |
| Regulatory Catalysts: Publisher | Publisher | String | Official Feed Ingest | `story.publisher` | Real-time stream | "RBI" / "SEBI" / "MoF" |
| Regulatory Catalysts: Time | Time IST | Time String | Official Feed Ingest | `story.displayRowTime` | Real-time stream | "11:00 IST" |
| Regulatory Catalysts: Headline | Policy Headline | String | Official Feed Ingest | `story.headline` | Real-time stream | Official policy headline |
| Regulatory Catalysts: Summary | Policy Summary | String | Official Feed Ingest | `story.summary` | Real-time stream | Grounded regulatory text |
| Carry-Forward Risks: Title | Risk Title | String | Risk Model | `risk.title` | Session close | "Crude Oil Volatility" |
| Carry-Forward Risks: Risk Level | RISK LEVEL | Enum/Badge | Risk Model | `risk.riskLevel` | Session close | "RED" / "AMBER" |
| Carry-Forward Risks: Detail | Risk Detail | String | Risk Model | `risk.detail` | Session close | Overnight exposure narrative |

---

## 4. CALENDAR SUB-TAB (`CalendarTab.tsx`)

| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| Scheduled Releases Count | SCHEDULED RELEASES | Integer | Macro Calendar | `filteredEvents.length` | Session load | "12 Scheduled Releases" |
| Region Filter Controls | ALL / INDIA / US / GLOBAL | Button Group | Frontend State | `regionFilter` | User click | "ALL" default |
| Impact Filter Controls | ALL / HIGH ONLY | Button Toggle | Frontend State | `impactFilter` | User click | "ALL" default |
| Calendar Event: Date | DATE | Date String | Macro Calendar | `ev.date` | Static Schedule | "22 Aug 2026" |
| Calendar Event: Time IST | TIME IST | Time String | Macro Calendar | `ev.timeIST` | Static Schedule | "17:30 IST" |
| Calendar Event: Region | REGION | Enum/Badge | Macro Calendar | `ev.region` | Static Schedule | "INDIA" / "US" / "GLOBAL" |
| Calendar Event: Event Name | EVENT NAME | String | Macro Calendar | `ev.eventName` | Static Schedule | "India CPI Inflation YoY" |
| Calendar Event: Impact Severity | IMPACT | Enum/Badge | Macro Calendar | `ev.impact` | Static Schedule | "HIGH" / "MEDIUM" / "LOW" |
| Calendar Event: Release Status | STATUS | Enum/Badge | Macro Calendar | `ev.status` | Real-time update | "UPCOMING" / "COMPLETED" |
| Calendar Event: Previous Value | PREVIOUS | Number/String | Macro Calendar | `ev.previous` | Static Schedule | "5.08%" / "--" |
| Calendar Event: Consensus Forecast | CONSENSUS | Number/String | Macro Calendar | `ev.consensus` | Static Schedule | "4.80%" / "--" |
| Calendar Event: Actual Value | ACTUAL | Number/String | Macro Calendar | `ev.actual` | On release | "4.75%" / "--" |
