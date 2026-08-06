from __future__ import annotations
import logging
from typing import List, Dict, Any, Optional

from src.broker.models.tick import TickModel
from src.broker.services.instrument_service import InstrumentService

logger = logging.getLogger("StreamingService")

STATIC_TOKENS = {
    256265: "NIFTY 50",
    260105: "NIFTY BANK",
    257801: "NIFTY FIN SERVICE",
    258057: "NIFTY MID SELECT"
}


class StreamingService:
    """
    Stateless StreamingService responsible for:
    • Tick ingestion
    • Batch processing
    • Symbol routing
    • Timestamp normalization
    • Immutable tick models
    """

    @staticmethod
    def ingest_ticks(raw_ticks: List[Dict[str, Any]]) -> List[TickModel]:
        """
        Ingests a batch of raw ticks, processes them, resolves symbols,
        normalizes timestamps, and returns a list of immutable TickModels.
        """
        processed_ticks: List[TickModel] = []
        inst_service = InstrumentService.get_instance()

        for raw in raw_ticks:
            token = raw.get("instrument_token")
            if not token:
                continue

            # Route & resolve token to symbol
            symbol = "N/A"
            if token in STATIC_TOKENS:
                symbol = STATIC_TOKENS[token]
            else:
                inst_details = inst_service.lookup_instrument_by_token(token)
                if inst_details:
                    symbol = inst_details.get("tradingsymbol") or "N/A"
                else:
                    # Generic fallback
                    symbol = f"TOKEN_{token}"

            try:
                tick_model = TickModel.from_dict(symbol, raw)
                processed_ticks.append(tick_model)
            except Exception as e:
                logger.error(f"Failed to process tick for token {token}: {e}")

        return processed_ticks

    @staticmethod
    def route_ticks_by_symbol(ticks: List[TickModel]) -> Dict[str, List[TickModel]]:
        """
        Routes tick models into lists grouped by symbol.
        """
        routed: Dict[str, List[TickModel]] = {}
        for tick in ticks:
            if tick.symbol not in routed:
                routed[tick.symbol] = []
            routed[tick.symbol].append(tick)
        return routed
