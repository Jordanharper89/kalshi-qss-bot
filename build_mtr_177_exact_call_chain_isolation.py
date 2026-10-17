
from pathlib import Path
import argparse
import ast
import hashlib
import json
import shutil
import sys
import unittest

NAME = "mtr_177_exact_call_chain_isolation"
PKG = Path("qseries_v2/oracle_execution/solana_atomic_executor")
SOURCE = PKG / "runtime.py"
TARGETS = {
    "canonical_price": "q87.c.signed_tx",
    "serve_canonical": "asyncio.create_task",
}

def dotted(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return dotted(node.value) + "." + node.attr
    return "<dynamic>"

def inventory(source):
    tree = ast.parse(source)
    funcs = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            funcs[node.name] = node
        elif isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    funcs[node.name + "." + child.name] = child
    return funcs

def calls_inside(fn):
    found = []
    parents = {}
    for parent in ast.walk(fn):
        for child in ast.iter_child_nodes(parent):
            parents[id(child)] = parent

    for node in ast.walk(fn):
        if not isinstance(node, ast.Call):
            continue
        name = dotted(node.func)
        guards = []
        current = node
        while id(current) in parents:
            current = parents[id(current)]
            if isinstance(current, ast.If):
                guards.append({
                    "kind": "IF",
                    "line": current.lineno,
                })
            elif isinstance(current, ast.Try):
                guards.append({
                    "kind": "TRY",
                    "line": current.lineno,
                })
            elif isinstance(current, (ast.For, ast.While, ast.AsyncFor)):
                guards.append({
                    "kind": "LOOP",
                    "line": current.lineno,
                })
        found.append({
            "call": name,
            "line": node.lineno,
            "context": list(reversed(guards)),
        })
    return found

def resolve(name, current, funcs):
    if name in funcs:
        return name
    if name.startswith(("self.", "cls.")):
        owner = current.rsplit(".", 1)[0] if "." in current else ""
        target = owner + "." + name.split(".", 1)[1]
        if target in funcs:
            return target
    return None

def trace(source, entry, target):
    funcs = inventory(source)
    if entry not in funcs:
        matches = [k for k in funcs if k.endswith("." + entry)]
        if len(matches) != 1:
            return {"status": "HOLD_ENTRY_AMBIGUOUS", "matches": matches}
        entry = matches[0]

    queue = [(entry, [])]
    visited = set()
    evidence = []
    dynamic_calls = []

    while queue:
        current, chain = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        for call in calls_inside(funcs[current]):
            step = {
                "function": current,
                "call": call["call"],
                "line": call["line"],
                "context": call["context"],
            }
            if call["call"] == target:
                evidence.append(chain + [step])
            next_name = resolve(call["call"], current, funcs)
            if next_name and next_name not in visited:
                queue.append((next_name, chain + [step]))
            elif call["call"] == "<dynamic>":
                dynamic_calls.append(step)

    return {
        "status": "TARGET_FOUND" if evidence else "HOLD_TARGET_NOT_RESOLVED",
        "entry": entry,
        "target": target,
        "paths": evidence[:10],
        "path_count": len(evidence),
        "functions_visited": len(visited),
        "dynamic_call_count": len(dynamic_calls),
        "analysis_limitations": [
            "No runtime activation",
            "Method aliasing and inherited dispatch unresolved",
            "Guards identified but not semantically proven",
            "No cross-module execution safety certification",
        ],
    }

def audit(root):
    path = root / SOURCE
    result = {
        "build": "MTR-177",
        "status": "HOLD",
        "source": str(SOURCE),
        "target_canary_sol": "0.010",
        "signing_performed": False,
        "broadcast_performed": False,
        "websocket_connected": False,
        "route_captured": False,
        "canary_sent": False,
    }
    if not path.is_file():
        result["hold_reason"] = "RUNTIME_SOURCE_MISSING"
        return result

    data = path.read_bytes()
    result["source_sha256"] = hashlib.sha256(data).hexdigest()
    try:
        source = data.decode("utf-8-sig")
        result["traces"] = {
            entry: trace(source, entry, target)
            for entry, target in TARGETS.items()
        }
        result["hold_reason"] = "EXECUTION_ISOLATION_NOT_CERTIFIED"
    except (SyntaxError, UnicodeError) as exc:
        result["hold_reason"] = "SOURCE_PARSE_FAILED"
        result["error_type"] = type(exc).__name__
    return result

class Tests(unittest.TestCase):
    def test_direct_target(self):
        src = "def canonical_price():\n    q87.c.signed_tx()\n"
        result = trace(src, "canonical_price", "q87.c.signed_tx")
        self.assertEqual(result["status"], "TARGET_FOUND")
        self.assertEqual(result["paths"][0][-1]["line"], 2)

    def test_indirect_local_target(self):
        src = (
            "def canonical_price():\n    helper()\n"
            "def helper():\n    q87.c.signed_tx()\n"
        )
        result = trace(src, "canonical_price", "q87.c.signed_tx")
        self.assertEqual(len(result["paths"][0]), 2)

    def test_control_flow_context(self):
        src = (
            "def canonical_price():\n"
            "    if enabled:\n"
            "        q87.c.signed_tx()\n"
        )
        result = trace(src, "canonical_price", "q87.c.signed_tx")
        self.assertEqual(
            result["paths"][0][-1]["context"][0]["kind"], "IF"
        )

    def test_missing_target_holds(self):
        result = trace("def canonical_price():\n    pass\n",
                       "canonical_price", "q87.c.signed_tx")
        self.assertEqual(result["status"], "HOLD_TARGET_NOT_RESOLVED")

    def test_missing_source_holds(self):
        result = audit(Path("__missing_mtr177__"))
        self.assertEqual(result["status"], "HOLD")
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
        result = audit(root)
        output = root / "MTR_177_EXACT_CALL_CHAIN.json"
        temp = output.with_suffix(".json.tmp")
        temp.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temp.replace(output)
        for entry, record in result.get("traces", {}).items():
            print("[ENTRY]", entry)
            print("[STATUS]", record["status"])
            print("[PATH_COUNT]", record.get("path_count", 0))
            print("[DYNAMIC_CALLS]", record.get("dynamic_call_count", 0))
            for path in record.get("paths", []):
                for step in path:
                    print("[CHAIN]", step["function"],
                          "line=", step["line"],
                          "call=", step["call"])
                    for guard in step["context"]:
                        print("[CONTEXT]", guard["kind"],
                              "line=", guard["line"])
        print("[MTR177]", result["status"])
        print("[HOLD]", result["hold_reason"])
        print("[REPORT]", output)
        print("[SIGNING] FALSE")
        print("[BROADCAST] FALSE")
        print("[LIVE_CAPTURE] FALSE")
        return 0

    dest = root / PKG / (NAME + ".py")
    if not dest.parent.is_dir():
        print("[FAIL] Canonical package directory missing")
        return 1
    src = Path(__file__).resolve()
    if src != dest.resolve():
        shutil.copyfile(src, dest)
    print("[PASS] MTR-177 installed:", dest)
    print("[SCOPE] Exact source call-chain tracing only")
    return 0

if __name__ == "__main__":
    sys.exit(main())
