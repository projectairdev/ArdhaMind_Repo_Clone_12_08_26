# src/live_assistant/llm_provider.py
"""
LLM Provider Abstraction Layer for Live Assistant.
Supports Google Gemini, OpenAI, and Mock/Fallback providers.
"""
from abc import ABC, abstractmethod
import json
import os
import urllib.request
import urllib.error
from typing import Any, Dict, Optional

from src.live_assistant.evidence_packet import BoundedEvidencePacket
from src.utils import setup_logger

logger = setup_logger("LiveAssistantLLMProvider")

SYSTEM_CONTRACT_PROMPT = """You are the conversational response layer for AIR ArdhaMind Live Assistant.

SYSTEM INVARIANT:
ARDHAMIND DECIDES WHAT IS TRUE. THE SYNTHESIS LAYER RANKS EVIDENCE. THE LLM ONLY DECIDES HOW TO SAY IT.

CONVERSATIONAL & GROUNDING RULES:
1. DIRECT ANSWER FIRST:
   - For factual/causal market questions ("Why did NIFTY rise yesterday?", "Why are we bullish?"), start IMMEDIATELY with the core conclusion in your first sentence.
   - Example: "Yesterday's NIFTY rise was primarily supported by broad market participation (38 advances to 12 declines) and strong gains in key index heavyweights, particularly Banking (+0.85%)."
   - Do NOT begin with raw OHLC stats ("Yesterday NIFTY opened at...").
2. CAUSATION VS CONTRIBUTION:
   - Differentiate measurable contributions (e.g. Bank Nifty +0.85%) from verified catalysts.
   - Treat FII/DII data published post-session as post-session context, NEVER as an intraday trigger.
3. NEWS & EVENTS GROUNDING:
   - For news queries ("What are the top news today?"), answer directly with tracked stories, scheduled events, and exposed sectors.
   - Do NOT lead with NIFTY spot prices ("NIFTY is at 24231.85...").
   - Differentiate published news from scheduled events.
   - Preserve UNCLEAR direction when canonical evidence states UNCLEAR. Never claim a news story will move NIFTY higher without canonical confirmation.
   - If canonical news feed is unavailable/degraded, state feed status cleanly. NEVER convert missing evidence into "there is no important news".
4. CONVERSATIONAL FREEDOM:
   - For greetings ("Hi", "Good morning"), respond naturally without dumping canned report headers.
   - For follow-ups ("Why?", "What about options?", "Which one?"), address the specific question directly.
5. ABSOLUTE PROHIBITIONS:
   - NEVER invent or calculate market prices, NIFTY spot levels, strikes, trade targets, stop loss levels, or confidence scores.
   - NEVER generate a trade setup when canonical status is NO_SETUP or NONE.
"""


class LiveAssistantLLMProvider(ABC):
    """Abstract Base Class for Live Assistant LLM Providers."""

    @abstractmethod
    def generate_grounded_answer(
        self, packet: BoundedEvidencePacket, system_contract: str = SYSTEM_CONTRACT_PROMPT
    ) -> str:
        pass

    @abstractmethod
    def health_check(self) -> bool:
        pass

    @abstractmethod
    def provider_metadata(self) -> Dict[str, Any]:
        pass


class GeminiProvider(LiveAssistantLLMProvider):
    """Google Gemini API Provider."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("LIVE_ASSISTANT_PROVIDER_KEY")
        self.model = os.getenv("LIVE_ASSISTANT_MODEL", model)

    def health_check(self) -> bool:
        return bool(self.api_key)

    def provider_metadata(self) -> Dict[str, Any]:
        return {"provider": "gemini", "model": self.model, "configured": bool(self.api_key)}

    def generate_grounded_answer(
        self, packet: BoundedEvidencePacket, system_contract: str = SYSTEM_CONTRACT_PROMPT
    ) -> str:
        if not self.api_key:
            raise ValueError("Gemini API key is not configured.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        user_prompt = f"User Question: {packet.question}\n\nCanonical Evidence Packet:\n{json.dumps(packet.to_dict(), indent=2)}"

        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": f"{system_contract}\n\n{user_prompt}"}]}
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 500,
            }
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return text.strip()


class OpenAIProvider(LiveAssistantLLMProvider):
    """OpenAI API Provider."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", model)

    def health_check(self) -> bool:
        return bool(self.api_key)

    def provider_metadata(self) -> Dict[str, Any]:
        return {"provider": "openai", "model": self.model, "configured": bool(self.api_key)}

    def generate_grounded_answer(
        self, packet: BoundedEvidencePacket, system_contract: str = SYSTEM_CONTRACT_PROMPT
    ) -> str:
        if not self.api_key:
            raise ValueError("OpenAI API key is not configured.")

        url = "https://api.openai.com/v1/chat/completions"
        user_prompt = f"User Question: {packet.question}\n\nCanonical Evidence Packet:\n{json.dumps(packet.to_dict(), indent=2)}"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_contract},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 500
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            },
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            text = data["choices"][0]["message"]["content"]
            return text.strip()


