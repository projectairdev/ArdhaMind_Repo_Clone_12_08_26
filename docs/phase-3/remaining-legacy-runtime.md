# Remaining legacy runtime

Still legacy: workspace context, broker funds/account presentation, portfolio,
configuration, intraday, validation, optimization, market-status, evening and
performance analytics reports. Operations remains legacy-produced. Historical
candles and option instruments have explicit contracts but their current cached
context producers do not expose raw snapshots to the application service.

Unresolved sources: real news/corporate events, consistent received timestamps,
raw candle provenance, complete per-contract option quote quality, and explicit
WebSocket-versus-REST source selection. Internal-fetch market/option pipelines
retain hardcoded fallback defects and were not made authoritative for snapshot
input; deleting duplicate engines remains prohibited in this phase.

Phase 4 should migrate raw feed adapters to `RuntimeSnapshot`, remove the legacy
dynamic calculation call, migrate React to canonical names, and retire duplicate
producers only after import and parity gates pass.
