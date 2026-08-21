# src/live_assistant/intent_taxonomy.py
"""
User Intent Taxonomy, Answer Act Resolver & Query Decomposer for Live Assistant.
Defines intent categories, temporal targets, answer acts, and query decomposition.
"""
from enum import Enum
from dataclasses import dataclass
from typing import List, Set, Optional, Tuple, Dict, Any


class UserIntent(str, Enum):
    # Conversational & Meta Intents
    GREETING = "GREETING"
    CASUAL_CONVERSATION = "CASUAL_CONVERSATION"
    CLARIFICATION = "CLARIFICATION"
    EDUCATIONAL = "EDUCATIONAL"
    FOLLOW_UP = "FOLLOW_UP"

    # Market Domain Intents
    MARKET_SUMMARY = "MARKET_SUMMARY"
    WHY_EXPLANATION = "WHY_EXPLANATION"
    TRADE_OPPORTUNITY = "TRADE_OPPORTUNITY"
    ENTRY_TIMING = "ENTRY_TIMING"
    OPTIONS_DERIVATIVES = "OPTIONS_DERIVATIVES"
    BREADTH_SECTORS_HEAVYWEIGHTS = "BREADTH_SECTORS_HEAVYWEIGHTS"
    NEWS_EVENTS = "NEWS_EVENTS"
    SESSION_HISTORY = "SESSION_HISTORY"
    PREMARKET_TOMORROW = "PREMARKET_TOMORROW"
    SYSTEM_DATA_STATUS = "SYSTEM_DATA_STATUS"


class TemporalTarget(str, Enum):
    PREVIOUS_COMPLETED_SESSION = "PREVIOUS_COMPLETED_SESSION"
    CURRENT_PRE_MARKET = "CURRENT_PRE_MARKET"
    LIVE_CURRENT = "LIVE_CURRENT"


class AnswerAct(str, Enum):
    SUMMARY = "SUMMARY"
    CAUSE = "CAUSE"
    EXPLANATION = "EXPLANATION"
    COMPARISON = "COMPARISON"
    CURRENT_STATE = "CURRENT_STATE"
    ACTION = "ACTION"
    ENTRY_READINESS = "ENTRY_READINESS"
    RISK = "RISK"
    DEFINITION = "DEFINITION"
    SYSTEM_STATUS = "SYSTEM_STATUS"
    PRIORITIZATION = "PRIORITIZATION"
    EVENT_CALENDAR = "EVENT_CALENDAR"


@dataclass
class SubQuery:
    text: str
    intents: List[UserIntent]
    temporal_target: TemporalTarget
    answer_act: AnswerAct


# Conversational Keywords
GREETING_KEYWORDS = [
    "hi", "hello", "good morning", "good afternoon", "good evening", "hey",
    "hii", "hiii", "namaste", "hi there", "greetings", "yo", "hello there"
]

CASUAL_KEYWORDS = [
    "thanks", "thank you", "got it", "okay", "ok", "cool", "perfect", "great", "nice"
]

EDUCATIONAL_PATTERNS = [
    "what is pcr", "what is max pain", "what is vwap", "what is vix",
    "what does pcr mean", "what does max pain mean", "explain pcr", "explain vwap",
    "define pcr", "define max pain", "define vwap"
]

CLARIFICATION_PATTERNS = [
    "explain that simply", "make it simpler", "simpler", "simplify",
    "what do you mean", "tell me more", "elaborate"
]

YESTERDAY_PATTERNS = [
    "yesterday", "previous session", "last session", "what happened yesterday",
    "how was yesterday", "market yesterday", "yesterday's session", "yesterday's market"
]

PREMARKET_PATTERNS = [
    "this morning", "at open", "expected open", "morning bias", "what are we expecting at open",
    "expecting at open", "opening setup", "today's setup", "pre-market", "pre market"
]

# Market Domain Keywords
INTENT_KEYWORDS = {
    UserIntent.MARKET_SUMMARY: [
        "happening", "market today", "nifty doing", "current view", "overview",
        "summary", "market status", "market view", "nifty state", "how's the market",
        "how are things looking", "current picture"
    ],
    UserIntent.WHY_EXPLANATION: [
        "why", "reason", "because", "explain", "why is", "why did", "drop", "surge",
        "rationale", "evidence for", "why that much raise", "why that raise", "why it rose"
    ],
    UserIntent.TRADE_OPPORTUNITY: [
        "trade", "setup", "opportunity", "buy ce", "buy pe", "option setup",
        "strike active", "qualified", "best trade", "signal", "trade idea", "can i trade"
    ],
    UserIntent.ENTRY_TIMING: [
        "enter now", "entry", "timing", "should i wait", "confirmation",
        "trigger happened", "entered", "entry condition", "enter immediately", "should i enter"
    ],
    UserIntent.OPTIONS_DERIVATIVES: [
        "pcr", "max pain", "option wall", "call wall", "put wall", "oi",
        "open interest", "call writing", "put writing", "iv", "derivatives", "options"
    ],
    UserIntent.BREADTH_SECTORS_HEAVYWEIGHTS: [
        "sector", "breadth", "heavyweight", "moving nifty", "contributing",
        "advances", "declines", "leading sector", "stock support", "broad or concentrated", "biggest contributor"
    ],
    UserIntent.NEWS_EVENTS: [
        "news", "headline", "event", "catalyst", "announcement", "fii", "dii",
        "institutional", "macro", "fed", "rbi", "fii cause", "top news", "important news",
        "news today", "market news", "news risk", "scheduled event", "which story",
        "news that might affect", "events today", "events scheduled"
    ],
    UserIntent.SESSION_HISTORY: [
        "happened today", "changed since", "timeline", "story",
        "earlier", "session history", "failed thesis"
    ],
    UserIntent.PREMARKET_TOMORROW: [
        "tomorrow", "carry-forward", "carry forward", "overnight"
    ],
    UserIntent.SYSTEM_DATA_STATUS: [
        "data live", "broker connected", "stale", "fresh", "feed status",
        "system status", "health", "latency", "provider health"
    ]
}


