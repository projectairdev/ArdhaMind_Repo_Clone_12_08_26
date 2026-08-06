# Live runtime before and after

Before: feed refresh and analytical synthesis occurred through several bridge
paths, and Phase 2 state construction consumed their mutable legacy dictionary.

After: the daemon freezes one input snapshot, validates it, invokes one
application pipeline service, overlays only that result as the authority for all
migrated fields, creates one canonical state sequence, serializes once, and emits
one state message. Input observed timestamps remain unchanged while `generated_at`
belongs to the assembled refresh.

Migrated fields are market, options, score, opportunity, strategy, scenarios,
confidence, deterministic risk, decision support and explanation. News is bounded
as real or unavailable. Operations and non-analytical legacy reports remain
compatibility fields.
