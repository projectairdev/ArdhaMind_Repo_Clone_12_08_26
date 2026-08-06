# AIR ArdhaMind Phase 1 Product Specification

## Product

AIR ArdhaMind observes real NIFTY market data, validates quality and freshness, analyzes NIFTY and NIFTY options, explains deterministic outputs, and assists a human trader. It never places or manages trades in Phase 1.

```text
Real data -> validation -> deterministic intelligence -> explanation -> human decision
```

## Operational profile

There is one user-facing profile: **LIVE INTELLIGENCE — READ ONLY**.

- Real Kite market and read-only account/session data
- Real timestamps, source and freshness metadata where available
- No sample, mock, practice or real-trading selector
- No paper portfolio, simulated execution or fake-data fallback
- No order placement, modification, cancellation or position exit

## Primary workspaces

1. NIFTY Live
2. Pre-Market Planner
3. Today’s Analysis
4. NEWS & UPDATES
5. Live Assistant
6. Settings

## Safety policy

Missing or invalid data is `Unavailable` or `Analysis blocked: <reason>`. Plausible numeric defaults are prohibited. Market-closed information must identify its final validated observation time. AI may explain validated engine outputs but may not calculate prices, bypass risk, invent levels or execute.

## Non-goals

Paper trading, portfolio accounting, execution, autonomous trading, OpenAI integration, professional chart libraries, pipeline recalibration and duplicate-engine consolidation are outside this phase.

