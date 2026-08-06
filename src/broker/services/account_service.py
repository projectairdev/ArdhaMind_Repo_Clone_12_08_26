from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional
import time
from datetime import datetime

@dataclass(frozen=True)
class AccountProfile:
    client_id: str
    client_name: str
    email: str
    pan: str
    broker_name: str
    user_type: str
    login_time: str

class AccountService:
    @staticmethod
    def get_profile(gateway) -> AccountProfile:
        """
        Retrieves live account profile details from the broker gateway and maps to AccountProfile.
        """
        raw = gateway.get_profile()

        pan = raw.get("pan", "N/A")
        masked_pan = "N/A"
        if pan and pan != "N/A":
            if len(pan) >= 5:
                # Mask first 5 characters e.g. ABCDE1234F -> XXXXX1234F
                masked_pan = "XXXXX" + pan[5:]
            else:
                masked_pan = "X" * len(pan)
        
        login_time = raw.get("login_time", "")
        if not login_time:
            login_time = time.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(login_time, datetime):
            login_time = login_time.strftime("%Y-%m-%d %H:%M:%S")
        else:
            login_time = str(login_time)

        return AccountProfile(
            client_id=raw.get("client_id") or raw.get("user_id") or "N/A",
            client_name=raw.get("user_name") or raw.get("client_name") or "N/A",
            email=raw.get("email", "N/A"),
            pan=masked_pan,
            broker_name=raw.get("broker") or "Zerodha",
            user_type=raw.get("user_type", "individual"),
            login_time=login_time,
        )
