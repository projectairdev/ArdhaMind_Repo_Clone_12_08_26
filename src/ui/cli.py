from __future__ import annotations

from typing import Dict, List, Any
import pandas as pd
from src.models import MarketRegime, OptionSignal, StockSignal, NewsContext


def print_market_regime(regime: MarketRegime) -> None:
    print("=" * 100)
    print(f"SCAN TIME       : {regime.scanned_at}")
    print(f"NIFTY TREND     : {regime.nifty_trend}")
    print(f"BANKNIFTY TREND : {regime.banknifty_trend}")
    print(f"OVERALL BIAS    : {regime.overall_bias}")
    print(f"REGIME SCORE    : {regime.regime_score}")
    print(f"REGIME TYPE     : {regime.regime_label}")
    print(f"VOLATILITY %    : {regime.volatility_score}")
    print(f"MARKET BREADTH  : {regime.market_breadth}")
    print(
        f"STRONG SECTORS  : {', '.join(regime.strong_sectors) if regime.strong_sectors else 'N/A'}"
    )
    print(
        f"WEAK SECTORS    : {', '.join(regime.weak_sectors) if regime.weak_sectors else 'N/A'}"
    )
    print(f"RATIONALE       : {regime.rationale}")
    print("=" * 100)


def print_signal(sig: OptionSignal) -> None:
    print("=" * 100)
    print(f"SCANNED AT          : {sig.scanned_at}")
    print(f"UNDERLYING QUOTE AT : {sig.underlying_quote_time}")
    print(f"OPTION QUOTE AT     : {sig.option_quote_time}")
    print(f"MARKET BIAS         : {sig.market_bias}")
    print(f"SETUP TYPE          : {sig.setup_type}")
    print(f"CONFIDENCE          : {sig.confidence}")
    print(f"STRATEGY REGIME     : {sig.strategy_regime}")

    print(f"UNDERLYING          : {sig.underlying}")
    print(f"UNDERLYING SPOT     : {sig.underlying_spot}")
    print(f"TRIGGER             : {sig.underlying_trigger}")
    print(
        f"TRIGGER DISTANCE    : {sig.trigger_distance_abs} ({sig.trigger_distance_pct}%)"
    )
    print(f"TREND               : {sig.trend}")
    print(
        f"TIMEFRAMES          : D={sig.daily_trend}, H1={sig.hourly_trend}, M15={sig.fifteen_min_trend}, M5={sig.five_min_trend}"
    )
    print(f"ALIGNMENT / STRUCT  : {sig.timeframe_alignment_score} / {sig.structure}")
    print(f"SECTOR              : {sig.sector} ({sig.sector_strength:+.2f})")
    print(f"RS VS NIFTY         : {sig.stock_vs_nifty_return:+.2f}%")
    print(f"SECTOR VS NIFTY     : {sig.sector_vs_nifty_return:+.2f}%")

    print(f"OPTION              : {sig.option_symbol} ({sig.option_type})")
    print(f"STRIKE / EXPIRY     : {sig.strike} / {sig.expiry} ({sig.days_to_expiry}d)")
    print(f"CURRENT VALUE       : {sig.option_ltp}")
    print(f"OPTION VOL / OI     : {sig.option_volume} / {sig.option_oi}")
    print(f"BID / ASK           : {sig.bid_price} / {sig.ask_price}")
    print(f"SPREAD %            : {sig.spread_pct}")
    print(f"QUALITY SCORE       : {sig.option_quality_score}")
    print(f"ENTRY (OPTION)      : {sig.suggested_entry_option}")
    print(f"STOP LOSS           : {sig.stop_loss_option}")
    print(f"TARGET              : {sig.target_option}")
    print(
        f"VWAP / PDH / PDL    : {sig.intraday_vwap} / {sig.prev_day_high} / {sig.prev_day_low}"
    )
    print(
        f"PDC / WH / WL       : {sig.prev_day_close} / {sig.weekly_high} / {sig.weekly_low}"
    )

    print(f"LOT SIZE            : {sig.lot_size}")
    print(f"CAPITAL REQUIRED    : {sig.capital_required}")
    print(f"RUPEE RISK          : {sig.rupee_risk}")
    print(f"RUPEE REWARD        : {sig.rupee_reward}")
    print(f"REWARD/RISK         : {sig.reward_risk_ratio}")

    print(f"WHEN TO ENTER       : {sig.entry_when_underlying}")
    print(f"EXIT RULE           : {sig.exit_rule}")
    print(f"RATIONALE           : {sig.rationale}")


def print_stock_signal(sig: StockSignal) -> None:
    print("=" * 100)
    print(f"SCANNED AT          : {sig.scanned_at}")
    print(f"QUOTE AT            : {sig.quote_time}")
    print(f"MARKET BIAS         : {sig.market_bias}")
    print(f"SETUP TYPE          : {sig.setup_type}")
    print(f"CONFIDENCE          : {sig.confidence}")

    print(f"SYMBOL              : {sig.symbol}")
    print(f"SIDE                : {sig.side}")
    print(f"SPOT PRICE          : {sig.spot_price}")
    print(f"TRIGGER             : {sig.trigger_price}")
    print(
        f"TRIGGER DISTANCE    : {sig.trigger_distance_abs} ({sig.trigger_distance_pct}%)"
    )
    print(f"TREND               : {sig.trend}")

    print(f"QUANTITY            : {sig.quantity}")
    print(f"CAPITAL REQUIRED    : {sig.capital_required}")
    print(f"RUPEE RISK          : {sig.rupee_risk}")
    print(f"RUPEE REWARD        : {sig.rupee_reward}")
    print(f"REWARD/RISK         : {sig.reward_risk_ratio}")

    print(f"ENTRY               : {sig.suggested_entry}")
    print(f"STOP LOSS           : {sig.stop_loss}")
    print(f"TARGET              : {sig.target}")
    print(f"EXIT RULE           : {sig.exit_rule}")
    print(f"RATIONALE           : {sig.rationale}")


