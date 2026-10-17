
"""MTR-140 full replacement: repository-wide physical contract discovery."""
from pathlib import Path
import ast
import json

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "runtime_state/oracle/oracle_live_execution/mtr_140_canonical_cutover_contract.json"

MARKERS = {
    "mtr137": ("MTR137_SUMMARY", "MTR-137", "mtr_137"),
    "oracle020": ("ORACLE020_EXACT_LATEST", "ORACLE020_SCAN_REPLACED", "oracle_020"),
    "oracle025": ("ORACLE025_TOKEN_WARM", "ORACLE025", "oracle_025"),
}
HOOKS = ("websocket", "subscribe", "inventory", "route", "pair",
         "snapshot", "hydrate", "warm", "pricing", "worker",
         "scan", "registry", "latest", "coalesc")

def eligible(path):
    parts = {x.lower() for x in path.relative_to(ROOT).parts}
    if parts & {".git", ".venv", "venv", "__pycache__",
                "node_modules", "runtime_state", "site-packages"}:
        return False
    name = path.name.lower()
    return not any(x in name for x in
                   ("mtr_138", "mtr_139", "mtr_140"))

def inspect_source(path):
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source)
    except (OSError, SyntaxError):
        return None

    names = []
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if any(x in node.name.lower() for x in HOOKS):
                names.append({"name": node.name, "line": node.lineno,
                              "kind": type(node).__name__})
        elif isinstance(node, ast.ImportFrom):
            if node.module and any(x in node.module.lower() for x in HOOKS):
                imports.append(node.module)

    matched = {
        key: [x for x in values if x.lower() in source.lower()]
        for key, values in MARKERS.items()
    }
    matched = {k: v for k, v in matched.items() if v}
    if not matched and not names:
        return None

    return {"path": str(path.relative_to(ROOT)),
            "markers": matched,
            "hooks": names[:100],
            "imports": imports[:30]}

def contract():
    files = []
    for path in ROOT.rglob("*.py"):
        if not eligible(path):
            continue
        item = inspect_source(path)
        if item:
            files.append(item)

    targets = {}
    for key in MARKERS:
        rows = [f for f in files if key in f["markers"]]
        rows.sort(key=lambda x: (
            -len(x["markers"][key]),
            -len(x["hooks"]), x["path"]
        ))
        targets[key] = rows

    result = {
        "mtr": "MTR-140",
        "mode": "READ_ONLY_REPOSITORY_WIDE_CONTRACT_DISCOVERY",
        "targets": targets,
        "targets_present": {k: bool(v) for k, v in targets.items()},
        "source_candidates": len(files),
        "size_ladder": [0.010, 0.015, 0.020, 0.025, 0.030],
        "scanner_mutated": False,
        "hot_rest_enabled": False,
        "private_key_used": False,
        "signing": False,
        "broadcast": False,
        "cutover_complete": False
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result

def main():
    r = contract()
    print("[MTR140_SOURCE_CANDIDATES]", r["source_candidates"])
    for key, rows in r["targets"].items():
        print("[MTR140_TARGET]", key, "matches=", len(rows))
        for row in rows[:8]:
            print("[SOURCE]", row["path"])
            print("[MARKERS]", ",".join(row["markers"][key]))
            print("[HOOKS]", ",".join(x["name"] for x in row["hooks"][:20]))
    ready = all(r["targets_present"].values())
    print("[MTR140_DISCOVERY_READY]", ready)
    print("[MTR140_CUTOVER] NOT_CONNECTED")
    print("[SCANNER] FROZEN")
    print("[PRIVATE_KEY] NOT_USED")
    print("[SIGNING] FALSE")
    print("[BROADCAST] FALSE")
    print("[REPORT]", OUT)
    if not ready:
        raise SystemExit("[HOLD] Physical source marker missing")

if __name__ == "__main__":
    main()
