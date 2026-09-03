from __future__ import annotations

from datetime import date, datetime, timezone
import inspect
import struct
import pytest

from src.market_data.bus.events import MarketEventType
from src.market_data.bus.event_bus import MarketEventBus
from src.market_data.models.canonical_instrument import CanonicalInstrument
from src.market_data.models.quality_enums import Exchange, InstrumentType, OptionType, Segment
from src.market_data.providers.dhan.dhan_instrument_mapper import DhanInstrumentMapper
from src.market_data.providers.dhan.dhan_market_data_provider import DhanMarketDataProvider
from src.market_data.providers.dhan.dhan_tick_normalizer import DhanTickNormalizer
from src.market_data.services.instrument_master_service import InstrumentMasterService


@pytest.fixture
def master_with_nifty():
    master = InstrumentMasterService()
    mapper = DhanInstrumentMapper(master)
    mapper.register_default_universe()
    # Also register an option contract
    mapper.map_and_register({
        "security_id": "45001",
        "exchange_segment": "NFO_OPT",
        "symbol": "NIFTY",
        "instrument_type": "OPTIDX",
        "expiry_date": "2026-09-03",
        "strike_price": 24500.0,
        "option_type": "CE",
    })
    return master


def test_1_instrument_mapping(master_with_nifty: InstrumentMasterService):
    nifty = master_with_nifty.get_by_provider_id("DHAN", "13")
    assert nifty is not None
    assert nifty.canonical_id == "IDX:NSE:NIFTY_50"

    vix = master_with_nifty.get_by_provider_id("DHAN", "26009")
    assert vix is not None
    assert vix.canonical_id == "IDX:NSE:INDIA_VIX"

    opt = master_with_nifty.get_by_provider_id("DHAN", "45001")
    assert opt is not None
    assert opt.canonical_id == "OPT:NFO:NIFTY:2026-09-03:24500:CE"


def test_2_binary_index_packet_parsing(master_with_nifty: InstrumentMasterService):
    normalizer = DhanTickNormalizer(master_with_nifty)
    now_epoch = int(datetime(2026, 8, 28, 9, 15, 30, tzinfo=timezone.utc).timestamp())

    # Response Code 1 (Index Packet): 8-byte header + 24-byte payload = 32 bytes (Little Endian <)
    # Header: resp_code(1)=1, msg_len(2)=32, exch_seg(1)=0, sec_id(4)=13 (NIFTY)
    # Payload: ltp(4)=24550.25, ltt(4)=now_epoch, open(4)=24500.0, high(4)=24580.0, low(4)=24480.0, close(4)=24450.0
    header = struct.pack("<B H B I", 1, 32, 0, 13)
    payload = struct.pack("<f I f f f f", 24550.25, now_epoch, 24500.0, 24580.0, 24480.0, 24450.0)
    raw_packet = header + payload

    tick = normalizer.parse_packet(raw_packet)
    assert tick is not None
    assert tick.canonical_instrument_id == "IDX:NSE:NIFTY_50"
    assert tick.last_price == 24550.25
    assert tick.open == 24500.0
    assert tick.high == 24580.0
    assert tick.low == 24480.0
    assert tick.previous_close == 24450.0
    assert tick.volume is None  # Index does not fabricate volume
    assert tick.provider == "DHAN"


def test_3_binary_india_vix_index_packet(master_with_nifty: InstrumentMasterService):
    normalizer = DhanTickNormalizer(master_with_nifty)
    now_epoch = int(datetime(2026, 8, 28, 9, 15, 30, tzinfo=timezone.utc).timestamp())

    # Sec ID 26009 -> INDIA VIX
    header = struct.pack("<B H B I", 1, 32, 0, 26009)
    payload = struct.pack("<f I f f f f", 12.85, now_epoch, 12.50, 13.10, 12.40, 12.60)
    raw_packet = header + payload

    tick = normalizer.parse_packet(raw_packet)
    assert tick is not None
    assert tick.canonical_instrument_id == "IDX:NSE:INDIA_VIX"
    assert tick.last_price == 12.85
    assert tick.open == 12.50
    assert tick.previous_close == 12.60


