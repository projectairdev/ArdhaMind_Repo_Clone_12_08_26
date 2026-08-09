# src/dashboard/macro_panel.py
"""
MacroIntelligencePanel — downstream compatibility serializer for MacroContext.

Must NEVER become a second source of truth. Formats canonical MacroContext snapshots
into workstation state dictionaries.
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from src.models.macro_context import MacroContext


class MacroIntelligencePanel:
    """
    Downstream compatibility serializer for MacroContext.
    """

    def __init__(self, macro_context: Optional[MacroContext] = None) -> None:
        self.macro_context = macro_context

    def to_dict(self) -> Dict[str, Any]:
        if not self.macro_context:
            return {
                "status": "UNAVAILABLE",
                "quotes": {},
                "institutional_flows": [],
                "economic_events": [],
                "corporate_actions": [],
                "earnings_events": [],
                "ipo_events": [],
                "constituent_metadata": None,
                "provider_health": {},
                "domain_freshness": {},
            }
        return self.macro_context.to_dict()
