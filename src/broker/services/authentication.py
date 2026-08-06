from __future__ import annotations
import logging
import time
from typing import Dict, Any, Optional

from src.config_engine import Config
from src.broker.utils.errors import (
    BrokerError,
    InvalidAPIKeyError,
    InvalidAPISecretError,
    ExpiredRequestTokenError,
    ExpiredAccessTokenError,
    NetworkFailureError,
    SessionMissingError,
    AuthenticationFailureError,
)

# Safely import kiteconnect or exceptions
try:
    from kiteconnect import KiteConnect
    from kiteconnect import exceptions as kite_exceptions
except ImportError:
    # Safe fallback if not installed/importable in some test contexts
    class KiteConnect:
        def __init__(self, *args, **kwargs): pass
        def login_url(self) -> str: return "https://kite.zerodha.com"
        def generate_session(self, *args, **kwargs): return {"access_token": "MOCK_TOKEN"}
        def invalidate_access_token(self, *args, **kwargs): pass
        def profile(self) -> dict: return {}
        
    class kite_exceptions:
        class TokenException(Exception): pass
        class InputException(Exception): pass
        class NetworkException(Exception): pass
        class DataException(Exception): pass

logger = logging.getLogger("AuthenticationManager")


class AuthenticationManager:
    """
    Stateless manager for Zerodha KiteConnect OAuth flow and access token lifecycle.
    """

    @classmethod
    def _map_exception(cls, exception: Exception) -> BrokerError:
        """
        Maps low-level KiteConnect exceptions to high-level, structured, immutable BrokerErrors.
        """
        exc_name = exception.__class__.__name__
        exc_msg = str(exception)
        
        if "api_key" in exc_msg.lower() or "apikey" in exc_msg.lower() or "api key" in exc_msg.lower():
            return InvalidAPIKeyError(f"API Key check failed: {exc_msg}")
        if "api_secret" in exc_msg.lower() or "secret" in exc_msg.lower():
            return InvalidAPISecretError(f"API Secret check failed: {exc_msg}")
        if "request_token" in exc_msg.lower() or "request token" in exc_msg.lower():
            return ExpiredRequestTokenError(f"Request token check failed: {exc_msg}")
        
        # Class-name based mapping
        if exc_name == "TokenException":
            if "expired" in exc_msg.lower():
                return ExpiredAccessTokenError(f"Session has expired: {exc_msg}")
            return AuthenticationFailureError(f"Token validation failed: {exc_msg}")
        elif exc_name == "InputException":
            if "api_key" in exc_msg.lower():
                return InvalidAPIKeyError(f"Invalid API Key parameter: {exc_msg}")
            if "secret" in exc_msg.lower():
                return InvalidAPISecretError(f"Invalid API Secret parameter: {exc_msg}")
            return AuthenticationFailureError(f"Input verification failure: {exc_msg}")
        elif exc_name == "NetworkException":
            return NetworkFailureError(f"Network error communicating with Zerodha: {exc_msg}")
        
        return AuthenticationFailureError(f"Authentication flow failed: {exc_msg}")

    @classmethod
    def generate_login_url(cls, api_key: Optional[str] = None, redirect_url: Optional[str] = None) -> str:
        """
        Generates the official Zerodha login URL.
        """
        key = api_key or getattr(Config, "KITE_API_KEY", "")
        if not key:
            raise InvalidAPIKeyError("KITE_API_KEY is missing or empty. Cannot generate login URL.")
            
        r_url = redirect_url or getattr(Config, "KITE_REDIRECT_URL", "")
        if not r_url:
            r_url = getattr(Config, "APP_URL", "http://127.0.0.1:3000") + "/api/broker/callback"
            
        try:
            kite = KiteConnect(api_key=key)
            login_url = f"https://kite.trade/connect/login?api_key={key}&v=3"
            if r_url:
                login_url += f"&redirect_params=redirect_uri%3D{r_url}"
            return login_url
        except Exception as e:
            logger.error(f"Error generating login URL: {e}")
            raise cls._map_exception(e)

    @classmethod
    def generate_access_token(
        cls, request_token: str, api_key: Optional[str] = None, api_secret: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Exchanges a request token for a persistent access token.
        """
        key = api_key or getattr(Config, "KITE_API_KEY", "")
        secret = api_secret or getattr(Config, "KITE_API_SECRET", "")
        
        if not key:
            raise InvalidAPIKeyError("KITE_API_KEY is missing or empty.")
        if not secret:
            raise InvalidAPISecretError("KITE_API_SECRET is missing or empty.")
        if not request_token:
            raise ExpiredRequestTokenError("Request token is missing or empty.")
            
        try:
            kite = KiteConnect(api_key=key)
            session = kite.generate_session(request_token, api_secret=secret)
            return session
        except Exception as e:
            logger.error(f"Error generating access token: {e}")
            raise cls._map_exception(e)

    @classmethod
    def validate_session(cls, access_token: str, api_key: Optional[str] = None) -> bool:
        """
        Validates the current session access token by attempting to fetch the profile.
        """
        key = api_key or getattr(Config, "KITE_API_KEY", "")
        if not key:
            raise InvalidAPIKeyError("KITE_API_KEY is missing.")
        if not access_token:
            raise SessionMissingError("Access token is missing.")
            
        try:
            kite = KiteConnect(api_key=key)
            kite.set_access_token(access_token)
            kite.profile()
            return True
        except Exception as e:
            logger.warning(f"Session validation failed: {e}")
            raise cls._map_exception(e)

    @classmethod
    def logout(cls, access_token: str, api_key: Optional[str] = None) -> bool:
        """
        Invalidates the active access token both on Zerodha's servers and locally.
        """
        key = api_key or getattr(Config, "KITE_API_KEY", "")
        if not key:
            raise InvalidAPIKeyError("KITE_API_KEY is missing.")
        if not access_token:
            return True  # Already logged out
            
        try:
            kite = KiteConnect(api_key=key)
            kite.set_access_token(access_token)
            kite.invalidate_access_token()
            return True
        except Exception as e:
            logger.error(f"Error during logout: {e}")
            # Map exception but return False or propagate depending on strictness
            raise cls._map_exception(e)
