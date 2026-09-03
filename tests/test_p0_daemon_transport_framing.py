"""
tests/test_p0_daemon_transport_framing.py

P0 Regression: Python daemon stdout NDJSON framing integrity.

Verifies that emit_daemon_message() is thread-safe and that concurrent
emission from multiple execution contexts cannot produce concatenated lines
that break Node's readline + JSON.parse protocol handler.

Tests:
  A - ConcurrentWriterStress      : 10 threads x 100 messages (all types)
  B - ResponseStateCollision      : exact production failure reproduction
  C - TickStateCollision          : high-frequency ticks vs. state publication
  D - AuthResponseCollision       : auth_event vs. stdin response
  E - ContractChecks              : emit_daemon_message API contract
"""
from __future__ import annotations

import io
import json
import sys
import threading
import unittest
from unittest.mock import patch

# Ensure the project root is on the path so server_bridge imports work.
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _import_emit():
    """Import emit_daemon_message cleanly, bypassing heavy daemon startup."""
    import src.server_bridge as sb
    return sb.emit_daemon_message, sb._stdout_protocol_lock


class _CapturedStdout:
    """Context manager: redirect sys.stdout to a StringIO buffer for the test."""

    def __enter__(self):
        self.buf = io.StringIO()
        self._patcher = patch("sys.stdout", self.buf)
        self._patcher.start()
        return self.buf

    def __exit__(self, *_):
        self._patcher.stop()


def _parse_lines(raw: str) -> list:
    """
    Split captured output on newlines and parse each non-empty line.
    Raises AssertionError on any parse failure.
    """
    results = []
    for i, line in enumerate(raw.splitlines()):
        if not line:
            continue
        try:
            results.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise AssertionError(
                f"Line {i} failed json.loads: {exc!r}\n"
                f"  Raw (first 300b): {line[:300]!r}"
            )
    return results


# ─────────────────────────────────────────────────────────────────────────────
# A  Concurrent writer stress
# ─────────────────────────────────────────────────────────────────────────────

class TestConcurrentWriterStress(unittest.TestCase):
    """
    10 threads each emit 100 messages covering all daemon message types.
    Total = 1 000 messages.
    """

    THREADS = 10
    MSGS_PER_THREAD = 100
    TOTAL = THREADS * MSGS_PER_THREAD

    def _worker(self, emit, thread_id, errors):
        try:
            for i in range(self.MSGS_PER_THREAD):
                msg_type = i % 5
                if msg_type == 0:
                    emit({"type": "state", "data": {"thread": thread_id, "seq": i, "runtime_id": "stress-test"}})
                elif msg_type == 1:
                    emit({"type": "tick", "symbol": "NSE:NIFTY 50", "data": {"last_price": 24500.0 + i, "thread": thread_id}})
                elif msg_type == 2:
                    emit({"type": "live_event", "data": {"symbol": "NSE:NIFTY 50", "price": 24500.0 + i, "thread": thread_id}})
                elif msg_type == 3:
                    emit({"type": "response", "requestId": f"req-{thread_id}-{i}", "success": True, "data": {"val": i}})
                else:
                    emit({"type": "auth_event", "brokerState": "CONNECTED_VERIFIED", "feedState": "READY", "timestamp": "2026-08-26T09:05:00Z"})
        except Exception as exc:
            errors.append(exc)

    def test_stress_no_concatenation(self):
        emit, _ = _import_emit()
        errors = []
        threads = []

        with _CapturedStdout() as buf:
            for t_id in range(self.THREADS):
                thr = threading.Thread(target=self._worker, args=(emit, t_id, errors))
                threads.append(thr)
            for thr in threads:
                thr.start()
            for thr in threads:
                thr.join(timeout=30)

        raw = buf.getvalue()

        self.assertEqual([], errors, f"Thread errors: {errors}")
        self.assertNotIn("}{", raw,
            "Detected '}{' in raw output -- at least two JSON objects were concatenated on one line")

        parsed = _parse_lines(raw)

        self.assertEqual(self.TOTAL, len(parsed),
            f"Expected {self.TOTAL} messages, got {len(parsed)}")

        valid_types = {"state", "tick", "live_event", "response", "auth_event", "feed_status"}
        for msg in parsed:
            self.assertIn("type", msg, f"Message missing 'type': {msg!r}")
            self.assertIn(msg["type"], valid_types,
                f"Unexpected message type: {msg['type']!r}")


# ─────────────────────────────────────────────────────────────────────────────
# B  Exact production failure: response + state collision
# ─────────────────────────────────────────────────────────────────────────────

