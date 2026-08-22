# KITE CONNECTIVITY ARCHITECTURE & RUNTIME TRACE AUDIT

**Document Version:** 1.0.0 — Authoritative Connectivity Architecture Audit  
**Target Subsystems:** `src/broker/`, `src/application/`, `src/opportunity_engine/`  
**Environment:** Staging (`/opt/ardhamind/staging`)  
**Scope:** Complete runtime trace from Zerodha OAuth to execution readiness.

---

## 1. END-TO-END KITE RUNTIME TRACE

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 COMPLETE KITE INGESTION & PIPELINE TRACE                         │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘

1. Zerodha OAuth Login Flow
   └─► Handler: src/broker/services/authentication.py -> handle_oauth_callback()
   └─► Kite REST Call: kite.generate_session(request_token, api_secret)
   └─► Persistence: Token saved with expiration metadata in KiteSessionManager

2. Token & Profile Verification
   └─► Function: src/broker/services/broker_service.py -> validate_session()
   └─► Verification: kite.profile() and kite.margins() invoked
   └─► State Emitted: broker_auth_state = "AUTHENTICATED" (or "TOKEN_EXPIRED")

3. Python Broker Adapter & WebSocket Init
   └─► Adapter: src/broker/adapters/kite_ticker_adapter.py -> KiteTickerAdapter.connect()
   └─► Underlying Client: kiteconnect.KiteTicker(api_key, access_token, reconnect=True)
   └─► Reconnect State: "CONNECTING" -> "CONNECTED"

4. Instrument Master & Subscriptions
   └─► Manager: src/broker/services/subscription_manager.py -> subscribe_instruments()
   └─► Tokens: NIFTY 50 (256265), India VIX (264969), 50 Nifty Constituents, ATM ± 10 Option Strikes
   └─► Mode: MODE_FULL (LTP, Depth, Volume, OI)

5. Tick Reception & Liveness Monitoring
   └─► Ingestion: KiteTickerAdapter._on_kite_ticks()
   └─► Health Watchdog: src/broker/services/stream_health_monitor.py -> record_ticks()
   └─► Metrics: Computes tick_rate, latency_ms, last_source_observation_at

6. Normalization & Canonical State Evaluation
   └─► Service: src/application/workstation_state_service.py -> evaluate_canonical_state()
   └─► Sequence: Advances monotonic state sequence (#18420+)
   └─► Decoupling: broker_auth_state != websocket_state != market_feed_state

7. Delta & Event Stream Publishing
   └─► Bridge: src/server_bridge.py -> emit_canonical_state()
   └─► Transport: Node.js WebSocket Bridge -> Browser Frontend Dashboard

8. Opportunity & Intelligence Evaluation
   └─► Registry: src/opportunity_engine/registry.py -> evaluate_and_update()
   └─► Qualification Gate: src/opportunity_engine/qualification.py -> qualify_opportunity()
   └─► Stale Safety Gate: Blocks candidate if freshness_state == "STALE"
```

---

## 2. SINGLE RECONNECT OWNER AUDIT

- **Authoritative Reconnect Owner:** **1 (Exactly ONE)**
  - Module: [`src/broker/services/streaming_orchestrator.py`](file:///opt/ardhamind/staging/src/broker/services/streaming_orchestrator.py#L80) via `StreamingOrchestrator.connect_stream()` and `_reconnect_loop()`.
  - Concurrency Lock: Protected by `threading.Lock()` (`_connect_lock` and `_reconnect_lock`), eliminating race conditions, duplicate subscription storms, or parallel connection attempts.
