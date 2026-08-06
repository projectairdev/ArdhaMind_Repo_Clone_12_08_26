# Controlled Architecture Migration Plan

## Guardrails

- Preserve public DTO and report contracts during early migration.
- Keep the application runnable after each reviewed checkpoint.
- Do not enable live order placement, modification or cancellation.
- Do not fabricate unavailable market values.
- Preserve deterministic trading, scoring and risk behavior unless fixing a separately identified defect.
- Extract and redirect behavior incrementally; do not create a parallel V3 architecture.
- Do not delete a legacy package until runtime imports, test imports and compatibility gaps are resolved.

## Checkpoint 1 — safe baseline

- Initialize Git and establish the pre-cleanup baseline.
- Exclude secrets, local state, generated environments, dependencies and build output.
- Restore a meaningful TypeScript quality boundary.
- Record baseline tests, build, smoke behavior, dependencies and risks.
- Tag the baseline and create the cleanup branch.

## Checkpoint 2 — canonical state and application skeleton

- Complete field-level runtime provenance mapping.
- Record canonical-module decisions for every duplicate pair.
- Define a versioned canonical workstation-state contract with provenance and freshness.
- Add a compatibility serializer for the existing React/Express shape.
- Introduce application-service module boundaries without changing trading behavior.

## Checkpoint 3 — bridge extraction and pipeline integration

- Incrementally extract command routing, scheduling, state serialization and runtime services.
- Route validated inputs through the canonical domain pipeline.
- Represent critical missing input as blocked/unavailable.
- Keep optional-section failures isolated.
- Add end-to-end synthetic snapshot integration coverage.

## Checkpoint 4 — duplicate-engine migration

- Migrate risk, configuration, broker, strategy and paper systems one pair at a time.
- Add compatibility adapters and import-boundary tests.
- Deprecate before removing.
- Keep live execution explicitly unavailable.

## Checkpoint 5 — mock isolation and frontend ownership

- Introduce explicit development, test, paper and live-readonly modes.
- Remove silent mock fallbacks from production-like modes.
- Make Python authoritative for business state, Express a transport relay and React a render/UI-preference client.
- Migrate widgets incrementally to canonical state and expose source/freshness/unavailable status.

Each checkpoint ends with a review summary and verification. No subsequent checkpoint starts automatically.

