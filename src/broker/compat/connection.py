from __future__ import annotations

import logging
import os
import sys
from typing import Dict, Any, Optional

# Add workspace root to system path to ensure kiteconnect is importable
workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

try:
    from kiteconnect import KiteConnect
except ImportError:
    # Fallback to local import if needed
    try:
        import kiteconnect
        KiteConnect = kiteconnect.KiteConnect
    except ImportError:
        class KiteConnect:
            def __init__(self, *args, **kwargs): pass
            def set_access_token(self, *args, **kwargs): pass
            def profile(self): return {"client_id": "MOCK_CLIENT"}

logger = logging.getLogger("BrokerConnection")


class BrokerConnectionError(Exception):
    """Custom exception for Broker Connection errors."""
    pass


class ConnectionManager:
    """
    Manages connection to Zerodha KiteConnect, including authentication,
    session validation, and connection state.
    """
    _instance: Optional[ConnectionManager] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ConnectionManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self.api_key: Optional[str] = None
        self.access_token: Optional[str] = None
        self.kite_client: Optional[KiteConnect] = None
        self._initialized = True

    def connect(self, api_key: str, request_token: str, api_secret: str) -> bool:
        """
        Generates session using request_token and initializes KiteConnect client.
        """
        try:
            logger.info("Initializing KiteConnect with API Key")
            client = KiteConnect(api_key=api_key)
            session = client.generate_session(request_token, api_secret=api_secret)
            access_token = session.get("access_token")
            
            if not access_token:
                raise BrokerConnectionError("No access token returned in session generation.")
                
            client.set_access_token(access_token)
            
            # Verify the session
            profile = client.profile()
            if not profile or "client_id" not in profile:
                raise BrokerConnectionError("Failed to retrieve profile with generated session.")
                
            self.api_key = api_key
            self.access_token = access_token
            self.kite_client = client
            logger.info(f"Connected to broker successfully. Client ID: {profile.get('client_id')}")
            return True
        except Exception as e:
            logger.error(f"Error establishing broker connection: {e}")
            self.disconnect()
            raise BrokerConnectionError(f"Broker connection failed: {str(e)}")

    def connect_with_token(self, api_key: str, access_token: str) -> bool:
        """
        Initializes KiteConnect client directly using a persistent access token.
        """
        try:
            logger.info("Initializing KiteConnect directly with Access Token")
            client = KiteConnect(api_key=api_key)
            client.set_access_token(access_token)
            
            # Verify the session
            profile = client.profile()
            if not profile or "client_id" not in profile:
                raise BrokerConnectionError("Invalid access token or connection expired.")
                
            self.api_key = api_key
            self.access_token = access_token
            self.kite_client = client
            logger.info(f"Connected to broker with token. Client ID: {profile.get('client_id')}")
            return True
        except Exception as e:
            logger.error(f"Error connecting with token: {e}")
            self.disconnect()
            raise BrokerConnectionError(f"Token connection failed: {str(e)}")

    def get_client(self) -> KiteConnect:
        """
        Returns the active KiteConnect client. Raises error if not connected.
        """
        if self.kite_client is None:
            raise BrokerConnectionError("Broker not connected. Please login first.")
        return self.kite_client

    def is_connected(self) -> bool:
        """
        Validates if connection is active by making a lightweight profile call.
        """
        if self.kite_client is None:
            return False
        try:
            profile = self.kite_client.profile()
            return profile is not None and "client_id" in profile
        except Exception:
            return False

    def disconnect(self) -> None:
        """Clears active connection state."""
        self.api_key = None
        self.access_token = None
        self.kite_client = None
        logger.info("Disconnected from broker.")

    def get_status_report(self) -> Dict[str, Any]:
        """
        Returns connection status information for reporting.
        """
        try:
            connected = self.is_connected()
            client_id = "N/A"
            client_name = "N/A"
            if connected and self.kite_client:
                profile = self.kite_client.profile()
                client_id = profile.get("client_id", "N/A")
                client_name = profile.get("user_name", profile.get("client_name", "N/A"))
            
            return {
                "connected": connected,
                "client_id": client_id,
                "client_name": client_name,
                "api_key_configured": self.api_key is not None,
                "access_token_configured": self.access_token is not None,
            }
        except Exception as e:
            return {
                "connected": False,
                "client_id": "N/A",
                "client_name": "N/A",
                "error": str(e)
            }
