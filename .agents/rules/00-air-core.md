# AIR Core Operational Rules

These fundamental rules govern all AI assistance on **AIR ArdhaMind**.

---

## 1. Investigation & Diagnosis
- **Inspect Before Modifying**: Always inspect codebase, configuration, and logs using code search tools before proposing or executing code changes.
- **Root Cause Fixes**: Never resolve errors by masking symptoms, swallowing exceptions, returning dummy fallbacks, commenting out broken assertions, or deleting failing unit tests. Trace back to root cause.
- **Empirical Evidence**: Base all diagnostic hypotheses strictly on empirical log evidence and code inspection.

## 2. Scope & Bounded Changes
- **Bounded Implementation**: Solve only the single causal issue in approved scope. Nearby unrelated technical debt must not be silently included.
- **Scope Expansion Protocol**: If root cause requires modifying protected scope or expanding authorized boundaries, stop and report `SCOPE_EXPANSION_REQUIRED`.
- **Preserve Unrelated Code**: Retain existing docstrings, comments, and architecture unrelated to the active task.

## 3. Server State & Security
- **Server-Authoritative State**: Critical analytical calculations belong on the server. Client interfaces must consume server state without duplicating mathematical logic.
- **Zero Secrets Exposure**: Never log or hardcode API credentials, Kite tokens, or secrets.
- **Truthful Data**: Never fabricate production or market data. Use authentic provider data or explicit `UNAVAILABLE` status.
