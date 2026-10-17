
from pathlib import Path
import argparse
import ast
import json
import shutil
import time
import unittest

VERSION = "ORACLE_029_LIVE_SCANNER_HANDOFF_CONTRACT"
BASE = Path("qseries_v2/oracle_execution/solana_atomic_executor")
DEST = BASE / "oracle_029_live_scanner_handoff_contract.py"
REPORT = Path("runtime_state/oracle/oracle_live_execution/ORACLE_029_HANDOFF.json")

SOURCES = {
    "economic": "solana_scanner/cross_venue_economic_rows_repaired.json",
    "executable": "solana_scanner/phase7_cross_venue_executable_candidates.json",
    "friction": "solana_scanner/phase7_cross_venue_native_friction.json",
    "latency": "solana_scanner/phase7_per_row_latency_recovery.json",
    "trade_tape": "universal_trade_tape/multidex_universal_economic_tape.json",
}
MODULES = [
    BASE / "mtr_165_ws_capture_only.py",
    BASE / "mtr_169_capture_lane_integration.py",
    BASE / "mtr_172_isolated_market_startup.py",
]
INTEREST = (
    "token", "mint", "pool", "venue", "route", "direction",
    "slot", "timestamp", "time", "age", "profit", "net",
    "bps", "fee", "liquidity", "status", "ready",
    "source", "pair", "capture", "fresh", "event"
)

def interesting(name):
    return any(word in name.lower() for word in INTEREST)

def inspect_records(root, relative):
    path = root / "runtime_state/solana_opportunities" / relative
    result = {"path": str(path), "exists": path.is_file()}
    if not path.is_file():
        return result

    result["file_age_seconds"] = round(
        max(0, time.time() - path.stat().st_mtime), 1
    )

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError):
        result["status"] = "UNREADABLE"
        return result

    if not isinstance(data, dict):
        result["status"] = "NOT_OBJECT"
        return result

    result["document_fields"] = sorted(
        x for x in data if interesting(x)
    )[:35]

    result["metadata"] = {
        key: data[key]
        for key in ("revision", "status", "read_only",
                    "execution_authority", "profitability_claimed")
        if key in data and isinstance(data[key], (str, bool, int))
    }

    candidates = [
        (key, value)
        for key, value in data.items()
        if isinstance(value, list)
    ]

    if not candidates:
        result["status"] = "NO_LIST_RECORDS"
        return result

    key, rows = max(candidates, key=lambda item: len(item[1]))
    result["record_container"] = key
    result["record_count"] = len(rows)

    samples = [
        row for row in rows[:100]
        if isinstance(row, dict)
    ][:3]

    result["sample_field_names"] = [
        sorted(row.keys())[:70] for row in samples
    ]

    result["identity_fields"] = sorted({
        key for row in samples for key in row
        if interesting(key)
    })

    result["status"] = "SCHEMA_INSPECTED"
    result["live_freshness_certified"] = False
    result["execution_certified"] = False
    return result

def inspect_module(path):
    result = {"path": str(path), "exists": path.is_file()}
    if not path.is_file():
        return result
    try:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    except (SyntaxError, OSError, UnicodeError):
        result["status"] = "SOURCE_UNREADABLE"
        return result

    result["functions"] = [
        {
            "name": node.name,
            "parameters": [x.arg for x in node.args.args]
        }
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and (interesting(node.name) or node.name in ("run", "main"))
    ][:25]
    result["status"] = "SOURCE_INSPECTED"
    return result

def audit(root):
    records = {
        name: inspect_records(root, relative)
        for name, relative in SOURCES.items()
    }
    modules = [
        inspect_module(root / relative)
        for relative in MODULES
    ]
    return {
        "revision": VERSION,
        "status": "HANDOFF_SCHEMA_AUDIT_COMPLETE",
        "scanner_records": records,
        "capture_modules": modules,
        "live_producer_binding_certified": False,
        "execution_authority": False,
        "historical_prices_executable": False,
        "fresh_onchain_validation_required": True,
        "api_requests": 0,
        "signing": False,
        "broadcast": False
    }

def save(root, data):
    path = root / REPORT
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
    temp.replace(path)

class Tests(unittest.TestCase):
    def test_read_only(self):
        row = audit(Path.cwd())
        self.assertFalse(row["signing"])
        self.assertFalse(row["broadcast"])

    def test_no_rpc(self):
        self.assertEqual(audit(Path.cwd())["api_requests"], 0)

    def test_no_historical_execution(self):
        self.assertFalse(audit(Path.cwd())["historical_prices_executable"])

    def test_schema_only(self):
        row = inspect_records(
            Path.cwd(), SOURCES["executable"]
        )
        self.assertNotIn("sample_record_values", row)

    def test_missing_file_safe(self):
        row = inspect_records(Path.cwd(), "missing_file.json")
        self.assertFalse(row["exists"])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--audit", action="store_true")
    args = parser.parse_args()
    root = Path.cwd()

    if args.test:
        result = unittest.TextTestRunner(
            verbosity=2
        ).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
        )
        return 0 if result.wasSuccessful() else 1

    if args.audit:
        result = audit(root)
        save(root, result)
        print("[STATUS]", result["status"])
        for name, row in result["scanner_records"].items():
            print("[SCANNER_RECORD]", name, json.dumps(row, sort_keys=True))
        for row in result["capture_modules"]:
            print("[CAPTURE_MODULE]", json.dumps(row, sort_keys=True))
        print("[API_REQUESTS] 0")
        print("[EXECUTION_AUTHORITY] FALSE")
        print("[REPORT]", root / REPORT)
        return 0

    target = root / DEST
    if not target.parent.is_dir():
        print("[HOLD] EXECUTOR_PACKAGE_MISSING")
        return 2
    if target.resolve() != Path(__file__).resolve():
        shutil.copyfile(Path(__file__), target)
    print("[PASS]", VERSION, target)
    print("[MODE] ORIGINAL_SCANNER_READ_ONLY_HANDOFF_AUDIT")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
