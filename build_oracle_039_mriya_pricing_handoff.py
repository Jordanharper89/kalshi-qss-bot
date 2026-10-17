
from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess
import sys
import unittest
import uuid

VERSION = "ORACLE_039_MRIYA_TO_LIVE_PRICING_HANDOFF"
PKG = Path("qseries_v2/oracle_execution/solana_atomic_executor")
NAME = "oracle_039_mriya_pricing_handoff.py"
REPORT = Path("runtime_state/oracle/oracle_live_execution/ORACLE_039_HANDOFF.json")
V24_REPORT = Path("runtime_state/oracle/oracle_live_execution/ORACLE_024_FRESH_CANDIDATES.json")
CAP = 120
CANARY = 10_000_000
SAFE = {
    "PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "SYSTEMDRIVE",
    "TEMP", "TMP", "COMSPEC", "SOLANA_RPC_URL",
    "QSB_SOLANA_RPC_URL", "SOLANA_WS_URL", "QSB_SOLANA_WALLET"
}

def clean_env(e):
    return {k:v for k,v in e.items() if k.upper() in SAFE}

class SharedGuard:
    def __init__(self, fn, limit=CAP):
        self.fn = fn
        self.limit = limit
        self.calls = 0
        self.methods = {}
        self.simulations = 0
        self.exhausted = False

    def __call__(self, method, params):
        if method in ("sendTransaction", "requestAirdrop"):
            raise RuntimeError("EXECUTION_RPC_FORBIDDEN")
        if method == "simulateTransaction" and self.simulations >= 1:
            raise RuntimeError("SHARED_SIMULATION_CAP")
        if self.calls >= self.limit:
            self.exhausted = True
            raise RuntimeError("SHARED_RPC_BUDGET_EXHAUSTED")
        self.calls += 1
        self.methods[method] = self.methods.get(method, 0) + 1
        if method == "simulateTransaction":
            self.simulations += 1
        return self.fn(method, params)

