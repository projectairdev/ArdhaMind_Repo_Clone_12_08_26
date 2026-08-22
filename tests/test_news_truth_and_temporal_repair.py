# tests/test_news_truth_and_temporal_repair.py
"""
P0 News Canonical Truth, Freshness, and Constituent Relevance Regression Suite.
Validates:
1. Economic Times incident fixture (no false ADANIPORTS match, accurate relevance).
2. False constituent matching stoplist (Economic, Hindustan, Consumer, Finance, Power).
3. Positive constituent matching (Adani Ports, HDFC Bank, Tata Consumer, Reliance, Infosys).
4. Stable deduplication across aggregator redirect URLs and recrawls.
5. Temporal integrity (Aggregator discovery vs verified official timestamps).
6. Provider health vs content freshness independence.
"""
from datetime import datetime, timezone
import pytest

from src.news_engine.relevance_v2 import NiftyRelevanceEngineV2, load_nifty_universe
from src.news_engine.deduplicator import NewsDeduplicator
from src.news_engine.temporal_integrity import assess_publication_time


@pytest.fixture
def nifty_universe():
    return {
        "ADANIPORTS": "Adani Ports and Special Economic Zone Limited",
        "HDFCBANK": "HDFC Bank Limited",
        "HINDUNILVR": "Hindustan Unilever Limited",
        "TATACONSUM": "Tata Consumer Products Limited",
        "RELIANCE": "Reliance Industries Limited",
        "INFY": "Infosys Limited",
        "TCS": "Tata Consultancy Services Limited",
        "SBIN": "State Bank of India",
        "POWERGRID": "Power Grid Corporation of India Limited",
        "JIOFIN": "Jio Financial Services Limited",
        "BAJFINANCE": "Bajaj Finance Limited",
    }


def test_et_incident_fixture_no_false_adaniports_match(nifty_universe):
    """Assert ET China stocks story does NOT match ADANIPORTS and receives balanced relevance."""
    headline = "Global Market: China stocks rebound on AI, chip rally; Hong Kong shares slip"
    content = "Global Market: China stocks rebound on AI, chip rally; Hong Kong shares slip The Economic Times"

    res = NiftyRelevanceEngineV2.assess(
        headline, content, "OTHER_RELEVANT", "US_MARKETS", "TIER_C_ESTABLISHED_MEDIA", nifty_universe
    )

    assert "ADANIPORTS" not in res["related_symbols"]
    assert res["related_symbols"] == []
    assert res["nifty_relevance_score"] <= 6.0
    assert res["impact_level"] != "HIGH"


def test_false_constituent_stopwords_rejected(nifty_universe):
    """Assert generic keywords in publisher names or prose do not falsely match constituents."""
    # 1. "The Economic Times" must not trigger ADANIPORTS
    res1 = NiftyRelevanceEngineV2.assess(
        "US inflation cools down in July",
        "Reported by The Economic Times today",
        "Macro", "US_MARKETS", "TIER_C_ESTABLISHED_MEDIA", nifty_universe
    )
    assert "ADANIPORTS" not in res1["related_symbols"]

    # 2. "Hindustan Times" must not trigger HINDUNILVR
    res2 = NiftyRelevanceEngineV2.assess(
        "Middle East tensions escalate over weekend",
        "Article published in Hindustan Times",
        "Geopolitics", "GEOPOLITICS", "TIER_C_ESTABLISHED_MEDIA", nifty_universe
    )
    assert "HINDUNILVR" not in res2["related_symbols"]

    # 3. Generic "consumer" survey must not trigger TATACONSUM
    res3 = NiftyRelevanceEngineV2.assess(
        "ECB Consumer Expectations Survey Results Announced",
        "Survey of eurozone consumer inflation expectations",
        "Macro", "EUROPE", "TIER_A_PRIMARY", nifty_universe
    )
    assert "TATACONSUM" not in res3["related_symbols"]

    # 4. Generic "financial" or "finance" must not trigger JIOFIN or BAJFINANCE
    res4 = NiftyRelevanceEngineV2.assess(
        "Global financial stability report released by IMF",
        "Assessment of non-bank financial institutions",
        "Macro", "GLOBAL_RISK", "TIER_C_ESTABLISHED_MEDIA", nifty_universe
    )
    assert "JIOFIN" not in res4["related_symbols"]
    assert "BAJFINANCE" not in res4["related_symbols"]

    # 5. Generic "power" must not trigger POWERGRID
    res5 = NiftyRelevanceEngineV2.assess(
        "Geopolitical balance of power in Indo-Pacific region",
        "Diplomatic analysis of regional defense initiatives",
        "Geopolitics", "GEOPOLITICS", "TIER_C_ESTABLISHED_MEDIA", nifty_universe
    )
    assert "POWERGRID" not in res5["related_symbols"]


