from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2/oracle_execution/solana_atomic_executor"

MODULE = r'''
"""MTR-166: clean, capture-only callback replacement."""
import json
import time
from pathlib import Path

REVISION = "MTR166_CLEAN_CAPTURE_BOUNDARY"

COUNTER_NAMES = (
    "positive_seen",
    "captured",
    "wrong_direction",
    "wrong_size",
    "route_holds",
    "superseded",
)

def new_counters():
    return {name: 0 for name in COUNTER_NAMES}

def capture_callback(public_user, output_dir, counters):
    """Record a canonical route; never compile, sign, or broadcast."""
    if not isinstance(counters, dict):
        raise TypeError("COUNTERS_MUST_BE_DICTIONARY")

    for name in COUNTER_NAMES:
        counters.setdefault(name, 0)

    def capture(lane, token, snap, opportunity,
                slot, received_ns, generation):

        counters["positive_seen"] += 1

        if lane.newer_waiting(token, generation):
            counters["superseded"] += 1
            return

        if opportunity.get("direction") != "PUMP_TO_METEORA":
            counters["wrong_direction"] += 1
            return

        if int(opportunity.get("start", 0)) != 10000000:
            counters["wrong_size"] += 1
            return

        try:
            from qseries_v2.oracle_execution.solana_atomic_executor import runtime
            from qseries_v2.oracle_execution.solana_atomic_executor.mtr_164_live_route_capture import verify

            route = runtime.same_snapshot_route(
                public_user, snap, opportunity
            )
            evidence = verify(route)

        except Exception as exc:
            counters["route_holds"] += 1
            print(
                "[MTR166_ROUTE_HOLD]",
                type(exc).__name__,
                str(exc)[:100],
                flush=True,
            )
            return

        record = {
            "route": route,
            "token": token,
            "slot": int(slot),
            "captured_at": time.time(),
            "evidence": evidence,
            "protected_bounds_verified": False,
            "atomic_simulation_passed": False,
            "profit_certified": False,
            "broadcast_authorized": False,
        }

        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)

        destination = output / "mtr_166_captured_route.json"

        destination.write_text(
            json.dumps(record, indent=2, default=str),
            encoding="utf-8",
        )

        counters["captured"] += 1

        print("[MTR166_ROUTE_CAPTURED]", destination)

    return capture


def main():
    counters = new_counters()
    print("[MTR166] CLEAN_CAPTURE_BOUNDARY_READY")
    print("[MTR166_REVISION]", REVISION)
    print("[MTR166_COUNTERS]", json.dumps(counters))
    print("[LIVE_ROUTE] NOT_YET_CAPTURED")
    print("[PRIVATE_KEY] NOT_USED")
    print("[SIGNING] FALSE")
    print("[BROADCAST] FALSE")


if __name__ == "__main__":
    main()
'''

TEST = r'''
import tempfile
import unittest
from unittest.mock import Mock

from qseries_v2.oracle_execution.solana_atomic_executor import (
    mtr_166_capture_boundary_replacement as m
)


class Tests(unittest.TestCase):

    def test_all_counters_initialized(self):
        counters = m.new_counters()

        self.assertEqual(len(counters), 6)

        for value in counters.values():
            self.assertEqual(value, 0)

    def test_empty_counter_dictionary(self):
        counters = {}
        lane = Mock()
        lane.newer_waiting.return_value = False

        cb = m.capture_callback("public", "unused", counters)

        cb(
            lane,
            "token",
            {},
            {"direction": "METEORA_TO_PUMP", "start": 10000000},
            1,
            1,
            1,
        )

        self.assertEqual(counters["positive_seen"], 1)
        self.assertEqual(counters["wrong_direction"], 1)

    def test_same_dictionary_is_updated(self):
        counters = m.new_counters()
        lane = Mock()
        lane.newer_waiting.return_value = False

        cb = m.capture_callback("public", "unused", counters)

        cb(
            lane,
            "token",
            {},
            {"direction": "METEORA_TO_PUMP", "start": 10000000},
            1,
            1,
            1,
        )

        self.assertEqual(counters["wrong_direction"], 1)

    def test_superseded_rejected(self):
        counters = {}
        lane = Mock()
        lane.newer_waiting.return_value = True

        cb = m.capture_callback("public", "unused", counters)

        cb(
            lane,
            "token",
            {},
            {"direction": "PUMP_TO_METEORA", "start": 10000000},
            1,
            1,
            1,
        )

        self.assertEqual(counters["superseded"], 1)
        self.assertEqual(counters["captured"], 0)

    def test_wrong_size_rejected(self):
        counters = {}
        lane = Mock()
        lane.newer_waiting.return_value = False

        cb = m.capture_callback("public", "unused", counters)

        cb(
            lane,
            "token",
            {},
            {"direction": "PUMP_TO_METEORA", "start": 5000000},
            1,
            1,
            1,
        )

        self.assertEqual(counters["wrong_size"], 1)
        self.assertEqual(counters["captured"], 0)

    def test_no_execution_authority(self):
        import inspect

        source = inspect.getsource(m.capture_callback)

        forbidden = (
            "signed_tx(",
            "keypair(",
            "send_transaction(",
            "simulate_current(",
            "compile_current(",
        )

        for term in forbidden:
            self.assertNotIn(term, source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
'''

ast.parse(MODULE)
ast.parse(TEST)

if not (PKG / "mtr_164_live_route_capture.py").is_file():
    raise SystemExit("[HOLD] MTR-164 dependency missing")

module_path = PKG / "mtr_166_capture_boundary_replacement.py"
test_path = ROOT / "test_mtr_166_capture_boundary_replacement.py"

module_path.write_text(MODULE, encoding="utf-8")
test_path.write_text(TEST, encoding="utf-8")

if module_path.read_text(encoding="utf-8") != MODULE:
    raise SystemExit("[FAIL] MODULE_READBACK_MISMATCH")

if test_path.read_text(encoding="utf-8") != TEST:
    raise SystemExit("[FAIL] TEST_READBACK_MISMATCH")

print("[PASS] MTR-166 CLEAN REPLACEMENT INSTALLED")
print("[REVISION] MTR166_CLEAN_CAPTURE_BOUNDARY")
print("[MODULE_AND_TEST_READBACK] PASS")
print("[MTR165] RETIRED")
print("[PRIVATE_KEY] NOT_USED")
print("[SIGNING] FALSE")
print("[BROADCAST] FALSE")