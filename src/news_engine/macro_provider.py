# src/news_engine/macro_provider.py
"""
BaseMacroProvider — abstract base class for macro data providers.

Features:
  - 4-state circuit breaker: closed -> open -> half_open -> recovery/open
  - Exponential backoff with testable jitter
  - ETag / Last-Modified caching
  - File persistence state serialization (get_state / restore_state)
  - Provider Health diagnostics
"""
from __future__ import annotations

import abc
import random
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.models.news_context_v2 import ProviderHealth

_OPEN_THRESHOLD = 3


class BaseMacroProvider(abc.ABC):
    """
    Abstract base class for macro data ingestion providers.
    """

    def __init__(
        self,
        provider_name: str,
        refresh_interval: float = 300.0,
        is_enabled: bool = True,
        jitter_seed: Optional[int] = None,
    ) -> None:
        self.provider_name = provider_name
        self.refresh_interval = refresh_interval
        self.is_enabled = is_enabled
        self.jitter_seed = jitter_seed

        self.status = "ready"  # ready | degraded | unavailable | stale | blocked
        self.last_successful_fetch: Optional[str] = None
        self.last_attempted_fetch: Optional[str] = None
        self.item_count: int = 0
        self.error_count: int = 0
        self.operational_error_reason: Optional[str] = None
        self.failure_detail: Optional[str] = None
        self.next_retry_at: Optional[str] = None

        self.etags: Dict[str, str] = {}
        self.last_modified_headers: Dict[str, str] = {}
        self.cached_raw_data: List[Dict[str, Any]] = []

        self.cb_state: str = "closed"  # closed | open | half_open
        self.consecutive_failures: int = 0
        self.circuit_open_until: float = 0.0
        self.last_fetch_timestamp: float = 0.0

    def _transition_to_open(self, backoff: float) -> None:
        self.cb_state = "open"
        self.circuit_open_until = time.time() + backoff
        retry_dt = datetime.fromtimestamp(self.circuit_open_until, timezone.utc)
        self.next_retry_at = retry_dt.isoformat().replace("+00:00", "Z")

    def _transition_to_half_open(self) -> None:
        self.cb_state = "half_open"
        self.next_retry_at = None

    def _transition_to_closed(self) -> None:
        self.cb_state = "closed"
        self.consecutive_failures = 0
        self.circuit_open_until = 0.0
        self.next_retry_at = None

    def should_fetch(self) -> bool:
        if not self.is_enabled:
            return False

        now = time.time()
        if self.cb_state == "closed":
            return (now - self.last_fetch_timestamp) >= self.refresh_interval

        if self.cb_state == "open":
            if now >= self.circuit_open_until:
                self._transition_to_half_open()
                return True
            return False

        if self.cb_state == "half_open":
            return True

        return False

    def record_success(self, items: List[Dict[str, Any]]) -> None:
        now_str = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self.status = "ready" if items else "unavailable"
        self.last_successful_fetch = now_str
        self.last_attempted_fetch = now_str
        self.item_count = len(items)
        self.operational_error_reason = None if items else "no_usable_records"
        self.failure_detail = None if items else "HTTP succeeded but produced zero valid usable records."
        self.cached_raw_data = list(items)
        self.last_fetch_timestamp = time.time()
        self._transition_to_closed()

    def record_failure(self, exc: Exception) -> None:
        now_str = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self.consecutive_failures += 1
        self.error_count += 1
        self.last_attempted_fetch = now_str
        self.last_fetch_timestamp = time.time()

        exc_str = str(exc).lower()
        self.failure_detail = str(exc)[:300]
        if "timeout" in exc_str:
            self.operational_error_reason = "timeout"
        elif "rate" in exc_str or "429" in exc_str:
            self.operational_error_reason = "rate_limited"
        elif "xml" in exc_str or "json" in exc_str or "parse" in exc_str:
            self.operational_error_reason = "parse_error"
        else:
            self.operational_error_reason = "connection_error"

        # Deterministic testable jitter
        if self.jitter_seed is not None:
            jitter = (self.jitter_seed % 5)
        else:
            jitter = random.uniform(0, 5)

        backoff = min(3600.0, (2.0 ** self.consecutive_failures) * 10.0 + jitter)

        if self.cb_state in ("closed", "half_open"):
            if self.consecutive_failures >= _OPEN_THRESHOLD or self.cb_state == "half_open":
                self.status = "unavailable"
                self._transition_to_open(backoff)
            else:
                self.status = "degraded"
        elif self.cb_state == "open":
            self._transition_to_open(backoff)
            self.status = "unavailable"

    def get_state(self) -> Dict[str, Any]:
        return {
            "provider_name": self.provider_name,
            "status": self.status,
            "last_successful_fetch": self.last_successful_fetch,
            "last_attempted_fetch": self.last_attempted_fetch,
            "item_count": self.item_count,
            "error_count": self.error_count,
            "operational_error_reason": self.operational_error_reason,
            "failure_detail": self.failure_detail,
            "next_retry_at": self.next_retry_at,
            "etags": self.etags,
            "last_modified_headers": self.last_modified_headers,
            "cached_raw_data": self.cached_raw_data,
            "cb_state": self.cb_state,
            "consecutive_failures": self.consecutive_failures,
            "circuit_open_until": self.circuit_open_until,
            "last_fetch_timestamp": self.last_fetch_timestamp,
        }

    def restore_state(self, state: Dict[str, Any]) -> None:
        if not state:
            return
        for attr in (
            "status", "last_successful_fetch", "last_attempted_fetch",
            "item_count", "error_count", "operational_error_reason", "failure_detail",
            "next_retry_at", "etags", "last_modified_headers",
            "cached_raw_data", "cb_state", "consecutive_failures",
            "circuit_open_until", "last_fetch_timestamp",
        ):
            if attr in state:
                setattr(self, attr, state[attr])

    def get_health(self) -> ProviderHealth:
        return ProviderHealth(
            provider_name=self.provider_name,
            status=self.status,
            last_successful_fetch=self.last_successful_fetch,
            last_attempted_fetch=self.last_attempted_fetch,
            item_count=self.item_count,
            error_count=self.error_count,
            operational_error_reason=self.operational_error_reason,
            failure_detail=self.failure_detail,
            next_retry_at=self.next_retry_at,
            is_enabled=self.is_enabled,
        )

    @abc.abstractmethod
    def fetch_raw_data(self) -> List[Dict[str, Any]]:
        pass
