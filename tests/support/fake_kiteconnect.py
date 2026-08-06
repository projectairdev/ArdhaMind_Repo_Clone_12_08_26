"""Explicit test-only Kite doubles. Never import this module from production code."""


class FakeKiteConnect:
    def __init__(self, api_key: str = "test-key"):
        self.api_key = api_key
        self.access_token = None

    def set_access_token(self, token: str) -> None:
        self.access_token = token

    def profile(self) -> dict[str, str]:
        return {"client_id": "MOCK_CLIENT", "user_name": "Test User"}

    def generate_session(self, request_token: str, api_secret: str) -> dict[str, str]:
        return {"access_token": "test-access-token"}


class FakeKiteTicker:
    MODE_FULL = "full"

    def __init__(self, api_key: str, access_token: str, **kwargs):
        self.api_key = api_key
        self.access_token = access_token
        self._connected = False

    def connect(self, threaded: bool = True) -> None:
        self._connected = True

    def close(self) -> None:
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def subscribe(self, tokens):
        return tokens

    def unsubscribe(self, tokens):
        return tokens

    def set_mode(self, mode, tokens):
        return None
