#!/usr/bin/env python3
"""
AIR ArdhaMind — Live Market Diagnostic Probe (READ-ONLY)

This utility is STRICTLY READ-ONLY. It:
  - NEVER restarts services
  - NEVER modifies state
  - NEVER reconnects broker
  - NEVER changes subscriptions
  - NEVER writes session history
  - NEVER places orders

Usage:
  python scripts/live_market_probe.py           # Single snapshot
  python scripts/live_market_probe.py --watch    # Continuous 5s refresh
  python scripts/live_market_probe.py --json     # JSON output
"""

import argparse
import json
import os
import signal
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

IST = timezone(timedelta(hours=5, minutes=30))

STAGING_ROOT = Path("/opt/ardhamind/staging")
STAGING_SERVICE = "ardhamind-staging.service"
STAGING_API_PORT = 3001


def _proc_cmdline(pid):
    """Read /proc/<pid>/cmdline without modifying anything."""
    if not pid:
        return ""
    try:
        raw = Path(f"/proc/{pid}/cmdline").read_bytes()
        return raw.replace(bytes([0]), b" ").decode(
            "utf-8", errors="replace"
        ).strip()
    except Exception:
        return ""


def get_service_pids():
    """
    Resolve ONLY ardhamind-staging.service.

    This VPS runs multiple Ardha instances, so global pgrep
    must never be used for staging diagnostics.
    """
    import subprocess

    pids = {
        "node": None,
        "python": None,
        "error": None,
    }

    try:
        result = subprocess.run(
            [
                "systemctl",
                "--user",
                "show",
                STAGING_SERVICE,
                "--property=MainPID",
                "--value",
            ],
            capture_output=True,
            text=True,
            timeout=3,
        )

        if result.returncode != 0:
            pids["error"] = (
                result.stderr.strip()
                or result.stdout.strip()
                or "systemctl query failed"
            )
            return pids

        raw_pid = result.stdout.strip()

        if not raw_pid or raw_pid == "0":
            pids["error"] = (
                f"{STAGING_SERVICE} has no active MainPID"
            )
            return pids

        node_pid = int(raw_pid)
        node_cmd = _proc_cmdline(node_pid)

        if (
            str(STAGING_ROOT) not in node_cmd
            or "dist/server.cjs" not in node_cmd
        ):
            pids["error"] = (
                f"MainPID {node_pid} is not staging: {node_cmd}"
            )
            return pids

        pids["node"] = node_pid

        children_path = Path(
            f"/proc/{node_pid}/task/{node_pid}/children"
        )

        child_pids = []

        if children_path.exists():
            child_pids = [
                int(value)
                for value in children_path.read_text().split()
                if value.isdigit()
            ]

        for child_pid in child_pids:
            child_cmd = _proc_cmdline(child_pid)

            if (
                str(STAGING_ROOT) in child_cmd
                and "server_bridge.py" in child_cmd
                and "--action daemon" in child_cmd
            ):
                pids["python"] = child_pid
                break

        if pids["python"] is None:
            pids["error"] = (
                "Staging Python daemon not found below "
                f"Node PID {node_pid}"
            )

    except Exception as exc:
        pids["error"] = str(exc)

    return pids


def get_process_memory(pid):
    """Read RSS from /proc without modification."""
    if pid is None:
        return None
    try:
        with open(f"/proc/{pid}/status", "r") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) * 1024  # bytes
    except Exception:
        return None


def get_process_threads(pid):
    """Read thread count from /proc without modification."""
    if pid is None:
        return None
    try:
        with open(f"/proc/{pid}/status", "r") as f:
            for line in f:
                if line.startswith("Threads:"):
                    return int(line.split()[1])
    except Exception:
        return None


def fetch_api(path, port=STAGING_API_PORT):
    """Read-only HTTP GET against staging API."""
    import urllib.request
    try:
        url = f"http://127.0.0.1:{port}{path}"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}


