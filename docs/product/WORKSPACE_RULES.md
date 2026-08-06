# Workspace Rules

| Workspace | Required inputs | Optional inputs | Blocking/degraded behavior |
|---|---|---|---|
| NIFTY Live | None for access | Market, option and score state | Cards show unavailable independently |
| Pre-Market Planner | Historical/final session snapshot | News and global cues | Waiting reason when no prior context |
| Today’s Analysis | Validated market context | News, options, contribution data | Blocked until market context exists |
| NEWS & UPDATES | Real news source | Classification/impact | Provider-unavailable state; no fixtures |
| Live Assistant | Validated market context and analytical outputs | News narrative | Blocked until fresh analysis exists |
| Settings | None | All service diagnostics | Always accessible |

No workspace exposes order, quantity, portfolio, paper or execution controls.

