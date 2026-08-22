# AIR Ardha Staging — Dashboard Component-to-Field Map

**Environment:** Staging (`staging.ardhamind.projectair.in`)  
**Audit Date:** August 2026  
**Scope:** Exhaustive mapping from React Component file path to every rendered child component, container, section, and visible data field.

---

## 1. GLOBAL APPLICATION SHELL

### `src/frontend/layout/DashboardLayout.tsx` & `src/frontend/components/WorkstationTopBar.tsx`
- **Container Elements:**
  - Top Navigation Bar (`WorkstationTopBar`)
  - Primary Sidebar (`PRIMARY_MODULES`)
  - Sub-Tab Navigation Bar
  - Main Viewport (`<main>`)
  - Live Assistant Drawer Overlay (`LiveAssistantPanel`)
  - Settings Modal (`SettingsWorkspace`)
- **Rendered Data Fields:**
  - Brand Mark & Logo ("ARDHA")
  - Staging Environment Badge (`[STAGING]`)
  - Market Session Status Indicator (`sessionBadge.label`, `isOpen`, `isPreMarket`)
  - Broker Connection Health Badge (`brokerLabel`, `CONNECTED_VERIFIED`, `CONNECTED_AUTH_REQUIRED`, `BROKER_STATE_UNVERIFIED`, `DISCONNECTED`)
  - Expired Broker Session Warning Strip (Kite auth required warning)
  - Live IST Clock (`clockIst.dateStr`, `clockIst.timeStr`)
  - Navigation Module Switchers (`MARKET`, `MARKET INTELLIGENCE`, `NEWS & UPDATES`, `PORTFOLIO`)
  - Global Drawer Triggers (Copilot Drawer Trigger, Settings Modal Trigger)

---

## 2. MARKET WORKSPACE (`/market`)

### A. NIFTY Sub-Tab (`src/frontend/components/NiftyLiveWorkspace.tsx`)
- **PRE View (`PreMarketDashboard`):**
  - Opening Bias Badge, Expected Gap Points, Expected Open Price, Reference Close, Overall Confidence Score, Risk Summary
  - Global Cross-Assets Table (10 assets: GIFT Nifty, S&P 500, Nasdaq, Dow Jones, Nikkei 225, Hang Seng, Brent Crude, Gold Comex, DXY, USD/INR) with prices, % changes, and trend sparklines
  - Market Availability Matrix (Tokyo, Shanghai, Hong Kong, Mumbai, Frankfurt, London)
  - Key Structural Levels (Reference Close, GIFT Nifty, Expected Gap, Resistance, Support, Pivot)
  - Institutional Positioning Bar (FII Cash Net, DII Cash Net, Combined Net Flow, Positioning Slider)
  - Ranked Catalysts (Top 5 news items with impact and direction badges)
  - Scheduled Macro Events Table (Time IST, Event Name)
  - Primary Scenario Plan & Invalidation Condition
- **LIVE View (`LiveDashboard`):**
  - Spot Price Hero, Change Points & Percent, Trend Badge
  - Inline Telemetry: Open, High, Low, Previous Close, Breadth Advance/Decline Counts & Bar, India VIX Value & Change %
  - Timeframe Candlestick Chart (1m, 5m, 15m, 1H, 1D OHLCV candles)
  - Movers Summary Cards: Top Gainers (5 equities), Top Losers (5 equities)
  - Sector Heatmap Strip (Nifty Metal, Bank, Realty, Energy, IT)
  - Market Inspector Rail: Intraday Day Range Bar, Key Levels Grid (R2, R1, Pivot, S1, S2, S3), Institutional Cash Flows (FII/DII/Net), Options Snapshot (PCR, Max Pain, ATM Strike, ATM IV, Volatility Gauge), Sector Donut
