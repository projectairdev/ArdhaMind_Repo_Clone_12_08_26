from __future__ import annotations
import logging
import sqlite3
import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Any, Optional, List, Dict

logger = logging.getLogger("InstrumentCacheManager")

DB_PATH = "cache/instruments.db"
CACHE_VERSION = "1.0.0"

_IST = ZoneInfo("Asia/Kolkata")

# A cache from an earlier calendar day is "loadable" (better than no instrument
# master at all — all future option expiries are still valid) but not "fresh"
# (a same-day refresh is still wanted). Past this hard ceiling the cache is
# refused outright even as a stale fallback.
STALE_CACHE_CEILING_DAYS = 5

class InstrumentCacheManager:
    """
    Production-grade SQLite manager for instrument caching.
    Handles cache loading, saving, validation, age calculation, and invalidation.
    Supports version tracking and daily refresh.
    """

    @classmethod
    def _get_connection(cls) -> sqlite3.Connection:
        """Helper to get SQLite connection and ensure directory exists."""
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        return sqlite3.connect(DB_PATH)

    @classmethod
    def load_cache(cls, broker_name: str, allow_stale: bool = False) -> Optional[List[Dict[str, Any]]]:
        """Loads cached instruments if valid. Returns None if invalid or missing.

        With ``allow_stale=True`` the same-calendar-day (daily refresh) check is
        skipped so a cache from an earlier day — up to ``STALE_CACHE_CEILING_DAYS``
        old — is still returned. Version, broker and row-count integrity checks
        always apply. This is the last-resort fallback when a live re-download
        fails: a day-old instrument master still resolves every future expiry.
        """
        if not cls.cache_validation(broker_name, allow_stale=allow_stale):
            logger.info(f"Cache validation failed or cache is expired/missing for {broker_name}.")
            return None

        try:
            with cls._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT instrument_token, exchange_token, tradingsymbol, name, 
                           last_price, expiry, strike, tick_size, lot_size, 
                           instrument_type, segment, exchange 
                    FROM instruments
                """)
                rows = cursor.fetchall()
                instruments = [dict(row) for row in rows]
                logger.info(f"Successfully loaded {len(instruments)} instruments from cache for {broker_name}.")
                return instruments
        except Exception as e:
            logger.error(f"Error loading instrument cache: {e}")
            return None

    @classmethod
    def save_cache(cls, broker_name: str, data: Any) -> bool:
        """Saves instruments list or dict to local cache."""
        # Standardize format to list of dicts
        inst_list = []
        if isinstance(data, dict):
            inst_list = list(data.values()) if data else []
        elif isinstance(data, list):
            inst_list = data

        try:
            with cls._get_connection() as conn:
                cursor = conn.cursor()
                # Create tables if not exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS cache_metadata (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS instruments (
                        instrument_token INTEGER PRIMARY KEY,
                        exchange_token INTEGER,
                        tradingsymbol TEXT,
                        name TEXT,
                        last_price REAL,
                        expiry TEXT,
                        strike REAL,
                        tick_size REAL,
                        lot_size INTEGER,
                        instrument_type TEXT,
                        segment TEXT,
                        exchange TEXT
                    )
                """)

                # Truncate old instruments
                cursor.execute("DELETE FROM instruments")

                # Insert new instruments if any
                if inst_list:
                    cursor.executemany("""
                        INSERT OR REPLACE INTO instruments (
                            instrument_token, exchange_token, tradingsymbol, name,
                            last_price, expiry, strike, tick_size, lot_size,
                            instrument_type, segment, exchange
                        ) VALUES (
                            :instrument_token, :exchange_token, :tradingsymbol, :name,
                            :last_price, :expiry, :strike, :tick_size, :lot_size,
                            :instrument_type, :segment, :exchange
                        )
                    """, inst_list)

                # Save metadata
                now_str = datetime.now().isoformat()
                cursor.execute("INSERT OR REPLACE INTO cache_metadata (key, value) VALUES ('timestamp', ?)", (now_str,))
                cursor.execute("INSERT OR REPLACE INTO cache_metadata (key, value) VALUES ('version', ?)", (CACHE_VERSION,))
                cursor.execute("INSERT OR REPLACE INTO cache_metadata (key, value) VALUES ('record_count', ?)", (str(len(inst_list)),))
                cursor.execute("INSERT OR REPLACE INTO cache_metadata (key, value) VALUES ('broker', ?)", (broker_name,))

                conn.commit()
                logger.info(f"Successfully saved {len(inst_list)} instruments to cache for {broker_name} at {now_str}.")
                return True
        except Exception as e:
            logger.error(f"Error saving instrument cache: {e}")
            return False

    @classmethod
    def cache_exists(cls, broker_name: str) -> bool:
        """Checks if cache exists and matches the given broker."""
        if not os.path.exists(DB_PATH):
            return False
        try:
            with cls._get_connection() as conn:
                cursor = conn.cursor()
                # Check if metadata table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cache_metadata'")
                if not cursor.fetchone():
                    return False
                cursor.execute("SELECT value FROM cache_metadata WHERE key='broker'")
                row = cursor.fetchone()
                if not row:
                    return False
                return row[0] == broker_name
        except Exception:
            return False

    @classmethod
    def cache_age(cls, broker_name: str) -> float:
        """Returns cache age in hours. Returns float('inf') if missing or invalid."""
        if not cls.cache_exists(broker_name):
            return float('inf')
        try:
            with cls._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM cache_metadata WHERE key='timestamp'")
                row = cursor.fetchone()
                if not row:
                    return float('inf')
                ts_str = row[0]
                ts = datetime.fromisoformat(ts_str)
                age_seconds = (datetime.now() - ts).total_seconds()
                age_hours = max(0.0, age_seconds / 3600.0)
                if age_hours < 0.0002:
                    return 0.0
                return round(age_hours, 2)
        except Exception:
            return float('inf')

    @classmethod
    def cache_validation(cls, broker_name: str, allow_stale: bool = False) -> bool:
        """
        Validates cache integrity, version alignment, and daily refresh criteria.
        Returns True if cache is valid and from the CURRENT (IST) calendar day.

        With ``allow_stale=True`` the daily-refresh check is relaxed: a cache from
        an earlier day still passes as long as it is within
        ``STALE_CACHE_CEILING_DAYS`` and all integrity checks hold.
        """
        if not cls.cache_exists(broker_name):
            return False

        try:
            with cls._get_connection() as conn:
                cursor = conn.cursor()
                
                # Verify Version
                cursor.execute("SELECT value FROM cache_metadata WHERE key='version'")
                row_ver = cursor.fetchone()
                if not row_ver or row_ver[0] != CACHE_VERSION:
                    logger.info("Cache version mismatch.")
                    return False

                # Verify Broker
                cursor.execute("SELECT value FROM cache_metadata WHERE key='broker'")
                row_br = cursor.fetchone()
                if not row_br or row_br[0] != broker_name:
                    logger.info("Cache broker mismatch.")
                    return False

                # Verify Record Count matches DB rows
                cursor.execute("SELECT value FROM cache_metadata WHERE key='record_count'")
                row_count = cursor.fetchone()
                if not row_count:
                    return False
                meta_count = int(row_count[0])

                cursor.execute("SELECT COUNT(*) FROM instruments")
                db_count = cursor.fetchone()[0]
                if meta_count != db_count:
                    logger.warning(f"Cache integrity check failed: metadata count ({meta_count}) != row count ({db_count})")
                    return False

                # Daily Refresh Check: Ensure cache was saved on the same calendar day
                cursor.execute("SELECT value FROM cache_metadata WHERE key='timestamp'")
                row_ts = cursor.fetchone()
                if not row_ts:
                    return False
                ts_str = row_ts[0]
                ts = datetime.fromisoformat(ts_str)

                # "Today" on the exchange (IST), matching the option-expiry
                # comparison elsewhere. The VPS runs in UTC, which lags IST by a
                # full calendar day during 00:00-05:30 IST.
                today = datetime.now(_IST).date()
                if ts.date() != today:
                    age_days = (today - ts.date()).days
                    if not allow_stale:
                        logger.info(f"Cache is from a previous calendar day ({ts.date()}). Requires daily refresh.")
                        return False
                    if age_days > STALE_CACHE_CEILING_DAYS:
                        logger.warning(
                            f"Instrument cache is {age_days}d old (ceiling {STALE_CACHE_CEILING_DAYS}d) — "
                            "refusing even as a stale fallback."
                        )
                        return False
                    logger.warning(
                        f"Instrument cache is {age_days}d stale ({ts.date()}); accepting as a fallback "
                        "because a live re-download is unavailable."
                    )

                return True
        except Exception as e:
            logger.error(f"Error during cache validation: {e}")
            return False

    @classmethod
    def invalidate_cache(cls, broker_name: str) -> bool:
        """Invalidates / deletes current cache file."""
        logger.info(f"Invalidating instrument cache for {broker_name}")
        if os.path.exists(DB_PATH):
            try:
                os.remove(DB_PATH)
                logger.info("Successfully deleted instruments database file.")
                return True
            except Exception as e:
                logger.error(f"Failed to delete database file: {e}")
                # Fallback to truncation
                try:
                    with cls._get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("DROP TABLE IF EXISTS instruments")
                        cursor.execute("DROP TABLE IF EXISTS cache_metadata")
                        conn.commit()
                    return True
                except Exception as ex:
                    logger.error(f"Fallback database drop failed: {ex}")
                    return False
        return True
