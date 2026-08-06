# Live Trading Guide

This guide describes how to configure the workstation for **Manual Broker Evaluation & Live Tracking**. 

> [!WARNING]
> **No Auto-Trading on Live Accounts**: This workstation is structured as a **decision support system** and manual execution bridge. It does NOT execute automated orders directly without physical operator authorization. All live trades must be validated and executed under direct operator oversight.

---

## 🔒 Security & Credentials Management

The workstation prioritizes the absolute security of broker API credentials and session tokens:

1. **No Hardcoded Keys**: API secrets are strictly loaded via the system environment (`.env` file) or dynamically entered in the dashboard workspace.
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
