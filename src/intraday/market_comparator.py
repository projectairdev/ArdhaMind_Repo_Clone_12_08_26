from __future__ import annotations

from typing import List, Optional
from src.models import MarketContext, OptionContext, MarketScore, MarketChange, EveningReport


def compare_market(
    evening_report: EveningReport,
    current_market_context: MarketContext,
    current_option_context: Optional[OptionContext] = None,
    current_market_score: Optional[MarketScore] = None,
    previous_option_context: Optional[OptionContext] = None,
) -> List[MarketChange]:
    changes = []

    # 1. Spot Price / Gap Change
    prev_spot = evening_report.market_summary.spot_price
    curr_spot = current_market_context.current_spot
    if prev_spot > 0:
        gap_pct = ((curr_spot - prev_spot) / prev_spot) * 100
        is_sig_gap = abs(gap_pct) >= 0.5
        msg = f"Spot price moved from {prev_spot:,.2f} to {curr_spot:,.2f} ({gap_pct:+.2f}%)."
        if is_sig_gap:
            msg += " Significant opening/intraday gap detected."
        changes.append(
            MarketChange(
                metric_name="SPOT_PRICE",
                previous_value=prev_spot,
                current_value=curr_spot,
                change_pct=gap_pct,
                is_significant=is_sig_gap,
                message=msg,
            )
        )

    # 2. India VIX Change
    prev_vix = evening_report.market_summary.vix_price
    curr_vix = current_market_context.india_vix if current_market_context.india_vix is not None else 0.0
    if prev_vix > 0 and curr_vix > 0:
        vix_pct = ((curr_vix - prev_vix) / prev_vix) * 100
        is_sig_vix = abs(curr_vix - prev_vix) >= 1.5 or abs(vix_pct) >= 10.0
        msg = f"India VIX shifted from {prev_vix:.2f} to {curr_vix:.2f} ({vix_pct:+.2f}%)."
        if is_sig_vix:
            msg += " High volatility shift detected."
        changes.append(
            MarketChange(
                metric_name="INDIA_VIX",
                previous_value=prev_vix,
                current_value=curr_vix,
                change_pct=vix_pct,
                is_significant=is_sig_vix,
                message=msg,
            )
        )

    # 3. Trend Direction Changes
    prev_trend = evening_report.market_summary.trend_direction
    curr_trend = current_market_context.trend_direction
    if prev_trend != curr_trend:
        changes.append(
            MarketChange(
                metric_name="TREND_DIRECTION",
                previous_value=prev_trend,
                current_value=curr_trend,
                is_significant=True,
                message=f"Trend reversed from {prev_trend} to {curr_trend}!",
            )
        )

    # 4. Market Regime Changes
    prev_regime = evening_report.market_summary.regime
    curr_regime = current_market_context.market_regime
    if prev_regime != curr_regime:
        changes.append(
            MarketChange(
                metric_name="MARKET_REGIME",
                previous_value=prev_regime,
                current_value=curr_regime,
                is_significant=True,
                message=f"Market regime shifted from {prev_regime} to {curr_regime}.",
            )
        )

    # 5. S/R Violations
    support_levels = evening_report.tomorrow_outlook.key_support_levels
    resistance_levels = evening_report.tomorrow_outlook.key_resistance_levels

    for sup in support_levels:
        if curr_spot < sup:
            changes.append(
                MarketChange(
                    metric_name="SUPPORT_BREACH",
                    previous_value=sup,
                    current_value=curr_spot,
                    is_significant=True,
                    message=f"Key support level {sup:,.2f} breached downward!",
                )
            )

    for res in resistance_levels:
        if curr_spot > res:
            changes.append(
                MarketChange(
                    metric_name="RESISTANCE_BREACH",
                    previous_value=res,
                    current_value=curr_spot,
                    is_significant=True,
                    message=f"Key resistance level {res:,.2f} breached upward!",
                )
            )

    # 6. PCR Shifts
    if current_option_context:
        curr_pcr = current_option_context.pcr
        prev_pcr = previous_option_context.pcr if previous_option_context else 1.0
        pcr_diff = curr_pcr - prev_pcr
        is_sig_pcr = abs(pcr_diff) >= 0.15
        msg = f"PCR shifted from {prev_pcr:.2f} to {curr_pcr:.2f} (diff: {pcr_diff:+.2f})."
        if is_sig_pcr:
            msg += " Significant sentiment shift in options chain."
        changes.append(
            MarketChange(
                metric_name="PCR",
                previous_value=prev_pcr,
                current_value=curr_pcr,
                change_pct=pcr_diff,
                is_significant=is_sig_pcr,
                message=msg,
            )
        )

    # 7. IV Shifts
    if current_option_context:
        curr_iv = current_option_context.atm_iv
        prev_iv = previous_option_context.atm_iv if previous_option_context else 15.0
        iv_diff = curr_iv - prev_iv
        is_sig_iv = abs(iv_diff) >= 2.0
        msg = f"ATM IV shifted from {prev_iv:.1f}% to {curr_iv:.1f}% (diff: {iv_diff:+.1f}%)."
        if is_sig_iv:
            msg += " Volatility expansion/contraction detected in options chain."
        changes.append(
            MarketChange(
                metric_name="ATM_IV",
                previous_value=prev_iv,
                current_value=curr_iv,
                is_significant=is_sig_iv,
                message=msg,
            )
        )

    # 8. Liquidity Shifts
    if current_option_context and previous_option_context:
        curr_spread = current_option_context.liquidity_metrics.get("avg_spread_pct", 0.0)
        prev_spread = previous_option_context.liquidity_metrics.get("avg_spread_pct", 0.0)
        if prev_spread > 0:
            spread_pct_change = ((curr_spread - prev_spread) / prev_spread) * 100
            is_sig_spread = spread_pct_change >= 50.0  # Spread widened by 50% or more
            msg = f"Average bid-ask spread went from {prev_spread:.3f}% to {curr_spread:.3f}%."
            if is_sig_spread:
                msg += " Liquidity risk! Option spreads have widened significantly."
            changes.append(
                MarketChange(
                    metric_name="LIQUIDITY_SPREAD",
                    previous_value=prev_spread,
                    current_value=curr_spread,
                    change_pct=spread_pct_change,
                    is_significant=is_sig_spread,
                    message=msg,
                )
            )

    return changes
