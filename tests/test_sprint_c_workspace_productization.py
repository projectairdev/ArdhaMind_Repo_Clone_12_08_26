from pathlib import Path


ROOT = Path("src/frontend/components")


def source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_shared_semantic_components_cover_required_states():
    text = source("intelligence/CanonicalPresentation.tsx")
    for state in ("READY", "PARTIAL", "BLOCKED", "STALE", "LAST_VALID_SESSION", "UNAVAILABLE"):
        assert state in text


def test_shared_components_preserve_provenance_and_freshness():
    text = source("intelligence/CanonicalPresentation.tsx")
    assert "Source:" in text and "Observed:" in text
    assert 'kind="freshness"' in text


def test_key_levels_are_canonical_and_never_filled_with_defaults():
    text = source("intelligence/CanonicalPresentation.tsx")
    assert "Genuine key levels" in text
    assert "no genuine canonical level is eligible" in text
    assert "PRICE_STRUCTURE" not in text and "OPTION_OI" not in text


def test_scenario_cards_are_conditional_not_predictions():
    text = source("intelligence/CanonicalPresentation.tsx")
    assert "Conditional scenario only" in text
    assert "Not a prediction" in text and "No execution instruction" in text


def test_nifty_live_is_a_canonical_command_center():
    text = source("NiftyLiveWorkspace.tsx")
    assert '<UnifiedIntelligencePanel workspace="NIFTY_LIVE"' in text
    assert all(term in text for term in ("SpotSummary", "breadth", "top_gainers", "top_losers", "PCR / Max Pain", "ATM Option IV"))


def test_nifty_live_preserves_closed_session_and_last_valid_semantics():
    text = source("NiftyLiveWorkspace.tsx")
    assert "LAST_VALID_SESSION" in text and "isClosed" in text
    assert "Previous-session comparison unavailable" in text


def test_unified_panel_uses_only_canonical_state():
    text = source("UnifiedIntelligencePanel.tsx")
    assert "canonicalState?.unified_intelligence" in text
    assert "fetch(" not in text and "axios" not in text
    assert "BREADTH_MIN_COVERAGE" not in text and "pcr >" not in text.lower()


def test_all_decision_workspaces_share_one_panel():
    phase = source("PhaseOneWorkspaces.tsx")
    premarket = source("PreMarketPlannerWorkspace.tsx")
    nifty = source("NiftyLiveWorkspace.tsx")
    assert '<UnifiedIntelligencePanel workspace="PRE_MARKET"' in premarket
    assert '<UnifiedIntelligencePanel workspace="TODAYS_ANALYSIS"' in phase
    assert '<UnifiedIntelligencePanel workspace="LIVE_ASSISTANT"' in phase
    assert '<UnifiedIntelligencePanel workspace="NIFTY_LIVE"' in nifty


def test_live_assistant_is_structured_canonical_explanation_not_chatbot():
    text = source("UnifiedIntelligencePanel.tsx")
    assert all(question in text for question in ("What is the market state?", "What is the current risk?", "How complete is the evidence?"))
    assert "openai" not in text.lower() and "chatbot" not in text.lower()


def test_change_intelligence_unavailable_is_explicit():
    text = source("UnifiedIntelligencePanel.tsx")
    assert "What changed?" in text
    assert 'change.status || "UNAVAILABLE"' in text


def test_news_workspace_prioritizes_and_preserves_provider_isolation():
    text = source("NewsIntelligence.tsx")
    assert "Market-moving" in text and "Market Impact" in text
    assert "Partial provider coverage" in text
    assert "Healthy-provider items remain available" in text


def test_news_items_keep_source_time_and_impact_metadata():
    text = source("NewsIntelligence.tsx")
    assert "source_name" in text and "published_at" in text
    assert "nifty_relevance" in text and "impact_level" in text


def test_settings_hides_broker_identifier_and_bounded_diagnostics():
    text = source("SettingsDashboard.tsx")
    assert "PROFILE VALIDATED — IDENTIFIER HIDDEN" in text
    assert "brokerStatus: {" in text
    assert "brokerStatus: broker" not in text


def test_settings_exposes_license_and_not_configured_states_truthfully():
    text = source("SettingsDashboard.tsx")
    assert "LICENSE_REQUIRED" in text or "license" in text.lower()
    assert text.count('provider: "Not configured"') >= 2
    assert "no estimates are rendered" in text.lower()


def test_productization_adds_no_workspace_network_or_reasoning_engine():
    productized = "\n".join(source(path) for path in (
        "UnifiedIntelligencePanel.tsx", "NiftyLiveWorkspace.tsx",
        "PreMarketPlannerWorkspace.tsx", "intelligence/CanonicalPresentation.tsx",
    ))
    assert "fetch(" not in productized
    assert "new WebSocket" not in productized
    assert "score =" not in productized.lower()
    assert "synthetic" not in productized.lower()