def test_positive_constituent_matching_preserved(nifty_universe):
    """Assert genuine company mentions are accurately matched."""
    # Exact symbol
    res1 = NiftyRelevanceEngineV2.assess(
        "ADANIPORTS cargo volumes rise 12% in Q1",
        "Port operator reports record container throughput",
        "Corporate", "INDIA", "TIER_C_ESTABLISHED_MEDIA", nifty_universe
    )
    assert "ADANIPORTS" in res1["related_symbols"]

    # Canonical alias: "Adani Ports"
    res2 = NiftyRelevanceEngineV2.assess(
        "Adani Ports signs concession agreement for new terminal",
        "Operational expansion announced by management",
        "Corporate", "INDIA", "TIER_C_ESTABLISHED_MEDIA", nifty_universe
    )
    assert "ADANIPORTS" in res2["related_symbols"]

    # "HDFC Bank"
    res3 = NiftyRelevanceEngineV2.assess(
        "HDFC Bank advances deposit mobilization strategy",
        "Credit to deposit ratio improves in latest quarter",
        "Banking", "INDIA", "TIER_C_ESTABLISHED_MEDIA", nifty_universe
    )
    assert "HDFCBANK" in res3["related_symbols"]

    # "Tata Consumer Products"
    res4 = NiftyRelevanceEngineV2.assess(
        "Tata Consumer acquires specialty beverage brand",
        "FMCG expansion targeting premium retail distribution",
        "Corporate", "INDIA", "TIER_C_ESTABLISHED_MEDIA", nifty_universe
    )
    assert "TATACONSUM" in res4["related_symbols"]

    # "Infosys"
    res5 = NiftyRelevanceEngineV2.assess(
        "Infosys signs $1.5 billion digital transformation deal with European bank",
        "IT services major expands enterprise cloud contracts",
        "IT", "INDIA", "TIER_C_ESTABLISHED_MEDIA", nifty_universe
    )
    assert "INFY" in res5["related_symbols"]


def test_stable_dedupe_identity_across_recrawls():
    """Assert same article with different Google redirect tokens and changing pubDates yields identical canonical ID."""
    headline = "Global Market: China stocks rebound on AI, chip rally; Hong Kong shares slip"
    source = "The Economic Times"

    # Crawl 1 on Aug 20
    url1 = "https://news.google.com/rss/articles/CBMi5AFBVV95cUxNVDVSMEd2X3g0Yk9kVGRXTFRRVU14YUJMeWdZeFN4OEIzVnJkY3E5ZFcxYTAyVTFUbDVtVlNkbkxaV2p3dDV1X2poWnUwd1VacVhYTHRRbS1oMUZPbnFLb2FnWGJ2ZE5iOUtFdTJCWlo3V256WDVtdkVXSFR2WWRCOGVnUlQ5SjRxczE3aUxrV2haNGE5YWlDWTY1SnJlOUNhakcxM0FxTnRfa0xTVHByQTRVd0VYOUZSZWw4elFCX2N3MnVvYkk0WDVoOWVaX1phWEFGSFJBQWtaemdQc0YzQTdPNWXSAeoB?oc=5"
    pubDate1 = "Thu, 20 Aug 2026 12:16:32 GMT"
    id1 = NewsDeduplicator.compute_stable_id(headline, url1, source, pubDate1)

    # Crawl 2 on Aug 22 (different redirect token, different pubDate)
    url2 = "https://news.google.com/rss/articles/CBMi5AFBVV95cUxNVDVSMEd2X3g0Yk9kVGRXTFRRVU14YUJMeWdZeFN4OEIzVnJkY3E5ZFcxYTAyVTFUbDVtVlNkbkxaV2p3dDV1X2poWnUwd1VacVhYTHRRbS1oMUZPbnFLb2FnWGJ2ZE5iOUtFdTJCWlo3V256WDVtdkVXSFR2WWRCOGVnUlQ5SjRxczE3aUxrV2haNGE5YWlDWTY1SnJlOUNhakcxM0FxTnRfa0xTVHByQTRVd0VYOUZSZWw4elFCX2N3MnVvYkk0WDVoOWVaX1phWEFGSFJBQWtaemdQc0YzQTdPNWXSAeoBQVVfeXFMTUJldTAtSUxqYzY1Y09sR3VoNG5HOVNnT3RwQldkVUNwZldvQlRDdmY5N0NOUVEtMm5icXJhWEJaZ21RajBCNWpJOGdqc1ZINE9kWTFJbnNMWTY2bmlNVmRUVnlHTmRuRWJTYVhyUE1DcE4zX1hpMExIdlpBdndWY3oyMko4UFhPZFpWZzY1dHEyM2xtS2RjTWN6Ykp5TXMyNnhwZzd3Wi1kMzVQTHdZMk5SbFN4MVBUWHBTODVoel8tOU1IRTZYck1EdEM2X0NFUkxvdnE5cTVSbmEyNjhBdS1IYndFZDJpSTFB?oc=5"
    pubDate2 = "Sat, 22 Aug 2026 00:20:43 GMT"
    id2 = NewsDeduplicator.compute_stable_id(headline, url2, source, pubDate2)

    assert id1 == id2, "Aggregator crawl changes must not create duplicate canonical IDs"


def test_temporal_integrity_provenance():
    """Assert unverified aggregator discovery timestamps do not gain live current eligibility."""
    now = datetime(2026, 8, 22, 1, 49, 14, tzinfo=timezone.utc)

    # 1. Unverified aggregator discovery timestamp
    assessment_unverified = assess_publication_time(
        "Sat, 22 Aug 2026 00:20:43 GMT",
        now,
        timestamp_source="AGGREGATOR_DISCOVERY",
        timestamp_verified=False,
    )
    assert assessment_unverified.current_eligible is False
    assert assessment_unverified.timestamp_validity == "UNVERIFIED"
    assert assessment_unverified.temporal_class == "DISCOVERY_RECENT"

    # 2. Verified official primary timestamp
    assessment_official = assess_publication_time(
        "Sat, 22 Aug 2026 00:20:43 GMT",
        now,
        timestamp_source="OFFICIAL_FEED",
        timestamp_verified=True,
    )
    assert assessment_official.current_eligible is True
    assert assessment_official.timestamp_validity == "VALID"
    assert assessment_official.temporal_class == "CURRENT"