def test_4_binary_ticker_packet_parsing(master_with_nifty: InstrumentMasterService):
    normalizer = DhanTickNormalizer(master_with_nifty)
    now_epoch = int(datetime(2026, 8, 28, 9, 15, 30, tzinfo=timezone.utc).timestamp())

    # Response Code 2 (Ticker Packet): 8-byte header + 8-byte payload = 16 bytes
    # Payload: ltp(4)=24550.25, ltt(4)=now_epoch
    header = struct.pack("<B H B I", 2, 16, 0, 13)
    payload = struct.pack("<f I", 24550.25, now_epoch)
    raw_packet = header + payload

    tick = normalizer.parse_packet(raw_packet)
    assert tick is not None
    assert tick.canonical_instrument_id == "IDX:NSE:NIFTY_50"
    assert tick.last_price == 24550.25
    assert tick.provider == "DHAN"


def test_5_binary_quote_packet_parsing(master_with_nifty: InstrumentMasterService):
    normalizer = DhanTickNormalizer(master_with_nifty)
    now_epoch = int(datetime(2026, 8, 28, 9, 15, 30, tzinfo=timezone.utc).timestamp())

    # Response Code 4 (Quote Packet): 8-byte header + 42-byte payload = 50 bytes
    header = struct.pack("<B H B I", 4, 50, 1, 45001)
    payload = struct.pack("<f H I f I f f f f", 125.5, 50, now_epoch, 124.0, 50000, 110.0, 130.0, 105.0, 100.0)
    raw_packet = header + payload

    tick = normalizer.parse_packet(raw_packet)
    assert tick is not None
    assert tick.canonical_instrument_id == "OPT:NFO:NIFTY:2026-09-03:24500:CE"
    assert tick.last_price == 125.5
    assert tick.open == 110.0
    assert tick.high == 130.0
    assert tick.low == 105.0
    assert tick.previous_close == 100.0
    assert tick.volume == 50000


def test_6_binary_oi_and_prev_close_fragmented_merge(master_with_nifty: InstrumentMasterService):
    normalizer = DhanTickNormalizer(master_with_nifty)
    now_epoch = int(datetime(2026, 8, 28, 9, 15, 30, tzinfo=timezone.utc).timestamp())

    # Step 1: Initial Ticker Packet sets LTP = 125.0
    p1 = struct.pack("<B H B I f I", 2, 16, 1, 45001, 125.0, now_epoch)
    t1 = normalizer.parse_packet(p1)
    assert t1.last_price == 125.0
    assert t1.oi is None
    assert t1.previous_close is None

    # Step 2: Response Code 6 (Prev Close Packet): prev_close=100.0, prev_oi=80000
    p2 = struct.pack("<B H B I f I", 6, 16, 1, 45001, 100.0, 80000)
    t2 = normalizer.parse_packet(p2)
    assert t2.previous_close == 100.0
    assert t2.oi == 80000

    # Step 3: Response Code 5 (OI Packet): oi=95000
    p3 = struct.pack("<B H B I I", 5, 12, 1, 45001, 95000)
    t3 = normalizer.parse_packet(p3)
    assert t3.oi == 95000
    assert t3.previous_close == 100.0  # Retained from same session cache

    # Step 4: Next Ticker packet retains merged intraday metadata
    p4 = struct.pack("<B H B I f I", 2, 16, 1, 45001, 126.5, now_epoch + 1)
    t4 = normalizer.parse_packet(p4)
    assert t4.last_price == 126.5
    assert t4.oi == 95000
    assert t4.previous_close == 100.0


def test_7_binary_full_packet_parsing(master_with_nifty: InstrumentMasterService):
    normalizer = DhanTickNormalizer(master_with_nifty)
    now_epoch = int(datetime(2026, 8, 28, 9, 15, 30, tzinfo=timezone.utc).timestamp())

    # Response Code 8 (Full Packet): Quote + Depth + OI
    header = struct.pack("<B H B I", 8, 54, 1, 45001)
    payload = struct.pack("<f H I f I f f f f I f f", 125.5, 50, now_epoch, 124.0, 50000, 110.0, 130.0, 105.0, 100.0, 120000, 125.0, 125.5)
    raw_packet = header + payload

    tick = normalizer.parse_packet(raw_packet)
    assert tick is not None
    assert tick.canonical_instrument_id == "OPT:NFO:NIFTY:2026-09-03:24500:CE"
    assert tick.last_price == 125.5
    assert tick.oi == 120000
    assert tick.bid == 125.0
    assert tick.ask == 125.5


