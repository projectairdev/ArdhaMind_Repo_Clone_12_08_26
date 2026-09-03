from __future__ import annotations
import logging
from typing import List, Dict, Any, Optional, Set
from datetime import datetime

from src.broker.utils.cache_manager import InstrumentCacheManager
from src.broker.models.trading_mode import TradingMode

logger = logging.getLogger("InstrumentService")

INDEX_MAPPING = {
    "NIFTY": "NIFTY 50",
    "BANKNIFTY": "NIFTY BANK",
    "FINNIFTY": "NIFTY FIN SERVICE",
    "MIDCPNIFTY": "NIFTY MID SELECT",
    "NIFTY50": "NIFTY 50",
    "NIFTYBANK": "NIFTY BANK"
}

class InstrumentService:
    """
    Singleton service for downloading, caching, and querying the Zerodha Instrument Master.
    """
    _instance: Optional[InstrumentService] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(InstrumentService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self._instruments: List[Dict[str, Any]] = []
        self._by_token: Dict[int, Dict[str, Any]] = {}
        self._by_symbol: Dict[str, Dict[str, Any]] = {}
        self._broker_name: str = "MOCK"
        self._last_load_source: str = "none"
        self._last_load_ts: Optional[datetime] = None
        self._initialized = True

    def has_index(self) -> bool:
        """True once an instrument master (fresh, downloaded, or stale fallback)
        has been indexed in memory."""
        return bool(self._instruments)

    def load_diagnostics(self) -> Dict[str, Any]:
        return {
            "source": self._last_load_source,
            "loaded_at": self._last_load_ts.isoformat() if self._last_load_ts else None,
            "instrument_count": len(self._instruments),
            "broker": self._broker_name,
        }

    @classmethod
    def get_instance(cls) -> InstrumentService:
        return cls()

    def load_instruments(self, broker_service: Any, force_refresh: bool = False) -> bool:
        """
        Loads the instrument master list.
        First tries to read from the SQLite Instrument Cache.
        If cache is missing, stale, or force_refresh is True, it downloads from the broker
        and updates the cache.
        """
        # Determine active broker name based on mode
        is_live = getattr(broker_service, "trading_mode", None) == TradingMode.LIVE_ZERODHA
        self._broker_name = "ZERODHA" if is_live else "MOCK"

        # Try to load from cache
        if not force_refresh:
            cached_data = InstrumentCacheManager.load_cache(self._broker_name)
            if cached_data is not None:
                self._build_indexes(cached_data)
                self._last_load_source = "cache_fresh"
                self._last_load_ts = datetime.now()
                return True

        # Cache miss or forced refresh: download from active broker gateway
        try:
            logger.info(f"Downloading instrument master from broker gateway ({self._broker_name})...")
            # Get instruments from active gateway
            instruments = broker_service.get_instruments()
            if instruments:
                # Standardize format (ensure they are dictionaries)
                standard_list = []
                for inst in instruments:
                    if isinstance(inst, dict):
                        standard_list.append(inst)
                    else:
                        # Sometimes instruments returns objects with attributes; convert to dict
                        standard_list.append({
                            "instrument_token": getattr(inst, "instrument_token", 0),
                            "exchange_token": getattr(inst, "exchange_token", 0),
                            "tradingsymbol": getattr(inst, "tradingsymbol", ""),
                            "name": getattr(inst, "name", ""),
                            "last_price": float(getattr(inst, "last_price", 0.0) or 0.0),
                            "expiry": str(getattr(inst, "expiry", "")) if getattr(inst, "expiry", None) else "",
                            "strike": float(getattr(inst, "strike", 0.0) or 0.0),
                            "tick_size": float(getattr(inst, "tick_size", 0.0) or 0.0),
                            "lot_size": int(getattr(inst, "lot_size", 0) or 0),
                            "instrument_type": getattr(inst, "instrument_type", ""),
                            "segment": getattr(inst, "segment", ""),
                            "exchange": getattr(inst, "exchange", ""),
                        })

                # Filter list to supported segments/exchanges/indices for efficiency
                # (NSE and NFO are main segments requested)
                filtered_list = [
                    inst for inst in standard_list
                    if inst.get("exchange") in ("NSE", "NFO")
                ]
                
                # If filtered_list is empty, keep full list to prevent clearing cache accidentally
                final_list = filtered_list if filtered_list else standard_list

                # Save to cache
                InstrumentCacheManager.save_cache(self._broker_name, final_list)
                self._build_indexes(final_list)
                self._last_load_source = "download"
                self._last_load_ts = datetime.now()
                return True
            else:
                logger.warning("Broker returned empty instrument master list.")
                return self._fall_back_to_stale_cache("empty_download")
        except Exception as e:
            logger.error(f"Error downloading/caching instruments: {e}", exc_info=True)
            return self._fall_back_to_stale_cache(f"download_failed: {e}")

    def _fall_back_to_stale_cache(self, reason: str) -> bool:
        """Last resort when a live re-download is unavailable: use a same-day
        cache if one somehow exists, otherwise a day-old one. A stale instrument
        master still resolves every future option expiry; failing silently and
        leaving an empty in-memory index does not.
        """
        cached_data = InstrumentCacheManager.load_cache(self._broker_name)
        if cached_data is None:
            cached_data = InstrumentCacheManager.load_cache(self._broker_name, allow_stale=True)
            source = "cache_stale_fallback"
        else:
            source = "cache_fresh"
        if cached_data is not None:
            self._build_indexes(cached_data)
            self._last_load_source = source
            self._last_load_ts = datetime.now()
            logger.warning(
                f"Instrument master unavailable from broker ({reason}); "
                f"serving {len(cached_data)} instruments from {source}."
            )
            return True
        logger.error(
            f"Instrument master unavailable from broker ({reason}) and no usable cache — "
            "expiry resolution will be blocked until the next successful sync."
        )
        return False

    def _build_indexes(self, data: List[Dict[str, Any]]) -> None:
        """Builds in-memory dictionaries for instant lookups."""
        self._instruments = data
        self._by_token = {inst["instrument_token"]: inst for inst in data if inst.get("instrument_token")}
        self._by_symbol = {inst["tradingsymbol"]: inst for inst in data if inst.get("tradingsymbol")}
        logger.info(f"Indexed {len(self._instruments)} instruments in memory.")

    # Lookup Operations

    def lookup_instrument_by_token(self, token: int) -> Optional[Dict[str, Any]]:
        """Looks up a single instrument by its unique token."""
        return self._by_token.get(token)

    def lookup_instrument_by_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Looks up an instrument by its tradingsymbol (e.g. 'NIFTY26JUL22000CE')."""
        return self._by_symbol.get(symbol)

    def lookup_token_by_symbol(self, symbol: str) -> Optional[int]:
        """Looks up the instrument token for a given tradingsymbol."""
        inst = self.lookup_instrument_by_symbol(symbol)
        return inst["instrument_token"] if inst else None

    def lookup_instruments_by_exchange(self, exchange: str) -> List[Dict[str, Any]]:
        """Returns all instruments belonging to an exchange (e.g. NSE, NFO)."""
        return [inst for inst in self._instruments if inst.get("exchange") == exchange]

    def lookup_expiries(self, name: str) -> List[str]:
        """
        Returns sorted unique expiry dates (YYYY-MM-DD or string representation)
        for a underlying index name (e.g. NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY) in NFO.
        """
        expiries: Set[str] = set()
        for inst in self._instruments:
            if inst.get("exchange") == "NFO" and inst.get("name") == name:
                exp = inst.get("expiry")
                if exp:
                    expiries.add(exp)
        return sorted(list(expiries))

    def lookup_strikes(self, name: str, expiry: str) -> List[float]:
        """
        Returns sorted unique strike prices for a given index name and expiry date.
        """
        strikes: Set[float] = set()
        for inst in self._instruments:
            if inst.get("exchange") == "NFO" and inst.get("name") == name and inst.get("expiry") == expiry:
                strike = inst.get("strike")
                if strike is not None:
                    try:
                        strikes.add(float(strike))
                    except (ValueError, TypeError):
                        pass
        return sorted(list(strikes))

    def lookup_option_type(self, name: str, expiry: str, strike: float, option_type: str) -> Optional[Dict[str, Any]]:
        """
        Looks up a specific option contract.
        option_type must be 'CE' or 'PE'.
        """
        # Normalize CE/PE
        opt_type = option_type.upper()
        for inst in self._instruments:
            if (
                inst.get("exchange") == "NFO"
                and inst.get("name") == name
                and inst.get("expiry") == expiry
                and abs(float(inst.get("strike", 0.0) or 0.0) - float(strike)) < 0.01
                and inst.get("instrument_type", "").upper() == opt_type
            ):
                return inst
        return None

    def lookup_index_instrument(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Looks up the underlying index spot/EQ instrument (e.g. NIFTY 50 index spot instrument).
        Supports NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY.
        """
        normalized_name = INDEX_MAPPING.get(name.upper(), name)
        # Search for index in NSE segment
        for inst in self._instruments:
            if inst.get("exchange") == "NSE" and inst.get("segment") == "INDICES" and inst.get("name") == normalized_name:
                return inst
            if inst.get("exchange") == "NSE" and inst.get("tradingsymbol") == normalized_name:
                return inst
        # Fallback search anywhere
        for inst in self._instruments:
            if inst.get("name") == normalized_name:
                return inst
            if inst.get("tradingsymbol") == normalized_name:
                return inst
        return None
