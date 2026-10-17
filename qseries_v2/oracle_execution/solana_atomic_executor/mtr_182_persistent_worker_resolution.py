
from pathlib import Path
import argparse
import ast
import hashlib
import json
import shutil
import sys
import unittest

NAME = "mtr_182_persistent_worker_resolution"
PKG = Path("qseries_v2/oracle_execution/solana_atomic_executor")
Q19 = Path("qseries_v2/oracle_execution/oracle_019_venue_native_reserve_feed_cutover.py")
RISK = ("sign", "send_transaction", "send_raw_transaction",
        "broadcast", "keypair", "private_key", "secret",
        "subprocess", "popen", "exec", "eval", "system")

def dotted(n):
    if isinstance(n, ast.Name):
        return n.id
    if isinstance(n, ast.Attribute):
        return dotted(n.value) + "." + n.attr
    if isinstance(n, ast.Call):
        return "CALL:" + dotted(n.func)
    return type(n).__name__

def aliases(tree):
    out = {}
    for n in tree.body:
        if isinstance(n, ast.Import):
            for a in n.names:
                out[a.asname or a.name.split(".")[0]] = a.name
        elif isinstance(n, ast.ImportFrom) and not n.level:
            for a in n.names:
                out[a.asname or a.name] = (
                    (n.module or "") + "." + a.name
                )
    return out

def module_path(root, name):
    if not name or not all(x.isidentifier() for x in name.split(".")):
        return None
    p = root.joinpath(*name.split("."))
    for candidate in (p.with_suffix(".py"), p / "__init__.py"):
        if candidate.is_file():
            return candidate
    return None

def persistent_bindings(tree):
    out = []
    for n in tree.body:
        if isinstance(n, (ast.Assign, ast.AnnAssign)):
            targets = n.targets if isinstance(n, ast.Assign) else [n.target]
            if any(isinstance(t, ast.Name) and t.id == "persistent"
                   for t in targets):
                out.append({"line": n.lineno, "value": dotted(n.value)})
    return out

def workers(tree):
    found = []
    def visit(nodes, owners):
        for n in nodes:
            if isinstance(n, ast.ClassDef):
                visit(n.body, owners + [n.name])
            elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if n.name == "_worker":
                    calls = sorted({
                        dotted(x.func) for x in ast.walk(n)
                        if isinstance(x, ast.Call)
                    })
                    found.append({
                        "name": ".".join(owners + [n.name]),
                        "line": n.lineno,
                        "async": isinstance(n, ast.AsyncFunctionDef),
                        "calls": calls,
                        "risk_calls": [c for c in calls
                            if any(k in c.lower() for k in RISK)],
                    })
                visit(n.body, owners + [n.name])
    visit(tree.body, [])
    return found

def parse_file(path):
    data = path.read_bytes()
    return ast.parse(data.decode("utf-8-sig")), hashlib.sha256(data).hexdigest()

