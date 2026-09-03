from __future__ import annotations
import inspect
import sys
import threading
import pytest
from datetime import date

from src.market_data.models.canonical_instrument import CanonicalInstrument
from src.market_data.models.quality_enums import Exchange, Segment, InstrumentType, OptionType
from src.market_data.services.instrument_master_service import (
    InstrumentMasterService,
    build_canonical_id,
    normalize_strike,
)


@pytest.fixture
def service() -> InstrumentMasterService:
    return InstrumentMasterService()


def test_1_register_nifty(service: InstrumentMasterService):
    nifty = CanonicalInstrument(
        canonical_id="IDX:NSE:NIFTY_50",
        symbol="NIFTY 50",
        exchange=Exchange.NSE,
        segment=Segment.INDEX,
        instrument_type=InstrumentType.INDEX,
        lot_size=50,
        tick_size=0.05,
        provider_ids={"KITE": 256265, "DHAN": "13"},
    )
    service.register(nifty)
    assert service.get_by_canonical_id("IDX:NSE:NIFTY_50") == nifty


def test_2_register_india_vix(service: InstrumentMasterService):
    vix = CanonicalInstrument(
        canonical_id="IDX:NSE:INDIA_VIX",
        symbol="INDIA VIX",
        exchange=Exchange.NSE,
        segment=Segment.INDEX,
        instrument_type=InstrumentType.INDEX,
        lot_size=1,
        tick_size=0.01,
        provider_ids={"KITE": 264969},
    )
    service.register(vix)
    assert service.get_by_canonical_id("IDX:NSE:INDIA_VIX") == vix


def test_3_get_by_canonical_id(service: InstrumentMasterService):
    nifty = CanonicalInstrument(
        canonical_id="IDX:NSE:NIFTY_50",
        symbol="NIFTY 50",
        exchange=Exchange.NSE,
        segment=Segment.INDEX,
        instrument_type=InstrumentType.INDEX,
    )
    service.register(nifty)
    assert service.get_by_canonical_id("IDX:NSE:NIFTY_50") is not None
    assert service.get_by_canonical_id("NON_EXISTENT") is None


def test_4_resolve_nifty_aliases(service: InstrumentMasterService):
    nifty = CanonicalInstrument(
        canonical_id="IDX:NSE:NIFTY_50",
        symbol="NIFTY 50",
        exchange=Exchange.NSE,
        segment=Segment.INDEX,
        instrument_type=InstrumentType.INDEX,
    )
    service.register(nifty)

    assert service.resolve_symbol("NIFTY") == nifty
    assert service.resolve_symbol("NIFTY 50") == nifty
    assert service.resolve_symbol("NIFTY50") == nifty
    assert service.resolve_symbol("NSE:NIFTY 50") == nifty
    assert service.resolve_symbol("NSE:NIFTY50") == nifty
    assert service.resolve_symbol("nifty 50") == nifty


def test_5_resolve_vix_aliases(service: InstrumentMasterService):
    vix = CanonicalInstrument(
        canonical_id="IDX:NSE:INDIA_VIX",
        symbol="INDIA VIX",
        exchange=Exchange.NSE,
        segment=Segment.INDEX,
        instrument_type=InstrumentType.INDEX,
    )
    service.register(vix)

    assert service.resolve_symbol("INDIA VIX") == vix
    assert service.resolve_symbol("INDIAVIX") == vix
    assert service.resolve_symbol("NSE:INDIA VIX") == vix
    assert service.resolve_symbol("NSE:INDIAVIX") == vix


def test_6_provider_id_lookup(service: InstrumentMasterService):
    nifty = CanonicalInstrument(
        canonical_id="IDX:NSE:NIFTY_50",
        symbol="NIFTY 50",
        exchange=Exchange.NSE,
        segment=Segment.INDEX,
        instrument_type=InstrumentType.INDEX,
        provider_ids={"KITE": 256265, "DHAN": {"security_id": "13"}},
    )
    service.register(nifty)

    assert service.get_provider_id("IDX:NSE:NIFTY_50", "KITE") == 256265
    assert service.get_provider_id("IDX:NSE:NIFTY_50", "DHAN") == {"security_id": "13"}
    assert service.get_provider_id("IDX:NSE:NIFTY_50", "UNKNOWN") is None


