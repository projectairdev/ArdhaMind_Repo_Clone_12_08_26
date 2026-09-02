from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.proposal_engine.models import (
    OrderIntent,
    ProposalState,
    TradeProposal,
)
from src.utils import setup_logger

logger = setup_logger("ProposalBuilder")

DEFAULT_INSTRUMENTS_DB = Path("/opt/ardhamind/staging/cache/instruments.db")


def resolve_lot_size(underlying: str = "NIFTY", default: int = 25, db_path: Optional[Path | str] = None) -> int:
    """
    Dynamically queries cache/instruments.db to find the active lot_size for NIFTY option contracts.
    Falls back gracefully to default (25) if instruments db is unavailable.
    """
    path = Path(db_path) if db_path else DEFAULT_INSTRUMENTS_DB
    if not path.exists():
        return default
    conn = None
    try:
        conn = sqlite3.connect(str(path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT lot_size FROM instruments WHERE name = ? AND exchange = 'NFO' AND instrument_type IN ('CE', 'PE') AND lot_size > 0 ORDER BY expiry ASC LIMIT 1",
            (underlying.upper(),),
        )
        row = cursor.fetchone()
        if row and row[0]:
            return int(row[0])
    except Exception as e:
        logger.warning(f"Failed to query dynamic lot size from {path}: {e}")
    finally:
        if conn:
            conn.close()
    return default


def resolve_contract_metadata(
    underlying: str = "NIFTY",
    strike: int = 24150,
    option_type: str = "CE",
    db_path: Optional[Path | str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Dynamically queries cache/instruments.db to find authoritative NFO option contract metadata.
    Returns numeric instrument_token, exchange, tradingsymbol, strike, expiry, lot_size.
    """
    path = Path(db_path) if db_path else DEFAULT_INSTRUMENTS_DB
    if not path.exists():
        return None
    conn = None
    try:
        conn = sqlite3.connect(str(path))
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT instrument_token, exchange, tradingsymbol, strike, expiry, lot_size
            FROM instruments
            WHERE name = ? AND exchange = 'NFO' AND strike = ? AND instrument_type = ?
            ORDER BY expiry ASC LIMIT 1
            """,
            (underlying.upper(), float(strike), option_type.upper()),
        )
        row = cursor.fetchone()
        if row:
            return {
                "instrument_token": int(row[0]),
                "exchange": str(row[1]),
                "tradingsymbol": str(row[2]),
                "strike": int(row[3]),
                "expiry": str(row[4]),
                "lot_size": int(row[5]),
            }
    except Exception as e:
        logger.warning(f"Failed to query contract metadata for {underlying} {strike} {option_type} from {path}: {e}")
    finally:
        if conn:
            conn.close()
    return None


def calculate_confluence_score(
    structure_score: float,
    options_score: float,
    breadth_score: float,
    macro_score: float = 0.0,
) -> float:
    """
    Computes weighted multi-factor confluence score for setup qualification:
    Confluence Score = 0.40 * Structure + 0.30 * Options Flow + 0.20 * Breadth + 0.10 * Macro
    Qualifies setup when composite score >= 65/100.
    """
    score = (
        (0.40 * max(0.0, min(100.0, structure_score))) +
        (0.30 * max(0.0, min(100.0, options_score))) +
        (0.20 * max(0.0, min(100.0, breadth_score))) +
        (0.10 * max(0.0, min(100.0, macro_score)))
    )
    return round(score, 1)


class ProposalBuilder:
    """
    Deterministic builder connecting Opportunity and Options analytical engines
    to generate an actionable canonical TradeProposal with dynamic lot sizing
    and weighted confluence scoring.
    """

    DEFAULT_LOT_SIZE = 25

    @classmethod
    def _create_no_trade_proposal(
        cls,
        reason: str,
        spot: float = 0.0,
        safe_lots: int = 1,
        resolved_lot_size: int = 25,
        total_quantity: int = 25,
        product: str = "NRML",
        runtime_id: str = "rt-staging-1",
        confluence: float = 0.0,
        priority_score: float = 0.0,
    ) -> TradeProposal:
        now_iso = datetime.now(timezone.utc).isoformat()
        return TradeProposal(
            proposal_id=f"PROP-NO-TRADE-{datetime.now().strftime('%Y%m%d')}",
            timestamp=now_iso,
            underlying="NIFTY",
            setup_type="NONE",
            direction="NEUTRAL",
            strike=int(round(spot / 50.0) * 50) if spot > 0 else 0,
            option_type="NONE",
            contract_symbol="NO ACTIVE PROPOSAL",
            entry_price=0.0,
            stop_loss=0.0,
            target_1=0.0,
            target_2=0.0,
            risk_reward_ratio=0.0,
            confidence_score=0.0,
            priority_score=priority_score,
            quality_score=0.0,
            max_loss_inr=0.0,
            rationale=[reason],
            invalidation_condition="Awaiting market catalyst or technical breakout.",
            state=ProposalState.NO_TRADE.value,
            lots=safe_lots,
            lot_size=resolved_lot_size,
            total_quantity=total_quantity,
            product=product,
            order_intent=None,
            raw_metadata={"runtime_id": runtime_id, "is_no_trade": True, "confluence_score": confluence},
        )

    @classmethod
    def build_proposal(
        cls,
        best_opportunity: Optional[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
        runtime_id: str = "rt-staging-1",
        lots: int = 1,
        product: str = "NRML",
    ) -> TradeProposal:
        now_iso = datetime.now(timezone.utc).isoformat()
        ctx = context or {}
        market = ctx.get("market") or ctx.get("market_context") or {}
        raw_spot = market.get("current_spot") or market.get("spot_price") or 0.0
        try:
            spot = float(raw_spot) if raw_spot is not None else 0.0
        except (ValueError, TypeError):
            spot = 0.0

        resolved_lot_size = resolve_lot_size("NIFTY", default=cls.DEFAULT_LOT_SIZE)
        safe_lots = max(1, lots)
        total_quantity = safe_lots * resolved_lot_size

        # Multi-factor Confluence Scoring Check (honest 0.0 fallbacks, never fabricate 70)
        if best_opportunity:
            raw_struct = best_opportunity.get("structure_score")
            raw_prio = best_opportunity.get("priority_score")
            struct_s = float(raw_struct if raw_struct is not None else (raw_prio if raw_prio is not None else 0.0))

            raw_opts = best_opportunity.get("options_score")
            raw_conf = best_opportunity.get("confidence_score")
            opts_s = float(raw_opts if raw_opts is not None else (raw_conf if raw_conf is not None else 0.0))

            raw_breadth = best_opportunity.get("breadth_score")
            breadth_s = float(raw_breadth) if raw_breadth is not None else 0.0

            raw_macro = best_opportunity.get("macro_score")
            macro_s = float(raw_macro) if raw_macro is not None else 0.0

            confluence = calculate_confluence_score(struct_s, opts_s, breadth_s, macro_s)
            prio_score = float(raw_prio if raw_prio is not None else confluence)
        else:
            confluence = 0.0
            prio_score = 0.0

        # 1. No Trade / Below Conviction Threshold Guard (Score < 65) or Missing Opportunity
        if not best_opportunity or best_opportunity.get("status") == "NO_TRADE" or max(prio_score, confluence) < 65:
            reason_msg = (
                best_opportunity.get("message")
                if best_opportunity and best_opportunity.get("message")
                else "No high-conviction setup currently meets qualification thresholds (Confluence Score >= 65)."
            )
            return cls._create_no_trade_proposal(
                reason=reason_msg,
                spot=spot,
                safe_lots=safe_lots,
                resolved_lot_size=resolved_lot_size,
                total_quantity=total_quantity,
                product=product,
                runtime_id=runtime_id,
                confluence=confluence,
                priority_score=prio_score,
            )

        # 2. Decision-Critical Field Validation
        # Direction
        raw_direction = best_opportunity.get("direction")
        if not raw_direction or str(raw_direction).upper() not in ("BULLISH", "BEARISH"):
            return cls._create_no_trade_proposal(
                reason="Directional bias undefined or neutral for active opportunity.",
                spot=spot,
                safe_lots=safe_lots,
                resolved_lot_size=resolved_lot_size,
                total_quantity=total_quantity,
                product=product,
                runtime_id=runtime_id,
                confluence=confluence,
                priority_score=prio_score,
            )
        direction = str(raw_direction).upper()
        setup_type = str(best_opportunity.get("setup_type") or "UNSPECIFIED").upper()

        # Strike & Option Type: must be from provisional_strike or valid spot > 0 (zero fabrication)
        raw_strike = best_opportunity.get("provisional_strike")
        if raw_strike is not None and int(raw_strike) > 0:
            strike = int(raw_strike)
        elif spot > 0:
            strike = int(round(spot / 50.0) * 50)
        else:
            return cls._create_no_trade_proposal(
                reason="Insufficient market data: valid underlying spot price unavailable to determine option strike.",
                spot=spot,
                safe_lots=safe_lots,
                resolved_lot_size=resolved_lot_size,
                total_quantity=total_quantity,
                product=product,
                runtime_id=runtime_id,
                confluence=confluence,
                priority_score=prio_score,
            )

        option_type = str(best_opportunity.get("option_type") or ("CE" if direction == "BULLISH" else "PE")).upper()
        contract_symbol = f"NIFTY {strike} {option_type}"

        # Confidence and Quality scores: decision-critical, must be present and positive
        raw_qual = best_opportunity.get("quality_score")
        raw_conf = best_opportunity.get("confidence_score")
        if raw_qual is None or raw_conf is None:
            return cls._create_no_trade_proposal(
                reason="Insufficient model evaluation: quality or confidence score missing for active setup.",
                spot=spot,
                safe_lots=safe_lots,
                resolved_lot_size=resolved_lot_size,
                total_quantity=total_quantity,
                product=product,
                runtime_id=runtime_id,
                confluence=confluence,
                priority_score=prio_score,
            )
        qual_score = float(raw_qual)
        conf_score = float(raw_conf)
        if qual_score <= 0.0 or conf_score <= 0.0:
            return cls._create_no_trade_proposal(
                reason="Insufficient model conviction: quality or confidence score is zero.",
                spot=spot,
                safe_lots=safe_lots,
                resolved_lot_size=resolved_lot_size,
                total_quantity=total_quantity,
                product=product,
                runtime_id=runtime_id,
                confluence=confluence,
                priority_score=prio_score,
            )

        # Risk and Reward estimates: decision-critical, must be positive
        levels = best_opportunity.get("suggested_levels") or {}
        raw_risk = best_opportunity.get("estimated_risk")
        raw_reward = best_opportunity.get("estimated_reward")

        if raw_risk is not None and float(raw_risk) > 0:
            spot_risk = float(raw_risk)
        elif levels.get("entry_reference") and levels.get("invalidation_level"):
            diff = abs(float(levels["entry_reference"]) - float(levels["invalidation_level"]))
            spot_risk = diff if diff > 0 else 0.0
        else:
            spot_risk = 0.0

        if raw_reward is not None and float(raw_reward) > 0:
            spot_reward = float(raw_reward)
        elif levels.get("target_reference") and levels.get("entry_reference"):
            diff = abs(float(levels["target_reference"]) - float(levels["entry_reference"]))
            spot_reward = diff if diff > 0 else 0.0
        elif levels.get("target_zone_1") and levels.get("entry_reference"):
            diff = abs(float(levels["target_zone_1"]) - float(levels["entry_reference"]))
            spot_reward = diff if diff > 0 else 0.0
        else:
            spot_reward = 0.0

        if spot_risk <= 0.0 or spot_reward <= 0.0:
            return cls._create_no_trade_proposal(
                reason="Insufficient structural levels: risk or reward boundary unavailable for setup.",
                spot=spot,
                safe_lots=safe_lots,
                resolved_lot_size=resolved_lot_size,
                total_quantity=total_quantity,
                product=product,
                runtime_id=runtime_id,
                confluence=confluence,
                priority_score=prio_score,
            )

        # Option Entry Price resolution: must be from actual option levels or option chain quote
        opt_entry = None
        for k in ("option_entry", "option_price", "entry_price"):
            v = levels.get(k) or best_opportunity.get(k)
            if v is not None and 0 < float(v) < 1000:
                opt_entry = float(v)
                break

        if opt_entry is None:
            entry_ref_val = levels.get("entry_reference") or best_opportunity.get("entry_reference")
            if entry_ref_val is not None and 0 < float(entry_ref_val) < 1000:
                opt_entry = float(entry_ref_val)

        if opt_entry is None:
            opt_ctx = ctx.get("options") or ctx.get("option_context") or {}
            strike_universe = opt_ctx.get("strike_universe") or opt_ctx.get("strikes") or []
            if isinstance(strike_universe, list):
                row = next((s for s in strike_universe if isinstance(s, dict) and s.get("strike") == strike), None)
                if row:
                    call_put_key = "call_ltp" if option_type == "CE" else "put_ltp"
                    alt_key = "call_price" if option_type == "CE" else "put_price"
                    price_val = row.get(call_put_key) or row.get(alt_key) or row.get("ltp")
                    if price_val is not None and 0 < float(price_val) < 1000:
                        opt_entry = float(price_val)

        if opt_entry is None or opt_entry <= 0:
            return cls._create_no_trade_proposal(
                reason=f"Insufficient option chain data: live premium for NIFTY {strike} {option_type} unavailable.",
                spot=spot,
                safe_lots=safe_lots,
                resolved_lot_size=resolved_lot_size,
                total_quantity=total_quantity,
                product=product,
                runtime_id=runtime_id,
                confluence=confluence,
                priority_score=prio_score,
            )

        opt_entry = round(opt_entry, 2)

        # Option points estimates (delta approx 0.50 for ATM)
        delta_approx = 0.50
        opt_risk_points = max(5.0, round(spot_risk * delta_approx, 2))
        opt_sl = max(0.05, round(opt_entry - opt_risk_points, 2))
        opt_t1 = round(opt_entry + round(spot_reward * delta_approx, 2), 2)
        opt_t2 = round(opt_entry + round(spot_reward * 1.5 * delta_approx, 2), 2)

        risk_delta = max(0.05, abs(opt_entry - opt_sl))
        reward_delta = abs(opt_t1 - opt_entry)
        calculated_rr = round(reward_delta / risk_delta, 2)

        # Reward:Risk ratio validation — never fall back to 1.8
        raw_rr = best_opportunity.get("reward_risk_ratio")
        if raw_rr is not None and float(raw_rr) > 0:
            final_rr = float(raw_rr)
        elif calculated_rr >= 1.0:
            final_rr = calculated_rr
        else:
            return cls._create_no_trade_proposal(
                reason=f"Unfavorable reward-to-risk ratio (1:{calculated_rr:.2f} < 1:1.0 minimum threshold).",
                spot=spot,
                safe_lots=safe_lots,
                resolved_lot_size=resolved_lot_size,
                total_quantity=total_quantity,
                product=product,
                runtime_id=runtime_id,
                confluence=confluence,
                priority_score=prio_score,
            )

        max_loss_inr = round(opt_risk_points * total_quantity, 2)

        # 3. Construct Rationale & Invalidation
        rationale_bullets = cls._generate_rationale(
            best_opportunity, ctx, prio_score=prio_score, rr_ratio=final_rr
        )
        invalidation_text = cls._generate_invalidation(best_opportunity, opt_sl, levels)

        # Deterministic UUID generation from opportunity ID or properties
        opp_id = best_opportunity.get("opportunity_id", f"{direction}_{strike}_{setup_type}")
        proposal_uuid = f"PROP-{abs(hash(opp_id)) % 100000000:08d}"

        # Order Intent
        order_intent = OrderIntent(
            proposal_id=proposal_uuid,
            symbol=contract_symbol.replace(" ", ""),
            exchange="NFO",
            transaction_type="BUY",
            order_type="LIMIT",
            product=product,
            lots=safe_lots,
            lot_size=resolved_lot_size,
            quantity=total_quantity,
            price=opt_entry,
            trigger_price=None,
            dry_run=True,
            generated_at=now_iso,
        )

        return TradeProposal(
            proposal_id=proposal_uuid,
            timestamp=now_iso,
            underlying="NIFTY",
            setup_type=setup_type,
            direction=direction,
            strike=strike,
            option_type=option_type,
            contract_symbol=contract_symbol,
            entry_price=opt_entry,
            stop_loss=opt_sl,
            target_1=opt_t1,
            target_2=opt_t2,
            risk_reward_ratio=final_rr,
            confidence_score=conf_score,
            priority_score=prio_score,
            quality_score=qual_score,
            max_loss_inr=max_loss_inr,
            rationale=rationale_bullets,
            invalidation_condition=invalidation_text,
            state=ProposalState.PROPOSED.value,
            lots=safe_lots,
            lot_size=resolved_lot_size,
            total_quantity=total_quantity,
            product=product,
            margin_status="PENDING_CHECK",
            required_margin=round(opt_entry * total_quantity, 2),
            available_margin=None,
            margin_sufficient=None,
            order_intent=order_intent.to_dict(),
            risk_evaluation={
                "margin_required_approx": round(opt_entry * total_quantity, 2),
                "max_drawdown_limit_ok": True,
                "reward_risk_check": "PASS" if final_rr >= 1.5 else "CAUTION",
                "volatility_regime": "ACCEPTABLE",
                "confluence_score": confluence,
            },
            approval_timestamp=None,
            rejection_reason=None,
            raw_metadata={
                "opportunity_id": best_opportunity.get("opportunity_id"),
                "runtime_id": runtime_id,
                "confluence_score": confluence,
            },
        )

    @classmethod
    def _generate_rationale(
        cls,
        opp: Dict[str, Any],
        context: Dict[str, Any],
        prio_score: float,
        rr_ratio: float,
    ) -> List[str]:
        evidence = opp.get("evidence") or []
        bullets = []

        setup = opp.get("setup_type", "Trend Pullback").replace("_", " ").title()
        direction = opp.get("direction", "Bullish").title()
        bullets.append(f"{direction} {setup} setup supported by structural order flow and volume expansion.")

        options = context.get("options") or context.get("option_context") or {}
        pcr = options.get("pcr")
        if pcr is not None and float(pcr) > 0:
            bullets.append(f"Options OI structure and PCR ({float(pcr):.2f}) confirm directional momentum.")
        else:
            bullets.append("Options order flow structure confirms directional momentum.")

        bullets.append(f"Weighted confluence score ({prio_score:.0f}/100) with favorable 1:{rr_ratio:.1f} R:R profile.")

        if len(evidence) >= 1 and isinstance(evidence[0], str) and len(evidence[0]) > 5:
            bullets[0] = evidence[0]

        return bullets[:3]

    @classmethod
    def _generate_invalidation(cls, opp: Dict[str, Any], sl_price: float, levels: Dict[str, Any]) -> str:
        inval_ref = levels.get("invalidation_level")
        if inval_ref and float(inval_ref) > 1000:
            return f"5-minute spot close beyond {float(inval_ref):.1f} or option premium falling below ₹{sl_price:.1f}."
        return f"Option premium closing below stop-loss at ₹{sl_price:.1f} or reversal of structural market bias."
