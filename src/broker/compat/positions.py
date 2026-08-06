from __future__ import annotations

import logging
from typing import List, Dict, Any
from src.models.execution_report import BrokerPosition
from src.broker.compat.connection import ConnectionManager

logger = logging.getLogger("BrokerPositions")


class PositionsManager:
    """
    Manages retrieving positions from Zerodha KiteConnect.
    """
    @staticmethod
    def get_positions() -> List[BrokerPosition]:
        """
        Retrieves open net positions, calculates Today's MTM, and maps to BrokerPosition list.
        """
        try:
            client = ConnectionManager().get_client()
            raw_positions = client.positions()
            
            if not raw_positions:
                return []
                
            # If it's a dict containing 'net' and/or 'day' keys (Kite standard)
            net_positions = []
            if isinstance(raw_positions, dict):
                net_positions = raw_positions.get("net", [])
            elif isinstance(raw_positions, list):
                net_positions = raw_positions
                
            broker_positions = []
            for pos in net_positions:
                pnl = float(pos.get("pnl", 0.0))
                # m2m is today's MTM in Kite positions
                today_mtm = float(pos.get("m2m", pos.get("pnl", 0.0)))
                
                broker_positions.append(
                    BrokerPosition(
                        tradingsymbol=pos.get("tradingsymbol", ""),
                        exchange=pos.get("exchange", ""),
                        product=pos.get("product", ""),
                        quantity=int(pos.get("quantity", 0)),
                        average_price=float(pos.get("average_price", pos.get("buy_price", 0.0))),
                        last_price=float(pos.get("last_price", 0.0)),
                        pnl=pnl,
                        today_mtm=today_mtm
                    )
                )
            return broker_positions
        except Exception as e:
            logger.error(f"Error fetching broker positions: {e}")
            return []

    @staticmethod
    def get_today_mtm() -> float:
        """
        Calculates today's total MTM from net positions.
        """
        positions = PositionsManager.get_positions()
        return sum(pos.today_mtm for pos in positions)
