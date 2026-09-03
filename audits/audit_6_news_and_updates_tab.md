# News & Updates Tab — Full E2E Forensic Audit

### 1. Summary

A comprehensive, read-only forensic audit was conducted across the entire **News & Updates** workspace ([NewsWorkspace.tsx](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/news/NewsWorkspace.tsx)) and its three secondary subtabs:
1. **Live News Feed** ([LiveNewsFeedView.tsx](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/news/LiveNewsFeedView.tsx) / [LiveNewsTab.tsx](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/news/LiveNewsTab.tsx))
2. **Catalysts Matrix** ([CatalystsMatrixView.tsx](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/news/CatalystsMatrixView.tsx) / [CatalystsTab.tsx](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/news/CatalystsTab.tsx))
3. **Economic Calendar** ([EconomicCalendarView.tsx](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/news/EconomicCalendarView.tsx) / [CalendarTab.tsx](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/news/CalendarTab.tsx))

Additionally, the centralized canonical news adapter ([canonicalNewsAdapter.ts](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/utils/canonicalNewsAdapter.ts)) and the backend Python news ingestion engine ([src/news_engine/](file:///p:/ArdhaMind-Local/ardhamind/staging/src/news_engine/)) were investigated end-to-end.

The audit revealed **3 Critical**, **4 High**, **4 Medium**, and **4 Low** severity defects. While the workspace boasts a modern, dense Bloomberg-style UI with responsive filtering and zero broker execution risk, the data pipeline harbors synthetic fallback data disguised as live items, property mapping bugs that break the Catalysts subtab, and aggressive deduplication algorithms that silently drop valid news:
- In `canonicalNewsAdapter.ts`, when backend feeds are empty or initializing, the system falls back to `defaultStories` (15 completely fabricated news articles). The adapter dynamically computes synthetic relative timestamps (`Date.now() - minutesAgo * 60 * 1000`) so that these fake stories appear freshly discovered (e.g. "18 minutes ago", "37 minutes ago").
- In `CatalystsMatrixView.tsx`, the component queries `pres?.stories`, but the presentation state interface defines `liveFeed`. Because `pres.stories` is always undefined, both Market Upside Tailwinds and Downside Risks always evaluate to empty arrays, causing the Catalysts subtab to permanently display "Awaiting Ingestion".
- In `canonicalNewsAdapter.ts`, 65 static economic calendar events spanning August to September 2026 are hardcoded into the client-side adapter and served as the default calendar.
- The deduplication algorithm slices headlines to 30 characters (`headline.toLowerCase().slice(0, 30)`), which collides distinct articles that share similar prefixes and silently drops valid news stories.

| Severity | Finding Count | Primary Impact Area |
| :--- | :---: | :--- |
| **Critical** | **3** | Synthetic news generation with dynamic fake timestamps, broken Catalysts data binding (`pres.stories` vs `liveFeed`), 65 hardcoded calendar events |
| **High** | **4** | Hardcoded 5-factor macro ribbon, 30-char headline slice deduplication data loss, primitive regex keyword sentiment, hardcoded session date reference |
| **Medium** | **4** | Canned fallback transmission explanations, backend `provider_manager.py` mock data residue, hidden test assertion scaffold in DOM, cross-tab sentiment discrepancies |
| **Low** | **4** | Fixed top drivers and carry-forward risks in adapter, simulated provider health timestamps, default pipeline latency fallback, lack of DOM list virtualization |
| **Total** | **15** | |

---

### Complete Feed Inventory & Data Source Mapping

Every news feed element, macro metric, catalyst, and calendar event across all 3 subtabs is mapped below:

| UI Element / Metric | View / Location | Underlying Source / Field | Ingestion & Processing Method | Reality: Live vs Hardcoded |
| :--- | :--- | :--- | :--- | :--- |
| **Live News Stories** | Live News / Feed | `news_sentiment.items` or `news_intelligence.items` | Google News RSS & Official Feeds (300s) | Dynamic OR **15 Fallback Fake Stories** |
| **Story Relative Timestamp** | Live News / Row | `publishedAt` / `observedAt` | `formatNewsTimestamp` with IST conversion | Dynamic OR **Dynamic Fake Offset** |
| **Story Sentiment Pill** | Live News / Row | `expectedDirection` / `impactStrength` | Regex Keyword Matching on Headline | Derived Heuristic |
| **Why It Matters / Transmission** | Live News / Row | `item.transmission_summary` | Backend LLM/Rules OR Canned Strings | Dynamic / Canned Fallback |
| **Market News Tone (Strip)** | Live News / Ribbon | `pres.liveFeed` aggregate | `reduce(sum of +1 / -1 / 0)` | Dynamic Derived Metric |
| **Catalysts Count (Strip)** | Live News / Ribbon | `pres.liveFeed` aggregate | Count of stories with `impactStrength === "HIGH"` | Dynamic Derived Metric |
| **Lead Sector (Strip)** | Live News / Ribbon | `canonicalEnvelope.market.sectors` | Sorted max `change_percent` across sectors | Real-Time NSE Sector Feed |
| **Next Event (Strip)** | Live News / Ribbon | `pres.calendarEvents` | Nearest future event based on `sessionRefTime` | Dynamic / Fallback Calendar |
| **Event Risk (Strip)** | Live News / Ribbon | Single Source `vix.last_price` | Threshold check (`VIX > 15` or High Impact Event) | Dynamic Derived Metric |
| **Pipeline Status (Strip)** | Live News / Ribbon | `pres.providerHealthList` | `healthList.every(status === "HEALTHY")` | Dynamic Health State |
| **5-Factor Macro Forces Ribbon**| Catalysts / Ribbon | Hardcoded in `CatalystsMatrixView.tsx` | Static array of 5 macro objects | **COMPLETELY HARDCODED** |
| **Market Upside Tailwinds** | Catalysts / Ledger | `pres?.stories` (Bug: should be `liveFeed`) | Filtered `expectedDirection === "POSITIVE"` | **BROKEN / PERMANENTLY EMPTY** |
| **Downside Vulnerabilities** | Catalysts / Ledger | `pres?.stories` (Bug: should be `liveFeed`) | Filtered `expectedDirection === "NEGATIVE"` | **BROKEN / PERMANENTLY EMPTY** |
| **Economic Calendar Events** | Calendar / Table | `macro_intelligence.economic_events` | MoSPI / Central Banks OR Default Array | Dynamic OR **65 Hardcoded Events** |
| **Event Impact & Surprise** | Calendar / Row | `actualSurprise`, `impact` | Math comparison of actual vs consensus | Dynamic / Static Metadata |
| **NIFTY Reaction Matrix** | Calendar / Modal | `ev.reactionMatrix` | Curated economic rule-base / backend | Static Invariant Metadata |

---

### 2. Forensic Findings by Dimension (1–13)

```
================================================================================
DIMENSION 1: FEED INVENTORY & DATA SOURCE FIDELITY
================================================================================
```

#### Finding 1.1: Fake Synthetic News Feed Generated in Adapter When Feed is Empty
* **File & Lines:** [src/frontend/utils/canonicalNewsAdapter.ts:484-532, 899](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/utils/canonicalNewsAdapter.ts#L484-L532)
* **Actual Code:**
  ```typescript
  const nowMs = Date.now();
  const makeNewsTime = (minutesAgo: number) => {
    const iso = new Date(nowMs - minutesAgo * 60 * 1000).toISOString();
    return { iso, fmt: formatNewsTimestamp(iso) };
  };

  const nt1 = makeNewsTime(18);
  const nt2 = makeNewsTime(37);
  ...
  const defaultStories: CanonicalNewsStory[] = [
    {
      id: "NEWS-01",
      headline: "Wall St Week Ahead: Jobs Report & Broadcom Results Set Tone for Global Tech",
      publisher: "Reuters",
      provider: "Google News RSS",
      publishedAt: nt1.iso,
      ...
    },
    ...
  ];

  const liveFeed: CanonicalNewsStory[] = processedStories.length > 0 ? processedStories : defaultStories;
  ```
* **Why it is wrong:** When the backend news engine returns no items (e.g. network timeout, cold start, or empty state), `canonicalNewsAdapter.ts` does not display an awaiting-data or empty state. Instead, it serves 15 hardcoded fake articles (`defaultStories`) and uses `makeNewsTime(minutesAgo)` to forge publication timestamps relative to `Date.now()`. This directly violates the absolute safety invariant prohibiting the fabrication of market data and synthetic replacements.
* **Severity:** **Critical**

#### Finding 1.2: Property Mismatch in Catalysts Matrix Causes Total Blank State
* **File & Lines:** [src/frontend/components/news/CatalystsMatrixView.tsx:120, 142](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/news/CatalystsMatrixView.tsx#L120)
* **Actual Code:**
  ```tsx
  const upsideTailwinds: CatalystDetailItem[] = useMemo(() => {
    const stories = pres?.stories || [];
    const positive = stories.filter((s) => s.expectedDirection === "POSITIVE");
    ...
  }, [pres?.stories]);

  const downsideRisks: CatalystDetailItem[] = useMemo(() => {
    const stories = pres?.stories || [];
    const negative = stories.filter((s) => s.expectedDirection === "NEGATIVE" || s.expectedDirection === "MIXED");
    ...
  }, [pres?.stories]);
  ```
* **Why it is wrong:** `NewsPresentationState` (defined in `canonicalNewsAdapter.ts:156`) exposes `liveFeed: CanonicalNewsStory[]` and contains no `stories` property. Because `pres?.stories` is always undefined, `upsideTailwinds` and `downsideRisks` always evaluate to empty arrays (`[]`). The Catalysts subtab permanently renders "Awaiting Catalysts Tailwinds Ingestion" and "Awaiting Catalysts Downside Risks Ingestion", completely breaking the subtab even when real stories are ingested.
* **Severity:** **Critical**

#### Finding 1.3: 65 Static Hardcoded Economic Calendar Events Pinned to August/September 2026
* **File & Lines:** [src/frontend/utils/canonicalNewsAdapter.ts:1047-2430](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/utils/canonicalNewsAdapter.ts#L1047-L2430)
* **Actual Code:**
  ```typescript
  const defaultEvents: CanonicalEconomicEvent[] = [
    // ── 28 AUG 2026 (TODAY / ACTIVE SESSION) ──
    {
      id: "EVT-01",
      date: "28 Aug 2026",
      timeIST: "08:30 AM",
      rawTimestamp: "2026-08-28T03:00:00.000Z",
      eventName: "Japan Tokyo Core CPI YoY",
      ...
    },
    ...
    // ── 18 SEP 2026 ──
    {
      id: "EVT-65",
      date: "18 Sep 2026",
      timeIST: "04:30 PM",
      rawTimestamp: "2026-09-18T11:00:00.000Z",
      eventName: "Bank of England (BOE) Bank Rate Decision",
      ...
    }
  ];

  const calendarEvents: CanonicalEconomicEvent[] = processedEvents.length > 0 ? processedEvents : defaultEvents;
  ```
* **Why it is wrong:** 65 complete economic events are hardcoded into the client-side adapter with fixed dates in August and September 2026. If the backend economic calendar feed fails or returns empty data, the frontend serves this stale, invariant calendar indefinitely.
* **Severity:** **Critical**

```
================================================================================
DIMENSION 2: REAL-TIME PIPELINE
================================================================================
```

#### Finding 2.1: Aggressive 30-Character Headline Truncation Causes Silent Deduplication Data Loss
* **File & Lines:** [src/frontend/utils/canonicalNewsAdapter.ts:442-449](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/utils/canonicalNewsAdapter.ts#L442-L449)
* **Actual Code:**
  ```typescript
  const dupKey = headline.toLowerCase().slice(0, 30);
  const dupGroupId = item.duplicate_group_id || `GRP-${dupKey}`;

  if (dedupGroupMap.has(dupGroupId)) {
    dedupGroupMap.set(dupGroupId, (dedupGroupMap.get(dupGroupId) || 1) + 1);
  } else {
    dedupGroupMap.set(dupGroupId, 1);
    processedStories.push({ ... });
  }
  ```
* **Why it is wrong:** Deduplicating articles based on only the first 30 characters of their headline (`slice(0, 30)`) is overly aggressive. Distinct articles that begin with standard news wire boilerplate (e.g. `"US Federal Reserve announces in..."` vs `"US Federal Reserve signals fut..."`, or `"RBI Monetary Policy Committee m..."` vs `"RBI Monetary Policy Committee k..."`) share the identical 30-character prefix and are silently dropped as duplicates.
* **Severity:** **High**

```
================================================================================
DIMENSION 3: CALCULATED FIELDS
================================================================================
```

#### Finding 3.1: Primitive Regex Keyword Matching for Sentiment Direction
* **File & Lines:** [src/frontend/utils/canonicalNewsAdapter.ts:395-412](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/utils/canonicalNewsAdapter.ts#L395-L412)
* **Actual Code:**
  ```typescript
  const isBullishHeuristic = /\b(surge|surges|surged|surging|rally|rallies|rallied|rallying|gain|gains|gained|gaining|jump|jumps|jumped|jumping|record|soar|soars|soared|soaring|outperform|outperforms|outperformed|beat|beats|beaten|bullish|vanguard|inflow|inflows|expansion|expand|support|supportive|strengthen|rise|rises|rose|rising|up|advance|advances|advanced|advancing|climb|climbs|climbed|climbing|high|higher|highest|recovery|rebound|positive)\b/i.test(headline);
  const isBearishHeuristic = /\b(crash|crashes|crashed|plunge|plunges|plunged|drop|drops|dropped|slump|slumps|slumped|decline|declines|declined|drag|drags|dragged|loss|losses|bearish|selloff|panic|downgrade|downgrades|fall|falls|fell|falling|down|lower|lowest|negative|weak|weakness|plummets|plummeted)\b/i.test(headline);
  ```
* **Why it is wrong:** Story sentiment direction is derived through crude regex keyword pattern matching against the headline. For instance, the arbitrary word `"vanguard"` unconditionally flags a story as bullish, while headlines discussing "drop in inflation" or "decline in oil prices" are mistakenly classified as bearish (`NEGATIVE`) despite being market-positive. Negations ("fails to rally", "not expected to rise") are completely missed.
* **Severity:** **High**

```
================================================================================
DIMENSION 4: MARKET STATE HANDLING
================================================================================
```

#### Finding 4.1: Hardcoded Session Reference Date Pinned to August 28, 2026
* **File & Lines:** [src/frontend/utils/canonicalNewsAdapter.ts:984](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/utils/canonicalNewsAdapter.ts#L984), [src/frontend/components/news/EconomicCalendarView.tsx:52-56](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/news/EconomicCalendarView.tsx#L52-L56)
* **Actual Code:**
  ```typescript
  // canonicalNewsAdapter.ts:984
  const sessionRef = new Date("2026-08-28T10:00:00.000Z"); // 28 Aug 2026 15:30:00 IST

  const isToday = evDate.toDateString() === sessionRef.toDateString();
  const isFuture = evDate.getTime() > sessionRef.getTime();
  ```
* **Why it is wrong:** The calendar event processor hardcodes a static reference date (`2026-08-28T10:00:00.000Z`). When the application is operated on any subsequent trading date, the adapter continues evaluating `isToday` and `isFuture` relative to August 28, 2026, causing current calendar events to be miscategorized as historical or completed.
* **Severity:** **High**

```
================================================================================
DIMENSION 5: TIMESTAMP & TIMEZONE
```

* **Audit Result:** Dynamic articles properly use `formatNewsTimestamp` to format UTC timestamps into IST (`en-IN` timezone). However, this is undermined by **Finding 1.1**, where synthetic timestamps are programmatically generated to falsify recency.

```
================================================================================
DIMENSION 6: CROSS-TAB CONSISTENCY
================================================================================
```

#### Finding 6.1: Cross-Tab Tone & Sentiment Score Discrepancies
* **File & Lines:** [src/frontend/components/news/LiveNewsFeedView.tsx:121-133](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/news/LiveNewsFeedView.tsx#L121-L133), [src/frontend/components/canonical/MarketPulseWorkspace.tsx:210](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/canonical/MarketPulseWorkspace.tsx#L210)
* **Actual Code:**
  ```tsx
  // LiveNewsFeedView.tsx
  const netTone = useMemo(() => {
    return pres.liveFeed.reduce((acc, item) => {
      return acc + (item.expectedDirection === "POSITIVE" ? 1 : item.expectedDirection === "NEGATIVE" ? -1 : 0);
    }, 0);
  }, [pres.liveFeed]);
  const toneDisplay = `${netTone > 0 ? "+" : ""}${netTone} (${toneLabel})`;
  ```
* **Why it is wrong:** The Live News ribbon displays a discrete integer score (`+4 (POS)`, `-2 (NEG)`), whereas the Metrics tab (Tier 2 Sentiment) displays an aggregate percentage score (e.g. `68% Bullish`), and Market Intelligence displays qualitative strings (`BALANCED CUES`). There is no parity or normalized metric shared across tabs.
* **Severity:** **Medium**

```
================================================================================
DIMENSION 7: FORMATTING
```

* **Audit Result:** Verified clean. Headlines cleanly truncate via CSS `line-clamp-2`, badges maintain compact padding, and monospace numeric formatting is strictly preserved across timestamps and change percentages.

```
================================================================================
DIMENSION 8: ERROR HANDLING & FALLBACKS
```

#### Finding 8.1: Canned Fallback Transmission Sentences Interpolated as Macro Explanations
* **File & Lines:** [src/frontend/utils/canonicalNewsAdapter.ts:423-435](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/utils/canonicalNewsAdapter.ts#L423-L435)
* **Actual Code:**
  ```typescript
  } else if (lowerHeadline.includes("tech") || category === "IT_TECH") {
    whyItMatters = "Transmits to US tech risk appetite, NASDAQ momentum, and Indian IT exporters (INFY, TCS).";
  } else if (lowerHeadline.includes("gdp") || category === "BANKING_FINANCIALS") {
    whyItMatters = "Transmits to domestic yield curve, interbank liquidity, and Banking/Financials.";
  } else if (lowerHeadline.includes("crude") || category === "ENERGY") {
    whyItMatters = "Transmits to domestic inflation expectations, refining margins, and Oil & Gas constituents.";
  }
  ```
* **Why it is wrong:** If an article arrives without a dedicated transmission summary, the adapter does not leave it null or acknowledge missing transmission data. Instead, it generates canned boilerplate sentences based on simple keyword triggers.
* **Severity:** **Medium**

```
================================================================================
DIMENSION 9: LOADING STATES
```

* **Audit Result:** Verified clean. Subtabs render dedicated empty state containers (`Awaiting Catalysts Tailwinds Ingestion`, `Awaiting Live News Wire Ingestion`) rather than freezing or leaving orphaned spinners.

```
================================================================================
DIMENSION 10: UI/LAYOUT & RESPONSIVE INTEGRITY
```

* **Audit Result:** Verified clean. The 70/30 dominant wire cockpit collapses smoothly into a stacked layout on viewports under 1024px. The modal inspection dialogs (`CatalystsMatrixView` and `EconomicCalendarView`) render with fixed `z-50` overlays and handle the `Escape` key cleanly.

```
================================================================================
DIMENSION 11: DEAD CODE & MOCK-DATA RESIDUE
```

#### Finding 11.1: Completely Hardcoded 5-Factor Macro Forces Ribbon in Catalysts Matrix
* **File & Lines:** [src/frontend/components/news/CatalystsMatrixView.tsx:69-117](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/news/CatalystsMatrixView.tsx#L69-L117)
* **Actual Code:**
  ```tsx
  const macroForces = useMemo(() => {
    return [
      { id: "force-1", num: 1, name: "RBI Liquidity & Stance", state: "SUPPORTIVE", impact: "High", stateColor: "text-emerald-400", ... },
      { id: "force-2", num: 2, name: "US & Global Markets", state: "MONITORED", impact: "High", stateColor: "text-emerald-400", ... },
      { id: "force-3", num: 3, name: "Institutional Flows", state: "FLOW TRACKED", impact: "High", stateColor: "text-emerald-400", ... },
      { id: "force-4", num: 4, name: "Crude Oil & Energy", state: "MARGIN STABILITY", impact: "Med", stateColor: "text-amber-400", ... },
      { id: "force-5", num: 5, name: "USD / INR & FX", state: "CONSTRUCTIVE", impact: "Med", stateColor: "text-emerald-400", ... },
    ];
  }, []);
  ```
* **Why it is wrong:** The top horizontal macro ribbon in the Catalysts subtab is completely hardcoded in JSX. It displays static states ("SUPPORTIVE", "MONITORED", "FLOW TRACKED", "MARGIN STABILITY", "CONSTRUCTIVE") that never update based on real market context.
* **Severity:** **High**

#### Finding 11.2: Backend Provider Manager Emits Static Mock Data from July 2026
* **File & Lines:** [src/news_engine/provider_manager.py:28-69, 75-100](file:///p:/ArdhaMind-Local/ardhamind/staging/src/news_engine/provider_manager.py#L28-L69)
* **Actual Code:**
  ```python
  class GoogleNewsProvider(BaseNewsProvider):
      def fetch_raw_news(self) -> List[Dict[str, Any]]:
          return [
              {
                  "id": "raw_g1",
                  "title": "RBI Keeps Interest Rates Unchanged at 6.5% amid Inflation Concerns",
                  "pubDate": "Fri, 10 Jul 2026 09:15:00 GMT",
                  ...
              },
              ...
          ]
  ```
* **Why it is wrong:** The backend `provider_manager.py` contains default mock implementations of `GoogleNewsProvider` and `MacroCalendarProvider` that return hardcoded articles from July 2026 instead of raising an error or enforcing live RSS fetching.
* **Severity:** **Medium**

#### Finding 11.3: Hidden Test Assertion Scaffold Embedded in Workspace DOM
* **File & Lines:** [src/frontend/components/news/NewsWorkspace.tsx:44-53](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/news/NewsWorkspace.tsx#L44-L53)
* **Actual Code:**
  ```tsx
  {/* Hidden Hook for Test Contract Assertions */}
  <div className="hidden" aria-hidden="true">
    <span>NEWS &amp; UPDATES</span>
    <span>LIVE NEWS</span>
    <span>CATALYSTS</span>
    <span>CALENDAR</span>
    <span>MARKET NEWS TONE</span>
    <span>HIGH IMPACT STORIES</span>
    <span>MOST AFFECTED SECTOR</span>
  </div>
  ```
* **Why it is wrong:** A hidden DOM container (`aria-hidden="true"`) exists solely to render specific hardcoded text strings so that automated unit tests or contract assertion suites pass, even if the active UI fails to render them.
* **Severity:** **Medium**

#### Finding 11.4: Fixed Top Drivers and Carry-Forward Risks in Adapter
* **File & Lines:** [src/frontend/utils/canonicalNewsAdapter.ts:2439-2460](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/utils/canonicalNewsAdapter.ts#L2439-L2460)
* **Actual Code:**
  ```typescript
  const topDrivers = [
    { rank: 1, name: "RBI Liquidity & Interbank Yields", state: "SUPPORTIVE", impact: "HIGH", ... },
    { rank: 2, name: "US Inflation & Fed Rate Outlook", state: "POSITIVE", impact: "HIGH", ... },
    ...
  ];
  const carryForwardRisks = [
    { title: "Derivatives Concentration Barrier", detail: "Heavy Call OI at 24,500 acts as immediate intraday resistance.", riskLevel: "RED" },
    ...
  ];
  ```
* **Why it is wrong:** Hardcoded strike barriers (`"Heavy Call OI at 24,500"`) and driver states are hardcoded directly into the adapter return structure.
* **Severity:** **Low**

#### Finding 11.5: Simulated Provider Health List with Statically Claimed Latencies
* **File & Lines:** [src/frontend/utils/canonicalNewsAdapter.ts:974-979](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/utils/canonicalNewsAdapter.ts#L974-L979)
* **Actual Code:**
  ```typescript
  const providerHealthList: ProviderHealthItem[] = [
    { providerName: "Official RBI Feed", publisherLabel: "Reserve Bank of India", isOfficial: true, status: "HEALTHY", lastSuccessTime: "17:15 IST", itemCount: 1 },
    { providerName: "SEBI Official RSS", publisherLabel: "SEBI Press Releases", isOfficial: true, status: "HEALTHY", lastSuccessTime: "14:25 IST", itemCount: 1 },
    { providerName: "Google News RSS", publisherLabel: "Reuters / Bloomberg / ET", isOfficial: false, status: "HEALTHY", lastSuccessTime: "Just now", itemCount: liveFeed.length },
    { providerName: "NSE Macro Telemetry", publisherLabel: "NSE India Official", isOfficial: true, status: "HEALTHY", lastSuccessTime: "16:30 IST", itemCount: rawEvents.length },
  ];
  ```
* **Why it is wrong:** Provider health statuses and last success times (`"17:15 IST"`, `"14:25 IST"`) are hardcoded defaults rather than real telemetry fetched from backend provider health monitors.
* **Severity:** **Low**

#### Finding 11.6: Default Pipeline Latency Fallback (0.2s)
* **File & Lines:** [src/frontend/components/news/LiveNewsFeedView.tsx:205](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/news/LiveNewsFeedView.tsx#L205)
* **Actual Code:**
  ```tsx
  const latency = state?.pipeline_latency || state?.latency_ms ? `${(state?.latency_ms ?? 200) / 1000}s` : "0.2s";
  ```
* **Why it is wrong:** Hardcodes `0.2s` as the fallback latency instead of rendering `—` or an explicit awaiting-telemetry indicator.
* **Severity:** **Low**

```
================================================================================
DIMENSION 12: PERFORMANCE & MEMORY
================================================================================
```

#### Finding 12.1: Absence of DOM Virtualization for Large Feed Sizes
* **File & Lines:** [src/frontend/components/news/LiveNewsFeedView.tsx:380-450](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/news/LiveNewsFeedView.tsx#L380-L450), [src/frontend/components/news/EconomicCalendarView.tsx:180-280](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/news/EconomicCalendarView.tsx#L180-L280)
* **Actual Code:**
  Both `LiveNewsFeedView` and `EconomicCalendarView` render their full arrays directly into scrollable `div` containers without virtual scrolling (e.g. `react-window`).
* **Why it is wrong:** While adequate for small feeds (20–40 items), when feeds accumulate 100+ articles or economic events, rendering unvirtualized DOM nodes increases DOM memory footprint and slows layout passes during live ticks.
* **Severity:** **Low**

```
================================================================================
DIMENSION 13: CONSOLE & NETWORK HYGIENE
```

* **Audit Result:** Verified clean. Zero API keys are leaked in client payloads (Google News RSS is public and unauthenticated). External Google Search links safely encode query parameters via `encodeURIComponent`. No unhandled console exceptions occur.

---

### 3. Verified Clean

The following items were explicitly audited and verified to be clean of defects:

* **Read-Only Safety Invariant:** Verified clean. Zero order routing, broker mutation, or execution endpoints are reachable from any News & Updates component.
* **External Link Sanitization:** Verified clean. All article outgoing links include `rel="noopener noreferrer"` and safely open in external tabs without leaking window credentials.
* **Live Sector Telemetry Synchronization:** Verified clean. In `LiveNewsFeedView.tsx:97-114`, the Lead Sector indicator directly reads real-time sector percentages from `canonicalEnvelope.market.sectors`, accurately reflecting live NSE market movers.
* **Clean UI Clamping & Line Hygiene:** Verified clean. Headlines and summary snippets use strict CSS line clamping (`line-clamp-2`, `line-clamp-3`), preventing layout overflow across diverse resolutions.
* **Absence of Memory Leaks:** Verified clean. Keydown event listeners for modal dismissal (`Escape` key) in `CatalystsMatrixView` and `EconomicCalendarView` properly clean up on component unmount.
* **Public Feed Privacy:** Verified clean. No Kite session tokens, brokerage credentials, or user identifiers are included in RSS request headers or query parameters.
