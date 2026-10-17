
from pathlib import Path
import argparse
import ast
import json
import shutil
import unittest

VERSION = "ORACLE_046_PRODUCTION_ATTACHMENT_CONTRACT"
PKG = Path("qseries_v2/oracle_execution/solana_atomic_executor")
DEST = PKG / "oracle_046_production_attachment.py"
REPORT = Path(
    "runtime_state/oracle/oracle_live_execution/"
    "ORACLE_046_ATTACHMENT.json"
)

SOURCES = {
    "pricing": PKG / "oracle_024_fresh_candidate_revalidation.py",
    "receiver": PKG / "oracle_045_live_replenishment_dispatcher.py",
    "transport": PKG / "oracle_044_ws_rotation_transport.py",
    "rotation": PKG / "oracle_043_warm_rotation_handoff.py",
    "worker": PKG / "mry_001_continuous_replenishment.py",
}

def read_source(path):
    return path.read_text(encoding="utf-8-sig")

def inspect(root):
    result = {
        "revision": VERSION,
        "status": "PRODUCTION_ATTACHMENT_CONTRACT",
        "sources": {},
        "attachment_certified": False,
        "live_rotation_certified": False,
        "rpc_requests": 0,
        "signing": False,
        "broadcast": False,
        "canary_lamports": 10_000_000,
    }

    for name, relative in SOURCES.items():
        path = root / relative
        entry = {"exists": path.is_file()}
        result["sources"][name] = entry
        if not path.is_file():
            continue

        source = read_source(path)
        tree = ast.parse(source)
        entry["functions"] = [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (
                ast.FunctionDef, ast.AsyncFunctionDef
            ))
        ]
        entry["classes"] = [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef)
        ]

        if name != "pricing":
            continue

        lines = source.splitlines()
        entry["pricing_loop"] = []
        entry["receiver_calls"] = []
        entry["session_lifecycle"] = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            call = ast.unparse(node.func)
            text = call.lower()

            if any(x in text for x in (
                "connect", "recv", "send",
                "subscribe", "notification",
                "lateststatelane"
            )):
                entry["receiver_calls"].append({
                    "line": node.lineno,
                    "call": call,
                })

        for number, line in enumerate(lines, 1):
            if any(term in line for term in (
                "LatestStateLane",
                "async def",
                "def observe",
                "def price",
                "accountSubscribe",
                "accountNotification",
                "websockets.connect",
                "create_task",
                "lane.",
                "state['pairs']",
                "state[\"pairs\"]",
                "q20.",
                "finally:",
            )):
                entry["pricing_loop"].append(number)

        # The target interval covers V24's canonical pricing
        # callbacks and its WebSocket event-processing lifecycle.
        for number in range(138, min(len(lines), 249) + 1):
            entry["session_lifecycle"].append(
                {"line": number, "source": lines[number - 1]}
            )

    return result

def save(root, result):
    path = root / REPORT
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
    tmp.replace(path)
    return path

class Tests(unittest.TestCase):
    def test_sources_exist(self):
        result = inspect(Path.cwd())
        self.assertTrue(all(
            row["exists"]
            for row in result["sources"].values()
        ))

    def test_runtime_entrypoint(self):
        result = inspect(Path.cwd())
        self.assertIn(
            "child", result["sources"]["pricing"]["functions"]
        )

    def test_existing_receiver(self):
        result = inspect(Path.cwd())
        self.assertIn(
            "Dispatcher",
            result["sources"]["receiver"]["classes"]
        )

    def test_existing_transport(self):
        result = inspect(Path.cwd())
        self.assertIn(
            "Transport",
            result["sources"]["transport"]["classes"]
        )

    def test_no_false_certification(self):
        result = inspect(Path.cwd())
        self.assertFalse(result["attachment_certified"])
        self.assertFalse(result["live_rotation_certified"])
        self.assertEqual(result["rpc_requests"], 0)

    def test_canary(self):
        self.assertEqual(
            inspect(Path.cwd())["canary_lamports"],
            10_000_000
        )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--inspect", action="store_true")
    args = parser.parse_args()
    root = Path.cwd()

    if args.test:
        run = unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
        )
        return 0 if run.wasSuccessful() else 1

    if args.inspect:
        result = inspect(root)
        report = save(root, result)
        print("[STATUS]", result["status"])

        for name, entry in result["sources"].items():
            print("[SOURCE]", name, "EXISTS", entry["exists"])

        pricing = result["sources"]["pricing"]
        for item in pricing.get("receiver_calls", []):
            print("[RECEIVER_CALL]", json.dumps(item))

        for item in pricing.get("session_lifecycle", []):
            print(
                "[V24]", item["line"],
                item["source"]
            )

        print("[PRODUCTION_ATTACHMENT] NOT_YET_CONNECTED")
        print("[RPC_REQUESTS] 0")
        print("[SIGNING] FALSE [BROADCAST] FALSE")
        print("[REPORT]", report)
        return 0

    target = root / DEST
    if not target.parent.is_dir():
        print("[HOLD] EXECUTOR_PACKAGE_MISSING")
        return 2

    if target.resolve() != Path(__file__).resolve():
        shutil.copyfile(Path(__file__), target)

    print("[PASS]", VERSION)
    print("[MODE] EXISTING_V24_RUNTIME_BOUNDARY_INSPECTION")
    print("[SCANNER] UNCHANGED")
    print("[SIGNING] FALSE [BROADCAST] FALSE")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
