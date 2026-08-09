from __future__ import annotations

import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'").strip('"')
                        if k and k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass


def load_scoring_yaml() -> dict[str, dict[str, float]]:
    # Find scoring.yaml path
    base_dir = os.path.dirname(__file__)
    file_path = os.path.join(base_dir, "scoring.yaml")
    
    defaults = {
        "overall_weights": {
            "trend": 20.0,
            "options": 25.0,
            "volatility": 15.0,
            "liquidity": 15.0,
            "session": 10.0,
            "expiry": 5.0,
            "confluence": 10.0,
        },
        "trend_weights": {
            "trend_strength": 0.30,
            "ema_alignment": 0.20,
            "adx": 0.20,
            "slope": 0.15,
            "momentum": 0.15,
        },
        "option_weights": {
            "pcr": 0.20,
            "max_pain": 0.15,
            "oi_structure": 0.20,
            "oi_buildup": 0.15,
            "liquidity": 0.15,
            "iv": 0.05,
            "expected_move": 0.10,
        },
        "volatility_weights": {
            "atr": 0.25,
            "compression": 0.20,
            "expansion": 0.15,
            "iv_env": 0.20,
            "expected_move": 0.20,
        },
        "liquidity_weights": {
            "spread": 0.40,
            "volume": 0.25,
            "oi": 0.20,
            "tradability": 0.15,
        },
        "session_weights": {
            "session_type": 0.60,
            "is_tradable": 0.40,
        },
        "expiry_weights": {
            "days_remaining": 0.40,
            "expiry_type": 0.20,
            "classification": 0.40,
        },
        "confluence_weights": {
            "trend_confluence": 0.25,
            "support_resistance": 0.20,
            "option_bias": 0.20,
            "volatility": 0.15,
            "liquidity": 0.20,
        }
    }
    
    if not os.path.exists(file_path):
        return defaults
    
    try:
        import yaml
        with open(file_path, "r") as f:
            data = yaml.safe_load(f)
            if data:
                # Merge with defaults to ensure all keys exist
                for sec, keys in defaults.items():
                    if sec not in data:
                        data[sec] = keys
                    else:
                        for k, v in keys.items():
                            if k not in data[sec]:
                                data[sec][k] = v
                return data
    except Exception:
        pass

    # Custom line-by-line fallback parser for basic YAML structure
    config = {}
    current_section = None
    try:
        with open(file_path, "r") as f:
            for line in f:
                # Strip comments and whitespace
                line = line.split("#")[0].strip("\r\n")
                if not line.strip():
                    continue
                # section header
                if not line.startswith(" ") and ":" in line:
                    key = line.split(":")[0].strip()
                    config[key] = {}
                    current_section = key
                # key-value inside section
                elif line.startswith(" ") and ":" in line:
                    key, val = line.split(":", 1)
                    key = key.strip()
                    val = val.strip()
                    try:
                        parsed_val = float(val) if "." in val else int(val)
                    except ValueError:
                        parsed_val = val
                    if current_section:
                        config[current_section][key] = parsed_val
                    else:
                        config[key] = parsed_val
    except Exception:
        pass

    # Merge parsed config with defaults to ensure no keys are missing
    for sec, keys in defaults.items():
        if sec not in config:
            config[sec] = keys
        else:
            for k, v in keys.items():
                if k not in config[sec]:
                    config[sec][k] = v
    return config


