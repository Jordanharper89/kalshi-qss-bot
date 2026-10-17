
from pathlib import Path
import argparse
import ast
import json
import shutil
import unittest

VERSION = "ORACLE_030_ORIGINAL_SCANNER_LIVE_PRODUCER_BINDING"
PKG = Path("qseries_v2/oracle_execution/solana_atomic_executor")
DEST = PKG / "oracle_030_live_producer_binding.py"
REPORT = Path("runtime_state/oracle/oracle_live_execution/ORACLE_030_BINDING.json")

TARGETS = {
    "mriya_discovery":
        Path("qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot/engine.py"),
    "ws_capture":
        PKG / "mtr_165_ws_capture_only.py",
    "capture_lane":
        PKG / "mtr_169_capture_lane_integration.py",
    "market_startup":
        PKG / "mtr_172_isolated_market_startup.py",
    "atomic_runtime":
        PKG / "runtime.py",
}

SYMBOLS = {
    "mriya_hot_tokens",
    "raw_candidate_universe",
    "candidate_universe",
    "prepare_pairs",
    "make_capture_lane",
    "route_capture_cb",
    "capture_only",
    "exact_snapshot_opportunities",
    "same_snapshot_route",
    "canonical_price",
    "compile_current",
    "simulate_current",
    "build_bound",
}

def name_of(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = name_of(node.value)
        return prefix + "." + node.attr if prefix else node.attr
    return ""

def inspect_file(root, relative):
    path = root / relative
    if not path.is_file():
        return {"path": str(relative), "exists": False}

    tree = ast.parse(
        path.read_text(encoding="utf-8-sig"),
        filename=str(path)
    )
    functions = []
    imports = []
    calls = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in SYMBOLS or relative.name.startswith("mtr_"):
                functions.append({
                    "name": node.name,
                    "line": node.lineno,
                    "arguments": [
                        a.arg for a in node.args.args
                    ],
                    "calls": sorted({
                        name_of(call.func)
                        for call in ast.walk(node)
                        if isinstance(call, ast.Call)
                        and name_of(call.func)
                    })[:45]
                })
        elif isinstance(node, ast.ImportFrom):
            if node.module and (
                "oracle" in node.module
                or "solana" in node.module
            ):
                imports.append(node.module)
        elif isinstance(node, ast.Call):
            n = name_of(node.func)
            if any(n.endswith(x) for x in SYMBOLS):
                calls.append({
                    "name": n,
                    "line": node.lineno
                })

    return {
        "path": str(relative),
        "exists": True,
        "functions": functions[:35],
        "imports": sorted(set(imports))[:35],
        "symbol_calls": calls[:50],
    }

def find_consumers(root):
    folders = [
        PKG,
        Path("qseries_v2/oracle_strategy_intelligence/solana_money")
    ]
    found = []
    seen = set()
    needles = (
        "make_capture_lane(",
        "route_capture_cb(",
        "mriya_hot_tokens(",
        "candidate_universe(",
    )

    for folder in folders:
        base = root / folder
        if not base.is_dir():
            continue
        for path in base.rglob("*.py"):
            if path in seen:
                continue
            seen.add(path)
            try:
                source = path.read_text(encoding="utf-8-sig")
            except (OSError, UnicodeError):
                continue
            matched = [x for x in needles if x in source]
            if matched:
                found.append({
                    "path": str(path.relative_to(root)),
                    "symbols": matched
                })

    return sorted(found, key=lambda x: x["path"])

def audit(root):
    files = {
        name: inspect_file(root, path)
        for name, path in TARGETS.items()
    }
    consumers = find_consumers(root)
    return {
        "revision": VERSION,
        "status": "SOURCE_BINDING_DISCOVERED",
        "source_contracts": files,
        "caller_inventory": consumers[:65],
        "caller_count": len(consumers),
        "producer_runtime_certified": False,
        "live_handoff_activated": False,
        "historical_prices_executable": False,
        "fresh_identity_required": True,
        "fresh_pricing_required": True,
        "rpc_requests": 0,
        "private_key_used": False,
        "signing": False,
        "broadcast": False,
        "canary_lamports": 10000000,
    }

def save(root, result):
    path = root / REPORT
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
    temp.replace(path)

class Tests(unittest.TestCase):
    def test_no_rpc(self):
        self.assertEqual(audit(Path.cwd())["rpc_requests"], 0)

    def test_execution_locked(self):
        result = audit(Path.cwd())
        self.assertFalse(result["signing"])
        self.assertFalse(result["broadcast"])

    def test_no_old_prices(self):
        self.assertFalse(
            audit(Path.cwd())["historical_prices_executable"]
        )

    def test_capture_module_present(self):
        self.assertTrue(
            audit(Path.cwd())["source_contracts"]["ws_capture"]["exists"]
        )

    def test_exact_canary(self):
        self.assertEqual(
            audit(Path.cwd())["canary_lamports"], 10000000
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
        for name, contract in result["source_contracts"].items():
            print(
                "[SOURCE_CONTRACT]", name,
                json.dumps(contract, sort_keys=True)
            )
        print("[CALLER_COUNT]", result["caller_count"])
        for row in result["caller_inventory"]:
            print("[CALLER]", json.dumps(row, sort_keys=True))
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
    print("[PASS]", VERSION, target)
    print("[SCANNER] FROZEN")
    print("[EXECUTION] DISABLED")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
