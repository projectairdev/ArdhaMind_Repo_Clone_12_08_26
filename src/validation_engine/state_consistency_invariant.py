# src/validation_engine/state_consistency_invariant.py
"""
AIR ArdhaMind State Consistency Invariant Engine.

Enforces cross-system operational and lifecycle state consistency rules to prevent
contradictory UI state combinations, invalid lifecycle overwrites, or false attention flags.
"""
from typing import Any, Dict, List


def verify_state_consistency_invariants(canonical_state: Dict[str, Any]) -> List[str]:
    """
    Evaluates the canonical workstation state against lifecycle and operational invariants.
    Returns a list of violation messages (empty list if all invariants pass).
    """
    violations = []
    if not isinstance(canonical_state, dict):
        return ["INVALID_STATE: Canonical state is not a dictionary."]

    market_session = canonical_state.get("market_session") or {}
    sess_status = str(market_session.get("status") or "").upper()
    is_closed = bool(market_session.get("is_closed") or sess_status in ("CLOSED", "POST_CLOSE", "HOLIDAY"))

    # INVARIANT 1: MARKET_CLOSED must not coexist with present-tense "Regular market session active."
    pre_market = canonical_state.get("pre_market_report") or (canonical_state.get("session_story") or {}).get("pre_market_report") or {}
    opening_val = pre_market.get("opening_validation") or {}
    val_summary = str(opening_val.get("summary") or "")

    if is_closed and "Regular market session active" in val_summary:
        violations.append("INVARIANT_VIOLATION_1: MARKET_CLOSED coexists with present-tense 'Regular market session active' in opening validation.")

    # INVARIANT 2: Expected closed-market transport inactivity must not automatically force ATTENTION_REQUIRED
    broker_status = canonical_state.get("broker_status") or {}
    broker_state = str(broker_status.get("status") or "").upper()
    is_authenticated = broker_state == "CONNECTED" or bool(broker_status.get("session_valid"))

    readiness = canonical_state.get("workspace_readiness") or {}
    overall_readiness = str(readiness.get("overall_state") or "").upper()

    if is_authenticated and is_closed and overall_readiness in ("ATTENTION_REQUIRED", "BLOCKED"):
        # Check if there is an actual critical failure or if it's purely idle stream
        feed_status = canonical_state.get("market_feed_status") or {}
        stream_status = str(feed_status.get("stream_status") or "").upper()
        if stream_status in ("CONNECTED", "IDLE", "CLOSED", "STANDBY", "LIVE"):
            violations.append("INVARIANT_VIOLATION_2: Authenticated closed-market session marked ATTENTION_REQUIRED without genuine system failure.")

    # INVARIANT 3: Finalized previous-session analytical truth must not be overwritten by empty post-close recomputation
    todays_analysis = canonical_state.get("todays_analysis") or (canonical_state.get("session_story") or {}).get("todays_analysis") or {}
    analysis_status = str(todays_analysis.get("analysis_status") or "").upper()
    trend_score = todays_analysis.get("trend_score")
    conviction = todays_analysis.get("conviction")

    snapshots = canonical_state.get("snapshots_history") or []
    has_snapshots = len(snapshots) > 0

    if is_closed and has_snapshots and (analysis_status == "INSUFFICIENT_DATA" or (trend_score == 0.0 and conviction == 0.0)):
        violations.append("INVARIANT_VIOLATION_3: Closed session with valid snapshot history reports empty/uninitialized Today's Analysis.")

    # INVARIANT 4: Educational/explainer content must be penalized in news relevance
    news_items = (canonical_state.get("news_intelligence") or {}).get("items") or []
    explainer_terms = ("how to", "what is", "understanding ", "guide to", "explainer:", "basics of")
    for item in news_items:
        headline = str(item.get("headline") or "").lower()
        rel_score = float(item.get("nifty_relevance_score") or 0.0)
        impact = str(item.get("impact_level") or "").upper()
        if any(term in headline for term in explainer_terms):
            if rel_score > 4.0 or impact in ("HIGH", "CRITICAL"):
                violations.append(f"INVARIANT_VIOLATION_4: Explainer headline '{headline[:30]}' unpenalized (relevance {rel_score}, impact {impact}).")

    # INVARIANT 5: READ_ONLY Safety Invariant
    app_status = canonical_state.get("application_status") or {}
    read_only_policy = canonical_state.get("read_only_policy") or {}
    orders_enabled = app_status.get("order_execution_enabled") or read_only_policy.get("orders_enabled")
    if orders_enabled is True:
        violations.append("INVARIANT_VIOLATION_5: READ_ONLY safety invariant breached! Orders enabled.")

    return violations
