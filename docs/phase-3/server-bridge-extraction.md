# Server bridge extraction

Phase 3 began with `src/server_bridge.py` at 1,977 lines and ended at 1,130 lines.
Analytical orchestration,
runtime input validation, blocking and coherent result assembly now live in
`src/application`. Phase 2 already owned canonical state and compatibility
serialization there.

The bridge retains CLI/command routing, service initialization, feed polling,
cache refresh, limited ancillary report coordination and JSON transport. The
836-line legacy dynamic analytical producer and every call to it were removed.
All analytical commands and daemon state now use `AnalyticalPipelineResult`.

Further line reduction requires separating command routing and removing legacy
evening/analytics/configuration report creation; those changes are outside Phase
3 and should follow consumer migration.
