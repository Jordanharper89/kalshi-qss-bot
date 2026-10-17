
from pathlib import Path
import ast, json

ROOT = Path(__file__).resolve().parents[3]
PKG = ROOT / "qseries_v2" / "oracle_execution" / "solana_atomic_executor"
OUT = ROOT / "runtime_state" / "oracle" / "oracle_live_execution"
TERMS = (
    "mtr_137", "oracle_020", "oracle_025", "websocket", "registry",
    "inventory", "binding", "hydrate", "warm", "subscribe", "latest_state"
)

def symbols(path):
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return []
    rows = []
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            rows.append({"name": n.name, "kind": type(n).__name__, "line": n.lineno})
    return rows

def imports(path):
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return []
    rows = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            rows.extend(x.name for x in n.names)
        elif isinstance(n, ast.ImportFrom):
            rows.append((n.module or "") + ":" + ",".join(x.name for x in n.names))
    return rows

def run():
    files = []
    for p in ROOT.rglob("*.py"):
        low = str(p).lower()
        if any(t in low for t in TERMS):
            files.append(p)

    report = {
        "mtr": "MTR-138",
        "purpose": "WARM_CONTINUOUS_INVENTORY_ADMISSION_SURFACE_AUDIT",
        "scanner_modified": False,
        "rest_hot_path_allowed": False,
        "private_key_used": False,
        "signing": False,
        "broadcast": False,
        "size_policy_sol": [0.010, 0.015, 0.020, 0.025, 0.030],
        "required_lifecycle": [
            "DISCOVERED", "EXACT_BOUND", "HYDRATED_WARM",
            "WS_SUBSCRIBED", "LIVE_STATE_READY", "HOT_ADMITTED"
        ],
        "files": []
    }

    for p in sorted(files):
        rel = str(p.relative_to(ROOT))
        syms = symbols(p)
        imps = imports(p)
        if syms or any(x in rel.lower() for x in ("mtr_137", "oracle_020", "oracle_025")):
            report["files"].append({
                "path": rel,
                "symbols": syms,
                "imports": imps
            })

    names = [
        x["path"].lower()
        for x in report["files"]
    ]
    report["mtr137_found"] = any("mtr_137" in x for x in names)
    report["oracle020_found"] = any("oracle_020" in x for x in names)
    report["oracle025_found"] = any("oracle_025" in x for x in names)
    report["integration_surface_ready"] = (
        report["mtr137_found"] and
        report["oracle020_found"] and
        report["oracle025_found"]
    )

    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / "mtr_138_warm_inventory_admission_surface_audit.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("[MTR138_FILES]", len(report["files"]))
    print("[MTR138_MTR137]", report["mtr137_found"])
    print("[MTR138_ORACLE020]", report["oracle020_found"])
    print("[MTR138_ORACLE025]", report["oracle025_found"])
    print("[MTR138_INTEGRATION_SURFACE_READY]", report["integration_surface_ready"])
    print("[SCANNER_MODIFIED] FALSE")
    print("[REST_HOT_PATH] FALSE")
    print("[PRIVATE_KEY] NOT_USED")
    print("[SIGNING] FALSE")
    print("[BROADCAST] FALSE")
    print("[REPORT]", out)
    print("[MTR-138] COMPLETE")
    return report

if __name__ == "__main__":
    run()
