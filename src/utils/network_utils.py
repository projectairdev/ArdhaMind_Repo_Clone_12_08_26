from __future__ import annotations

import time
from typing import Any, Callable
from src.configuration_engine.runtime import Config


def call_with_retry(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    last_exc = None
    for attempt in range(1, Config.RETRY_ATTEMPTS + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            last_exc = exc
            if attempt < Config.RETRY_ATTEMPTS:
                time.sleep(Config.RETRY_SLEEP_SECONDS * attempt)
    raise last_exc
