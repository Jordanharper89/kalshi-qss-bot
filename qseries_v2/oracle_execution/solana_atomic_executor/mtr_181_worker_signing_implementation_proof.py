
from pathlib import Path
import argparse
import ast
import hashlib
import json
import shutil
import sys
import unittest

NAME = "mtr_181_worker_signing_implementation_proof"
PKG = Path("qseries_v2/oracle_execution/solana_atomic_executor")
WORKER = Path("qseries_v2/oracle_execution/oracle_019_venue_native_reserve_feed_cutover.py")
SIGNER = Path("qseries_v2/oracle_strategy_intelligence/solana_money/native_atomic_money_machine/core.py")

def dotted(n):
    if isinstance(n, ast.Name):
        return n.id
    if isinstance(n, ast.Attribute):
        return dotted(n.value) + "." + n.attr
    if isinstance(n, ast.Call):
        return "CALL:" + dotted(n.func)
    return type(n).__name__

def calls(n):
    return sorted(set(
        dotted(x.func) for x in ast.walk(n)
        if isinstance(x, ast.Call)
    ))

def definitions(tree, name):
    result = []
    def visit(nodes, owners):
        for n in nodes:
            if isinstance(n, ast.ClassDef):
                visit(n.body, owners + [n.name])
            elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if n.name == name:
                    result.append({
                        "qualified_name": ".".join(owners + [name]),
                        "line": n.lineno,
                        "end_line": n.end_lineno,
                        "async": isinstance(n, ast.AsyncFunctionDef),
                        "calls": calls(n),
                        "parameters": [a.arg for a in n.args.args],
                    })
                visit(n.body, owners + [n.name])
    visit(tree.body, [])
    return result

def assignments(tree, name):
    found = []
    for n in ast.walk(tree):
        if isinstance(n, (ast.Assign, ast.AnnAssign)):
            targets = n.targets if isinstance(n, ast.Assign) else [n.target]
            for target in targets:
                if isinstance(target, ast.Name) and target.id == name:
                    found.append({
                        "line": n.lineno,
                        "value_shape": dotted(n.value),
                    })
    return found

def inspect(path, target):
    raw = path.read_bytes()
    tree = ast.parse(raw.decode("utf-8-sig"))
    return {
        "sha256": hashlib.sha256(raw).hexdigest(),
        "definitions": definitions(tree, target),
        "persistent_assignments": assignments(tree, "persistent"),
        "module_calls": sorted(set(
            dotted(n.func) for item in tree.body
            if not isinstance(item, (
                ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef
            ))
            for n in ast.walk(item) if isinstance(n, ast.Call)
        )),
    }

def audit(root):
    result = {
        "build": "MTR-181",
        "status": "HOLD",
        "target_canary_sol": "0.010",
        "sources": {},
        "hold_reasons": [],
        "runtime_started": False,
        "wallet_access": False,
        "signing": False,
        "broadcast": False,
        "live_capture": False,
        "canary_sent": False,
        "profit_verified": False,
    }
    for label, relative, target in (
        ("worker", WORKER, "_worker"),
        ("signer", SIGNER, "signed_tx"),
    ):
        path = root / relative
        if not path.is_file():
            result["hold_reasons"].append("MISSING_" + label.upper())
            continue
        try:
            record = inspect(path, target)
            record["path"] = str(relative)
            result["sources"][label] = record
            if not record["definitions"]:
                result["hold_reasons"].append(
                    "DEFINITION_NOT_LOCAL_" + label.upper()
                )
        except (SyntaxError, UnicodeError, OSError, ValueError) as exc:
            result["hold_reasons"].append(
                "UNREADABLE_" + label.upper() + "_" + type(exc).__name__
            )

    result["hold_reasons"].extend([
        "WORKER_OBJECT_IDENTITY_NOT_CERTIFIED",
        "WORKER_TRANSITIVE_SIDE_EFFECTS_NOT_CERTIFIED",
        "SIGNER_IMPLEMENTATION_NOT_EXECUTED",
        "NETWORK_PROCESS_ISOLATION_NOT_CERTIFIED",
        "LIVE_CAPTURE_NOT_PERFORMED",
        "ATOMIC_SIMULATION_NOT_PERFORMED",
    ])
    return result

class Tests(unittest.TestCase):
    def test_worker_definition(self):
        tree = ast.parse(
            "class Feed:\n"
            "    async def _worker(self):\n"
            "        await observe()\n"
        )
        d = definitions(tree, "_worker")
        self.assertEqual(d[0]["qualified_name"], "Feed._worker")
        self.assertIn("observe", d[0]["calls"])

    def test_signer_definition(self):
        tree = ast.parse(
            "def signed_tx(message, signer):\n"
            "    return signer.sign(message)\n"
        )
        d = definitions(tree, "signed_tx")
        self.assertIn("signer.sign", d[0]["calls"])

    def test_persistent_assignment(self):
        tree = ast.parse("persistent = Worker()\n")
        self.assertEqual(
            assignments(tree, "persistent")[0]["value_shape"],
            "CALL:Worker",
        )

    def test_missing_root_fails_closed(self):
        result = audit(Path("__missing_mtr181__"))
        self.assertEqual(result["status"], "HOLD")
        self.assertFalse(result["canary_sent"])

    def test_no_execution(self):
        result = audit(Path("__missing_mtr181__"))
        self.assertFalse(result["signing"])
        self.assertFalse(result["broadcast"])
        self.assertFalse(result["live_capture"])

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--test", action="store_true")
    p.add_argument("--audit", action="store_true")
    args = p.parse_args()
    if args.test:
        r = unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
        )
        return 0 if r.wasSuccessful() else 1

    root = Path.cwd()
    if args.audit:
        report = audit(root)
        path = root / "MTR_181_WORKER_SIGNING_PROOF.json"
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        tmp.replace(path)
        print("[MTR181_STATUS]", report["status"])
        for label, record in report["sources"].items():
            print("[SOURCE]", label, record["path"])
            print("[SHA256]", record["sha256"])
            for item in record["definitions"]:
                print("[DEFINITION]", item["qualified_name"],
                      "lines=", item["line"], "-", item["end_line"])
                print("[PARAMETERS]", json.dumps(item["parameters"]))
                print("[CALLS]", json.dumps(item["calls"]))
            if label == "worker":
                print("[PERSISTENT_ASSIGNMENTS]",
                      json.dumps(record["persistent_assignments"]))
                print("[MODULE_CALLS]",
                      json.dumps(record["module_calls"]))
        for reason in report["hold_reasons"]:
            print("[HOLD]", reason)
        print("[REPORT]", path)
        print("[SIGNING] FALSE")
        print("[BROADCAST] FALSE")
        print("[LIVE_CAPTURE] FALSE")
        return 0

    dest = root / PKG / (NAME + ".py")
    if not dest.parent.is_dir():
        print("[FAIL] Canonical executor package missing")
        return 1
    src = Path(__file__).resolve()
    if src != dest.resolve():
        shutil.copyfile(src, dest)
    print("[PASS] MTR-181 installed:", dest)
    print("[SCOPE] Source inspection only; no runtime activation")
    return 0

if __name__ == "__main__":
    sys.exit(main())
