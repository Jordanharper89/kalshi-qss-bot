
from pathlib import Path
import argparse
import ast
import hashlib
import json
import shutil
import sys
import unittest
from datetime import datetime, timezone

NAME = "mtr_176_execution_boundary_resolution"
PKG = Path("qseries_v2/oracle_execution/solana_atomic_executor")
FILES = {
    "runtime.py": ["serve_canonical", "canonical_price"],
    "mry_005_runtime_activation.py": ["serve_rotating"],
    "mtr_169_capture_lane_integration.py": [],
}
RISK = (
    "sign", "send", "broadcast", "submit_transaction",
    "execute", "keypair", "secret", "private_key",
    "wallet", "canary", "transaction", "subprocess",
    "popen", "exec", "eval", "system", "create_task",
    "run_until_complete",
)
TARGET = "0.010"

def dotted(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return dotted(node.value) + "." + node.attr
    if isinstance(node, ast.Subscript):
        return dotted(node.value) + "[indexed]"
    return "<dynamic>"

def functions_of(tree):
    result = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result[node.name] = node
    return result

def imports_of(tree):
    result = {}
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                result[alias.asname or alias.name.split(".")[0]] = alias.name
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                result[alias.asname or alias.name] = (
                    "." * node.level + module + "." + alias.name
                )
    return result

def calls_of(node):
    return sorted({
        (dotted(n.func), n.lineno)
        for n in ast.walk(node)
        if isinstance(n, ast.Call)
    }, key=lambda v: (v[1], v[0]))

def hazards(name):
    value = name.lower()
    return sorted({word for word in RISK if word in value})

def analyze_source(data, entries):
    tree = ast.parse(data.decode("utf-8-sig"))
    funcs = functions_of(tree)
    aliases = imports_of(tree)
    output = {}
    for entry in entries:
        if entry not in funcs:
            output[entry] = {"found": False}
            continue
        visited = set()
        pending = [entry]
        unresolved = []
        while pending:
            current = pending.pop()
            if current in visited:
                continue
            visited.add(current)
            for name, line in calls_of(funcs[current]):
                leaf = name.rsplit(".", 1)[-1]
                if name in funcs and name not in visited:
                    pending.append(name)
                elif leaf in funcs and (
                    name.startswith("self.") or
                    name.startswith("cls.")
                ):
                    pending.append(leaf)
                else:
                    head = name.split(".")[0]
                    unresolved.append({
                        "caller": current,
                        "line": line,
                        "call": name,
                        "import_target": aliases.get(head),
                        "risk_tokens": hazards(name),
                    })
        output[entry] = {
            "found": True,
            "local_reachable": sorted(visited),
            "unresolved_calls": sorted(
                unresolved, key=lambda item: (
                    item["caller"], item["line"], item["call"]
                )
            ),
        }
    return {
        "imports": aliases,
        "function_count": len(funcs),
        "entries": output,
    }

def audit(root):
    directory = root / PKG
    sources = {}
    blockers = []
    for filename, entries in FILES.items():
        path = directory / filename
        if not path.is_file():
            sources[filename] = {"present": False}
            blockers.append("SOURCE_MISSING:" + filename)
            continue
        data = path.read_bytes()
        record = {
            "present": True,
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
        }
        try:
            parsed = analyze_source(data, entries)
            record.update(parsed)
            for entry, detail in parsed["entries"].items():
                if not detail["found"]:
                    blockers.append("ENTRY_MISSING:" + entry)
                else:
                    unresolved = detail["unresolved_calls"]
                    if unresolved:
                        blockers.append(
                            "UNRESOLVED_BOUNDARY:" + entry
                        )
                    if any(item["risk_tokens"] for item in unresolved):
                        blockers.append(
                            "RISK_REVIEW_REQUIRED:" + entry
                        )
        except (SyntaxError, UnicodeError, ValueError) as exc:
            record["parse_error_type"] = type(exc).__name__
            blockers.append("SOURCE_PARSE_FAILURE:" + filename)
        sources[filename] = record
    blockers.extend([
        "DYNAMIC_DISPATCH_NOT_RESOLVED",
        "TRANSITIVE_IMPORTS_NOT_CERTIFIED",
        "CAPTURE_PROCESS_ISOLATION_NOT_PROVEN",
        "LIVE_WEBSOCKET_CAPTURE_NOT_PERFORMED",
        "ATOMIC_SIMULATION_NOT_PERFORMED",
    ])
    return {
        "build": "MTR-176",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "status": "HOLD",
        "scope": "STATIC_EXECUTION_BOUNDARY_RESOLUTION",
        "target_canary_sol": TARGET,
        "sources": sources,
        "hold_reasons": sorted(set(blockers)),
        "runtime_started": False,
        "private_key_access": False,
        "signing": False,
        "broadcast": False,
        "websocket_connected": False,
        "route_captured": False,
        "canary_sent": False,
        "realized_profit_verified": False,
    }

class Tests(unittest.TestCase):
    def test_import_resolution(self):
        data = (
            b"import alpha as a\n"
            b"async def serve_canonical():\n"
            b"    await a.observe()\n"
        )
        result = analyze_source(data, ["serve_canonical"])
        calls = result["entries"]["serve_canonical"]["unresolved_calls"]
        self.assertEqual(calls[0]["import_target"], "alpha")

    def test_sensitive_call_detection(self):
        data = b"def f():\n    client.send_raw_transaction(payload)\n"
        result = analyze_source(data, ["f"])
        calls = result["entries"]["f"]["unresolved_calls"]
        self.assertIn("send", calls[0]["risk_tokens"])

    def test_local_reachability(self):
        data = b"def a():\n    b()\ndef b():\n    observe()\n"
        result = analyze_source(data, ["a"])
        local = result["entries"]["a"]["local_reachable"]
        self.assertEqual(local, ["a", "b"])

    def test_missing_source_hold(self):
        result = audit(Path("__missing_mtr176_root__"))
        self.assertEqual(result["status"], "HOLD")
        self.assertFalse(result["canary_sent"])

    def test_no_execution_claims(self):
        result = audit(Path("__missing_mtr176_root__"))
        for key in (
            "runtime_started", "private_key_access",
            "signing", "broadcast", "websocket_connected",
            "route_captured", "realized_profit_verified"
        ):
            self.assertFalse(result[key])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--audit", action="store_true")
    args = parser.parse_args()

    if args.test:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        return 0 if result.wasSuccessful() else 1

    root = Path.cwd()
    if args.audit:
        result = audit(root)
        path = root / "MTR_176_EXECUTION_BOUNDARY.json"
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        tmp.replace(path)

        print("[MTR176_STATUS]", result["status"])
        for filename, record in result["sources"].items():
            print("[SOURCE]", filename, "present=", record["present"])
            for entry, detail in record.get("entries", {}).items():
                print("[ENTRY]", entry, "found=", detail["found"])
                unresolved = detail.get("unresolved_calls", [])
                print("[UNRESOLVED_COUNT]", len(unresolved))
                for call in unresolved:
                    if call["risk_tokens"]:
                        print(
                            "[RISK_REVIEW]",
                            filename,
                            "line=", call["line"],
                            "call=", call["call"],
                            "tokens=", ",".join(call["risk_tokens"]),
                        )
        for reason in result["hold_reasons"]:
            print("[HOLD]", reason)
        print("[REPORT]", path)
        print("[SIGNING] FALSE")
        print("[BROADCAST] FALSE")
        print("[LIVE_CAPTURE] FALSE")
        return 0

    destination = root / PKG / (NAME + ".py")
    if not destination.parent.is_dir():
        print("[FAIL] Canonical package missing")
        return 1
    source = Path(__file__).resolve()
    if source != destination.resolve():
        shutil.copyfile(source, destination)
    print("[PASS] MTR-176 installed:", destination)
    print("[SCOPE] Static boundary resolution only")
    return 0

if __name__ == "__main__":
    sys.exit(main())
