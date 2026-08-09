import sys
import os

# Ensure workspace root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from kiteconnect import KiteConnect

def test_live_broker():
    api_key = os.environ.get("KITE_API_KEY", "")
    access_token = os.environ.get("KITE_ACCESS_TOKEN", "")

    if not api_key or not access_token:
        print("Skipping live broker check: KITE_API_KEY or KITE_ACCESS_TOKEN not set in environment.")
        return

    print("Initializing KiteConnect with environment credentials...")
    try:
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        print("KiteConnect initialization: SUCCESS")
    except Exception as e:
        print(f"KiteConnect initialization: FAILED ({str(e)})")
        return

    # 1. Profile
    try:
        profile = kite.profile()
        print(f"profile(): SUCCESS (Received type: {type(profile)})")
    except Exception as e:
        print(f"profile(): FAILED ({str(e)})")

    # 2. Margins
    try:
        margins = kite.margins()
        print(f"margins(): SUCCESS (Received type: {type(margins)})")
    except Exception as e:
        print(f"margins(): FAILED ({str(e)})")

    # 3. Holdings
    try:
        holdings = kite.holdings()
        print(f"holdings(): SUCCESS (Received type: {type(holdings)}, Count: {len(holdings)})")
    except Exception as e:
        print(f"holdings(): FAILED ({str(e)})")

if __name__ == "__main__":
    test_live_broker()
