from __future__ import annotations

import logging
from typing import List, Optional
from src.models import LivePosition, PositionContext, PortfolioContext, BrokerFunds

logger = logging.getLogger("PortfolioSynchronizer")


class PortfolioSynchronizer:
    """
    Synchronizes portfolio state based on current PositionContext and BrokerFunds.
    Identifies active (open) vs closed positions and tracks capital utilization.
    """

    @staticmethod
    def synchronize(
        position_context: PositionContext,
        broker_funds: Optional[BrokerFunds] = None,
        default_capital: float = 1000000.0
    ) -> PortfolioContext:
        """
        Builds a PortfolioContext from the current live positions and broker funds.
        """
        active_positions: List[LivePosition] = []
        closed_positions: List[LivePosition] = []
        portfolio_mtm = 0.0

        for pos in position_context.positions:
            if pos.quantity != 0:
                active_positions.append(pos)
                portfolio_mtm += pos.pnl  # P&L of active positions
            else:
                closed_positions.append(pos)

        # Extract capital and utilization from broker funds if available
        if broker_funds:
            capital_utilized = broker_funds.utilized_margin
            available_capital = broker_funds.available_margin
        else:
            capital_utilized = 0.0
            available_capital = default_capital

        return PortfolioContext(
            active_positions=active_positions,
            closed_positions=closed_positions,
            capital_utilized=capital_utilized,
            available_capital=available_capital,
            portfolio_mtm=portfolio_mtm
        )
