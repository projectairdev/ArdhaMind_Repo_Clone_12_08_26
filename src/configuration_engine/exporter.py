from __future__ import annotations

import json
from typing import Dict, Any, Optional

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


class ExportManager:
    """
    Stateless configuration exporter. Converts unified config maps to JSON, YAML, or text summaries.
    """

    @staticmethod
    def to_json(config_data: Dict[str, Any]) -> str:
        """
        Exports the raw config data to a formatted JSON string.
        """
        return json.dumps(config_data, indent=2, sort_keys=True)

    @staticmethod
    def to_yaml(config_data: Dict[str, Any]) -> str:
        """
        Exports the raw config data to a formatted YAML string.
        """
        if yaml:
            try:
                return yaml.dump(config_data, default_flow_style=False, sort_keys=True)
            except Exception:
                pass

        # Fallback simple custom YAML formatter if PyYAML is unavailable
        lines = []
        for cat, val in sorted(config_data.items()):
            lines.append(f"{cat}:")
            if isinstance(val, dict):
                for k, v in sorted(val.items()):
                    if isinstance(v, (list, dict)):
                        lines.append(f"  {k}: {json.dumps(v)}")
                    else:
                        lines.append(f"  {k}: {v}")
            else:
                lines.append(f"  {val}")
        return "\n".join(lines)

    @staticmethod
    def to_summary_text(config_data: Dict[str, Any]) -> str:
        """
        Exports configuration data to an elegantly formatted human-readable ASCII summary report.
        """
        lines = []
        lines.append("=" * 80)
        lines.append(" TRADING WORKSTATION - UNIFIED CONFIGURATION BACKUP SUMMARY")
        lines.append("=" * 80)
        
        for category, settings in sorted(config_data.items()):
            lines.append(f"\n[+] CATEGORY: {category.upper()}")
            lines.append("-" * 40)
            if isinstance(settings, dict):
                for k, v in sorted(settings.items()):
                    if isinstance(v, dict):
                        lines.append(f"  * {k:24}:")
                        for sub_k, sub_v in sorted(v.items()):
                            lines.append(f"    - {sub_k:20}: {sub_v}")
                    elif isinstance(v, list):
                        items_str = ", ".join(map(str, v))
                        lines.append(f"  * {k:24}: [{items_str}]")
                    else:
                        lines.append(f"  * {k:24}: {v}")
            else:
                lines.append(f"  {settings}")
            lines.append("-" * 40)
            
        lines.append("\n" + "=" * 80)
        lines.append(" END OF CONFIGURATION BACKUP REPORT")
        lines.append("=" * 80)
        
        return "\n".join(lines)