def test_7_reverse_provider_lookup(service: InstrumentMasterService):
    nifty = CanonicalInstrument(
        canonical_id="IDX:NSE:NIFTY_50",
        symbol="NIFTY 50",
        exchange=Exchange.NSE,
        segment=Segment.INDEX,
        instrument_type=InstrumentType.INDEX,
        provider_ids={"KITE": 256265, "DHAN": "13"},
    )
    service.register(nifty)

    assert service.resolve_provider_id("KITE", 256265) == nifty
    assert service.resolve_provider_id("KITE", "256265") == nifty
    assert service.resolve_provider_id("DHAN", "13") == nifty
    assert service.resolve_provider_id("KITE", 999999) is None


def test_8_duplicate_identical_registration_is_idempotent(service: InstrumentMasterService):
    nifty = CanonicalInstrument(
        canonical_id="IDX:NSE:NIFTY_50",
        symbol="NIFTY 50",
        exchange=Exchange.NSE,
        segment=Segment.INDEX,
        instrument_type=InstrumentType.INDEX,
        provider_ids={"KITE": 256265},
    )
    service.register(nifty)
    # Re-registering identical object must succeed without raising
    service.register(nifty)
    assert len(service.list_instruments()) == 1


def test_9_conflicting_canonical_registration_rejected(service: InstrumentMasterService):
    nifty1 = CanonicalInstrument(
        canonical_id="IDX:NSE:NIFTY_50",
        symbol="NIFTY 50",
        exchange=Exchange.NSE,
        segment=Segment.INDEX,
        instrument_type=InstrumentType.INDEX,
        lot_size=50,
    )
    nifty2 = CanonicalInstrument(
        canonical_id="IDX:NSE:NIFTY_50",
        symbol="NIFTY 50",
        exchange=Exchange.NSE,
        segment=Segment.INDEX,
        instrument_type=InstrumentType.INDEX,
        lot_size=75,  # Conflicting lot size
    )
    service.register(nifty1)
    with pytest.raises(ValueError, match="conflicting instrument already exists"):
        service.register(nifty2)


def test_10_provider_id_collision_rejected(service: InstrumentMasterService):
    inst1 = CanonicalInstrument(
        canonical_id="IDX:NSE:NIFTY_50",
        symbol="NIFTY 50",
        exchange=Exchange.NSE,
        segment=Segment.INDEX,
        instrument_type=InstrumentType.INDEX,
        provider_ids={"KITE": 256265},
    )
    inst2 = CanonicalInstrument(
        canonical_id="IDX:NSE:NIFTY_BANK",
        symbol="NIFTY BANK",
        exchange=Exchange.NSE,
        segment=Segment.INDEX,
        instrument_type=InstrumentType.INDEX,
        provider_ids={"KITE": 256265},  # Collision on provider token
    )
    service.register(inst1)
    with pytest.raises(ValueError, match="Provider ID collision"):
        service.register(inst2)


def test_11_valid_option_registration(service: InstrumentMasterService):
    opt = CanonicalInstrument(
        canonical_id="OPT:NFO:NIFTY:2026-09-03:24500:CE",
        symbol="NIFTY2690324500CE",
        exchange=Exchange.NFO,
        segment=Segment.OPTIONS,
        instrument_type=InstrumentType.CE,
        expiry=date(2026, 9, 3),
        strike=24500.0,
        option_type=OptionType.CE,
        provider_ids={"KITE": 12345},
    )
    service.register(opt)
    assert service.get_by_canonical_id("OPT:NFO:NIFTY:2026-09-03:24500:CE") == opt


