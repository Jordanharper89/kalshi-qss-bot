
from pathlib import Path
import argparse
import ast
import hashlib
import json
import shutil
import sys
import unittest

NAME = "mtr_178_capture_execution_separation"
PKG = Path("qseries_v2/oracle_execution/solana_atomic_executor")
SOURCE = PKG / "runtime.py"

TARGETS = (
    ("canonical_price", "fast_live_attack"),
    ("fast_live_attack", "compile_current"),
    ("compile_current", "q87.c.signed_tx"),
    ("serve_canonical", "asyncio.create_task"),
)

def dotted(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return dotted(node.value) + "." + node.attr
    return "<dynamic>"

def shape(node):
    if isinstance(node, (ast.Name, ast.Attribute)):
        return dotted(node)
    if isinstance(node, ast.Call):
        return "CALL:" + dotted(node.func)
    if isinstance(node, ast.Await):
        return "AWAIT:" + shape(node.value)
    if isinstance(node, ast.Constant):
        return "<literal>"
    if isinstance(node, (ast.Tuple, ast.List, ast.Dict)):
        return type(node).__name__
    return type(node).__name__

def definitions(tree):
    found = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            found.setdefault(node.name, []).append(node)
    return found

def inspect_function(node, target):
    parents = {}
    for parent in ast.walk(node):
        for child in ast.iter_child_nodes(parent):
            parents[id(child)] = parent

    matches = []
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        if dotted(child.func) != target:
            continue
        current = child
        guards = []
        while id(current) in parents:
            current = parents[id(current)]
            if isinstance(current, ast.If):
                guards.append({
                    "kind": "IF",
                    "line": current.lineno,
                    "condition": shape(current.test),
                })
            elif isinstance(current, (ast.For, ast.While, ast.AsyncFor)):
                guards.append({
                    "kind": type(current).__name__,
                    "line": current.lineno,
                })
            elif isinstance(current, ast.Try):
                guards.append({
                    "kind": "TRY",
                    "line": current.lineno,
                })
            elif isinstance(current, (ast.FunctionDef,
                                      ast.AsyncFunctionDef)) and current is not node:
                guards.append({
                    "kind": "NESTED_FUNCTION",
                    "line": current.lineno,
                })
        matches.append({
            "line": child.lineno,
            "arguments": [shape(a) for a in child.args],
            "keywords": {
                k.arg or "<unpacked>": shape(k.value)
                for k in child.keywords
            },
            "context": list(reversed(guards)),
        })
    return matches

def audit_source(source):
    tree = ast.parse(source)
    funcs = definitions(tree)
    evidence = []
    blockers = []
    for owner, target in TARGETS:
        candidates = funcs.get(owner, [])
        if len(candidates) != 1:
            blockers.append("MISSING_OR_AMBIGUOUS:" + owner)
            evidence.append({
                "owner": owner,
                "target": target,
                "status": "HOLD",
                "definition_count": len(candidates),
            })
            continue
        node = candidates[0]
        calls = inspect_function(node, target)
        if not calls:
            blockers.append("TARGET_NOT_FOUND:" + owner)
        evidence.append({
            "owner": owner,
            "definition_line": node.lineno,
            "target": target,
            "matches": calls,
            "status": "FOUND" if calls else "HOLD",
        })
    blockers.extend([
        "CREATED_TASK_TRANSITIVE_BEHAVIOR_UNPROVEN",
        "SIGNED_TX_SEMANTICS_UNPROVEN",
        "CAPTURE_EXECUTION_SEPARATION_UNPROVEN",
        "LIVE_WEBSOCKET_CAPTURE_NOT_PERFORMED",
    ])
    return evidence, sorted(set(blockers))

def audit(root):
    path = root / SOURCE
    report = {
        "build": "MTR-178",
        "status": "HOLD",
        "target_canary_sol": "0.010",
        "scope": "READ_ONLY_AST_SEPARATION_EVIDENCE",
        "runtime_started": False,
        "wallet_access": False,
        "signed": False,
        "broadcast": False,
        "canary_sent": False,
        "realized_profit_verified": False,
    }
    if not path.is_file():
        report["hold_reasons"] = ["RUNTIME_SOURCE_MISSING"]
        return report
    raw = path.read_bytes()
    report["source_sha256"] = hashlib.sha256(raw).hexdigest()
    try:
        evidence, blockers = audit_source(raw.decode("utf-8-sig"))
        report["call_boundaries"] = evidence
        report["hold_reasons"] = blockers
    except (SyntaxError, UnicodeError) as exc:
        report["hold_reasons"] = ["SOURCE_PARSE_FAILED"]
        report["error_type"] = type(exc).__name__
    return report

class Tests(unittest.TestCase):
    def test_task_argument(self):
        src = ("async def serve_canonical():\n"
               "    asyncio.create_task(worker())\n")
        evidence, _ = audit_source(src)
        task = evidence[-1]["matches"][0]
        self.assertEqual(task["arguments"], ["CALL:worker"])

    def test_signed_call_shape(self):
        src = ("def compile_current():\n"
               "    q87.c.signed_tx(value, secret='hidden')\n")
        evidence, _ = audit_source(src)
        call = evidence[2]["matches"][0]
        self.assertEqual(call["arguments"], ["value"])
        self.assertEqual(call["keywords"]["secret"], "<literal>")

    def test_guard_record(self):
        src = ("def compile_current():\n"
               "    if allowed:\n"
               "        q87.c.signed_tx(value)\n")
        evidence, _ = audit_source(src)
        self.assertEqual(
            evidence[2]["matches"][0]["context"][0]["kind"], "IF"
        )

    def test_missing_boundary_holds(self):
        evidence, blockers = audit_source("def other():\n    pass\n")
        self.assertEqual(evidence[0]["status"], "HOLD")
        self.assertTrue(blockers)

    def test_missing_source_no_execution(self):
        result = audit(Path("__mtr178_missing__"))
        self.assertEqual(result["status"], "HOLD")
        self.assertFalse(result["canary_sent"])
        self.assertFalse(result["broadcast"])

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
        result = audit(root)
        output = root / "MTR_178_CAPTURE_EXECUTION_SEPARATION.json"
        tmp = output.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8"
        )
        tmp.replace(output)
        for entry in result.get("call_boundaries", []):
            print("[BOUNDARY]", entry["owner"], "->", entry["target"])
            print("[STATUS]", entry["status"])
            for match in entry.get("matches", []):
                print("[CALL_LINE]", match["line"])
                print("[ARGUMENTS]", json.dumps(match["arguments"]))
                print("[KEYWORDS]", json.dumps(match["keywords"]))
                print("[CONTEXT]", json.dumps(match["context"]))
        for reason in result["hold_reasons"]:
            print("[HOLD]", reason)
        print("[REPORT]", output)
        print("[SIGNING] FALSE")
        print("[BROADCAST] FALSE")
        print("[LIVE_CAPTURE] FALSE")
        return 0

    dest = root / PKG / (NAME + ".py")
    if not dest.parent.is_dir():
        print("[FAIL] Canonical directory missing")
        return 1
    src = Path(__file__).resolve()
    if src != dest.resolve():
        shutil.copyfile(src, dest)
    print("[PASS] MTR-178 installed:", dest)
    print("[SCOPE] Source boundary evidence; execution disabled")
    return 0

if __name__ == "__main__":
    sys.exit(main())
