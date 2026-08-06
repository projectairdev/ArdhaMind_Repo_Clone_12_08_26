from __future__ import annotations

import logging
from typing import Optional
from src.models.execution_report import BrokerAccount
from src.broker_engine.connection import ConnectionManager

logger = logging.getLogger("BrokerAccount")


class AccountManager:
    """
    Manages retrieving account details from Zerodha KiteConnect.
    """
    @staticmethod
    def get_account_info() -> BrokerAccount:
        """
        Fetches the user's profile details and maps it to BrokerAccount model.
        """
        try:
            client = ConnectionManager().get_client()
            profile = client.profile()
            
            if not profile:
                raise ValueError("Received empty profile from broker.")
                
            return BrokerAccount(
                client_id=profile.get("client_id", "N/A"),
                name=profile.get("user_name", profile.get("client_name", "N/A")),
                email=profile.get("email", "N/A"),
                broker="Zerodha"
            )
        except Exception as e:
            logger.error(f"Error fetching broker account info: {e}")
            return BrokerAccount(
                client_id="ERROR",
                name="ERROR",
                email="ERROR",
                broker="Zerodha"
            )
