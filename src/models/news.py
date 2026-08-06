from __future__ import annotations

from dataclasses import dataclass


@dataclass
class NewsHeadline:
    title: str
    source: str
    published_at: str
    link: str
    sentiment: str
    score: float


@dataclass
class NewsContext:
    enabled: bool
    scanned_at: str
    overall_bias: str
    score: float
    rationale: str
    key_factors: list[str]
    headlines: list[NewsHeadline]
    error: str = ""
