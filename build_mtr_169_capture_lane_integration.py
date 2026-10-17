from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2/oracle_execution/solana_atomic_executor"

MODULE = r'''
"""MTR-169: Canonical pricing lane capture integration."""

from qseries_v2.oracle_execution.solana_atomic_executor import runtime as rt
from qseries_v2.oracle_execution.solana_atomic_executor import (
    mtr_168_fast_live_capture_boundary as m168
)

REVISION = "MTR169_CANONICAL_CAPTURE_LANE"


class IntegrationHold(RuntimeError):
    pass


def make_capture_lane(public_wallet, output_dir):
    """Create an unstarted, capture-only canonical pricing lane."""

    m168.validate_runtime_boundary()

    prepared = m168.prepare_capture(
        public_wallet,
        output_dir,
    )

    lane = rt.q20.LatestStateLane()

    safe_price = prepared["price"]

    if safe_price.__globals__.get("fast_live_attack") is not prepared["callback"]:
        raise IntegrationHold("CAPTURE_CALLBACK_NOT_BOUND")

    if safe_price.__globals__.get("compile_current") is not m168.forbidden:
        raise IntegrationHold("COMPILATION_GUARD_MISSING")

    if safe_price.__globals__.get("simulate_current") is not m168.forbidden:
        raise IntegrationHold("SIMULATION_GUARD_MISSING")

    lane._price = safe_price.__get__(
        lane,
        rt.q20.LatestStateLane,
    )

    if lane._price.__func__ is not safe_price:
        raise IntegrationHold("LANE_BINDING_FAILED")

    if lane._price.__self__ is not lane:
        raise IntegrationHold("LANE_INSTANCE_MISMATCH")

    return {
        "lane": lane,
        "callback": prepared["callback"],
        "counters": prepared["counters"],
        "safe_price": safe_price,
    }


def verify_lane(public_wallet, output_dir):
    original_price = rt.canonical_price
    original_attack = rt.fast_live_attack

    result = make_capture_lane(
        public_wallet,
        output_dir,
    )

    if rt.canonical_price is not original_price:
        raise IntegrationHold("PRODUCTION_PRICE_MUTATED")

    if rt.fast_live_attack is not original_attack:
        raise IntegrationHold("PRODUCTION_ATTACK_MUTATED")

    return result


def main():
    wallet = "11111111111111111111111111111111"

    result = verify_lane(
        wallet,
        "runtime_state/oracle/oracle_live_execution",
    )

    print("[MTR169_REVISION]", REVISION)
    print("[MTR169_LANE]", type(result["lane"]).__name__)
    print("[MTR169_CALLBACK]", "fast_live_attack")
    print("[MTR169_BINDING] PASS")
    print("[MTR169_CAPTURE_COUNTERS]", result["counters"])
    print("[LIVE_WEBSOCKET] NOT_STARTED")
    print("[PRODUCTION_RUNTIME] UNMODIFIED")
    print("[SCANNER] UNMODIFIED")
    print("[PRIVATE_KEY] NOT_USED")
    print("[SIGNING] FALSE")
    print("[BROADCAST] FALSE")


if __name__ == "__main__":
    main()
'''

TEST = r'''
import unittest

from qseries_v2.oracle_execution.solana_atomic_executor import (
    mtr_169_capture_lane_integration as m
)


class Tests(unittest.TestCase):

    def setUp(self):
        self.wallet = "11111111111111111111111111111111"
        self.output = "runtime_state/oracle/oracle_live_execution"

    def test_correct_boundary(self):
        self.assertEqual(
            m.m168.validate_runtime_boundary()["callback"],
            "fast_live_attack",
        )

    def test_lane_instance(self):
        result = m.verify_lane(self.wallet, self.output)

        self.assertIsInstance(
            result["lane"],
            m.rt.q20.LatestStateLane,
        )

    def test_price_method_binding(self):
        result = m.verify_lane(self.wallet, self.output)

        self.assertIs(
            result["lane"]._price.__func__,
            result["safe_price"],
        )

    def test_callback_identity(self):
        result = m.verify_lane(self.wallet, self.output)

        self.assertIs(
            result["safe_price"].__globals__["fast_live_attack"],
            result["callback"],
        )

    def test_compiler_guard(self):
        result = m.verify_lane(self.wallet, self.output)

        with self.assertRaises(m.m168.BoundaryHold):
            result["safe_price"].__globals__["compile_current"]()

    def test_simulation_guard(self):
        result = m.verify_lane(self.wallet, self.output)

        with self.assertRaises(m.m168.BoundaryHold):
            result["safe_price"].__globals__["simulate_current"]()

    def test_production_unchanged(self):
        before_price = m.rt.canonical_price
        before_attack = m.rt.fast_live_attack

        m.verify_lane(self.wallet, self.output)

        self.assertIs(m.rt.canonical_price, before_price)
        self.assertIs(m.rt.fast_live_attack, before_attack)

    def test_counters_fresh(self):
        first = m.verify_lane(self.wallet, self.output)
        second = m.verify_lane(self.wallet, self.output)

        self.assertIsNot(first["counters"], second["counters"])
        self.assertEqual(first["counters"]["captured"], 0)
        self.assertEqual(second["counters"]["captured"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
'''

ast.parse(MODULE)
ast.parse(TEST)

if not (PKG / "mtr_168_fast_live_capture_boundary.py").is_file():
    raise SystemExit("[HOLD] MTR-168 missing")

module_path = PKG / "mtr_169_capture_lane_integration.py"
test_path = ROOT / "test_mtr_169_capture_lane_integration.py"

module_path.write_text(MODULE, encoding="utf-8")
test_path.write_text(TEST, encoding="utf-8")

if module_path.read_text(encoding="utf-8") != MODULE:
    raise SystemExit("[FAIL] MODULE_READBACK")

if test_path.read_text(encoding="utf-8") != TEST:
    raise SystemExit("[FAIL] TEST_READBACK")

print("[PASS] MTR-169 INSTALLED")
print("[REVISION] MTR169_CANONICAL_CAPTURE_LANE")
print("[MODULE_TEST_READBACK] PASS")
print("[SCANNER] UNMODIFIED")
print("[PRIVATE_KEY] NOT_USED")
print("[SIGNING] FALSE")
print("[BROADCAST] FALSE")