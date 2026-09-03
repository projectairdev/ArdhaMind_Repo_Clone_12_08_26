from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import logging
from typing import Any, Callable, Dict, List, Optional, Sequence, Union

from src.market_data.interfaces.historical_data_provider import IHistoricalDataProvider
from src.market_data.models.canonical_candle import CanonicalCandle
from src.market_data.models.canonical_instrument import CanonicalInstrument
from src.market_data.models.quality_enums import CandleQuality, Timeframe

logger = logging.getLogger(__name__)


class DhanHistoricalProvider(IHistoricalDataProvider):
    """
    DhanHQ historical candle provider adapter.
    Normalizes Dhan REST chart endpoints into validated CanonicalCandles.
    """

    TIMEFRAME_TO_DHAN_INTERVAL: Dict[str, str] = {
        "1m": "1",
        "5m": "5",
        "15m": "15",
        "60m": "60",
        "1D": "D",
    }

    def __init__(
        self,
        client_id: Optional[str] = None,
        access_token: Optional[str] = None,
        transport_fetcher: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
    ) -> None:
        self.client_id = client_id or ""
        self._access_token = access_token or ""
        self.transport_fetcher = transport_fetcher

    def provider_name(self) -> str:
        return "DHAN"

    def fetch_candles(
        self,
        instrument: CanonicalInstrument,
        timeframe: Timeframe | str,
        start: datetime,
        end: datetime,
    ) -> Sequence[CanonicalCandle]:
        """
        Fetches and normalizes historical candles from Dhan REST API.
        """
        if not isinstance(instrument, CanonicalInstrument):
            return []

        sec_id = instrument.provider_ids.get("DHAN")
        if not sec_id:
            logger.warning(f"No Dhan security_id mapped for {instrument.canonical_id}")
            return []

        tf_str = timeframe.value if hasattr(timeframe, "value") else str(timeframe)
        interval_code = self.TIMEFRAME_TO_DHAN_INTERVAL.get(tf_str)
        if not interval_code:
            logger.error(f"Unsupported timeframe {tf_str} for Dhan historical provider.")
            return []

        # Prepare request params
        req_params = {
            "securityId": sec_id,
            "exchangeSegment": instrument.exchange.value if hasattr(instrument.exchange, "value") else str(instrument.exchange),
            "instrument": instrument.instrument_type.value if hasattr(instrument.instrument_type, "value") else str(instrument.instrument_type),
            "interval": interval_code,
            "fromDate": start.strftime("%Y-%m-%d %H:%M:%S"),
            "toDate": end.strftime("%Y-%m-%d %H:%M:%S"),
        }

        # If custom fetcher supplied, use it; else return empty or handle network
        if self.transport_fetcher is not None:
            raw_response = self.transport_fetcher(req_params)
            return self.normalize_historical_payload(instrument, timeframe, raw_response, start, end)

        return []

    def normalize_historical_payload(
        self,
        instrument: CanonicalInstrument,
        timeframe: Timeframe | str,
        payload: Dict[str, Any],
        start: datetime,
        end: datetime,
    ) -> List[CanonicalCandle]:
        """
        Normalizes Dhan column-based or row-based JSON charts response into CanonicalCandles.
        """
        tf_enum = Timeframe(timeframe) if isinstance(timeframe, str) and timeframe in [t.value for t in Timeframe] else timeframe
        candles: List[CanonicalCandle] = []

        # Case A: Column arrays format {"open": [...], "high": [...], "low": [...], "close": [...], "volume": [...], "start_Time": [...]}
        if "open" in payload and isinstance(payload["open"], list):
            opens = payload["open"]
            highs = payload.get("high", [])
            lows = payload.get("low", [])
            closes = payload.get("close", [])
            volumes = payload.get("volume", [None] * len(opens))
            times = payload.get("start_Time", payload.get("timestamp", []))

            count = min(len(opens), len(highs), len(lows), len(closes), len(times))
            tf_delta = timedelta(minutes=1 if str(timeframe) == "1m" else (5 if str(timeframe) == "5m" else (15 if str(timeframe) == "15m" else (60 if str(timeframe) == "60m" else 1440))))

            for i in range(count):
                try:
                    o = float(opens[i])
                    h = float(highs[i])
                    l = float(lows[i])
                    c = float(closes[i])
                    v = int(volumes[i]) if volumes[i] is not None and int(volumes[i]) >= 0 else None

                    raw_t = times[i]
                    if isinstance(raw_t, (int, float)):
                        st_dt = datetime.fromtimestamp(raw_t, tz=timezone.utc)
                    elif isinstance(raw_t, str):
                        st_dt = datetime.fromisoformat(raw_t.replace("Z", "+00:00"))
                        if st_dt.tzinfo is None:
                            st_dt = st_dt.replace(tzinfo=timezone.utc)
                    else:
                        continue

                    # Filter range
                    if st_dt < start or st_dt > end:
                        continue

                    end_dt = st_dt + tf_delta

                    candle = CanonicalCandle(
                        canonical_instrument_id=instrument.canonical_id,
                        provider="DHAN",
                        session_date=st_dt.date(),
                        timeframe=tf_enum,
                        start_timestamp=st_dt,
                        end_timestamp=end_dt,
                        open=o,
                        high=h,
                        low=l,
                        close=c,
                        volume=v,
                        quality=CandleQuality.VALID,
                    )
                    candles.append(candle)
                except Exception:
                    continue

        # Deduplicate and sort by start_timestamp
        candles_by_start: Dict[datetime, CanonicalCandle] = {}
        for cand in candles:
            candles_by_start[cand.start_timestamp] = cand

        sorted_candles = [candles_by_start[k] for k in sorted(candles_by_start.keys())]
        return sorted_candles
