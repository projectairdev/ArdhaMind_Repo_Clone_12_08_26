from __future__ import annotations
import json
import os
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from src.configuration_engine.runtime import Config
from src.broker.utils.errors import SessionMissingError, ExpiredAccessTokenError

logger = logging.getLogger("SessionManager")


class SessionManager:
    """
    Manages loading, storing, validating, and deleting KiteConnect sessions.
    Persists session data locally in a JSON file (.cache/session.json).
    """

    @classmethod
    def get_cache_path(cls) -> str:
        """Returns the configured session cache path."""
        path = getattr(Config, "SESSION_CACHE_PATH", ".cache/session.json")
        # Ensure the directory exists
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            try:
                os.makedirs(directory, exist_ok=True)
            except Exception as e:
                logger.error(f"Failed to create cache directory {directory}: {e}")
        return path

    @classmethod
    def save_session(
        cls,
        access_token: str,
        api_key: Optional[str] = None,
        login_time: Optional[float] = None,
        persist_key: bool = True,
        persist_token: bool = True
    ) -> bool:
        """
        Stores access token, login timestamp, and calculated expiry to the local cache.
        Respects opt-in persist flags.
        """
        cache_path = cls.get_cache_path()
        now = login_time or time.time()
        expires_at = now + 86400  # 24 hours
        
        session_data = {}
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r") as f:
                    session_data = json.load(f)
            except Exception:
                pass

        if persist_token:
            session_data["access_token"] = access_token
            session_data["login_timestamp"] = now
            session_data["expires_at"] = expires_at
            session_data["expired"] = False
        else:
            session_data.pop("access_token", None)
            session_data.pop("login_timestamp", None)
            session_data.pop("expires_at", None)
            session_data.pop("expired", None)

        if persist_key and api_key:
            session_data["api_key"] = api_key
        elif not persist_key:
            session_data.pop("api_key", None)

        try:
            with open(cache_path, "w") as f:
                json.dump(session_data, f, indent=2)
            logger.info(f"Session saved successfully to {cache_path} with persist_key={persist_key}, persist_token={persist_token}")
            return True
        except Exception as e:
            logger.error(f"Error saving session data: {e}")
            return False

    @classmethod
    def load_session(cls) -> Optional[Dict[str, Any]]:
        """
        Loads the active session if it exists.
        Handles expired tokens gracefully without losing persisted API Keys.
        """
        cache_path = cls.get_cache_path()
        if not os.path.exists(cache_path):
            return None
            
        try:
            with open(cache_path, "r") as f:
                data = json.load(f)
                
            if not data:
                return None
                
            # Check expiry if access_token is present
            if "access_token" in data:
                expires_at = data.get("expires_at", 0)
                if time.time() > expires_at:
                    logger.warning("Loaded session has expired.")
                    data["expired"] = True
                    # Update file to mark as expired
                    try:
                        with open(cache_path, "w") as f:
                            json.dump(data, f, indent=2)
                    except Exception:
                        pass
                
            return data
        except Exception as e:
            logger.error(f"Error loading session: {e}")
            return None

    @classmethod
    def delete_session(cls) -> bool:
        """
        Deletes the locally stored session.
        """
        cache_path = cls.get_cache_path()
        if os.path.exists(cache_path):
            try:
                os.remove(cache_path)
                logger.info(f"Session deleted at {cache_path}")
                return True
            except Exception as e:
                logger.error(f"Error deleting session file: {e}")
                return False
        return True

    @classmethod
    def is_session_expired(cls) -> bool:
        """
        Checks if the stored session has expired.
        """
        cache_path = cls.get_cache_path()
        if not os.path.exists(cache_path):
            return True
            
        try:
            with open(cache_path, "r") as f:
                data = json.load(f)
            expires_at = data.get("expires_at", 0)
            return time.time() > expires_at
        except Exception:
            return True

    @classmethod
    def validate_session(cls) -> bool:
        """
        Ensures the loaded session is fully valid.
        Raises appropriate BrokerError if invalid, or returns True.
        """
        session = cls.load_session()
        if not session:
            raise SessionMissingError("No active session found. Please log in.")
            
        if cls.is_session_expired():
            raise ExpiredAccessTokenError("The access token has expired.")
            
        return True
