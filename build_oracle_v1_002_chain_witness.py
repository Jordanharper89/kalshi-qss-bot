
"""ORACLE V1-002: read-only startup chain witness."""
from pathlib import Path
import ast
import hashlib
import json
import re
import sys

ROOT = Path.cwd()
BASE = ROOT / "qseries_v2/oracle_execution/solana_atomic_executor"
NAMES = [
    "V1/scanner.py",
    "V1/executor.py",
    "oracle_525_native_inventory_hydration.py",
    "oracle_524_verified_execution_shadow.py",
    "oracle_523_scanner_executor_handoff.py",
    "oracle_504_execution_engine.py",
    "oracle_500_scanner_machine.py",
    "oracle_344_scanner_align.py",
]
BUILDERS = [
    "build_oracle_322_scanner_isolated_discovery.py",
    "build_oracle_500_scanner_machine.py",
    "build_oracle_504_exact_native_hydration_replacement.py",
    "build_oracle_525_native_inventory_hydration.py",
]
WORDS = (
    "def prepare_native", "def prepare_once", "def run(",
    "def main(", "def hydrate(", "def enrich(",
    "def install_and_hook", "def quote_and_publish",
    "def isolated_hydrate", "decimals_x",
    "raise RuntimeError", "raise Hold(",
    "q525.native_candidate", "native_candidate(",
    "checkpoint12", "cp12", "warmup", "warm(",
    "pairs=", "28", "56", "sqlite3.connect",
)
SENSITIVE = re.compile(
    r"(?i)(api.key|private.key|authorization|secret|password)"
    r"\s*[=:]\s*([^\s,;]+)"
)
URI = re.compile(r"(?i)(https?://|wss?://)\S+")

def clean(s):
    s = SENSITIVE.sub(r"\1=[REDACTED]", s)
    return URI.sub("[URL_REDACTED]", s)[:240]

def examine(path):
    if not path.is_file() or path.is_symlink():
        return {"path": str(path.relative_to(ROOT)), "status": "MISSING"}
    src = path.read_text(encoding="utf-8-sig")
    tree = ast.parse(src, filename=str(path))
    lines = src.splitlines()
    selected = set()
    names = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in ("main", "run", "prepare_native",
                             "prepare_once", "hydrate", "enrich",
                             "install_and_hook", "isolated_hydrate"):
                names.append({"name": node.name,
                              "line": node.lineno,
                              "end": node.end_lineno})
                for j in range(node.lineno, min(node.lineno + 12,
                                                node.end_lineno + 1)):
                    selected.add(j)
    for j, line in enumerate(lines, 1):
        if any(k.lower() in line.lower() for k in WORDS):
            for k in range(max(1, j-2), min(len(lines), j+3)+1):
                selected.add(k)
    items = [{"n": j, "text": clean(lines[j-1])}
             for j in sorted(selected) if j <= len(lines)]
    return {"path": str(path.relative_to(ROOT)),
            "sha256": hashlib.sha256(src.encode()).hexdigest(),
            "lines": len(lines), "functions": names,
            "excerpts": items[:500],
            "excerpts_truncated": len(items)>500}

def logs():
    dirs = [ROOT / "runtime_state/oracle",
            ROOT / "logs"]
    markers = ("Traceback (most recent call last)", "RuntimeError:",
               "V1_SCANNER", "V1_EXECUTOR", "CHECKPOINT12")
    results = []
    for folder in dirs:
        if not folder.exists():
            continue
        for p in folder.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in (".log", ".txt", ".jsonl"):
                continue
            if p.stat().st_size > 8000000:
                continue
            try:
                rows = p.read_text(
                    encoding="utf-8", errors="replace"
                ).splitlines()
            except OSError:
                continue
            hits = [i for i, s in enumerate(rows)
                    if any(w in s for w in markers)]
            if hits:
                i = hits[-1]
                results.append({
                    "path": str(p.relative_to(ROOT)),
                    "modified_ns": p.stat().st_mtime_ns,
                    "line": i+1,
                    "tail": [
                        clean(x)
                        for x in rows[max(0,i-8):i+15]
                    ]
                })
    return sorted(
        results, key=lambda x:x["modified_ns"], reverse=True
    )[:20]

