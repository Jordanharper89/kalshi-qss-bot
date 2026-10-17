
from pathlib import Path
import argparse
import ast
import hashlib
import json
import shutil
import sys
import unittest

NAME = "mtr_180_external_ownership_gate"
PKG = Path("qseries_v2/oracle_execution/solana_atomic_executor")
RUNTIME = PKG / "runtime.py"
Q87 = ("qseries_v2.oracle_strategy_intelligence.solana_money."
       "qarb_execution_engineering."
       "qarb_087_two_second_compaction_liquidity_repair")
TARGETS = {"_worker", "signed_tx"}

def module_file(root, module):
    if not module or module.startswith("."):
        return None
    path = root.joinpath(*module.split("."))
    for candidate in (path.with_suffix(".py"), path / "__init__.py"):
        if candidate.is_file():
            return candidate
    return None

def bindings(tree):
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Import):
            for a in node.names:
                out[a.asname or a.name.split(".")[0]] = a.name
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            for a in node.names:
                out[a.asname or a.name] = (
                    (node.module or "") + "." + a.name
                )
    return out

def definitions(tree, target):
    found = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == target:
                found.append({
                    "line": node.lineno,
                    "async": isinstance(node, ast.AsyncFunctionDef),
                    "parameter_names": [
                        a.arg for a in node.args.posonlyargs + node.args.args
                    ],
                })
    return found

def inspect_file(root, path):
    raw = path.read_bytes()
    tree = ast.parse(raw.decode("utf-8-sig"))
    return {
        "path": str(path.relative_to(root)),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "imports": bindings(tree),
        "worker_definitions": definitions(tree, "_worker"),
        "signed_tx_definitions": definitions(tree, "signed_tx"),
    }

def inspect_module(root, module):
    path = module_file(root, module)
    if path is None:
        return {"module": module, "status": "MISSING"}
    try:
        record = inspect_file(root, path)
        record["module"] = module
        record["status"] = "PARSED"
        return record
    except (SyntaxError, UnicodeError, OSError, ValueError) as exc:
        return {
            "module": module,
            "status": "UNREADABLE",
            "error_type": type(exc).__name__,
        }

def resolve(root):
    result = {
        "build": "MTR-180",
        "status": "HOLD",
        "canary_sol": "0.010",
        "sources": {},
        "hold_reasons": [],
        "live_capture": False,
        "signed": False,
        "broadcast": False,
        "private_key_access": False,
        "canary_sent": False,
        "profit_verified": False,
    }
    runtime = root / RUNTIME
    if not runtime.is_file():
        result["hold_reasons"].append("RUNTIME_NOT_FOUND")
        return result

    try:
        entry = inspect_file(root, runtime)
    except (SyntaxError, UnicodeError, OSError, ValueError):
        result["hold_reasons"].append("RUNTIME_UNREADABLE")
        return result

    result["sources"]["runtime"] = {
        "path": entry["path"],
        "sha256": entry["sha256"],
    }

    q25 = entry["imports"].get("q25")
    if not q25:
        result["hold_reasons"].append("Q25_IMPORT_UNRESOLVED")
    else:
        q25_record = inspect_module(root, q25)
        result["sources"]["q25"] = q25_record

        if q25_record["status"] == "PARSED":
            q19 = q25_record["imports"].get("q19")
            if q19:
                result["sources"]["q19"] = inspect_module(root, q19)
            else:
                result["hold_reasons"].append("Q19_ALIAS_UNRESOLVED")
        else:
            result["hold_reasons"].append("Q25_SOURCE_UNRESOLVED")

    q87_record = inspect_module(root, Q87)
    result["sources"]["q87"] = q87_record

    if q87_record["status"] == "PARSED":
        c_binding = q87_record["imports"].get("c")
        if c_binding:
            result["sources"]["q87_c"] = inspect_module(root, c_binding)
        else:
            result["hold_reasons"].append("Q87_C_BINDING_UNRESOLVED")
    else:
        result["hold_reasons"].append("Q87_SOURCE_UNRESOLVED")

    result["hold_reasons"].extend([
        "OBJECT_IDENTITY_NOT_PROVEN",
        "TRANSITIVE_EXECUTION_SAFETY_NOT_PROVEN",
        "CAPTURE_PROCESS_ISOLATION_NOT_PROVEN",
        "LIVE_CAPTURE_NOT_PERFORMED",
        "SIGNED_ATOMIC_SIMULATION_NOT_PERFORMED",
    ])
    return result

class Tests(unittest.TestCase):
    def test_import_alias(self):
        tree = ast.parse("import example.worker as q19")
        self.assertEqual(bindings(tree)["q19"], "example.worker")

    def test_from_import(self):
        tree = ast.parse("from example import worker as q19")
        self.assertEqual(bindings(tree)["q19"], "example.worker")

    def test_definition(self):
        tree = ast.parse("async def _worker(self):\n    pass\n")
        self.assertTrue(definitions(tree, "_worker")[0]["async"])

    def test_missing_root(self):
        report = resolve(Path("__missing_mtr180_root__"))
        self.assertEqual(report["status"], "HOLD")
        self.assertIn("RUNTIME_NOT_FOUND", report["hold_reasons"])

    def test_no_execution(self):
        report = resolve(Path("__missing_mtr180_root__"))
        self.assertFalse(report["signed"])
        self.assertFalse(report["broadcast"])
        self.assertFalse(report["canary_sent"])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--audit", action="store_true")
    args = parser.parse_args()

    if args.test:
        run = unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
        )
        return 0 if run.wasSuccessful() else 1

    root = Path.cwd()
    if args.audit:
        report = resolve(root)
        output = root / "MTR_180_EXTERNAL_OWNERSHIP.json"
        tmp = output.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        tmp.replace(output)

        print("[MTR180_STATUS]", report["status"])
        for label, source in report["sources"].items():
            print("[SOURCE]", label, source.get("status", "PARSED"))
            print("[PATH]", source.get("path", source.get("module")))
            for name in ("_worker", "signed_tx"):
                for item in source.get(name + "_definitions", []):
                    print("[DEFINITION]", name, "line=", item["line"])
            if label == "q25":
                print("[Q19_BINDING]", source.get("imports", {}).get("q19"))
            if label == "q87":
                print("[C_BINDING]", source.get("imports", {}).get("c"))
        for reason in report["hold_reasons"]:
            print("[HOLD]", reason)
        print("[REPORT]", output)
        print("[LIVE_CAPTURE] FALSE")
        print("[SIGNING] FALSE")
        print("[BROADCAST] FALSE")
        return 0

    destination = root / PKG / (NAME + ".py")
    if not destination.parent.is_dir():
        print("[FAIL] Canonical package missing")
        return 1
    source = Path(__file__).resolve()
    if source != destination.resolve():
        shutil.copyfile(source, destination)
    print("[PASS] MTR-180 installed:", destination)
    print("[SCOPE] External source ownership; no runtime activation")
    return 0

if __name__ == "__main__":
    sys.exit(main())
