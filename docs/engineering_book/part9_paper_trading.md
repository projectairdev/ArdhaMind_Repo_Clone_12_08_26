# Part 9: Paper Trading & Margin Modeling

This section documents the simulated paper trading environment, accounting ledgers, margin requirements, and analytical engines within the NIFTY Option Finder & Market Intelligence Workstation.

---

## 🏛️ Simulation Architecture

The local paper trading engine allows operators to test strategies, risk controls, and execution models under real-world conditions without exposing live capital. 

The simulator features three core layers:
1. **The Double-Entry Accounting Ledger**: Records all transactions as debit/credit journal entries to maintain mathematical balance.
2. **The Portfolio Valuator**: Tracks open and closed positions, calculating equity curves and cash balances in real-time.
3. **The Slippage and Latency Simulator**: Approximates market frictions, ensuring realistic simulation results.

---

## 🗄️ Double-Entry Ledger System

To prevent balance tracking errors, the simulator operates on standard double-entry accounting rules. Every transaction is recorded as a balanced debit/credit pair:

```text
       [ SIMULATED TRANSACTION ]
                  │
         ┌────────┴────────┐
         ▼                 ▼
[ CASH ACCOUNT ]    [ POSITION ASSETS ]
 (Credit Debit)      (Debit Credit)
```

### Ledger Journal Format
Each transaction log contains a unique entry ID, timestamp, transaction type, debit/credit values, and the current balance:

```json
{
  "entry_id": "TX_20260710_001",
  "timestamp": "2026-07-10T13:12:00Z",
  "tx_type": "BUY_OPEN",
  "contract": "NIFTY26NOV24200CE",
  "lots": 10,
  "premium": 150.00,
  "cash_debit": 75000.00,
  "asset_credit": 75000.00,
  "transaction_fee": 20.00,
  "resulting_cash_balance": 924980.00
}
```

This immutable ledger history is persisted inside `/cache/paper_ledger.json`, ensuring full auditability of all simulated trades.

---

## 📊 Margin Accounting Rules

Before executing any candidate buy order, the paper trading pipeline performs a two-tier margin check:

### 1. Initial Margin Check
For option buying, the required premium is reserved completely:
$$\text{Margin Reserved} = \text{Lots} \times \text{Standard Lot Size (50)} \times \text{Contract Premium}$$
If the required margin exceeds the active portfolio's available cash, the transaction is rejected immediately by the risk engine.

### 2. Maintenance Margin Check
If the portfolio's available cash falls below `15%` of the required maintenance margin, the engine triggers a **Margin Call Warning** and blocks further position opening.

---

## 🏎️ Slippage & Latency Simulation

To prevent unrealistic paper performance, the engine models execution slippage and network latency:

- **Slippage Modeling**: Calculates slippage based on contract premium, bid-ask spreads, and options volatility:
  $$\text{Slippage Fee} = \text{Premium} \times \text{Slippage Coefficient (default: 0.05\%)}$$
  This ensures that transaction entries are executed at slightly worse premiums, and exits are cleared slightly lower.
- **Execution Delay**: Introduces random simulated network delays between `100ms` and `500ms` before order confirmation.

---

## 📈 Performance Analytics Suite

The analytics engine processes historical ledger entries to generate institutional-grade performance metrics:

### 1. Win Rate
The ratio of profitable closed trades to total completed transactions:
$$\text{Win Rate} = \frac{\text{Winning Trades}}{\text{Total Completed Trades}}$$

### 2. Annualized Sharpe Ratio
Calculated relative to a risk-free rate (typically `6.0%` for standard Indian bonds):
$$\text{Sharpe Ratio} = \frac{\bar{R}_p - R_f}{\sigma_p}$$
Where $\bar{R}_p$ is the average return, $R_f$ is the risk-free rate, and $\sigma_p$ is the standard deviation of returns.

### 3. Maximum Drawdown (MDD)
The peak-to-valley balance decline:
$$\text{MDD} = \frac{\text{Peak Value} - \text{Valley Value}}{\text{Peak Value}} \times 100\%$$

This deep analytical suite allows operators to prove their trading edge under real-world conditions prior to manual broker routing.