- **POST View (`PostMarketDashboard`):**
  - Session Completed Header with Date
  - 9-Metric Summary Grid: Final Close, Change Points & %, Open, High, Low, Prev Close, Range, Trend, Breadth (Adv/Dec/Unch)
  - 4-Cell Trader State Bar: Day Character, Breadth State, Close Location, Institutional Stance
  - Completed Session 15m Candlestick Chart (25 bars)
  - Market Structure Card: Advances/Declines counts & %, A/D ratio, NSE 52W Highs, NSE 52W Lows
  - Volatility & Options Card: India VIX, PCR, Max Pain, ATM Strike, ATM IV
  - Institutional Flows Card: FII Net, DII Net, Combined Net, Flow Date
  - Sector Leadership Card: Rank #1 to #5 sectors with % changes
  - What Drove the Session: Positives, Negatives, Key Takeaways
  - Important Session News Timeline: Timestamps & Headlines
- **Slide-Over Drawer (`MoversSectorsDrawer.tsx`):**
  - Full NSE Gainers Table, Full NSE Losers Table, All 10 NSE Sectors Table

### B. Metrics Sub-Tab (`src/frontend/components/MarketPulseWorkspace.tsx`)
- **Market State Hero Card:** Spot, Change, Trend, Regime, Momentum, Volatility Regime, Breadth Bias
- **Global & Macro Context (11 Cross-Asset Cards):** GIFT Nifty, S&P 500, Nasdaq, Dow Jones, Nikkei 225, Hang Seng, Brent Crude, Gold Comex, USD/INR, DXY, US 10Y Yield
- **5-Column Technical & Breadth Grid:**
  - Price & Trend Metrics: VWAP & Deviation %, EMA20 & Delta %, EMA50 & Delta %, EMA200 & Delta %, RSI (14) & Zone, MACD Line/Signal, ADX (14), Market Structure
  - Structural Levels: Floor R2, Floor R1, Floor Pivot, Floor S1, Floor S2, Local R1 (+1σ ATR), Local S1 (-1σ ATR), Session High, Session Low, Prev Close, Intraday Range
  - Market Breadth: Advances/Declines counts & bar, Unchanged, Coverage (50/50), A/D ratio, Advancing %, Declining %, Breadth Trend, 52W Highs/Lows, Participation State
  - Volatility & Range: India VIX & Change %, Volatility Regime, ATR (14), Day Low, Day High, Range Consumed % Slider, ATR % of Spot
  - Key Telemetry Summary: 10 key metric cells
- **3-Column Sector, Institutional & Interpretation Grid:**
  - Sector Participation Table: 10 Sectors (Name, Chg %, Adv/Dec, Breadth Bar, Trend), Strongest/Weakest Sector
  - Institutional Positioning Card: FII Cash Net & Stance, DII Cash Net & Stance, Combined Net & Stance, Balance Slider, 6-Cell Raw State Grid
  - Metric Interpretation Card: 6-Cell Raw State Grid, Structured Deterministic Summary (Market State, Participation, Positioning, Risk), Key Alignment Strip
- **Footer Metadata Strip:** Session status, dates, sources attribution

### C. Options Sub-Tab (`src/frontend/components/OptionsWorkspace.tsx`, `OptionChainLadder.tsx`, `OpenInterestHeatmap.tsx`)
- **Derivatives State Strip (11 Cells):** Expiry Date & Countdown, Spot & Delta, ATM Strike, PCR OI & Sentiment, PCR Volume, Max Pain, ATM IV %, IV State, Total Call OI (Cr) & %, Total Put OI (Cr) & %, OI Skew & Bias
- **Left Column (Positioning Map):** Expiry Selector, Call vs Put OI Cr values, CE/PE Balance Bar, Call Wall & Put Wall Strikes, Max Pain Pin, Distance & Range Structure
- **Center Column (Smart Option Chain):**
  - Mode Toggles: Table / OI Heatmap / OI Change
  - Strike Sort Toggle: Ascending / Descending
  - 11 Columns: Call OI (Lakh), Call ΔOI, Call LTP, Call Chg %, Call IV, Call Buildup Label, Center Strike (with ATM / Wall / Pain badges), Put Buildup Label, Put IV, Put Chg %, Put LTP, Put ΔOI, Put OI (Lakh)
