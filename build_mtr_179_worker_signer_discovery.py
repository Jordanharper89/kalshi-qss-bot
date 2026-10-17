
from pathlib import Path
import argparse
import ast
import hashlib
import json
import shutil
import sys
import unittest

NAME = "mtr_179_worker_signer_discovery"
PKG = Path("qseries_v2/oracle_execution/solana_atomic_executor")
RUNTIME = PKG / "runtime.py"
TARGETS = {"_worker", "signed_tx"}
MAX_CANDIDATES = 30

def dotted(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return dotted(node.value) + "." + node.attr
    if isinstance(node, ast.Call):
        return "CALL:" + dotted(node.func)
    return type(node).__name__

def inspect_runtime(source):
    tree = ast.parse(source)
    assignments = []
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = (
                node.targets if isinstance(node, ast.Assign)
                else [node.target]
            )
            for target in targets:
                if isinstance(target, ast.Name) and target.id in {
                    "persistent", "q87"
                }:
                    assignments.append({
                        "name": target.id,
                        "line": node.lineno,
                        "value_shape": dotted(node.value),
                    })
        if isinstance(node, ast.Import):
            for item in node.names:
                if item.asname == "q87" or item.name.endswith("q87"):
                    imports.append({
                        "line": node.lineno,
                        "module": item.name,
                        "alias": item.asname,
                    })
        if isinstance(node, ast.ImportFrom):
            for item in node.names:
                if item.asname == "q87" or item.name == "q87":
                    imports.append({
                        "line": node.lineno,
                        "module": "." * node.level + (node.module or ""),
                        "name": item.name,
                        "alias": item.asname,
                    })
    return {"assignments": assignments, "imports": imports}

def inspect_definitions(source, relative_path):
    tree = ast.parse(source)
    found = []
    def walk(nodes, owners):
        for node in nodes:
            if isinstance(node, ast.ClassDef):
                walk(node.body, owners + [node.name])
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name in TARGETS:
                    calls = sorted({
                        dotted(child.func)
                        for child in ast.walk(node)
                        if isinstance(child, ast.Call)
                    })
                    found.append({
                        "path": relative_path,
                        "qualified_name": ".".join(owners + [node.name]),
                        "line": node.lineno,
                        "async": isinstance(node, ast.AsyncFunctionDef),
                        "arguments": [
                            arg.arg for arg in node.args.args
                        ],
                        "call_names": calls[:80],
                        "call_count": len(calls),
                    })
                walk(node.body, owners + [node.name])
    walk(tree.body, [])
    return found

def audit(root):
    base = root / PKG
    report = {
        "build": "MTR-179",
        "status": "HOLD",
        "target_canary_sol": "0.010",
        "runtime_started": False,
        "websocket_connected": False,
        "private_key_read": False,
        "transaction_signed": False,
        "transaction_broadcast": False,
        "canary_sent": False,
        "realized_profit_verified": False,
        "hold_reasons": [],
        "definitions": [],
    }
    runtime = root / RUNTIME
    if not runtime.is_file():
        report["hold_reasons"].append("RUNTIME_NOT_FOUND")
        return report

    data = runtime.read_bytes()
    report["runtime_sha256"] = hashlib.sha256(data).hexdigest()
    try:
        report["runtime_bindings"] = inspect_runtime(
            data.decode("utf-8-sig")
        )
    except (SyntaxError, UnicodeError):
        report["hold_reasons"].append("RUNTIME_PARSE_FAILED")
        return report

    errors = 0
    file_count = 0
    for path in sorted(base.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        file_count += 1
        try:
            relative = str(path.relative_to(root))
            matches = inspect_definitions(
                path.read_text(encoding="utf-8-sig"),
                relative,
            )
            report["definitions"].extend(matches)
        except (SyntaxError, UnicodeError, OSError):
            errors += 1

    report["files_examined"] = file_count
    report["files_unreadable_or_unparseable"] = errors
    report["worker_candidates"] = sum(
        item["qualified_name"].split(".")[-1] == "_worker"
        for item in report["definitions"]
    )
    report["signed_tx_candidates"] = sum(
        item["qualified_name"].split(".")[-1] == "signed_tx"
        for item in report["definitions"]
    )
    report["hold_reasons"].extend([
        "WORKER_INSTANCE_TYPE_NOT_CERTIFIED",
        "SIGNED_TX_CALL_SEMANTICS_NOT_CERTIFIED",
        "DYNAMIC_IMPORTS_AND_DISPATCH_UNRESOLVED",
        "CAPTURE_PROCESS_ISOLATION_NOT_CERTIFIED",
        "NO_LIVE_WEBSOCKET_CAPTURE",
        "NO_SIGNED_ATOMIC_SIMULATION",
    ])
    if errors:
        report["hold_reasons"].append("SOME_SOURCE_FILES_UNPARSEABLE")
    return report

class Tests(unittest.TestCase):
    def test_worker_discovery(self):
        src = "class Persistent:\n    async def _worker(self):\n        await run()\n"
        found = inspect_definitions(src, "fixture.py")
        self.assertEqual(found[0]["qualified_name"], "Persistent._worker")
        self.assertTrue(found[0]["async"])

    def test_signer_discovery(self):
        src = "class C:\n    def signed_tx(self, x):\n        return x\n"
        found = inspect_definitions(src, "fixture.py")
        self.assertEqual(found[0]["qualified_name"], "C.signed_tx")

    def test_binding_discovery(self):
        src = "persistent = Factory()\nimport example as q87\n"
        result = inspect_runtime(src)
        self.assertEqual(
            result["assignments"][0]["value_shape"], "CALL:Factory"
        )
        self.assertEqual(result["imports"][0]["alias"], "q87")

    def test_missing_root_holds(self):
        result = audit(Path("__mtr179_missing_root__"))
        self.assertEqual(result["status"], "HOLD")
        self.assertIn("RUNTIME_NOT_FOUND", result["hold_reasons"])

    def test_no_execution(self):
        result = audit(Path("__mtr179_missing_root__"))
        self.assertFalse(result["transaction_signed"])
        self.assertFalse(result["transaction_broadcast"])
        self.assertFalse(result["canary_sent"])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--audit", action="store_true")
    args = parser.parse_args()

    if args.test:
        result = unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
        )
        return 0 if result.wasSuccessful() else 1

    root = Path.cwd()
    if args.audit:
        report = audit(root)
        output = root / "MTR_179_WORKER_SIGNER_DISCOVERY.json"
        temp = output.with_suffix(".json.tmp")
        temp.write_text(
            json.dumps(report, indent=2) + "\n",
            encoding="utf-8",
        )
        temp.replace(output)

        print("[MTR179_STATUS]", report["status"])
        print("[FILES_EXAMINED]", report.get("files_examined", 0))
        print("[PARSE_FAILURES]",
              report.get("files_unreadable_or_unparseable", 0))
        for item in report.get("runtime_bindings", {}).get(
            "assignments", []
        ):
            print("[BINDING]", item["line"], item["name"],
                  item["value_shape"])
        for item in report.get("runtime_bindings", {}).get(
            "imports", []
        ):
            print("[Q87_IMPORT]", json.dumps(item))
        print("[WORKER_CANDIDATES]",
              report.get("worker_candidates", 0))
        print("[SIGNED_TX_CANDIDATES]",
              report.get("signed_tx_candidates", 0))
        for item in report["definitions"][:MAX_CANDIDATES]:
            print("[DEFINITION]", item["path"],
                  "line=", item["line"],
                  "name=", item["qualified_name"])
            print("[CALL_NAMES]", json.dumps(item["call_names"]))
        for reason in report["hold_reasons"]:
            print("[HOLD]", reason)
        print("[REPORT]", output)
        print("[SIGNING] FALSE")
        print("[BROADCAST] FALSE")
        print("[LIVE_CAPTURE] FALSE")
        return 0

    destination = root / PKG / (NAME + ".py")
    if not destination.parent.is_dir():
        print("[FAIL] Canonical package directory missing")
        return 1
    source = Path(__file__).resolve()
    if source != destination.resolve():
        shutil.copyfile(source, destination)
    print("[PASS] MTR-179 installed:", destination)
    print("[SCOPE] Static worker/signer discovery only")
    return 0

if __name__ == "__main__":
    sys.exit(main())
