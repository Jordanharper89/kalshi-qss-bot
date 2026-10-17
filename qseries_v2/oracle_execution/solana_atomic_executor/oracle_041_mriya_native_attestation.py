
from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess
import sys
import unittest
import uuid

VERSION = "ORACLE_041_MRIYA_NATIVE_ATTESTATION"
BASE = Path("qseries_v2/oracle_execution/solana_atomic_executor")
NAME = "oracle_041_mriya_native_attestation.py"
REPORT = Path(
    "runtime_state/oracle/oracle_live_execution/"
    "ORACLE_041_ATTESTATION.json"
)
V24_REPORT = Path(
    "runtime_state/oracle/oracle_live_execution/"
    "ORACLE_024_FRESH_CANDIDATES.json"
)

RPC_CAP = 120
PAIR_CAP = 8
CANARY = 10_000_000

SAFE = {
    "PATH", "PATHEXT", "SYSTEMROOT", "WINDIR",
    "SYSTEMDRIVE", "TEMP", "TMP", "COMSPEC",
    "SOLANA_RPC_URL", "QSB_SOLANA_RPC_URL",
    "SOLANA_WS_URL", "QSB_SOLANA_WALLET",
}

KNOWN_HOLDS = {
    "NO_EXACT_PUMPSWAP_DLMM_PAIRS",
    "NO_VERIFIED_PAIR",
    "POOL_OWNER_ATTESTATION_INCOMPLETE",
    "NO_READY_EXECUTION_PAIRS",
    "PAIR_ACCOUNT_COVERAGE_MISSING",
    "PAIR_REGISTRY_WRONG_INDEX",
    "RPC_REQUEST_BUDGET_EXHAUSTED",
    "ATOMIC_COMPILE_REJECTED",
    "UNSIGNED_ATOMIC_V0_INVALID",
    "STALE_BEFORE_SIMULATION",
}

def scrub(env):
    return {k: v for k, v in env.items()
            if k.upper() in SAFE}

def save(root, result):
    path = root / REPORT
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    tmp.replace(path)

def verified_intake(engine, candidates, telemetry):
    """
    The original V24 identity function remains authoritative.
    This wrapper invokes it before V24 hydrates each pool.
    """
    def producer(root):
        admitted = []
        rejected = 0
        for row in candidates:
            token = row["token"]
            pool = row["pump_pool"]
            try:
                valid, reason = engine.exact_pool_ok(token, pool)
            except (ValueError, TypeError, KeyError):
                valid = False
            if valid:
                admitted.append(dict(row))
            else:
                rejected += 1
        telemetry["pda_registered"] = len(admitted)
        telemetry["pda_rejected"] = rejected
        return admitted
    return producer

