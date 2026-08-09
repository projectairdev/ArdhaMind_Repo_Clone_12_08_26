# src/news_engine/provider.py
"""
BaseNewsProvider — abstract base for all news ingestion providers.

Circuit-breaker lifecycle:
  closed    → normal operation
  open      → blocked after consecutive_failures >= OPEN_THRESHOLD
  half_open → single probe allowed after circuit_open_until has elapsed
  closed    → recovery after probe succeeds
  open      → returns to open if probe fails

Persistence:
  Providers expose get_state() / restore_state(dict) so the pipeline can
  persist and reload ETag, Last-Modified, last_successful_fetch,
  item_count, cached items, and circuit state across restarts.
"""
from __future__ import annotations

import abc
import random
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.models.news_context_v2 import ProviderHealth


# Number of consecutive failures required to trip the breaker to open state
_OPEN_THRESHOLD = 3
# In half-open, one probe is allowed; how many seconds before next half-open probe
_HALF_OPEN_MIN_WAIT = 30.0


class BaseNewsProvider(abc.ABC):
    """
    Abstract base class for news ingestion providers.

    Circuit-breaker states:
      "closed"    — healthy, fetching normally
      "open"      — blocked, no fetches until circuit_open_until elapses
      "half_open" — one probe fetch in flight or about to be tried
    """

    def __init__(
        self,
        provider_name: str,
        refresh_interval: float = 300.0,
        is_enabled: bool = True,
    ) -> None:
        self.provider_name = provider_name
        self.refresh_interval = refresh_interval
        self.is_enabled = is_enabled

        # ---- canonical status vocabulary ----
        # "ready" | "degraded" | "stale" | "unavailable" | "blocked"
        self.status = "ready"

        # ---- fetch metadata (persisted) ----
        self.last_successful_fetch: Optional[str] = None
        self.last_attempted_fetch: Optional[str] = None
        self.item_count: int = 0
        self.error_count: int = 0
        self.operational_error_reason: Optional[str] = None
        self.failure_detail: Optional[str] = None
        self.next_retry_at: Optional[str] = None

        # ---- ETag / Last-Modified per URL (persisted) ----
        self.etags: Dict[str, str] = {}
        self.last_modified_headers: Dict[str, str] = {}

        # ---- last good results (persisted) ----
        self.cached_items: List[Dict[str, Any]] = []

        # ---- circuit-breaker internals ----
        self.cb_state: str = "closed"        # closed | open | half_open
        self.consecutive_failures: int = 0
        self.circuit_open_until: float = 0.0
        self.last_fetch_timestamp: float = 0.0
        self.raw_item_count: int = 0
        self.normalized_item_count: int = 0
        self.unique_item_count: int = 0
        self.event_cluster_count: int = 0
        self.discovery_streams: List[str] = []
        self.rate_limit_state: str = "READY"
        # A completed discovery query can be healthy while returning zero
        # matching records. Providers opt in when an empty result is meaningful.
        self.empty_success_is_healthy: bool = False

    # ------------------------------------------------------------------
    # Circuit-breaker state machine
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Public lifecycle helpers
    # ------------------------------------------------------------------

    def should_fetch(self) -> bool:
        """
        Returns True only when:
        - Provider is enabled
        - Circuit breaker allows a fetch:
            closed → cooldown elapsed
            open   → False, unless cooldown elapsed → transitions to half_open
            half_open → True (probe attempt)
        """
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
        """Records a successful fetch; resets circuit breaker to closed."""
        now_str = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        healthy = bool(items) or self.empty_success_is_healthy
        self.status = "ready" if healthy else "unavailable"
        self.last_successful_fetch = now_str
        self.last_attempted_fetch = now_str
        self.item_count = len(items)
        self.operational_error_reason = None if healthy else "no_usable_records"
        self.failure_detail = None if healthy else "HTTP succeeded but produced zero valid usable records."
        self.cached_items = list(items)          # persist last good result
        self.rate_limit_state = "READY"
        self.last_fetch_timestamp = time.time()
        self._transition_to_closed()

    def record_failure(self, exc: Exception) -> None:
        """
        Records a failed fetch.
        - closed  → increment counter; if >= threshold, trip to open
        - half_open → failed probe; return to open with increased backoff
        - open  → update timestamp only (shouldn't normally be called)
        """
        now_str = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self.consecutive_failures += 1
        self.error_count += 1
        self.last_attempted_fetch = now_str
        self.last_fetch_timestamp = time.time()

        # Classify error reason
        exc_str = str(exc).lower()
        self.failure_detail = str(exc)[:300]
        if "timeout" in exc_str:
            self.operational_error_reason = "timeout"
        elif "rate" in exc_str or "429" in exc_str:
            self.operational_error_reason = "rate_limited"
            self.rate_limit_state = "RATE_LIMITED"
        elif "xml" in exc_str or "parse" in exc_str:
            self.operational_error_reason = "parse_error"
        elif "ssrf" in exc_str or "blocked" in exc_str or "private" in exc_str:
            self.operational_error_reason = "connection_error"
        else:
            self.operational_error_reason = "connection_error"

        # Compute backoff with jitter (capped at 1 h)
        backoff = min(3600.0, (2.0 ** self.consecutive_failures) * 10.0 + random.uniform(0, 5))

        if self.cb_state in ("closed", "half_open"):
            if self.consecutive_failures >= _OPEN_THRESHOLD or self.cb_state == "half_open":
                self.status = "unavailable"
                self._transition_to_open(backoff)
            else:
                self.status = "degraded"
        # If already open, just update backoff
        elif self.cb_state == "open":
            self._transition_to_open(backoff)
            self.status = "unavailable"

    # ------------------------------------------------------------------
    # Persistence support
    # ------------------------------------------------------------------

    def get_state(self) -> Dict[str, Any]:
        """
        Returns a JSON-serialisable dict of all state that must survive
        a process restart (ETag, Last-Modified, timestamps, cached items,
        circuit-breaker state).
        """
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
            "cached_items": self.cached_items,
            "cb_state": self.cb_state,
            "consecutive_failures": self.consecutive_failures,
            "circuit_open_until": self.circuit_open_until,
            "last_fetch_timestamp": self.last_fetch_timestamp,
            "raw_item_count": self.raw_item_count,
            "normalized_item_count": self.normalized_item_count,
            "unique_item_count": self.unique_item_count,
            "event_cluster_count": self.event_cluster_count,
            "discovery_streams": self.discovery_streams,
            "rate_limit_state": self.rate_limit_state,
        }

    def restore_state(self, state: Dict[str, Any]) -> None:
        """
        Restores persisted state after a process restart.
        Only fields from the saved dict are restored; missing keys are ignored
        so that adding new fields does not break existing saved state.
        """
        if not state:
            return
        for attr in (
            "status", "last_successful_fetch", "last_attempted_fetch",
            "item_count", "error_count", "operational_error_reason", "failure_detail",
            "next_retry_at", "etags", "last_modified_headers",
            "cached_items", "cb_state", "consecutive_failures",
            "circuit_open_until", "last_fetch_timestamp",
            "raw_item_count", "normalized_item_count", "unique_item_count",
            "event_cluster_count", "rate_limit_state",
        ):
            if attr in state:
                setattr(self, attr, state[attr])

        if isinstance(self.cached_items, list):
            from src.news_engine.normalizer import clean_html_text
            for it in self.cached_items:
                if isinstance(it, dict):
                    if "headline" in it:
                        it["headline"] = clean_html_text(it.get("headline", ""), max_length=200)
                    if "summary_snippet" in it:
                        it["summary_snippet"] = clean_html_text(it.get("summary_snippet", ""), max_length=500)
                    if "title" in it:
                        it["title"] = clean_html_text(it.get("title", ""), max_length=200)
                    if "summary" in it:
                        it["summary"] = clean_html_text(it.get("summary", ""), max_length=500)
                    if "description" in it:
                        it["description"] = clean_html_text(it.get("description", ""), max_length=500)

    # ------------------------------------------------------------------
    # Provider health report
    # ------------------------------------------------------------------

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
            raw_item_count=self.raw_item_count,
            normalized_item_count=self.normalized_item_count,
            unique_item_count=self.unique_item_count,
            event_cluster_count=self.event_cluster_count,
            discovery_streams=list(self.discovery_streams),
            rate_limit_state=self.rate_limit_state,
        )

    # ------------------------------------------------------------------
    # Abstract
    # ------------------------------------------------------------------

    @abc.abstractmethod
    def fetch_raw_news(self) -> List[Dict[str, Any]]:
        """
        Fetches raw data from the provider source.
        Returns a list of raw item dicts (normalized by the provider).
        Must call record_success() or record_failure() before returning.
        """
        ...
