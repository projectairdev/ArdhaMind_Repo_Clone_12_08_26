# Revised Cleanup Checkpoint Plan

The four-checkpoint sequence remains structurally sound but must reflect the read-only product decision and paper extraction boundary.

## Checkpoint 2 — provenance, canonical decisions and state contract

**Product objective:** Make every proposed Phase 1 field traceable and define the single read-only product contract.

**Architecture objective:** Complete field-level provenance; decide duplicate-module roles; add a versioned canonical workstation-state contract and backward-compatible serializer.

**Affected:** `docs/architecture-cleanup`, models/contracts, serializer tests, shared schema tooling. Application skeleton may be introduced but not activated.

**Excluded:** Pipeline behavior changes, UI migration, mock removal, engine deletion, AI integration and execution implementation.

**Acceptance:** Every major widget field maps to producer/source/freshness/fallback; state has stage status, provenance, warnings/errors and no execution state; old shape remains available.

**Tests:** Contract serialization, schema compatibility, unavailable/partial state, no execution fields capable of causing action.

**Rollback:** `v0.6-baseline`; checkpoint commit/tag created before moving on.

## Checkpoint 3 — application services and canonical read-only pipeline

**Product objective:** Produce trustworthy live intelligence without fabricated values.

**Architecture objective:** Extract application services and route validated observations through the canonical pipeline into canonical state.

**Affected:** `server_bridge.py`, new application services, canonical pipelines, provenance validators, integration tests.

**Excluded:** Legacy deletion, frontend visual redesign, OpenAI and paper code removal.

**Acceptance:** One internally consistent snapshot traverses every mandatory stage; missing/stale critical inputs block downstream output; optional failures stay isolated; bridge is materially thinner.

**Tests:** Full suite, canonical integration, blocked-input cases, daemon/IPC/WebSocket smoke, explicit no-order invocation.

**Rollback:** Checkpoint 2 commit/tag.

## Checkpoint 4 — duplicate consolidation and read-only broker boundary

**Product objective:** Remove ambiguity about which calculation and broker implementations are authoritative.

**Architecture objective:** Migrate risk, configuration, broker and strategy consumers one pair at a time; formalize paper extraction seams.

**Affected:** Duplicate packages, imports, adapters and import-boundary tests.

**Excluded:** Physical paper repository extraction, AI, broad UI redesign and live execution.

**Acceptance:** Canonical implementations own production flow; legacy imports are enumerated/deprecated or removed safely; root Kite shim no longer affects production; order methods remain unavailable.

**Tests:** Semantic regression, import boundaries, official Kite resolution, read-only gateway contract and full suite.

**Rollback:** Per-pair focused commits; checkpoint 3 tag.

## Checkpoint 5 — product-mode simplification, mock isolation and frontend migration

**Product objective:** Deliver the `LIVE INTELLIGENCE — READ ONLY` user experience.

**Architecture objective:** Remove Sample/Mock/Real user modes, isolate fixtures, remove execution/paper navigation, migrate React to canonical state and establish clear runtime ownership.

**Affected:** React layout/context/services, Express routes/state, workspace configuration, mock providers, paper runtime imports, health/provenance UI.

**Excluded:** Physical creation of the separate paper repository, OpenAI implementation and visual redesign beyond information architecture.

**Acceptance:** No production screen silently displays mock data; no order/exit endpoint or UI control exists; canonical state drives all retained pages; freshness/unavailable states are visible; paper capability is disconnected and extraction-ready.

**Tests:** Frontend critical pages, WebSocket reconnect/stale behavior, development fixtures, live-readonly smoke, negative execution tests, production bundle mock-import check.

**Rollback:** Checkpoint 4 tag.

## Recommended following phase

Checkpoint 6 should build historical intelligence persistence and professional market/option visualizations. Bounded OpenAI interpretation should follow only after canonical state, provenance and audit storage are stable.

