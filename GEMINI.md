# AIR ArdhaMind — Production Gemini Instructions

You are operating inside the PRODUCTION AIR ArdhaMind codebase on the Linode VPS.

## PRODUCT
AIR ArdhaMind is a READ-ONLY NIFTY 50 intelligence workstation.

Primary workspaces:
1. NIFTY Live
2. Live Assistant
3. Today's Analysis
4. Forward Outlook
5. Pre-Market Planner
6. Market Pulse
7. NEWS & UPDATES
8. Settings

## ABSOLUTE SAFETY INVARIANTS
- READ_ONLY must remain intact.
- Never add order placement, modify/cancel/exit, paper trading, autonomous execution, or broker mutation capabilities.
- Never fabricate market data.
- Never replace missing data with synthetic values.
- Never weaken execution guards.
- Never expose secrets, access tokens, API keys, .env contents, or credentials.
- Never delete production caches, session history, logs, or persisted canonical state unless explicitly instructed.
- Never modify nginx, firewall, SSH, DNS, TLS, system packages, or VPS infrastructure unless explicitly requested.
- Never restart ardhamind.service automatically after code changes unless explicitly approved.
- Never deploy, git push, force-push, tag, or commit without explicit approval.
- Never perform broad refactors or redesigns unless explicitly requested.

## ARCHITECTURAL PRINCIPLES
Preserve:
- CanonicalWorkstationState as frontend source of truth.
- Deterministic intelligence engines.
- DataQualityService freshness semantics.
- StreamingOrchestrator single-upstream-ticker invariant.
- Browser WebSocket transport independence from Kite broker authentication.
- Broker Auth, Stream Transport, Market Session, and Data Feed as separate state dimensions.
- StructuralLevelEngine evidence-based levels only.
- No arbitrary price offsets.
- OpenAI/Gemini may explain deterministic outputs but must not invent facts, prices, probabilities, or signals.

## KITE SESSION RULES
Kite broker authentication and KiteTicker transport are distinct.

Transient failures such as:
- HTTP 5xx
- network timeout
- browser websocket reconnect
- market closed
- stream idle
must NOT automatically invalidate a valid broker authentication session.

Authoritative auth rejection such as:
- HTTP 401
- HTTP 403
- ExpiredAccessTokenError
may invalidate authentication.

Explicit USER DISCONNECT must remain disconnected until the user explicitly authenticates again.

Opening/refreshing browser tabs must never create additional upstream KiteTicker instances.

Expected invariant:
- Node/Express processes: 1
- Python daemon: 1
- StreamingOrchestrator: 1
- Active KiteTicker: <= 1

## DATA TRUTH
Always distinguish:
- observed_at
- checked_at
- trading_date
- freshness_status

A refresh may update checked_at without changing observed_at.

Missing numeric data is NOT zero.

Off-market historical data must be labeled as previous/last-valid session with exact dates/times.

## WORKING METHOD
Before modifying code:
1. Inspect relevant files.
2. Trace the full render/backend path.
3. Identify root cause.
4. State exact files that need changes.
5. Make the smallest scoped change possible.

After modification:
1. Run targeted tests first.
2. Run relevant regression suites.
3. Run TypeScript if frontend changed.
4. Run production build if frontend/server changed.
5. Run git diff --check.
6. Do not restart production without explicit approval.

## PRODUCTION BEHAVIOR
This directory is live production:
`/opt/ArdhaMind`

Avoid destructive commands.

If a change could interrupt the running application, explain it before executing.

If uncertain, inspect rather than assume.
