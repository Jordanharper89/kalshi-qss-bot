from pathlib import Path
import ast
import hashlib

ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2/oracle_execution/solana_atomic_executor"

MODULE = r'''
"""MTR-168: correct isolated fast_live_attack capture boundary."""

import types

from qseries_v2.oracle_execution.solana_atomic_executor import runtime as rt
from qseries_v2.oracle_execution.solana_atomic_executor.mtr_166_capture_boundary_replacement import (
    capture_callback,
    new_counters,
)

REVISION = "MTR168_FAST_LIVE_ATTACK_BOUNDARY"
CALLBACK_NAME = "fast_live_attack"


class BoundaryHold(RuntimeError):
    pass


def forbidden(*args, **kwargs):
    raise BoundaryHold("MTR168_EXECUTION_DISABLED")


def validate_runtime_boundary():
    price = rt.canonical_price

    names = set(price.__code__.co_names)

    if CALLBACK_NAME not in names:
        raise BoundaryHold("FAST_LIVE_ATTACK_NOT_IN_PRICE")

    if "attack" in names:
        raise BoundaryHold("AMBIGUOUS_ATTACK_BOUNDARY")

    if CALLBACK_NAME not in price.__globals__:
        raise BoundaryHold("FAST_LIVE_ATTACK_GLOBAL_MISSING")

    if not callable(price.__globals__[CALLBACK_NAME]):
        raise BoundaryHold("FAST_LIVE_ATTACK_NOT_CALLABLE")

    if price.__code__.co_freevars:
        raise BoundaryHold("UNEXPECTED_PRICE_CLOSURE")

    return {
        "revision": REVISION,
        "callback": CALLBACK_NAME,
        "source_file": price.__code__.co_filename,
        "source_line": price.__code__.co_firstlineno,
        "boundary_verified": True,
    }


def make_capture_price(callback):
    validate_runtime_boundary()

    original = rt.canonical_price

    isolated = dict(original.__globals__)

    isolated[CALLBACK_NAME] = callback

    # Any accidental attempt to reach these names must fail.
    for name in (
        "attack",
        "compile_current",
        "simulate_current",
        "_execute_route_once",
        "signed_tx",
        "send",
        "keypair",
    ):
        isolated[name] = forbidden

    safe = types.FunctionType(
        original.__code__,
        isolated,
        original.__name__,
        original.__defaults__,
        original.__closure__,
    )

    if safe is original:
        raise BoundaryHold("FUNCTION_NOT_ISOLATED")

    if safe.__globals__[CALLBACK_NAME] is not callback:
        raise BoundaryHold("CALLBACK_BINDING_FAILED")

    if rt.canonical_price is not original:
        raise BoundaryHold("PRODUCTION_PRICE_MUTATED")

    return safe


def prepare_capture(public_wallet, output_dir):
    if not isinstance(public_wallet, str):
        raise BoundaryHold("PUBLIC_WALLET_REQUIRED")

    try:
        raw = rt.q87.c.b58d(public_wallet)
    except Exception as exc:
        raise BoundaryHold("INVALID_PUBLIC_WALLET") from exc

    if len(raw) != 32:
        raise BoundaryHold("INVALID_PUBLIC_WALLET_LENGTH")

    counters = new_counters()

    callback = capture_callback(
        public_wallet,
        output_dir,
        counters,
    )

    price = make_capture_price(callback)

    return {
        "price": price,
        "callback": callback,
        "counters": counters,
    }


def main():
    result = validate_runtime_boundary()

    print("[MTR168_REVISION]", result["revision"])
    print("[MTR168_CALLBACK]", result["callback"])
    print("[MTR168_SOURCE]", result["source_file"])
    print("[MTR168_SOURCE_LINE]", result["source_line"])
    print("[MTR168_BOUNDARY] PASS")
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
from unittest.mock import Mock

from qseries_v2.oracle_execution.solana_atomic_executor import (
    mtr_168_fast_live_capture_boundary as m
)


class Tests(unittest.TestCase):

    def test_actual_runtime_callback(self):
        result = m.validate_runtime_boundary()
        self.assertEqual(
            result["callback"],
            "fast_live_attack",
        )

    def test_original_function_preserved(self):
        before = m.rt.canonical_price
        safe = m.make_capture_price(Mock())

        self.assertIs(m.rt.canonical_price, before)
        self.assertIsNot(safe, before)

    def test_correct_callback_replaced(self):
        callback = Mock()
        safe = m.make_capture_price(callback)

        self.assertIs(
            safe.__globals__["fast_live_attack"],
            callback,
        )

    def test_old_callback_not_used(self):
        safe = m.make_capture_price(Mock())

        with self.assertRaises(m.BoundaryHold):
            safe.__globals__["attack"]()

    def test_compiler_blocked(self):
        safe = m.make_capture_price(Mock())

        with self.assertRaises(m.BoundaryHold):
            safe.__globals__["compile_current"]()

    def test_simulator_blocked(self):
        safe = m.make_capture_price(Mock())

        with self.assertRaises(m.BoundaryHold):
            safe.__globals__["simulate_current"]()

    def test_execution_function_blocked(self):
        safe = m.make_capture_price(Mock())

        with self.assertRaises(m.BoundaryHold):
            safe.__globals__["_execute_route_once"]()

    def test_signer_blocked(self):
        safe = m.make_capture_price(Mock())

        with self.assertRaises(m.BoundaryHold):
            safe.__globals__["signed_tx"]()

    def test_broadcast_blocked(self):
        safe = m.make_capture_price(Mock())

        with self.assertRaises(m.BoundaryHold):
            safe.__globals__["send"]()

    def test_public_wallet_only(self):
        wallet = "11111111111111111111111111111111"

        prepared = m.prepare_capture(
            wallet,
            "runtime_state/oracle/oracle_live_execution",
        )

        self.assertEqual(
            prepared["counters"]["captured"],
            0,
        )

        self.assertTrue(callable(prepared["price"]))

    def test_invalid_wallet_rejected(self):
        with self.assertRaises(m.BoundaryHold):
            m.prepare_capture("invalid", "unused")

    def test_no_production_mutation(self):
        before = m.rt.canonical_price
        before_globals = before.__globals__

        m.make_capture_price(Mock())

        self.assertIs(m.rt.canonical_price, before)
        self.assertIs(before.__globals__, before_globals)

        self.assertIsNot(
            before.__globals__["fast_live_attack"],
            m.forbidden,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
'''

