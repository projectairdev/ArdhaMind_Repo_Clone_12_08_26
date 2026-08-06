from __future__ import annotations

import json
import os
import pandas as pd
from typing import Any, Dict, List
from src.config_engine import Config


def ensure_export_dir(export_dir: str = Config.EXPORT_DIR) -> None:
    os.makedirs(export_dir, exist_ok=True)


def export_json_file(payload: Dict[str, Any], filepath: str) -> None:
    ensure_export_dir(os.path.dirname(filepath))
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def export_csv_file(data: List[Dict[str, Any]], filepath: str) -> None:
    if not data:
        return
    ensure_export_dir(os.path.dirname(filepath))
    df = pd.DataFrame(data)
    df.to_csv(filepath, index=False)
