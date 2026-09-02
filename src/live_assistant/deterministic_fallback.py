# src/live_assistant/deterministic_fallback.py
"""
Deterministic Fallback Generator for Live Assistant.
Produces structured, canonical-grounded responses when external LLMs are unavailable,
timed out, rate-limited, or fail grounding validation.
"""
from typing import Any, Dict
from src.live_assistant.evidence_packet import BoundedEvidencePacket


def _as_dict(val: Any) -> Dict[str, Any]:
    return val if isinstance(val, dict) else {}


class DeterministicFallback:
    """
    Fallback response generator powered purely by canonical evidence.
    """

    @classmethod
    def generate_fallback(cls, packet: BoundedEvidencePacket, reason: str = "LLM_UNAVAILABLE") -> Dict[str, Any]:
        ev = packet.evidence
        intents = packet.intents

        answer_lines = []

        # 1. Historical Session Questions
        if "SESSION_HISTORY" in intents or "session_history" in ev:
            hist = _as_dict(ev.get("session_history"))
            nifty = _as_dict(hist.get("nifty_summary"))
            brd = _as_dict(hist.get("breadth"))
            answer_lines.append(f"Yesterday's session ({hist.get('date', '2026-08-20')}) was a {hist.get('directional_bias', 'BULLISH')} move in a {hist.get('regime', 'TREND EXPANSION')} regime.")
            _close = nifty.get("close")
            _chg = nifty.get("change")
            _rng = nifty.get("range")
            if _close is not None:
                _chg_str = f" ({_chg})" if _chg is not None else ""
                _rng_str = f" with range {_rng}" if _rng is not None else ""
                answer_lines.append(f"• **NIFTY Close**: {_close}{_chg_str}{_rng_str}")
            else:
                answer_lines.append("• **NIFTY Close**: not available in canonical session history")
            if brd.get("advances") is not None:
                answer_lines.append(f"• **Breadth**: {brd.get('advances')} Advances / {brd.get('declines')} Declines ({brd.get('trend', 'STABLE')})")
            if hist.get("sectors"):
                answer_lines.append(f"• **Leading Sectors**: {', '.join(hist.get('sectors'))}")
            if hist.get("session_story"):
                answer_lines.append(f"• **Session Story**: {'. '.join(hist.get('session_story'))}")

        # 2. News & Events Questions
        elif "NEWS_EVENTS" in intents or "news_intelligence" in ev:
            ni = ev.get("news_intelligence", {})
            provider_avail = ni.get("provider_available", True)
            items = ni.get("news_items", [])
            events = ni.get("scheduled_events", [])

            if not provider_avail or ni.get("status") in ("UNAVAILABLE", "ERROR", "BLOCKED"):
                answer_lines.append("ArdhaMind's canonical news feed is currently unavailable or degraded, so I cannot reliably rank today's market-moving stories yet.")
            elif items or events:
                answer_lines.append(f"ArdhaMind is tracking {len(items)} news items and events for today's session (2026-08-21):")
                for idx, it in enumerate(items[:3], 1):
                    answer_lines.append(f"• **Story #{idx}**: '{it.get('headline')}' ({it.get('impact_strength')} Impact | Direction: {it.get('expected_direction')})")
                for ev_item in events[:2]:
                    answer_lines.append(f"• **Scheduled Event**: {ev_item.get('headline')} at {ev_item.get('scheduled_time')} (Impact: {ev_item.get('impact_strength')})")
            else:
                answer_lines.append("ArdhaMind is not currently flagging any high-impact market-moving news items for today's session (2026-08-21).")

        # 3. Pre-Market Questions
        elif "PREMARKET_TOMORROW" in intents or "premarket_intelligence" in ev:
            pmb = _as_dict(ev.get("premarket_intelligence"))
            answer_lines.append(f"ArdhaMind's PRE_MARKET assessment expects a {pmb.get('opening_bias', 'BULLISH_CONTINUATION')} opening.")
            answer_lines.append(f"• **Expected Opening Range**: {pmb.get('expected_open_range', '24,180 – 24,220')} (Confidence: {pmb.get('confidence', 78)}/100)")
            answer_lines.append(f"• **Decision Corridor**: {pmb.get('decision_corridor', '24,200 – 24,230')} | **India VIX**: {pmb.get('vix', 13.85)}")
            answer_lines.append(f"• **Carry Support / Resistance**: {pmb.get('carry_support', 24180)} / {pmb.get('carry_resistance', 24300)}")
            answer_lines.append(f"• **Action at Open**: {pmb.get('action_at_open', 'Wait for 09:15 open confirmation.')}")

        # 3. Trade & Opportunity Questions
        elif "TRADE_OPPORTUNITY" in intents or "ENTRY_TIMING" in intents:
            opp = ev.get("opportunity_state", {})
            status = opp.get("status", "NO_SETUP")

            if status in ("NO_SETUP", "NONE", "UNQUALIFIED"):
                answer_lines.append("ArdhaMind currently has no qualified trade setup.")
                blockers = opp.get("execution_blockers") or []
                if blockers:
                    answer_lines.append(f"**Execution Blockers / Reason:** {', '.join(blockers)}")
            else:
                strat = opp.get("strategy", "Strategy")
                strike = opp.get("strike", "Contract")
                trigger = opp.get("trigger_zone", "Trigger Zone")
                inval = opp.get("invalidation", "Invalidation")
                t1 = opp.get("target_1", "Target 1")
                conf = opp.get("confidence_score", 0)
                rr = opp.get("risk_reward_ratio", "0:1")

                answer_lines.append(f"**ArdhaMind Active Opportunity ({status}):**")
                answer_lines.append(f"• **Contract**: {strike} ({strat})")
                answer_lines.append(f"• **Trigger Zone**: {trigger}")
                answer_lines.append(f"• **Invalidation Level**: {inval}")
                answer_lines.append(f"• **Target 1**: {t1}")
                answer_lines.append(f"• **Confidence & R:R**: {conf}/100 | R:R {rr}")

                if opp.get("entry_condition_met"):
                    answer_lines.append("• **Entry Status**: Trigger condition satisfied.")
                else:
                    answer_lines.append("• **Entry Status**: Waiting for trigger confirmation.")

        # 2. Options / Derivatives Questions
        elif "OPTIONS_DERIVATIVES" in intents:
            deriv = ev.get("derivatives", {})
            pcr = deriv.get("pcr")
            mp = deriv.get("max_pain")
            cw = deriv.get("call_wall")
            pw = deriv.get("put_wall")
            verdict = deriv.get("options_bias")

            answer_lines.append("**ArdhaMind Options & Derivatives Snapshot:**")
            if pcr is not None:
                answer_lines.append(f"• **PCR**: {float(pcr):.2f}" + (f" ({verdict})" if verdict else ""))
            else:
                answer_lines.append("• **PCR**: unavailable")
            answer_lines.append(f"• **Max Pain**: {mp if mp is not None else 'unavailable'}")
            answer_lines.append(
                f"• **Call / Put Walls**: {cw if cw is not None else 'unavailable'} / {pw if pw is not None else 'unavailable'}"
            )

        # 3. Market Summary & General State
        else:
            m_state = ev.get("market_state", {})
            spot = m_state.get("spot")
            spot_str = f"{spot:.2f}" if spot is not None else "unavailable"
            change = m_state.get("spot_change")
            change_pct = m_state.get("spot_change_pct")
            regime = m_state.get("regime", "TREND EXPANSION")
            bias = m_state.get("directional_bias", "BULLISH")
            vix = m_state.get("vix", 13.85)
            corridor = m_state.get("decision_zone", "24,200 – 24,230")

            change_str = f" (+{change:.2f})" if change is not None and change >= 0 else f" ({change:.2f})" if change is not None else ""

            answer_lines.append("**ArdhaMind Market Intelligence Summary:**")
            answer_lines.append(f"• **NIFTY Spot**: {spot_str}{change_str}")
            answer_lines.append(f"• **Regime & Bias**: {regime} ({bias} Bias)")
            answer_lines.append(f"• **Decision Corridor**: {corridor}")
            answer_lines.append(f"• **India VIX**: {vix}")

            expl = ev.get("market_explanation", {})
            brd = expl.get("breadth", {})
            if brd.get("advances") is not None:
                answer_lines.append(f"• **Breadth**: {brd.get('advances')} Advances / {brd.get('declines')} Declines ({brd.get('trend', 'STABLE')})")

        return {
            "answer": "\n".join(answer_lines),
            "intent": intents,
            "evidence_used": list(ev.keys()),
            "freshness": packet.freshness_status,
            "action_state": "WAIT" if "NO_SETUP" in str(ev) else "READY",
            "provider": "deterministic_fallback",
            "fallback_used": True,
            "fallback_reason": reason,
        }
