from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from types import MappingProxyType
from typing import Any, Mapping, Optional

from src.market_data.models.quality_enums import Exchange, Segment, InstrumentType, OptionType


@dataclass(frozen=True)
class CanonicalInstrument:
    """
    Immutable, provider-independent representation of a tradable or index instrument.
    Provider IDs (Kite token, Dhan security ID) are stored strictly as metadata.
    """
    canonical_id: str
    symbol: str
    exchange: Exchange | str
    segment: Segment | str
    instrument_type: InstrumentType | str
    expiry: Optional[date | str] = None
    strike: Optional[float] = None
    option_type: Optional[OptionType | str] = None
    lot_size: int = 1
    tick_size: float = 0.05
    provider_ids: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.canonical_id or not isinstance(self.canonical_id, str) or not self.canonical_id.strip():
            raise ValueError("CanonicalInstrument 'canonical_id' must be a non-empty string.")
        if not self.symbol or not isinstance(self.symbol, str) or not self.symbol.strip():
            raise ValueError("CanonicalInstrument 'symbol' must be a non-empty string.")
        if not self.exchange:
            raise ValueError("CanonicalInstrument 'exchange' is required.")
        if not self.segment:
            raise ValueError("CanonicalInstrument 'segment' is required.")
        if not self.instrument_type:
            raise ValueError("CanonicalInstrument 'instrument_type' is required.")
        if not isinstance(self.lot_size, int) or self.lot_size <= 0:
            raise ValueError("CanonicalInstrument 'lot_size' must be a positive integer.")
        if not isinstance(self.tick_size, (int, float)) or self.tick_size <= 0:
            raise ValueError("CanonicalInstrument 'tick_size' must be a positive number.")

        # Ensure provider_ids is immutable mapping
        if not isinstance(self.provider_ids, MappingProxyType):
            object.__setattr__(self, "provider_ids", MappingProxyType(dict(self.provider_ids or {})))

        # Validate Option instruments
        inst_type_str = str(self.instrument_type.value if hasattr(self.instrument_type, "value") else self.instrument_type).upper()
        seg_str = str(self.segment.value if hasattr(self.segment, "value") else self.segment).upper()
        is_option = inst_type_str in ("CE", "PE", "OPT", "OPTIONS") or seg_str == "OPTIONS"

        if is_option:
            if self.expiry is None:
                raise ValueError(f"Option instrument '{self.canonical_id}' requires 'expiry'.")
            if self.strike is None or not isinstance(self.strike, (int, float)) or self.strike <= 0:
                raise ValueError(f"Option instrument '{self.canonical_id}' requires a positive numeric 'strike'.")
            if self.option_type is None:
                raise ValueError(f"Option instrument '{self.canonical_id}' requires 'option_type' ('CE' or 'PE').")
            opt_type_str = str(self.option_type.value if hasattr(self.option_type, "value") else self.option_type).upper()
            if opt_type_str not in ("CE", "PE"):
                raise ValueError(f"Option instrument '{self.canonical_id}' invalid option_type '{self.option_type}'. Expected 'CE' or 'PE'.")
