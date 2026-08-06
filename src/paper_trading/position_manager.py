from __future__ import annotations

from src.models import PaperTrade, PaperPosition


class PaperPositionManager:
    """
    Stateless manager responsible for tracking active paper positions.
    """

    @staticmethod
    def create_position(trade: PaperTrade) -> PaperPosition:
        """
        Creates a new OPEN position from a PaperTrade.
        """
        return PaperPosition(
            position_id=f"P_{trade.trade_id}",
            trade=trade,
            current_mtm=0.0,
            peak_mtm=0.0,
            drawdown=0.0,
            holding_time_seconds=0.0,
            status="OPEN",
            current_premium=trade.premium,
        )

    @staticmethod
    def update_position(
        position: PaperPosition, current_premium: float, elapsed_seconds: float
    ) -> PaperPosition:
        """
        Updates MTM, peak MTM, drawdown, and holding time of a position.
        Returns a new immutable PaperPosition.
        """
        if position.status == "CLOSED":
            return position

        # Determine lot size (50 for Nifty options, 1 for stocks)
        lot_size = 50 if "NIFTY" in position.trade.tradingsymbol else 1

        # Calculate MTM based on side
        entry_premium = position.trade.premium
        lots = position.trade.lots

        if position.trade.action == "BUY":
            current_mtm = (current_premium - entry_premium) * lots * lot_size
        else:  # "SELL"
            current_mtm = (entry_premium - current_premium) * lots * lot_size

        peak_mtm = max(position.peak_mtm, current_mtm)
        drawdown = max(0.0, peak_mtm - current_mtm)
        new_holding_time = position.holding_time_seconds + elapsed_seconds

        return PaperPosition(
            position_id=position.position_id,
            trade=position.trade,
            current_mtm=current_mtm,
            peak_mtm=peak_mtm,
            drawdown=drawdown,
            holding_time_seconds=new_holding_time,
            status="OPEN",
            current_premium=current_premium,
        )