class Config:
    SCORING = load_scoring_yaml()

    # Broker Abstraction Layer Config (Sprint 27)
    TRADING_MODE = os.getenv("TRADING_MODE", "LIVE_ZERODHA")
    BROKER_TYPE = "ZERODHA"
    CACHE_LOCATION = os.getenv("CACHE_LOCATION", "instrument_cache")
    
    try:
        HEARTBEAT_INTERVAL_SECONDS = int(os.getenv("HEARTBEAT_INTERVAL_SECONDS", "30"))
    except ValueError:
        HEARTBEAT_INTERVAL_SECONDS = 30

    try:
        RECONNECT_ATTEMPTS = int(os.getenv("RECONNECT_ATTEMPTS", "3"))
    except ValueError:
        RECONNECT_ATTEMPTS = 3

    try:
        REQUEST_TIMEOUT_SECONDS = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "10.0"))
    except ValueError:
        REQUEST_TIMEOUT_SECONDS = 10.0

    # Kite Credentials
    KITE_API_KEY = os.getenv("KITE_API_KEY", "")
    KITE_ACCESS_TOKEN = os.getenv("KITE_ACCESS_TOKEN", "")
    KITE_API_SECRET = os.getenv("KITE_API_SECRET", "")
    KITE_REDIRECT_URL = os.getenv("KITE_REDIRECT_URL", "http://127.0.0.1:3000/api/broker/callback")
    SESSION_CACHE_PATH = os.getenv("SESSION_CACHE_PATH", ".cache/session.json")
    AUTO_LOAD_SESSION = os.getenv("AUTO_LOAD_SESSION", "True").lower() == "true"
    AUTO_VALIDATE_SESSION = os.getenv("AUTO_VALIDATE_SESSION", "True").lower() == "true"
    
    try:
        CONNECTION_TIMEOUT = float(os.getenv("CONNECTION_TIMEOUT", "10.0"))
    except ValueError:
        CONNECTION_TIMEOUT = 10.0

    # Workspace Operating Mode Config (Sprint 29)
    WORKSPACE_MODE = "READ_ONLY"
    DEFAULT_WORKSPACE_MODE = "READ_ONLY"
    ALLOW_LIVE_TRADING = False
    REQUIRE_CONFIRMATION = os.getenv("REQUIRE_CONFIRMATION", "True").lower() == "true"
    SHOW_MODE_WARNING = os.getenv("SHOW_MODE_WARNING", "True").lower() == "true"
    AUTO_FALLBACK_TO_DEVELOPMENT = False

    # General configuration
    APP_URL = os.getenv("APP_URL", "http://localhost:3000")

    # Timeframe setup
    HIST_INTERVAL = "5minute"
    LOOKBACK_DAYS = 10
    SCAN_TOP_N_OPTIONS = 30
    SCAN_TOP_N_STOCKS = 12

    # Technical parameters
    EMA_FAST = 20
    EMA_SLOW = 50
    RSI_PERIOD = 14
    ATR_PERIOD = 14
    VOL_AVG_PERIOD = 20

    # Risk constraints
    ENTRY_BUFFER_ATR = 0.10
    SL_ATR_MULT = 0.80
    TARGET_ATR_MULT = 1.60

    KITE_API_KEY = os.getenv("KITE_API_KEY", "")
    KITE_API_SECRET = os.getenv("KITE_API_SECRET", "")
    KITE_REDIRECT_URL = os.getenv("KITE_REDIRECT_URL", "http://127.0.0.1:3000/api/broker/callback")

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    MIN_OPTION_LTP = 5.0
    MAX_OPTION_LTP = 500.0

    MAX_CAPITAL_PER_TRADE_OPTIONS = 40000.0
    MAX_RISK_PER_TRADE_OPTIONS = 3000.0

    MAX_CAPITAL_PER_TRADE_STOCKS = 30000.0
    MAX_RISK_PER_TRADE_STOCKS = 2500.0

    MIN_STOCK_LTP = 50.0
    MIN_STOCK_VOLUME_OPTIONS = 75000
    MIN_STOCK_VOLUME_STOCKS = 100000
    MIN_ABS_PCT_MOVE_OPTIONS = 0.7
    MIN_ABS_PCT_MOVE_STOCKS = 1.0

    BREAKOUT_VOL_MULT_OPTIONS = 1.10
    BREAKOUT_VOL_MULT_STOCKS = 1.20
    MIN_CONFIDENCE_TO_SHOW_OPTIONS = 0.40
    MIN_CONFIDENCE_TO_SHOW_STOCKS = 0.45
    SECTOR_STRENGTH_WEIGHT = 1.25

    # Option Quality Score Weights
    OQS_DISTANCE_MULT = 100.0
    OQS_COST_DIV = 10000.0
    OQS_LTP_MULT = 1.0
    OQS_OI_WEIGHT = 2.5
    OQS_VOLUME_WEIGHT = 1.5
    OQS_SPREAD_WEIGHT = 1.0

    EXPORT_JSON = True
    EXPORT_CSV = True
    EXPORT_DIR = "scanner_output"

    RETRY_ATTEMPTS = 3
    RETRY_SLEEP_SECONDS = 1.0

    # News Settings
    ENABLE_MARKET_NEWS = True
    MARKET_NEWS_QUERY_LIMIT = 4
    MARKET_NEWS_HEADLINE_LIMIT = 8
    MARKET_NEWS_TIMEOUT_SECONDS = 6.0

    # Symbol Sector Map
    SYMBOL_SECTOR_MAP = {
        "360ONE": "FINANCIALS",
        "ABB": "CAPITAL_GOODS",
        "ABCAPITAL": "FINANCIALS",
        "ABFRL": "CONSUMER",
        "ACC": "CEMENT",
        "ADANIENSOL": "ENERGY",
        "ADANIENT": "ENERGY",
        "ADANIGREEN": "ENERGY",
        "ADANIPORTS": "INFRA",
        "ADANIPOWER": "ENERGY",
        "AMBUJACEM": "CEMENT",
        "APOLLOHOSP": "PHARMA",
        "ASHOKLEY": "AUTO",
        "ASIANPAINT": "CONSUMER",
        "AUROPHARMA": "PHARMA",
        "AXISBANK": "FINANCIALS",
        "BAJAJ-AUTO": "AUTO",
        "BAJAJFINSV": "FINANCIALS",
        "BAJFINANCE": "FINANCIALS",
        "BANKBARODA": "FINANCIALS",
        "BEL": "DEFENCE",
        "BHARATFORG": "AUTO",
        "BHARTIARTL": "TELECOM",
        "BHEL": "CAPITAL_GOODS",
        "BIOCON": "PHARMA",
        "BPCL": "ENERGY",
        "BRITANNIA": "FMCG",
        "CANBK": "FINANCIALS",
        "CHOLAFIN": "FINANCIALS",
        "CIPLA": "PHARMA",
        "COALINDIA": "METALS",
        "COFORGE": "IT",
        "COLPAL": "FMCG",
        "DABUR": "FMCG",
        "DIVISLAB": "PHARMA",
        "DLF": "REALTY",
        "DRREDDY": "PHARMA",
        "EICHERMOT": "AUTO",
        "EXIDEIND": "AUTO",
        "FEDERALBNK": "FINANCIALS",
        "GAIL": "ENERGY",
        "GLENMARK": "PHARMA",
        "GMRINFRA": "INFRA",
        "GNFC": "CHEMICALS",
        "GODREJCP": "CONSUMER",
        "GRASIM": "CEMENT",
        "HAL": "DEFENCE",
        "HAVELLS": "CAPITAL_GOODS",
        "HCLTECH": "IT",
        "HDFCBANK": "FINANCIALS",
        "HDFCLIFE": "INSURANCE",
        "HEROMOTOCO": "AUTO",
        "HINDALCO": "METALS",
        "HINDCOPPER": "METALS",
        "HINDPETRO": "ENERGY",
        "HINDUNILVR": "FMCG",
        "ICICIBANK": "FINANCIALS",
        "ICICIGI": "INSURANCE",
        "ICICIPRULI": "INSURANCE",
        "IDEA": "TELECOM",
        "INDHOTEL": "CONSUMER",
        "INDIGO": "TRANSPORT",
        "INDUSINDBK": "FINANCIALS",
        "INFY": "IT",
        "IOC": "ENERGY",
        "IREDA": "FINANCIALS",
        "IRFC": "FINANCIALS",
        "ITC": "FMCG",
        "JINDALSTEL": "METALS",
        "JSWENERGY": "ENERGY",
        "JSWSTEEL": "METALS",
        "JUBLFOOD": "CONSUMER",
        "KOTAKBANK": "FINANCIALS",
        "LICHSGFIN": "FINANCIALS",
        "LT": "CAPITAL_GOODS",
        "LTIM": "IT",
        "LTTS": "IT",
        "M&M": "AUTO",
        "MANAPPURAM": "FINANCIALS",
        "MARICO": "FMCG",
        "MARUTI": "AUTO",
        "MCDOWELL-N": "CONSUMER",
        "MFSL": "FINANCIALS",
        "MOTHERSON": "AUTO",
        "MPHASIS": "IT",
        "NMDC": "METALS",
        "NTPC": "ENERGY",
        "OBEROIRLTY": "REALTY",
        "ONGC": "ENERGY",
        "PEL": "FINANCIALS",
        "PERSISTENT": "IT",
        "PETRONET": "ENERGY",
        "PNB": "FINANCIALS",
        "POLYCAB": "CAPITAL_GOODS",
        "POWERGRID": "ENERGY",
        "PVRINOX": "MEDIA",
        "RAMCOCEM": "CEMENT",
        "RECLTD": "FINANCIALS",
        "RELIANCE": "ENERGY",
        "SAIL": "METALS",
        "SBICARD": "FINANCIALS",
        "SBILIFE": "INSURANCE",
        "SBIN": "FINANCIALS",
        "SHRIRAMFIN": "FINANCIALS",
        "SIEMENS": "CAPITAL_GOODS",
        "SUNPHARMA": "PHARMA",
        "TATAELXSI": "IT",
        "TATAMOTORS": "AUTO",
        "TATAPOWER": "ENERGY",
        "TATASTEEL": "METALS",
        "TCS": "IT",
        "TECHM": "IT",
        "TITAN": "CONSUMER",
        "TORNTPHARM": "PHARMA",
        "TRENT": "CONSUMER",
        "TVSMOTOR": "AUTO",
        "ULTRACEMCO": "CEMENT",
        "VEDL": "METALS",
        "WIPRO": "IT",
        "ZYDUSLIFE": "PHARMA",
    }
