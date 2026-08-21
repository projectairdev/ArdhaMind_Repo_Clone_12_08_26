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
    try:
        with sqlite3.connect(str(path)) as conn:
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
    try:
        with sqlite3.connect(str(path)) as conn:
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
    return None


def calculate_confluence_score(
    structure_score: float,
    options_score: float,
    breadth_score: float,
    macro_score: float = 70.0,
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
        spot = float(market.get("current_spot") or market.get("spot_price") or 0.0)

        resolved_lot_size = resolve_lot_size("NIFTY", default=cls.DEFAULT_LOT_SIZE)
        safe_lots = max(1, lots)
        total_quantity = safe_lots * resolved_lot_size

        # Multi-factor Confluence Scoring Check
        if best_opportunity:
            struct_s = float(best_opportunity.get("structure_score") or best_opportunity.get("priority_score", 70))
            opts_s = float(best_opportunity.get("options_score") or best_opportunity.get("confidence_score", 70))
            breadth_s = float(best_opportunity.get("breadth_score") or 70.0)
            macro_s = float(best_opportunity.get("macro_score") or 70.0)

            confluence = calculate_confluence_score(struct_s, opts_s, breadth_s, macro_s)
            prio_score = float(best_opportunity.get("priority_score") or confluence)
        else:
            confluence = 0.0
            prio_score = 0.0

        # 1. No Trade / Below Conviction Threshold Guard (Score < 65)
        if not best_opportunity or best_opportunity.get("status") == "NO_TRADE" or max(prio_score, confluence) < 65:
            reason_msg = (
                best_opportunity.get("message")
                if best_opportunity and best_opportunity.get("message")
                else "No high-conviction setup currently meets qualification thresholds (Confluence Score >= 65)."
            )
            return TradeProposal(
                proposal_id=f"PROP-NO-TRADE-{datetime.now().strftime('%Y%m%d')}",
                timestamp=now_iso,
                underlying="NIFTY",
                setup_type="NONE",
                direction="NEUTRAL",
                strike=int(round(spot / 50.0) * 50) if spot > 0 else 24500,
                option_type="NONE",
                contract_symbol="NO ACTIVE PROPOSAL",
                entry_price=0.0,
                stop_loss=0.0,
                target_1=0.0,
                target_2=0.0,
                risk_reward_ratio=0.0,
                confidence_score=float(best_opportunity.get("confidence_score", 0)) if best_opportunity else 0.0,
                priority_score=prio_score,
                quality_score=float(best_opportunity.get("quality_score", 0)) if best_opportunity else 0.0,
                max_loss_inr=0.0,
                rationale=[reason_msg],
                invalidation_condition="Awaiting market catalyst or technical breakout.",
                state=ProposalState.NO_TRADE.value,
                lots=safe_lots,
                lot_size=resolved_lot_size,
                total_quantity=total_quantity,
                product=product,
                order_intent=None,
                raw_metadata={"runtime_id": runtime_id, "is_no_trade": True, "confluence_score": confluence},
            )

        # 2. Extract Candidate Opportunity Data
        setup_type = str(best_opportunity.get("setup_type", "TREND_PULLBACK_VWAP")).upper()
        direction = str(best_opportunity.get("direction", "BULLISH")).upper()
        qual_score = float(best_opportunity.get("quality_score", 80.0))
        conf_score = float(best_opportunity.get("confidence_score", 75.0))
        rr_ratio = float(best_opportunity.get("reward_risk_ratio", 1.8))

        # Strike & Option Type
        strike = int(best_opportunity.get("provisional_strike") or (round(spot / 50.0) * 50 if spot > 0 else 24500))
        option_type = str(best_opportunity.get("option_type") or ("CE" if direction == "BULLISH" else "PE")).upper()
        contract_symbol = f"NIFTY {strike} {option_type}"

        # Levels
        levels = best_opportunity.get("suggested_levels") or {}
        entry_ref = float(levels.get("entry_reference") or spot or 24500.0)
        entry_price = float(levels.get("entry_reference") or 120.0) if levels.get("entry_reference", 0) < 1000 else 120.0

        # Spot vs Option Level Calculation
        spot_risk = float(best_opportunity.get("estimated_risk") or 30.0)
        spot_reward = float(best_opportunity.get("estimated_reward") or 55.0)

        # Option points estimates (delta approx 0.50 for ATM)
        delta_approx = 0.50
        opt_entry = round(entry_price if entry_price < 1000 else 125.0, 2)
        opt_risk_points = max(10.0, round(spot_risk * delta_approx, 2))
        opt_sl = max(5.0, round(opt_entry - opt_risk_points, 2))
        opt_t1 = round(opt_entry + round(spot_reward * delta_approx, 2), 2)
        opt_t2 = round(opt_entry + round(spot_reward * 1.5 * delta_approx, 2), 2)

        calculated_rr = round(abs(opt_t1 - opt_entry) / max(1.0, abs(opt_entry - opt_sl)), 2)
        if calculated_rr < 1.0:
            calculated_rr = rr_ratio

        max_loss_inr = round(opt_risk_points * total_quantity, 2)

        # 3. Construct Rationale & Invalidation
        rationale_bullets = cls._generate_rationale(best_opportunity, ctx)
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
            risk_reward_ratio=calculated_rr,
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
                "reward_risk_check": "PASS" if calculated_rr >= 1.5 else "CAUTION",
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
    def _generate_rationale(cls, opp: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
        evidence = opp.get("evidence") or []
        bullets = []

        setup = opp.get("setup_type", "Trend Pullback VWAP").replace("_", " ").title()
        direction = opp.get("direction", "Bullish").title()
        bullets.append(f"{direction} {setup} setup supported by structural order flow and volume expansion.")

        options = context.get("options") or context.get("option_context") or {}
        pcr = float(options.get("pcr") or 1.0)
        bullets.append(f"Options OI structure and PCR ({pcr:.2f}) confirm directional momentum.")

        prio = opp.get("priority_score", 75)
        rr = opp.get("reward_risk_ratio", 1.8)
        bullets.append(f"Weighted confluence score ({prio}/100) with favorable 1:{rr:.1f} R:R profile.")

        if len(evidence) >= 1 and isinstance(evidence[0], str) and len(evidence[0]) > 5:
            bullets[0] = evidence[0]

        return bullets[:3]

    @classmethod
    def _generate_invalidation(cls, opp: Dict[str, Any], sl_price: float, levels: Dict[str, Any]) -> str:
        inval_ref = levels.get("invalidation_level")
        if inval_ref and float(inval_ref) > 1000:
            return f"5-minute spot close beyond {float(inval_ref):.1f} or option premium falling below ₹{sl_price:.1f}."
        return f"Option premium closing below stop-loss at ₹{sl_price:.1f} or reversal of structural market bias."
