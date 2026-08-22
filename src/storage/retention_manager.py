"""
src/storage/retention_manager.py

Session-count-aware retention manager for AIR Ardha Lightweight Session Storage.
Enforces permanent retention for Close Core, Options Baseline, and Integrity Envelopes.
Prunes rolling stores strictly by trading-session count.
"""
import logging
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)


class RetentionManager:
    """
    Manages lifecycle pruning of lightweight session artifacts.
    """

    DEFAULT_LIMITS = {
        "telemetry": 5,        # 5 rolling trading sessions
        "connectivity": 30,    # 30 rolling trading sessions
    }

    @classmethod
    def prune_rolling_stores(cls, base_dir: Path, custom_limits: Dict[str, int] = None) -> Dict[str, int]:
        """
        Prunes rolling directories by session count.
        NOTE: close, options_close, and integrity directories are PERMANENT and never pruned.
        Legacy session_history is untouched.
        """
        limits = custom_limits or cls.DEFAULT_LIMITS
        pruned_counts = {}
        base_dir = Path(base_dir).resolve()
        
        for subdir_name, max_count in limits.items():
            target_dir = base_dir / subdir_name
            if not target_dir.exists():
                pruned_counts[subdir_name] = 0
                continue
                
            # Sort files descending by date/name
            files = sorted(
                [f for f in target_dir.iterdir() if f.is_file() and not f.name.endswith(".tmp")],
                key=lambda p: p.name,
                reverse=True
            )
            
            pruned_in_dir = 0
            if len(files) > max_count:
                for old_file in files[max_count:]:
                    try:
                        old_file.unlink()
                        pruned_in_dir += 1
                    except Exception as exc:
                        logger.warning(f"[RetentionManager] Could not prune {old_file}: {exc}")
                        
            pruned_counts[subdir_name] = pruned_in_dir
            
        return pruned_counts
