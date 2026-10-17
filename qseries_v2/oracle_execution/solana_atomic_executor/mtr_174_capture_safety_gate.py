
from pathlib import Path
import argparse
import ast
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timezone

NAME = "mtr_174_capture_safety_gate"
PACKAGE = Path("qseries_v2/oracle_execution/solana_atomic_executor")
TARGET_SOL = "0.010"

REQUIRED = {
    "runtime": ["serve_canonical", "canonical_price"],
    "mry_005_runtime_activation": ["serve_rotating"],
}

INSPECT = {
    "runtime": "runtime.py",
    "mry_005_runtime_activation": "mry_005_runtime_activation.py",
    "mtr_169": "mtr_169_canonical_latest_state_lane_capture.py",
}

DANGEROUS = (
    "send_transaction",
    "send_raw_transaction",
    "sendTransaction",
    "sendRawTransaction",
    "sign_transaction",
    "sign_message",
    "signTransaction",
    "send_and_confirm",
    "execute_canary",
    "broadcast_transaction",
)

def inventory(source):
    tree = ast.parse(source)
    functions = set()
    calls = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.add(node.name)
        elif isinstance(node, ast.Call):
            target = node.func
            if isinstance(target, ast.Name):
                calls.add(target.id)
            elif isinstance(target, ast.Attribute):
                calls.add(target.attr)
    return functions, calls

def audit(root):
    directory = root / PACKAGE
    evidence = {}
    blockers = []
    for label, filename in INSPECT.items():
        path = directory / filename
        if not path.is_file():
            evidence[label] = {"present": False}
            blockers.append("MISSING_SOURCE_" + label.upper())
            continue
        data = path.read_bytes()
        record = {
            "present": True,
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
        }
        try:
            functions, calls = inventory(data.decode("utf-8-sig"))
            required = REQUIRED.get(label, [])
            missing = sorted(set(required) - functions)
            hazards = sorted(set(calls).intersection(DANGEROUS))
            record["required_symbols_present"] = not missing
            record["missing_symbols"] = missing
            record["direct_sensitive_call_names"] = hazards
            if missing:
                blockers.append("MISSING_SYMBOLS_" + label.upper())
            if hazards:
                blockers.append("SENSITIVE_CALL_SURFACE_" + label.upper())
        except (SyntaxError, UnicodeError) as exc:
            record["parse_ok"] = False
            record["error_type"] = type(exc).__name__
            blockers.append("UNPARSABLE_SOURCE_" + label.upper())
        evidence[label] = record

    # Static source inspection cannot establish dynamic call safety.
    blockers.extend([
        "INDIRECT_EXECUTION_PATH_NOT_CERTIFIED",
        "CAPTURE_ONLY_PROCESS_ISOLATION_NOT_CERTIFIED",
        "NO_PHYSICAL_WEBSOCKET_CAPTURE_IN_THIS_BUILD",
        "NO_SIGNED_ATOMIC_SIMULATION_PROOF",
    ])
    return {
        "build": "MTR-174",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "status": "HOLD",
        "mode": "STATIC_PHYSICAL_BOUNDARY_AUDIT",
        "target_input_sol": TARGET_SOL,
        "read_only": True,
        "signing_performed": False,
        "broadcast_performed": False,
        "private_key_access_performed": False,
        "websocket_connected": False,
        "real_route_artifact_produced": False,
        "canary_sent": False,
        "realized_net_profit_verified": False,
        "mtr_172_certified_pairs": 4,
        "mtr_172_certified_addresses": 179,
        "previous_pair_target": 28,
        "previous_address_target": 318,
        "source_evidence": evidence,
        "hold_reasons": blockers,
    }

def save_report(root, report):
    output = root / "MTR_174_CAPTURE_SAFETY_GATE.json"
    payload = json.dumps(report, indent=2, sort_keys=True)
    temporary = output.with_suffix(".json.tmp")
    temporary.write_text(payload + "\n", encoding="utf-8")
    temporary.replace(output)
    return output

class Tests(unittest.TestCase):
    def test_symbol_discovery(self):
        functions, calls = inventory(
            "async def serve_canonical():\n"
            "    await harmless()\n"
        )
        self.assertIn("serve_canonical", functions)
        self.assertIn("harmless", calls)

    def test_sensitive_call_discovery(self):
        _, calls = inventory(
            "def f():\n"
            "    client.send_raw_transaction(b'data')\n"
        )
        self.assertIn("send_raw_transaction", calls)

    def test_missing_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            report = audit(Path(directory))
            self.assertEqual(report["status"], "HOLD")
            self.assertFalse(report["canary_sent"])
            self.assertFalse(report["websocket_connected"])
            self.assertIn(
                "MISSING_SOURCE_RUNTIME",
                report["hold_reasons"]
            )

    def test_report_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = audit(root)
            output = save_report(root, report)
            loaded = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(loaded["target_input_sol"], "0.010")
            self.assertFalse(loaded["realized_net_profit_verified"])

    def test_no_executable_capture_claim(self):
        report = audit(Path("__mtr174_missing_root__"))
        self.assertFalse(report["real_route_artifact_produced"])
        self.assertIn(
            "CAPTURE_ONLY_PROCESS_ISOLATION_NOT_CERTIFIED",
            report["hold_reasons"]
        )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--audit", action="store_true")
    args = parser.parse_args()

    if args.test:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        return 0 if result.wasSuccessful() else 1

    root = Path.cwd()
    if args.live or args.audit:
        report = audit(root)
        output = save_report(root, report)
        print("[MTR-174] " + report["status"])
        print("[MODE] STATIC_SOURCE_AUDIT_ONLY")
        print("[REPORT]", output)
        for reason in report["hold_reasons"]:
            print("[HOLD]", reason)
        print("[SIGNING] FALSE")
        print("[BROADCAST] FALSE")
        print("[CANARY_SENT] FALSE")
        print("[REAL_ROUTE_CAPTURE] FALSE")
        return 2 if args.live else 0

    destination = root / PACKAGE / (NAME + ".py")
    if not (root / PACKAGE).is_dir():
        print("[FAIL] Canonical package directory missing")
        return 1

    source = Path(__file__).resolve()
    if source != destination.resolve():
        shutil.copyfile(source, destination)
    print("[PASS] MTR-174 installed:", destination)
    print("[SCOPE] Capture isolation audit; execution disabled")
    return 0

if __name__ == "__main__":
    sys.exit(main())