def child(root, seconds, run_id):
    result = {
        "revision": VERSION,
        "run_id": run_id,
        "status": "HOLD",
        "stage": "BOOTSTRAP",
        "worker_generation": 0,
        "worker_candidates": 0,
        "selected_pairs": 0,
        "pda_registered": 0,
        "pda_rejected": 0,
        "ready": 0,
        "priced_events": 0,
        "shared_rpc_requests": 0,
        "shared_simulations": 0,
        "rpc_cap": RPC_CAP,
        "scanner_modified": False,
        "continuous_replenishment": False,
        "signing": False,
        "broadcast": False,
        "canary_lamports": CANARY,
    }

    restore = []
    guard = None
    worker = None

    try:
        if any(
            "PRIVATE_KEY" in key.upper()
            or "SECRET_KEY" in key.upper()
            for key in os.environ
        ):
            result["status"] = "HOLD_SECRET_ENVIRONMENT"
            return 2

        sys.path.insert(0, str(root.resolve()))

        result["stage"] = "IMPORTS"

        from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
        from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import engine
        from qseries_v2.oracle_execution.solana_atomic_executor import mry_001_continuous_replenishment as mry
        from qseries_v2.oracle_execution.solana_atomic_executor import oracle_036_live_worker_handoff as v36
        from qseries_v2.oracle_execution.solana_atomic_executor import oracle_039_mriya_pricing_handoff as v39
        from qseries_v2.oracle_execution.solana_atomic_executor import oracle_024_fresh_candidate_revalidation as v24
        from qseries_v2.oracle_execution.solana_atomic_executor import oracle_021_deterministic_pool_bootstrap as v21

        if (v24.CANARY, v24.PAIR_CAP, v24.SIM_CAP) != (
            CANARY, PAIR_CAP, 1
        ):
            raise RuntimeError("V24_CONTRACT_DRIFT")

        original_rpc = core.rpc
        original_pool = engine.exact_pool_ok
        original_universe = engine.candidate_universe
        original_reason = v24.hold_reason
        old_limits = (
            engine.MAX_TOKENS,
            engine.DISCOVERY_BUDGET,
            engine.CROSSLIST_TTL,
        )

        def restore_all():
            core.rpc = original_rpc
            engine.exact_pool_ok = original_pool
            engine.candidate_universe = original_universe
            v24.hold_reason = original_reason
            (
                engine.MAX_TOKENS,
                engine.DISCOVERY_BUDGET,
                engine.CROSSLIST_TTL,
            ) = old_limits

        restore.append(restore_all)

        guard = v39.SharedGuard(original_rpc, RPC_CAP)
        core.rpc = guard

        # During discovery, keep deterministic identity checks.
        # V24 will later install its own identity function.
        def discovery_identity(token, pool):
            try:
                good = v21.derived_pool(token, core) == pool
            except (ValueError, TypeError, KeyError):
                good = False
            return good, (
                "PDA_MATCH" if good else "PDA_MISMATCH"
            )

        engine.exact_pool_ok = discovery_identity

        result["stage"] = "MRIYA_REFRESH"
        worker = mry.ReplenishmentWorker(root)
        worker.refresh()

        generation, candidates = v36.worker_snapshot(worker)
        result["worker_generation"] = generation
        result["worker_candidates"] = len(candidates)
        result["mriya_hot_count"] = sum(
            x.get("source") == "MRIYA_HOT"
            for x in candidates
        )

        result["stage"] = "EXACT_INVENTORY_ADMISSION"
        selected, rejected = v36.admission(
            candidates, v36.inventory_rows(root), PAIR_CAP
        )
        result["selected_pairs"] = len(selected)
        result["rejections"] = rejected

        if not selected:
            result["status"] = "HOLD_NO_EXACT_PAIRS"
            return 0

        # Critical fix: V24's own engine.exact_pool_ok
        # is called when it requests its candidate universe.
        engine.candidate_universe = verified_intake(
            engine, selected, result
        )

        def safe_hold(error):
            if (
                type(error) is RuntimeError
                and str(error) in KNOWN_HOLDS
            ):
                return str(error)
            return "REDACTED_" + type(error).__name__

        v24.hold_reason = safe_hold

        result["stage"] = "V24_NATIVE_ATTESTATION_AND_PRICING"

        code = v24.child(root, seconds, run_id)

        path = root / V24_REPORT
        if not path.is_file():
            result["status"] = "HOLD_V24_REPORT_MISSING"
            return 2

        prior = json.loads(
            path.read_text(encoding="utf-8")
        )
        if prior.get("run_id") != run_id:
            result["status"] = "HOLD_STALE_V24_REPORT"
            return 2

        for field in (
            "ready", "priced_events", "evaluations",
            "positive_candidates", "native_passes",
            "simulations", "attempts", "holds",
            "rejects", "best_quotes",
        ):
            if field in prior:
                result[field] = prior[field]

        result["v24_status"] = prior.get("status")
        result["stage"] = "RESULT_VERIFICATION"

        if result["pda_registered"] == 0:
            result["status"] = "HOLD_NO_PDA_REGISTERED_PAIRS"
        elif result["ready"] == 0:
            result["status"] = "HOLD_NO_READY_PAIRS"
        elif result["priced_events"] == 0:
            result["status"] = "HOLD_NO_LIVE_PRICING"
        elif code != 0:
            result["status"] = "HOLD_V24_ENGINE"
        else:
            result["status"] = (
                "MRIYA_NATIVE_ATTESTATION_TO_PRICING_VERIFIED"
            )

        return code

    except Exception as error:
        result["status"] = "HOLD_" + type(error).__name__
        result["error_class"] = type(error).__name__
        return 2

    finally:
        if worker is not None:
            try:
                worker.close()
            except Exception:
                pass

        for action in reversed(restore):
            try:
                action()
            except Exception:
                result["status"] = "HOLD_RESTORE_FAILED"

        if guard is not None:
            result["shared_rpc_requests"] = guard.calls
            result["shared_rpc_methods"] = guard.methods
            result["shared_simulations"] = guard.simulations
            result["rpc_exhausted"] = guard.exhausted

            if guard.exhausted:
                result["status"] = "HOLD_RPC_CAP_EXHAUSTED"

        save(root, result)

