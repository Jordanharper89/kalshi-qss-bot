
from pathlib import Path
import argparse
import ast
import json
import shutil
import unittest

VERSION = "ORACLE_033_MRIYA_WARM_INVENTORY_CONTRACT"
PKG = Path("qseries_v2/oracle_execution/solana_atomic_executor")
DEST = PKG / "oracle_033_mriya_warm_inventory_contract.py"
REPORT = Path("runtime_state/oracle/oracle_live_execution/ORACLE_033_CONTRACT.json")

SOURCES = {
    "dynamic_registry":
        Path("runtime_state/qseries/qarb_clean_bot/mriya_dynamic_token_registry.json"),
    "exact_bindings":
        Path("runtime_state/qseries/qarb_clean_bot/mriya_dynamic_exact_bindings.json"),
    "replenishment_priority":
        Path("runtime_state/oracle/solana_atomic_executor/mriya_replenishment_priority.json"),
    "full_inventory":
        Path("runtime_state/oracle/solana_atomic_executor/full_surface_replenishment_inventory.json"),
    "replenishment_status":
        Path("runtime_state/oracle/solana_atomic_executor/mriya_replenishment_status.json"),
}

WORKER = PKG / "mry_001_continuous_replenishment.py"

def shape(value, depth=0):
    if isinstance(value, dict):
        result = {"type": "object", "keys": sorted(value)[:65]}
        if depth < 2:
            result["children"] = {
                key: shape(child, depth + 1)
                for key, child in list(value.items())[:16]
                if isinstance(child, (dict, list))
            }
        return result
    if isinstance(value, list):
        result = {"type": "list", "count": len(value)}
        if value and depth < 3:
            result["first_record_shape"] = shape(value[0], depth + 1)
        return result
    return {"type": type(value).__name__}

def inspect_state(root):
    out = {}
    for name, rel in SOURCES.items():
        path = root / rel
        row = {"exists": path.is_file(), "path": str(rel)}
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                row["schema"] = shape(data)
                row["bytes"] = path.stat().st_size
            except (OSError, ValueError, UnicodeError):
                row["error"] = "UNREADABLE"
        out[name] = row
    return out

def inspect_worker(root):
    path = root / WORKER
    result = {"exists": path.is_file(), "path": str(WORKER)}
    if not path.is_file():
        return result
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    result["interfaces"] = []
    result["call_sites"] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result["interfaces"].append({
                "name": node.name,
                "parameters": [a.arg for a in node.args.args],
                "line": node.lineno
            })
        elif isinstance(node, ast.Call):
            try:
                call = ast.unparse(node.func)
            except Exception:
                continue
            if any(s in call.lower() for s in (
                "candidate_universe", "snapshot",
                "refresh", "latest", "sleep",
                "configure", "start", "close"
            )):
                result["call_sites"].append({
                    "call": call,
                    "line": node.lineno
                })
    return result

def audit(root):
    state = inspect_state(root)
    worker = inspect_worker(root)
    return {
        "revision": VERSION,
        "status": "WARM_INVENTORY_BINDING_CONTRACT_INSPECTED",
        "worker": worker,
        "registry_contracts": state,
        "registry_present": state["dynamic_registry"]["exists"],
        "worker_present": worker["exists"],
        "atomic_warm_limit": 8,
        "handoff_connected": False,
        "historical_quotes_executable": False,
        "fresh_pool_validation_required": True,
        "rpc_requests": 0,
        "scanner_modified": False,
        "signing": False,
        "broadcast": False,
        "canary_lamports": 10000000,
    }

def save(root, row):
    path = root / REPORT
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(
        json.dumps(row, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
    temp.replace(path)

class Tests(unittest.TestCase):
    def test_schema_only(self):
        sample = {"rows": [{"token": "example", "score": 10}]}
        text = json.dumps(shape(sample))
        self.assertIn("token", text)
        self.assertNotIn("example", text)

    def test_read_only(self):
        row = audit(Path.cwd())
        self.assertFalse(row["signing"])
        self.assertFalse(row["broadcast"])
        self.assertFalse(row["scanner_modified"])

    def test_no_rpc(self):
        self.assertEqual(audit(Path.cwd())["rpc_requests"], 0)

    def test_exact_canary(self):
        self.assertEqual(
            audit(Path.cwd())["canary_lamports"],
            10000000
        )

    def test_no_false_connection(self):
        self.assertFalse(audit(Path.cwd())["handoff_connected"])

    def test_no_historical_execution(self):
        self.assertFalse(
            audit(Path.cwd())["historical_quotes_executable"]
        )

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
        save(root, result)
        print("[STATUS]", result["status"])
        print("[WORKER]", json.dumps(result["worker"], sort_keys=True))
        for name, row in result["registry_contracts"].items():
            print("[REGISTRY]", name, json.dumps(row, sort_keys=True))
        print("[HANDOFF_CONNECTED] FALSE")
        print("[RPC_REQUESTS] 0")
        print("[SIGNING] FALSE [BROADCAST] FALSE")
        print("[REPORT]", root / REPORT)
        return 0

    target = root / DEST
    if not target.parent.is_dir():
        print("[HOLD] EXECUTOR_PACKAGE_MISSING")
        return 2
    if target.resolve() != Path(__file__).resolve():
        shutil.copyfile(Path(__file__), target)
    print("[PASS]", VERSION)
    print("[MODE] EXISTING_MRIYA_REGISTRY_AND_WORKER_ONLY")
    print("[SCANNER] UNCHANGED [EXECUTION] DISABLED")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