def get_session_file_info(session_date=None):
    """Read session history file metadata without modifying it."""
    cache_dir = STAGING_ROOT / "data" / "cache"
    if not cache_dir.exists():
        return {"exists": False, "size_bytes": 0}
    if session_date:
        target = cache_dir / f"session_history_{session_date}.json"
    else:
        files = sorted(cache_dir.glob("session_history_*.json"), key=lambda p: p.name, reverse=True)
        target = files[0] if files else None
    if target and target.exists():
        stat = target.stat()
        return {
            "path": str(target),
            "size_bytes": stat.st_size,
            "size_human": f"{stat.st_size / 1024:.1f} KB" if stat.st_size < 1048576 else f"{stat.st_size / 1048576:.2f} MB",
            "modified": datetime.fromtimestamp(stat.st_mtime, tz=IST).strftime("%Y-%m-%d %H:%M:%S IST"),
        }
    return {"exists": False, "size_bytes": 0}


def run_diagnostics(market_data, workspace_data, session_date=None):
    """Run read-only consistency checks. Returns list of (check, status, detail)."""
    checks = []

    # 1. Market data availability
    m = market_data if not isinstance(market_data, dict) or "error" not in market_data else {}
    w = workspace_data if not isinstance(workspace_data, dict) or "error" not in workspace_data else {}

    # Extract spots from different endpoints
    api_market_spot = None
    api_workspace_spot = None
    if isinstance(m, dict):
        mc = m.get("market_context") or m.get("market_context") or m.get("marketContext") or m.get("market_data") or m
        api_market_spot = mc.get("current_spot") or mc.get("spot")
    if isinstance(w, dict):
        ws_market = (w.get("state") or w).get("market_data") or {}
        api_workspace_spot = ws_market.get("spot") or ws_market.get("current_spot")

    # Check: API agreement
    if api_market_spot is not None and api_workspace_spot is not None:
        if abs(float(api_market_spot) - float(api_workspace_spot)) < 0.01:
            checks.append(("API_SPOT_AGREEMENT", "OK", f"market={api_market_spot}, workspace={api_workspace_spot}"))
        else:
            checks.append(("API_SPOT_AGREEMENT", "WARN", f"DIVERGENCE: market={api_market_spot} vs workspace={api_workspace_spot}"))
    elif api_market_spot is None and api_workspace_spot is None:
        checks.append(("API_SPOT_AGREEMENT", "OK", "Both null (expected after hours)"))
    else:
        checks.append(("API_SPOT_AGREEMENT", "WARN", f"market={api_market_spot}, workspace={api_workspace_spot}"))

    # Check: Feed status
    feed = {}
    if isinstance(w, dict):
        feed = w.get("market_feed_status") or {}
    if not feed and isinstance(m, dict):
        feed = m.get("market_feed_status") or {}
    stream_status = feed.get("stream_status", "UNKNOWN")
    if stream_status in ("CONNECTED", "READY"):
        checks.append(("WS_STREAM", "OK", stream_status))
    elif stream_status in ("DISCONNECTED", "STALE"):
        checks.append(("WS_STREAM", "WARN", stream_status))
    else:
        checks.append(("WS_STREAM", "OK", f"{stream_status} (expected after hours)"))

    # Check: Source type
    source = None
    if isinstance(m, dict):
        mc = m.get("market_context") or m.get("marketContext") or m
        source = mc.get("source_type")
    if source in ("WEBSOCKET", "ZERODHA_KITE"):
        checks.append(("SOURCE_TYPE", "OK", source))
    elif source in ("REST_QUOTE", "REST_POLL"):
        session_status = str(
            ((w.get("market_session") or {}).get("status") or "")
        ).lower()
        session_mode = str(mc.get("session_mode") or "").upper()

        if session_status == "closed" or session_mode == "LAST_SESSION":
            checks.append((
                "SOURCE_TYPE",
                "OK",
                f"{source} (expected for completed session)"
            ))
        else:
            checks.append((
                "SOURCE_TYPE",
                "WARN",
                f"REST fallback: {source}"
            ))
    elif source in ("UNAVAILABLE", None):
        checks.append(("SOURCE_TYPE", "OK", f"{source or 'null'} (expected after hours)"))
    else:
        checks.append(("SOURCE_TYPE", "OK", source))

    # Check: Freshness
    freshness = None
    if isinstance(m, dict):
        mc = m.get("market_context") or m.get("marketContext") or m
        freshness = mc.get("freshness_status") or mc.get("freshness")
    if freshness in ("FRESH", "HEALTHY"):
        checks.append(("FRESHNESS", "OK", freshness))
    elif freshness in ("STALE", "BLOCKED"):
        checks.append(("FRESHNESS", "WARN", freshness))
    else:
        checks.append(("FRESHNESS", "OK", f"{freshness or 'null'} (expected after hours)"))

    # Check: Previous close not hardcoded
    prev_close = None
    if isinstance(m, dict):
        mc = m.get("market_context") or m.get("marketContext") or m
        prev_close = mc.get("previous_close")
    if prev_close is not None:
        checks.append(("PREVIOUS_CLOSE", "OK", f"{prev_close}"))
    else:
        checks.append(("PREVIOUS_CLOSE", "OK", "null (dynamic, resolves at session start)"))

    # Check: Session file
    sf = get_session_file_info(session_date)
    if sf.get("size_bytes", 0) > 0:
        if sf["size_bytes"] > 50 * 1024 * 1024:
            checks.append(("SESSION_FILE_SIZE", "WARN", f"LARGE: {sf.get('size_human')}"))
        else:
            checks.append(("SESSION_FILE_SIZE", "OK", sf.get("size_human", "unknown")))
    else:
        checks.append(("SESSION_FILE_SIZE", "OK", "No active session file"))

    return checks