def parent(root, seconds):
    run_id = str(uuid.uuid4())
    command = [
        sys.executable, "-I",
        str(Path(__file__).resolve()),
        "--child", "--seconds", str(seconds),
        "--run-id", run_id,
    ]

    try:
        process = subprocess.run(
            command,
            cwd=root,
            env=scrub(os.environ),
            capture_output=True,
            text=True,
            timeout=seconds + 180,
        )
    except subprocess.TimeoutExpired:
        print("[HOLD] CHILD_TIMEOUT")
        return 2

    path = root / REPORT
    if not path.is_file():
        print("[HOLD] CHILD_REPORT_MISSING")
        print("[CHILD_EXIT]", process.returncode)
        return 2

    result = json.loads(
        path.read_text(encoding="utf-8")
    )
    if result.get("run_id") != run_id:
        print("[HOLD] STALE_REPORT")
        return 2

    for field in (
        "status", "stage", "error_class",
        "worker_generation", "worker_candidates",
        "mriya_hot_count", "selected_pairs",
        "pda_registered", "pda_rejected",
        "ready", "priced_events", "evaluations",
        "positive_candidates", "native_passes",
        "simulations", "holds", "rejects",
        "shared_rpc_requests", "shared_rpc_methods",
        "shared_simulations", "rpc_exhausted",
    ):
        if field in result:
            print(
                "[" + field.upper() + "]",
                json.dumps(result[field], sort_keys=True),
                flush=True,
            )

    print("[SCANNER] FROZEN")
    print("[SIGNING] FALSE [BROADCAST] FALSE")
    print("[REPORT]", path)
    return process.returncode

class Tests(unittest.TestCase):

    def test_native_registration(self):
        class Engine:
            @staticmethod
            def exact_pool_ok(token, pool):
                return (token == "A" and pool == "P", "CHECK")
        state = {}
        producer = verified_intake(
            Engine,
            [
                {"token": "A", "pump_pool": "P"},
                {"token": "B", "pump_pool": "Q"},
            ],
            state,
        )
        selected = producer(Path("."))
        self.assertEqual(len(selected), 1)
        self.assertEqual(state["pda_registered"], 1)
        self.assertEqual(state["pda_rejected"], 1)

    def test_no_bypass(self):
        class Engine:
            @staticmethod
            def exact_pool_ok(token, pool):
                return (False, "MISMATCH")
        rows = verified_intake(
            Engine,
            [{"token": "A", "pump_pool": "P"}],
            {},
        )(Path("."))
        self.assertEqual(rows, [])

    def test_scrub(self):
        result = scrub({
            "PATH": "ok",
            "QSB_SOLANA_PRIVATE_KEY": "secret",
        })
        self.assertEqual(result, {"PATH": "ok"})

    def test_rpc_budget(self):
        from qseries_v2.oracle_execution.solana_atomic_executor import oracle_039_mriya_pricing_handoff as v39
        calls = []
        guard = v39.SharedGuard(
            lambda method, params: calls.append(method),
            2,
        )
        guard("getSlot", [])
        guard("getSlot", [])
        with self.assertRaises(RuntimeError):
            guard("getSlot", [])
        self.assertEqual(len(calls), 2)

    def test_no_broadcast(self):
        from qseries_v2.oracle_execution.solana_atomic_executor import oracle_039_mriya_pricing_handoff as v39
        guard = v39.SharedGuard(
            lambda method, params: None
        )
        with self.assertRaises(RuntimeError):
            guard("sendTransaction", [])
        self.assertEqual(guard.calls, 0)

    def test_canary(self):
        self.assertEqual(CANARY, 10_000_000)

    def test_pair_cap(self):
        self.assertEqual(PAIR_CAP, 8)

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
        result = unittest.TextTestRunner(
            verbosity=2
        ).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(
                Tests
            )
        )
        return 0 if result.wasSuccessful() else 1

    if args.child:
        return child(root, args.seconds, args.run_id)

    if args.run:
        if not 45 <= args.seconds <= 90:
            print("[HOLD] INVALID_SESSION_DURATION")
            return 2
        return parent(root, args.seconds)

    target = root / BASE / NAME
    if not target.parent.is_dir():
        print("[HOLD] EXECUTOR_PACKAGE_MISSING")
        return 2

    if target.resolve() != Path(__file__).resolve():
        shutil.copyfile(Path(__file__), target)

    print("[PASS]", VERSION)
    print("[FIX] V24_NATIVE_POOL_REGISTRATION_RESTORED")
    print("[SCANNER] FROZEN")
    print("[SIGNING] FALSE [BROADCAST] FALSE")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
