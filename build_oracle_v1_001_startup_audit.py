
from pathlib import Path
import ast
import json
import re
import sys
import traceback

ROOT = Path.cwd()
BASE = ROOT / "qseries_v2" / "oracle_execution" / "solana_atomic_executor"
OUT = ROOT / "runtime_state" / "oracle" / "v1_integration"
OUT.mkdir(parents=True, exist_ok=True)

TARGETS = (
    "oracle_322", "oracle_344", "oracle_500",
    "oracle_504", "oracle_522", "oracle_523",
    "oracle_524", "oracle_525", "v1",
    "scanner", "executor", "checkpoint12",
)
SIGNALS = (
    "RuntimeError", "decimals_x", "warmup",
    "sqlite3.connect", "create_task",
    "asyncio.run", "raise ", "28_pair",
    "ready_pairs", "watched_addresses",
    "checkpoint12", "hydration",
    "native", "signed_simulation",
)

def sanitize(text):
    text = str(text)
    text = re.sub(
        r"(?i)(api[-_]?key|private[-_]?key|"
        r"authorization|secret|token)\s*[=:]\s*"
        r"['\"]?[^'\"\s,;]+",
        r"\1=[REDACTED]", text
    )
    text = re.sub(
        r"(?i)(api-key=)[^&\s]+",
        r"\1[REDACTED]", text
    )
    return text[:280]

def describe(path):
    relative = path.relative_to(ROOT).as_posix()
    raw = path.read_text(encoding="utf-8-sig")
    tree = ast.parse(raw, filename=relative)
    imports = []
    funcs = []
    classes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(x.name for x in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
        elif isinstance(node, (ast.FunctionDef,
                               ast.AsyncFunctionDef)):
            funcs.append(node.name)
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)
    lines = raw.splitlines()
    matches = []
    for number, line in enumerate(lines, 1):
        if any(s.lower() in line.lower() for s in SIGNALS):
            matches.append({
                "line": number,
                "snippet": sanitize(line.strip())
            })
    return {
        "path": relative,
        "lines": len(lines),
        "imports": sorted(set(imports)),
        "functions": sorted(set(funcs)),
        "classes": sorted(set(classes)),
        "signals": matches[:35],
    }

def main():
    print("[ORACLE-V1-001] LOCAL SOURCE AUDIT")
    print("[ROOT]", ROOT)
    print("[SCOPE] READ_ONLY")
    print("[PRIVATE_KEY] NOT_ACCESSED")
    print("[SIGNING] FALSE")
    print("[BROADCAST] FALSE")
    if not BASE.is_dir():
        print("[FAIL] CANONICAL_EXECUTOR_DIRECTORY_MISSING")
        return 2

    candidates = []
    candidates.extend(ROOT.glob("build_oracle_*.py"))
    candidates.extend(ROOT.glob("*v1*.py"))
    candidates.extend(BASE.rglob("*.py"))
    candidates = sorted(set(p for p in candidates
                            if p.is_file()))

    selected = []
    for p in candidates:
        name = p.name.lower()
        if any(t in name for t in TARGETS):
            selected.append(p)

    inventory = {
        "files_scanned": len(candidates),
        "relevant_files": len(selected),
        "modules": [],
        "syntax_errors": [],
        "runtime_logs": [],
    }

    print("[FILES]", len(candidates))
    print("[RELEVANT]", len(selected))

    for path in selected:
        try:
            item = describe(path)
            inventory["modules"].append(item)
            print("[MODULE]", item["path"],
                  "lines=" + str(item["lines"]))
        except (SyntaxError, UnicodeError) as exc:
            message = {
                "path": path.relative_to(ROOT).as_posix(),
                "error": sanitize(exc),
            }
            inventory["syntax_errors"].append(message)
            print("[SOURCE_ERROR]", message)

    logroots = [
        ROOT / "runtime_state" / "oracle",
        ROOT / "logs",
    ]
    patterns = (
        "Traceback (most recent call last)",
        "RuntimeError:",
        "decimals_x",
    )
    for directory in logroots:
        if not directory.is_dir():
            continue
        found = 0
        for path in directory.rglob("*"):
            if found >= 100:
                break
            if not path.is_file():
                continue
            if path.suffix.lower() not in (
                ".log", ".txt", ".jsonl"
            ):
                continue
            try:
                if path.stat().st_size > 4_000_000:
                    continue
                raw = path.read_text(
                    encoding="utf-8", errors="replace"
                )
                lines = raw.splitlines()
                for i, line in enumerate(lines):
                    if any(s in line for s in patterns):
                        excerpt = lines[max(0, i-3):i+10]
                        inventory["runtime_logs"].append({
                            "path": path.relative_to(
                                ROOT).as_posix(),
                            "line": i + 1,
                            "excerpt": [
                                sanitize(x) for x in excerpt
                            ]
                        })
                        found += 1
                        break
            except OSError:
                continue

    report = OUT / "oracle_v1_001_startup_audit.json"
    report.write_text(
        json.dumps(inventory, indent=2),
        encoding="utf-8"
    )

    print("[SYNTAX_ERRORS]",
          len(inventory["syntax_errors"]))
    print("[RUNTIME_LOG_MATCHES]",
          len(inventory["runtime_logs"]))
    for item in inventory["runtime_logs"][:12]:
        print("[LOG]", item["path"],
              "line=" + str(item["line"]))
        for line in item["excerpt"]:
            print(" ", line)

    print("[REPORT]", report)
    print("[STATUS] AUDIT_COMPLETE_NO_MUTATIONS")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        sys.exit(1)
