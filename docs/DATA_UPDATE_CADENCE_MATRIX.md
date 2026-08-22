# Data Update Cadence Matrix (STAGING ONLY)

**Environment**: STAGING ONLY (`/opt/ardhamind/staging`)  
**Specification**: Cadence inventory across Provider Ingest, Server Rebuild, API Delivery, and Frontend Refresh.

---

## 1. Cadence Inventory Across Architectural Layers

| Data Family | Source Provider | Server Ingest Cadence | Server Rebuild Cadence | API Delivery Cadence | Frontend Refresh Method & Cadence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **NIFTY Tick Data** | Zerodha Kite WS | Ticks (~1,000 ms) | 1,000 ms | Event / SSE Bridge | WebSocket Stream / 1,000 ms Poll |
| **NIFTY Intraday Candles** | Kite Historical API | 60,000 ms (1m bar) | 60,000 ms | State Poll (5,000 ms) | 5,000 ms Polling |
| **Option Chain Ticks & OI** | NSE Option Engine | 5,000 ms | 5,000 ms | State Poll (5,000 ms) | 5,000 ms Polling |
| **GIFT Nifty / Global Cues** | Global Macro Feed | 15,000 ms | 15,000 ms | State Poll (5,000 ms) | 5,000 ms Polling |
| **Institutional Flows (FII/DII)**| NSDL / NSE Daily | 300,000 ms (EOD) | 300,000 ms | State Poll (5,000 ms) | 5,000 ms Polling |
| **Verified Financial News** | RSS / Publisher Pipeline | 60,000 ms | 60,000 ms | `/api/news/latest` | 60,000 ms Polling / Manual Refresh |
| **Economic Calendar** | Macro Calendar Pipeline | 300,000 ms | 300,000 ms | `/api/macro/calendar` | 300,000 ms Polling |
| **Broker Session Health** | Zerodha OAuth Heartbeat | 10,000 ms | 10,000 ms | `/api/broker/health` | 10,000 ms Polling |

---

## 2. Streaming & Ingestion Architecture

### Zerodha Kite Connect WebSocket Stream
- **Path**: `wss://ws.kite.trade` &rarr; `src/market_data/zerodha_feed.py` &rarr; `KiteFeedHandler`
- **Ingestion**: Listens for NIFTY spot tick updates (mode: `full` or `quote`).
- **Processing**: Publishes ticks to internal `StateEngine` queue.

### Server-to-Frontend WebSocket Bridge
- **Path**: `ws://localhost:3000/api/ws` &rarr; `src/frontend/context/WorkstationStateContext.tsx`
- **Bridge Events**: Sends `state_update`, `phase3_order_updated`, `phase3_positions_updated`, `phase3_safety_updated`.
- **Fallback Mechanism**: Standard HTTP polling (`/api/state/canonical`) at `5,000 ms` interval if WebSocket connection is degraded.
