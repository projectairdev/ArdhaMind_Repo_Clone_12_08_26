# Part 11: News Intelligence & Sentiment Analysis

This section documents the news ingestion pipelines, deduplication filters, sentiment weighting math, and future provider expansion architectures within the NIFTY Option Finder & Market Intelligence Workstation.

---

## 🔌 News Ingestion & Normalization

The workstation incorporates macroeconomic events and breakout headlines to supplement technical momentum indicators. 

### 1. Ingestion Flow
The `NewsPipeline` executes concurrently on a separate polling thread (typically every 60 seconds), fetching raw articles from:
- Financial News RSS Feeds (e.g., Bloomberg, Reuters, Moneycontrol).
- Scheduled Macroeconomic Calendars (e.g., RBI rate announcements, US Federal Reserve statements, inflation statistics).

### 2. Normalization Schema
Raw data formats differ across providers. The engine normalizes all incoming articles into an intermediate `RawArticle` contract before analysis:

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class RawArticle:
    headline: str
    summary: str
    source: str
    published_at: datetime
    url: str
```

---

## 🔍 Semantic Deduplication

To prevent a single news story published by multiple outlets from artificially multiplying sentiment scores, the engine filters articles using semantic comparison checks:

1. **Jaccard Distance Check**: Computes token overlap between headlines. If overlap exceeds 75%, articles are categorized as duplicates.
2. **Cosine Similarity Check**: If headlines differ slightly in vocabulary but share semantic meaning, a local TF-IDF vectorizer compares the text strings. If similarity exceeds `0.80`, the duplicate is dropped.

---

## 📈 Sentiment Weighting & Deceleration

Once normalized and deduplicated, each article is evaluated by a sentiment analyzer, producing a score ranging from `-1.0` (extremely bearish) to `+1.0` (extremely bullish).

To ensure that news impact is mathematically bounded and decay-weighted over time, the final news sentiment multiplier is computed using two algorithms:

### 1. Severity Impact Weighting
Articles containing critical regulatory or macroeconomic keywords (e.g., "RBI hike", "War escalation", "Default") are assigned a **High Severity** flag. These articles are given triple weight in cumulative scoring averages.

### 2. Time Decay Deceleration
The impact of a news article decays exponentially over time, mirroring the market's digestion speed:
$$S(t) = S_0 \times e^{-\lambda t}$$
Where $S(t)$ is the current decayed sentiment score, $S_0$ is the original sentiment score, $t$ is the minutes elapsed since publication, and $\lambda$ is the decay constant (typically set to `0.015`, resulting in a 3-hour news half-life).

---

## 🔄 Sentiment Score Multiplier Integration

The cumulative news sentiment score acts as a scaling multiplier inside the `OpportunityPipeline`. 

- If news sentiment is extremely negative (`-0.75`), while technical scoring models evaluate a bullish grade of `85.0`, the sentiment score reduces the final directional opportunity strength:
  $$\text{Adjusted Opportunity Score} = 85.0 \times (1.0 + \text{Sentiment Score}) = 85.0 \times 0.25 = 21.25$$
  This drops the opportunity below the trade initiation threshold, preventing bullish positions during panic selling events.

---

## 🔌 Future Ingestion Provider Adaptations

The engine is decoupled from specific news APIs. Developers can integrate new providers by subclassing the base scraper:

```python
class BaseNewsProvider:
    def fetch_headlines(self) -> List[RawArticle]:
        raise NotImplementedError
```

This clean abstraction allows developers to add future providers (such as social sentiment trackers or custom Bloomberg terminal bridges) without modifying core scoring calculations.
