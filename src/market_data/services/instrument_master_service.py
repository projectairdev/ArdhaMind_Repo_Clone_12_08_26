from __future__ import annotations

import re
import threading
from datetime import date, datetime
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

from src.market_data.models.canonical_instrument import CanonicalInstrument
from src.market_data.models.quality_enums import Exchange, InstrumentType, OptionType, Segment


def normalize_strike(strike: float | int) -> str:
    """Formats strike price deterministically without trailing decimal zeros if whole."""
    val = float(strike)
    if val.is_integer():
        return str(int(val))
    return f"{val:.2f}"


def build_canonical_id(
    exchange: Exchange | str,
    segment: Segment | str,
    instrument_type: InstrumentType | str,
    symbol_or_underlying: str,
    expiry: Optional[date | str] = None,
    strike: Optional[float | int] = None,
    option_type: Optional[OptionType | str] = None,
) -> str:
    """
    Constructs a deterministic, provider-independent canonical instrument ID.
    Examples:
      - IDX:NSE:NIFTY_50
      - IDX:NSE:INDIA_VIX
      - FUT:NFO:NIFTY:2026-09-24
      - OPT:NFO:NIFTY:2026-09-03:24300:CE
    """
    exc_str = str(exchange.value if hasattr(exchange, "value") else exchange).upper().strip()
    seg_str = str(segment.value if hasattr(segment, "value") else segment).upper().strip()
    itype_str = str(instrument_type.value if hasattr(instrument_type, "value") else instrument_type).upper().strip()
    clean_sym = re.sub(r"[\s\-]+", "_", symbol_or_underlying.upper().strip())

    if itype_str == "INDEX" or seg_str == "INDEX":
        return f"IDX:{exc_str}:{clean_sym}"
    elif itype_str in ("FUT", "FUTURES") or seg_str == "FUTURES":
        exp_str = str(expiry)[:10] if expiry else "UNKNOWN"
        return f"FUT:{exc_str}:{clean_sym}:{exp_str}"
    elif itype_str in ("CE", "PE", "OPT", "OPTIONS") or seg_str == "OPTIONS":
        exp_str = str(expiry)[:10] if expiry else "UNKNOWN"
        stk_str = normalize_strike(strike) if strike is not None else "0"
        opt_str = str(option_type.value if hasattr(option_type, "value") else (option_type or itype_str)).upper().strip()
        return f"OPT:{exc_str}:{clean_sym}:{exp_str}:{stk_str}:{opt_str}"
    else:
        return f"EQ:{exc_str}:{clean_sym}"


def _normalize_alias_key(alias: str) -> str:
    """Normalizes raw user or broker symbol strings for deterministic alias matching."""
    s = alias.strip().upper()
    # Remove leading exchange prefixes if formatted like NSE: or NFO:
    if s.startswith("NSE:") or s.startswith("NFO:") or s.startswith("BSE:") or s.startswith("MCX:"):
        s = s.split(":", 1)[1].strip()
    # Normalize spaces and underscores
    s = re.sub(r"[\s_]+", "", s)
    return s


