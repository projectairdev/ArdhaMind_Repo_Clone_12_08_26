from __future__ import annotations

import datetime
from typing import Optional
import pandas as pd

from src.models.option_context import OptionContext
from src.data_engine.market_context import fetch_nifty_spot
from src.data_engine.instruments import InstrumentManager
from src.options_engine.chain_builder import build_option_chain
from src.options_engine.oi_analysis import analyze_oi
from src.options_engine.max_pain import calculate_max_pain
from src.options_engine.liquidity import analyze_liquidity
from src.options_engine.iv import analyze_iv
from src.options_engine.strike_ranker import rank_strikes
from src.utils import setup_logger, now_str

logger = setup_logger("OptionIntelligencePipeline")


class OptionIntelligencePipeline:
    """
    Assembles NIFTY options chain and coordinates the execution of options analysis
    engines to produce a single source of truth: OptionContext.
    """

    def __init__(self) -> None:
        pass

    def run(
        self,
        kite,
        instruments_df: pd.DataFrame,
        spot_price: Optional[float] = None,
        expiry_date: Optional[datetime.date] = None,
    ) -> OptionContext:
        logger.info("Initializing NIFTY Option Intelligence Pipeline...")

        # 1. Resolve or fetch Underlying Spot Price
        if spot_price is None:
            try:
                spot_price = fetch_nifty_spot(kite)
            except Exception as exc:
                raise RuntimeError("NIFTY spot is unavailable; option intelligence is blocked.") from exc

        # 2. Expiry Resolution
        expiries = InstrumentManager.get_option_expiries(instruments_df, "NIFTY")
        expiries_str = [e.strftime("%Y-%m-%d") for e in expiries] if expiries else []

        weekly_expiry = InstrumentManager.resolve_weekly_expiry(instruments_df, "NIFTY")
        next_weekly_expiry = InstrumentManager.resolve_next_weekly_expiry(instruments_df, "NIFTY")
        monthly_expiry = InstrumentManager.resolve_monthly_expiry(instruments_df, "NIFTY")
        next_monthly_expiry = InstrumentManager.resolve_next_monthly_expiry(instruments_df, "NIFTY")
        far_expiry_val = expiries[-1] if expiries else monthly_expiry

        if expiry_date is None:
            expiry_date = weekly_expiry or InstrumentManager.resolve_nearest_expiry(instruments_df, "NIFTY")

        if expiry_date is None:
            raise RuntimeError("No active option expiries resolved for NIFTY.")

        # Pool target expiries
        target_expiries = sorted(list(filter(None, set([
            weekly_expiry, 
            next_weekly_expiry, 
            monthly_expiry, 
            next_monthly_expiry, 
            far_expiry_val
        ]))))

        # 3. Resolve Strike step and ATM strike
        step = InstrumentManager.resolve_strike_step(instruments_df, "NIFTY")
        if step is None:
            step = 50.0

        atm_strike = InstrumentManager.resolve_atm_strike(instruments_df, "NIFTY", spot_price)
        if atm_strike is None:
            atm_strike = round(spot_price / step) * step

        # 4. Fetch & Normalize Option Chain (Task 2)
        chain = build_option_chain(
            kite=kite,
            instruments_df=instruments_df,
            symbol="NIFTY",
            expiry=target_expiries,
            spot_price=spot_price,
        )

        # 5. Calculate OI Metrics (Task 3)
        oi_res = analyze_oi(chain)

        # 6. Calculate Max Pain (Task 4)
        max_pain_res = calculate_max_pain(chain)

        # 7. Calculate Liquidity Metrics (Task 5)
        liq_res = analyze_liquidity(chain, atm_strike, step)

        # 8. Calculate Implied Volatility (Task 6)
        iv_res = analyze_iv(chain, spot_price, atm_strike, expiry_date)

        # 9. Rank Strikes (Task 7)
        ranked_strikes = rank_strikes(chain, liq_res, iv_res, atm_strike)

        # 10. Assemble OptionContext (Task 1 & Task 10)
        # Market Option Bias: Based primarily on PCR OI
        if oi_res.pcr_oi > 1.15:
            market_option_bias = "BULLISH"
        elif oi_res.pcr_oi < 0.85:
            market_option_bias = "BEARISH"
        else:
            market_option_bias = "NEUTRAL"

        # Days to expiry
        dte = (expiry_date - datetime.date.today()).days

        # Top candidates to List[Dict] for the consumers
        top_candidates = []
        for r_strk in ranked_strikes[:30]:  # Fetch up to 30 ranked strikes to cover different expiries
            top_candidates.append(
                {
                    "tradingsymbol": r_strk.tradingsymbol,
                    "strike": float(r_strk.strike),
                    "instrument_type": r_strk.instrument_type,
                    "distance_from_atm": float(r_strk.distance_from_atm),
                    "oi": int(r_strk.oi),
                    "volume": int(r_strk.volume),
                    "spread_pct": float(r_strk.spread_pct),
                    "iv": float(r_strk.iv),
                    "tradability_score": float(r_strk.tradability_score),
                    "ranking_score": float(r_strk.ranking_score),
                    "rank": int(r_strk.rank),
                    "expiry": r_strk.expiry,
                }
            )

        weekly_expiry_str = weekly_expiry.strftime("%Y-%m-%d") if weekly_expiry else ""
        monthly_expiry_str = monthly_expiry.strftime("%Y-%m-%d") if monthly_expiry else ""
        next_weekly_expiry_str = next_weekly_expiry.strftime("%Y-%m-%d") if next_weekly_expiry else ""
        next_monthly_expiry_str = next_monthly_expiry.strftime("%Y-%m-%d") if next_monthly_expiry else ""
        far_expiry_str = far_expiry_val.strftime("%Y-%m-%d") if far_expiry_val else ""

        option_chain_summary = {
            "total_calls_oi": int(sum(c.oi for c in chain if c.instrument_type == "CE")),
            "total_puts_oi": int(sum(c.oi for c in chain if c.instrument_type == "PE")),
            "total_calls_volume": int(sum(c.volume for c in chain if c.instrument_type == "CE")),
            "total_puts_volume": int(sum(c.volume for c in chain if c.instrument_type == "PE")),
            "chain_length": len(chain),
            "oi_shift_description": oi_res.oi_shift_description,
        }

        liquidity_metrics_dict = {
            "average_spread_pct": float(liq_res.average_spread_pct),
            "overall_liquidity_score": float(liq_res.overall_liquidity_score),
            "total_volume": int(liq_res.total_volume),
            "total_oi": int(liq_res.total_oi),
            "liquid_contracts_count": int(liq_res.liquid_contracts_count),
            "unsuitable_contracts_count": int(liq_res.unsuitable_contracts_count),
        }

        opt_ctx = OptionContext(
            underlying_spot=float(spot_price),
            atm_strike=float(atm_strike),
            strike_step=float(step),
            current_weekly_expiry=weekly_expiry_str,
            current_monthly_expiry=monthly_expiry_str,
            next_weekly_expiry=next_weekly_expiry_str,
            next_monthly_expiry=next_monthly_expiry_str,
            far_expiry=far_expiry_str,
            all_expiries=expiries_str,
            time_to_expiry=float(dte),
            atm_iv=float(iv_res.atm_iv),
            expected_move=float(iv_res.expected_move),
            pcr=float(oi_res.pcr_oi),
            max_pain=float(max_pain_res.max_pain_strike),
            highest_call_oi=float(oi_res.highest_ce_oi_value),
            highest_put_oi=float(oi_res.highest_pe_oi_value),
            highest_call_oi_change=float(oi_res.highest_ce_oi_change_value),
            highest_put_oi_change=float(oi_res.highest_pe_oi_change_value),
            support_strikes=[float(s) for s in oi_res.oi_concentration_pe],
            resistance_strikes=[float(s) for s in oi_res.oi_concentration_ce],
            liquidity_metrics=liquidity_metrics_dict,
            option_chain_summary=option_chain_summary,
            top_candidate_strikes=top_candidates,
            market_option_bias=market_option_bias,
            timestamp=now_str(),
            schema_version="1.0",
            pipeline_version="1.0",
        )

        logger.info(
            f"NIFTY OptionContext assembled successfully: "
            f"Regime Spot={opt_ctx.underlying_spot}, ATM={opt_ctx.atm_strike}, "
            f"PCR={opt_ctx.pcr}, MaxPain={opt_ctx.max_pain}, "
            f"Bias={opt_ctx.market_option_bias}"
        )
        return opt_ctx
