from __future__ import annotations

import os
from kiteconnect import KiteConnect
from src.configuration_engine.runtime import Config
from src.utils import setup_logger

logger = setup_logger("KiteClient")


def make_kite() -> KiteConnect:
    api_key = Config.KITE_API_KEY
    access_token = Config.KITE_ACCESS_TOKEN

    if not api_key or not access_token:
        logger.error("Missing KITE_API_KEY or KITE_ACCESS_TOKEN in environment.")
        raise RuntimeError("Missing KITE_API_KEY or KITE_ACCESS_TOKEN.")

    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)
    return kite