def test_12_ce_and_pe_remain_distinct(service: InstrumentMasterService):
    ce = CanonicalInstrument(
        canonical_id="OPT:NFO:NIFTY:2026-09-03:24500:CE",
        symbol="NIFTY2690324500CE",
        exchange=Exchange.NFO,
        segment=Segment.OPTIONS,
        instrument_type=InstrumentType.CE,
        expiry=date(2026, 9, 3),
        strike=24500.0,
        option_type=OptionType.CE,
        provider_ids={"KITE": 12345},
    )
    pe = CanonicalInstrument(
        canonical_id="OPT:NFO:NIFTY:2026-09-03:24500:PE",
        symbol="NIFTY2690324500PE",
        exchange=Exchange.NFO,
        segment=Segment.OPTIONS,
        instrument_type=InstrumentType.PE,
        expiry=date(2026, 9, 3),
        strike=24500.0,
        option_type=OptionType.PE,
        provider_ids={"KITE": 12346},
    )
    service.register(ce)
    service.register(pe)

    assert service.get_by_canonical_id("OPT:NFO:NIFTY:2026-09-03:24500:CE") == ce
    assert service.get_by_canonical_id("OPT:NFO:NIFTY:2026-09-03:24500:PE") == pe
    assert ce != pe


def test_13_expiry_separation(service: InstrumentMasterService):
    opt_w1 = CanonicalInstrument(
        canonical_id="OPT:NFO:NIFTY:2026-09-03:24500:CE",
        symbol="NIFTY2690324500CE",
        exchange=Exchange.NFO,
        segment=Segment.OPTIONS,
        instrument_type=InstrumentType.CE,
        expiry=date(2026, 9, 3),
        strike=24500.0,
        option_type=OptionType.CE,
    )
    opt_w2 = CanonicalInstrument(
        canonical_id="OPT:NFO:NIFTY:2026-09-10:24500:CE",
        symbol="NIFTY2691024500CE",
        exchange=Exchange.NFO,
        segment=Segment.OPTIONS,
        instrument_type=InstrumentType.CE,
        expiry=date(2026, 9, 10),
        strike=24500.0,
        option_type=OptionType.CE,
    )
    service.register_many([opt_w1, opt_w2])
    assert service.get_available_expiries("NIFTY") == ["2026-09-03", "2026-09-10"]


def test_14_strike_separation(service: InstrumentMasterService):
    opt_24500 = CanonicalInstrument(
        canonical_id="OPT:NFO:NIFTY:2026-09-03:24500:CE",
        symbol="NIFTY2690324500CE",
        exchange=Exchange.NFO,
        segment=Segment.OPTIONS,
        instrument_type=InstrumentType.CE,
        expiry=date(2026, 9, 3),
        strike=24500.0,
        option_type=OptionType.CE,
    )
    opt_24600 = CanonicalInstrument(
        canonical_id="OPT:NFO:NIFTY:2026-09-03:24600:CE",
        symbol="NIFTY2690324600CE",
        exchange=Exchange.NFO,
        segment=Segment.OPTIONS,
        instrument_type=InstrumentType.CE,
        expiry=date(2026, 9, 3),
        strike=24600.0,
        option_type=OptionType.CE,
    )
    service.register_many([opt_24500, opt_24600])

    opts = service.find_options("NIFTY", expiry="2026-09-03")
    assert len(opts) == 2
    assert opts[0].strike == 24500.0
    assert opts[1].strike == 24600.0


def test_15_find_all_options_for_expiry(service: InstrumentMasterService):
    options = [
        CanonicalInstrument(
            canonical_id=f"OPT:NFO:NIFTY:2026-09-03:{s}:{t}",
            symbol=f"NIFTY26903{s}{t}",
            exchange=Exchange.NFO,
            segment=Segment.OPTIONS,
            instrument_type=getattr(InstrumentType, t),
            expiry=date(2026, 9, 3),
            strike=float(s),
            option_type=getattr(OptionType, t),
        )
        for s in [24400, 24500, 24600]
        for t in ["CE", "PE"]
    ]
    service.register_many(options)

    found = service.find_options("NIFTY", expiry="2026-09-03")
    assert len(found) == 6