class InstrumentMasterService:
    """
    Thread-safe in-memory authority for canonical instrument identity,
    alias normalization, provider mappings, and options discovery.
    """

    # Built-in deterministic standard index aliases
    DEFAULT_INDEX_ALIASES: Dict[str, str] = {
        "NIFTY": "IDX:NSE:NIFTY_50",
        "NIFTY50": "IDX:NSE:NIFTY_50",
        "NIFTY 50": "IDX:NSE:NIFTY_50",
        "NSE:NIFTY 50": "IDX:NSE:NIFTY_50",
        "NSE:NIFTY50": "IDX:NSE:NIFTY_50",
        "INDIA VIX": "IDX:NSE:INDIA_VIX",
        "INDIAVIX": "IDX:NSE:INDIA_VIX",
        "NSE:INDIA VIX": "IDX:NSE:INDIA_VIX",
        "NSE:INDIAVIX": "IDX:NSE:INDIA_VIX",
        "BANKNIFTY": "IDX:NSE:NIFTY_BANK",
        "NIFTY BANK": "IDX:NSE:NIFTY_BANK",
        "NSE:NIFTY BANK": "IDX:NSE:NIFTY_BANK",
        "NSE:BANKNIFTY": "IDX:NSE:NIFTY_BANK",
        "FINNIFTY": "IDX:NSE:NIFTY_FIN_SERVICE",
        "NIFTY FIN SERVICE": "IDX:NSE:NIFTY_FIN_SERVICE",
        "NSE:NIFTY FIN SERVICE": "IDX:NSE:NIFTY_FIN_SERVICE",
        "MIDCPNIFTY": "IDX:NSE:NIFTY_MID_SELECT",
        "NIFTY MID SELECT": "IDX:NSE:NIFTY_MID_SELECT",
        "NSE:NIFTY MID SELECT": "IDX:NSE:NIFTY_MID_SELECT",
    }

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._by_id: Dict[str, CanonicalInstrument] = {}
        self._by_symbol: Dict[str, str] = {}  # symbol -> canonical_id
        self._aliases: Dict[str, str] = {}   # normalized_alias -> canonical_id
        self._provider_map: Dict[Tuple[str, str], str] = {}  # (provider, provider_id_str) -> canonical_id
        self._options_by_underlying: Dict[str, List[str]] = {}  # underlying -> list of canonical_ids

        # Load default aliases
        for alias, cid in self.DEFAULT_INDEX_ALIASES.items():
            norm = _normalize_alias_key(alias)
            self._aliases[norm] = cid

    def register(
        self,
        instrument: CanonicalInstrument,
        aliases: Optional[Sequence[str]] = None,
    ) -> None:
        """
        Registers a CanonicalInstrument into the master registry.
        Idempotent if registered again with identical data.
        Raises ValueError on conflicting metadata, provider collisions, or alias collisions.
        """
        with self._lock:
            cid = instrument.canonical_id

            # 1. Check existing canonical ID
            if cid in self._by_id:
                existing = self._by_id[cid]
                if existing == instrument:
                    # Idempotent re-registration of exact instrument
                    pass
                else:
                    raise ValueError(
                        f"Cannot register '{cid}': conflicting instrument already exists with different metadata. "
                        f"Existing: {existing}, New: {instrument}"
                    )
            else:
                self._by_id[cid] = instrument

            # 2. Map primary tradingsymbol
            sym_key = instrument.symbol.strip().upper()
            if sym_key in self._by_symbol and self._by_symbol[sym_key] != cid:
                raise ValueError(
                    f"Symbol collision: '{sym_key}' is already mapped to '{self._by_symbol[sym_key]}', "
                    f"cannot re-map to '{cid}'."
                )
            self._by_symbol[sym_key] = cid

            # Also register normalized symbol as an alias
            norm_sym = _normalize_alias_key(instrument.symbol)
            if norm_sym in self._aliases and self._aliases[norm_sym] != cid:
                # If it matches a default index alias to the same target, allow
                if self._aliases[norm_sym] == cid:
                    pass
                else:
                    raise ValueError(
                        f"Symbol alias collision: normalized '{norm_sym}' is already registered to "
                        f"'{self._aliases[norm_sym]}', cannot re-map to '{cid}'."
                    )
            self._aliases[norm_sym] = cid

            # 3. Register custom aliases
            if aliases:
                for a in aliases:
                    if not a or not isinstance(a, str):
                        continue
                    norm_a = _normalize_alias_key(a)
                    if norm_a in self._aliases and self._aliases[norm_a] != cid:
                        raise ValueError(
                            f"Alias collision: '{a}' (normalized '{norm_a}') is already registered to "
                            f"'{self._aliases[norm_a]}', cannot re-map to '{cid}'."
                        )
                    self._aliases[norm_a] = cid

            # 4. Map provider IDs
            for prov, prov_data in (instrument.provider_ids or {}).items():
                prov_upper = str(prov).upper().strip()
                if isinstance(prov_data, (int, str, float)):
                    val_str = str(prov_data).strip()
                    pkey = (prov_upper, val_str)
                    if pkey in self._provider_map and self._provider_map[pkey] != cid:
                        raise ValueError(
                            f"Provider ID collision: ({prov_upper}, '{val_str}') already mapped to "
                            f"'{self._provider_map[pkey]}', cannot re-map to '{cid}'."
                        )
                    self._provider_map[pkey] = cid
                elif isinstance(prov_data, (dict, Mapping)):
                    for sub_k, sub_v in prov_data.items():
                        v_str = str(sub_v).strip()
                        # Register both with sub-key and direct value
                        pkey_sub = (prov_upper, f"{sub_k}:{v_str}")
                        if pkey_sub in self._provider_map and self._provider_map[pkey_sub] != cid:
                            raise ValueError(
                                f"Provider ID collision: ({prov_upper}, '{sub_k}:{v_str}') already mapped to "
                                f"'{self._provider_map[pkey_sub]}', cannot re-map to '{cid}'."
                            )
                        self._provider_map[pkey_sub] = cid
                        # Direct value registration
                        pkey_val = (prov_upper, v_str)
                        if pkey_val in self._provider_map and self._provider_map[pkey_val] != cid:
                            raise ValueError(
                                f"Provider ID collision: ({prov_upper}, '{v_str}') already mapped to "
                                f"'{self._provider_map[pkey_val]}', cannot re-map to '{cid}'."
                            )
                        self._provider_map[pkey_val] = cid

            # 5. Index options by underlying
            inst_type_str = str(
                instrument.instrument_type.value
                if hasattr(instrument.instrument_type, "value")
                else instrument.instrument_type
            ).upper()
            seg_str = str(
                instrument.segment.value
                if hasattr(instrument.segment, "value")
                else instrument.segment
            ).upper()
            if inst_type_str in ("CE", "PE", "OPT", "OPTIONS") or seg_str == "OPTIONS":
                # Extract underlying root (e.g. from OPT:NFO:NIFTY:... -> NIFTY)
                parts = cid.split(":")
                underlying = parts[2] if len(parts) > 2 else instrument.symbol
                underlying_key = underlying.upper().strip()
                if underlying_key not in self._options_by_underlying:
                    self._options_by_underlying[underlying_key] = []
                if cid not in self._options_by_underlying[underlying_key]:
                    self._options_by_underlying[underlying_key].append(cid)

    def register_many(self, instruments: Sequence[CanonicalInstrument]) -> None:
        """Atomically registers multiple CanonicalInstruments."""
        with self._lock:
            for inst in instruments:
                self.register(inst)

    def get_by_canonical_id(self, canonical_id: str) -> Optional[CanonicalInstrument]:
        """Retrieves a CanonicalInstrument by exact canonical ID."""
        with self._lock:
            return self._by_id.get(canonical_id.strip())

    def resolve_symbol(
        self,
        symbol: str,
        exchange: Optional[Exchange | str] = None,
        segment: Optional[Segment | str] = None,
    ) -> Optional[CanonicalInstrument]:
        """
        Resolves a symbol or alias string to its CanonicalInstrument.
        Supports exact symbols, normalized aliases, and built-in indices.
        """
        if not symbol or not isinstance(symbol, str):
            return None

        with self._lock:
            # 1. Exact canonical ID match
            if symbol in self._by_id:
                return self._by_id[symbol]

            # 2. Exact symbol match
            sym_key = symbol.strip().upper()
            if sym_key in self._by_symbol:
                cid = self._by_symbol[sym_key]
                return self._by_id.get(cid)

            # 3. Normalized alias match
            norm_key = _normalize_alias_key(symbol)
            if norm_key in self._aliases:
                cid = self._aliases[norm_key]
                return self._by_id.get(cid)

            # 4. Optional exchange / segment qualified match
            if exchange or segment:
                exc_val = str(exchange.value if hasattr(exchange, "value") else exchange).upper() if exchange else None
                seg_val = str(segment.value if hasattr(segment, "value") else segment).upper() if segment else None
                for inst in self._by_id.values():
                    if inst.symbol.upper() == sym_key:
                        inst_exc = str(inst.exchange.value if hasattr(inst.exchange, "value") else inst.exchange).upper()
                        inst_seg = str(inst.segment.value if hasattr(inst.segment, "value") else inst.segment).upper()
                        if (not exc_val or inst_exc == exc_val) and (not seg_val or inst_seg == seg_val):
                            return inst

            return None

    def resolve_provider_id(self, provider: str, provider_id: Any) -> Optional[CanonicalInstrument]:
        """
        Resolves a provider-specific token or security ID to its CanonicalInstrument.
        Example: resolve_provider_id("KITE", 256265) -> CanonicalInstrument(IDX:NSE:NIFTY_50)
        """
        if provider is None or provider_id is None:
            return None

        prov_upper = str(provider).upper().strip()
        val_str = str(provider_id).strip()

        with self._lock:
            cid = self._provider_map.get((prov_upper, val_str))
            if cid:
                return self._by_id.get(cid)
            return None

    def get_by_provider_id(self, provider: str, provider_id: Any) -> Optional[CanonicalInstrument]:
        """Convenience alias for resolve_provider_id."""
        return self.resolve_provider_id(provider, provider_id)

    def get_provider_id(self, canonical_id: str, provider: str) -> Optional[Any]:
        """
        Returns the provider-specific ID dictionary or scalar mapped to the given canonical ID.
        """
        if not canonical_id or not provider:
            return None

        with self._lock:
            inst = self._by_id.get(canonical_id.strip())
            if not inst or not inst.provider_ids:
                return None

            prov_upper = str(provider).upper().strip()
            for k, v in inst.provider_ids.items():
                if k.upper().strip() == prov_upper:
                    return v
            return None

    def list_instruments(self) -> List[CanonicalInstrument]:
        """Returns a snapshot list of all registered CanonicalInstruments."""
        with self._lock:
            return list(self._by_id.values())

    def find_options(
        self,
        underlying: str,
        expiry: Optional[date | str] = None,
        option_type: Optional[OptionType | str] = None,
        strike_min: Optional[float] = None,
        strike_max: Optional[float] = None,
    ) -> List[CanonicalInstrument]:
        """
        Finds registered option contracts matching criteria.
        Returns results sorted deterministically by (expiry, strike, option_type).
        """
        if not underlying:
            return []

        u_key = underlying.upper().strip()
        exp_str = str(expiry)[:10] if expiry else None
        opt_type_str = str(option_type.value if hasattr(option_type, "value") else option_type).upper() if option_type else None

        with self._lock:
            cids = self._options_by_underlying.get(u_key, [])
            results = []
            for cid in cids:
                inst = self._by_id.get(cid)
                if not inst:
                    continue

                # Filter Expiry
                if exp_str is not None:
                    inst_exp = str(inst.expiry)[:10] if inst.expiry else ""
                    if inst_exp != exp_str:
                        continue

                # Filter Option Type
                if opt_type_str is not None:
                    inst_opt = str(inst.option_type.value if hasattr(inst.option_type, "value") else inst.option_type).upper()
                    if inst_opt != opt_type_str:
                        continue

                # Filter Strike Range
                if inst.strike is not None:
                    if strike_min is not None and inst.strike < strike_min:
                        continue
                    if strike_max is not None and inst.strike > strike_max:
                        continue

                results.append(inst)

            # Deterministic sorting: (expiry ASC, strike ASC, option_type ASC)
            results.sort(
                key=lambda x: (
                    str(x.expiry or ""),
                    float(x.strike or 0.0),
                    str(x.option_type or ""),
                )
            )
            return results

    def get_available_expiries(self, underlying: str) -> List[str]:
        """
        Returns a sorted unique list of YYYY-MM-DD expiry strings for the given underlying.
        """
        if not underlying:
            return []

        u_key = underlying.upper().strip()
        with self._lock:
            cids = self._options_by_underlying.get(u_key, [])
            expiries: Set[str] = set()
            for cid in cids:
                inst = self._by_id.get(cid)
                if inst and inst.expiry:
                    expiries.add(str(inst.expiry)[:10])

            return sorted(list(expiries))

    def get_nearest_expiry(
        self,
        underlying: str,
        reference_date: date | str,
    ) -> Optional[str]:
        """
        Returns the earliest registered expiry >= reference_date.
        Expired dates prior to reference_date are excluded.
        """
        if not underlying or reference_date is None:
            return None

        ref_str = str(reference_date)[:10]
        expiries = self.get_available_expiries(underlying)
        for exp in expiries:
            if exp >= ref_str:
                return exp
        return None

    def snapshot(self) -> Dict[str, Any]:
        """
        Returns an immutable / copy-safe snapshot of all internal mappings for testing or diagnostics.
        """
        with self._lock:
            return {
                "instruments_count": len(self._by_id),
                "symbols_count": len(self._by_symbol),
                "aliases_count": len(self._aliases),
                "provider_mappings_count": len(self._provider_map),
                "underlying_options_tracked": list(self._options_by_underlying.keys()),
                "instruments": {cid: inst for cid, inst in self._by_id.items()},
                "aliases": dict(self._aliases),
            }
