from __future__ import annotations

from datetime import datetime
from html import unescape
import os
from typing import Dict, List, Tuple
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from src.configuration_engine.runtime import Config
from src.models import NewsHeadline, NewsContext
from src.utils import setup_logger, now_str

logger = setup_logger("NewsEngine")


def env_bool(name: str, default: bool = True) -> bool:
    value = (os.getenv(name) or "").strip().lower()
    if not value:
        return default
    return value in {"1", "true", "yes", "on"}


def market_news_queries() -> List[str]:
    default_queries = [
        "Nifty 50 India market",
        "India crude oil prices market",
        "Iran oil market India",
        "RBI FII DII India market",
    ]
    extra_queries = [
        item.strip()
        for item in (os.getenv("MARKET_NEWS_EXTRA_QUERIES") or "").split("|")
        if item.strip()
    ]
    query_limit = int(os.getenv("MARKET_NEWS_QUERY_LIMIT", str(Config.MARKET_NEWS_QUERY_LIMIT)))
    return (extra_queries + default_queries)[:query_limit]


def build_google_news_rss_url(query: str) -> str:
    params = urlencode({"q": query, "hl": "en-IN", "gl": "IN", "ceid": "IN:en"})
    return f"https://news.google.com/rss/search?{params}"


def market_news_feed_urls() -> List[str]:
    override = [
        item.strip()
        for item in (os.getenv("MARKET_NEWS_FEEDS") or "").split(",")
        if item.strip()
    ]
    if override:
        return override
    return [build_google_news_rss_url(query) for query in market_news_queries()]


def fetch_feed_items(url: str, timeout_seconds: float) -> List[Dict[str, str]]:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=timeout_seconds) as response:
        payload = response.read()

    root = ET.fromstring(payload)
    items: List[Dict[str, str]] = []
    for item in root.findall(".//item"):
        row: Dict[str, str] = {}
        for child in item:
            tag = child.tag.rsplit("}", 1)[-1].lower()
            text = (child.text or "").strip()
            if tag == "title":
                row["title"] = unescape(text)
            elif tag == "link":
                row["link"] = text
            elif tag in {"pubdate", "published"}:
                row["published_at"] = text
            elif tag == "source":
                row["source"] = unescape(text)
        if row.get("title"):
            row.setdefault("source", urlparse(row.get("link", "")).netloc or "Unknown")
            row.setdefault("published_at", "")
            items.append(row)
    return items


def sentiment_from_score(score: float) -> str:
    if score >= 0.6:
        return "BULLISH"
    if score <= -0.6:
        return "BEARISH"
    return "NEUTRAL"


def score_market_headline(title: str) -> Tuple[float, List[str]]:
    text = title.lower()
    score = 0.0
    factors: List[str] = []

    market_terms = ["nifty", "sensex", "india", "indian market", "rbi", "fii", "dii", "crude", "oil", "iran"]
    relevance = sum(1 for term in market_terms if term in text)
    if relevance == 0:
        relevance = 1

    if any(term in text for term in ["war", "missile", "attack", "strike", "drone", "escalation", "sanction", "conflict"]):
        score -= 1.2
        factors.append("geopolitical_risk")

    if any(term in text for term in ["ceasefire", "de-escalation", "peace talks", "truce", "diplomatic"]):
        score += 1.0
        factors.append("geopolitical_relief")

    if any(term in text for term in ["crude", "oil", "brent", "wti", "opec", "hormuz"]):
        if any(term in text for term in ["surge", "jump", "rise", "spike", "higher", "hits", "climbs"]):
            score -= 1.4
            factors.append("rising_oil")
        if any(term in text for term in ["fall", "ease", "cool", "slip", "lower", "drops", "declines"]):
            score += 1.2
            factors.append("easing_oil")

    if "rbi" in text:
        if "rate cut" in text or "accommodative" in text:
            score += 0.9
            factors.append("rbi_supportive")
        if "rate hike" in text or "hawkish" in text:
            score -= 0.9
            factors.append("rbi_hawkish")

    if "fii" in text or "foreign investors" in text:
        if any(term in text for term in ["buy", "inflow", "net buyers"]):
            score += 0.8
            factors.append("fii_buying")
        if any(term in text for term in ["sell", "outflow", "net sellers"]):
            score -= 0.8
            factors.append("fii_selling")

    if "inflation" in text:
        if any(term in text for term in ["cool", "ease", "lower", "softens"]):
            score += 0.7
            factors.append("cooling_inflation")
        if any(term in text for term in ["hot", "rises", "higher", "sticky"]):
            score -= 0.7
            factors.append("hot_inflation")

    if "nifty" in text or "sensex" in text:
        if any(term in text for term in ["rally", "gains", "record high", "surges", "up"]):
            score += 0.6
            factors.append("market_strength")
        if any(term in text for term in ["selloff", "slides", "falls", "down", "crash"]):
            score -= 0.6
            factors.append("market_weakness")

    return round(score * min(1.6, 1 + (relevance - 1) * 0.12), 2), factors