def test_16_ce_only_filtering(service: InstrumentMasterService):
    options = [
        CanonicalInstrument(
            canonical_id=f"OPT:NFO:NIFTY:2026-09-03:{s}:{t}",
            symbol=f"NIFTY26903{s}{t}",
            exchange=Exchange.NFO,
            segment=Segment.OPTIONS,
            instrument_type=getattr(InstrumentType, t),
            expiry=date(2026, 9, 3),
            strike=float(s),
            option_type=getattr(OptionType, t),
        )
        for s in [24400, 24500, 24600]
        for t in ["CE", "PE"]
    ]
    service.register_many(options)

    ces = service.find_options("NIFTY", expiry="2026-09-03", option_type=OptionType.CE)
    assert len(ces) == 3
    assert all(c.option_type == OptionType.CE for c in ces)


def test_17_pe_only_filtering(service: InstrumentMasterService):
    options = [
        CanonicalInstrument(
            canonical_id=f"OPT:NFO:NIFTY:2026-09-03:{s}:{t}",
            symbol=f"NIFTY26903{s}{t}",
            exchange=Exchange.NFO,
            segment=Segment.OPTIONS,
            instrument_type=getattr(InstrumentType, t),
            expiry=date(2026, 9, 3),
            strike=float(s),
            option_type=getattr(OptionType, t),
        )
        for s in [24400, 24500, 24600]
        for t in ["CE", "PE"]
    ]
    service.register_many(options)

    pes = service.find_options("NIFTY", expiry="2026-09-03", option_type="PE")
    assert len(pes) == 3
    assert all(p.option_type == OptionType.PE for p in pes)


def test_18_strike_range_filtering(service: InstrumentMasterService):
    options = [
        CanonicalInstrument(
            canonical_id=f"OPT:NFO:NIFTY:2026-09-03:{s}:CE",
            symbol=f"NIFTY26903{s}CE",
            exchange=Exchange.NFO,
            segment=Segment.OPTIONS,
            instrument_type=InstrumentType.CE,
            expiry=date(2026, 9, 3),
            strike=float(s),
            option_type=OptionType.CE,
        )
        for s in [24200, 24300, 24400, 24500, 24600, 24700]
    ]
    service.register_many(options)

    ranged = service.find_options("NIFTY", expiry="2026-09-03", strike_min=24300, strike_max=24500)
    assert len(ranged) == 3
    assert [r.strike for r in ranged] == [24300.0, 24400.0, 24500.0]


def test_19_available_expiries_sorted(service: InstrumentMasterService):
    options = [
        CanonicalInstrument(
            canonical_id=f"OPT:NFO:NIFTY:{exp}:24500:CE",
            symbol=f"NIFTY{exp}24500CE",
            exchange=Exchange.NFO,
            segment=Segment.OPTIONS,
            instrument_type=InstrumentType.CE,
            expiry=exp,
            strike=24500.0,
            option_type=OptionType.CE,
        )
        for exp in ["2026-09-24", "2026-09-03", "2026-09-17", "2026-09-10"]
    ]
    service.register_many(options)

    expiries = service.get_available_expiries("NIFTY")
    assert expiries == ["2026-09-03", "2026-09-10", "2026-09-17", "2026-09-24"]


def test_20_nearest_expiry(service: InstrumentMasterService):
    options = [
        CanonicalInstrument(
            canonical_id=f"OPT:NFO:NIFTY:{exp}:24500:CE",
            symbol=f"NIFTY{exp}24500CE",
            exchange=Exchange.NFO,
            segment=Segment.OPTIONS,
            instrument_type=InstrumentType.CE,
            expiry=exp,
            strike=24500.0,
            option_type=OptionType.CE,
        )
        for exp in ["2026-09-03", "2026-09-10", "2026-09-17", "2026-09-24"]
    ]
    service.register_many(options)

    nearest = service.get_nearest_expiry("NIFTY", reference_date=date(2026, 9, 5))
    assert nearest == "2026-09-10"

    nearest_exact = service.get_nearest_expiry("NIFTY", reference_date="2026-09-03")
    assert nearest_exact == "2026-09-03"


