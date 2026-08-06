# AIR ArdhaMind Phase 4 report

Phase 4 implements the canonical module decisions: one configuration package,
one risk package, one strategy package, one broker namespace and one live
analytical orchestration path. Old package names are removed from active source,
test doubles are test-only, and paper/execution code cannot enter the runtime.

The six-workspace React shell, canonical state 2.0.0, deterministic stage order,
compatibility serializer and analytical semantics are unchanged. Remaining
compatibility debt consists of `broker/compat`, historical dashboard serializers,
and isolated paper/execution fixtures retained for later extraction.

`server_bridge.py` fell from 1,130 to 981 lines in this phase. Final verification
and tag identity are recorded after the final run.
Rollback safely with `git switch --detach v0.9-canonical-runtime`, or create a
branch using `git switch -c rollback/phase3 v0.9-canonical-runtime`.

Recommendation for Phase 5: migrate React consumers from legacy camelCase fields
to canonical state, then remove the compatibility serializer field aliases. Do
not combine that with charts, AI, alerts, or persistence.
