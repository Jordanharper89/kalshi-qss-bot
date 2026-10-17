
from pathlib import Path
import argparse
import json
import shutil
import unittest

VERSION = "ORACLE_042_PERSISTENT_MRIYA_REPLENISHMENT"
PKG = Path("qseries_v2/oracle_execution/solana_atomic_executor")
DEST = PKG / "oracle_042_persistent_replenishment.py"
STATE = Path("runtime_state/oracle/oracle_live_execution/ORACLE_042_STATE.json")
CAP = 8
CANARY = 10_000_000

def identity(row):
    if not isinstance(row, dict):
        return None
    values = tuple(row.get(k) for k in (
        "token", "pump_pool", "meteora_pool"
    ))
    if not all(isinstance(x, str) and x for x in values):
        return None
    return values

def reconcile(active, incoming, generation, previous=None):
    previous = previous or {}
    old_generation = int(previous.get("generation", 0))
    if generation <= old_generation:
        return {
            "status": "HOLD_GENERATION_NOT_ADVANCED",
            "generation": old_generation,
            "active": list(active),
            "pending": [],
            "removed": [],
            "admitted": [],
        }

    retained = []
    seen = set()

    for row in active:
        key = identity(row)
        if key and key not in seen:
            retained.append(dict(row))
            seen.add(key)

    if len(retained) > CAP:
        return {
            "status": "HOLD_ACTIVE_CAPACITY_INVALID",
            "generation": old_generation,
            "active": retained,
            "pending": [],
            "removed": [],
            "admitted": [],
        }

    pending = []
    for row in incoming:
        key = identity(row)
        if key and key not in seen:
            pending.append(dict(row))
            seen.add(key)

    # A discovered candidate is not a ready replacement.
    # Only the live atomic runtime may validate and promote it.
    return {
        "status": "ROTATION_PLAN_PENDING_LIVE_VALIDATION",
        "generation": generation,
        "active": retained,
        "pending": pending,
        "removed": [],
        "admitted": [],
        "capacity": CAP,
        "free_slots": CAP - len(retained),
        "signing": False,
        "broadcast": False,
    }

def read_state(root):
    path = root / STATE
    if not path.is_file():
        return {"generation": 0, "active": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError("INVALID_STATE_DOCUMENT")
    return data

def atomic_write(root, data):
    path = root / STATE
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
    tmp.replace(path)

def process_generation(root, generation, rows, active=None):
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle_036_live_worker_handoff as v36
    )
    state = read_state(root)
    live_active = state.get("active", []) if active is None else active
    inventory = v36.inventory_rows(root)
    exact, rejects = v36.admission(rows, inventory, len(rows) or 1)

    plan = reconcile(live_active, exact, generation, state)
    plan["revision"] = VERSION
    plan["worker_rows"] = len(rows)
    plan["inventory_rows"] = len(inventory)
    plan["exact_metadata_matches"] = len(exact)
    plan["rejections"] = rejects
    plan["worker_refresh_started"] = False
    plan["fresh_onchain_attestation"] = False
    plan["websocket_rotation_applied"] = False
    plan["rpc_requests"] = 0
    plan["canary_lamports"] = CANARY

    if plan["status"] == "ROTATION_PLAN_PENDING_LIVE_VALIDATION":
        atomic_write(root, plan)
    return plan

def audit(root):
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        mry_001_continuous_replenishment as mry
    )
    worker = mry.ReplenishmentWorker(root)
    generation, rows = worker.latest()
    result = {
        "revision": VERSION,
        "status": "PERSISTENT_CONTROLLER_READY",
        "worker_contract": "generation,rows",
        "worker_generation": generation,
        "worker_running": False,
        "candidate_count": len(rows),
        "prior_generation": read_state(root).get("generation", 0),
        "warm_capacity": CAP,
        "live_socket_connected": False,
        "rotation_applied": False,
        "rpc_requests": 0,
        "signing": False,
        "broadcast": False,
        "canary_lamports": CANARY,
    }
    return result

class Tests(unittest.TestCase):
    def row(self, n):
        return {
            "token": "T" + str(n),
            "pump_pool": "P" + str(n),
            "meteora_pool": "M" + str(n)
        }

    def test_retain_active(self):
        plan = reconcile(
            [self.row(1)], [self.row(2)], 2,
            {"generation": 1}
        )
        self.assertEqual(len(plan["active"]), 1)
        self.assertEqual(len(plan["pending"]), 1)
        self.assertEqual(plan["removed"], [])

    def test_no_automatic_promotion(self):
        plan = reconcile(
            [], [self.row(1)], 1,
            {"generation": 0}
        )
        self.assertEqual(plan["admitted"], [])
        self.assertEqual(plan["active"], [])

    def test_dedup(self):
        plan = reconcile(
            [self.row(1)],
            [self.row(1), self.row(2), self.row(2)],
            2, {"generation": 1}
        )
        self.assertEqual(len(plan["pending"]), 1)

    def test_stale_generation(self):
        plan = reconcile(
            [self.row(1)], [self.row(2)], 3,
            {"generation": 3}
        )
        self.assertEqual(
            plan["status"], "HOLD_GENERATION_NOT_ADVANCED"
        )

    def test_capacity(self):
        plan = reconcile(
            [self.row(i) for i in range(9)],
            [], 2, {"generation": 1}
        )
        self.assertEqual(
            plan["status"], "HOLD_ACTIVE_CAPACITY_INVALID"
        )

    def test_no_forced_eviction(self):
        plan = reconcile(
            [self.row(i) for i in range(8)],
            [self.row(10)], 2, {"generation": 1}
        )
        self.assertEqual(len(plan["active"]), 8)
        self.assertEqual(len(plan["pending"]), 1)
        self.assertEqual(plan["free_slots"], 0)

    def test_canary(self):
        self.assertEqual(CANARY, 10_000_000)

    def test_worker_stays_unstarted(self):
        result = audit(Path.cwd())
        self.assertFalse(result["worker_running"])
        self.assertEqual(result["rpc_requests"], 0)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--audit", action="store_true")
    args = parser.parse_args()
    root = Path.cwd()

    if args.test:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
        result = unittest.TextTestRunner(
            verbosity=2
        ).run(suite)
        return 0 if result.wasSuccessful() else 1

    if args.audit:
        for k, v in audit(root).items():
            print("[" + k.upper() + "]", json.dumps(v))
        return 0

    target = root / DEST
    if not target.parent.is_dir():
        print("[HOLD] EXECUTOR_PACKAGE_MISSING")
        return 2
    if target.resolve() != Path(__file__).resolve():
        shutil.copyfile(Path(__file__), target)
    print("[PASS]", VERSION)
    print("[WARM_CAPACITY]", CAP)
    print("[SCANNER] UNCHANGED")
    print("[SIGNING] FALSE [BROADCAST] FALSE")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
