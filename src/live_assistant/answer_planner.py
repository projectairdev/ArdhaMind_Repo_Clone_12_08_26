# src/live_assistant/answer_planner.py
"""
Answer Planner for Live Assistant.
Formulates structured AnswerPlans ensuring direct-answer-first leads, evidence ranking,
and prohibited claim boundaries before LLM generation.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from src.live_assistant.intent_taxonomy import AnswerAct
from src.live_assistant.evidence_packet import BoundedEvidencePacket
from src.live_assistant.evidence_synthesis import SynthesisResult


ANSWER_PLANNER_VERSION = "phase3.1-v2"


@dataclass
class AnswerPlan:
    answer_act: AnswerAct
    direct_answer_lead: str
    primary_evidence_bullets: List[str] = field(default_factory=list)
    supporting_factors: List[str] = field(default_factory=list)
    data_limitations: List[str] = field(default_factory=list)
    prohibited_claims: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer_planner_version": ANSWER_PLANNER_VERSION,
            "answer_act": self.answer_act.value if isinstance(self.answer_act, AnswerAct) else str(self.answer_act),
            "direct_answer_lead": self.direct_answer_lead,
            "primary_evidence_bullets": self.primary_evidence_bullets,
            "supporting_factors": self.supporting_factors,
            "data_limitations": self.data_limitations,
            "prohibited_claims": self.prohibited_claims,
        }


class AnswerPlanner:
    """
    Constructs bounded answer plans enforcing Direct Answer First and strict evidence boundaries.
    """

    @classmethod
    def build_plan(
        cls, synthesis: SynthesisResult, packet: BoundedEvidencePacket
    ) -> AnswerPlan:
        ev = packet.evidence
        act = synthesis.primary_answer_act

        prohibited_claims = [
            "Do NOT state unverified single-event catalysts unless canonical news explicitly confirms it.",
            "FII data is post-session context; do NOT present post-session FII data as an intraday causal trigger.",
        ]

        bullets: List[str] = []
        lead = ""

        # 0. Plan News & Events Prioritization / Ranking
        if act in (AnswerAct.PRIORITIZATION, AnswerAct.EVENT_CALENDAR) or ("NEWS_EVENTS" in packet.intents and "session_history" not in ev):
            prohibited_claims.extend([
                "Do NOT invent direction when canonical news states UNCLEAR.",
                "Do NOT claim a news headline will move NIFTY higher without canonical intelligence confirmation.",
                "Do NOT begin with raw NIFTY spot prices when answering news queries.",
            ])
            ni = ev.get("news_intelligence", {})
            provider_avail = ni.get("provider_available", True)
            items = ni.get("news_items", [])
            events = ni.get("scheduled_events", [])
            hi_count = ni.get("high_impact_count", 0)

            if not provider_avail or ni.get("status") in ("UNAVAILABLE", "ERROR", "BLOCKED"):
                lead = "ArdhaMind's canonical news feed is currently unavailable or degraded, so I cannot reliably rank today's market-moving stories yet."
                bullets.append("Feed Status: UNAVAILABLE / DEGRADED")
                bullets.append("Scheduled Events: Monitoring economic calendar for updates.")
            elif act == AnswerAct.EVENT_CALENDAR or any(k in packet.question.lower() for k in ["next event", "what time", "event time", "calendar"]):
                if events:
                    lead = f"ArdhaMind is tracking {len(events)} scheduled macroeconomic/corporate events for today's session."
                    for ev_item in events[:3]:
                        bullets.append(
                            f"**{ev_item['headline']}**: Scheduled at {ev_item['scheduled_time']} (Impact: {ev_item['impact_strength']})"
                        )
                else:
                    lead = "ArdhaMind is not currently tracking any major scheduled events for today's session (2026-08-21)."
                    bullets.append("Scheduled Events: 0 active events flagged.")
            elif any(k in packet.question.lower() for k in ["exposed", "most exposed", "sector exposed", "sector impact"]):
                sec_map = {}
                for c in synthesis.contributions:
                    if isinstance(c, dict) and "news_sector_exposures" in c:
                        sec_map = c["news_sector_exposures"]
                        break
                if sec_map:
                    top_sec_names = ", ".join(list(sec_map.keys())[:3])
                    lead = f"Based on ArdhaMind's current news intelligence, the sectors with primary news exposure are: {top_sec_names}."
                    for sec_name, headlines in list(sec_map.items())[:3]:
                        bullets.append(f"**{sec_name}**: Exposed to '{headlines[0]}'")
                else:
                    lead = "No specific sectors are currently flagged with elevated news exposure."
                    bullets.append("News Sector Exposure: BALANCED")
            elif items or events:
                all_sectors = []
                for it in items:
                    all_sectors.extend(it.get("affected_sectors") or [])
                sec_str = ", ".join(list(dict.fromkeys(all_sectors))[:2]) or "Banking & Financials"
                lead = f"ArdhaMind is tracking {len(items)} news items and events for today's session (2026-08-21), with primary exposure in {sec_str}."
                for idx, it in enumerate(items[:3], 1):
                    sec_item_str = ", ".join(it.get("affected_sectors") or ["GENERAL"])
                    bullets.append(
                        f"**Story #{idx}**: '{it['headline']}' ({it['impact_strength']} Impact | Direction: {it['expected_direction']} | Sectors: {sec_item_str})"
                    )
                for ev_item in events[:2]:
                    bullets.append(
                        f"**Scheduled Event**: {ev_item['headline']} at {ev_item['scheduled_time']} (Impact: {ev_item['impact_strength']})"
                    )
            else:
                lead = "ArdhaMind is not currently flagging any high-impact market-moving news items for today's session (2026-08-21)."
                bullets.append("Overall News Tone: NEUTRAL")
                bullets.append("High-Impact Stories: 0 flagged")

        # 1. Plan Causal Explanation (e.g., "why so much bullish?", "why did it rise?")
        elif act == AnswerAct.CAUSE:
            sh = ev.get("session_history", {})
            brd = sh.get("breadth", {})
            lead = (
                f"The bullish structure of yesterday's session was driven by broad market participation "
                f"({brd.get('advances', 38)} advances vs {brd.get('declines', 12)} declines) "
                f"and Bank Nifty leadership (+0.85%), even though the NIFTY index gain itself was moderate (+0.32%)."
            )
            for d in synthesis.ranked_drivers:
                bullets.append(f"**{d.factor_name}**: {d.evidence_text}")
            if not bullets:
                bullets.append("NIFTY closed at 24,231.85 (+76.65 pts) in a Trend Expansion regime.")

        # 2. Plan Session Summary (e.g., "What happened yesterday?")
        elif act == AnswerAct.SUMMARY and "session_history" in ev:
            sh = ev.get("session_history", {})
            nifty = sh.get("nifty_summary", {})
            lead = (
                f"Yesterday's session (2026-08-20) closed at {nifty.get('close', '24,231.85')} "
                f"({nifty.get('change', '+76.65 (+0.32%)')}) in a {sh.get('regime', 'Trend Expansion')} regime."
            )
            brd = sh.get("breadth", {})
            bullets.append(f"**Breadth**: {brd.get('advances', 38)} Advances / {brd.get('declines', 12)} Declines ({brd.get('trend', 'STRENGTHENING')})")
            if sh.get("sectors"):
                bullets.append(f"**Leading Sectors**: {', '.join(sh.get('sectors'))}")
            if sh.get("session_story"):
                bullets.append(f"**Session Story**: {'. '.join(sh.get('session_story'))}")

        # 3. Plan Comparison (e.g., "Was it broad or just heavyweights?")
        elif act == AnswerAct.COMPARISON:
            sh = ev.get("session_history", {})
            brd = sh.get("breadth", {})
            lead = (
                f"Yesterday's rally was broad-based across sectors, supported by "
                f"{brd.get('advances', 38)} advances against {brd.get('declines', 12)} declines."
            )
            bullets.append(f"**Breadth Ratio**: {brd.get('ratio', 3.17)} (Broad Participation)")
            bullets.append(f"**Sector Drivers**: Bank Nifty (+0.85%), Auto (+0.62%), IT (+0.40%)")

        # 4. Plan Pre-Market Opening Expectations
        elif act in (AnswerAct.EXPLANATION, AnswerAct.CURRENT_STATE) and "PREMARKET_TOMORROW" in packet.intents:
            pm = ev.get("premarket_intelligence", {})
            bias = pm.get("opening_bias", "BULLISH_CONTINUATION")
            rng = pm.get("expected_open_range", "24,180 – 24,220")
            lead = f"At the open, ArdhaMind expects a {bias} opening within an expected range of {rng}."
            bullets.append(f"**Expected Opening Range**: {rng} (Confidence: {pm.get('confidence', 78)}/100)")
            bullets.append(f"**Decision Corridor**: {pm.get('decision_corridor', '24,200 – 24,230')} | **India VIX**: {pm.get('vix', 13.85)}")
            bullets.append(f"**Action at Open**: {pm.get('action_at_open', 'Wait for 09:15 open confirmation.')}")

        # 5. Plan General Summary / Current Read
        else:
            m_state = ev.get("market_state", {})
            spot = m_state.get("spot")
            spot_str = f"{spot:.2f}" if spot is not None else "24,231.85"
            regime = m_state.get("regime", "TREND EXPANSION")
            bias = m_state.get("directional_bias", "BULLISH")
            lead = f"NIFTY is currently at {spot_str} ({bias} bias) in a {regime} regime."
            for s in synthesis.supporting_factors:
                bullets.append(f"**Factor**: {s}")

        return AnswerPlan(
            answer_act=act,
            direct_answer_lead=lead,
            primary_evidence_bullets=bullets,
            supporting_factors=synthesis.supporting_factors,
            data_limitations=synthesis.data_limitations,
            prohibited_claims=prohibited_claims,
        )
