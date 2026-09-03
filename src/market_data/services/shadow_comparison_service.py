from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import math
from typing import Any, Dict, Optional


class ShadowComparisonStatus(str, Enum):
    MATCH = "MATCH"
    WITHIN_TOLERANCE = "WITHIN_TOLERANCE"
    SOURCE_NEWER = "SOURCE_NEWER"
    SOURCE_OLDER = "SOURCE_OLDER"
    SESSION_MISMATCH = "SESSION_MISMATCH"
    MISSING_OLD = "MISSING_OLD"
    MISSING_NEW = "MISSING_NEW"
    DIVERGED = "DIVERGED"


@dataclass(frozen=True)
class FieldComparison:
    field_name: str
    old_value: Any
    new_value: Any
    status: ShadowComparisonStatus
    difference: Optional[float] = None
    note: Optional[str] = None


@dataclass(frozen=True)
class ShadowComparisonReport:
    overall_status: ShadowComparisonStatus
    field_comparisons: Dict[str, FieldComparison] = field(default_factory=dict)
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ShadowComparisonService:
    """
    Compares Legacy runtime state vs Canonical New runtime state in shadow mode.
    Never automatically chooses a winner based solely on price difference.
    """

    def __init__(self, price_tolerance_pct: float = 0.05) -> None:
        self.price_tolerance_pct = price_tolerance_pct

    def compare_states(
        self,
        old_state: Dict[str, Any],
        new_state: Dict[str, Any],
    ) -> ShadowComparisonReport:
        """
        Evaluates equivalent fields across old and new runtimes.
        Fields compared:
          nifty_price, vix_price, session_date, market_phase, previous_close,
          nifty_open, nifty_high, nifty_low, tick_age_ms
        """
        comparisons: Dict[str, FieldComparison] = {}
        divergences = 0
        mismatches = 0

        # 1. Session Date
        old_sess = old_state.get("session_date")
        new_sess = new_state.get("session_date")
        if old_sess and new_sess:
            if str(old_sess)[:10] == str(new_sess)[:10]:
                comparisons["session_date"] = FieldComparison("session_date", old_sess, new_sess, ShadowComparisonStatus.MATCH)
            else:
                comparisons["session_date"] = FieldComparison("session_date", old_sess, new_sess, ShadowComparisonStatus.SESSION_MISMATCH)
                mismatches += 1
        elif not old_sess and new_sess:
            comparisons["session_date"] = FieldComparison("session_date", None, new_sess, ShadowComparisonStatus.MISSING_OLD)
        elif old_sess and not new_sess:
            comparisons["session_date"] = FieldComparison("session_date", old_sess, None, ShadowComparisonStatus.MISSING_NEW)

        # 2. NIFTY Price
        comparisons["nifty_price"] = self._compare_numeric("nifty_price", old_state.get("nifty_price"), new_state.get("nifty_price"))

        # 3. INDIA VIX Price
        comparisons["vix_price"] = self._compare_numeric("vix_price", old_state.get("vix_price"), new_state.get("vix_price"))

        # 4. Previous Close
        comparisons["previous_close"] = self._compare_numeric("previous_close", old_state.get("previous_close"), new_state.get("previous_close"))

        # 5. OHLC comparison
        for ohlc_field in ("nifty_open", "nifty_high", "nifty_low"):
            comparisons[ohlc_field] = self._compare_numeric(ohlc_field, old_state.get(ohlc_field), new_state.get(ohlc_field))

        # Overall Status Resolution
        statuses = [c.status for c in comparisons.values()]
        if ShadowComparisonStatus.SESSION_MISMATCH in statuses:
            overall = ShadowComparisonStatus.SESSION_MISMATCH
        elif ShadowComparisonStatus.DIVERGED in statuses:
            overall = ShadowComparisonStatus.DIVERGED
        elif ShadowComparisonStatus.WITHIN_TOLERANCE in statuses:
            overall = ShadowComparisonStatus.WITHIN_TOLERANCE
        elif all(s == ShadowComparisonStatus.MATCH for s in statuses):
            overall = ShadowComparisonStatus.MATCH
        elif ShadowComparisonStatus.MISSING_OLD in statuses or ShadowComparisonStatus.MISSING_NEW in statuses:
            overall = ShadowComparisonStatus.WITHIN_TOLERANCE
        else:
            overall = ShadowComparisonStatus.MATCH

        return ShadowComparisonReport(
            overall_status=overall,
            field_comparisons=comparisons,
            evaluated_at=datetime.now(timezone.utc),
        )

    def _compare_numeric(self, name: str, old_val: Optional[float], new_val: Optional[float]) -> FieldComparison:
        if old_val is None and new_val is None:
            return FieldComparison(name, None, None, ShadowComparisonStatus.MATCH)
        if old_val is None:
            return FieldComparison(name, None, new_val, ShadowComparisonStatus.MISSING_OLD)
        if new_val is None:
            return FieldComparison(name, old_val, None, ShadowComparisonStatus.MISSING_NEW)

        try:
            o_f = float(old_val)
            n_f = float(new_val)
        except (ValueError, TypeError):
            return FieldComparison(name, old_val, new_val, ShadowComparisonStatus.DIVERGED)

        diff = round(abs(n_f - o_f), 4)
        if diff == 0.0:
            return FieldComparison(name, o_f, n_f, ShadowComparisonStatus.MATCH, difference=0.0)

        # Check tolerance percentage
        base = o_f if o_f != 0 else n_f
        pct_diff = (diff / abs(base)) * 100.0 if base != 0 else 0.0

        if pct_diff <= self.price_tolerance_pct:
            return FieldComparison(name, o_f, n_f, ShadowComparisonStatus.WITHIN_TOLERANCE, difference=diff)
        else:
            return FieldComparison(name, o_f, n_f, ShadowComparisonStatus.DIVERGED, difference=diff)
