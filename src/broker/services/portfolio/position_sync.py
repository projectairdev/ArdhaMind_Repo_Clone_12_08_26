from __future__ import annotations

import logging
from typing import List
from src.models import BrokerPosition, LivePosition, PositionContext

logger = logging.getLogger("PositionSynchronizer")


class PositionSynchronizer:
    """
    Synchronizes broker-reported positions into immutable LivePosition and PositionContext.
    Calculates realized vs unrealized P&L and today's MTM.
    """

    @staticmethod
    def synchronize(broker_positions: List[BrokerPosition]) -> PositionContext:
        """
        Processes a list of raw BrokerPositions and builds a synchronized PositionContext.
        """
        live_positions: List[LivePosition] = []
        total_mtm = 0.0
        open_count = 0

        for bp in broker_positions:
            qty = bp.quantity
            avg_price = bp.average_price
            ltp = bp.last_price
            pnl = bp.pnl
            today_mtm = bp.today_mtm

            # Calculate realized vs unrealized P&L
            # If position is closed (quantity is 0), all PnL is realized
            if qty == 0:
                unrealized_pnl = 0.0
                realized_pnl = pnl
            else:
                # If open, unrealized PnL is (LTP - Avg Price) * Qty
                # Handle exchange transaction types if quantity is negative (short)
                unrealized_pnl = (ltp - avg_price) * qty
                realized_pnl = pnl - unrealized_pnl
                open_count += 1

            live_pos = LivePosition(
                tradingsymbol=bp.tradingsymbol,
                exchange=bp.exchange,
                product=bp.product,
                quantity=qty,
                average_price=avg_price,
                last_price=ltp,
                pnl=pnl,
                realized_pnl=realized_pnl,
                unrealized_pnl=unrealized_pnl,
                today_mtm=today_mtm
            )
            live_positions.append(live_pos)
            total_mtm += today_mtm

        return PositionContext(
            positions=live_positions,
            total_positions_count=len(live_positions),
            open_positions_count=open_count,
            today_mtm=total_mtm
        )