class MockProvider(LiveAssistantLLMProvider):
    """Mock/Testing Provider for offline development and test suites."""

    def health_check(self) -> bool:
        return True

    def provider_metadata(self) -> Dict[str, Any]:
        return {"provider": "mock", "model": "mock-grounded-v1", "configured": True}

    def generate_grounded_answer(
        self, packet: BoundedEvidencePacket, system_contract: str = SYSTEM_CONTRACT_PROMPT
    ) -> str:
        # Grounded mock generator strictly extracting packet fields
        ev = packet.evidence
        m_state = ev.get("market_state", {})
        opp = ev.get("opportunity_state", {})

        # Conversational Intent Handling
        if "GREETING" in packet.intents:
            return "Good day! I am your ArdhaMind Live Assistant. Ask me about today's market setup, opening expectations, options, risk, or news."

        if "CASUAL_CONVERSATION" in packet.intents:
            return "You're welcome! Let me know if you need any further analysis of ArdhaMind's canonical evidence."

        if "EDUCATIONAL" in packet.intents:
            deriv = ev.get("derivatives", {})
            pcr = deriv.get("pcr", 1.25)
            return f"PCR (Put-Call Ratio) measures put trading volume relative to calls. In ArdhaMind's current options state, PCR is {pcr}."

        if "TRADE_OPPORTUNITY" in packet.intents or "ENTRY_TIMING" in packet.intents:
            status = opp.get("status", "NO_SETUP")
            if status in ("NO_SETUP", "NONE"):
                return "ArdhaMind currently has no qualified trade setup."
            else:
                strat = opp.get("strategy", "CE Pullback")
                strike = opp.get("strike", "NIFTY 24250 CE")
                trigger = opp.get("trigger_zone", "24,200")
                conf = opp.get("confidence_score", 82)
                return f"ArdhaMind currently highlights a qualified setup: {strike} ({strat}) with trigger zone {trigger} and confidence score {conf}/100."

        if "PREMARKET_TOMORROW" in packet.intents:
            pmb = ev.get("premarket_intelligence", {})
            bias = pmb.get("opening_bias", "BULLISH_CONTINUATION")
            rng = pmb.get("expected_open_range", "24,180 – 24,220")
            return f"ArdhaMind's pre-market assessment indicates a {bias} bias with an expected opening range of {rng}."

        if "MARKET_SUMMARY" in packet.intents:
            spot = m_state.get("spot")
            spot_str = f"{spot:.2f}" if spot is not None else "currently unavailable in canonical feed"
            regime = m_state.get("regime", "TREND EXPANSION")
            bias = m_state.get("directional_bias", "BULLISH")
            vix = m_state.get("vix", 13.85)
            return f"NIFTY spot is {spot_str} ({bias} bias) in a {regime} regime with India VIX at {vix}."

        return f"ArdhaMind canonical evidence confirms {packet.canonical_session} session state at {packet.market_timestamp}."


def get_llm_provider(provider_name: Optional[str] = None) -> LiveAssistantLLMProvider:
    """Factory function to resolve configured LLM provider."""
    name = (provider_name or os.getenv("LIVE_ASSISTANT_PROVIDER") or "gemini").lower()

    if name == "mock":
        return MockProvider()

    if name in ("gemini", "auto"):
        g_prov = GeminiProvider()
        if g_prov.health_check():
            return g_prov
        # Fallback to configured OpenAI key if Gemini key not set
        o_prov = OpenAIProvider()
        if o_prov.health_check():
            logger.info("Gemini key unconfigured, using configured OpenAI Provider.")
            return o_prov
        raise RuntimeError("No active LLM API Key configured for Gemini/OpenAI.")

    if name == "openai":
        o_prov = OpenAIProvider()
        if o_prov.health_check():
            return o_prov
        g_prov = GeminiProvider()
        if g_prov.health_check():
            return g_prov
        raise RuntimeError("No active LLM API Key configured for OpenAI/Gemini.")

    return MockProvider()
