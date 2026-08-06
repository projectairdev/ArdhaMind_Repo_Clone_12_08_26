# Canonical state schema

Phase 2 introduces `CanonicalWorkstationState` version `2.0.0` in
`src/models/canonical_workstation_state.py`. The producer is
`WorkstationStateService.build_from_legacy`; it owns the monotonic process-local
sequence and UTC generation timestamp.

The contract contains session/application/broker/feed status; market, technical,
option, score, opportunity and strategy sections; scenarios, confidence, risk,
decision support and explanation; news, optional read-only account summary,
operations, workspace readiness, quality metadata, warnings and errors.

The recursive read-only sanitizer rejects/removes execution commands, quantity,
lots/capital allocation, paper/virtual portfolio state, and mock/sample/trading
mode fields. `read_only_account_summary` is nullable and market intelligence does
not depend on it.

`ValueMetadata` records source, instrument, observed/received/generated times,
age, freshness, quality, classification, calculation method, dependencies,
warnings and error. Production enums deliberately exclude mock and sample.

## Dependency behavior

- Blocked spot blocks technicals, score, opportunity, confidence-dependent
  assistance and scenarios; news remains independent.
- Blocked options preserve spot analysis and degrade option-dependent workspaces.
- Missing news degrades Today's Analysis and makes NEWS & UPDATES unavailable.
- Closed sessions classify validated snapshots as historical/market_closed.
- Expired broker sessions explicitly require reconnect and block live sources.