ast.parse(MODULE)
ast.parse(TEST)

dependency = PKG / "mtr_166_capture_boundary_replacement.py"

if not dependency.is_file():
    raise SystemExit(
        "[HOLD] MTR-166 certified dependency missing"
    )

module_path = PKG / "mtr_168_fast_live_capture_boundary.py"

test_path = ROOT / "test_mtr_168_fast_live_capture_boundary.py"

# Only new MTR-168 files are written.
module_path.write_text(MODULE, encoding="utf-8")
test_path.write_text(TEST, encoding="utf-8")

if module_path.read_text(encoding="utf-8") != MODULE:
    raise SystemExit("[FAIL] MODULE_READBACK")

if test_path.read_text(encoding="utf-8") != TEST:
    raise SystemExit("[FAIL] TEST_READBACK")

print("[PASS] MTR-168 INSTALLED")
print("[REVISION] MTR168_FAST_LIVE_ATTACK_BOUNDARY")
print("[MODULE_TEST_READBACK] PASS")
print("[MTR165] RETIRED")
print("[MTR167] RETIRED")
print("[PRODUCTION_RUNTIME] UNMODIFIED")
print("[SCANNER] UNMODIFIED")
print("[PRIVATE_KEY] NOT_USED")
print("[SIGNING] FALSE")
print("[BROADCAST] FALSE")