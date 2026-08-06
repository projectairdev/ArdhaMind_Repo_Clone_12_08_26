# Failure Handling

Supported visible states are Initializing, Loading, Unavailable, Delayed, Stale, Blocked, Market Closed, Kite Session Expired, Feed Disconnected, Partial Data and Service Error.

- Disconnection never crashes the shell; Settings remains accessible.
- Stale values show their last successful timestamp and cannot drive live confirmation language.
- Market closed shows the final validated snapshot, never zero-filled live cards.
- Missing option quotes block option-dependent scenarios.
- Missing news leaves the news workspace unavailable but does not fabricate neutral sentiment.
- AI failure uses the deterministic explanation and is explicitly labeled.

