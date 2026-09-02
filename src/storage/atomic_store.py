"""
src/storage/atomic_store.py

Robust atomic file storage primitives for AIR Ardha Lightweight Session Storage.
Pattern: Serialize -> Write Temp File -> Flush -> Fsync -> Atomic os.replace.
"""
import json
import logging
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def atomic_write_json(target_path: Path, data: Any, indent: int = 2) -> bool:
    """
    Atomically writes a JSON-serializable object to target_path.
    Guarantees no partial or corrupted files exist on disk if a crash occurs.
    """
    try:
        target_path = Path(target_path).resolve()
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to unique temp file in same directory to guarantee atomic rename across filesystems
        temp_file = target_path.with_name(f"{target_path.name}.tmp.{uuid.uuid4().hex[:8]}")
        
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
            
        os.replace(temp_file, target_path)
        return True
    except Exception as exc:
        logger.error(f"[AtomicStore] Failed to atomically write {target_path}: {exc}", exc_info=True)
        # Attempt to clean up orphan temp file if it exists
        try:
            if 'temp_file' in locals() and temp_file.exists():
                temp_file.unlink()
        except Exception:
            pass
        return False


def atomic_read_json(target_path: Path) -> Optional[Dict[str, Any]]:
    """
    Safely reads and deserializes a JSON file.
    Returns None if file does not exist or if file is malformed/corrupted.
    """
    target_path = Path(target_path).resolve()
    if not target_path.exists():
        return None
    try:
        with open(target_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as exc:
        logger.warning(f"[AtomicStore] Corrupted JSON detected at {target_path}: {exc}")
        return None
    except Exception as exc:
        logger.warning(f"[AtomicStore] Failed reading {target_path}: {exc}")
        return None


def append_jsonl(target_path: Path, data: Dict[str, Any]) -> bool:
    """
    Appends a single JSON object as a line to a .jsonl file.
    """
    try:
        target_path = Path(target_path).resolve()
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        line = json.dumps(data, ensure_ascii=False) + "\n"
        with open(target_path, "a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())
        return True
    except Exception as exc:
        logger.error(f"[AtomicStore] Failed appending to jsonl {target_path}: {exc}")
        return False


def read_jsonl(target_path: Path) -> List[Dict[str, Any]]:
    """
    Reads all lines from a .jsonl file. Ignores malformed lines safely.
    """
    target_path = Path(target_path).resolve()
    if not target_path.exists():
        return []
    records = []
    try:
        with open(target_path, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if not line_str:
                    continue
                try:
                    records.append(json.loads(line_str))
                except Exception:
                    continue
    except Exception as exc:
        logger.warning(f"[AtomicStore] Failed reading jsonl {target_path}: {exc}")
    return records


def cleanup_orphaned_tmp_files(root_dir: Path | str, max_age_seconds: float = 300.0) -> int:
    """
    Boot-time and maintenance sweep that unlinks orphaned *.tmp.* files in root_dir.
    Age-gated: only removes temp files older than max_age_seconds (default 5 minutes)
    to prevent racing active in-flight atomic writes.
    """
    import time
    removed_count = 0
    now = time.time()
    try:
        p = Path(root_dir).resolve()
        if not p.exists():
            return 0
        for tmp_file in p.rglob("*.tmp.*"):
            try:
                if tmp_file.is_file():
                    stat = tmp_file.stat()
                    if (now - stat.st_mtime) >= max_age_seconds:
                        tmp_file.unlink()
                        removed_count += 1
                        logger.info(f"[AtomicStore] Cleaned up orphaned temp file: {tmp_file.name}")
            except Exception as e:
                logger.debug(f"[AtomicStore] Could not unlink temp file {tmp_file}: {e}")
    except Exception as exc:
        logger.warning(f"[AtomicStore] Error during orphan temp file sweep: {exc}")
    return removed_count
