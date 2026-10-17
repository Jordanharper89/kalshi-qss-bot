"""MTR-143 precise AST-only canonical snapshot compatibility evidence."""
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "runtime_state/oracle/oracle_live_execution/mtr_143_snapshot_compatibility.json"
SOURCES = {
    "lane": "qseries_v2/oracle_execution/oracle_020_latest_state_exact_pricing_worker.py",
    "warm": "qseries_v2/oracle_execution/oracle_025_single_hydration_exact_live_reuse.py",
    "driver": "mtr_137_continuous_live_divergence_lane.py",
    "replenishment": "mtr_114_controlled_replenishment_warm_cutover.py",
    "admission": "qseries_v2/oracle_execution/solana_atomic_executor/mtr_139_ws_warm_admission_gate.py",
    "handoff": "qseries_v2/oracle_execution/solana_atomic_executor/mtr_142_admitted_latest_state_handoff.py",
}
TARGETS = {
    "lane": {"LatestStateLane", "__init__", "submit", "_pair_snapshot", "_warm", "_price", "_loop", "_patched_process_event", "install", "_serve"},
    "warm": {"install_hot_math_and_prewarm"},
    "driver": {"main", "run"},
    "replenishment": {"hydrate_exact", "main", "run"},
    "admission": {"publish", "current", "hot_inventory", "observe_ws"},
    "handoff": {"offer"},
}

def dotted(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return dotted(node.value) + "." + node.attr
    return type(node).__name__

def signature(node):
    if isinstance(node, ast.ClassDef):
        return "class"
    args = node.args
    return {"positional": [a.arg for a in args.posonlyargs + args.args],
            "keyword_only": [a.arg for a in args.kwonlyargs],
            "vararg": args.vararg.arg if args.vararg else None,
            "kwarg": args.kwarg.arg if args.kwarg else None}

def analyze(path, label):
    tree = ast.parse(path.read_text(encoding="utf-8-sig", errors="replace"))
    nodes = []
    for n in ast.walk(tree):
        if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if n.name not in TARGETS[label]:
            continue
        # AST-only metadata: do not print raw source, string literals, keys, or RPC endpoints.
        calls = sorted(set(dotted(x.func) for x in ast.walk(n) if isinstance(x, ast.Call)))
        fields = sorted(set(dotted(x.value) + "." + x.attr for x in ast.walk(n)
                            if isinstance(x, ast.Attribute) and isinstance(x.value, ast.Name)))
        reads = sorted(set(x.value for x in ast.walk(n) if isinstance(x, ast.Constant)
                           and isinstance(x.value, str) and x.value in
                           {"token", "pairs", "pool", "pump", "meteora", "slot", "snap", "price", "dlmm"}))
        nodes.append({"name": n.name, "line": n.lineno, "end_line": n.end_lineno,
                      "signature": signature(n), "calls": calls[:70],
                      "attribute_accesses": fields[:70], "known_dictionary_keys": reads})
    return nodes

def run():
    report = {"mtr": "MTR-143", "sources": {}, "missing": [],
              "production_cutover": False, "scanner_modified": False,
              "private_key_used": False, "signing": False, "broadcast": False}
    for label, relative in SOURCES.items():
        path = ROOT / relative
        if not path.is_file():
            report["missing"].append(relative)
            continue
        try:
            report["sources"][label] = {"path": relative, "nodes": analyze(path, label)}
        except (SyntaxError, OSError, UnicodeError) as exc:
            report["missing"].append(relative + ":" + type(exc).__name__)
    required = {"lane": {"LatestStateLane", "submit", "_pair_snapshot", "_warm", "_price"},
                "admission": {"publish", "current"}, "handoff": {"offer"}}
    for label, names in required.items():
        have = {x["name"] for x in report["sources"].get(label, {}).get("nodes", [])}
        if names - have:
            report["missing"].append(label + ":" + ",".join(sorted(names - have)))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    for label, data in report["sources"].items():
        print("[MTR143_SOURCE]", label, data["path"])
        for node in data["nodes"]:
            print("[MTR143_NODE]", label, node["name"], node["line"], node["signature"])
            print("[MTR143_CALLS]", label, node["name"], ",".join(node["calls"][:30]))
            if label == "lane":
                print("[MTR143_FIELDS]", node["name"], ",".join(node["attribute_accesses"][:30]))
    print("[MTR143_MISSING]", report["missing"])
    print("[MTR143_CONTRACT_READY]", not report["missing"])
    print("[PRODUCTION_CUTOVER] FALSE")
    print("[SCANNER] FROZEN")
    print("[PRIVATE_KEY] NOT_USED")
    print("[SIGNING] FALSE")
    print("[BROADCAST] FALSE")
    print("[REPORT]", OUT)
    if report["missing"]:
        raise SystemExit("[HOLD] Snapshot contract incomplete")
    return report

if __name__ == "__main__":
    run()
