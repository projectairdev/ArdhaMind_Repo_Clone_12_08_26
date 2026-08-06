# Runtime provenance summary

The field-level evidence and migration decisions are in
`docs/architecture-cleanup/runtime-provenance.md`. The verified live route is
React `WorkstationStateContext` -> browser WebSocket -> Express state relay ->
`src/server_bridge.py:run_daemon` -> existing services/pipelines -> broker/feed or
calculation source. Phase 2 inserts validation/canonical state/compatibility
serialization immediately before transport.

Market and options remain sourced from the current Kite-backed feed paths when
available. Derived analytics remain calculated. News has no production provider
and is explicitly unavailable. Timestamp gaps now cause blocked/unavailable
metadata rather than plausible values. Detailed duplicate-family import evidence
and retirement gates are in `canonical-module-decisions.md`.
