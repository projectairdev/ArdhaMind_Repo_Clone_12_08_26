from __future__ import annotations
import logging
from typing import List, Set, Dict, Any, Optional

from src.broker.services.instrument_service import InstrumentService

logger = logging.getLogger("SubscriptionManager")

DEFAULT_INDICES = {
    "NIFTY": 256265,
    "BANKNIFTY": 260105,
    "FINNIFTY": 257801,
    "MIDCPNIFTY": 258057
}


class SubscriptionManager:
    """
    Manages active, dynamic subscriptions for indices and option contracts,
    avoiding duplicate subscriptions at runtime.
    """

    def __init__(self, ticker_adapter: Any = None) -> None:
        self.ticker_adapter = ticker_adapter
        self.active_symbols: Set[str] = set()
        self.active_tokens: Set[int] = set()
        self._symbol_tokens: Dict[str, int] = {}

    def set_ticker_adapter(self, ticker_adapter: Any) -> None:
        self.ticker_adapter = ticker_adapter

    def subscribe(self, symbols: List[str]) -> List[int]:
        """
        Dynamically subscribes to a list of symbols (indices or contracts).
        Filters out already subscribed symbols to avoid duplicates.
        Returns a list of newly subscribed tokens.
        """
        tokens_to_sub: List[int] = []
        inst_service = InstrumentService.get_instance()

        for symbol in symbols:
            upper_sym = symbol.upper()
            if upper_sym in self.active_symbols:
                logger.debug(f"Symbol already subscribed: {symbol}")
                continue

            # 1. Resolve to token
            token = None
            if upper_sym in DEFAULT_INDICES:
                token = DEFAULT_INDICES[upper_sym]
            else:
                # Try finding from InstrumentService
                inst = inst_service.lookup_instrument_by_symbol(symbol)
                if inst:
                    token = inst.get("instrument_token")
                else:
                    # Try looking up as index instrument
                    idx_inst = inst_service.lookup_index_instrument(symbol)
                    if idx_inst:
                        token = idx_inst.get("instrument_token")

            if token:
                token = int(token)
                self.active_symbols.add(upper_sym)
                self._symbol_tokens[upper_sym] = token
                if token not in self.active_tokens:
                    tokens_to_sub.append(token)
                    self.active_tokens.add(token)
                    logger.info(f"Subscribed to {symbol} (Token: {token})")
                else:
                    logger.debug(f"Token already subscribed through another symbol: {token}")
            else:
                logger.warning(f"Could not resolve symbol to token: {symbol}")

        if tokens_to_sub and self.ticker_adapter:
            self.ticker_adapter.subscribe(tokens_to_sub)

        return tokens_to_sub

    def unsubscribe(self, symbols: List[str]) -> List[int]:
        """
        Unsubscribes from a list of symbols.
        Only unsubscribes if currently subscribed.
        Returns a list of unsubscribed tokens.
        """
        tokens_to_unsub: List[int] = []
        inst_service = InstrumentService.get_instance()

        for symbol in symbols:
            upper_sym = symbol.upper()
            if upper_sym not in self.active_symbols:
                logger.debug(f"Symbol not active, skip unsub: {symbol}")
                continue

            # Resolve to token
            token = self._symbol_tokens.get(upper_sym)
            if token is None:
                if upper_sym in DEFAULT_INDICES:
                    token = DEFAULT_INDICES[upper_sym]
                else:
                    inst = inst_service.lookup_instrument_by_symbol(symbol)
                    if inst:
                        token = inst.get("instrument_token")

            if token:
                self.active_symbols.discard(upper_sym)
                self._symbol_tokens.pop(upper_sym, None)
                if token not in self._symbol_tokens.values():
                    tokens_to_unsub.append(token)
                    self.active_tokens.discard(token)
                logger.info(f"Unsubscribed from {symbol} (Token: {token})")
            else:
                # If we couldn't resolve, but we had it in set, discard
                self.active_symbols.discard(upper_sym)

        if tokens_to_unsub and self.ticker_adapter:
            self.ticker_adapter.unsubscribe(tokens_to_unsub)

        return tokens_to_unsub

    def get_active_subscriptions(self) -> List[str]:
        return sorted(list(self.active_symbols))

    def get_active_tokens(self) -> List[int]:
        return sorted(list(self.active_tokens))

    def clear(self) -> None:
        """Clears all tracking."""
        self.active_symbols.clear( )
        self.active_tokens.clear()
        self._symbol_tokens.clear()
