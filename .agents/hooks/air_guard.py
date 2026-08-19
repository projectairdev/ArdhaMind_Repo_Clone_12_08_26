#!/usr/bin/env python3
"""
AIR Governance PreToolUse Hook Guard (Layer 2 Mechanical Hardening)
===================================================================
Intercepts tool calls (run_command, replace_file_content, write_to_file, multi_replace_file_content, delete_file)
to enforce environment safety, production immutability, and destructive command blocking.
"""

import sys
import json
import os
import re

PROD_PATH = "/opt/ArdhaMind"

DESTRUCTIVE_GIT_PATTERNS = [
    r"\bgit\s+reset\s+--hard\b",
    r"\bgit\s+clean\s+-[a-zA-Z]*f",
    r"\bgit\s+push\s+.*(--force|-f)\b",
    r"\bgit\s+checkout\s+--\s+\.",
    r"\bgit\s+restore\s+.*--source",
    r"\bgit\s+restore\s+\.",
]

DESTRUCTIVE_DB_PATTERNS = [
    r"\bDROP\s+DATABASE\b",
    r"\bDROP\s+TABLE\b",
    r"\bTRUNCATE\b",
    r"\bDELETE\s+FROM\s+\w+\s*(;|$)",
    r"\brm\s+.*\.sqlite\b",
    r"\brm\s+.*\.db\b",
]

LIVE_BROKER_PATTERNS = [
    r"\bplace_order\b",
    r"\bmodify_order\b",
    r"\bcancel_order\b",
    r"\bexit_position\b",
    r"kite\.place_order",
    r"orders/regular",
]

SERVICE_CONTROL_PATTERNS = [
    r"\bsystemctl\s+(restart|stop|start|disable|enable|daemon-reload)\b",
    r"\bservice\s+\w+\s+(restart|stop|start)\b",
    r"\bkill\b",
    r"\bkillall\b",
    r"\bpkill\b",
    r"\bfuser\s+-k\b",
]

DEPLOYMENT_PATTERNS = [
    r"\bnginx\s+-s\s+(reload|stop)\b",
    r"\bsystemctl\s+reload\s+nginx\b",
    r"/etc/nginx/",
    r"\.env\.production\b",
]


def is_production_target(file_path: str, cwd: str = None) -> bool:
    """Robust path canonicalization resolving relative paths, symlinks, and .. segments."""
    if not file_path:
        return False
    
    base_dir = cwd if (cwd and os.path.isabs(cwd)) else "/opt/ardhamind/staging"
    
    if not os.path.isabs(file_path):
        resolved = os.path.abspath(os.path.join(base_dir, file_path))
    else:
        resolved = os.path.abspath(file_path)

    try:
        real_p = os.path.realpath(resolved)
    except Exception:
        real_p = resolved

    if "/staging/" in resolved or resolved.endswith("/staging"):
        return False

    return real_p.startswith(PROD_PATH) or PROD_PATH in real_p or "/ArdhaMind" in resolved or "/ArdhaMind" in real_p