def resolve_answer_act(query: str, intents: List[UserIntent]) -> AnswerAct:
    """Resolves what kind of answer structure the user is requesting."""
    q_clean = query.strip().lower()

    if any(pat in q_clean for pat in ["top news", "important news", "which story", "what news", "which news", "news that might affect", "biggest news risk", "news risk", "which story matters"]):
        return AnswerAct.PRIORITIZATION
    if any(pat in q_clean for pat in ["what time", "event time", "next event", "scheduled event", "calendar", "rbi time", "fed time", "when is the event"]):
        return AnswerAct.EVENT_CALENDAR
    if any(pat in q_clean for pat in ["why", "why so much", "why bullish", "why that much", "why did", "why it rose", "reason", "because", "drove", "what caused"]):
        return AnswerAct.CAUSE
    if any(pat in q_clean for pat in ["broad or concentrated", "move actually big", "structure bullish", "broad based", "compare", "vs", "versus", "concentrated"]):
        return AnswerAct.COMPARISON
    if any(pat in q_clean for pat in ["should i enter", "enter now", "can i trade", "what should i do"]):
        return AnswerAct.ACTION
    if any(pat in q_clean for pat in ["risk", "invalidate", "stop loss", "downside"]):
        return AnswerAct.RISK
    if any(pat in q_clean for pat in EDUCATIONAL_PATTERNS):
        return AnswerAct.DEFINITION
    if UserIntent.PREMARKET_TOMORROW in intents:
        return AnswerAct.EXPLANATION
    if UserIntent.SESSION_HISTORY in intents and not any(k in q_clean for k in ["why", "reason", "drove", "cause"]):
        return AnswerAct.SUMMARY
    if UserIntent.GREETING in intents:
        return AnswerAct.DEFINITION
    if UserIntent.NEWS_EVENTS in intents:
        return AnswerAct.PRIORITIZATION
    return AnswerAct.CURRENT_STATE


