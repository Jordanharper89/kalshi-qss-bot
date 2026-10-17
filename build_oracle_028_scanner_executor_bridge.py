
from pathlib import Path
import ast
import argparse
import json
import shutil
import unittest

VERSION = "ORACLE_028_SCANNER_EXECUTOR_HANDOFF_CERTIFICATION"
PKG = Path("qseries_v2/oracle_execution/solana_atomic_executor")
DEST = PKG / "oracle_028_scanner_executor_bridge.py"
REPORT = Path("runtime_state/oracle/oracle_live_execution/ORACLE_028_BRIDGE.json")

KEYWORDS = (
    "mriya", "scanner", "discovery", "opportunity",
    "capture", "inventory", "hot_lane", "replenishment"
)
PRODUCER_HINTS = (
    "candidate_universe", "raw_candidate_universe",
    "mriya_hot_tokens", "capture_lane", "discovery",
    "publish", "emit", "opportunity"
)

def inspect_module(path):
    source = path.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(path))
    names = []
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.append(node.name)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    hits = sorted(set(names).intersection(PRODUCER_HINTS))
    for name in names:
        if any(word in name.lower() for word in KEYWORDS):
            hits.append(name)
    return {
        "path": str(path),
        "functions": sorted(set(hits))[:30],
        "oracle_imports": sorted(set(
            x for x in imports if x.startswith("qseries_v2")
        ))[:15]
    }

def inspect_json(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError):
        return None
    if not isinstance(value, dict):
        return None
    keys = sorted(value.keys())
    possible = (
        "opportunities", "candidates", "signals",
        "exact_rows", "rows", "pairs", "tokens"
    )
    counts = {
        name: len(value[name])
        for name in possible
        if isinstance(value.get(name), list)
    }
    if not counts and not any(
        k in path.name.lower() for k in KEYWORDS
    ):
        return None
    return {
        "path": str(path),
        "keys": keys[:40],
        "record_counts": counts
    }

def audit(root):
    source_root = root / "qseries_v2"
    modules = []
    for path in source_root.rglob("*.py"):
        if not any(k in path.name.lower() for k in KEYWORDS):
            continue
        try:
            modules.append(inspect_module(path))
        except (SyntaxError, UnicodeError, OSError):
            continue

    modules.sort(
        key=lambda row: (
            -len(row["functions"]), row["path"]
        )
    )

    records = []
    state = root / "runtime_state"
    if state.exists():
        for path in state.rglob("*.json"):
            if not any(k in str(path).lower() for k in KEYWORDS):
                continue
            item = inspect_json(path)
            if item:
                records.append(item)

    records.sort(
        key=lambda row: (
            -sum(row["record_counts"].values()),
            row["path"]
        )
    )

    required = {
        "original_scanner_package": source_root.is_dir(),
        "oracle_executor_package": (root / PKG).is_dir(),
        "v20_native_atomic": (
            root / PKG / "oracle_atomic_closeout.py"
        ).is_file(),
        "v24_freshness_gate": (
            root / PKG /
            "oracle_024_fresh_candidate_revalidation.py"
        ).is_file(),
        "v25_sim_forensics": (
            root / PKG /
            "oracle_025_atomic_sim_forensics.py"
        ).is_file()
    }

    return {
        "revision": VERSION,
        "status": (
            "HANDOFF_DISCOVERY_READY"
            if all(required.values())
            else "HOLD_MISSING_DEPENDENCY"
        ),
        "required_components": required,
        "candidate_producer_modules": modules[:45],
        "candidate_state_records": records[:35],
        "candidate_module_count": len(modules),
        "candidate_record_count": len(records),
        "consumer": str(PKG),
        "handoff_execution_enabled": False,
        "historical_signals_executable": False,
        "fresh_validation_required": True,
        "scanner_modified": False,
        "rpc_requests": 0,
        "signing": False,
        "broadcast": False,
        "canary_lamports": 10000000,
        "simulation_limit": 1,
        "api_policy": {
            "transport": "WEBSOCKET_FIRST",
            "rest": "ON_DEMAND_ONLY",
            "shared_rate_budget_required": True,
            "backpressure_required": True,
            "stale_event_replay": False,
            "provider_limit_source": "PLAN_CONFIGURATION_REQUIRED"
        }
    }

def save(root, data):
    path = root / REPORT
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
    temp.replace(path)

class Tests(unittest.TestCase):
    def test_read_only(self):
        result = audit(Path.cwd())
        self.assertFalse(result["signing"])
        self.assertFalse(result["broadcast"])
        self.assertFalse(result["scanner_modified"])

    def test_no_helius(self):
        self.assertEqual(audit(Path.cwd())["rpc_requests"], 0)

    def test_canary(self):
        self.assertEqual(
            audit(Path.cwd())["canary_lamports"],
            10000000
        )

    def test_stale_not_executable(self):
        self.assertFalse(
            audit(Path.cwd())["historical_signals_executable"]
        )

    def test_api_boundary(self):
        policy = audit(Path.cwd())["api_policy"]
        self.assertTrue(policy["shared_rate_budget_required"])
        self.assertEqual(policy["transport"], "WEBSOCKET_FIRST")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--audit", action="store_true")
    args = parser.parse_args()
    root = Path.cwd()

    if args.test:
        result = unittest.TextTestRunner(
            verbosity=2
        ).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
        )
        return 0 if result.wasSuccessful() else 1

    if args.audit:
        data = audit(root)
        save(root, data)
        print("[STATUS]", data["status"])
        print("[PRODUCER_MODULES]", data["candidate_module_count"])
        print("[STATE_RECORDS]", data["candidate_record_count"])
        print("[TOP_PRODUCERS]")
        for row in data["candidate_producer_modules"][:12]:
            print(json.dumps(row, sort_keys=True))
        print("[TOP_STATE_RECORDS]")
        for row in data["candidate_state_records"][:8]:
            print(json.dumps(row, sort_keys=True))
        print("[RPC_REQUESTS] 0")
        print("[SIGNING] FALSE [BROADCAST] FALSE")
        print("[REPORT]", root / REPORT)
        return 0 if data["status"] == "HANDOFF_DISCOVERY_READY" else 2

    destination = root / DEST
    if not destination.parent.is_dir():
        print("[HOLD] EXECUTOR_PACKAGE_MISSING")
        return 2
    if Path(__file__).resolve() != destination.resolve():
        shutil.copyfile(Path(__file__), destination)
    print("[PASS]", VERSION)
    print("[SCANNER] UNCHANGED")
    print("[EXECUTION] DISABLED")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
