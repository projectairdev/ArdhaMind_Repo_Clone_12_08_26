# Operator Guide

This guide is designed for operators of the **NIFTY Option Finder & Market Intelligence Workstation**. It explains how to interpret dashboard panels, read directional indicators, monitor system metrics, and respond to alerts.

---

## 🖥️ Terminal Dashboard layout

When running the terminal workstation, the screen is formatted into structured ASCII blocks:

```text
================================================================================
          NIFTY OPTION FINDER & MARKET INTELLIGENCE WORKSTATION
================================================================================
 [SYSTEM STATUS: ACTIVE]   [TIME: 2026-07-10 13:08:00 UTC]   [UPTIME: 03:24:12]
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

## 🚦 Understanding Directional Market Scores

The core decision metrics are driven by the **Market Scoring Pipeline**:

- **Excellent (90.0 - 100.0 / Grade A+)**: Optimal setup. Strong alignment of macro news sentiment, Put-Call Ratio support, and upward momentum breakout. Permissive capital limits are unlocked.
- **Good (80.0 - 89.9 / Grade B or B+)**: Standard high-probability trend conditions. Excellent for Scalping and Trend Following.
- **Fair / Limited (60.0 - 79.9 / Grade C)**: Market is rangebound or exhibiting high volatility with mixed sentiment. Trade sizes are reduced by 50% automatically.
- **Caution / Avoid (< 60.0 / Grade F)**: Severe trend divergence or critical downside risks. Risk Engine imposes a total block on new order execution (`WATCH` status only).

---

## ⚙️ Operating Procedures

### 1. Ingesting Daily Market Parameters
On startup, verify that the scoring parameters are updated to match recent NIFTY volatility levels. Operators can verify this by checking the `SCHEMA VALIDATION CHECKS` section in the **Configuration Panel**.

### 2. Manual Action Override
If an option candidate requires manual adjustment, the operator can switch profiles:
- To reduce risk instantly under extreme news events: Activate the **`CONSERVATIVE`** profile.
- To execute heavy position volumes on option expiry: Activate the **`EXPIRY_DAY`** profile.

### 3. Monitoring Position Lifecycles
Positions progress through five type-safe lifecycle stages:
1. `INITIATED`: Decision engine formulated buy plan.
2. `PLACED`: Manual broker order was registered.
3. `EXECUTED`: Order filled, active exposure tracked.
4. `CLOSED`: Exit condition (Target/Stop/Manual) reached.
5. `REJECTED`: Blocked by Risk limits or broker failure.

---

## 🚨 Troubleshooting Critical Indicators

- **Health Monitor displays `NOT_READY`**:
  Check the **Startup Diagnostics** checks in the terminal. If `env_vars` is `FAIL`, ensure that the `.env` file exists and contains valid credentials.
- **Readiness score drops below 80.0**:
  Indicates resource limits (high memory usage) or missing local cache databases. Clean up `/cache/` or restart background tasks.
