# Architecture Cleanup Decisions

## ADR-001 — Initialize a new repository baseline

**Status:** Accepted on 2026-08-06.

No Git metadata or recoverable history exists. Initialize a new repository on `main`, commit the complete safe pre-cleanup source snapshot, tag it `v0.6-baseline`, and perform cleanup work on `architecture/canonical-runtime`.

Generated environments, dependency trees, build products, caches, local databases, logs, sessions and secrets are excluded from the baseline. Git identity is taken from the existing user configuration and is not invented by the cleanup process.

## ADR-002 — Preserve behavior during consolidation

**Status:** Accepted.

Checkpoint 1 changes repository configuration and documentation only. Analytical rules, thresholds, risk semantics, runtime orchestration, mocks and duplicate engines remain unchanged.

## ADR-003 — Provisional canonical directions

**Status:** Proposed pending the detailed dependency/provenance map.

- `broker/` over `broker_engine/`
- `risk_engine_v2/` over `risk_engine/`
- `configuration_engine/` over `config_engine/`
- `strategy_engine/` for strategy suitability
- `paper_trading/` for paper domain management
- `pipeline/` for workflow orchestration
- React for visual presentation
- `models/` for domain contracts
- `explanation_engine/` for deterministic fallback narratives

These choices are not deletion authorization. Unique capabilities and compatibility consumers must first be mapped.

## ADR-004 — Exclude generated environments and scope TypeScript

**Status:** Accepted.

Python environments, Node dependencies, output directories and local runtime state are reproducible or private and must not enter Git. TypeScript includes only `server.ts`, `vite.config.ts`, and TypeScript/TSX files below `src/`; JavaScript in Python environments is not part of the application project.

## ADR-005 — Retain the root Kite shim temporarily

**Status:** Accepted with risk.

`kiteconnect.py` is retained in the baseline to preserve behavior and because multiple imports may resolve through it. It is documented as a high-risk package-shadowing compatibility shim. A later checkpoint must move mock behavior behind explicit development/test providers.

## ADR-006 — Live execution remains disabled

**Status:** Accepted.

The existing unimplemented Kite order methods remain unchanged. Architecture cleanup must not make real order placement, modification or cancellation possible.

