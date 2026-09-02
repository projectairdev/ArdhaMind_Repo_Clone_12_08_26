from __future__ import annotations

from datetime import date, datetime
from typing import Iterator, List, Optional, Sequence

from src.replay.models.replay_models import ReplayConfig, ReplayEvent


class ReplaySource:
    """
    Source of recorded canonical market events.
    Yields events in strictly sorted chronological sequence.
    """

    def __init__(self, events: Sequence[ReplayEvent]) -> None:
        # Sort strictly by timestamp and sequence
        self._events: List[ReplayEvent] = sorted(events, key=lambda e: (e.event_timestamp, e.sequence))

    def get_events(self, config: Optional[ReplayConfig] = None) -> List[ReplayEvent]:
        """Returns filtered list of events based on session date and time bounds."""
        if config is None:
            return list(self._events)

        filtered = []
        for e in self._events:
            if e.session_date and e.session_date != config.session_date:
                continue
            if config.start_time and e.event_timestamp < config.start_time:
                continue
            if config.end_time and e.event_timestamp > config.end_time:
                continue
            filtered.append(e)

        return filtered

    def __len__(self) -> int:
        return len(self._events)
