# Part 8: Presentation & Dashboard Systems

This section documents the presentation layers, terminal-based ASCII layouts, React-based web dashboards, and serialization systems within the NIFTY Option Finder & Market Intelligence Workstation.

---

## 🎨 Unified Presentation Standards

To prevent visual clutter, both the CLI terminal and React dashboard adhere to strict presentation rules:
1. **Architectural Honesty**: No telemetry logging, pseudo-status lights, or unrequested metrics cluttering the screens.
2. **Design-First Color Palettes**:
   - **CLI**: Standard high-contrast white-on-black or customized high-contrast themes.
   - **React Dashboard**: Built on an off-white or charcoal-gray background with generous negative space.
3. **Typography**: Headings use clean sans-serif layouts (Space Grotesk), while data, prices, and stats use monospace fonts (JetBrains Mono) for readability.

---

## 🖥️ CLI Terminal Layout Specs

When running the terminal workstation, the layout is divided into six structured ASCII boxes:

```text
================================================================================
          NIFTY OPTION FINDER & MARKET INTELLIGENCE WORKSTATION
================================================================================
 [SYSTEM STATUS: ACTIVE]   [TIME: 2026-07-10 13:10:00 UTC]   [UPTIME: 03:26:12]
--------------------------------------------------------------------------------

+- MARKET INTELLIGENCE SUMMARY PANEL ------------------------------------------+
| Spot Price: 24,200.00 | Directional Bias: BULLISH | Regime: TRENDING        |
| Trend Strength: 71.09% | ATR: 125.40               | S/R Zone: 24150 - 24300 |
+------------------------------------------------------------------------------+

+- NIFTY OPTION CHAIN INTEL PANEL ---------------------------------------------+
| ATM Strike: 24,200.00 | Put-Call Ratio: 1.05       | Max Pain Strike: 24,200  |
| Call IV   : 14.20%    | Put IV        : 14.80%     | OI Trend: BULLISH CONFL. |
+------------------------------------------------------------------------------+

+- DIRECTIONAL MARKET SCORING -------------------------------------------------+
| Score: 83.67 / 100    | Grade: B                  | Outlook: GOOD            |
+------------------------------------------------------------------------------+

+- ACTIVE OPPORTUNITY CANDIDATES -----------------------------------------------+
| * CANDIDATE: SCALPING_NIFTY26NOV24200CE | Score: 92.0 | Sizing: 10 Lots (500) |
| * CANDIDATE: MOMENTUM_NIFTY26NOV24150CE | Score: 88.5 | Sizing: 8 Lots (400)  |
+------------------------------------------------------------------------------+

+- OPERATIONS HEALTH MONITOR --------------------------------------------------+
| Overall Health: READY | CPU Usage: 4.2%           | Memory Used: 142.5 MB    |
+------------------------------------------------------------------------------+
```

---

## 🌐 React Web Dashboard Components

For web-based monitoring, the frontend mirrors the terminal's logical layout using interactive React components:

### 1. Market Intelligence Summary Card
- **Responsibilities**: Displays spot prices, current regime, and support/resistance lines.
- **Interactions**: Interactive charts displaying support/resistance zones.

### 2. Option Chain Panel
- **Responsibilities**: Displays At-The-Money (ATM) contract lines and Put-Call Ratio charts.
- **Interactions**: Expandable option chain list displaying strikes, premiums, open interest, and implied volatility.

### 3. Directional Scoring Gauge
- **Responsibilities**: Displays overall market scores, assigned grades, and outlook sentiment.
- **Interactions**: Interactive gauge with historical score charts.

### 4. Active Candidates Table
- **Responsibilities**: Displays risk-approved trade plans, entry thresholds, stops, targets, and lot sizes.
- **Interactions**: Click-to-copy buttons for quick manual trade entry.

### 5. Operations & Health Panel
- **Responsibilities**: Displays CPU usage, memory allocations, directory access permissions, and required `.env` API keys.
- **Interactions**: Clean self-diagnostic run button.

### 6. Workspace Configurations Panel
- **Responsibilities**: Displays active profiles, preference settings, and validation warnings.
- **Interactions**: Dropdowns to switch active profiles and sliders to adjust refresh rates.

---

## 🔄 Backend-to-Frontend Serialization

The React frontend communicates with the Python backend via structured JSON payloads. When a pipeline execution cycle completes, the backend generates a serialized dashboard payload:

```json
{
  "timestamp": "2026-07-10T13:10:00Z",
  "system_status": "ACTIVE",
  "market_context": {
    "spot_price": 24200.00,
    "directional_bias": "BULLISH",
    "regime": "TRENDING"
  },
  "scoring": {
    "score": 83.67,
    "grade": "B",
    "outlook": "GOOD"
  },
  "health": {
    "status": "READY",
    "cpu_usage": 4.2,
    "memory_mb": 142.5
  }
}
```

This simple, structured data schema ensures fast, lightweight, and reliable communication between layers.
