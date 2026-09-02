from __future__ import annotations

import os
import json
import time
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from src.news_engine.safe_utils import atomic_write_json
from src.application.material_change_detector import MaterialChangeDetector

logger = logging.getLogger(__name__)


class SessionPersistenceAdapter:
    """Handles disk caching, bounded retention, and atomic persistence for workstation session history."""

    @staticmethod
    def get_session_recording_window(now_dt: datetime | None = None) -> tuple[str, float]:
        """
        Evaluates current IST time against the canonical recording windows:
        - WINDOW_A_BEFORE_0845 (00:00 - 08:44:59 IST): heartbeat = 0.0
        - WINDOW_B_PRE_MARKET_EVIDENCE (08:45 - 08:59:59 IST): heartbeat = 60.0s
        - WINDOW_C_PRE_OPEN (09:00 - 09:14:59 IST): heartbeat = 15.0s
        - WINDOW_D_LIVE (09:15 - 15:29:59 IST): heartbeat = 15.0s
        - WINDOW_E_CLOSING_FINALIZATION (15:30 - 15:44:59 IST): heartbeat = 15.0s
        - WINDOW_F_NEWS_ONLY (15:45 - 18:30:00 IST): heartbeat = 0.0
        - WINDOW_G_OFF_MARKET (18:30 - 23:59:59 IST): heartbeat = 0.0
        """
        dt = now_dt or datetime.now(timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        ist = timezone(timedelta(hours=5, minutes=30))
        dt_ist = dt.astimezone(ist)
        t_min = dt_ist.hour * 60 + dt_ist.minute + dt_ist.second / 60.0

        if t_min < 525.0:  # 08:45:00
            return "WINDOW_A_BEFORE_0845", 0.0
        elif t_min < 540.0:  # 09:00:00
            return "WINDOW_B_PRE_MARKET_EVIDENCE", 60.0
        elif t_min < 555.0:  # 09:15:00
            return "WINDOW_C_PRE_OPEN", 15.0
        elif t_min < 930.0:  # 15:30:00
            return "WINDOW_D_LIVE", 15.0
        elif t_min < 945.0:  # 15:45:00
            return "WINDOW_E_CLOSING_FINALIZATION", 15.0
        elif t_min <= 1110.0:  # 18:30:00
            return "WINDOW_F_NEWS_ONLY", 0.0
        else:
            return "WINDOW_G_OFF_MARKET", 0.0

    @staticmethod
    def put_bounded_version(target_dict: dict[str, Any], key: str, val: Any, max_size: int = 50) -> None:
        """Adds key/value to target dictionary with bounded FIFO eviction policy."""
        if key in target_dict:
            del target_dict[key]
        elif len(target_dict) >= max_size:
            oldest_key = next(iter(target_dict))
            del target_dict[oldest_key]
        target_dict[key] = val

    @staticmethod
    def filter_retained_snapshots(snapshots: list[dict[str, Any]], session_date: str) -> list[dict[str, Any]]:
        """Filters snapshot history to preserve all canonical session checkpoints."""
        if not snapshots:
            return []

        dates = {s.get("session_date") for s in snapshots if s.get("session_date")}
        if not dates:
            return snapshots[-500:]

        retained_all = []
        for d in sorted(dates):
            d_snaps = [s for s in snapshots if s.get("session_date") == d]
            checkpoint_keys = set()

            for phase in ("PRE_MARKET", "PRE_OPEN", "MARKET_OPEN", "OPEN", "CONTINUOUS_TRADING"):
                for s in d_snaps:
                    if s.get("market_session_phase") == phase or (phase in ("MARKET_OPEN", "OPEN") and s.get("continuous_session_open") and s.get("spot") is not None):
                        checkpoint_keys.add((s.get("timestamp"), s.get("state_sequence")))
                        break

            d_valid_spots = [s for s in d_snaps if isinstance(s.get("spot"), (int, float))]
            if d_valid_spots:
                max_s = max(d_valid_spots, key=lambda s: s["spot"])
                min_s = min(d_valid_spots, key=lambda s: s["spot"])
                checkpoint_keys.add((max_s.get("timestamp"), max_s.get("state_sequence")))
                checkpoint_keys.add((min_s.get("timestamp"), min_s.get("state_sequence")))

            seen_3m_buckets = set()
            for s in d_snaps:
                ts_str = str(s.get("timestamp") or "")
                if ts_str:
                    try:
                        dt_u = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        dt_i = dt_u.astimezone(timezone(timedelta(hours=5, minutes=30)))
                        bucket = f"{dt_i.hour:02d}:{(dt_i.minute // 3) * 3:02d}"
                        if bucket not in seen_3m_buckets:
                            seen_3m_buckets.add(bucket)
                            checkpoint_keys.add((s.get("timestamp"), s.get("state_sequence")))
                    except Exception:
                        pass

            checkpoints = [s for s in d_snaps if (s.get("timestamp"), s.get("state_sequence")) in checkpoint_keys]
            recent_rolling = d_snaps[-500:] if d == session_date else d_snaps[-50:]

            combined_dict = {}
            for s in checkpoints + recent_rolling:
                key = (s.get("timestamp"), s.get("state_sequence"))
                combined_dict[key] = s

            retained_d = list(combined_dict.values())
            retained_d.sort(key=lambda x: (x.get("timestamp") or "", x.get("state_sequence") or 0))
            retained_all.extend(retained_d)

        return retained_all