- **Right Column (Options Inspector):**
  - Volatility Structure: ATM IV, IV Percentile, RBI Base Rate (6.50%)
  - Selected Strike Inspector: Strike price, Focus badge, Distance from spot pts and %
  - CE Breakdown: LTP, OI Lakhs, ΔOI Lakhs, IV %
  - PE Breakdown: LTP, OI Lakhs, ΔOI Lakhs, IV %
  - Black-Scholes Greeks: Clean "Unavailable" status with clear architectural notice
- **Bottom Grid:**
  - What Changed: Derivatives evidence bullet points
  - Strike Structure Summary: 3-Node structural rail (Put support strike, Spot/Max Pain, Call resistance strike) + PCR/Skew summary

---

## 3. MARKET INTELLIGENCE WORKSPACE (`/intelligence`)

### `src/frontend/components/MarketIntelligenceWorkspace.tsx`
- Sub-Tab Switcher: `MORNING PLAN` (Pre), `LIVE GUIDE` (Now), `TOMORROW PLAN` (Next Day)
- Session Resolver & Staging Preview Override Selector

### A. Morning Plan View (`src/frontend/components/intelligence/MorningPlanView.tsx`)
- Best Plan at Open (Spot Index, Carry-Forward Level, Opening Range Est, Preferred Bias, Invalidation, Rationale)
- Primary & Alternate Scenarios (Name, Confidence %, Plan, Data Basis, Evidence Table, Historical Proof)
- What to Watch First 15 Min (5 actionable items with status)
- Suitable Strategies Table (Strategy Name, Preferred/Alternate Tag, Condition, Trigger, Target, Confidence, Proof)
- Yesterday's Market Info Card (Close, High, Low, Change, Breadth, VWAP, FII Cash, DII Cash)
- Today's Market Open Snapshot (09:00–09:08 Frozen: Open, High, Low, VWAP, Range, Breadth, PCR, Institutional Cash)
- Key Levels & Decision Zone (R2, R1, Pivot Decision Zone, S1, S2, Bullish Above, Bearish Below, Invalidation, Must Hold, Trend Filter)
- Morning Risk Context (Global Cues, Nifty VIX, Event Risk, Overall Risk Badge)
- Data-Backed Value Suggestions Table (Zone, Upper, Lower, Conviction, Rationale/Data Basis)

### B. Live Guide View (`src/frontend/components/intelligence/LiveGuideView.tsx`)
- Best Action Now Card (Status Badge, Confidence Score, Action Headline, Next Trigger, Invalidation, Rationale)
- Current Market State (Structure, Breadth, VWAP Status, Momentum, Volatility/VIX, Bias Badge)
- Live Primary & Alternate Scenarios (Name, Confidence %, Plan, Conditions, What To Do, Key Levels, Invalidation, Evidence Tags)
- Key Levels & Value Suggestions Table (Type, Level/Zone, Conviction, Why Level Matters, Data Basis)
- Market Metrics Snapshot Card (Nifty Spot & Chg, Bank Nifty Spot & Chg, India VIX & Chg, RSI, PCR, Breadth)
- Real-Time Watchlist (Leading Sectors, Lagging Sectors, Top Gainers, Top Losers)
- Suitable Strategies Now (Ranked Strategy Cards with Star Rating, When, Trigger, Target, R:R, Confidence)
- Opportunity Qualification Pipeline (5-step pipeline: Idea → Conditions → Confirm → Qualified → Action, Summary, Portfolio Link)
- Live Risk Context (Global Cues, News/Events, Volatility Expectation, Overall Risk, Confirmations, Blockers)

