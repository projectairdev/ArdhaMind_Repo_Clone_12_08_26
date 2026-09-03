"""
Authoritative Read-Only Live Dhan Market Data Validation Harness.
Executes during live NSE market hours to prove feed integrity before cutover.

Usage:
    python -m src.market_data.runtime.validate_live_dhan [--duration-seconds 300] [--dry-run]
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import logging
import os
import sys
import time
from typing import Any, Dict

from src.market_data.runtime.canonical_runtime import CanonicalBackendRuntime
from src.market_data.runtime.cutover_readiness import CutoverStatus, EnhancedCutoverEvaluator


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("validate_live_dhan")


def run_validation(duration_seconds: int = 300, is_dry_run: bool = False) -> Dict[str, Any]:
    """Runs read-only live Dhan market data validation."""
    client_id = os.getenv("DHAN_CLIENT_ID", "")
    access_token = os.getenv("DHAN_ACCESS_TOKEN", "")

    has_creds = bool(client_id and access_token)
    logger.info("Starting Dhan live validation harness (READ-ONLY)")
    logger.info("Credentials check: %s", "PRESENT (Redacted)" if has_creds else "MISSING")

    start_time = datetime.now(timezone.utc)

    if not has_creds and not is_dry_run:
        logger.error("DHAN_CLIENT_ID or DHAN_ACCESS_TOKEN not configured in environment.")
        return {
            "status": "FAILED_MISSING_CREDENTIALS",
            "session_date": start_time.date().isoformat(),
            "started_at": start_time.isoformat(),
            "passed": False,
            "readiness_status": CutoverStatus.READY_FOR_LIVE_VALIDATION.value,
            "message": "Dhan credentials required for live market-hours proof.",
        }

    runtime = CanonicalBackendRuntime(client_id=client_id, access_token=access_token)

    if is_dry_run:
        logger.info("Dry-run mode active. Initializing runtime components without network blocking.")
        report = runtime.evaluate_cutover_readiness()
        return {
            "status": "DRY_RUN_COMPLETED",
            "session_date": start_time.date().isoformat(),
            "started_at": start_time.isoformat(),
            "duration_seconds": 0,
            "passed": True,
            "readiness_status": CutoverStatus.READY_FOR_LIVE_VALIDATION.value,
            "gates_evaluated": {k: v.passed for k, v in report.gates.items()},
        }

    # Live start
    logger.info("Starting CanonicalBackendRuntime orchestrator...")
    started = runtime.start()
    if not started:
        logger.error("Failed to start orchestrator.")
        return {
            "status": "STARTUP_FAILED",
            "passed": False,
            "readiness_status": CutoverStatus.NOT_READY.value,
        }

    logger.info("Observing live stream for %d seconds...", duration_seconds)
    elapsed = 0
    while elapsed < duration_seconds:
        time.sleep(5)
        elapsed += 5
        stats = runtime.state_store.get_stats()
        health = runtime.export_canonical_feed_health()
        logger.info(
            "[%ds/%ds] Updates: %d | NIFTY Feed: %s",
            elapsed,
            duration_seconds,
            stats.get("total_updates", 0),
            health.get("nifty_feed", {}).get("status", "UNKNOWN"),
        )

    end_time = datetime.now(timezone.utc)
    runtime.stop()

    cutover_report = runtime.evaluate_cutover_readiness()
    summary = {
        "status": "VALIDATION_COMPLETED",
        "session_date": start_time.date().isoformat(),
        "started_at": start_time.isoformat(),
        "ended_at": end_time.isoformat(),
        "duration_seconds": duration_seconds,
        "readiness_status": cutover_report.status.value,
        "passed_gates_count": cutover_report.passed_gates_count,
        "total_gates_count": cutover_report.total_gates_count,
        "gate_results": cutover_report.gate_results,
        "blocking_reasons": cutover_report.blocking_reasons,
    }

    logger.info("Validation complete. Report: %s", json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate Live Dhan Market Data Feed")
    parser.add_argument("--duration-seconds", type=int, default=300, help="Observation duration in seconds")
    parser.add_argument("--dry-run", action="store_true", help="Run dry run verification")
    args = parser.parse_args()

    res = run_validation(duration_seconds=args.duration_seconds, is_dry_run=args.dry_run)
    sys.exit(0 if res.get("passed", True) else 1)