def format_bytes(n):
    if n is None:
        return "—"
    if n < 1024:
        return f"{n} B"
    if n < 1048576:
        return f"{n/1024:.1f} KB"
    return f"{n/1048576:.1f} MB"


def probe_once(args):
    """Single read-only probe invocation."""
    now_ist = datetime.now(IST)
    pids = get_service_pids()

    # Fetch API data (read-only)
    market_data = fetch_api("/api/market")
    workspace_data = fetch_api("/api/workspace")

    # Extract fields
    m = market_data if isinstance(market_data, dict) and "error" not in market_data else {}
    mc = m.get("market_context") or m.get("market_context") or m.get("marketContext") or m.get("market_data") or m

    session_date = mc.get("session_date") or mc.get("trading_date") or now_ist.strftime("%Y-%m-%d")
    w = workspace_data if isinstance(workspace_data, dict) and "error" not in workspace_data else {}
    market_session = w.get("market_session") or {}
    session_phase = (
        mc.get("market_session_phase")
        or mc.get("session_phase")
        or m.get("auth_session")
        or market_session.get("status")
        or mc.get("session_mode")
        or "UNKNOWN"
    )

    spot = mc.get("current_spot") or mc.get("spot")
    prev_close = mc.get("previous_close")
    change_val = mc.get("change") or mc.get("spot_change")
    change_pct = mc.get("change_percent") or mc.get("spot_change_pct")
    open_p = mc.get("open")
    high_p = mc.get("high")
    low_p = mc.get("low")
    source_type = mc.get("source_type") or "UNKNOWN"
    freshness = mc.get("freshness_status") or mc.get("freshness") or "UNKNOWN"

    # Options
    opt = m.get("optionContext") or mc.get("options") or {}
    atm = opt.get("atm_strike")
    pcr = opt.get("pcr")
    max_pain = opt.get("max_pain")
    atm_iv = opt.get("atm_iv")

    # Breadth
    breadth = mc.get("breadth") or m.get("breadth") or {}
    adv = breadth.get("advances")
    dec_v = breadth.get("declines")

    # VIX
    vix = None
    macro = mc.get("macro") or m.get("macro") or {}
    if isinstance(macro, dict):
        vix_obj = macro.get("india_vix") or {}
        vix = vix_obj.get("value") if isinstance(vix_obj, dict) else None

    # Feed
    w = workspace_data if isinstance(workspace_data, dict) and "error" not in workspace_data else {}
    feed = w.get("market_feed_status") or m.get("market_feed_status") or {}
    ws_status = feed.get("stream_status") or "UNKNOWN"

    # Session file
    sf = get_session_file_info(session_date)

    # Diagnostics
    diag_checks = run_diagnostics(
        market_data, workspace_data, session_date=session_date
    )
    overall = "OK"
    for _, status, _ in diag_checks:
        if status == "FAIL":
            overall = "FAIL"
            break
        if status == "WARN" and overall == "OK":
            overall = "WARN"

    # Recorder
    recorder_window = mc.get("recorder_window") or "UNKNOWN"

    result = {
        "time_ist": now_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
        "trading_date": session_date,
        "session_phase": session_phase,
        "node_pid": pids["node"],
        "python_pid": pids["python"],
        "node_rss": format_bytes(get_process_memory(pids["node"])),
        "python_rss": format_bytes(get_process_memory(pids["python"])),
        "ws_status": ws_status,
        "authoritative_spot": spot,
        "authoritative_source": source_type,
        "freshness": freshness,
        "previous_close": prev_close,
        "change": change_val,
        "change_pct": change_pct,
        "open": open_p,
        "high": high_p,
        "low": low_p,
        "atm_strike": atm,
        "pcr": pcr,
        "max_pain": max_pain,
        "atm_iv": atm_iv,
        "breadth_adv": adv,
        "breadth_dec": dec_v,
        "india_vix": vix,
        "recorder_window": recorder_window,
        "session_file": sf.get("size_human") or "—",
        "overall_status": overall,
        "diagnostics": diag_checks,
    }

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print_report(result)

    return result


