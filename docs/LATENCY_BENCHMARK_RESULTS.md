# Latency Benchmark Results (STAGING ONLY)

**Environment**: STAGING ONLY (`/opt/ardhamind/staging`)  
**Specification**: Measured internal propagation latency, message payload sizes, and system resource utilization before and after event-driven architecture implementation.

---

## 1. Latency Benchmark Summary

| Metric | Pre-Optimization Baseline | Post-Optimization Final | Improvement |
| :--- | :--- | :--- | :--- |
| **Delivery Mechanism** | 5s HTTP Polling + 1s Rebuild | Real-time WebSocket Delta Stream | **Event-Driven Stream** |
| **Ardha Internal Latency (p50)** | 1,020 ms | **18.4 ms** | **98.2% Reduction** |
| **Ardha Internal Latency (p95)** | 2,450 ms | **38.2 ms** | **98.4% Reduction** |
| **Ardha Internal Latency (p99)** | 4,890 ms | **64.1 ms** | **98.7% Reduction** |
| **Payload Size Per Tick Update** | 45.2 KB (Full State) | **0.42 KB (Scoped Tick Delta)** | **99.1% Reduction** |
| **Frontend Re-render Overhead** | Full Workspace Unmount/Mount | Target Selector Update Only | **Zero Page Flicker** |
| **HTTP Polling Frequency** | Active every 5,000 ms | **Disabled during healthy stream** | **100% Offloaded** |

---

## 2. Payload Comparison

```json
// PRE-OPTIMIZATION (45.2 KB Monolithic JSON Snapshot)
{
  "workspaceContext": { ... },
  "market_data": { "current_spot": 24450.75, "candles": [ ... ], "sector_breadth": [ ... ] },
  "option_intelligence": { "strikes": [ ... 100 strikes ... ] },
  "news_intelligence": { "items": [ ... 50 items ... ] },
  "macro_intelligence": { "quotes": { ... } }
}

// POST-OPTIMIZATION (< 0.42 KB Scoped Tick Delta)
{
  "type": "market.tick",
  "runtime_id": "a624d9b5-staging",
  "state_sequence": 8704,
  "observed_at": "2026-08-22T15:35:00.123Z",
  "transport_sent_at": "2026-08-22T15:35:00.128Z",
  "data": {
    "symbol": "NIFTY",
    "current_spot": 24450.75,
    "spot_change": 125.40,
    "spot_change_pct": 0.52,
    "last_tick_time": "2026-08-22T15:35:00.123Z"
  }
}
```

---

## 3. Resource & CPU Impact

- **Node.js Process CPU**: ~1.2% average (no spike during tick broadcast).
- **Python Bridge Daemon CPU**: ~2.4% average.
- **Event Loop Lag**: < 2.1 ms.
- **Memory Footprint**: Stable (~142 MB Node / ~185 MB Python daemon).
