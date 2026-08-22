# Low-Latency Event-Driven Architecture (STAGING ONLY)

**Environment**: STAGING ONLY (`/opt/ardhamind/staging`)  
**Specification**: High-performance, event-driven market data delivery pipeline for AIR ArdhaMind.

---

## 1. High-Level Event-Driven Delivery Flow

```
+-----------------------------+
| Zerodha KiteConnect WS Tick | (T0: Provider Exchange Observation Timestamp)
+--------------+--------------+
               |
               v (T1: Ardha Server Receive)
+--------------+--------------+
|   Python Feed Normalizer    | (T2: Normalized Tick Ready)
+--------------+--------------+
               |
               v (T3: Canonical State / Event Delta Committed)
+--------------+--------------+
|  Python-to-Node IPC Bridge  | (Line-Delimited JSON IPC)
+--------------+--------------+
               |
               v (T4: Outbound Serialization Complete)
+--------------+--------------+
|   Node WebSocketServer (ws) | (ws://localhost:3000/api/ws)
+--------------+--------------+
               |
               v (T5: Browser Receives Frame)
+--------------+--------------+
| WorkstationStateContext Store| (T6: Store State Committed)
+--------------+--------------+
               |
               v (T7: Target Component Paint)
+--------------+--------------+
|     NiftyLiveWorkspace UI   | (< 50 ms Ardha Internal T7 - T1)
+-----------------------------+
```

---

## 2. Latency Boundary Clocks (T0 – T7)

| Boundary | Clock Definition | Description | Typical Duration |
| :--- | :--- | :--- | :--- |
| **T0** | Provider Timestamp | `observed_at` (Exchange tick creation) | Upstream |
| **T1** | Server Receive Timestamp | `server_received_at` (Python process ingress) | Upstream &rarr; Ardha |
| **T2** | Normalizer Complete | Normalized tick object ready | T2 - T1 (< 2 ms) |
| **T3** | Canonical Commit | Canonical state & delta sequence committed | T3 - T2 (< 5 ms) |
| **T4** | Outbound Stream Sent | Node WS `transport_sent_at` | T4 - T3 (< 3 ms) |
| **T5** | Browser Ingress | `browser_received_at` (WebSocket `onmessage`) | T5 - T4 (< 10 ms) |
| **T6** | Frontend Store Commit | `store_committed_at` (React context updated) | T6 - T5 (< 4 ms) |
| **T7** | Component Paint | `render_painted_at` (`requestAnimationFrame`) | T7 - T6 (< 16 ms) |

- **Upstream Latency**: `T1 - T0` (Provider/ISP network latency outside Ardha control).
- **Ardha Internal Propagation Latency**: `T7 - T1` (Measured with monotonic `performance.now()` clocks). Target: **< 50 ms p95**.
- **Total Observed Latency**: `T7 - T0`.

---

## 3. Hot Path vs Heavy Background Derivation Separation

To prevent heavy AI/scenario computations from blocking tick delivery, calculations are strictly split into two paths:

1. **Hot Path (Immediate Event Delivery)**:
   - NIFTY spot tick updates (`current_spot`, `spot_change`, `spot_change_pct`, `last_tick_time`).
   - Session high / low / VWAP incremental updates.
   - Option LTP & OI tick updates.
   - Emits < 1 KB scoped JSON deltas immediately upon tick receipt.

2. **Heavy Background Path (Coalesced / Periodic)**:
   - Market Intelligence scenario re-scoring (runs on 15s interval or level-break triggers).
   - Full option chain Max Pain / IV surface reconstruction.
   - Full news sentiment aggregation.
