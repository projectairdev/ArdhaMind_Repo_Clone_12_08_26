"""Machine-readable source ownership for critical canonical sections."""

PROVENANCE_REGISTRY = {
    "market_data": {"source": "kite_market_feed", "classification": "live"},
    "technical_analysis": {"source": "market_analysis_pipeline", "classification": "calculated"},
    "option_intelligence": {"source": "option_analysis_pipeline", "classification": "calculated"},
    "market_score": {"source": "scoring_pipeline", "classification": "calculated"},
    "opportunity": {"source": "opportunity_pipeline", "classification": "calculated"},
    "strategy_suitability": {"source": "strategy_engine", "classification": "calculated"},
    "confidence": {"source": "confidence_pipeline", "classification": "calculated"},
    "deterministic_risk": {"source": "risk_engine_v2", "classification": "calculated"},
    "decision_support": {"source": "decision_support_adapter", "classification": "calculated"},
    "news_intelligence": {"source": "news_provider", "classification": "unavailable"},
}
