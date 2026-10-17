from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2/oracle_execution/solana_atomic_executor"

MODULE = r'''
"""MTR-170: isolated real-market route capture, no execution."""

import argparse
import json
import types
from pathlib import Path

from qseries_v2.oracle_execution.solana_atomic_executor import runtime as rt
from qseries_v2.oracle_execution.solana_atomic_executor import (
    mtr_168_fast_live_capture_boundary as m168
)
from qseries_v2.oracle_execution.solana_atomic_executor import (
    mtr_169_capture_lane_integration as m169
)

REVISION = "MTR170_INTEGRATED_CAPTURE_ONLY"


class CaptureHold(RuntimeError):
    pass


def forbidden(*args, **kwargs):
    raise CaptureHold("EXECUTION_PATH_DISABLED")


def inspect_boundary():
    """Reject changes to the canonical startup/callback contract."""

    price = rt.canonical_price
    run = rt.run

    if "fast_live_attack" not in price.__code__.co_names:
        raise CaptureHold("LIVE_CALLBACK_CHANGED")

    required = {
        "canonical_price",
        "serve_canonical",
        "prebuild_templates",
        "prebuild_meteora_templates",
    }

    if not required.issubset(set(run.__code__.co_names)):
        raise CaptureHold("CANONICAL_STARTUP_CHANGED")

    prohibited = {
        "signed_tx",
        "keypair",
        "send",
        "compile_current",
        "simulate_current",
        "fast_live_attack",
        "attack",
    }

    if prohibited.intersection(run.__code__.co_names):
        raise CaptureHold("UNSAFE_STARTUP_DEPENDENCY")

    if rt.canonical_price.__globals__ is not rt.run.__globals__:
        raise CaptureHold("RUNTIME_GLOBALS_CHANGED")

    m168.validate_runtime_boundary()

    return True


def prepare(public_wallet, output_dir):
    inspect_boundary()

    result = m169.verify_lane(
        public_wallet,
        output_dir,
    )

    safe_price = result["safe_price"]

    if safe_price.__globals__.get("fast_live_attack") is not result["callback"]:
        raise CaptureHold("CAPTURE_CALLBACK_NOT_BOUND")

    if result["lane"]._price.__func__ is not safe_price:
        raise CaptureHold("CAPTURE_LANE_NOT_BOUND")

    return result


def make_isolated_run(public_wallet, safe_price):
    """Clone the launcher globals; never patch production globals."""

    inspect_boundary()

    original = rt.run

    safe_globals = dict(original.__globals__)

    # Block direct execution paths in the isolated namespace.
    for name in (
        "attack",
        "fast_live_attack",
        "compile_current",
        "simulate_current",
        "_execute_route_once",
        "signed_tx",
        "keypair",
        "send",
    ):
        safe_globals[name] = forbidden

    safe_globals["canonical_price"] = safe_price

    # Avoid the original sim_identity(), which may inspect the
    # private-key environment variable.
    class PublicCore:
        def sim_identity(self):
            return None, public_wallet

    class PublicQ87:
        c = PublicCore()

    safe_globals["q87"] = PublicQ87()

    # Capture does not need a blockhash cache.
    # The production cache must remain untouched.
    safe_globals["BLOCKHASH"] = types.SimpleNamespace(
        start=lambda: None,
        close=lambda: None,
    )

    cloned = types.FunctionType(
        original.__code__,
        safe_globals,
        original.__name__,
        original.__defaults__,
        original.__closure__,
    )

    if cloned is original:
        raise CaptureHold("RUN_NOT_ISOLATED")

    if cloned.__globals__["canonical_price"] is not safe_price:
        raise CaptureHold("SAFE_PRICE_NOT_INSTALLED")

    if rt.run is not original:
        raise CaptureHold("PRODUCTION_RUN_MUTATED")

    return cloned


def run_capture(seconds, public_wallet, output_dir):
    if not 5 <= seconds <= 120:
        raise CaptureHold("DURATION_OUT_OF_BOUNDS")

    prepared = prepare(public_wallet, output_dir)

    safe_run = make_isolated_run(
        public_wallet,
        prepared["safe_price"],
    )

    print("[MTR170_MODE] LIVE_CAPTURE_ONLY", flush=True)
    print("[MTR170_CALLBACK] MTR166", flush=True)
    print("[MTR170_LANE] MTR169", flush=True)
    print("[PRIVATE_KEY] NOT_REQUESTED", flush=True)
    print("[SIGNING] DISABLED", flush=True)
    print("[BROADCAST] DISABLED", flush=True)

    try:
        safe_run(float(seconds))
    finally:
        counters = prepared["counters"]

        print(
            "[MTR170_CAPTURE_COUNTS]",
            json.dumps(counters, sort_keys=True),
            flush=True,
        )

        print("[PRODUCTION_RUNTIME] UNMODIFIED", flush=True)
        print("[SIGNING] FALSE", flush=True)
        print("[BROADCAST] FALSE", flush=True)

    return prepared["counters"]


def main(argv=None):
    parser = argparse.ArgumentParser()

    parser.add_argument("--live", action="store_true")
    parser.add_argument("--seconds", type=float, default=30)
    parser.add_argument("--public-wallet")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path.cwd() /
        "runtime_state/oracle/oracle_live_execution",
    )

    args = parser.parse_args(argv)

    inspect_boundary()

    if not args.live:
        print("[MTR170] INTEGRATED_CAPTURE_RUNNER_READY")
        print("[LIVE_WEBSOCKET] NOT_STARTED")
        print("[SIGNING] FALSE")
        print("[BROADCAST] FALSE")
        return

    if not args.public_wallet:
        raise SystemExit(
            "[HOLD] PUBLIC_WALLET_REQUIRED"
        )

    run_capture(
        args.seconds,
        args.public_wallet,
        args.output_dir,
    )


if __name__ == "__main__":
    main()
'''