def print_news_context(news_context: NewsContext) -> None:
    print("=" * 100)
    print(f"NEWS SCAN TIME     : {news_context.scanned_at}")
    print(f"NEWS ENABLED       : {'YES' if news_context.enabled else 'NO'}")
    print(f"NEWS BIAS          : {news_context.overall_bias}")
    print(f"NEWS SCORE         : {news_context.score}")
    print(f"NEWS RATIONALE     : {news_context.rationale}")
    print(
        f"KEY FACTORS        : {', '.join(news_context.key_factors) if news_context.key_factors else 'N/A'}"
    )
    if news_context.error:
        print(f"NEWS ERROR         : {news_context.error}")
    if news_context.headlines:
        print("TOP HEADLINES      :")
        for item in news_context.headlines[:5]:
            source = item.source or "Unknown"
            published_at = item.published_at or "Unknown time"
            print(
                f" - [{item.sentiment} {item.score:+.2f}] {item.title} | {source} | {published_at}"
            )
            if item.link:
                print(f"   {item.link}")
    print("=" * 100)


def print_nifty_result(result: Any, heading: str) -> None:
    print(f"\n{heading}\n")

    if result.primary_signal is not None:
        print_signal(result.primary_signal)
        return

    print("No clean directional setup right now. Showing CE/PE watchlist instead.\n")
    for sig in result.watchlist_signals:
        print_signal(sig)
        print()


def print_evening_market_report(
    market_regime: MarketRegime,
    snapshot_df: pd.DataFrame,
    sector_summary: List[Dict[str, Any]],
    monitor_lists: Dict[str, List[Any]],
    report_list_size: int,
) -> None:
    from src.utils import now_str

    print("=" * 110)
    print(f"EVENING MARKET WRAP : {now_str()}")
    print(f"OVERALL BIAS        : {market_regime.overall_bias}")
    print(f"REGIME SCORE        : {market_regime.regime_score}")
    print(
        f"NIFTY / BANKNIFTY   : {market_regime.nifty_trend} / {market_regime.banknifty_trend}"
    )
    print(f"MARKET BREADTH      : {market_regime.market_breadth}")
    print(
        f"STRONG SECTORS      : {', '.join(market_regime.strong_sectors) if market_regime.strong_sectors else 'N/A'}"
    )
    print(
        f"WEAK SECTORS        : {', '.join(market_regime.weak_sectors) if market_regime.weak_sectors else 'N/A'}"
    )
    print(f"RATIONALE           : {market_regime.rationale}")
    print("=" * 110)

    if not snapshot_df.empty:
        positive = int((snapshot_df["pct_change"] > 0).sum())
        negative = int((snapshot_df["pct_change"] < 0).sum())
        unchanged = int((snapshot_df["pct_change"] == 0).sum())
        print(
            f"Universe analyzed: {len(snapshot_df)} | Positive: {positive} | Negative: {negative} | Flat: {unchanged}"
        )

        top_gainers = snapshot_df.sort_values("pct_change", ascending=False).head(5)
        top_losers = snapshot_df.sort_values("pct_change", ascending=True).head(5)

        print("\nTop gainers:")
        for _, row in top_gainers.iterrows():
            print(
                f" - {row['symbol']}: {row['pct_change']:.2f}% | sector={row['sector']} | vol={int(row['volume'])}"
            )

        print("\nTop losers:")
        for _, row in top_losers.iterrows():
            print(
                f" - {row['symbol']}: {row['pct_change']:.2f}% | sector={row['sector']} | vol={int(row['volume'])}"
            )

    if sector_summary:
        print("\nSector summary:")
        for row in sector_summary[:8]:
            print(
                f" - {row['sector']}: score={row['sector_score']:+.2f}, "
                f"avg_move={row['avg_pct_change']:+.2f}%, breadth={row['breadth']:+.2f}"
            )

    pretty_names = {
        "bullish_continuation": "Bullish continuation watch",
        "bearish_continuation": "Bearish continuation watch",
        "near_breakout": "Near breakout watch",
        "near_breakdown": "Near breakdown watch",
        "reversal_watch": "Reversal watch",
    }

    for key, rows in monitor_lists.items():
        print(f"\n{pretty_names[key]}:")
        if not rows:
            print(" - None")
            continue
        for row in rows[:report_list_size]:
            trigger = (
                f"buy>{row.buy_trigger:.2f}"
                if "breakout" in key or "bullish" in key
                else f"sell<{row.sell_trigger:.2f}"
            )
            print(
                f" - {row.symbol}: {row.pct_change:+.2f}% | trend={row.trend} | rsi={row.rsi:.1f} | "
                f"vol_ratio={row.volume_ratio:.2f} | sector={row.sector} ({row.sector_strength:+.2f}) | "
                f"{trigger} | score={row.setup_score:.2f}"
            )