### C. Tomorrow Plan View (`src/frontend/components/intelligence/TomorrowPlanView.tsx`)
- Best Plan for Tomorrow (Headline, Rationale, Confidence Score, Spot Index, Carry-Forward Level, Opening Zone, Directional Bias, Invalidation, Proof)
- Best Strike Suggestions Table (Best Call Strike Zone, Best Put Strike Zone, Rationale, Confidence, Proof)
- Night Preparation Checklist (4-5 items with checklist icons and proof basis)
- Suitable Strategies (Name, Tag, When, Trigger, Target, Confidence, Proof)
- Tomorrow Risk Context (Market Mood, Event Risk, Confirmations X/5, Blockers X, Confidence Score, Plan Quality)
- Today's Market Overview Card (Open, High, Low, Close, Day Change, Range, Day Type, Breadth, VWAP, VIX, PCR, Leadership)
- Confidence & Structure Strip (Plan Conf, Data Quality, Score, Regime, Liquidity)

---

## 4. NEWS & UPDATES WORKSPACE (`/news`)

### `src/frontend/components/news/NewsWorkspace.tsx`
- Temporal Context Strip & Sub-Tab Bar (`LIVE NEWS`, `CATALYSTS`, `CALENDAR`)
- Bottom News Alert Banner (High impact event alert with pulse icon)

### A. Live News Tab (`src/frontend/components/news/LiveNewsTab.tsx`)
- Top Summary Strip (Market News Tone, High Impact Count, Direction Breakdown POS/NEG & Bar, Most Affected Sector, Next Major Event, News Risk Level)
- Live News Feed (Headline, Publisher, Official Shield Badge, Time IST, Category, Direction POS/NEG, Impact HIGH/MED, Why It Matters, Affected Companies, Affected Sectors, External Source Link)
- Feed Filter Selector (ALL, HIGH IMPACT, POSITIVE, NEGATIVE, OFFICIAL, EARNINGS, MACRO)

