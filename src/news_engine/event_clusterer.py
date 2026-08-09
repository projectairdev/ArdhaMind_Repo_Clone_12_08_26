"""Deterministic cross-source event clustering for global market news."""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List

from src.models.news_context_v2 import EventCluster, NewsItem
from src.news_engine.relevance_v2 import parse_timestamp, recency
from src.news_engine.source_authority import authority_rank


STOPWORDS = {
    "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "with", "as", "at", "by",
    "from", "after", "amid", "over", "says", "said", "news", "latest", "update", "market", "markets",
    "stock", "stocks", "could", "may", "this", "that", "its", "is", "are", "be", "has", "have",
}


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", str(text or "").lower())
    return {word for word in words if len(word) > 2 and word not in STOPWORDS}


def _similarity(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _category_family(category: str) -> str:
    value = str(category or "Other")
    if value in {"Crude", "Geopolitics"}:
        return "ENERGY_GEOPOLITICS"
    if value in {"Macro", "Currency/Yields", "RBI", "Government Policy"}:
        return "MACRO_RATES"
    if value in {"Global Markets", "Exchange Operations"}:
        return "MARKETS"
    return value


def _independent_publishers(articles: List[NewsItem]) -> List[str]:
    publishers = []
    fingerprints = set()
    for article in articles:
        publisher = article.publisher or article.source_name or "Unknown"
        fingerprint = re.sub(r"[^a-z0-9]", "", publisher.lower())
        headline_fingerprint = " ".join(sorted(_tokens(article.headline)))
        syndication_key = (fingerprint, headline_fingerprint)
        if syndication_key in fingerprints:
            continue
        fingerprints.add(syndication_key)
        if publisher not in publishers:
            publishers.append(publisher)
    return publishers


class NewsEventClusterer:
    WINDOW_SECONDS = 36 * 3600

    @classmethod
    def cluster(cls, articles: Iterable[NewsItem]) -> List[EventCluster]:
        ordered = sorted(list(articles), key=lambda item: parse_timestamp(item.published_at) or datetime.min.replace(tzinfo=timezone.utc))
        groups: List[List[NewsItem]] = []
        group_tokens: List[set[str]] = []
        for article in ordered:
            article_tokens = _tokens(f"{article.headline} {article.summary_snippet}")
            observed = parse_timestamp(article.published_at)
            matched = None
            for index, group in enumerate(groups):
                anchor = group[-1]
                anchor_time = parse_timestamp(anchor.published_at)
                if observed and anchor_time and abs((observed - anchor_time).total_seconds()) > cls.WINDOW_SECONDS:
                    continue
                same_family = _category_family(article.category) == _category_family(anchor.category)
                shared_symbol = bool(set(article.affected_symbols) & set(anchor.affected_symbols))
                shared_country = bool(set(article.related_countries) & set(anchor.related_countries))
                similarity = _similarity(article_tokens, group_tokens[index])
                if same_family and (similarity >= 0.24 or shared_symbol or (shared_country and similarity >= 0.16)):
                    matched = index
                    break
            if matched is None:
                groups.append([article])
                group_tokens.append(set(article_tokens))
            else:
                groups[matched].append(article)
                group_tokens[matched].update(article_tokens)

        clusters = [cls._build(group) for group in groups]
        clusters.sort(key=lambda item: item.priority_score, reverse=True)
        return clusters

    @staticmethod
    def _build(articles: List[NewsItem]) -> EventCluster:
        ranked = sorted(articles, key=lambda item: (authority_rank(item.source_tier), item.priority_score), reverse=True)
        current_articles = [item for item in articles if item.canonical_eligible]
        current_ranked = sorted(current_articles, key=lambda item: (authority_rank(item.source_tier), item.priority_score), reverse=True)
        # Historical lineage can remain attached, but only a current update may
        # determine the headline of a current cluster.
        canonical = current_ranked[0] if current_ranked else ranked[0]
        timestamps = [(parse_timestamp(item.published_at), item.published_at) for item in articles]
        valid = [(dt, raw) for dt, raw in timestamps if dt is not None]
        first_seen = min(valid, key=lambda item: item[0])[1] if valid else ""
        last_updated = max(valid, key=lambda item: item[0])[1] if valid else ""
        publishers = _independent_publishers(articles)
        primary_sources = list(dict.fromkeys(item.publisher or item.source_name for item in articles if item.source_tier == "TIER_A_PRIMARY"))
        if primary_sources and len(publishers) >= 2:
            verification = "VERY_HIGH"
        elif primary_sources:
            verification = "VERIFIED"
        elif len(publishers) >= 3:
            verification = "HIGH"
        elif len(publishers) >= 2:
            verification = "MEDIUM"
        else:
            verification = "LOW"
        directions = {item.expected_direction.upper() for item in articles if item.expected_direction.upper() not in {"NOT_ASSESSED", "UNCERTAIN"}}
        direction = directions.pop() if len(directions) == 1 else "MIXED" if len(directions) > 1 else "NOT_ASSESSED"
        impact_rank = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        impact = max((item.impact_strength.upper() for item in articles), key=lambda value: impact_rank.get(value, 0), default="LOW")
        relevance = max((item.nifty_relevance_score for item in articles), default=0.0)
        latest_current = max(
            current_articles,
            key=lambda item: parse_timestamp(item.published_at) or datetime.min.replace(tzinfo=timezone.utc),
            default=None,
        )
        if latest_current:
            state = latest_current.temporal_class
            _, _, decay = recency(latest_current.published_at)
        else:
            state = "HISTORICAL"
            decay = 0.0
        confirmation_bonus = {"LOW": 0, "MEDIUM": 6, "HIGH": 10, "VERIFIED": 12, "VERY_HIGH": 16}[verification]
        priority = round(relevance * 10 + impact_rank.get(impact, 1) * 8 + authority_rank(canonical.source_tier) * 3 + decay * 10 + confirmation_bonus, 2)
        identity = "|".join(sorted(item.id for item in articles))
        cluster_id = "EVT-" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20]
        reasons = list(dict.fromkeys(reason for item in ranked for reason in item.assessment_reasons))
        return EventCluster(
            event_cluster_id=cluster_id,
            canonical_headline=canonical.headline,
            category=canonical.category,
            first_seen=first_seen,
            last_updated=last_updated,
            article_count=len(articles),
            publishers=publishers,
            primary_sources=primary_sources,
            related_countries=list(dict.fromkeys(country for item in articles for country in item.related_countries)),
            related_symbols=list(dict.fromkeys(symbol for item in articles for symbol in item.affected_symbols)),
            verification_strength=verification,
            nifty_relevance=relevance,
            impact_level=impact,
            expected_direction=direction,
            reasoning="; ".join(reasons[:3]) or "No deterministic transmission mechanism identified.",
            affected_channels=list(dict.fromkeys(channel for item in articles for channel in item.affected_channels)),
            article_ids=[item.id for item in articles],
            discovery_streams=list(dict.fromkeys(item.discovery_stream for item in articles if item.discovery_stream)),
            recency_state=state,
            priority_score=priority,
            latest_article_published_at=last_updated,
            current_article_count=len(current_articles),
            historical_article_count=len(articles) - len(current_articles),
            temporal_class=state,
            canonical_eligible=bool(current_articles),
        )