def test_21_expired_instruments_not_returned_as_nearest_future_expiry(service: InstrumentMasterService):
    options = [
        CanonicalInstrument(
            canonical_id=f"OPT:NFO:NIFTY:{exp}:24500:CE",
            symbol=f"NIFTY{exp}24500CE",
            exchange=Exchange.NFO,
            segment=Segment.OPTIONS,
            instrument_type=InstrumentType.CE,
            expiry=exp,
            strike=24500.0,
            option_type=OptionType.CE,
        )
        for exp in ["2026-08-20", "2026-08-27"]
    ]
    service.register_many(options)

    # Reference date is 2026-09-01 (after both expiries)
    assert service.get_nearest_expiry("NIFTY", reference_date="2026-09-01") is None


def test_22_immutable_copy_safe_snapshot(service: InstrumentMasterService):
    nifty = CanonicalInstrument(
        canonical_id="IDX:NSE:NIFTY_50",
        symbol="NIFTY 50",
        exchange=Exchange.NSE,
        segment=Segment.INDEX,
        instrument_type=InstrumentType.INDEX,
    )
    service.register(nifty)

    snap = service.snapshot()
    assert snap["instruments_count"] == 1
    # Mutating returned dictionary must not affect service state
    snap["instruments"]["IDX:NSE:NIFTY_50"] = None
    assert service.get_by_canonical_id("IDX:NSE:NIFTY_50") == nifty


def test_23_thread_safe_concurrent_reads(service: InstrumentMasterService):
    nifty = CanonicalInstrument(
        canonical_id="IDX:NSE:NIFTY_50",
        symbol="NIFTY 50",
        exchange=Exchange.NSE,
        segment=Segment.INDEX,
        instrument_type=InstrumentType.INDEX,
    )
    service.register(nifty)

    errors = []

    def reader_worker():
        try:
            for _ in range(100):
                inst = service.resolve_symbol("NIFTY")
                if inst is None or inst.canonical_id != "IDX:NSE:NIFTY_50":
                    errors.append("Failed resolve_symbol")
                by_id = service.get_by_canonical_id("IDX:NSE:NIFTY_50")
                if by_id is None:
                    errors.append("Failed get_by_canonical_id")
        except Exception as ex:
            errors.append(str(ex))

    threads = [threading.Thread(target=reader_worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0


def test_24_ambiguous_alias_registration_rejected(service: InstrumentMasterService):
    nifty = CanonicalInstrument(
        canonical_id="IDX:NSE:NIFTY_50",
        symbol="NIFTY 50",
        exchange=Exchange.NSE,
        segment=Segment.INDEX,
        instrument_type=InstrumentType.INDEX,
    )
    service.register(nifty, aliases=["BENCHMARK"])

    banknifty = CanonicalInstrument(
        canonical_id="IDX:NSE:NIFTY_BANK",
        symbol="NIFTY BANK",
        exchange=Exchange.NSE,
        segment=Segment.INDEX,
        instrument_type=InstrumentType.INDEX,
    )
    # Attempting to assign existing alias "BENCHMARK" to a different canonical ID must raise ValueError
    with pytest.raises(ValueError, match="Alias collision"):
        service.register(banknifty, aliases=["BENCHMARK"])


def test_25_architectural_import_inspection():
    """Verifies that InstrumentMasterService does not import any broker/provider SDKs or runtime engines."""
    import src.market_data.services.instrument_master_service as ims_mod

    source = inspect.getsource(ims_mod)
    forbidden_modules = [
        "kiteconnect",
        "dhanhq",
        "src.broker",
        "src.controlled_execution",
        "src.proposal_engine",
        "src.server_bridge",
        "src.frontend",
    ]

    for forbidden in forbidden_modules:
        assert f"import {forbidden}" not in source, f"InstrumentMasterService violates architectural boundary with: import {forbidden}"
        assert f"from {forbidden}" not in source, f"InstrumentMasterService violates architectural boundary with: from {forbidden}"
