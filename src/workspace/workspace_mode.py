from __future__ import annotations
from enum import Enum, unique

@unique
class WorkspaceMode(str, Enum):
    LIVE_PRACTICE = "LIVE_PRACTICE"
    LIVE_TRADING = "LIVE_TRADING"
