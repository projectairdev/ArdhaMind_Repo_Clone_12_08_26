# Legacy compatibility

`CompatibilitySerializer.to_phase1_payload` is the only Phase 2 canonical-to-Phase
1 transport boundary. It maps canonical market, options, score, opportunity,
strategy, confidence, deterministic risk, decision support, explanation, news and
operations sections to existing camelCase names. It also exposes
`workspaceReadiness` and non-breaking `canonicalMetadata`.

Canonical fields populated now are status, source/timestamp quality, market and
option snapshots when present, deterministic sections mapped from current engine
outputs, decision-support state and readiness. `canonicalMetadata` lists fields
that remain legacy-produced. No unavailable section is converted to zero.

Temporarily legacy-produced fields include broker account/funds, portfolio,
tradePlan, configuration, intraday, validation, optimization, market-status,
evening and analytics reports. They are retained for Phase 1 rendering but are
not admitted into the canonical state. Real news is unavailable until a provider
is integrated. Phase 3 should migrate each analytical producer directly into the
canonical service, then remove its legacy field and the DecisionReport adapter.