def write(root, row):
    p = root / REPORT
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(row, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8")
    tmp.replace(p)

def execute(root, seconds, rid):
    row = {
        "revision": VERSION,
        "run_id": rid,
        "status": "HOLD",
        "stage": "START",
        "worker_generation": 0,
        "worker_candidates": 0,
        "mriya_hot_count": 0,
        "selected_pairs": 0,
        "ready": 0,
        "priced_events": 0,
        "shared_rpc_requests": 0,
        "shared_simulations": 0,
        "scanner_modified": False,
        "signing": False,
        "broadcast": False,
        "canary_lamports": CANARY,
        "continuous_replenishment_certified": False
    }
    guard = None
    worker = None
    restore = []
    try:
        if any("PRIVATE_KEY" in k.upper() or "SECRET_KEY" in k.upper()
               for k in os.environ):
            raise RuntimeError("SECRET_ENVIRONMENT_REFUSED")

        sys.path.insert(0, str(root.resolve()))
        row["stage"] = "IMPORTS"
        from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
        from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import engine
        from qseries_v2.oracle_execution.solana_atomic_executor import mry_001_continuous_replenishment as mry
        from qseries_v2.oracle_execution.solana_atomic_executor import oracle_036_live_worker_handoff as v36
        from qseries_v2.oracle_execution.solana_atomic_executor import oracle_024_fresh_candidate_revalidation as v24
        from qseries_v2.oracle_execution.solana_atomic_executor import oracle_021_deterministic_pool_bootstrap as v21

        if (v24.CANARY, v24.PAIR_CAP, v24.SIM_CAP) != (CANARY, 8, 1):
            raise RuntimeError("V24_CONTRACT_CHANGED")

        original_rpc = core.rpc
        original_pool = engine.exact_pool_ok
        original_universe = engine.candidate_universe
        limits = (engine.MAX_TOKENS, engine.DISCOVERY_BUDGET,
                  engine.CROSSLIST_TTL)

        def restore_engine():
            core.rpc = original_rpc
            engine.exact_pool_ok = original_pool
            engine.candidate_universe = original_universe
            (engine.MAX_TOKENS, engine.DISCOVERY_BUDGET,
             engine.CROSSLIST_TTL) = limits

        restore.append(restore_engine)
        guard = SharedGuard(original_rpc)
        core.rpc = guard

        def exact_identity(token, pool):
            try:
                good = v21.derived_pool(token, core) == pool
            except (ValueError, TypeError, KeyError):
                good = False
            return good, "PDA_MATCH" if good else "PDA_MISMATCH"

        engine.exact_pool_ok = exact_identity

        row["stage"] = "MRIYA_WORKER_REFRESH"
        worker = mry.ReplenishmentWorker(root)
        worker.refresh()
        generation, candidates = v36.worker_snapshot(worker)

        row["worker_generation"] = generation
        row["worker_candidates"] = len(candidates)
        row["mriya_hot_count"] = sum(
            x.get("source") == "MRIYA_HOT" for x in candidates
        )

        row["stage"] = "EXACT_PAIR_ADMISSION"
        selected, rejects = v36.admission(
            candidates, v36.inventory_rows(root), 8
        )
        row["selected_pairs"] = len(selected)
        row["rejections"] = rejects
        row["selected_tokens"] = [x["token"] for x in selected]

        if not selected:
            row["status"] = "HOLD_NO_MATCHED_MRIYA_PAIRS"
            return 0

        # One process: reuse this already-discovered selection.
        # V24 performs fresh pool hydration and on-chain attestation.
        engine.candidate_universe = lambda path: list(selected)

        row["stage"] = "V24_LIVE_WEBSOCKET_PRICING"
        code = v24.child(root, seconds, rid)

        prior_path = root / V24_REPORT
        if not prior_path.is_file():
            raise RuntimeError("V24_REPORT_MISSING")
        prior = json.loads(prior_path.read_text(encoding="utf-8"))
        if prior.get("run_id") != rid:
            raise RuntimeError("STALE_V24_REPORT")

        for key in ("ready", "priced_events", "evaluations", "best_quotes",
                    "positive_candidates", "native_passes", "rechecks",
                    "attempts", "holds", "rejects", "simulations"):
            if key in prior:
                row[key] = prior[key]

        row["v24_status"] = prior.get("status")
        row["stage"] = "HANDOFF_EVALUATION"

        if code != 0:
            row["status"] = "HOLD_PRICING_RUNTIME"
        elif row.get("ready", 0) != len(selected):
            row["status"] = "HOLD_INCOMPLETE_WARM_ADMISSION"
        elif row.get("priced_events", 0) <= 0:
            row["status"] = "HOLD_NO_LIVE_PRICING_EVENTS"
        else:
            row["status"] = "MRIYA_TO_LIVE_WEBSOCKET_PRICING_VERIFIED"

        return code

    except Exception as exc:
        row["status"] = "HOLD_" + type(exc).__name__
        row["stage_error_class"] = type(exc).__name__
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
                row["status"] = "HOLD_RESTORE_FAILED"
        if guard is not None:
            row["shared_rpc_requests"] = guard.calls
            row["shared_rpc_methods"] = guard.methods
            row["shared_simulations"] = guard.simulations
            row["shared_rpc_exhausted"] = guard.exhausted
            if guard.exhausted:
                row["status"] = "HOLD_SHARED_RPC_CAP_EXHAUSTED"
        write(root, row)

def parent(root, seconds):
    rid = str(uuid.uuid4())
    cmd = [sys.executable, "-I", str(Path(__file__).resolve()),
           "--child", "--seconds", str(seconds), "--run-id", rid]
    try:
        proc = subprocess.run(
            cmd, cwd=root, env=clean_env(os.environ),
            capture_output=True, text=True, timeout=seconds + 180
        )
    except subprocess.TimeoutExpired:
        print("[HOLD] CHILD_TIMEOUT")
        return 2

    path = root / REPORT
    if not path.is_file():
        print("[HOLD] REPORT_MISSING [CHILD_EXIT]", proc.returncode)
        return 2

    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("run_id") != rid:
        print("[HOLD] STALE_REPORT")
        return 2

    for key in ("status", "stage", "stage_error_class",
                "worker_generation", "worker_candidates",
                "mriya_hot_count", "selected_pairs", "rejections",
                "ready", "priced_events", "evaluations", "best_quotes",
                "positive_candidates", "native_passes", "simulations",
                "shared_rpc_requests", "shared_rpc_methods",
                "shared_rpc_exhausted", "attempts", "holds"):
        if key in data:
            print("[" + key.upper() + "]",
                  json.dumps(data[key], sort_keys=True), flush=True)

    print("[SCANNER] FROZEN [SIGNING] FALSE [BROADCAST] FALSE")
    print("[CONTINUOUS_REPLENISHMENT] NOT_YET_CERTIFIED")
    print("[REPORT]", path)
    return proc.returncode

class Tests(unittest.TestCase):
    def test_secret_scrub(self):
        self.assertEqual(
            clean_env({"PATH":"x", "QSB_SOLANA_PRIVATE_KEY":"secret"}),
            {"PATH":"x"}
        )

    def test_shared_budget(self):
        calls = []
        g = SharedGuard(lambda m,p:calls.append(m), 2)
        g("getSlot", [])
        g("getAccountInfo", [])
        with self.assertRaises(RuntimeError):
            g("getSlot", [])
        self.assertEqual(len(calls), 2)
        self.assertTrue(g.exhausted)

    def test_no_broadcast(self):
        g = SharedGuard(lambda m,p:None)
        with self.assertRaises(RuntimeError):
            g("sendTransaction", [])
        self.assertEqual(g.calls, 0)

    def test_one_simulation(self):
        g = SharedGuard(lambda m,p:{"value":{}}, 10)
        g("simulateTransaction", [])
        with self.assertRaises(RuntimeError):
            g("simulateTransaction", [])
        self.assertEqual(g.simulations, 1)

    def test_canary(self):
        self.assertEqual(CANARY, 10_000_000)

    def test_worker_contract(self):
        from qseries_v2.oracle_execution.solana_atomic_executor import mry_001_continuous_replenishment as mry
        self.assertEqual(mry.ReplenishmentWorker(Path.cwd()).latest(), (0, []))

    def test_v24_contract(self):
        from qseries_v2.oracle_execution.solana_atomic_executor import oracle_024_fresh_candidate_revalidation as v24
        self.assertEqual((v24.CANARY, v24.PAIR_CAP, v24.SIM_CAP),
                         (10_000_000, 8, 1))

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--test", action="store_true")
    p.add_argument("--run", action="store_true")
    p.add_argument("--child", action="store_true")
    p.add_argument("--seconds", type=int, default=60)
    p.add_argument("--run-id", default="")
    args = p.parse_args()
    root = Path.cwd()

    if args.test:
        result = unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
        )
        return 0 if result.wasSuccessful() else 1

    if args.child:
        return execute(root, args.seconds, args.run_id)

    if args.run:
        if not 45 <= args.seconds <= 90:
            print("[HOLD] DURATION_45_TO_90_SECONDS")
            return 2
        return parent(root, args.seconds)

    target = root / PKG / NAME
    if not target.parent.is_dir():
        print("[HOLD] EXECUTOR_PACKAGE_MISSING")
        return 2
    if target.resolve() != Path(__file__).resolve():
        shutil.copyfile(Path(__file__), target)
    print("[PASS]", VERSION)
    print("[MODE] MRIYA_REFRESH_TO_EXISTING_V24_WEBSOCKET_PRICING")
    print("[SHARED_RPC_CAP]", CAP)
    print("[SIGNING] FALSE [BROADCAST] FALSE")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
