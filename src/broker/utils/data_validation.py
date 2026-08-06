from __future__ import annotations
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger("MarketDataValidator")

@dataclass(frozen=True)
class DataValidationItem:
    field: str
    error_type: str  # "OHLC_INCONSISTENCY", "TIMESTAMP_ORDERING", "DUPLICATE_CANDLE", "MISSING_CANDLE", "NEGATIVE_VOLUME", "INVALID_PRICE", "EXPIRED_INSTRUMENT", "INVALID_TOKEN"
    message: str
    severity: str  # "ERROR", "WARNING"
    invalid_value: Any = None

@dataclass(frozen=True)
class MarketDataValidationReport:
    is_valid: bool
    errors: List[DataValidationItem] = field(default_factory=list)
    warnings: List[DataValidationItem] = field(default_factory=list)
    record_count: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

class MarketDataValidator:
    """
    Validates correctness and integrity of real-time quotes and historical candle data.
    """

    @classmethod
    def validate_quotes(cls, quotes: Dict[str, Any], instrument_service: Optional[Any] = None) -> MarketDataValidationReport:
        """
        Validates real-time quotes from Zerodha.
        """
        errors: List[DataValidationItem] = []
        warnings: List[DataValidationItem] = []
        record_count = len(quotes)

        for symbol, quote_data in quotes.items():
            token = quote_data.get("instrument_token")
            
            # Check invalid token
            if not token or token <= 0:
                errors.append(DataValidationItem(
                    field=f"{symbol}.instrument_token",
                    error_type="INVALID_TOKEN",
                    message=f"Symbol {symbol} has missing or invalid instrument token: {token}",
                    severity="ERROR",
                    invalid_value=token
                ))

            # Lookup instrument service for expiry or validity
            if instrument_service is not None and token:
                inst = instrument_service.lookup_instrument_by_token(token)
                if not inst:
                    errors.append(DataValidationItem(
                        field=f"{symbol}.instrument_token",
                        error_type="INVALID_TOKEN",
                        message=f"Token {token} for {symbol} not found in instrument master.",
                        severity="ERROR",
                        invalid_value=token
                    ))
                else:
                    # Check expired instrument
                    expiry_str = inst.get("expiry")
                    if expiry_str:
                        try:
                            # Parse YYYY-MM-DD or standard ISO date
                            expiry_dt = datetime.strptime(expiry_str[:10], "%Y-%m-%d").date()
                            if expiry_dt < datetime.now().date():
                                errors.append(DataValidationItem(
                                    field=f"{symbol}.expiry",
                                    error_type="EXPIRED_INSTRUMENT",
                                    message=f"Instrument {symbol} (token {token}) is expired since {expiry_str}.",
                                    severity="ERROR",
                                    invalid_value=expiry_str
                                ))
                        except Exception:
                            pass

            # Check prices
            last_price = quote_data.get("last_price", 0.0)
            if last_price <= 0.0:
                errors.append(DataValidationItem(
                    field=f"{symbol}.last_price",
                    error_type="INVALID_PRICE",
                    message=f"Last price for {symbol} is non-positive: {last_price}",
                    severity="ERROR",
                    invalid_value=last_price
                ))

            # Check volumes
            volume = quote_data.get("volume", 0)
            if volume < 0:
                errors.append(DataValidationItem(
                    field=f"{symbol}.volume",
                    error_type="NEGATIVE_VOLUME",
                    message=f"Volume for {symbol} is negative: {volume}",
                    severity="ERROR",
                    invalid_value=volume
                ))

            # Check OHLC
            ohlc = quote_data.get("ohlc", {})
            if ohlc:
                open_val = ohlc.get("open", 0.0)
                high_val = ohlc.get("high", 0.0)
                low_val = ohlc.get("low", 0.0)
                close_val = ohlc.get("close", 0.0)

                # Negative price check in OHLC
                for k, v in [("open", open_val), ("high", high_val), ("low", low_val), ("close", close_val)]:
                    if v <= 0.0:
                        errors.append(DataValidationItem(
                            field=f"{symbol}.ohlc.{k}",
                            error_type="INVALID_PRICE",
                            message=f"{k.capitalize()} price for {symbol} is non-positive: {v}",
                            severity="ERROR",
                            invalid_value=v
                        ))

                # Coherence check
                if high_val < low_val:
                    errors.append(DataValidationItem(
                        field=f"{symbol}.ohlc",
                        error_type="OHLC_INCONSISTENCY",
                        message=f"OHLC inconsistency for {symbol}: High ({high_val}) is less than Low ({low_val})",
                        severity="ERROR",
                        invalid_value={"high": high_val, "low": low_val}
                    ))
                if high_val < open_val or high_val < close_val:
                    errors.append(DataValidationItem(
                        field=f"{symbol}.ohlc",
                        error_type="OHLC_INCONSISTENCY",
                        message=f"OHLC inconsistency for {symbol}: High ({high_val}) is less than Open ({open_val}) or Close ({close_val})",
                        severity="ERROR",
                        invalid_value={"high": high_val, "open": open_val, "close": close_val}
                    ))
                if low_val > open_val or low_val > close_val:
                    errors.append(DataValidationItem(
                        field=f"{symbol}.ohlc",
                        error_type="OHLC_INCONSISTENCY",
                        message=f"OHLC inconsistency for {symbol}: Low ({low_val}) is greater than Open ({open_val}) or Close ({close_val})",
                        severity="ERROR",
                        invalid_value={"low": low_val, "open": open_val, "close": close_val}
                    ))

        is_valid = len(errors) == 0
        return MarketDataValidationReport(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            record_count=record_count
        )

    @classmethod
    def validate_historical_candles(
        cls,
        candles: List[Dict[str, Any]],
        instrument_token: int,
        instrument_service: Optional[Any] = None
    ) -> MarketDataValidationReport:
        """
        Validates a list of historical candles.
        """
        errors: List[DataValidationItem] = []
        warnings: List[DataValidationItem] = []
        record_count = len(candles)

        # Validate token
        if instrument_token <= 0:
            errors.append(DataValidationItem(
                field="instrument_token",
                error_type="INVALID_TOKEN",
                message=f"Instrument token is invalid: {instrument_token}",
                severity="ERROR",
                invalid_value=instrument_token
            ))

        if instrument_service is not None:
            inst = instrument_service.lookup_instrument_by_token(instrument_token)
            if not inst:
                errors.append(DataValidationItem(
                    field="instrument_token",
                    error_type="INVALID_TOKEN",
                    message=f"Token {instrument_token} not found in instrument master.",
                    severity="ERROR",
                    invalid_value=instrument_token
                ))

        if not candles:
            warnings.append(DataValidationItem(
                field="candles",
                error_type="MISSING_CANDLE",
                message="Historical candle list is empty.",
                severity="WARNING"
            ))
            return MarketDataValidationReport(is_valid=True, errors=errors, warnings=warnings, record_count=0)

        prev_timestamp: Optional[datetime] = None
        seen_timestamps = set()

        for idx, candle in enumerate(candles):
            date_val = candle.get("date") or candle.get("timestamp")
            
            # Parse datetime
            curr_timestamp: Optional[datetime] = None
            if isinstance(date_val, datetime):
                curr_timestamp = date_val
            elif date_val:
                try:
                    # Try ISO or standard datetime parse
                    curr_timestamp = datetime.fromisoformat(str(date_val).replace("Z", "+00:00"))
                except ValueError:
                    try:
                        curr_timestamp = datetime.strptime(str(date_val), "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        try:
                            curr_timestamp = datetime.strptime(str(date_val), "%Y-%m-%d")
                        except ValueError:
                            pass

            if not curr_timestamp:
                errors.append(DataValidationItem(
                    field=f"candles[{idx}].date",
                    error_type="TIMESTAMP_ORDERING",
                    message=f"Candle at index {idx} has unparseable timestamp: {date_val}",
                    severity="ERROR",
                    invalid_value=date_val
                ))
                continue

            # Check timestamp ordering
            if prev_timestamp and curr_timestamp <= prev_timestamp:
                errors.append(DataValidationItem(
                    field=f"candles[{idx}].date",
                    error_type="TIMESTAMP_ORDERING",
                    message=f"Timestamp ordering violation at index {idx}: {curr_timestamp} <= {prev_timestamp}",
                    severity="ERROR",
                    invalid_value={"current": curr_timestamp.isoformat(), "previous": prev_timestamp.isoformat()}
                ))

            # Check duplicate candles
            ts_key = curr_timestamp.isoformat()
            if ts_key in seen_timestamps:
                errors.append(DataValidationItem(
                    field=f"candles[{idx}].date",
                    error_type="DUPLICATE_CANDLE",
                    message=f"Duplicate candle timestamp found at index {idx}: {ts_key}",
                    severity="ERROR",
                    invalid_value=ts_key
                ))
            else:
                seen_timestamps.add(ts_key)

            # Check missing candles (unusual gaps > 1 day for non-weekends)
            if prev_timestamp:
                delta = curr_timestamp - prev_timestamp
                # Check for standard daily gaps or larger gaps. If gap is > 3 days, trigger warning
                if delta.days > 3:
                    warnings.append(DataValidationItem(
                        field=f"candles[{idx}].date",
                        error_type="MISSING_CANDLE",
                        message=f"Large gap in historical candles between {prev_timestamp} and {curr_timestamp} ({delta.days} days)",
                        severity="WARNING",
                        invalid_value={"current": curr_timestamp.isoformat(), "previous": prev_timestamp.isoformat()}
                    ))

            # Check OHLC values
            op = candle.get("open", 0.0)
            hp = candle.get("high", 0.0)
            lp = candle.get("low", 0.0)
            cp = candle.get("close", 0.0)

            for k, v in [("open", op), ("high", hp), ("low", lp), ("close", cp)]:
                if v <= 0.0:
                    errors.append(DataValidationItem(
                        field=f"candles[{idx}].{k}",
                        error_type="INVALID_PRICE",
                        message=f"Price {k} at index {idx} is non-positive: {v}",
                        severity="ERROR",
                        invalid_value=v
                    ))

            # Coherence
            if hp < lp:
                errors.append(DataValidationItem(
                    field=f"candles[{idx}]",
                    error_type="OHLC_INCONSISTENCY",
                    message=f"Candle high ({hp}) < low ({lp}) at index {idx}",
                    severity="ERROR",
                    invalid_value={"high": hp, "low": lp}
                ))
            if hp < op or hp < cp:
                errors.append(DataValidationItem(
                    field=f"candles[{idx}]",
                    error_type="OHLC_INCONSISTENCY",
                    message=f"Candle high ({hp}) is less than open ({op}) or close ({cp}) at index {idx}",
                    severity="ERROR",
                    invalid_value={"high": hp, "open": op, "close": cp}
                ))
            if lp > op or lp > cp:
                errors.append(DataValidationItem(
                    field=f"candles[{idx}]",
                    error_type="OHLC_INCONSISTENCY",
                    message=f"Candle low ({lp}) is greater than open ({op}) or close ({cp}) at index {idx}",
                    severity="ERROR",
                    invalid_value={"low": lp, "open": op, "close": cp}
                ))

            # Volume
            vol = candle.get("volume", 0)
            if vol < 0:
                errors.append(DataValidationItem(
                    field=f"candles[{idx}].volume",
                    error_type="NEGATIVE_VOLUME",
                    message=f"Candle volume is negative at index {idx}: {vol}",
                    severity="ERROR",
                    invalid_value=vol
                ))

            prev_timestamp = curr_timestamp

        is_valid = len(errors) == 0
        return MarketDataValidationReport(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            record_count=record_count
        )
