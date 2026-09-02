from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from src.replay.models.replay_models import ReplaySpeed, ReplayState


class ReplayClock:
    """
    Deterministic simulated clock for market replay.
    Eliminates non-deterministic system clock calls during replay.
    """

    def __init__(self, initial_time: Optional[datetime] = None) -> None:
        self._current_time: datetime = initial_time or datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)
        self._state: ReplayState = ReplayState.IDLE
        self._speed: ReplaySpeed = ReplaySpeed.SPEED_MAX

    @property
    def current_time(self) -> datetime:
        """Returns the current simulated time."""
        return self._current_time

    @property
    def state(self) -> ReplayState:
        return self._state

    def start(self, initial_time: Optional[datetime] = None, speed: ReplaySpeed = ReplaySpeed.SPEED_MAX) -> None:
        if initial_time:
            if initial_time.tzinfo is None:
                raise ValueError("ReplayClock initial_time must be timezone-aware.")
            self._current_time = initial_time
        self._speed = speed
        self._state = ReplayState.RUNNING

    def pause(self) -> None:
        if self._state == ReplayState.RUNNING:
            self._state = ReplayState.PAUSED

    def resume(self) -> None:
        if self._state == ReplayState.PAUSED:
            self._state = ReplayState.RUNNING

    def advance_to(self, target_time: datetime) -> None:
        """Advances simulated time to target_time monotonically."""
        if target_time.tzinfo is None:
            raise ValueError("ReplayClock target_time must be timezone-aware.")
        if target_time < self._current_time:
            raise ValueError(f"Cannot advance clock backwards in time ({target_time} < {self._current_time})")
        self._current_time = target_time

    def step(self, delta_seconds: float = 1.0) -> datetime:
        """Steps simulated clock forward by delta_seconds."""
        if delta_seconds < 0:
            raise ValueError("Step delta cannot be negative.")
        self._current_time += timedelta(seconds=delta_seconds)
        return self._current_time

    def complete(self) -> None:
        self._state = ReplayState.COMPLETED
