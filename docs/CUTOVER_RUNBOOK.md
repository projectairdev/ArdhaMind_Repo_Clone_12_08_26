# AIR ArdhaMind — Production Cutover Runbook (DhanHQ Canonical Stack)

This document provides the authoritative, step-by-step operational runbook for transitioning AIR ArdhaMind from legacy Kite runtime to the new provider-independent Canonical Market Data and Intelligence Stack.

---

## 1. Safety Invariants & Pre-Conditions

1. **Read-Only Invariant**:
   - Zero execution or order routing capabilities exist anywhere in the canonical stack.
   - Broker credentials only possess read-only market data and quote entitlements.
2. **Current System State**:
   - Status: `READY_FOR_LIVE_VALIDATION`.
   - All 239 deterministic unit tests passing across all 6 core packages (`market_data`, `analytics`, `prediction`, `decision`, `replay`, `observability`).
3. **Execution Gate**:
   - Production cutover MUST NOT occur until Live Market-Hours Validation is completed and verified against live NSE feeds.

---

## 2. Phase 1: Pre-Cutover Live Validation (During NSE Market Hours: 09:15 – 15:30 IST)

### Step 1.1: Configure Dhan Read-Only Credentials
Ensure live credentials exist in `.env`:
```bash
DHAN_CLIENT_ID="<client_id>"
DHAN_ACCESS_TOKEN="<access_token>"
```

### Step 1.2: Execute Live Validation Harness
Run the validation harness for at least 5 minutes (300 seconds):
```bash
python -m src.market_data.runtime.validate_live_dhan --duration-seconds 300
```

### Step 1.3: Verify Gate Results
Verify all 13 core gates pass in the output summary:
- `1_dhan_auth_verified`: True
- `2_websocket_connected`: True
- `3_desired_subscriptions_active`: True
- `4_real_nifty_ticks_observed`: True
- `5_feed_healthy`: True
- `6_session_authority_correct`: True
- `7_no_session_mismatch`: True
- `8_candles_updating`: True
- `9_rest_reconciliation_functioning`: True
- `10_historical_bootstrap_functioning`: True
- `11_option_chain_functioning`: True
- `12_shadow_comparison_acceptable`: True
- `13_zero_fabricated_fallback_values`: True

---

## 3. Phase 2: Shadow Runtime Verification

### Step 2.1: Run Shadow Comparison
Run the backend in shadow mode alongside the legacy Kite provider.
Verify that `CanonicalBackendRuntime.perform_shadow_comparison(legacy_state)` outputs `MATCH` or `CANONICAL_NEWER`.

### Step 2.2: Verify Latency and Replay Parity
Confirm telemetry metrics:
- Latency (`exchange_to_receive_ms` + `state_to_decision_ms`) < 100ms.
- Replay evaluator SHA-256 reproducibility hash remains 100% bitwise identical.

---

## 4. Phase 3: Controlled Frontend Authority Switchover

### Step 3.1: Switch Frontend Ingestion Endpoint
Update the frontend WebSocket / state consumer to bind to `CanonicalFrontendEnvelope`:
```typescript
// Envelope contains:
{
  runtime_id: string,
  state_revision: number,
  session: SessionContext,
  market: LiveMarketState,
  analytics: MarketAnalyticsSnapshot,
  prediction: PredictionSnapshot,
  decision: DecisionSnapshot,
  active_product: ProductSnapshot
}
```

### Step 3.2: Monitor Convergence
Verify frontend UI receives monotonic revisions with zero UI stutter, flicker, or sequence locking on server restarts.

---

## 5. Rollback Procedure

If any anomaly occurs during live validation or cutover:
1. **Immediate Fallback**: Keep legacy Kite runtime active as fallback source.
2. **Isolate Diagnostics**: Capture `IncidentSnapshot` via `IncidentSnapshotBuilder.capture()`.
3. **Redact & Review**: Review redacted diagnostic logs to inspect root causes.
