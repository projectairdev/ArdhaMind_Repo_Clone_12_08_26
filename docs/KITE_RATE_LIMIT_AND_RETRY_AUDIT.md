# KITE RATE LIMIT, RETRY & BURST SAFETY AUDIT

**Document Version:** 1.0.0 — Authoritative Rate Limit & Retry Audit  
**Target Modules:** `src/broker/adapters/kite_broker.py`, `src/broker/services/streaming_orchestrator.py`

---

## 1. ZERODHA KITE OFFICIAL RATE LIMITS

- **Historical Data API (`kite.historical_data`):** **3 requests / second**
- **Quote API (`kite.quote`, `kite.ohlc`, `kite.ltp`):** **10 requests / second**
- **Orders & Positions API:** **10 requests / second**
- **General REST Endpoints:** **10 requests / second**

---

## 2. CALL BURST ANALYSIS BY LIFECYCLE EVENT

| Operational Event | REST Endpoints Invoked | Total Requests | Execution Window | Peak Rate | Rate Limit Compliance |
|:---|:---|:---:|:---:|:---:|:---:|
| **Cold Startup Initialization** | `profile()`, `instruments("NSE")`, `historical_data()`, `quote()` | **4 requests** | ~1,200 ms | ~3.3 req/s (1 hist) | **PASS** (Within limits) |
| **Normal Live Streaming** | None (All streaming ticks via WebSocket) | **0 req/s** | Ongoing | 0 req/s | **PASS** (Zero REST load) |
| **Periodic Breadth / Macro Poll** | `quote(["NSE:..."])` (50 constituents batch) | **1 batch request** | Every 15–30s | 0.05 req/s | **PASS** |
| **Transient Gap Backfill** | `historical_data(nifty_token, 5m)` | **1 request** | Post-reconnect | 1.0 req/s | **PASS** |
| **EOD Close Reconciliation** | `historical_data(nifty_token, "day")` | **1 request** | At 15:35 IST | 1.0 req/s | **PASS** |

---

## 3. RETRY & EXPONENTIAL BACKOFF SPECIFICATION

- **Max Reconnect Attempts:** **5 attempts**
- **Backoff Multiplier:** Exponential $2^n \times 1.0\text{s}$ with jitter ($1.0\text{s} \rightarrow 2.0\text{s} \rightarrow 4.0\text{s} \rightarrow 8.0\text{s} \rightarrow 10.0\text{s}\text{ max}$).
- **Auth Error Circuit Breaker:**
  If Kite Connect returns `HTTP 403`, `TokenException`, `"invalid token"`, or `"token expired"`, the reconnect loop is **immediately halted**, `auth_required` is set to `True`, and a high-priority diagnostic alert is emitted. This guarantees zero API storming or account locking.
