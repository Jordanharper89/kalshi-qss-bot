
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "runtime_state/oracle/oracle_live_execution/mtr_141_live_lane_integration_contract.json"

SOURCES = {
    "lane": "qseries_v2/oracle_execution/oracle_020_latest_state_exact_pricing_worker.py",
    "warm": "qseries_v2/oracle_execution/oracle_025_single_hydration_exact_live_reuse.py",
    "driver": "mtr_137_continuous_live_divergence_lane.py",
    "replenishment": "mtr_114_controlled_replenishment_warm_cutover.py",
    "admission": "qseries_v2/oracle_execution/solana_atomic_executor/mtr_139_ws_warm_admission_gate.py"
}
KEYS = ("LatestStateLane", "_pair_snapshot", "_warm",
        "install_hot_math_and_prewarm", "subscribe",
        "inventory", "hydrate", "admit", "run")

def inspect(path):
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    lines = source.splitlines()
    definitions = []
    references = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            definitions.append({
                "name": node.name,
                "line": node.lineno,
                "signature": lines[node.lineno - 1].strip()[:240]
            })
        if isinstance(node, ast.Call):
            fn = ast.unparse(node.func)
            if any(k.lower() in fn.lower() for k in KEYS):
                references.append({"line": node.lineno, "call": fn[:120]})
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            imports.append({
                "module": node.module,
                "names": [x.name for x in node.names]
            })
    return {
        "definitions": definitions,
        "calls": references[:100],
        "imports": imports[:100]
    }

def run():
    report = {
        "mtr": "MTR-141",
        "scope": "TARGETED_SOURCE_CONTRACT",
        "files": {},
        "missing": [],
        "scanner_modified": False,
        "private_key_used": False,
        "signing": False,
        "broadcast": False,
        "cutover_connected": False
    }
    for label, rel in SOURCES.items():
        path = ROOT / rel
        if not path.is_file():
            report["missing"].append(rel)
            continue
        try:
            report["files"][label] = {
                "path": rel,
                **inspect(path)
            }
        except (SyntaxError, UnicodeError, OSError) as exc:
            report["missing"].append(rel + ": " + type(exc).__name__)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")

    for label, data in report["files"].items():
        print("[MTR141_SOURCE]", label, data["path"])
        for item in data["definitions"]:
            if (label in ("lane", "admission") or
                any(k.lower() in item["name"].lower() for k in KEYS)):
                print("[MTR141_DEF]", label, item["line"], item["signature"])
        for item in data["calls"][:12]:
            print("[MTR141_CALL]", label, item["line"], item["call"])

    print("[MTR141_MISSING]", report["missing"])
    print("[MTR141_CONTRACT_READY]", not report["missing"])
    print("[CUTOVER_CONNECTED] FALSE")
    print("[PRIVATE_KEY] NOT_USED")
    print("[SIGNING] FALSE")
    print("[BROADCAST] FALSE")
    print("[REPORT]", OUT)
    if report["missing"]:
        raise SystemExit("[HOLD] Missing required source")
    return report

if __name__ == "__main__":
    run()