def aggregate_market_news() -> NewsContext:
    if not env_bool("ENABLE_MARKET_NEWS", Config.ENABLE_MARKET_NEWS):
        return NewsContext(
            enabled=False,
            scanned_at=now_str(),
            overall_bias="DISABLED",
            score=0.0,
            rationale="Market news disabled by configuration.",
            key_factors=[],
            headlines=[],
        )

    timeout_seconds = float(os.getenv("MARKET_NEWS_TIMEOUT_SECONDS", str(Config.MARKET_NEWS_TIMEOUT_SECONDS)))
    headline_limit = int(os.getenv("MARKET_NEWS_HEADLINE_LIMIT", str(Config.MARKET_NEWS_HEADLINE_LIMIT)))
    dedupe = set()
    headlines: List[NewsHeadline] = []
    factor_counts: Dict[str, int] = {}
    fetch_errors: List[str] = []

    for url in market_news_feed_urls():
        try:
            items = fetch_feed_items(url, timeout_seconds=timeout_seconds)
        except Exception as exc:
            fetch_errors.append(str(exc))
            continue

        for item in items:
            title = item.get("title", "").strip()
            key = title.lower()
            if not title or key in dedupe:
                continue
            dedupe.add(key)

            score, factors = score_market_headline(title)
            if score == 0 and not factors:
                continue

            for factor in factors:
                factor_counts[factor] = factor_counts.get(factor, 0) + 1

            published_at = item.get("published_at", "")
            if published_at:
                # Timezone-aware UTC ISO ('...Z'); never a naive strftime strip
                # (drops the offset -> frontend re-applies IST -> future-dated).
                from src.news_engine.safe_utils import rfc822_to_utc_iso
                normalized_published = rfc822_to_utc_iso(published_at)
                if normalized_published:
                    published_at = normalized_published

            headlines.append(
                NewsHeadline(
                    title=title,
                    source=item.get("source", "Unknown"),
                    published_at=published_at,
                    link=item.get("link", ""),
                    sentiment=sentiment_from_score(score),
                    score=score,
                )
            )

    headlines = sorted(headlines, key=lambda item: abs(item.score), reverse=True)[:headline_limit]

    if not headlines:
        error_message = fetch_errors[0] if fetch_errors else "No relevant market-moving headlines found."
        return NewsContext(
            enabled=True,
            scanned_at=now_str(),
            overall_bias="NEUTRAL",
            score=0.0,
            rationale="News fetch returned no usable market headlines.",
            key_factors=[],
            headlines=[],
            error=error_message,
        )

    total_score = sum(item.score for item in headlines)
    normalized_score = round(max(-1.0, min(1.0, total_score / max(len(headlines) * 1.5, 1))), 2)
    if normalized_score >= 0.18:
        overall_bias = "BULLISH"
    elif normalized_score <= -0.18:
        overall_bias = "BEARISH"
    else:
        overall_bias = "NEUTRAL"

    sorted_factors = sorted(factor_counts.items(), key=lambda item: (-item[1], item[0]))
    key_factors = [name for name, _ in sorted_factors[:4]]
    rationale = (
        f"News bias {overall_bias} ({normalized_score:+.2f}) from {len(headlines)} relevant headlines. "
        f"Top factors: {', '.join(key_factors) if key_factors else 'mixed'}."
    )

    return NewsContext(
        enabled=True,
        scanned_at=now_str(),
        overall_bias=overall_bias,
        score=normalized_score,
        rationale=rationale,
        key_factors=key_factors,
        headlines=headlines,
        error=fetch_errors[0] if fetch_errors and not headlines else "",
    )
