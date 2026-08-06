# Server bridge cleanup

Phase 4 began at 1,130 lines. It removed the embedded 113-line mock Kite client,
execution/mode command registration, execution CLI arguments, and obsolete
parameter extraction. The bridge retains daemon/CLI entry, read-only login/logout
compatibility, feed refresh, canonical pipeline/state assembly and transport.

The final bridge is 981 lines, a reduction of 149 lines in Phase 4 and 996 lines
across Phases 3–4. HTTP execution endpoints remain
410 tombstones in the Express server so old clients fail explicitly; no request
can reach Python broker execution.
