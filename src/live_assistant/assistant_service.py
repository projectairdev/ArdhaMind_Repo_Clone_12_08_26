# src/live_assistant/assistant_service.py
"""
Live Assistant Main Service Orchestrator.
Coordinates conversation memory, evidence routing, LLM provider invocation,
grounding validation, and deterministic fallback.
"""
from typing import Any, Dict, List, Optional
import time

from src.live_assistant.intent_taxonomy import UserIntent, AnswerAct, decompose_query
from src.live_assistant.evidence_router import EvidenceRouter
from src.live_assistant.evidence_synthesis import EvidenceSynthesizer
from src.live_assistant.answer_planner import AnswerPlanner, ANSWER_PLANNER_VERSION
from src.live_assistant.llm_provider import get_llm_provider, LiveAssistantLLMProvider
from src.live_assistant.grounding_validator import GroundingValidator
from src.live_assistant.deterministic_fallback import DeterministicFallback
from src.utils import setup_logger

logger = setup_logger("LiveAssistantService")


class LiveAssistantService:
    """
    Main Service entry point for Live Assistant queries.
    """

    _conversation_history: Dict[str, List[Dict[str, Any]]] = {}

    @classmethod
    def process_query(
        cls,
        user_message: str,
        conversation_id: str = "default",
        workstation_state: Optional[Dict[str, Any]] = None,
        provider_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        start_time = time.time()
        c_id = conversation_id or "default"

        # Bounded Memory: Retrieve last conversation turn for context (follow-up intent inheritance)
        history = cls._conversation_history.get(c_id, [])
        previous_intents: Optional[List[UserIntent]] = None
        if history:
            last_turn = history[-1]
            previous_intents = []
            for i in last_turn.get("intents", []):
                if i in UserIntent.__members__:
                    previous_intents.append(UserIntent[i])
                elif i in [e.value for e in UserIntent]:
                    previous_intents.append(UserIntent(i))

        # 1. Query Decomposition & Intent Resolution
        subqueries = decompose_query(user_message, previous_intents)

        # 2. Deterministic Evidence Routing & Minimization
        c_state = workstation_state or {}
        packet = EvidenceRouter.route_query(user_message, c_state, previous_intents)

        # 3. Evidence Synthesis & Answer Planning
        synthesis = EvidenceSynthesizer.synthesize(subqueries, packet)
        plan = AnswerPlanner.build_plan(synthesis, packet)
        packet.evidence["answer_plan"] = plan.to_dict()

        # 4. Fast Conversational Greeting Handler
        if UserIntent.GREETING.value in packet.intents or UserIntent.GREETING in packet.intents:
            session_phase = packet.canonical_session.upper()
            if session_phase in ("PRE_MARKET", "PREMARKET"):
                greeting_text = "Hi. ArdhaMind is currently in the PRE_MARKET preparation phase. What would you like to check this morning?"
            else:
                greeting_text = f"Hi. ArdhaMind is currently in the {session_phase.replace('_', ' ')} phase. What would you like to check?"

            history.append({"message": user_message, "intents": [UserIntent.GREETING.value], "timestamp": packet.market_timestamp})
            cls._conversation_history[c_id] = history[-5:]
            return {
                "answer": greeting_text,
                "intent": [UserIntent.GREETING.value],
                "answer_act": synthesis.primary_answer_act.value,
                "evidence_used": ["session_context"],
                "freshness": packet.freshness_status,
                "action_state": "READY",
                "provider": "conversational_handler",
                "model": "session-aware-v1",
                "fallback_used": False,
                "data_sufficiency": synthesis.data_sufficiency,
                "validation_violations": [],
                "latency_ms": round((time.time() - start_time) * 1000, 2),
            }

        if UserIntent.CASUAL_CONVERSATION.value in packet.intents or UserIntent.CASUAL_CONVERSATION in packet.intents:
            history.append({"message": user_message, "intents": [UserIntent.CASUAL_CONVERSATION.value], "timestamp": packet.market_timestamp})
            cls._conversation_history[c_id] = history[-5:]
            return {
                "answer": "You're welcome! Feel free to ask if you'd like to explore ArdhaMind's canonical evidence further.",
                "intent": [UserIntent.CASUAL_CONVERSATION.value],
                "answer_act": synthesis.primary_answer_act.value,
                "evidence_used": ["conversation_context"],
                "freshness": packet.freshness_status,
                "action_state": "READY",
                "provider": "conversational_handler",
                "model": "session-aware-v1",
                "fallback_used": False,
                "data_sufficiency": synthesis.data_sufficiency,
                "validation_violations": [],
                "latency_ms": round((time.time() - start_time) * 1000, 2),
            }

        # 5. Provider Resolution
        provider: LiveAssistantLLMProvider = get_llm_provider(provider_override)
        meta = provider.provider_metadata()

        result_payload: Dict[str, Any] = {}

        try:
            # 6. LLM Generation
            raw_answer = provider.generate_grounded_answer(packet)

            # 7. Strict Grounding & Contract Validation
            val_res = GroundingValidator.validate(raw_answer, packet)

            if val_res.is_valid:
                # 8. Conversational Similarity Guard: Ensure CAUSE answers don't repeat SUMMARY text
                if history and len(history) >= 1:
                    prev_ans = history[-1].get("answer", "")
                    if prev_ans and synthesis.primary_answer_act == AnswerAct.CAUSE:
                        words_prev = set(prev_ans.lower().split())
                        words_curr = set(raw_answer.lower().split())
                        overlap = len(words_prev.intersection(words_curr)) / max(len(words_curr), 1)
                        if overlap > 0.75 and plan.direct_answer_lead:
                            raw_answer = f"{plan.direct_answer_lead}\n\n" + raw_answer.split("\n\n")[-1]

                result_payload = {
                    "answer": raw_answer,
                    "intent": packet.intents,
                    "answer_act": synthesis.primary_answer_act.value,
                    "evidence_used": [k for k in packet.evidence.keys() if k != "answer_plan"],
                    "freshness": packet.freshness_status,
                    "action_state": "READY",
                    "provider": meta.get("provider", "LLM"),
                    "model": meta.get("model", "grounded-v1"),
                    "fallback_used": False,
                    "data_sufficiency": synthesis.data_sufficiency,
                    "drivers": [d.factor_name for d in synthesis.ranked_drivers],
                    "validation_violations": [],
                    "runtime_build_id": "phase3_1_a13c92f_20260821T0425",
                    "answer_planner_version": ANSWER_PLANNER_VERSION,
                    "answer_pipeline_version": "phase3.1-answerplanner-v2",
                    "latency_ms": round((time.time() - start_time) * 1000, 2),
                }
            else:
                logger.warning(
                    "Grounding validation failed for query '%s': %s. Falling back.",
                    user_message,
                    val_res.violations,
                )
                fallback_res = DeterministicFallback.generate_fallback(
                    packet, reason=f"GROUNDING_VIOLATION: {val_res.violations[0]}"
                )
                result_payload = fallback_res
                result_payload["validation_violations"] = val_res.violations

        except Exception as err:
            logger.error("LLM Provider generation failed: %s. Using fallback.", err, exc_info=True)
            fallback_res = DeterministicFallback.generate_fallback(packet, reason=str(err))
            result_payload = fallback_res

        # Record Bounded History (Max 5 turns stored)
        history.append({
            "message": user_message,
            "answer": result_payload.get("answer", ""),
            "intents": packet.intents,
            "timestamp": packet.market_timestamp,
        })
        cls._conversation_history[c_id] = history[-5:]

        latency_ms = round((time.time() - start_time) * 1000, 2)
        result_payload["latency_ms"] = latency_ms

        # Add Canonical News State Parity Diagnostics
        ni_ev = packet.evidence.get("news_intelligence", {})
        news_items_ev = ni_ev.get("news_items", [])
        result_payload["news_state_source"] = "canonical_news_intelligence" if ni_ev else "none"
        result_payload["news_story_count"] = len(news_items_ev)
        result_payload["news_high_impact_count"] = ni_ev.get("high_impact_count", 0)
        result_payload["news_freshness"] = packet.freshness_status
        result_payload["news_provider_health"] = ni_ev.get("provider_health", {})
        result_payload["event_count"] = len(ni_ev.get("scheduled_events", []))

        return result_payload

    @classmethod
    def clear_history(cls, conversation_id: str = "default") -> None:
        if conversation_id in cls._conversation_history:
            del cls._conversation_history[conversation_id]