def audit(root):
    result = {
        "build": "MTR-182", "status": "HOLD",
        "target_canary_sol": "0.010",
        "sources": {}, "worker_candidates": [],
        "hold_reasons": [],
        "websocket_started": False, "key_access": False,
        "signed": False, "broadcast": False, "canary_sent": False,
        "profit_verified": False,
    }
    q19_path = root / Q19
    if not q19_path.is_file():
        result["hold_reasons"].append("Q19_MISSING")
        return result

    try:
        tree, digest = parse_file(q19_path)
        imports = aliases(tree)
        assignments = persistent_bindings(tree)
        result["sources"]["q19"] = {
            "path": str(Q19), "sha256": digest,
            "persistent_assignments": assignments,
            "q14_import": imports.get("q14"),
        }
        q14_module = imports.get("q14")
        if not q14_module:
            result["hold_reasons"].append("Q14_IMPORT_UNRESOLVED")
            return result
        path = module_path(root, q14_module)
        if path is None:
            result["hold_reasons"].append("Q14_SOURCE_MISSING")
            return result

        qtree, qdigest = parse_file(path)
        binding = persistent_bindings(qtree)
        candidates = workers(qtree)
        result["sources"]["q14"] = {
            "path": str(path.relative_to(root)),
            "sha256": qdigest,
            "persistent_assignments": binding,
            "imports": aliases(qtree),
        }
        result["worker_candidates"] = candidates
        if not candidates:
            result["hold_reasons"].append("WORKER_NOT_DEFINED_IN_Q14")
        if not binding:
            result["hold_reasons"].append("Q14_PERSISTENT_BINDING_MISSING")
        for item in candidates:
            if item["risk_calls"]:
                result["hold_reasons"].append(
                    "WORKER_RISK_CALLS_REQUIRE_REVIEW"
                )
    except (OSError, SyntaxError, UnicodeError, ValueError) as exc:
        result["hold_reasons"].append(
            "SOURCE_INSPECTION_FAILED_" + type(exc).__name__
        )

    result["hold_reasons"] += [
        "WORKER_OBJECT_IDENTITY_UNPROVEN",
        "TRANSITIVE_SIDE_EFFECTS_UNPROVEN",
        "PROCESS_NETWORK_ISOLATION_UNPROVEN",
        "NO_PHYSICAL_WEBSOCKET_CAPTURE",
        "NO_SIGNED_ATOMIC_SIMULATION",
    ]
    return result

class Tests(unittest.TestCase):
    def test_q14_alias(self):
        tree = ast.parse("from example import feed as q14")
        self.assertEqual(aliases(tree)["q14"], "example.feed")

    def test_persistent_binding(self):
        tree = ast.parse("persistent = Feed()")
        self.assertEqual(persistent_bindings(tree)[0]["value"], "CALL:Feed")

    def test_async_worker(self):
        tree = ast.parse(
            "class Feed:\n"
            "    async def _worker(self):\n"
            "        await observe()\n"
        )
        self.assertEqual(workers(tree)[0]["name"], "Feed._worker")

    def test_risk_call(self):
        tree = ast.parse(
            "class Feed:\n"
            "    async def _worker(self):\n"
            "        client.send_raw_transaction(x)\n"
        )
        self.assertTrue(workers(tree)[0]["risk_calls"])

    def test_missing_root_fails_closed(self):
        r = audit(Path("__missing_mtr182_root__"))
        self.assertEqual(r["status"], "HOLD")
        self.assertFalse(r["canary_sent"])

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
        result = audit(root)
        output = root / "MTR_182_PERSISTENT_WORKER_RESOLUTION.json"
        tmp = output.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(result, indent=2) + "\n",
                       encoding="utf-8")
        tmp.replace(output)
        print("[MTR182_STATUS]", result["status"])
        for name, source in result["sources"].items():
            print("[SOURCE]", name, source["path"])
            print("[SHA256]", source["sha256"])
            print("[PERSISTENT]", json.dumps(
                source["persistent_assignments"]))
            if name == "q19":
                print("[Q14_IMPORT]", source["q14_import"])
        print("[WORKER_CANDIDATES]", len(result["worker_candidates"]))
        for item in result["worker_candidates"]:
            print("[WORKER]", item["name"], "line=", item["line"],
                  "async=", item["async"])
            print("[CALLS]", json.dumps(item["calls"]))
            print("[RISK_CALLS]", json.dumps(item["risk_calls"]))
        for reason in result["hold_reasons"]:
            print("[HOLD]", reason)
        print("[REPORT]", output)
        print("[SIGNING] FALSE")
        print("[BROADCAST] FALSE")
        print("[LIVE_CAPTURE] FALSE")
        return 0

    dest = root / PKG / (NAME + ".py")
    if not dest.parent.is_dir():
        print("[FAIL] Canonical package directory missing")
        return 1
    source = Path(__file__).resolve()
    if source != dest.resolve():
        shutil.copyfile(source, dest)
    print("[PASS] MTR-182 installed:", dest)
    print("[SCOPE] Worker source resolution; no execution")
    return 0

if __name__ == "__main__":
    sys.exit(main())
