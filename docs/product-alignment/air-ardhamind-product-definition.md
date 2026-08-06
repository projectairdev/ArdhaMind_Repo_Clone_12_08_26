# AIR ArdhaMind Product Definition

## Definitive Phase 1 statement

**AIR ArdhaMind is a live, NIFTY-focused trading intelligence and decision-support workstation. It consumes validated real market and broker data, runs deterministic technical, option-chain, scoring, opportunity, strategy, confidence and risk analysis, and presents source-aware trade scenarios to a human trader. AI may explain validated results; the human decides. AIR ArdhaMind never places, modifies or cancels an order.**

Short form for an about screen:

> Live NIFTY and NIFTY-options intelligence for human traders—deterministic analysis, bounded AI explanation, and no order execution.

## Product identity

The authoritative name is **AIR ArdhaMind**. Existing documentation and package metadata also use generic names such as “NIFTY Option Finder,” “Market Intelligence Workstation,” and “Nifty Option Trading Workstation.” No confirmed `AIR ArthaMind`, `ArdhMind`, or `Ardha Mind` source identifier was found in the reviewed runtime files, but naming normalization should occur only after owner approval.

## Target user

An active NIFTY options trader who wants a trustworthy, continuously updated interpretation layer beside a broker terminal and retains full responsibility for trading decisions and execution.

## Supported scope

### Market

- NIFTY spot and NIFTY derivatives
- India VIX when available
- NIFTY option instruments, expiries, strikes and quotes
- NIFTY-relevant news and macro events
- Market-closed snapshots that are clearly labeled historical/cached

### Broker

- Zerodha Kite read-only authentication and session health
- Instrument master, quotes, ticks and historical candles
- Read-only account/profile information where operationally useful
- No order, position-exit or execution commands

### Deterministic analysis

- Price trend, structure, volatility and support/resistance
- Option-chain OI, PCR, max pain, IV and liquidity
- Market scoring and opportunity classification
- Strategy suitability
- Trade scenarios, confirmation and invalidation conditions
- Confidence and risk evaluation
- Intraday monitoring and historical intelligence

### AI assistance

Optional bounded explanation of already validated canonical outputs:

- Market Command Center narrative and “Why Today?”
- Option-chain interpretation
- Risk and trade-scenario explanation
- Pre-market, intraday and end-of-day summaries

AI is never a calculator, market-data source, risk gate, quantity authority or execution actor.

## Dashboard scope

1. Market Command Center
2. NIFTY Price and Trend Analysis
3. NIFTY Option-Chain Intelligence
4. Trade Assistant
5. Market Intelligence and News
6. Intraday Assistant
7. Historical Intelligence
8. System Health and Data Provenance
9. Settings and Broker Connection

## Alerts and reports

Phase 1 supports in-application alerts for stale/missing data, material regime changes, scenario confirmations/invalidations, broker/feed health and important news. External delivery channels are a later enhancement.

Reports include pre-market briefing, current market intelligence, intraday situation updates, trade-scenario records and end-of-day intelligence review. Reports must preserve their source snapshot and timestamps.

## Explicit non-goals

- Sample/demo mode in the production application
- Mock/paper user mode
- Paper portfolio, simulated fills or training journal
- Live order placement, modification, cancellation or emergency exit
- Autonomous or supervised trading bot
- AI-generated prices, levels, quantities or risk decisions
- Multi-broker or multi-market expansion during Phase 1
- Portfolio accounting and exchange reconciliation
- Institutional-grade backtesting in the current cleanup

## Safety and data-quality rules

1. Critical missing or stale inputs block dependent scenarios.
2. No numeric fake default may substitute for unavailable market data.
3. Every important displayed value carries source, observation time, freshness and quality.
4. Calculated values identify their method and dependencies.
5. Cached market-closed data is read-only and visibly historical.
6. AI receives only validated structured data and cannot call broker execution interfaces.
7. Server execution endpoints and UI execution controls must be absent in the final product.
8. Kite order methods remain unimplemented and tests prove that execution is impossible.

## User journey

```text
Start application
  -> validate configuration
  -> connect read-only Kite session
  -> validate instrument master
  -> start feeds
  -> verify timestamps and quality
  -> run canonical deterministic pipeline
  -> display command center and analysis
  -> monitor scenario confirmation/invalidation
  -> optionally explain validated outputs with AI
  -> record historical intelligence
  -> never place an order
```

## User-visible operational states

| State | What the user sees | Allowed calculations | Blocked outputs / warning |
|---|---|---|---|
| Connecting | Progress and dependency being contacted | Configuration validation only | All live analysis blocked |
| Connected | Kite session valid; feeds initializing | Read-only account/instrument checks | Recommendations wait for fresh feeds |
| Live | Green source and age indicators | Full pipeline | None beyond normal caveats |
| Delayed | Amber age and delayed-source badge | Non-time-critical context where thresholds permit | Intraday confirmations blocked when beyond stage limit |
| Stale | Red stale age and last observation | Historical display only | All dependent scenarios blocked |
| Partial | Available sections plus dependency list | Independent valid stages only | Dependent stages unavailable, never fabricated |
| Unavailable | Explicit empty state and cause | None for that section | Section outputs absent |
| Market closed | Last close time and snapshot label | End-of-day/historical calculations | No “live” or intraday claim |
| Broker disconnected | Connection remediation | Cached historical views only if labeled | Live market and account outputs blocked |
| Analysis blocked | Blocking dependency and stage | Earlier valid stages may display | No downstream trade scenario |
| AI unavailable | Deterministic explanation shown | All deterministic engines continue | No silent mock AI narrative |
| News unavailable | News error and last successful scan | Market pipeline may continue with news-independent status | No invented neutral news claim |

