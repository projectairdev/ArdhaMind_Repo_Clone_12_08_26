from __future__ import annotations
import time
import logging
from typing import List, Dict, Any, Optional

from src.broker.interfaces.broker_interface import IBrokerGateway
from src.broker.models.health import BrokerHealth
from src.broker.services.authentication import AuthenticationManager, KiteConnect
from src.broker.services.session_manager import SessionManager
from src.configuration_engine.runtime import Config
from src.broker.utils.errors import (
    BrokerError,
    SessionMissingError,
    ExpiredRequestTokenError,
    ExpiredAccessTokenError,
    InvalidAPIKeyError,
    InvalidAPISecretError,
    AuthenticationFailureError,
)

logger = logging.getLogger("KiteBrokerGateway")


import sys
import builtins

def print(*args, **kwargs):
    kwargs.setdefault("file", sys.stderr)
    builtins.print(*args, **kwargs)


class KiteBrokerGateway(IBrokerGateway):
    """
    KiteConnect adapter implementation for Zerodha.
    Implements real authentication, session management, and health metrics
    for Sprint 28. Market data and order management raise NotImplementedError.
    """

    def __init__(self) -> None:
        self.api_key = getattr(Config, "KITE_API_KEY", "")
        self.api_secret = getattr(Config, "KITE_API_SECRET", "")
        self.access_token: Optional[str] = None
        self._kite_client: Optional[KiteConnect] = None
        self._connected = False
        self._last_error: Optional[str] = None
        self._last_latency: float = 0.0

        # Auto-load session if configured
        if getattr(Config, "AUTO_LOAD_SESSION", True):
            try:
                self.load_session()
            except Exception as e:
                logger.warning(f"Failed to auto-load session: {e}")

    def connect(self, **kwargs) -> bool:
        """
        Establishes connection to KiteConnect using an active API key and access token.
        Can receive parameters or fallback to Config and loaded session.
        """
        api_key = kwargs.get("api_key") or self.api_key
        access_token = kwargs.get("access_token") or self.access_token

        if not api_key:
            self._last_error = "Missing API Key"
            return False
        if not access_token:
            self._last_error = "Missing Access Token"
            return False

        try:
            kite = KiteConnect(api_key=api_key)
            kite.set_access_token(access_token)
            
            # Optionally validate session with a simple call
            if getattr(Config, "AUTO_VALIDATE_SESSION", True):
                start_time = time.time()
                kite.profile()
                self._last_latency = (time.time() - start_time) * 1000.0
            
            self.api_key = api_key
            self.access_token = access_token
            self._kite_client = kite
            self._connected = True
            self._last_error = None
            return True
        except Exception as e:
            logger.error(f"Kite connect failed: {e}")
            self._last_error = str(e)
            self._connected = False
            return False

    def disconnect(self) -> None:
        """Clears local connection state."""
        self.access_token = None
        self._kite_client = None
        self._connected = False
        self._last_error = None

    def is_connected(self) -> bool:
        """Checks if connection is active."""
        return self._connected

    # --- Task 7 Authentication Methods ---

    def login(self, request_token: str) -> bool:
        """
        Exchanges request token for access token, stores session, and connects.
        """
        if not request_token:
            raise ExpiredRequestTokenError("Request token cannot be empty.")

        try:
            session_details = AuthenticationManager.generate_access_token(
                request_token=request_token,
                api_key=self.api_key,
                api_secret=self.api_secret
            )
            
            access_token = session_details.get("access_token")
            if not access_token:
                raise SessionMissingError("Failed to extract access_token from Zerodha login response.")
            
            # Save token to file cache
            SessionManager.save_session(access_token)
            
            # Establish active connection
            return self.connect(access_token=access_token)
        except Exception as e:
            self._last_error = str(e)
            self._connected = False
            if isinstance(e, BrokerError):
                raise e
            raise AuthenticationManager._map_exception(e)

    def logout(self) -> bool:
        """
        Logs out of KiteConnect, invalidating access token and deleting cached session.
        """
        try:
            if self.access_token:
                try:
                    AuthenticationManager.logout(self.access_token, api_key=self.api_key)
                except Exception as e:
                    logger.warning(f"Remote logout failed (already invalidated/expired): {e}")
            
            SessionManager.delete_session()
            self.disconnect()
            return True
        except Exception as e:
            self._last_error = str(e)
            if isinstance(e, BrokerError):
                raise e
            raise AuthenticationManager._map_exception(e)

    def validate_session(self) -> bool:
        """
        Validates active session. Raises BrokerError if invalid.
        """
        if not self.access_token:
            self._connected = False
            raise SessionMissingError("No active session found to validate.")

        try:
            start_time = time.time()
            AuthenticationManager.validate_session(self.access_token, api_key=self.api_key)
            self._last_latency = (time.time() - start_time) * 1000.0
            self._connected = True
            self._last_error = None
            return True
        except Exception as e:
            self._connected = False
            self._last_error = str(e)
            if isinstance(e, BrokerError):
                raise e
            raise AuthenticationManager._map_exception(e)

    def get_login_url(self) -> str:
        """
        Generates the KiteConnect login URL.
        """
        return AuthenticationManager.generate_login_url(api_key=self.api_key)

    def load_session(self) -> bool:
        """
        Restores the cached session from file, with fallback to environment variables.
        """
        try:
            session_data = SessionManager.load_session() or {}
            
            api_key = session_data.get("api_key") or self.api_key or getattr(Config, "KITE_API_KEY", "")
            access_token = session_data.get("access_token")
            expired = session_data.get("expired", False)
            
            if expired:
                access_token = None
                
            if not access_token:
                # Fallback to the environment variable passed by the server
                access_token = getattr(Config, "KITE_ACCESS_TOKEN", "")
                
            if not api_key:
                api_key = getattr(Config, "KITE_API_KEY", "")
                
            if api_key:
                self.api_key = api_key
                
            if access_token:
                # Attempt connection with the loaded or fallback token
                return self.connect(api_key=api_key, access_token=access_token)
            return False
        except Exception as e:
            logger.error(f"Error loading session: {e}")
            self._last_error = str(e)
            return False

    def save_session(self, access_token: str) -> bool:
        """
        Saves current access token manually.
        """
        return SessionManager.save_session(access_token)

    # --- Profile & Account Methods (Sprint 28 Skeleton) ---

    def get_profile(self) -> Dict[str, Any]:
        """Retrieves user profile details if connected."""
        if not self._connected or not self._kite_client:
            raise SessionMissingError("Broker not connected. Access token required.")
        
        import sys
        import time
        import json
        print("\n[Kite]\nProfile Request...", flush=True)
        start_time = time.time()
        try:
            res = self._kite_client.profile()
            latency = int((time.time() - start_time) * 1000.0)
            print("\n✓ Success", flush=True)
            print(f"\nTime: {latency} ms", flush=True)
            print("\nResponse:", flush=True)
            
            normalized = dict(res) if isinstance(res, dict) else {}
            if "user_id" in normalized and "client_id" not in normalized:
                normalized["client_id"] = normalized["user_id"]
            if "user_name" in normalized and "client_name" not in normalized:
                normalized["client_name"] = normalized["user_name"]
            
            print(json.dumps(normalized, indent=2, default=str), flush=True)
            return normalized
        except Exception as e:
            latency = int((time.time() - start_time) * 1000.0)
            print("\n✗ Failed", flush=True)
            print(f"\nTime: {latency} ms", flush=True)
            print(f"\nReason:\n{str(e)}", flush=True)
            raise AuthenticationManager._map_exception(e)

    # --- Prohibited Actions (Later Sprints) ---

    def get_funds(self) -> Any:
        if not self._connected or not self._kite_client:
            raise SessionMissingError("Broker not connected. Access token required.")
        
        import sys
        import time
        import json
        print("\n[Kite]\nMargins Request...", flush=True)
        start_time = time.time()
        try:
            res = self._kite_client.margins()
            latency = int((time.time() - start_time) * 1000.0)
            print("\n✓ Success", flush=True)
            print(f"\nTime: {latency} ms", flush=True)
            print("\nResponse:", flush=True)
            print(json.dumps(res, indent=2, default=str), flush=True)
            
            equity = res.get("equity", {})
            equity_avail = equity.get("available", {})
            equity_util = equity.get("utilised", {})
            
            cash = float(equity_avail.get("cash", 0.0))
            net_margin = float(equity.get("net", 0.0)) or float(equity_avail.get("live_balance", 0.0))
            debits = float(equity_util.get("debits", 0.0))
            
            from src.models.execution_report import BrokerFunds
            funds_obj = BrokerFunds(
                available_cash=cash,
                margins=net_margin,
                utilized_margin=debits,
                available_margin=net_margin
            )
            return funds_obj
        except Exception as e:
            latency = int((time.time() - start_time) * 1000.0)
            print("\n✗ Failed", flush=True)
            print(f"\nTime: {latency} ms", flush=True)
            print(f"\nReason:\n{str(e)}", flush=True)
            raise AuthenticationManager._map_exception(e)

    def get_holdings(self) -> List[Any]:
        if not self._connected or not self._kite_client:
            raise SessionMissingError("Broker not connected. Access token required.")
        
        import sys
        import time
        import json
        print("\n[Kite]\nHoldings Request...", flush=True)
        start_time = time.time()
        try:
            res = self._kite_client.holdings()
            latency = int((time.time() - start_time) * 1000.0)
            print("\n✓ Success", flush=True)
            print(f"\nTime: {latency} ms", flush=True)
            print("\nResponse:", flush=True)
            print(json.dumps(res, indent=2, default=str), flush=True)
            return res
        except Exception as e:
            latency = int((time.time() - start_time) * 1000.0)
            print("\n✗ Failed", flush=True)
            print(f"\nTime: {latency} ms", flush=True)
            print(f"\nReason:\n{str(e)}", flush=True)
            raise AuthenticationManager._map_exception(e)

    def get_positions(self) -> List[Any]:
        if not self._connected or not self._kite_client:
            raise SessionMissingError("Broker not connected. Access token required.")
        
        import sys
        import time
        import json
        print("\n[Kite]\nPositions Request...", flush=True)
        start_time = time.time()
        try:
            res = self._kite_client.positions()
            latency = int((time.time() - start_time) * 1000.0)
            print("\n✓ Success", flush=True)
            print(f"\nTime: {latency} ms", flush=True)
            print("\nResponse:", flush=True)
            print(json.dumps(res, indent=2, default=str), flush=True)
            return res
        except Exception as e:
            latency = int((time.time() - start_time) * 1000.0)
            print("\n✗ Failed", flush=True)
            print(f"\nTime: {latency} ms", flush=True)
            print(f"\nReason:\n{str(e)}", flush=True)
            raise AuthenticationManager._map_exception(e)

    def get_orders(self) -> List[Any]:
        if not self._connected or not self._kite_client:
            raise SessionMissingError("Broker not connected. Access token required.")
        
        import sys
        import time
        import json
        print("\n[Kite]\nOrders Request...", flush=True)
        start_time = time.time()
        try:
            res = self._kite_client.orders()
            latency = int((time.time() - start_time) * 1000.0)
            print("\n✓ Success", flush=True)
            print(f"\nTime: {latency} ms", flush=True)
            print("\nResponse:", flush=True)
            print(json.dumps(res, indent=2, default=str), flush=True)
            return res
        except Exception as e:
            latency = int((time.time() - start_time) * 1000.0)
            print("\n✗ Failed", flush=True)
            print(f"\nTime: {latency} ms", flush=True)
            print(f"\nReason:\n{str(e)}", flush=True)
            raise AuthenticationManager._map_exception(e)

    def get_order_history(self, order_id: str) -> List[Any]:
        if not self._connected or not self._kite_client:
            raise SessionMissingError("Broker not connected. Access token required.")
        
        import sys
        import time
        import json
        print(f"\n[Kite]\nOrder History Request for {order_id}...", flush=True)
        start_time = time.time()
        try:
            res = self._kite_client.order_history(order_id)
            latency = int((time.time() - start_time) * 1000.0)
            print("\n✓ Success", flush=True)
            print(f"\nTime: {latency} ms", flush=True)
            print("\nResponse:", flush=True)
            print(json.dumps(res, indent=2, default=str), flush=True)
            return res
        except Exception as e:
            latency = int((time.time() - start_time) * 1000.0)
            print("\n✗ Failed", flush=True)
            print(f"\nTime: {latency} ms", flush=True)
            print(f"\nReason:\n{str(e)}", flush=True)
            raise AuthenticationManager._map_exception(e)

    def get_trades(self) -> List[Any]:
        if not self._connected or not self._kite_client:
            raise SessionMissingError("Broker not connected. Access token required.")
        
        import sys
        import time
        import json
        print("\n[Kite]\nTrades Request...", flush=True)
        start_time = time.time()
        try:
            res = self._kite_client.trades()
            latency = int((time.time() - start_time) * 1000.0)
            print("\n✓ Success", flush=True)
            print(f"\nTime: {latency} ms", flush=True)
            print("\nResponse:", flush=True)
            print(json.dumps(res, indent=2, default=str), flush=True)
            return res
        except Exception as e:
            latency = int((time.time() - start_time) * 1000.0)
            print("\n✗ Failed", flush=True)
            print(f"\nTime: {latency} ms", flush=True)
            print(f"\nReason:\n{str(e)}", flush=True)
            raise AuthenticationManager._map_exception(e)

    def get_quote(self, symbols: List[str]) -> Dict[str, Any]:
        """Retrieves quotes for a list of instruments."""
        if not self._connected or not self._kite_client:
            raise SessionMissingError("Broker not connected. Active session is required to fetch quotes.")
        try:
            start_time = time.time()
            res = self._kite_client.quote(symbols)
            self._last_latency = (time.time() - start_time) * 1000.0
            self._last_error = None
            return res or {}
        except Exception as e:
            self._last_error = str(e)
            if isinstance(e, BrokerError):
                raise e
            raise AuthenticationManager._map_exception(e)

    def get_ltp(self, symbols: List[str]) -> Dict[str, Any]:
        """Retrieves Last Traded Price (LTP) map for a list of instruments."""
        if not self._connected or not self._kite_client:
            raise SessionMissingError("Broker not connected. Active session is required to fetch LTP.")
        try:
            start_time = time.time()
            res = self._kite_client.ltp(symbols)
            self._last_latency = (time.time() - start_time) * 1000.0
            self._last_error = None
            return res or {}
        except Exception as e:
            self._last_error = str(e)
            if isinstance(e, BrokerError):
                raise e
            raise AuthenticationManager._map_exception(e)

    def get_historical_data(
        self,
        instrument_token: int,
        from_date: Any,
        to_date: Any,
        interval: str,
        continuous: bool = False,
        oi: bool = False
    ) -> List[Dict[str, Any]]:
        """Retrieves historical candle data."""
        if not self._connected or not self._kite_client:
            raise SessionMissingError("Broker not connected. Active session is required to fetch historical data.")
        try:
            start_time = time.time()
            res = self._kite_client.historical_data(
                instrument_token=instrument_token,
                from_date=from_date,
                to_date=to_date,
                interval=interval,
                continuous=continuous,
                oi=oi
            )
            self._last_latency = (time.time() - start_time) * 1000.0
            self._last_error = None
            return res or []
        except Exception as e:
            self._last_error = str(e)
            if isinstance(e, BrokerError):
                raise e
            raise AuthenticationManager._map_exception(e)

    def get_instruments(self, exchange: Optional[str] = None) -> Any:
        """Retrieves master list of instruments from Zerodha."""
        if not self._connected or not self._kite_client:
            raise SessionMissingError("Broker not connected. Active session is required to fetch instruments.")
        try:
            start_time = time.time()
            if exchange:
                res = self._kite_client.instruments(exchange)
            else:
                res = self._kite_client.instruments()
            self._last_latency = (time.time() - start_time) * 1000.0
            self._last_error = None
            return res or []
        except Exception as e:
            self._last_error = str(e)
            if isinstance(e, BrokerError):
                raise e
            raise AuthenticationManager._map_exception(e)

    def place_order(self, **kwargs) -> Any:
        raise NotImplementedError("Order placement is not implemented for this sprint.")

    def modify_order(self, **kwargs) -> Any:
        raise NotImplementedError("Order modification is not implemented for this sprint.")

    def cancel_order(self, **kwargs) -> Any:
        raise NotImplementedError("Order cancellation is not implemented for this sprint.")

    # --- Task 4 Broker Health Integration ---

    def health(self) -> BrokerHealth:
        """
        Builds a comprehensive BrokerHealth object with the authentication and session metrics.
        """
        # Load local session data for age calculations
        session = SessionManager.load_session()
        
        session_age_hours = 0.0
        last_login_str = "N/A"
        token_expiry_str = "N/A"
        session_valid_bool = False
        
        if session:
            login_ts = session.get("login_timestamp", 0)
            expires_ts = session.get("expires_at", 0)
            
            if login_ts:
                session_age_hours = (time.time() - login_ts) / 3600.0
                last_login_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(login_ts))
            if expires_ts:
                token_expiry_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(expires_ts))
            
            session_valid_bool = not SessionManager.is_session_expired()

        connection_status = "DISCONNECTED"
        if self._connected:
            connection_status = "CONNECTED"
        elif self._last_error:
            connection_status = "ERROR"

        auth_state = "UNAUTHENTICATED"
        if self._connected and session_valid_bool:
            auth_state = "AUTHENTICATED"
        elif session and not session_valid_bool:
            auth_state = "EXPIRED"

        health_score = 0.0
        if self._connected and session_valid_bool:
            health_score = 100.0
        elif session_valid_bool:
            health_score = 50.0  # Session exists but disconnected

        # Dynamically determine cache status
        from src.broker.utils.cache_manager import InstrumentCacheManager
        cache_status = "MISSING"
        if InstrumentCacheManager.cache_exists("ZERODHA"):
            if InstrumentCacheManager.cache_validation("ZERODHA"):
                cache_status = "VALID"
            else:
                cache_status = "EXPIRED"

        # Dynamically determine market status using service
        from src.broker.services.market_status_service import MarketStatusService
        try:
            status_service = MarketStatusService.get_instance()
            market_report = status_service.get_market_status()
            market_status_str = market_report.status
        except Exception:
            market_status_str = "CLOSED"

        return BrokerHealth(
            broker_name="Zerodha KiteConnect",
            connection_status=connection_status,
            trading_mode="LIVE_ZERODHA",
            latency=self._last_latency,
            authentication_state=auth_state,
            last_heartbeat=time.strftime("%Y-%m-%d %H:%M:%S"),
            instrument_cache_status=cache_status,
            market_status=market_status_str,
            health_score=health_score,
            last_error=self._last_error,
            
            # Extended metrics (Sprint 28)
            authentication_status=auth_state,
            session_age_hours=round(session_age_hours, 2),
            token_expiry=token_expiry_str,
            last_login_time=last_login_str,
            session_valid=session_valid_bool,
            broker_version="KiteConnect v5.2",
            api_status="ONLINE" if self._last_error != "Network failure" else "OFFLINE"
        )
