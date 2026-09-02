from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from src.market_data.models.canonical_instrument import CanonicalInstrument
from src.market_data.models.quality_enums import Exchange, InstrumentType, OptionType, Segment
from src.market_data.services.instrument_master_service import (
    InstrumentMasterService,
    build_canonical_id,
    normalize_strike,
)


class DhanInstrumentMapper:
    """
    Maps Dhan security master metadata records (CSV/JSON/API) into CanonicalInstruments
    and registers them into the InstrumentMasterService with provider ID mappings.
    """

    EXCHANGE_MAP = {
        "NSE": Exchange.NSE,
        "NFO": Exchange.NFO,
        "BSE": Exchange.BSE,
        "BFO": Exchange.BFO,
        "MCX": Exchange.MCX,
    }

    SEGMENT_MAP = {
        "IDX": Segment.INDEX,
        "INDEX": Segment.INDEX,
        "E": Segment.EQUITY,
        "EQ": Segment.EQUITY,
        "EQUITY": Segment.EQUITY,
        "D": Segment.OPTIONS,
        "F": Segment.FUTURES,
        "FNO": Segment.OPTIONS,
        "FUT": Segment.FUTURES,
        "OPT": Segment.OPTIONS,
        "FUTURES": Segment.FUTURES,
        "OPTIONS": Segment.OPTIONS,
    }

    def __init__(self, instrument_master: InstrumentMasterService) -> None:
        self.instrument_master = instrument_master

    def map_and_register(self, record: Dict[str, Any]) -> Optional[CanonicalInstrument]:
        """
        Parses a single Dhan instrument record and registers it into the master service.
        Record fields may include:
        security_id, exchange_segment, symbol, display_name, instrument_type, expiry, strike, option_type, lot_size, tick_size.
        """
        sec_id = str(record.get("security_id", "")).strip()
        if not sec_id:
            return None

        exch_seg_str = str(record.get("exchange_segment", record.get("exchange", "NSE"))).upper().strip()
        parts = exch_seg_str.split("_")
        raw_exch = parts[0] if parts else "NSE"
        raw_seg = parts[1] if len(parts) > 1 else ("INDEX" if "IDX" in exch_seg_str else "EQUITY")

        exchange = self.EXCHANGE_MAP.get(raw_exch, Exchange.NSE)
        segment = self.SEGMENT_MAP.get(raw_seg, Segment.EQUITY if exchange == Exchange.NSE else Segment.OPTIONS)

        raw_opt = str(record.get("option_type", "")).upper().strip()
        opt_type: Optional[OptionType] = None
        if raw_opt in ("CE", "CALL"):
            opt_type = OptionType.CE
        elif raw_opt in ("PE", "PUT"):
            opt_type = OptionType.PE

        raw_type = str(record.get("instrument_type", "")).upper().strip()
        if opt_type == OptionType.CE or "CE" in raw_type or "OPT" in raw_type and opt_type == OptionType.CE:
            inst_type = InstrumentType.CE
        elif opt_type == OptionType.PE or "PE" in raw_type or "OPT" in raw_type and opt_type == OptionType.PE:
            inst_type = InstrumentType.PE
        elif "FUT" in raw_type:
            inst_type = InstrumentType.FUT
            segment = Segment.FUTURES
        elif segment == Segment.INDEX or ("NIFTY" in str(record.get("symbol", "")).upper() and "IDX" in exch_seg_str):
            inst_type = InstrumentType.INDEX
            segment = Segment.INDEX
        else:
            inst_type = InstrumentType.EQUITY
            segment = Segment.EQUITY

        raw_symbol = str(record.get("symbol", record.get("display_name", ""))).strip()
        underlying = record.get("underlying_symbol", record.get("underlying", "NIFTY" if "NIFTY" in raw_symbol else None))
        if underlying:
            underlying = str(underlying).strip().upper()

        expiry_date: Optional[date] = None
        raw_exp = record.get("expiry_date", record.get("expiry"))
        if raw_exp:
            if isinstance(raw_exp, date):
                expiry_date = raw_exp
            elif isinstance(raw_exp, str) and raw_exp.strip():
                try:
                    expiry_date = datetime.strptime(raw_exp.strip()[:10], "%Y-%m-%d").date()
                except ValueError:
                    pass

        strike_val: Optional[float] = None
        raw_strike = record.get("strike_price", record.get("strike"))
        if raw_strike is not None:
            try:
                strike_val = float(raw_strike)
            except (ValueError, TypeError):
                pass

        if inst_type in (InstrumentType.CE, InstrumentType.PE, InstrumentType.FUT):
            if record.get("display_name"):
                symbol = str(record["display_name"]).strip()
            elif raw_symbol and raw_symbol != underlying:
                symbol = raw_symbol
            else:
                opt_str = "CE" if inst_type == InstrumentType.CE else ("PE" if inst_type == InstrumentType.PE else "FUT")
                strike_part = f"_{normalize_strike(strike_val)}" if strike_val else ""
                symbol = f"{underlying}_{str(expiry_date)[:10]}{strike_part}_{opt_str}"
        else:
            symbol = raw_symbol

        sym_or_und = underlying if (underlying and inst_type in (InstrumentType.CE, InstrumentType.PE, InstrumentType.FUT)) else symbol
        canonical_id = build_canonical_id(
            exchange=exchange,
            segment=segment,
            instrument_type=inst_type,
            symbol_or_underlying=sym_or_und,
            expiry=expiry_date,
            strike=strike_val,
            option_type=opt_type,
        )

        provider_ids = {"DHAN": sec_id}
        if "kite_token" in record:
            provider_ids["KITE"] = str(record["kite_token"])

        inst = CanonicalInstrument(
            canonical_id=canonical_id,
            symbol=symbol,
            exchange=exchange,
            segment=segment,
            instrument_type=inst_type,
            expiry=expiry_date,
            strike=strike_val,
            option_type=opt_type,
            lot_size=int(record.get("lot_size", 1)) if record.get("lot_size") else 1,
            tick_size=float(record.get("tick_size", 0.05)) if record.get("tick_size") else 0.05,
            provider_ids=provider_ids,
        )

        self.instrument_master.register(inst)
        return inst

    def register_default_universe(self) -> List[CanonicalInstrument]:
        """Registers essential NIFTY 50 and INDIA VIX default index instruments."""
        nifty_rec = {
            "security_id": "13",
            "exchange_segment": "NSE_IDX",
            "symbol": "NIFTY 50",
            "instrument_type": "INDEX",
        }
        vix_rec = {
            "security_id": "26009",
            "exchange_segment": "NSE_IDX",
            "symbol": "INDIA VIX",
            "instrument_type": "INDEX",
        }
        inst_nifty = self.map_and_register(nifty_rec)
        inst_vix = self.map_and_register(vix_rec)
        return [inst for inst in (inst_nifty, inst_vix) if inst is not None]