def classify_user_query_with_temporal(
    query: str, previous_intents: Optional[List[UserIntent]] = None
) -> Tuple[List[UserIntent], TemporalTarget]:
    """
    Multi-dimensional classifier returning (domain_intents, temporal_target).
    """
    q_clean = query.strip().lower()
    words = [w.strip(".,!?") for w in q_clean.split()]

    temporal_target = TemporalTarget.LIVE_CURRENT

    # Stage 1: Check Pure Greeting
    if any(q_clean == kw or q_clean.startswith(kw + " ") or q_clean.endswith(" " + kw) for kw in GREETING_KEYWORDS):
        if len(words) <= 3 and not any(m_kw in q_clean for m_kw in ["market", "nifty", "trade", "setup", "pcr", "open", "yesterday"]):
            return ([UserIntent.GREETING], TemporalTarget.LIVE_CURRENT)

    # Stage 2: Check Casual Acknowledgment
    if len(words) <= 3 and any(q_clean == kw for kw in CASUAL_KEYWORDS):
        return ([UserIntent.CASUAL_CONVERSATION], TemporalTarget.LIVE_CURRENT)

    # Stage 3: Educational
    if any(pat in q_clean for pat in EDUCATIONAL_PATTERNS):
        return ([UserIntent.EDUCATIONAL, UserIntent.OPTIONS_DERIVATIVES], TemporalTarget.LIVE_CURRENT)

    # Stage 4: Yesterday
    if any(pat in q_clean for pat in YESTERDAY_PATTERNS):
        temporal_target = TemporalTarget.PREVIOUS_COMPLETED_SESSION
        detected = {UserIntent.SESSION_HISTORY}
        if any(w in q_clean for w in ["why", "reason", "raise", "rose"]):
            detected.add(UserIntent.WHY_EXPLANATION)
        if "options" in q_clean or "pcr" in q_clean:
            detected.add(UserIntent.OPTIONS_DERIVATIVES)
        return (list(detected), temporal_target)

    # Stage 5: Pre-Market
    if any(pat in q_clean for pat in PREMARKET_PATTERNS):
        temporal_target = TemporalTarget.CURRENT_PRE_MARKET
        detected = {UserIntent.PREMARKET_TOMORROW}
        if "why" in q_clean:
            detected.add(UserIntent.WHY_EXPLANATION)
        if "options" in q_clean or "pcr" in q_clean:
            detected.add(UserIntent.OPTIONS_DERIVATIVES)
        return (list(detected), temporal_target)

    # Stage 6: Clarification
    if any(pat in q_clean for pat in CLARIFICATION_PATTERNS):
        detected: Set[UserIntent] = {UserIntent.CLARIFICATION}
        if previous_intents:
            for prev in previous_intents:
                detected.add(prev)
        return (list(detected), temporal_target)

    # Stage 7: Standard Domain Classification
    detected: Set[UserIntent] = set()
    for intent, keywords in INTENT_KEYWORDS.items():
        for kw in keywords:
            if kw in q_clean:
                detected.add(intent)
                break

    # Stage 8: Follow-up Inheritance
    if previous_intents:
        # Filter previous intents to only include active domain topics (avoiding historical clutter)
        clean_prev = [p for p in previous_intents if p not in (UserIntent.MARKET_SUMMARY, UserIntent.SESSION_HISTORY, UserIntent.FOLLOW_UP)]
        if "why" in q_clean or "reason" in q_clean:
            detected.add(UserIntent.FOLLOW_UP)
            detected.add(UserIntent.WHY_EXPLANATION)
            for prev in clean_prev:
                detected.add(prev)
        elif "options" in q_clean or "pcr" in q_clean:
            detected.add(UserIntent.FOLLOW_UP)
            detected.add(UserIntent.OPTIONS_DERIVATIVES)
            for prev in clean_prev:
                detected.add(prev)
        elif "invalidate" in q_clean or "risk" in q_clean:
            detected.add(UserIntent.FOLLOW_UP)
            detected.add(UserIntent.TRADE_OPPORTUNITY)
            for prev in clean_prev:
                detected.add(prev)
        elif any(p in q_clean for p in ["which one", "which story", "matters most", "most exposed", "next event", "what time", "what event"]):
            detected.add(UserIntent.FOLLOW_UP)
            detected.add(UserIntent.NEWS_EVENTS)
            for prev in clean_prev:
                detected.add(prev)
        elif len(words) <= 3 and not detected:
            detected.add(UserIntent.FOLLOW_UP)
            for prev in clean_prev:
                detected.add(prev)

    if not detected:
        detected.add(UserIntent.MARKET_SUMMARY)

    # Prevent generic MARKET_SUMMARY or BREADTH_SECTORS pollution for explicit NEWS_EVENTS queries
    if UserIntent.NEWS_EVENTS in detected:
        if UserIntent.MARKET_SUMMARY in detected and len(detected) > 1:
            detected.remove(UserIntent.MARKET_SUMMARY)
        if UserIntent.BREADTH_SECTORS_HEAVYWEIGHTS in detected:
            detected.remove(UserIntent.BREADTH_SECTORS_HEAVYWEIGHTS)

    return (list(detected), temporal_target)


def classify_user_intents(query: str, previous_intents: Optional[List[UserIntent]] = None) -> List[UserIntent]:
    """Backward compatible helper returning List[UserIntent]."""
    intents, _ = classify_user_query_with_temporal(query, previous_intents)
    return intents


def decompose_query(query: str, previous_intents: Optional[List[UserIntent]] = None) -> List[SubQuery]:
    """
    Decomposes compound queries (e.g. 'what happened yesterday, why that much raise?') into subqueries.
    """
    q_clean = query.strip()

    # Split on explicit clause delimiters: commas, question marks, or 'and why'
    raw_clauses: List[str] = []
    if "," in q_clean:
        raw_clauses = [c.strip() for c in q_clean.split(",") if c.strip()]
    elif " and why " in q_clean.lower():
        parts = q_clean.lower().split(" and why ")
        raw_clauses = [parts[0], "why " + parts[1]]
    elif "?" in q_clean and len([c for c in q_clean.split("?") if c.strip()]) > 1:
        raw_clauses = [c.strip() for c in q_clean.split("?") if c.strip()]
    else:
        raw_clauses = [q_clean]

    subqueries: List[SubQuery] = []

    # Inherit temporal target from first clause if subsequent clause is temporal-relative
    inherited_temporal = TemporalTarget.LIVE_CURRENT

    for idx, clause in enumerate(raw_clauses):
        intents, temporal = classify_user_query_with_temporal(clause, previous_intents)
        if idx == 0 and temporal != TemporalTarget.LIVE_CURRENT:
            inherited_temporal = temporal
        elif idx > 0 and temporal == TemporalTarget.LIVE_CURRENT and inherited_temporal != TemporalTarget.LIVE_CURRENT:
            temporal = inherited_temporal
            if UserIntent.SESSION_HISTORY not in intents and inherited_temporal == TemporalTarget.PREVIOUS_COMPLETED_SESSION:
                intents.append(UserIntent.SESSION_HISTORY)

        act = resolve_answer_act(clause, intents)
        subqueries.append(SubQuery(text=clause, intents=intents, temporal_target=temporal, answer_act=act))

    return subqueries
