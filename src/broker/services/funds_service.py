from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass(frozen=True)
class FundSegment:
    available_cash: float
    utilized_margin: float
    available_margin: float
    opening_balance: float
    collateral: float
    payin_amount: float
    payout_amount: float

@dataclass(frozen=True)
class AccountFunds:
    equity: FundSegment
    commodity: FundSegment

class FundsService:
    @staticmethod
    def get_funds(gateway) -> AccountFunds:
        """
        Retrieves live account funds/margins from the broker gateway and maps to AccountFunds.
        """
        raw = gateway.get_funds()

        # If gateway returned a flat structure or custom object, we'll wrap or adapt it.
        # But our Kite and Mock gateways will both return the standard nested dictionary:
        # {"equity": {...}, "commodity": {...}}
        
        def parse_segment(data: Any) -> FundSegment:
            if not isinstance(data, dict):
                # Fallback to zeros/defaults
                return FundSegment(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
                
            avail = data.get("available", {})
            util = data.get("utilised", {})
            
            # Net margin or available margin is usually the net field at the segment root,
            # or live_balance under available.
            net_margin = float(data.get("net", 0.0)) or float(avail.get("live_balance", 0.0))
            
            return FundSegment(
                available_cash=float(avail.get("cash", 0.0)),
                utilized_margin=float(util.get("debits", 0.0)),
                available_margin=net_margin,
                opening_balance=float(avail.get("opening_balance", 0.0)),
                collateral=float(avail.get("collateral", 0.0)),
                payin_amount=float(avail.get("intraday_payin", 0.0)),
                payout_amount=float(util.get("payout", 0.0))
            )

        if isinstance(raw, dict):
            equity_raw = raw.get("equity", {})
            commodity_raw = raw.get("commodity", {})
        else:
            # Safe fallback if raw is not a dictionary (e.g. mock BrokerFunds object)
            equity_raw = {
                "net": getattr(raw, "available_margin", 0.0),
                "available": {
                    "cash": getattr(raw, "available_cash", 0.0),
                    "live_balance": getattr(raw, "available_margin", 0.0),
                    "opening_balance": getattr(raw, "available_cash", 0.0),
                    "collateral": getattr(raw, "margins", 0.0) - getattr(raw, "available_cash", 0.0),
                },
                "utilised": {
                    "debits": getattr(raw, "utilized_margin", 0.0)
                }
            }
            commodity_raw = {}

        return AccountFunds(
            equity=parse_segment(equity_raw),
            commodity=parse_segment(commodity_raw)
        )
