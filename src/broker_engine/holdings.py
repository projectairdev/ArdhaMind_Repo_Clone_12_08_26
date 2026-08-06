from __future__ import annotations

import logging
from typing import List, Dict, Any
from src.models.execution_report import BrokerHolding
from src.broker_engine.connection import ConnectionManager

logger = logging.getLogger("BrokerHoldings")


class HoldingsManager:
    """
    Manages retrieving holdings from Zerodha KiteConnect.
    """
    @staticmethod
    def get_holdings() -> List[BrokerHolding]:
        """
        Retrieves long-term holdings and maps to BrokerHolding list.
        """
        try:
            client = ConnectionManager().get_client()
            raw_holdings = client.holdings()
            
            if not raw_holdings:
                return []
                
            broker_holdings = []
            for h in raw_holdings:
                # average price can be 'average_price' or 'buy_price'
                avg_price = float(h.get("average_price", h.get("buy_price", 0.0)))
                qty = int(h.get("quantity", 0))
                last_price = float(h.get("last_price", 0.0))
                
                # Calculate P&L if not provided
                pnl = float(h.get("pnl", (last_price - avg_price) * qty))
                
                broker_holdings.append(
                    BrokerHolding(
                        tradingsymbol=h.get("tradingsymbol", ""),
                        exchange=h.get("exchange", "NSE"),
                        product=h.get("product", "CNC"),
                        quantity=qty,
                        average_price=avg_price,
                        last_price=last_price,
                        pnl=pnl
                    )
                )
            return broker_holdings
        except Exception as e:
            logger.error(f"Error fetching broker holdings: {e}")
            return []
