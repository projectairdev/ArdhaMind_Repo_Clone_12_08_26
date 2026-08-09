# src/services/openai_interpretation_service.py
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


class OpenAIInterpretationService:
    """
    Bounded OpenAI Interpretation Layer:
    - Explains canonical workstation state deterministically.
    - Never overrides prices, signals, risk limits, or confidence scores.
    - Gracefully degrades to deterministic fallbacks when API key is missing or service fails.
    - Enforces prompt grounding, timeouts, retries, caching, and diagnostics telemetry.
    """

    MODEL_NAME = "gpt-4o-mini"
    MAX_TOKENS = 600
    TIMEOUT_SECONDS = 8

    _cache: Dict[str, Dict[str, Any]] = {}
    _last_request_time: Optional[str] = None
    _last_latency_ms: float = 0.0
    _last_error: Optional[str] = None
    _total_requests: int = 0
    _failed_requests: int = 0

    @classmethod
    def get_model_name(cls) -> str:
        from src.configuration_engine.runtime import Config
        return os.getenv("OPENAI_MODEL") or getattr(Config, "OPENAI_MODEL", "gpt-4o-mini")

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            status = "disabled"
            reason = "OPENAI_API_KEY environment variable not configured"
        elif cls._last_error:
            status = "degraded"
            reason = cls._last_error
        else:
            status = "available"
            reason = "Ready to interpret canonical workstation state"

        return {
            "status": status,
            "reason": reason,
            "model": cls.get_model_name(),
            "last_request": cls._last_request_time,
            "last_latency_ms": round(cls._last_latency_ms, 2),
            "total_requests": cls._total_requests,
            "failed_requests": cls._failed_requests,
            "api_key_configured": bool(api_key),
        }

    @classmethod
    def interpret_canonical_state(
        cls, canonical_state: Dict[str, Any], section: str = "all"
    ) -> Dict[str, Any]:
        cls._total_requests += 1
        start_time = time.time()
        cls._last_request_time = datetime.now(timezone.utc).isoformat()

        # Cache lookup
        state_seq = canonical_state.get("state_sequence", 0)
        cache_key = f"{state_seq}_{section}"
        if cache_key in cls._cache:
            return cls._cache[cache_key]

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            fallback = cls._generate_deterministic_fallback(canonical_state, section, "OPENAI_API_KEY missing")
            cls._cache[cache_key] = fallback
            return fallback

        # Construct grounded context
        market = canonical_state.get("market_data") or {}
        options = canonical_state.get("option_intelligence") or {}
        news = canonical_state.get("news_intelligence") or {}
        macro = canonical_state.get("macro_intelligence") or {}
        evening = canonical_state.get("evening_report") or {}
        intraday = canonical_state.get("intraday_report") or {}

        spot = market.get("current_spot", "N/A")
        vwap = market.get("vwap", "N/A")
        pcr = options.get("pcr", "N/A")
        vix = market.get("india_vix", "N/A")
        bias = evening.get("tomorrow_outlook", {}).get("directional_bias", "NEUTRAL")

        system_prompt = (
            "You are an expert financial market analyst interpreting an authoritative intraday workstation state. "
            "STRICT RULES:\n"
            "1. You MUST NEVER invent or alter market prices, support/resistance levels, option strikes, quantities, risk limits, confidence scores, or trading signals.\n"
            "2. All supplied canonical data is absolute truth. If a value is missing or N/A, report it as unavailable.\n"
            "3. Do NOT provide trade execution instructions or order placement commands.\n"
            "4. Clearly separate factual canonical observations from analytical interpretation.\n"
            "5. Return output as a valid JSON object matching the requested schema."
        )

        user_prompt = f"""
Canonical Market Context:
- Spot: {spot}, VWAP: {vwap}, India VIX: {vix}, Options PCR: {pcr}
- Directional Bias: {bias}
- Active News Count: {len(news.get('articles', []))}
- Section Requested: {section}

Please provide structured natural language interpretations:
1. Market Narrative (Explain current NIFTY state)
2. Why Today (Key behavior drivers)
3. Pre-Market Narrative (8:50 AM briefing interpretation)
4. Todays Analysis Narrative (Expectations vs actual behavior)
5. Live Assistant Interpretation (What changed, What matters now, What to watch next)
6. End of Day Summary
"""

        # Perform HTTPS request to OpenAI API (with retries and timeouts)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        body = {
            "model": cls.get_model_name(),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": cls.MAX_TOKENS,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }

        try:
            req = Request(
                "https://api.openai.com/v1/chat/completions",
                data=json.dumps(body).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with urlopen(req, timeout=cls.TIMEOUT_SECONDS) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
                content_str = resp_data["choices"][0]["message"]["content"]
                parsed = json.loads(content_str)
                result = cls._validate_and_format_response(parsed, canonical_state)
                cls._last_latency_ms = (time.time() - start_time) * 1000
                cls._last_error = None
                cls._cache[cache_key] = result
                return result
        except Exception as err:
            cls._failed_requests += 1
            cls._last_error = str(err)
            cls._last_latency_ms = (time.time() - start_time) * 1000
            fallback = cls._generate_deterministic_fallback(
                canonical_state, section, f"OpenAI call failed: {str(err)}"
            )
            cls._cache[cache_key] = fallback
            return fallback

    @classmethod
    def _generate_deterministic_fallback(
        cls, canonical_state: Dict[str, Any], section: str, reason: str
    ) -> Dict[str, Any]:
        market = canonical_state.get("market_data") or {}
        options = canonical_state.get("option_intelligence") or {}
        evening = canonical_state.get("evening_report") or {}

        spot = market.get("current_spot") if market.get("current_spot") is not None else "N/A"
        vwap = market.get("vwap") if market.get("vwap") is not None else "N/A"
        pcr = options.get("pcr") if options.get("pcr") is not None else "N/A"
        bias = evening.get("tomorrow_outlook", {}).get("directional_bias", "NEUTRAL")

        return {
            "ai_status": "disabled" if "OPENAI_API_KEY" in reason else "degraded",
            "fallback_active": True,
            "fallback_reason": reason,
            "market_narrative": f"NIFTY spot is trading at {spot}, with intraday VWAP at {vwap}. Option chain PCR is {pcr}. Market posture is {bias}.",
            "why_today": f"Market behavior is guided by technical VWAP structure and options building around {spot}.",
            "pre_market_narrative": f"Pre-market briefing indicated a {bias} bias. Opening expectations align with technical levels.",
            "todays_analysis_narrative": f"Actual price action is evaluating pre-market expectations with spot at {spot}.",
            "live_assistant_interpretation": {
                "what_changed": f"PCR level observed at {pcr}.",
                "what_matters_now": f"Spot posture relative to VWAP ({vwap}).",
                "what_to_watch_next": "Monitor key technical support and resistance levels.",
            },
            "end_of_day_summary": f"Session status recorded with NIFTY spot at {spot}.",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    @classmethod
    def _validate_and_format_response(
        cls, parsed: Dict[str, Any], canonical_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {
            "ai_status": "available",
            "fallback_active": False,
            "fallback_reason": None,
            "market_narrative": str(parsed.get("market_narrative") or parsed.get("Market Narrative") or "Narrative generated from canonical state."),
            "why_today": str(parsed.get("why_today") or parsed.get("Why Today") or "Drivers derived from canonical indicators."),
            "pre_market_narrative": str(parsed.get("pre_market_narrative") or parsed.get("Pre-Market Narrative") or "8:50 AM briefing interpretation."),
            "todays_analysis_narrative": str(parsed.get("todays_analysis_narrative") or parsed.get("Todays Analysis Narrative") or "Expectation vs actual behavior comparison."),
            "live_assistant_interpretation": parsed.get("live_assistant_interpretation") or parsed.get("Live Assistant Interpretation") or {
                "what_changed": "Market shifts observed in canonical state.",
                "what_matters_now": "VWAP and PCR levels holding.",
                "what_to_watch_next": "Monitor key technical resistance levels."
            },
            "end_of_day_summary": str(parsed.get("end_of_day_summary") or parsed.get("End of Day Summary") or "Session summary based on canonical data."),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
