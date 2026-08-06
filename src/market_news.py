#!/usr/bin/env python3
from __future__ import annotations

import os
import sys

# Add src to python path if run as script
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import setup_logger
from src.utils.io_utils import export_json_file
from src.news_engine import aggregate_market_news
from src.ui import print_news_context

logger = setup_logger("MarketNewsApp")


def main() -> None:
    logger.info("Starting evening news sentiment analysis...")
    news_ctx = aggregate_market_news()

    # Formatted terminal print
    print_news_context(news_ctx)

    # Export news data
    news_dict = {
        "enabled": news_ctx.enabled,
        "scanned_at": news_ctx.scanned_at,
        "overall_bias": news_ctx.overall_bias,
        "score": news_ctx.score,
        "rationale": news_ctx.rationale,
        "key_factors": news_ctx.key_factors,
        "headlines": [
            {
                "title": h.title,
                "source": h.source,
                "published_at": h.published_at,
                "link": h.link,
                "sentiment": h.sentiment,
                "score": h.score,
            }
            for h in news_ctx.headlines
        ],
        "error": news_ctx.error,
    }

    filepath = os.path.join("scanner_output", "market_news.json")
    export_json_file(news_dict, filepath)
    logger.info(f"Market news report written to: {filepath}")


if __name__ == "__main__":
    main()
