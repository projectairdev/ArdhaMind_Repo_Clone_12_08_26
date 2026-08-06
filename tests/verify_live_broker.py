import sys
import os

# Ensure workspace root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from kiteconnect import KiteConnect

def test_live_broker():
    api_key = "v9a94g597emt8vch"
    access_token = "C0ZCTUYp8cM5hVO2GXX77S7urS8oOqzp"
    
    print("Initializing KiteConnect with live credentials...")
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

    # 4. Positions
    try:
        positions = kite.positions()
        print(f"positions(): SUCCESS (Received type: {type(positions)})")
    except Exception as e:
        print(f"positions(): FAILED ({str(e)})")

    # 5. Orders
    try:
        orders = kite.orders()
        print(f"orders(): SUCCESS (Received type: {type(orders)}, Count: {len(orders)})")
    except Exception as e:
        print(f"orders(): FAILED ({str(e)})")

    # 6. Trades
    try:
        trades = kite.trades()
        print(f"trades(): SUCCESS (Received type: {type(trades)}, Count: {len(trades)})")
    except Exception as e:
        print(f"trades(): FAILED ({str(e)})")

if __name__ == "__main__":
    test_live_broker()
