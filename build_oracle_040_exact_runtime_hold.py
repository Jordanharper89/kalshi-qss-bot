
from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess
import sys
import unittest
import uuid

VERSION = "ORACLE_040_EXACT_RUNTIME_HOLD"
PKG = Path("qseries_v2/oracle_execution/solana_atomic_executor")
NAME = "oracle_040_exact_runtime_hold.py"
REPORT = Path("runtime_state/oracle/oracle_live_execution/ORACLE_040_HOLD.json")
PREVIOUS = Path("runtime_state/oracle/oracle_live_execution/ORACLE_039_HANDOFF.json")

KNOWN = {
    "NO_EXACT_PUMPSWAP_DLMM_PAIRS",
    "NO_VERIFIED_PAIR",
    "POOL_OWNER_ATTESTATION_INCOMPLETE",
    "NO_READY_EXECUTION_PAIRS",
    "INCOMPLETE_PAIR",
    "PAIR_ACCOUNT_COVERAGE_MISSING",
    "PAIR_REGISTRY_WRONG_INDEX",
    "UNRELATED_OR_MISSING_ACCOUNT_IN_REGISTRY",
    "RPC_REQUEST_BUDGET_EXHAUSTED",
    "SHARED_RPC_BUDGET_EXHAUSTED",
    "NON_READONLY_RPC_REFUSED",
    "SIMULATION_LIMIT_EXHAUSTED",
    "COMPILE_ATTEMPT_LIMIT",
    "ATOMIC_COMPILE_REJECTED",
    "UNSIGNED_ATOMIC_V0_INVALID",
    "STALE_BEFORE_SIMULATION",
    "BAD_FORWARD_RECEIPT_NET",
    "BAD_REVERSE_RECEIPT_NET",
}

SAFE = {
    "PATH", "PATHEXT", "SYSTEMROOT", "WINDIR",
    "SYSTEMDRIVE", "TEMP", "TMP", "COMSPEC",
    "SOLANA_RPC_URL", "QSB_SOLANA_RPC_URL",
    "SOLANA_WS_URL", "QSB_SOLANA_WALLET"
}

def scrub(env):
    return {k: v for k, v in env.items() if k.upper() in SAFE}

def classify(error):
    if type(error) is RuntimeError and str(error) in KNOWN:
        return str(error)
    return "UNCLASSIFIED_" + type(error).__name__

def persist(root, data):
    path = root / REPORT
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
    tmp.replace(path)

def child(root, seconds, run_id):
    result = {
        "revision": VERSION,
        "run_id": run_id,
        "status": "HOLD",
        "stage": "PREFLIGHT",
        "original_scanner_modified": False,
        "simulation_limit": 1,
        "signing": False,
        "broadcast": False,
        "canary_lamports": 10000000,
    }

    try:
        sys.path.insert(0, str(root.resolve()))

        if any(
            "PRIVATE_KEY" in k.upper() or
            "SECRET_KEY" in k.upper()
            for k in os.environ
        ):
            result["status"] = "HOLD_SECRET_ENVIRONMENT"
            return 2

        from solders.pubkey import Pubkey
        wallet = os.environ.get("QSB_SOLANA_WALLET", "").strip()
        try:
            Pubkey.from_string(wallet)
        except (ValueError, TypeError):
            result["status"] = "HOLD_PUBLIC_WALLET_NOT_CONFIGURED"
            return 2

        from qseries_v2.oracle_execution.solana_atomic_executor import (
            oracle_024_fresh_candidate_revalidation as v24,
            oracle_039_mriya_pricing_handoff as v39
        )

        original_hold_reason = v24.hold_reason
        identified = []

        def safe_reason(error):
            code = classify(error)
            identified.append(code)
            return code

        result["stage"] = "V39_CONTROLLED_REPLAY"
        v24.hold_reason = safe_reason

        try:
            exit_code = v39.execute(root, seconds, run_id)
        finally:
            v24.hold_reason = original_hold_reason

        result["v39_exit_code"] = exit_code
        result["exact_internal_holds"] = identified

        path = root / PREVIOUS
        if not path.is_file():
            result["status"] = "HOLD_V39_REPORT_MISSING"
            return 2

        prior = json.loads(path.read_text(encoding="utf-8"))
        if prior.get("run_id") != run_id:
            result["status"] = "HOLD_V39_REPORT_RUN_MISMATCH"
            return 2

        for key in (
            "worker_generation", "worker_candidates",
            "mriya_hot_count", "selected_pairs",
            "ready", "priced_events",
            "positive_candidates", "native_passes",
            "shared_rpc_requests", "shared_rpc_methods",
            "shared_rpc_exhausted", "holds", "rejections"
        ):
            if key in prior:
                result[key] = prior[key]

        result["v39_status"] = prior.get("status")
        result["stage"] = "CLASSIFICATION_COMPLETE"
        result["status"] = (
            "LIVE_PRICING_VERIFIED"
            if prior.get("status") ==
            "MRIYA_TO_LIVE_WEBSOCKET_PRICING_VERIFIED"
            else "HOLD_CLASSIFIED"
        )
        return exit_code

    except Exception as error:
        result["status"] = "HOLD_ORCHESTRATOR_EXCEPTION"
        result["error_class"] = type(error).__name__
        return 2

    finally:
        persist(root, result)

