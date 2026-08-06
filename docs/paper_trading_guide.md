# Paper Trading Guide

This guide details the operation of the **Paper Trading Engine**, which provides simulated execution environment with advanced margin modeling, slippage, and performance analytics.

---

## 🏗️ Engine Architecture

The Paper Trading Engine operates locally without exposing active capital. It mirrors live exchange rules for option contract sizes, margin requirements, and execution fills:

- **Lot Sizing**: Enforces NIFTY standard lot size rules (e.g. 50 contracts per lot).
- **Execution Delay**: Simulates realistic internet latencies by delaying fills between `100ms` and `500ms`.
- **Slippage Model**: Computes transactional slippage based on contract bid-ask spreads and options volatility (configured via `slippage_percent`, typically defaulting to `0.05%` of contract premium).
- **Double-Entry Ledger**: Every transaction (order entry, exit, fee payment) is logged as an immutable debit/credit journal entry to prevent balance skew.

---

## 📊 Margin Accounting Rules

Before executing any candidate buy order, the paper trading pipeline performs rigorous margin validation:

1. **Initial Margin Reservation**:
   - For option buying: Standard contract premium is reserved completely:
     $$\text{Margin Reserved} = \text{Premium} \times \text{Lots} \times 50$$
   - For option selling: Enforces span margins plus exposure margins based on index levels (simulated via local margins rules).
2. **Maintenance Margin Check**:
   If overall paper cash balance drops below `15%` of the required maintenance margin, the engine triggers an automatic **Margin Call Alert** and halts further position opening.

---

## 📈 Performance Analytics Suite

The Performance Engine compiles historical transactions and generates institutional-grade risk metrics:

- **Win Rate**: Ratio of winning transactions to total closed trades.
- **Sharpe Ratio**: Annualized Sharpe ratio calculated relative to a risk-free rate (typically `6.0%` for standard Indian bonds):
  $$\text{Sharpe Ratio} = \frac{\bar{R}_p - R_f}{\sigma_p}$$
- **Drawdown Tracking**: Tracks peak-to-valley balance declines to determine Maximum Drawdown (MDD) percentages.
- **Regime Analysis**: Breaks down strategy performance (e.g., Scalping vs. Swing) across Bullish, Bearish, and Sideways market regimes to identify strategy edge.

---

## ⚙️ Standard Paper Trading Procedure

### Step 1: Initialize Capital
Set the initial capital balance inside `paper_trading.yaml` (defaults to `1,000,000.00 INR`).

### Step 2: Running Performance Diagnostics
To audit portfolio metrics, view the **Performance Analytics Panel** or execute:
```bash
python3 -m unittest tests/test_performance_analytics.py
```

### Step 3: Inspecting Execution Logs
Check the double-entry transactions ledger in your local workspace directory:
`cache/paper_ledger.json` (or standard database file if active).