def main():
    if not BASE.is_dir():
        raise SystemExit("[HOLD] CANONICAL_BASE_MISSING")
    paths = [BASE / x for x in NAMES]
    paths += [ROOT / x for x in BUILDERS]
    report = {
        "build": "ORACLE_V1_002",
        "read_only": True,
        "signing": False,
        "broadcast": False,
        "source": [examine(p) for p in paths],
        "recent_logs": logs()
    }
    out = ROOT / (
        "runtime_state/oracle/v1_integration/"
        "v1_002_chain_witness.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    for x in report["source"]:
"""ORACLE V1-002: read-only startup chain witness."""
from pathlib import Path
import ast
import hashlib
import json
import re
import sys

ROOT = Path.cwd()
BASE = ROOT / "qseries_v2/oracle_execution/solana_atomic_executor"
NAMES = [
    "V1/scanner.py",
    "V1/executor.py",
    "oracle_525_native_inventory_hydration.py",
    "oracle_524_verified_execution_shadow.py",
    "oracle_523_scanner_executor_handoff.py",
    "oracle_504_execution_engine.py",
    "oracle_500_scanner_machine.py",
    "oracle_344_scanner_align.py",
]
BUILDERS = [
    "build_oracle_322_scanner_isolated_discovery.py",
    "build_oracle_500_scanner_machine.py",
    "build_oracle_504_exact_native_hydration_replacement.py",
    "build_oracle_525_native_inventory_hydration.py",
]
WORDS = (
    "def prepare_native", "def prepare_once", "def run(",
    "def main(", "def hydrate(", "def enrich(",
    "def install_and_hook", "def quote_and_publish",
    "def isolated_hydrate", "decimals_x",
    "raise RuntimeError", "raise Hold(",
    "q525.native_candidate", "native_candidate(",
    "checkpoint12", "cp12", "warmup", "warm(",
    "pairs=", "28", "56", "sqlite3.connect",
)
SENSITIVE = re.compile(
    r"(?i)(api.key|private.key|authorization|secret|password)"
    r"\s*[=:]\s*([^\s,;]+)"
)
URI = re.compile(r"(?i)(https?://|wss?://)\S+")

def clean(s):
    s = SENSITIVE.sub(r"\1=[REDACTED]", s)
    return URI.sub("[URL_REDACTED]", s)[:240]

def examine(path):
    if not path.is_file() or path.is_symlink():
        return {"path": str(path.relative_to(ROOT)), "status": "MISSING"}
    src = path.read_text(encoding="utf-8-sig")
    tree = ast.parse(src, filename=str(path))
    lines = src.splitlines()
    selected = set()
    names = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in ("main", "run", "prepare_native",
                             "prepare_once", "hydrate", "enrich",
                             "install_and_hook", "isolated_hydrate"):
                names.append({"name": node.name,
                              "line": node.lineno,
                              "end": node.end_lineno})
                for j in range(node.lineno, min(node.lineno + 12,
                                                node.end_lineno + 1)):
                    selected.add(j)
    for j, line in enumerate(lines, 1):
        if any(k.lower() in line.lower() for k in WORDS):
            for k in range(max(1, j-2), min(len(lines), j+3)+1):
                selected.add(k)
    items = [{"n": j, "text": clean(lines[j-1])}
             for j in sorted(selected) if j <= len(lines)]
    return {"path": str(path.relative_to(ROOT)),
            "sha256": hashlib.sha256(src.encode()).hexdigest(),
            "lines": len(lines), "functions": names,
            "excerpts": items[:500],
            "excerpts_truncated": len(items)>500}

def logs():
    dirs = [ROOT / "runtime_state/oracle",
            ROOT / "logs"]
    markers = ("Traceback (most recent call last)", "RuntimeError:",
               "V1_SCANNER", "V1_EXECUTOR", "CHECKPOINT12")
    results = []
    for folder in dirs:
        if not folder.exists():
            continue
        for p in folder.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in (".log", ".txt", ".jsonl"):
                continue
            if p.stat().st_size > 8000000:
                continue
            try:
                rows = p.read_text(
                    encoding="utf-8", errors="replace"
                ).splitlines()
            except OSError:
                continue
            hits = [i for i, s in enumerate(rows)
                    if any(w in s for w in markers)]
            if hits:
                i = hits[-1]
                results.append({
                    "path": str(p.relative_to(ROOT)),
                    "modified_ns": p.stat().st_mtime_ns,
                    "line": i+1,
                    "tail": [
                        clean(x)
                        for x in rows[max(0,i-8):i+15]
                    ]
                })
    return sorted(
        results, key=lambda x:x["modified_ns"], reverse=True
    )[:20]

def main():
    if not BASE.is_dir():
        raise SystemExit("[HOLD] CANONICAL_BASE_MISSING")
    paths = [BASE / x for x in NAMES]
    paths += [ROOT / x for x in BUILDERS]
    report = {
        "build": "ORACLE_V1_002",
        "read_only": True,
        "signing": False,
        "broadcast": False,
        "source": [examine(p) for p in paths],
        "recent_logs": logs()
    }
    out = ROOT / (
        "runtime_state/oracle/v1_integration/"
        "v1_002_chain_witness.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    for x in report["source"]:
        print("[SOURCE]", x["path"],
              x.get("lines"), x.get("status", "FOUND"))
        for f in x.get("functions", []):
            print("[ENTRY]", f["name"],
                  f["line"], f["end"])
    print("[RECENT_LOGS]", len(report["recent_logs"]))
    for l in report["recent_logs"][:8]:
        print("[LOG]", l["path"], "line", l["line"])
        for s in l["tail"]:
            print(" ", s)
    print("[REPORT]", out)
    print("[PASS] READ_ONLY_NO_IMPORT_NO_TRADE")
    return 0

if __name__ == "__main__":
    sys.exit(main())

        print("[SOURCE]", x["path"],
              x.get("lines"), x.get("status", "FOUND"))
        for f in x.get("functions", []):
            print("[ENTRY]", f["name"],
                  f["line"], f["end"])
    print("[RECENT_LOGS]", len(report["recent_logs"]))
    for l in report["recent_logs"][:8]:
        print("[LOG]", l["path"], "line", l["line"])
        for s in l["tail"]:
            print(" ", s)
    print("[REPORT]", out)
    print("[PASS] READ_ONLY_NO_IMPORT_NO_TRADE")
    return 0

if __name__ == "__main__":
    sys.exit(main())
