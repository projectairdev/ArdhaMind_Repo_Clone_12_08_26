from __future__ import annotations

from datetime import date, datetime, timezone
import struct
import threading
from typing import Any, Dict, Optional, Tuple, Union

from src.market_data.models.canonical_tick import CanonicalTick
from src.market_data.services.instrument_master_service import InstrumentMasterService


class DhanTickNormalizer:
    """
    Decodes DhanHQ v2 binary and JSON WebSocket packets into immutable CanonicalTick objects.
    Uses official Little-Endian (<) unpacking and handles fragmented metadata assembly.
    """

    # Official DhanHQ v2 Feed Response Codes
    RESP_INDEX = 1
    RESP_TICKER = 2
    RESP_QUOTE = 4
    RESP_OI = 5
    RESP_PREV_CLOSE = 6
    RESP_MARKET_STATUS = 7
    RESP_FULL = 8
    RESP_DISCONNECT = 50

    def __init__(self, instrument_master: InstrumentMasterService) -> None:
        self.instrument_master = instrument_master
        self._lock = threading.RLock()

        # Telemetry
        self.malformed_packets_count: int = 0
        self.unmapped_security_ids_count: int = 0
        self.unknown_packets_count: int = 0
        self.disconnect_packets_count: int = 0
        self.market_status_packets_count: int = 0

        # Provider-side fragmented metadata cache: (sec_id, session_date) -> dict
        self._cached_session_metadata: Dict[Tuple[str, date], Dict[str, Any]] = {}
        self._last_known_prices: Dict[str, float] = {}

    def _get_metadata(self, sec_id_str: str, sess_date: date) -> Dict[str, Any]:
        with self._lock:
            if (sec_id_str, sess_date) in self._cached_session_metadata:
                return self._cached_session_metadata[(sec_id_str, sess_date)]
            matches = [v for k, v in self._cached_session_metadata.items() if k[0] == sec_id_str]
            return matches[-1] if matches else {}

    def parse_packet(
        self,
        raw_packet: Union[bytes, Dict[str, Any]],
        received_at: Optional[datetime] = None,
    ) -> Optional[CanonicalTick]:
        """
        Parses a single binary or dictionary packet from DhanHQ v2.
        Returns CanonicalTick if valid and mapped; None otherwise.
        """
        rcv_time = received_at or datetime.now(timezone.utc)
        if rcv_time.tzinfo is None:
            rcv_time = rcv_time.replace(tzinfo=timezone.utc)

        if isinstance(raw_packet, bytes):
            return self._parse_binary_packet(raw_packet, rcv_time)
        elif isinstance(raw_packet, dict):
            return self._parse_dict_packet(raw_packet, rcv_time)
        else:
            with self._lock:
                self.malformed_packets_count += 1
            return None

    def _parse_binary_packet(self, data: bytes, rcv_time: datetime) -> Optional[CanonicalTick]:
        """
        DhanHQ v2 Binary Protocol Unpacker (Little-Endian <):
        Header (8 bytes):
          byte 0: response_code (uint8)
          byte 1-2: message_length (uint16 little-endian)
          byte 3: exchange_segment (uint8)
          byte 4-7: security_id (uint32 little-endian)
        """
        if len(data) < 8:
            with self._lock:
                self.malformed_packets_count += 1
            return None

        try:
            resp_code = data[0]
            msg_len = struct.unpack("<H", data[1:3])[0]
            exch_seg = data[3]
            sec_id = struct.unpack("<I", data[4:8])[0]
        except Exception:
            with self._lock:
                self.malformed_packets_count += 1
            return None

        # Handle disconnect packet (Code 50)
        if resp_code == self.RESP_DISCONNECT:
            with self._lock:
                self.disconnect_packets_count += 1
            return None

        # Handle market status packet (Code 7)
        if resp_code == self.RESP_MARKET_STATUS:
            with self._lock:
                self.market_status_packets_count += 1
            return None

        sec_id_str = str(sec_id)
        canonical_inst = self.instrument_master.get_by_provider_id("DHAN", sec_id_str)
        if canonical_inst is None:
            with self._lock:
                self.unmapped_security_ids_count += 1
            return None

        cid = canonical_inst.canonical_id

        try:
            # 1. Index Packet (Code 1): 8-byte header + 24-byte payload = 32 bytes
            # Payload: ltp (f32), ltt (i32), open (f32), high (f32), low (f32), close (f32)
            if resp_code == self.RESP_INDEX:
                if len(data) < 32:
                    with self._lock:
                        self.malformed_packets_count += 1
                    return None

                ltp, ltt, open_p, high_p, low_p, close_p = struct.unpack("<f I f f f f", data[8:32])
                ex_dt = datetime.fromtimestamp(ltt, tz=timezone.utc) if ltt > 0 else rcv_time
                sess_date = ex_dt.date()

                if ltp <= 0:
                    return None

                with self._lock:
                    self._last_known_prices[sec_id_str] = ltp

                return CanonicalTick(
                    canonical_instrument_id=cid,
                    provider="DHAN",
                    exchange_timestamp=ex_dt,
                    received_at=rcv_time,
                    session_date=sess_date,
                    last_price=round(ltp, 4),
                    open=round(open_p, 4) if open_p > 0 else None,
                    high=round(high_p, 4) if high_p > 0 else None,
                    low=round(low_p, 4) if low_p > 0 else None,
                    previous_close=round(close_p, 4) if close_p > 0 else None,
                )

            # 2. Ticker Packet (Code 2): 8-byte header + 8-byte payload = 16 bytes
            # Payload: ltp (f32), ltt (i32)
            elif resp_code == self.RESP_TICKER:
                if len(data) < 16:
                    with self._lock:
                        self.malformed_packets_count += 1
                    return None

                ltp, ltt = struct.unpack("<f I", data[8:16])
                ex_dt = datetime.fromtimestamp(ltt, tz=timezone.utc) if ltt > 0 else rcv_time
                sess_date = ex_dt.date()

                if ltp <= 0:
                    return None

                with self._lock:
                    self._last_known_prices[sec_id_str] = ltp
                    meta = self._get_metadata(sec_id_str, sess_date)

                return CanonicalTick(
                    canonical_instrument_id=cid,
                    provider="DHAN",
                    exchange_timestamp=ex_dt,
                    received_at=rcv_time,
                    session_date=sess_date,
                    last_price=round(ltp, 4),
                    previous_close=meta.get("previous_close"),
                    oi=meta.get("oi"),
                )

            # 3. Quote Packet (Code 4): 8-byte header + 34-byte payload = 42 bytes
            # Payload: ltp (f32), ltq (u16), ltt (i32), atp (f32), vol (u32), open (f32), high (f32), low (f32), close (f32)
            elif resp_code == self.RESP_QUOTE:
                if len(data) < 42:
                    with self._lock:
                        self.malformed_packets_count += 1
                    return None

                ltp = struct.unpack("<f", data[8:12])[0]
                ltq = struct.unpack("<H", data[12:14])[0]
                ltt = struct.unpack("<I", data[14:18])[0]
                atp = struct.unpack("<f", data[18:22])[0]
                vol = struct.unpack("<I", data[22:26])[0]
                open_p = struct.unpack("<f", data[26:30])[0]
                high_p = struct.unpack("<f", data[30:34])[0]
                low_p = struct.unpack("<f", data[34:38])[0]
                close_p = struct.unpack("<f", data[38:42])[0] if len(data) >= 42 else None

                ex_dt = datetime.fromtimestamp(ltt, tz=timezone.utc) if ltt > 0 else rcv_time
                sess_date = ex_dt.date()

                if ltp <= 0:
                    return None

                with self._lock:
                    self._last_known_prices[sec_id_str] = ltp
                    meta = self._get_metadata(sec_id_str, sess_date)
                    if close_p and close_p > 0:
                        meta["previous_close"] = round(close_p, 4)
                        self._cached_session_metadata[(sec_id_str, sess_date)] = meta

                return CanonicalTick(
                    canonical_instrument_id=cid,
                    provider="DHAN",
                    exchange_timestamp=ex_dt,
                    received_at=rcv_time,
                    session_date=sess_date,
                    last_price=round(ltp, 4),
                    open=round(open_p, 4) if open_p and open_p > 0 else None,
                    high=round(high_p, 4) if high_p and high_p > 0 else None,
                    low=round(low_p, 4) if low_p and low_p > 0 else None,
                    previous_close=round(close_p, 4) if close_p and close_p > 0 else meta.get("previous_close"),
                    volume=int(vol) if vol > 0 else None,
                    oi=meta.get("oi"),
                )

            # 4. OI Packet (Code 5): 8-byte header + 4-byte payload = 12 bytes
            # Payload: oi (u32)
            elif resp_code == self.RESP_OI:
                if len(data) < 12:
                    with self._lock:
                        self.malformed_packets_count += 1
                    return None

                oi_val = struct.unpack("<I", data[8:12])[0]
                sess_date = rcv_time.date()

                with self._lock:
                    meta = self._cached_session_metadata.setdefault((sec_id_str, sess_date), {})
                    meta["oi"] = int(oi_val)
                    last_p = self._last_known_prices.get(sec_id_str)

                if last_p is not None and last_p > 0:
                    return CanonicalTick(
                        canonical_instrument_id=cid,
                        provider="DHAN",
                        exchange_timestamp=rcv_time,
                        received_at=rcv_time,
                        session_date=sess_date,
                        last_price=round(last_p, 4),
                        oi=int(oi_val) if oi_val >= 0 else None,
                        previous_close=meta.get("previous_close"),
                    )
                return None

            # 5. Prev Close Packet (Code 6): 8-byte header + 8-byte payload = 16 bytes
            # Payload: prev_close (f32), prev_oi (u32)
            elif resp_code == self.RESP_PREV_CLOSE:
                if len(data) < 16:
                    with self._lock:
                        self.malformed_packets_count += 1
                    return None

                prev_close_val, prev_oi_val = struct.unpack("<f I", data[8:16])
                sess_date = rcv_time.date()

                with self._lock:
                    meta = self._cached_session_metadata.setdefault((sec_id_str, sess_date), {})
                    if prev_close_val > 0:
                        meta["previous_close"] = round(prev_close_val, 4)
                    if prev_oi_val > 0:
                        meta["oi"] = int(prev_oi_val)
                    last_p = self._last_known_prices.get(sec_id_str)

                if last_p is not None and last_p > 0 and prev_close_val > 0:
                    return CanonicalTick(
                        canonical_instrument_id=cid,
                        provider="DHAN",
                        exchange_timestamp=rcv_time,
                        received_at=rcv_time,
                        session_date=sess_date,
                        last_price=round(last_p, 4),
                        previous_close=round(prev_close_val, 4),
                        oi=int(prev_oi_val) if prev_oi_val > 0 else None,
                    )
                return None

            # 6. Full Packet (Code 8): Quote fields + Market Depth + OI
            elif resp_code == self.RESP_FULL:
                if len(data) < 50:
                    with self._lock:
                        self.malformed_packets_count += 1
                    return None

                ltp = struct.unpack("<f", data[8:12])[0]
                ltq = struct.unpack("<H", data[12:14])[0]
                ltt = struct.unpack("<I", data[14:18])[0]
                atp = struct.unpack("<f", data[18:22])[0]
                vol = struct.unpack("<I", data[22:26])[0]
                open_p = struct.unpack("<f", data[26:30])[0]
                high_p = struct.unpack("<f", data[30:34])[0]
                low_p = struct.unpack("<f", data[34:38])[0]
                close_p = struct.unpack("<f", data[38:42])[0] if len(data) >= 42 else None

                oi_val: Optional[int] = None
                bid_p: Optional[float] = None
                ask_p: Optional[float] = None

                if len(data) >= 54:
                    oi_val = struct.unpack("<I", data[42:46])[0]
                    bid_p = struct.unpack("<f", data[46:50])[0]
                    ask_p = struct.unpack("<f", data[50:54])[0]

                ex_dt = datetime.fromtimestamp(ltt, tz=timezone.utc) if ltt > 0 else rcv_time
                sess_date = ex_dt.date()

                if ltp <= 0:
                    return None

                with self._lock:
                    self._last_known_prices[sec_id_str] = ltp
                    meta = self._cached_session_metadata.setdefault((sec_id_str, sess_date), {})
                    if close_p and close_p > 0:
                        meta["previous_close"] = round(close_p, 4)
                    if oi_val is not None and oi_val > 0:
                        meta["oi"] = int(oi_val)

                return CanonicalTick(
                    canonical_instrument_id=cid,
                    provider="DHAN",
                    exchange_timestamp=ex_dt,
                    received_at=rcv_time,
                    session_date=sess_date,
                    last_price=round(ltp, 4),
                    open=round(open_p, 4) if open_p and open_p > 0 else None,
                    high=round(high_p, 4) if high_p and high_p > 0 else None,
                    low=round(low_p, 4) if low_p and low_p > 0 else None,
                    previous_close=round(close_p, 4) if close_p and close_p > 0 else meta.get("previous_close"),
                    volume=int(vol) if vol > 0 else None,
                    oi=int(oi_val) if oi_val is not None and oi_val > 0 else meta.get("oi"),
                    bid=round(bid_p, 4) if bid_p and bid_p > 0 else None,
                    ask=round(ask_p, 4) if ask_p and ask_p > 0 else None,
                )

            else:
                with self._lock:
                    self.unknown_packets_count += 1
                return None

        except Exception:
            with self._lock:
                self.malformed_packets_count += 1
            return None

    def _parse_dict_packet(self, data: Dict[str, Any], rcv_time: datetime) -> Optional[CanonicalTick]:
        """Parses dictionary tick payloads (REST responses or JSON WebSocket feeds)."""
        sec_id = str(data.get("security_id", data.get("securityId", ""))).strip()
        if not sec_id:
            with self._lock:
                self.malformed_packets_count += 1
            return None

        canonical_inst = self.instrument_master.get_by_provider_id("DHAN", sec_id)
        if canonical_inst is None:
            with self._lock:
                self.unmapped_security_ids_count += 1
            return None

        cid = canonical_inst.canonical_id

        try:
            ltp = float(data.get("LTP", data.get("last_price", data.get("ltp", 0.0))))
            if ltp <= 0:
                return None

            ltt_val = data.get("LTT", data.get("last_trade_time", data.get("time")))
            if isinstance(ltt_val, (int, float)) and ltt_val > 0:
                ex_dt = datetime.fromtimestamp(ltt_val, tz=timezone.utc)
            elif isinstance(ltt_val, str) and ltt_val.strip():
                ex_dt = datetime.fromisoformat(ltt_val.replace("Z", "+00:00"))
                if ex_dt.tzinfo is None:
                    ex_dt = ex_dt.replace(tzinfo=timezone.utc)
            else:
                ex_dt = rcv_time

            sess_date = ex_dt.date()

            open_p = float(data["open"]) if data.get("open") and float(data["open"]) > 0 else None
            high_p = float(data["high"]) if data.get("high") and float(data["high"]) > 0 else None
            low_p = float(data["low"]) if data.get("low") and float(data["low"]) > 0 else None
            prev_close = float(data["previous_close"]) if data.get("previous_close") and float(data["previous_close"]) > 0 else (
                float(data["close"]) if data.get("close") and float(data["close"]) > 0 else None
            )
            vol = int(data["volume"]) if data.get("volume") is not None and int(data["volume"]) >= 0 else None
            oi = int(data["OI"]) if data.get("OI") is not None and int(data["OI"]) >= 0 else (
                int(data["oi"]) if data.get("oi") is not None and int(data["oi"]) >= 0 else None
            )
            bid = float(data["bid"]) if data.get("bid") and float(data["bid"]) > 0 else None
            ask = float(data["ask"]) if data.get("ask") and float(data["ask"]) > 0 else None

            with self._lock:
                self._last_known_prices[sec_id] = ltp
                meta = self._cached_session_metadata.setdefault((sec_id, sess_date), {})
                if prev_close and prev_close > 0:
                    meta["previous_close"] = round(prev_close, 4)
                if oi is not None and oi > 0:
                    meta["oi"] = int(oi)

            return CanonicalTick(
                canonical_instrument_id=cid,
                provider="DHAN",
                exchange_timestamp=ex_dt,
                received_at=rcv_time,
                session_date=sess_date,
                last_price=round(ltp, 4),
                open=round(open_p, 4) if open_p else None,
                high=round(high_p, 4) if high_p else None,
                low=round(low_p, 4) if low_p else None,
                previous_close=round(prev_close, 4) if prev_close else meta.get("previous_close"),
                volume=vol,
                oi=oi if oi is not None else meta.get("oi"),
                bid=round(bid, 4) if bid else None,
                ask=round(ask, 4) if ask else None,
            )
        except Exception:
            with self._lock:
                self.malformed_packets_count += 1
            return None