def evaluate_tool_call(tool_name: str, args: dict) -> dict:
    # 1. Direct File-Edit Tool Protection
    if tool_name in ("replace_file_content", "write_to_file", "multi_replace_file_content", "delete_file"):
        target_file = str(args.get("TargetFile") or args.get("target_file") or args.get("AbsolutePath") or "")
        cwd = str(args.get("Cwd") or args.get("cwd") or "")
        
        if is_production_target(target_file, cwd):
            return {
                "decision": "deny",
                "reason": f"PRODUCTION WRITE DENIED: Direct modification of production path '{target_file}' is strictly blocked by AIR Governance."
            }
        return {"decision": "allow", "reason": "Staging file edit permitted."}

    # 2. Shell Command Inspection (run_command)
    if tool_name == "run_command":
        cmd = str(args.get("CommandLine") or args.get("command_line") or args.get("cmd") or "")
        cwd = str(args.get("Cwd") or args.get("cwd") or "")

        # Production Write Inspection (including relative paths and indirect shell commands)
        if PROD_PATH in cmd or is_production_target(cwd) or re.search(r"\.\./[a-zA-Z]*ArdhaMind\b", cmd):
            # Check read-only production commands
            is_read_only = bool(re.search(r"\bgit\s+-C\s+\S*ArdhaMind\S*\s+(status|log|diff|show|branch)\b", cmd)) or \
                           bool(re.search(r"\b(cat|grep|rg|ls|stat|head|tail|wc|file)\s+.*", cmd))
            
            # If shell command contains write operators or modification patterns targeting production
            has_write_op = bool(re.search(r"\b(cp|mv|rm|sed\s+-i|touch|chmod|chown|tee)\b", cmd)) or \
                           bool(re.search(r">\s*", cmd)) or \
                           bool(re.search(r"\bgit\s+-C\s+\S*ArdhaMind\S*\s+(checkout|commit|pull|merge|reset|clean)\b", cmd)) or \
                           bool(re.search(r"(bash|sh)\s+-c\s+.*(cp|mv|rm|sed|>)", cmd))

            if has_write_op and not is_read_only:
                return {
                    "decision": "deny",
                    "reason": f"PRODUCTION WRITE DENIED: Shell operation targeting production path '{PROD_PATH}' is blocked."
                }

        # Destructive Git
        for pat in DESTRUCTIVE_GIT_PATTERNS:
            if re.search(pat, cmd, re.IGNORECASE):
                return {
                    "decision": "deny",
                    "reason": f"DESTRUCTIVE GIT DENIED: Command matched pattern '{pat}'."
                }

        # Destructive Database
        for pat in DESTRUCTIVE_DB_PATTERNS:
            if re.search(pat, cmd, re.IGNORECASE):
                return {
                    "decision": "deny",
                    "reason": f"DESTRUCTIVE DB DENIED: Command matched pattern '{pat}'."
                }

        # Live Broker Order
        for pat in LIVE_BROKER_PATTERNS:
            if re.search(pat, cmd, re.IGNORECASE):
                return {
                    "decision": "deny",
                    "reason": f"LIVE BROKER EXECUTION DENIED: Command matched live broker pattern '{pat}'."
                }

        # Service Control
        for pat in SERVICE_CONTROL_PATTERNS:
            if re.search(pat, cmd, re.IGNORECASE):
                return {
                    "decision": "ask",
                    "reason": f"SERVICE CONTROL APPROVAL REQUIRED: Command matched service lifecycle pattern '{pat}'."
                }

        # Deployment / Env
        for pat in DEPLOYMENT_PATTERNS:
            if re.search(pat, cmd, re.IGNORECASE):
                return {
                    "decision": "ask",
                    "reason": f"DEPLOYMENT APPROVAL REQUIRED: Command matched deployment pattern '{pat}'."
                }

        return {"decision": "allow", "reason": "Shell command permitted by AIR Governance."}

    # Fail-safe for unknown or ambiguous tools
    return {"decision": "ask", "reason": f"AIR Guard Fail-Safe: Intercepted unclassified tool '{tool_name}'."}


def main():
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            print(json.dumps({"decision": "ask", "reason": "AIR Guard Fail-Safe: Empty input payload."}))
            return

        payload = json.loads(raw_input)
        tool_call = payload.get("toolCall") or {}
        tool_name = str(tool_call.get("name") or "")
        args = tool_call.get("args") or {}

        result = evaluate_tool_call(tool_name, args)
        print(json.dumps(result))
    except Exception as e:
        # Fail closed with ASK on any error/malformed payload
        print(json.dumps({"decision": "ask", "reason": f"AIR Guard Fail-Safe Parser Error: {str(e)}"}))


if __name__ == "__main__":
    main()