TEST = r'''
import unittest
from unittest.mock import Mock

from qseries_v2.oracle_execution.solana_atomic_executor import (
    mtr_170_integrated_capture_runner as m
)


WALLET = "11111111111111111111111111111111"


class Tests(unittest.TestCase):

    def test_runtime_boundary(self):
        self.assertTrue(m.inspect_boundary())

    def test_capture_lane(self):
        result = m.prepare(WALLET, "unused")

        self.assertIs(
            result["safe_price"].__globals__["fast_live_attack"],
            result["callback"],
        )

    def test_isolated_run(self):
        prepared = m.prepare(WALLET, "unused")

        before = m.rt.run

        cloned = m.make_isolated_run(
            WALLET,
            prepared["safe_price"],
        )

        self.assertIs(m.rt.run, before)
        self.assertIsNot(cloned, before)

    def test_public_identity(self):
        prepared = m.prepare(WALLET, "unused")

        cloned = m.make_isolated_run(
            WALLET,
            prepared["safe_price"],
        )

        identity = (
            cloned.__globals__["q87"].c.sim_identity()
        )

        self.assertEqual(identity, (None, WALLET))

    def test_compilation_disabled(self):
        prepared = m.prepare(WALLET, "unused")

        cloned = m.make_isolated_run(
            WALLET,
            prepared["safe_price"],
        )

        with self.assertRaises(m.CaptureHold):
            cloned.__globals__["compile_current"]()

    def test_signing_disabled(self):
        prepared = m.prepare(WALLET, "unused")

        cloned = m.make_isolated_run(
            WALLET,
            prepared["safe_price"],
        )

        with self.assertRaises(m.CaptureHold):
            cloned.__globals__["signed_tx"]()

    def test_broadcast_disabled(self):
        prepared = m.prepare(WALLET, "unused")

        cloned = m.make_isolated_run(
            WALLET,
            prepared["safe_price"],
        )

        with self.assertRaises(m.CaptureHold):
            cloned.__globals__["send"]()

    def test_duration_guard(self):
        with self.assertRaises(m.CaptureHold):
            m.run_capture(500, WALLET, "unused")

    def test_default_does_not_start_network(self):
        m.main([])

    def test_original_runtime_preserved(self):
        original_run = m.rt.run
        original_price = m.rt.canonical_price

        prepared = m.prepare(WALLET, "unused")

        m.make_isolated_run(
            WALLET,
            prepared["safe_price"],
        )

        self.assertIs(m.rt.run, original_run)
        self.assertIs(m.rt.canonical_price, original_price)


if __name__ == "__main__":
    unittest.main(verbosity=2)
'''

ast.parse(MODULE)
ast.parse(TEST)

for dependency in (
    "mtr_166_capture_boundary_replacement.py",
    "mtr_168_fast_live_capture_boundary.py",
    "mtr_169_capture_lane_integration.py",
):
    if not (PKG / dependency).is_file():
        raise SystemExit(
            "[HOLD] MISSING_DEPENDENCY: " + dependency
        )

module_path = PKG / "mtr_170_integrated_capture_runner.py"
test_path = ROOT / "test_mtr_170_integrated_capture_runner.py"

module_path.write_text(MODULE, encoding="utf-8")
test_path.write_text(TEST, encoding="utf-8")

if module_path.read_text(encoding="utf-8") != MODULE:
    raise SystemExit("[FAIL] MODULE_READBACK")

if test_path.read_text(encoding="utf-8") != TEST:
    raise SystemExit("[FAIL] TEST_READBACK")

print("[PASS] MTR-170 INSTALLED")
print("[REVISION] MTR170_INTEGRATED_CAPTURE_ONLY")
print("[MODULE_TEST_READBACK] PASS")
print("[PRODUCTION_RUNTIME] UNMODIFIED")
print("[SIGNING] FALSE")
print("[BROADCAST] FALSE")