import subprocess
import json
from pathlib import Path

GUARD_SCRIPT = Path("/opt/ardhamind/staging/.agents/hooks/air_guard.py")


def run_guard(tool_name: str, args: dict, raw_payload: str = None) -> dict:
    if raw_payload is not None:
        input_data = raw_payload
    else:
        payload = {
            "toolCall": {
                "name": tool_name,
                "args": args
            },
            "stepIdx": 1,
            "conversationId": "test-convo-id"
        }
        input_data = json.dumps(payload)

    res = subprocess.run(
        ["python3", str(GUARD_SCRIPT)],
        input=input_data,
        capture_output=True,
        text=True
    )
    assert res.returncode == 0, f"Guard script failed with stderr: {res.stderr}"
    return json.loads(res.stdout)


def test_guard_safe_read_allow():
    res = run_guard("run_command", {"CommandLine": "git status"})
    assert res["decision"] == "allow"


def test_guard_safe_staging_test_allow():
    res = run_guard("run_command", {"CommandLine": "npm run typecheck"})
    assert res["decision"] == "allow"


def test_guard_production_read_allow():
    res = run_guard("run_command", {"CommandLine": "git -C /opt/ArdhaMind status --short"})
    assert res["decision"] == "allow"


def test_guard_production_write_deny():
    res = run_guard("run_command", {"CommandLine": "echo test > /opt/ArdhaMind/DO_NOT_CREATE"})
    assert res["decision"] == "deny"
    assert "PRODUCTION WRITE DENIED" in res["reason"]


def test_guard_relative_production_path_canonicalization_deny():
    res = run_guard("replace_file_content", {"TargetFile": "../ArdhaMind/src/App.tsx", "Cwd": "/opt/ardhamind/staging"})
    assert res["decision"] == "deny"
    assert "PRODUCTION WRITE DENIED" in res["reason"]


def test_guard_indirect_shell_bash_c_deny():
    res = run_guard("run_command", {"CommandLine": "bash -c 'cp test.txt /opt/ArdhaMind/'"})
    assert res["decision"] == "deny"
    assert "PRODUCTION WRITE DENIED" in res["reason"]


def test_guard_indirect_shell_sed_i_deny():
    res = run_guard("run_command", {"CommandLine": "sed -i 's/foo/bar/g' /opt/ArdhaMind/server.ts"})
    assert res["decision"] == "deny"
    assert "PRODUCTION WRITE DENIED" in res["reason"]


def test_guard_destructive_git_deny():
    res = run_guard("run_command", {"CommandLine": "git reset --hard"})
    assert res["decision"] == "deny"
    assert "DESTRUCTIVE GIT DENIED" in res["reason"]


def test_guard_service_control_ask():
    res = run_guard("run_command", {"CommandLine": "systemctl restart ardhamind.service"})
    assert res["decision"] == "ask"
    assert "SERVICE CONTROL APPROVAL REQUIRED" in res["reason"]


def test_guard_live_kite_order_deny():
    res = run_guard("run_command", {"CommandLine": "python3 submit_order.py --action place_order"})
    assert res["decision"] == "deny"
    assert "LIVE BROKER EXECUTION DENIED" in res["reason"]


def test_guard_fail_safe_malformed_json():
    res = run_guard("", {}, raw_payload="{malformed_json")
    assert res["decision"] == "ask"
    assert "AIR Guard Fail-Safe" in res["reason"]


def test_guard_fail_safe_unknown_tool():
    res = run_guard("unknown_unclassified_tool", {"action": "write"})
    assert res["decision"] == "ask"
    assert "AIR Guard Fail-Safe" in res["reason"]


def test_production_untouched():
    res = subprocess.run(["git", "-C", "/opt/ArdhaMind", "status", "--porcelain"], capture_output=True, text=True)
    assert res.stdout.strip() == "", f"Production git tree must be clean, got: {res.stdout}"