def test_8_market_status_and_disconnect_packets_handled_safely(master_with_nifty: InstrumentMasterService):
    normalizer = DhanTickNormalizer(master_with_nifty)

    # Response Code 7 (Market Status)
    status_pkt = struct.pack("<B H B I", 7, 8, 0, 13)
    assert normalizer.parse_packet(status_pkt) is None
    assert normalizer.market_status_packets_count == 1

    # Response Code 50 (Feed Disconnect)
    disc_pkt = struct.pack("<B H B I", 50, 8, 0, 0)
    assert normalizer.parse_packet(disc_pkt) is None
    assert normalizer.disconnect_packets_count == 1


def test_9_malformed_and_unknown_packets_rejected(master_with_nifty: InstrumentMasterService):
    normalizer = DhanTickNormalizer(master_with_nifty)

    # Truncated header (< 8 bytes)
    assert normalizer.parse_packet(b"\x01\x00\x10") is None
    assert normalizer.malformed_packets_count == 1

    # Truncated payload for Index Packet
    bad_index = struct.pack("<B H B I", 1, 32, 0, 13) + b"\x00\x00"
    assert normalizer.parse_packet(bad_index) is None
    assert normalizer.malformed_packets_count == 2

    # Unknown Response Code (e.g. 99)
    unknown_pkt = struct.pack("<B H B I", 99, 8, 0, 13)
    assert normalizer.parse_packet(unknown_pkt) is None
    assert normalizer.unknown_packets_count == 1


def test_10_dict_packet_parsing(master_with_nifty: InstrumentMasterService):
    normalizer = DhanTickNormalizer(master_with_nifty)

    payload = {
        "security_id": "45001",
        "LTP": 125.5,
        "open": 110.0,
        "high": 130.0,
        "low": 105.0,
        "previous_close": 100.0,
        "volume": 25000,
        "OI": 120000,
        "bid": 125.0,
        "ask": 125.5,
        "LTT": int(datetime(2026, 8, 28, 9, 15, 30, tzinfo=timezone.utc).timestamp()),
    }

    tick = normalizer.parse_packet(payload)
    assert tick is not None
    assert tick.canonical_instrument_id == "OPT:NFO:NIFTY:2026-09-03:24500:CE"
    assert tick.last_price == 125.5
    assert tick.oi == 120000
    assert tick.bid == 125.0
    assert tick.ask == 125.5


def test_11_dhan_market_data_provider_lifecycle(master_with_nifty: InstrumentMasterService):
    bus = MarketEventBus()
    bus.start()

    provider = DhanMarketDataProvider(
        client_id="TEST_CLIENT",
        access_token="TEST_TOKEN",
        instrument_master=master_with_nifty,
        event_bus=bus,
    )

    ticks_received = []
    bus.subscribe(MarketEventType.TICK, lambda e: ticks_received.append(e))

    provider.connect()
    assert provider.is_connected() is True

    nifty = master_with_nifty.get_by_canonical_id("IDX:NSE:NIFTY_50")
    provider.subscribe([nifty])

    # Inject simulated packet
    provider.handle_raw_packet({
        "security_id": "13",
        "LTP": 24510.0,
    })

    import time
    time.sleep(0.05)
    bus.stop(drain=True)

    assert len(ticks_received) == 1
    assert ticks_received[0].payload.last_price == 24510.0


def test_12_architectural_import_inspection():
    import src.market_data.providers.dhan.dhan_market_data_provider as dmdp_mod
    import src.market_data.providers.dhan.dhan_tick_normalizer as dtn_mod
    for mod in (dmdp_mod, dtn_mod):
        source = inspect.getsource(mod)
        forbidden = ["kiteconnect", "src.broker", "src.frontend", "src.controlled_execution"]
        for f in forbidden:
            assert f"import {f}" not in source
            assert f"from {f}" not in source
