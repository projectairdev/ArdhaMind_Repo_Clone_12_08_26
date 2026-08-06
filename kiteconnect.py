# Mock kiteconnect module to satisfy imports during testing without real installation
# But if real_kiteconnect is installed and live credentials are used, we proxy to it.
from __future__ import annotations
import os
import sys

# Attempt to load the real kiteconnect package from site-packages
_has_real = False
real_kiteconnect = None

# To avoid name collision and circular import with this file (kiteconnect.py),
# we temporarily remove the workspace root from sys.path and kiteconnect from sys.modules
original_path = sys.path.copy()
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != current_dir]

current_module = sys.modules.get('kiteconnect')
if 'kiteconnect' in sys.modules:
    del sys.modules['kiteconnect']

try:
    import kiteconnect as _real_kc
    real_kiteconnect = _real_kc
    _has_real = True
except ImportError:
    pass
finally:
    # Restore sys.path
    sys.path = original_path
    # Restore sys.modules so subsequent imports of 'kiteconnect' resolve to this module
    if current_module is not None:
        sys.modules['kiteconnect'] = current_module

class MockKiteConnect:
    def __init__(self, *args, **kwargs):
        pass

    def set_access_token(self, *args, **kwargs):
        pass

    def generate_session(self, *args, **kwargs):
        return {"access_token": "MOCK_ACCESS_TOKEN"}

    def profile(self, *args, **kwargs):
        client_id = os.getenv("KITE_CLIENT_ID", "MOCK_CLIENT")
        user_name = os.getenv("KITE_CLIENT_NAME", "Mock User")
        email = os.getenv("KITE_EMAIL", "mock@example.com")
        return {
            "client_id": client_id,
            "user_name": user_name,
            "email": email,
            "broker_name": "Zerodha"
        }

    def margins(self, *args, **kwargs):
        try:
            cash = float(os.getenv("KITE_AVAILABLE_CASH", "1000000.0"))
        except ValueError:
            cash = 1000000.0
        return {
            "equity": {
                "net": cash,
                "available": {"cash": cash},
                "utilised": {"debits": 0.0}
            },
            "commodity": {
                "net": 0.0,
                "available": {"cash": 0.0},
                "utilised": {"debits": 0.0}
            }
        }

    def holdings(self, *args, **kwargs):
        return [
            {
                "tradingsymbol": "SBIN",
                "exchange": "NSE",
                "instrument_token": 12345,
                "isin": "INE062A01020",
                "product": "CNC",
                "quantity": 100,
                "t1_quantity": 0,
                "realised_quantity": 100,
                "average_price": 550.0,
                "last_price": 560.0,
                "pnl": 1000.0,
                "unrealised_pnl": 1000.0,
                "value": 56000.0,
                "price": 560.0
            }
        ]

    def positions(self, *args, **kwargs):
        return {
            "net": [
                {
                    "tradingsymbol": "NIFTY26NOV24200CE",
                    "exchange": "NFO",
                    "product": "NRML",
                    "quantity": 500,
                    "buy_quantity": 500,
                    "sell_quantity": 0,
                    "average_price": 155.40,
                    "last_price": 160.0,
                    "pnl": 2300.0,
                    "m2m": 2300.0,
                    "realised": 0.0,
                    "unrealised": 2300.0,
                    "buy_value": 77700.0,
                    "sell_value": 0.0
                }
            ],
            "day": []
        }

    def orders(self, *args, **kwargs):
        return [
            {
                "order_id": "O10001",
                "exchange_order_id": "E10001",
                "tradingsymbol": "NIFTY26NOV24200CE",
                "exchange": "NFO",
                "transaction_type": "BUY",
                "quantity": 500,
                "product": "NRML",
                "order_type": "MARKET",
                "status": "COMPLETE",
                "price": 155.40,
                "filled_quantity": 500,
                "pending_quantity": 0,
                "order_timestamp": "2026-07-12 10:15:30",
                "status_message": "ORDER PLACED AND FILLED",
                "average_price": 155.40,
                "tag": ""
            }
        ]

    def order_history(self, *args, **kwargs):
        return []

    def trades(self, *args, **kwargs):
        return []

    def instruments(self, *args, **kwargs):
        return []

    def historical_data(self, *args, **kwargs):
        return []

    def quote(self, *args, **kwargs):
        return {}

    def ltp(self, *args, **kwargs):
        return {}


class KiteConnect:
    def __init__(self, api_key, *args, **kwargs):
        # Determine if we should use the real KiteConnect
        is_mock_key = (str(api_key).upper().startswith("MOCK") or str(api_key).upper().startswith("TEST"))
        use_real = _has_real and not is_mock_key
        
        if use_real:
            self._delegate = real_kiteconnect.KiteConnect(api_key, *args, **kwargs)
        else:
            self._delegate = MockKiteConnect(api_key, *args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._delegate, name)

    def __setattr__(self, name, value):
        if name == "_delegate":
            super().__setattr__(name, value)
        else:
            setattr(self._delegate, name, value)


if _has_real:
    exceptions = real_kiteconnect.exceptions
else:
    class exceptions:
        class TokenException(Exception): pass
        class InputException(Exception): pass
        class NetworkException(Exception): pass
        class DataException(Exception): pass


class MockKiteTicker:
    def __init__(self, api_key: str, access_token: str, **kwargs):
        self.api_key = api_key
        self.access_token = access_token
        self.on_ticks = None
        self.on_connect = None
        self.on_close = None
        self.on_error = None
        self.on_reconnect = None
        self.on_noreconnect = None
        self._connected = False

    def connect(self, threaded=False, disable_ssl_verification=False):
        self._connected = True
        if self.on_connect:
            self.on_connect(self, {})

    def close(self):
        self._connected = False
        if self.on_close:
            self.on_close(self, 1000, "Closed")

    def is_connected(self):
        return self._connected

    def subscribe(self, tokens):
        pass

    def unsubscribe(self, tokens):
        pass

    def set_mode(self, mode, tokens):
        pass


class KiteTicker:
    def __init__(self, api_key: str, access_token: str, **kwargs):
        is_mock_key = (str(api_key).upper().startswith("MOCK") or str(api_key).upper().startswith("TEST"))
        use_real = _has_real and not is_mock_key
        
        if use_real:
            self._delegate = real_kiteconnect.KiteTicker(api_key, access_token, **kwargs)
        else:
            self._delegate = MockKiteTicker(api_key, access_token, **kwargs)

    def __getattr__(self, name):
        return getattr(self._delegate, name)

    def __setattr__(self, name, value):
        if name == "_delegate":
            super().__setattr__(name, value)
        else:
            setattr(self._delegate, name, value)
