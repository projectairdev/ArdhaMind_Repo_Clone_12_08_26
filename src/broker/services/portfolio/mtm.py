from __future__ import annotations

import logging
from typing import List, Dict
from src.models import LivePosition, PositionContext

logger = logging.getLogger("MTMCalculator")


class MTMCalculator:
    """
    Utility class dedicated to high-precision Mark-to-Market (MTM) calculations,
    risk sensitivity, and total P&L aggregation.
    """

    @staticmethod
    def calculate_total_mtm(positions: List[LivePosition]) -> float:
        """
        Sum today's MTM across all open and closed positions.
        """
        return sum(pos.today_mtm for pos in positions)

    @staticmethod
    def calculate_unrealized_pnl(positions: List[LivePosition]) -> float:
        """
        Sum unrealized P&L across all positions.
        """
        return sum(pos.unrealized_pnl for pos in positions)

    @staticmethod
    def calculate_realized_pnl(positions: List[LivePosition]) -> float:
        """
        Sum realized P&L across all positions.
        """
        return sum(pos.realized_pnl for pos in positions)

    @staticmethod
    def project_mtm_sensitivity(
        positions: List[LivePosition],
        price_shifts_percent: Dict[str, float]
    ) -> float:
        """
        Projects a theoretical MTM shift if specific symbols undergo a percentage price shift.
        price_shifts_percent maps tradingsymbol to percent change (e.g., {"RELIANCE": 1.5, "NIFTY26NOV24200CE": -5.0})
        """
        projected_mtm_delta = 0.0
        for pos in positions:
            if pos.quantity == 0:
                continue
            shift = price_shifts_percent.get(pos.tradingsymbol, 0.0) / 100.0
            if shift != 0:
                # Delta P&L = Qty * Average Price (or last price) * shift
                # Standard option/equity calculation: Qty * Last Price * shift
                projected_mtm_delta += pos.quantity * pos.last_price * shift
        return projected_mtm_delta