class TestResponseStateCollision(unittest.TestCase):
    """
    Reproduce the exact 26 Aug 2026 incident.
    Thread 1 emits state, Thread 2 emits response simultaneously.
    Output must be exactly 2 * ITERATIONS independently parseable lines.
    """

    ITERATIONS = 500

    def test_response_state_no_interleave(self):
        emit, _ = _import_emit()

        state_payload = {
            "type": "state",
            "data": {
                "broker_status": {"status": "connected"},
                "normalized_status": "CONNECTED_VERIFIED",
                "authenticated": True,
                "session_valid": True,
                "state_sequence": 42,
                "runtime_id": "regression-test"
            }
        }
        response_payload = {
            "type": "response",
            "requestId": "req-collision-test",
            "success": True,
            "data": {"result": "ok"}
        }

        errors = []

        def emit_state():
            try:
                for _ in range(self.ITERATIONS):
                    emit(state_payload)
            except Exception as exc:
                errors.append(exc)

        def emit_response():
            try:
                for _ in range(self.ITERATIONS):
                    emit(response_payload)
            except Exception as exc:
                errors.append(exc)

        with _CapturedStdout() as buf:
            t1 = threading.Thread(target=emit_state)
            t2 = threading.Thread(target=emit_response)
            t1.start(); t2.start()
            t1.join(timeout=15); t2.join(timeout=15)

        raw = buf.getvalue()
        self.assertEqual([], errors)
        self.assertNotIn("}{", raw,
            "Concatenation detected: state and response messages merged on one line")

        parsed = _parse_lines(raw)
        self.assertEqual(self.ITERATIONS * 2, len(parsed),
            f"Expected {self.ITERATIONS * 2} lines, got {len(parsed)}")

        states = [m for m in parsed if m["type"] == "state"]
        responses = [m for m in parsed if m["type"] == "response"]
        self.assertEqual(self.ITERATIONS, len(states))
        self.assertEqual(self.ITERATIONS, len(responses))


# ─────────────────────────────────────────────────────────────────────────────
# C  Tick + state concurrent collision
# ─────────────────────────────────────────────────────────────────────────────

class TestTickStateCollision(unittest.TestCase):
    """
    High-frequency ticks from KiteTicker callback thread while canonical
    main loop publishes state. Every line must parse independently.
    """

    TICK_COUNT = 400
    STATE_COUNT = 100

    def test_tick_state_no_interleave(self):
        emit, _ = _import_emit()
        errors = []

        def emit_ticks():
            try:
                for i in range(self.TICK_COUNT):
                    emit({
                        "type": "tick",
                        "symbol": "NSE:NIFTY 50",
                        "data": {"last_price": 24500.0 + i, "instrument_token": 256265, "seq": i}
                    })
                    emit({
                        "type": "live_event",
                        "data": {"symbol": "NSE:NIFTY 50", "price": 24500.0 + i, "event_type": "TICK"}
                    })
            except Exception as exc:
                errors.append(exc)

        def emit_states():
            try:
                for i in range(self.STATE_COUNT):
                    emit({"type": "state", "data": {"state_sequence": i, "runtime_id": "tick-state-test"}})
            except Exception as exc:
                errors.append(exc)

        with _CapturedStdout() as buf:
            t1 = threading.Thread(target=emit_ticks)
            t2 = threading.Thread(target=emit_states)
            t1.start(); t2.start()
            t1.join(timeout=15); t2.join(timeout=15)

        raw = buf.getvalue()
        self.assertEqual([], errors)
        self.assertNotIn("}{", raw,
            "Concatenation detected between tick/live_event and state messages")

        parsed = _parse_lines(raw)
        expected = self.TICK_COUNT * 2 + self.STATE_COUNT
        self.assertEqual(expected, len(parsed),
            f"Expected {expected} messages, got {len(parsed)}")


# ─────────────────────────────────────────────────────────────────────────────
# D  Auth event + stdin response collision
# ─────────────────────────────────────────────────────────────────────────────

