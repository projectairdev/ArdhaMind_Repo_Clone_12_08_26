from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict, Optional


class StructuredLogger:
    """
    Standardized JSON structured logger.
    Automatically enriches logs with component, session, and correlation context while redacting secrets.
    """

    def __init__(self, component_name: str, logger_instance: Optional[logging.Logger] = None) -> None:
        self.component_name = component_name
        self._logger = logger_instance or logging.getLogger(component_name)

    def log(
        self,
        level: int,
        event: str,
        correlation_id: Optional[str] = None,
        session_date: Optional[str] = None,
        instrument_id: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "component": self.component_name,
            "event": event,
            "correlation_id": correlation_id or "NONE",
            "session_date": session_date,
            "canonical_instrument_id": instrument_id,
        }
        if extra:
            payload.update(self._redact(extra))

        msg_json = json.dumps(payload, default=str)
        self._logger.log(level, msg_json)
        return payload

    def info(self, event: str, **kwargs: Any) -> Dict[str, Any]:
        return self.log(logging.INFO, event, **kwargs)

    def error(self, event: str, **kwargs: Any) -> Dict[str, Any]:
        return self.log(logging.ERROR, event, **kwargs)

    def warning(self, event: str, **kwargs: Any) -> Dict[str, Any]:
        return self.log(logging.WARNING, event, **kwargs)

    @staticmethod
    def _redact(data: Dict[str, Any]) -> Dict[str, Any]:
        sensitive = {"token", "secret", "password", "key", "authorization", "auth"}
        return {
            k: ("[REDACTED]" if any(s in k.lower() for s in sensitive) else v)
            for k, v in data.items()
        }