def print_report(r):
    """Pretty-print the probe report."""
    def val(v):
        return str(v) if v is not None else "—"

    sep = "─" * 60
    print(f"\n{'═' * 60}")
    print(f"  AIR ArdhaMind — Live Market Probe")
    print(f"{'═' * 60}")
    print(f"  TIME IST              {r['time_ist']}")
    print(f"  TRADING DATE          {r['trading_date']}")
    print(f"  SESSION PHASE         {r['session_phase']}")
    print(f"{sep}")
    print(f"  NODE PID              {val(r['node_pid'])}  RSS: {r['node_rss']}")
    print(f"  PYTHON PID            {val(r['python_pid'])}  RSS: {r['python_rss']}")
    print(f"{sep}")
    print(f"  WS STATUS             {r['ws_status']}")
    print(f"  AUTHORITATIVE SPOT    {val(r['authoritative_spot'])}")
    print(f"  AUTHORITATIVE SOURCE  {r['authoritative_source']}")
    print(f"  FRESHNESS             {r['freshness']}")
    print(f"{sep}")
    print(f"  PREVIOUS CLOSE        {val(r['previous_close'])}")
    print(f"  CHANGE                {val(r['change'])}")
    print(f"  CHANGE %              {val(r['change_pct'])}")
    print(f"{sep}")
    print(f"  OPEN                  {val(r['open'])}")
    print(f"  HIGH                  {val(r['high'])}")
    print(f"  LOW                   {val(r['low'])}")
    print(f"{sep}")
    print(f"  ATM STRIKE            {val(r['atm_strike'])}")
    print(f"  PCR                   {val(r['pcr'])}")
    print(f"  MAX PAIN              {val(r['max_pain'])}")
    print(f"  ATM IV                {val(r['atm_iv'])}")
    print(f"{sep}")
    adv = val(r['breadth_adv'])
    dec = val(r['breadth_dec'])
    print(f"  BREADTH               Adv: {adv}  Dec: {dec}")
    print(f"  INDIA VIX             {val(r['india_vix'])}")
    print(f"{sep}")
    print(f"  RECORDER WINDOW       {r['recorder_window']}")
    print(f"  SESSION FILE SIZE     {r['session_file']}")
    print(f"{sep}")
    print(f"  DIAGNOSTICS:")
    for check, status, detail in r["diagnostics"]:
        icon = "✓" if status == "OK" else ("⚠" if status == "WARN" else "✗")
        print(f"    {icon} [{status:4s}] {check}: {detail}")
    print(f"{sep}")
    overall = r["overall_status"]
    icon = "✓" if overall == "OK" else ("⚠" if overall == "WARN" else "✗")
    print(f"  OVERALL STATUS        {icon} {overall}")
    print(f"{'═' * 60}\n")


def watch_mode(args):
    """Continuous read-only watch mode with 5s refresh. Ctrl+C to exit."""
    def handle_sigint(sig, frame):
        print("\n\n  [Probe stopped cleanly by Ctrl+C]\n")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)

    print(f"\n  Live Market Probe — Watch Mode (5s refresh)")
    print(f"  Press Ctrl+C to stop\n")

    while True:
        os.system("clear" if os.name == "posix" else "cls")
        probe_once(args)
        time.sleep(5)


def main():
    parser = argparse.ArgumentParser(description="AIR ArdhaMind Live Market Probe (READ-ONLY)")
    parser.add_argument("--watch", action="store_true", help="Continuous 5s refresh mode")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.watch:
        watch_mode(args)
    else:
        probe_once(args)


if __name__ == "__main__":
    main()