class TestAuthResponseCollision(unittest.TestCase):
    """
    Auth completion emits auth_event while stdin_reader simultaneously emits
    a response. Historically the worst collision scenario.
    """

    ITERATIONS = 300

    def test_auth_response_no_interleave(self):
        emit, _ = _import_emit()
        errors = []

        auth_payload = {
            "type": "auth_event",
            "brokerState": "CONNECTED_VERIFIED",
            "feedState": "READY",
            "timestamp": "2026-08-26T09:05:00Z"
        }
        response_payload = {
            "type": "response",
            "requestId": "req-auth-collision",
            "success": True,
            "data": {"brokerState": "CONNECTED_VERIFIED", "feedState": "READY"}
        }

        def emit_auth():
            try:
                for _ in range(self.ITERATIONS):
                    emit(auth_payload)
            except Exception as exc:
                errors.append(exc)

        def emit_responses():
            try:
                for _ in range(self.ITERATIONS):
                    emit(response_payload)
            except Exception as exc:
                errors.append(exc)

        with _CapturedStdout() as buf:
            t1 = threading.Thread(target=emit_auth)
            t2 = threading.Thread(target=emit_responses)
            t1.start(); t2.start()
            t1.join(timeout=15); t2.join(timeout=15)

        raw = buf.getvalue()
        self.assertEqual([], errors)
        self.assertNotIn("}{", raw,
            "Concatenation detected between auth_event and response messages")

        parsed = _parse_lines(raw)
        self.assertEqual(self.ITERATIONS * 2, len(parsed),
            f"Expected {self.ITERATIONS * 2} messages, got {len(parsed)}")

        auth_msgs = [m for m in parsed if m["type"] == "auth_event"]
        resp_msgs = [m for m in parsed if m["type"] == "response"]
        self.assertEqual(self.ITERATIONS, len(auth_msgs))
        self.assertEqual(self.ITERATIONS, len(resp_msgs))


# ─────────────────────────────────────────────────────────────────────────────
# E  emit_daemon_message API contract
# ─────────────────────────────────────────────────────────────────────────────

class TestEmitDaemonMessageContract(unittest.TestCase):
    """Basic unit tests for emit_daemon_message() contract."""

    def test_single_message_is_valid_json_line(self):
        emit, _ = _import_emit()
        with _CapturedStdout() as buf:
            emit({"type": "state", "data": {"ok": True}})
        raw = buf.getvalue()
        self.assertTrue(raw.endswith("\n"), "Output must end with exactly one newline")
        lines = [l for l in raw.split("\n") if l]
        self.assertEqual(1, len(lines), f"Expected exactly 1 line, got: {lines!r}")
        parsed = json.loads(lines[0])
        self.assertEqual("state", parsed["type"])

    def test_output_uses_compact_separators(self):
        """Compact JSON (no spaces after : or ,) keeps NDJSON lines small."""
        emit, _ = _import_emit()
        with _CapturedStdout() as buf:
            emit({"type": "tick", "symbol": "NSE:NIFTY 50", "data": {"last_price": 24500.0}})
        raw = buf.getvalue().strip()
        self.assertNotIn(": ", raw, "Expected compact separators (no ': ')")
        self.assertNotIn(", ", raw, "Expected compact separators (no ', ')")

    def test_encoding_failure_does_not_crash(self):
        """A payload that cannot be serialised must not raise from emit_daemon_message."""
        emit, _ = _import_emit()
        # default=str handles most types; verify no exception propagates.
        with _CapturedStdout():
            try:
                emit({"type": "test", "data": object()})
            except Exception as exc:
                self.fail(f"emit_daemon_message raised unexpectedly: {exc}")

    def test_sequential_two_messages_are_two_lines(self):
        """Calling emit twice sequentially from one thread must produce two distinct lines."""
        emit, _ = _import_emit()
        with _CapturedStdout() as buf:
            emit({"type": "state", "data": {"seq": 1}})
            emit({"type": "state", "data": {"seq": 2}})
        lines = [l for l in buf.getvalue().split("\n") if l]
        self.assertEqual(2, len(lines), f"Expected 2 lines, got {lines!r}")
        self.assertEqual(1, json.loads(lines[0])["data"]["seq"])
        self.assertEqual(2, json.loads(lines[1])["data"]["seq"])

    def test_payload_contract_preserved(self):
        """emit_daemon_message must not alter the payload structure."""
        emit, _ = _import_emit()
        original = {
            "type": "response",
            "requestId": "test-req-1",
            "success": True,
            "data": {"foo": "bar", "nested": {"x": 1}}
        }
        with _CapturedStdout() as buf:
            emit(original)
        parsed = json.loads(buf.getvalue().strip())
        self.assertEqual("response", parsed["type"])
        self.assertEqual("test-req-1", parsed["requestId"])
        self.assertTrue(parsed["success"])
        self.assertEqual({"foo": "bar", "nested": {"x": 1}}, parsed["data"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
