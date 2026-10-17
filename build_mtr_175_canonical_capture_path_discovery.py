
from pathlib import Path
import argparse
import ast
import hashlib
import json
import shutil
import sys
import unittest
from datetime import datetime, timezone

NAME = "mtr_175_canonical_capture_path_discovery"
PKG = Path("qseries_v2/oracle_execution/solana_atomic_executor")

ENTRY = {
    "runtime.py": ("serve_canonical", "canonical_price"),
    "mry_005_runtime_activation.py": ("serve_rotating",),
}

SENSITIVE = {
    "sign", "sign_transaction", "sign_message",
    "send_transaction", "send_raw_transaction",
    "sendTransaction", "sendRawTransaction",
    "execute_canary", "send_and_confirm",
    "broadcast_transaction", "get_private_key",
    "load_keypair", "Keypair", "from_secret_key",
}

def call_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return call_name(node.value) + "." + node.attr
    return "<dynamic>"

def source_map(path):
    data = path.read_bytes()
    tree = ast.parse(data.decode("utf-8-sig"))
    functions = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            calls = []
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    calls.append(call_name(child.func))
            functions[node.name] = sorted(set(calls))
    return {
        "sha256": hashlib.sha256(data).hexdigest(),
        "functions": functions,
    }

def reachable(functions, entry):
    visited = set()
    queue = [entry]
    external = set()
    while queue:
        name = queue.pop()
        if name in visited:
            continue
        visited.add(name)
        for call in functions.get(name, []):
            leaf = call.rsplit(".", 1)[-1]
            if call in functions and call not in visited:
                queue.append(call)
            elif leaf not in functions:
                external.add(call)
    return sorted(visited), sorted(external)

def inspect(root):
    base = root / PKG
    sources = {}
    hold = []
    for filename, required in ENTRY.items():
        path = base / filename
        if not path.is_file():
            hold.append("MISSING_" + filename.upper())
            continue
        try:
            record = source_map(path)
        except (SyntaxError, UnicodeError) as exc:
            hold.append("UNPARSEABLE_" + filename.upper())
            sources[filename] = {"error": type(exc).__name__}
            continue
        for entry in required:
            if entry not in record["functions"]:
                hold.append("MISSING_ENTRY_" + entry.upper())
                continue
            local, external = reachable(record["functions"], entry)
            sensitive = [
                call for call in external
                if call.rsplit(".", 1)[-1] in SENSITIVE
            ]
            record[entry + "_reachable_local"] = local
            record[entry + "_external_calls"] = external
            record[entry + "_sensitive_calls"] = sensitive
            if sensitive:
                hold.append("SENSITIVE_SURFACE_" + entry.upper())
            if external:
                hold.append("UNRESOLVED_CALLS_" + entry.upper())
        sources[filename] = record

    candidates = []
    if base.is_dir():
        for path in sorted(base.rglob("*mtr*169*.py")):
            if path.is_file():
                try:
                    rec = source_map(path)
                    candidates.append({
                        "path": str(path.relative_to(root)),
                        "sha256": rec["sha256"],
                        "functions": sorted(rec["functions"]),
                    })
                except (SyntaxError, UnicodeError) as exc:
                    candidates.append({
                        "path": str(path.relative_to(root)),
                        "error": type(exc).__name__,
                    })
    if not candidates:
        hold.append("MTR169_SOURCE_NOT_DISCOVERED")

    hold.extend([
        "TRANSITIVE_EXTERNAL_CALL_GRAPH_UNCERTIFIED",
        "PROCESS_ISOLATION_UNCERTIFIED",
        "NO_LIVE_WEBSOCKET_CAPTURE",
        "NO_SIGNED_ATOMIC_SIMULATION",
    ])

    return {
        "build": "MTR-175",
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "status": "HOLD",
        "mode": "READ_ONLY_SOURCE_DISCOVERY",
        "target_input_sol": "0.010",
        "sources": sources,
        "mtr169_candidates": candidates,
        "hold_reasons": sorted(set(hold)),
        "runtime_started": False,
        "websocket_started": False,
        "private_key_access": False,
        "signing": False,
        "broadcast": False,
        "canary_sent": False,
        "realized_profit_verified": False,
    }

def test():
    class Tests(unittest.TestCase):
        def test_names(self):
            self.assertEqual(
                call_name(ast.parse("rt.serve_canonical()")
                          .body[0].value.func),
                "rt.serve_canonical",
            )

        def test_reachability(self):
            local, external = reachable(
                {"start": ["helper"], "helper": ["net.send"]},
                "start",
            )
            self.assertEqual(local, ["helper", "start"])
            self.assertEqual(external, ["net.send"])

        def test_sensitive_detection(self):
            self.assertIn("send_raw_transaction", SENSITIVE)

        def test_real_missing_root_holds(self):
            result = inspect(Path("__missing_mtr175_root__"))
            self.assertEqual(result["status"], "HOLD")
            self.assertFalse(result["canary_sent"])

        def test_no_runtime_claim(self):
            result = inspect(Path("__missing_mtr175_root__"))
            self.assertFalse(result["runtime_started"])
            self.assertFalse(result["signing"])
            self.assertFalse(result["broadcast"])

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
    )
    return 0 if result.wasSuccessful() else 1

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--test", action="store_true")
    p.add_argument("--audit", action="store_true")
    p.add_argument("--live", action="store_true")
    args = p.parse_args()

    if args.test:
        return test()

    root = Path.cwd()
    if args.audit or args.live:
        result = inspect(root)
        output = root / "MTR_175_CAPTURE_PATH_DISCOVERY.json"
        tmp = output.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        tmp.replace(output)
        print("[MTR-175]", result["status"])
        print("[MTR169_CANDIDATES]", len(result["mtr169_candidates"]))
        for item in result["mtr169_candidates"]:
            print("[MTR169_PATH]", item["path"])
        for name, record in result["sources"].items():
            print("[SOURCE]", name)
            for key, value in record.items():
                if key.endswith("_sensitive_calls"):
                    print("[SENSITIVE]", key, value)
                if key.endswith("_external_calls"):
                    print("[EXTERNAL_CALL_COUNT]", key, len(value))
        for reason in result["hold_reasons"]:
            print("[HOLD]", reason)
        print("[REPORT]", output)
        print("[SIGNING] FALSE")
        print("[BROADCAST] FALSE")
        print("[LIVE_CAPTURE] FALSE")
        return 2 if args.live else 0

    dest = root / PKG / (NAME + ".py")
    if not dest.parent.is_dir():
        print("[FAIL] Canonical executor directory missing")
        return 1
    src = Path(__file__).resolve()
    if src != dest.resolve():
        shutil.copyfile(src, dest)
    print("[PASS] MTR-175 installed:", dest)
    print("[SCOPE] Source discovery only; no runtime activation")
    return 0

if __name__ == "__main__":
    sys.exit(main())