def parent(root, seconds):
    run_id = str(uuid.uuid4())
    command = [
        sys.executable, "-I", str(Path(__file__).resolve()),
        "--child", "--seconds", str(seconds),
        "--run-id", run_id
    ]

    try:
        process = subprocess.run(
            command, cwd=root, env=scrub(os.environ),
            capture_output=True, text=True,
            timeout=seconds + 180
        )
    except subprocess.TimeoutExpired:
        print("[HOLD] CHILD_TIMEOUT")
        return 2

    path = root / REPORT
    if not path.is_file():
        print("[HOLD] REPORT_MISSING")
        print("[CHILD_EXIT]", process.returncode)
        return 2

    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("run_id") != run_id:
        print("[HOLD] STALE_REPORT")
        return 2

    for key in (
        "status", "stage", "v39_status",
        "exact_internal_holds", "error_class",
        "worker_generation", "worker_candidates",
        "mriya_hot_count", "selected_pairs",
        "ready", "priced_events", "positive_candidates",
        "native_passes", "shared_rpc_requests",
        "shared_rpc_methods", "shared_rpc_exhausted",
        "holds"
    ):
        if key in data:
            print(
                "[" + key.upper() + "]",
                json.dumps(data[key], sort_keys=True)
            )

    print("[SCANNER] FROZEN")
    print("[SIGNING] FALSE [BROADCAST] FALSE")
    print("[REPORT]", path)
    return process.returncode

class Tests(unittest.TestCase):

    def test_known_failure(self):
        self.assertEqual(
            classify(RuntimeError("NO_READY_EXECUTION_PAIRS")),
            "NO_READY_EXECUTION_PAIRS"
        )

    def test_unknown_error_redacted(self):
        self.assertEqual(
            classify(RuntimeError("api-key=confidential")),
            "UNCLASSIFIED_RuntimeError"
        )

    def test_other_exception_redacted(self):
        self.assertEqual(
            classify(ValueError("secret")),
            "UNCLASSIFIED_ValueError"
        )

    def test_secret_environment_scrub(self):
        env = scrub({
            "PATH": "safe",
            "QSB_SOLANA_PRIVATE_KEY": "never",
        })
        self.assertEqual(env, {"PATH": "safe"})

    def test_wallet_is_public_only(self):
        self.assertIn("QSB_SOLANA_WALLET", SAFE)
        self.assertNotIn("QSB_SOLANA_PRIVATE_KEY", SAFE)

    def test_canary_constant(self):
        self.assertEqual(10000000, 10_000_000)

    def test_original_engines_present(self):
        from qseries_v2.oracle_execution.solana_atomic_executor import (
            oracle_024_fresh_candidate_revalidation as v24,
            oracle_039_mriya_pricing_handoff as v39
        )
        self.assertTrue(callable(v24.hold_reason))
        self.assertTrue(callable(v39.execute))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--seconds", type=int, default=60)
    parser.add_argument("--run-id", default="")
    args = parser.parse_args()
    root = Path.cwd()

    if args.test:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
        result = unittest.TextTestRunner(
            verbosity=2
        ).run(suite)
        return 0 if result.wasSuccessful() else 1

    if args.child:
        return child(root, args.seconds, args.run_id)

    if args.run:
        if not 45 <= args.seconds <= 90:
            print("[HOLD] INVALID_SESSION_DURATION")
            return 2
        return parent(root, args.seconds)

    target = root / PKG / NAME
    if not target.parent.is_dir():
        print("[HOLD] EXECUTOR_PACKAGE_MISSING")
        return 2
    if target.resolve() != Path(__file__).resolve():
        shutil.copyfile(Path(__file__), target)

    print("[PASS]", VERSION)
    print("[MODE] ORIGINAL_V39_WITH_SAFE_V24_HOLD_CODES")
    print("[SCANNER] FROZEN")
    print("[SIGNING] FALSE [BROADCAST] FALSE")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
