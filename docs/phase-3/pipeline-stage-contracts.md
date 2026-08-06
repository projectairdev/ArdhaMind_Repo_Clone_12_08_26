# Pipeline stage contracts

`RuntimeSnapshot` is immutable and contains market session, broker session, NIFTY
market, candles, VIX, option instruments/quotes, expiry, news and optional account
inputs. Each carries source, instrument, observed/received timestamps, freshness,
quality, classification, payload, warnings and errors.

The authoritative order is:

`MarketContext -> OptionContext -> TradeContextBuilder -> MarketScoringPipeline -> OpportunityPipeline -> StrategyPipeline -> TradePlannerPipeline -> scenario adapter -> ConfidencePipeline -> RiskPipeline (risk_engine_v2) -> DecisionSupportReport -> deterministic explanation`.

Spot that is stale, blocked, invalid or unavailable blocks all authoritative
downstream stages. Missing options preserves market output and produces a degraded
explanation. Stale/partial options are explicitly degraded and propagate that
state to confidence and decision support. Stage exceptions block only unproduced
downstream stages and attach the error to the result.

Planner candidates are converted to scenarios containing conditions,
confirmations, invalidation, target zones, risk class, confidence and status.
Quantity, lots, capital, broker commands, approvals and execution state are never
copied. Closed sessions use `next_session_planning`, never live confirmation.
