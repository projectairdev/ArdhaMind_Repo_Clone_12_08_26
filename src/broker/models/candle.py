from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional

@dataclass(frozen=True)
class CandleModel:
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    oi: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CandleModel:
        # Standardize timestamp
        ts = data.get("date") or data.get("timestamp")
        if isinstance(ts, datetime):
            ts_str = ts.isoformat()
        else:
            ts_str = str(ts or "")
        return cls(
            timestamp=ts_str,
            open=float(data.get("open", 0.0) or 0.0),
            high=float(data.get("high", 0.0) or 0.0),
            low=float(data.get("low", 0.0) or 0.0),
            close=float(data.get("close", 0.0) or 0.0),
            volume=int(data.get("volume", 0) or 0),
            oi=int(data.get("oi", 0) or 0),
        )