### B. Catalysts Tab (`src/frontend/components/news/CatalystsTab.tsx`)
- Top Market Drivers (Rank #1-#6, Driver Name, Impact Badge, State ACTIVE, Direction, Why It Matters)
- Positive Catalysts List (Publisher, Headline, Why It Matters)
- Negative Catalysts & Risks List (Publisher, Headline, Why It Matters)
- Regulatory & Policy Catalysts List (Publisher SEBI/RBI, Timestamp, Headline, Summary)
- Carry-Forward Risks List (Title, RED/AMBER Risk Level, Detail)

### C. Calendar Tab (`src/frontend/components/news/CalendarTab.tsx`)
- Economic & Corporate Calendar Header (Scheduled Releases Count, Region Filter, Impact Filter)
- Upcoming Events Table (Date, Time IST, Region, Event Name, Impact Badge, Status Badge, Previous, Consensus, Actual)
- Completed Events Table (Date, Time IST, Region, Event Name, Impact Badge, Status Badge, Previous, Consensus, Actual)

---

## 5. PORTFOLIO WORKSPACE (`/portfolio`)

### `src/frontend/components/PortfolioWorkspace.tsx`
- Execution Header & Safety Bar: PHASE 3 ACTIVE Badge, Normalized Broker Status, Kill Switch Status, Sync Broker Button, Kill Switch Toggle
- Top Metric Strip: Live Open Positions Count, Total Unrealized P&L, Daily Realized Loss Gate Ratio, Execution State
- Action Feedback & Error Alert Banners
- Active Opportunity & Proposed Trade Action Hero (`ActiveOpportunityHero.tsx`):
  - Direction Badge, Contract Symbol, Setup Type, Interactive Lots Selector (1-10), Proposal State Badge, Conviction Score
  - Metric Strip: Entry Reference, Stop-Loss, Target 1 / Target 2, Risk:Reward, Quantity Exposure, Max Capital Risk
  - 3 Rationale Cards & Server-Enforced Invalidation Trigger Banner
  - Audit Metadata & Order Intent Expandable Drawer
  - Action Controls: Reject Button, Preview Order Modal Trigger, Approve Button (Dry-Run / Kite Router)
- Live Positions Table: Symbol, Stop/Target Breached Badges, Product, Quantity, Buy Avg, Live LTP, Unrealized P&L, Stop Loss, Target, Lineage Trigger, Exit Button
- Active Broker Order Book: Symbol, Transaction Type & Order Type, Product, Filled/Total/Remaining Quantity, Limit Price, Broker ID, Status Badge, Cancel Button
- Closed Trade Execution Journal & Lineage (M5): Total Trades, Win Rate %, Realized P&L, Journal Rows (Date, Contract, Setup, Avg Entry, Avg Exit, Slippage pts, Realized P&L, R-Multiple, Closing Reason, Audit Lineage Button)
- Modals & Drawers: Single Position Exit Confirmation Modal, Emergency Close All Confirmation Modal, Order Preview Modal, Trade Lineage Modal, Live Position Drawer

---

## 6. SETTINGS WORKSPACE (`/settings`)

### `src/frontend/components/settings/SettingsWorkspace.tsx`
- General Preferences: Time Format (12h/24h), Number Format (IN/INTL), Default Landing Workspace, Default Market View, Reset Preferences Action
- Connections: Zerodha KiteConnect (Status & Auth Button), Market Data (Status), Options Data (Status), News Engine (Status), Macro Calendar (Status), AI Assistant (Status)
- Notifications: Desktop Permission Action Banner, High Impact News Alerts Toggle, Session Open/Close Toggle, Broker Session Alerts Toggle, Macro Reminders Toggle, System Warnings Toggle
- Advanced Technical Snapshot: Runtime ID, State Sequence Number, Environment Tag, Market Session, Last Sync Timestamp, App Version
- Action Triggers: Open Diagnostics Drawer, View Performance Panel, Export JSON Diagnostics, Staging Session Mode Overrides (Staging only)
- Diagnostics Drawer (`AdvancedDiagnosticsDrawer.tsx`): Overall Health, Runtime ID, Sequence Number, Market Session, 8-Component Ingestion Readiness Matrix, 5-Metric Post-Auth Startup Latency Trace, Dataset Integrity Table & Counts, Export JSON Action
- Detector Health Panel (`DetectorHealthPanel.tsx`): Scan Duration ms, Detector Duration ms, Evaluated Candidates Today, Detector Cards (ID, Version, Status, Detected, Qualified, Blocked, Rejected, Input Blockers, Errors)
- Ardha Performance Panel (`ArdhaPerformancePanel.tsx`): Date Selector & History Dropdown, Summary Pills (Hits, Near, Misses, Pending, N/A), 5 Phase Filter Tabs, Evaluation Records Table (Time, Phase, Metric, Ardha Value, Real Value, Outcome Badge, Error Delta, Notes & Tolerance Rule)

---

## 7. LIVE ASSISTANT & INTRADAY NARRATOR

### `src/frontend/components/LiveAssistantPanel.tsx` & `IntradayAssistant.tsx`
- Header: Live Assistant Title, COPILOT Badge, GROUNDED Status Indicator, Current Context Module Badge, Window Expand/Collapse Toggle
- Thread: Chat History (User Bubble vs Assistant Formatted Markdown Bubble)
- Grounding Metadata Accordion: Grounded Sources Count, Freshness Tag, Speech Act, Data Sufficiency, Cited Canonical Sources, Underlying Provider, Fallback Active Tag, Ranked Drivers, Detected Intents
- Suggestions & Composer: Dynamic Session Question Pills, Text Input Field, Send Button
- Intraday Timeline: Monitoring Status, Spot Price Hero & Change, Current Market State & Read Narrative, 15-Minute Window Cards, Significant Event Stream, Confirmation Families Matrix (Price, Breadth, Options, Volatility, Heavyweights, Macro) with trend arrows and stance
