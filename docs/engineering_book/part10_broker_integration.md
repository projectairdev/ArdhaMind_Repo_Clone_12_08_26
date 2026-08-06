# Part 10: Broker Gateways & Order Lifecycles

This section documents the integration architecture for Zerodha Kite Connect, manual execution verification flows, and position state lifecycles within the NIFTY Option Finder & Market Intelligence Workstation.

---

## 🔒 Security & Credentials Management

The workstation prioritizes the absolute security of broker API credentials and session tokens:

1. **No Hardcoded Keys**: API keys are strictly loaded via the system environment (`.env` file) or dynamically entered in the dashboard workspace.
2. **Local Token Caching**: Session tokens (such as `access_token` for Kite Connect API) are stored locally in secure temporary caches (`cache/session.json`) that are listed in `.gitignore` to prevent leakage to source control.
3. **Session Expiry**: Session tokens are automatically invalidated every 24 hours to enforce daily manual re-authentication.

---

## 🔌 Zerodha Kite Connect Gateway

The default broker engine integrates with the Zerodha Kite Connect platform:

- **API Version**: `3.0`
- **Rate Limiting**: Implements a proactive token-bucket filter to ensure API requests remain well within the 10-requests-per-second limit.
- **Auto-Reconnect**: Supports 3 automatic reconnection attempts for real-time market streams before raising an alarm.

---

## ⚡ Manual Order Placement & Lifecycle Verification

To execute a recommended trade plan on a live broker account:

### Step 1: Gateway Connection Verification
Ensure the broker connection is verified by launching the diagnostic test:
```bash
python3 -m unittest tests/test_broker_integration.py
```
This confirms that credentials can connect, parse profiles, and query balances safely.

### Step 2: Evaluating Candidate Recommendations
Monitor the terminal's **Active Opportunity Candidates**. Each option plan defines precise entry premiums, lot limits, and risk levels.

### Step 3: Placing Order manually
1. Log in to your broker's desktop terminal or mobile application.
2. Manually enter the option order matching the workstation recommendation.
3. Once filled, log the order reference ID back into the workstation dashboard (under **Manual Broker Panel**) to initiate real-time trail stop and P&L tracking.

---

## 🔄 Position State Lifecycles

All transactions progress through five strict state lifecycles to ensure absolute risk control:

```text
[INITIATED] ──► [PLACED] ──► [EXECUTED] ──► [CLOSED]
     │                                         ▲
     └─────────────────────────────────────────┼──► [REJECTED]
```

### State Explanations:
1. **`INITIATED`**: The decision engine has formulated a buy plan for a candidate contract.
2. **`PLACED`**: The order is registered inside the workstation's manual tracking ledger.
3. **`EXECUTED`**: The operator has manually entered and filled the order, initiating active exposure tracking.
4. **`CLOSED`**: The exit target, stop loss, or manual override has been triggered and executed, closing active exposure.
5. **`REJECTED`**: The trade plan has been blocked due to risk violations, balance limitations, or broker failures.

This strict, type-safe lifecycle tracking ensures that open risk exposures are always accounted for, preventing unmonitored positions or runaway losses.
