# Realtime Recovery Model Specification (STAGING ONLY)

**Environment**: STAGING ONLY (`/opt/ardhamind/staging`)  
**Specification**: Stream-first bootstrap, sequence gap detection, runtime ID mismatch handling, and HTTP polling failover protocol.

---

## 1. Stream-First Bootstrap Sequence

To prevent state race conditions where a full snapshot overwrites newer stream deltas:

```
[Browser Client Starts]
        |
        v
1. Connect WebSocket to ws://localhost:3000/api/ws
        |
        v
2. Receive initial stream frame -> Record stream_sequence = N
        |
        v
3. Fetch full canonical snapshot GET /api/state/canonical
        |
        v
4. Reconcile Snapshot:
   - If snapshot.state_sequence <= N: Apply pending stream deltas (> N)
   - If snapshot.state_sequence > N: Update store to snapshot, set expected_sequence = snapshot.sequence + 1
        |
        v
5. Enter Normal Delta Stream State
```

---

## 2. Sequence Gap & Disconnect Recovery Protocol

### A. Sequence Gap Detection
- Client maintains `last_applied_sequence`.
- When a new frame arrives with `incoming_seq`:
  - **`incoming_seq === last_applied_sequence + 1`**: Apply delta normally. Increment `last_applied_sequence`.
  - **`incoming_seq <= last_applied_sequence`**: Duplicate or out-of-order frame. Log diagnostic and discard frame.
  - **`incoming_seq > last_applied_sequence + 1`**: Sequence gap detected (missed frames). Trigger immediate recovery snapshot fetch (`GET /api/state/canonical`).

### B. Runtime ID Mismatch Handling
- Every frame includes `runtime_id`.
- If a frame arrives with a `runtime_id` different from current session:
  - Python daemon process has restarted.
  - Clear local delta buffer, display `"RUNTIME RESTARTED — RECONNECTING"` status badge, and fetch fresh full canonical snapshot (`GET /api/state/canonical`).

### C. HTTP Polling Failover & Degradation
- If WebSocket drops (`onclose` or `onerror`):
  - Mark delivery status as `STREAM DEGRADED (HTTP Fallback)`.
  - Activate HTTP polling fallback (`fetchCanonicalState()`) every **5,000 ms**.
  - Attempt WebSocket reconnection using bounded exponential backoff (`1s`, `2s`, `4s`, `8s`, max `15s`).
- When WebSocket successfully reconnects:
  - Disable HTTP polling fallback.
  - Execute Stream-First Bootstrap Sequence.
  - Mark delivery status as `REAL-TIME STREAM ACTIVE`.
