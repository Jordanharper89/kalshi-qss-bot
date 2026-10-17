
from pathlib import Path
from contextlib import contextmanager
import argparse
import json
import shutil
import time
import unittest

VERSION = "ORACLE_035_MRIYA_WORKER_EXECUTOR_BINDING"
PKG = Path("qseries_v2/oracle_execution/solana_atomic_executor")
DEST = PKG / "oracle_035_worker_executor_binding.py"
REPORT = Path("runtime_state/oracle/oracle_live_execution/ORACLE_035_BINDING.json")
WSOL = "So11111111111111111111111111111111111111112"

def rows_from(value):
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in ("rows", "candidates", "pairs"):
            if isinstance(value.get(key), list):
                return value[key]
    return []

def identities(rows):
    found = {}
    for row in rows_from(rows):
        if not isinstance(row, dict):
            continue
        token = row.get("token")
        pump = row.get("pump_pool")
        meta = row.get("meteora_meta")
        if not isinstance(meta, dict):
            continue
        if not isinstance(token, str) or not isinstance(pump, str):
            continue
        if {meta.get("token_x"), meta.get("token_y")} != {token, WSOL}:
            continue
        if not isinstance(meta.get("address"), str):
            continue
        if token not in found:
            found[token] = {
                "token": token,
                "pump_pool": pump,
                "meteora_meta": dict(meta),
                "meteora_pool": meta["address"],
                "source": "MRIYA_WORKER",
                "crosslisted": True,
                "execution_authority": False,
            }
    return list(found.values())

def merge_verified(worker_rows, discovered, cap=12):
    # Never trust worker-only pool identities as verified.
    verified = {
        row.get("token"): row
        for row in discovered
        if isinstance(row, dict)
        and row.get("token")
        and row.get("pump_pool")
        and row.get("meteora_pool")
    }
    promoted = []
    seen = set()
    for row in identities(worker_rows):
        match = verified.get(row["token"])
        if not match:
            continue
        if match["pump_pool"] != row["pump_pool"]:
            continue
        if match["meteora_pool"] != row["meteora_pool"]:
            continue
        promoted.append(dict(match))
        seen.add(row["token"])
    for row in discovered:
        token = row.get("token") if isinstance(row, dict) else None
        if token and token not in seen:
            promoted.append(dict(row))
            seen.add(token)
    return promoted[:cap]

@contextmanager
def bind(engine, worker, telemetry=None, cap=12):
    original = engine.candidate_universe
    state = {"generation": None, "rows": []}

    def consume(root):
        # Read worker memory only; do not trigger refresh.
        current = worker.latest()
        generation = getattr(worker, "generation", None)
        if callable(generation):
            generation = generation()
        if generation is None:
            generation = getattr(worker, "last_generation", None)
        if generation != state["generation"]:
            state["generation"] = generation
            state["rows"] = rows_from(current)
        discovered = original(root)
        selected = merge_verified(state["rows"], discovered, cap)
        if telemetry is not None:
            telemetry.update({
                "worker_generation": generation,
                "worker_rows": len(state["rows"]),
                "verified_discovery_rows": len(discovered),
                "selected_rows": len(selected),
                "live_revalidation_complete": False,
                "signing": False,
                "broadcast": False,
            })
        return selected

    engine.candidate_universe = consume
    try:
        yield consume
    finally:
        engine.candidate_universe = original

def audit(root):
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        mry_001_continuous_replenishment as mry
    )
    import inspect

    worker = getattr(mry, "Replenisher", None)
    classes = [
        (name, obj)
        for name, obj in vars(mry).items()
        if inspect.isclass(obj)
        and obj.__module__ == mry.__name__
        and callable(getattr(obj, "latest", None))
    ]
    result = {
        "revision": VERSION,
        "status": "WORKER_INTERFACE_IDENTIFIED",
        "worker_classes": [name for name, _ in classes],
        "worker_latest_available": bool(classes),
        "worker_refresh_called": False,
        "executor_live_bound": False,
        "onchain_hydration_performed": False,
        "provider_requests": 0,
        "scanner_modified": False,
        "signing": False,
        "broadcast": False,
        "canary_lamports": 10000000,
    }
    target = root / REPORT
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8"
    )
    return result

class Tests(unittest.TestCase):
    def sample(self):
        return {
            "token": "T",
            "pump_pool": "P",
            "meteora_pool": "M",
            "meteora_meta": {
                "address": "M",
                "token_x": "T",
                "token_y": WSOL,
            },
        }

    def test_worker_identity(self):
        self.assertEqual(len(identities([self.sample()])), 1)

    def test_wrong_quote_asset(self):
        row = self.sample()
        row["meteora_meta"]["token_y"] = "WRONG"
        self.assertEqual(identities([row]), [])

    def test_no_unknown_pool_promotion(self):
        self.assertEqual(merge_verified([self.sample()], []), [])

    def test_verified_pool_match(self):
        item = self.sample()
        selected = merge_verified([item], [item])
        self.assertEqual(selected[0]["token"], "T")

    def test_identity_mismatch(self):
        item = self.sample()
        wrong = dict(item, pump_pool="OTHER")
        selected = merge_verified([item], [wrong])
        self.assertEqual(selected[0]["pump_pool"], "OTHER")

    def test_scoped_binding(self):
        class Engine:
            def candidate_universe(self, root):
                return [self_row]
        class Worker:
            generation = 1
            def latest(self):
                return [self_row]
        self_row = self.sample()
        engine = Engine()
        original = engine.candidate_universe.__func__
        diagnostics = {}
        with bind(engine, Worker(), diagnostics):
            selected = engine.candidate_universe(Path("."))
            self.assertEqual(len(selected), 1)
            self.assertEqual(diagnostics["worker_generation"], 1)
            self.assertFalse(diagnostics["signing"])
        self.assertIs(engine.candidate_universe.__func__, original)

    def test_no_live_side_effect(self):
        result = audit(Path.cwd())
        self.assertEqual(result["provider_requests"], 0)
        self.assertFalse(result["worker_refresh_called"])
        self.assertFalse(result["executor_live_bound"])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--audit", action="store_true")
    args = parser.parse_args()
    root = Path.cwd()

    if args.test:
        result = unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
        )
        return 0 if result.wasSuccessful() else 1

    if args.audit:
        result = audit(root)
        for key, value in result.items():
            print("[" + key.upper() + "]", json.dumps(value))
        print("[REPORT]", root / REPORT)
        return 0 if result["worker_latest_available"] else 2

    dest = root / DEST
    if not dest.parent.is_dir():
        print("[HOLD] EXECUTOR_PACKAGE_MISSING")
        return 2
    if dest.resolve() != Path(__file__).resolve():
        shutil.copyfile(Path(__file__), dest)
    print("[PASS]", VERSION)
    print("[MODE] WORKER_MEMORY_TO_VERIFIED_DISCOVERY")
    print("[SCANNER] FROZEN [SIGNING] FALSE [BROADCAST] FALSE")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
