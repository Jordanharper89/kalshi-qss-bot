from __future__ import annotations
import json
import re
from pathlib import Path

PATH_PATTERNS = (
    r"runtime_state",
    r"runtime[/\\]",
    r"\.jsonl?",
    r"\.sqlite3?",
    r"\.db",
    r"postgres",
    r"psycopg",
    r"Path\(",
    r"open\(",
    r"read_text",
    r"write_text",
    r"read_bytes",
    r"write_bytes",
    r"INSERT INTO",
    r"SELECT ",
    r"CREATE TABLE",
    r"pool",
    r"mint",
    r"token",
    r"swap",
    r"signature",
    r"slot",
    r"block_time",
    r"observed_at",
)

def inspect_source(root: Path, relative: str) -> dict:
    path = root / relative
    if not path.is_file():
        return {"path": relative, "exists": False, "matches": []}
    text = path.read_text(encoding="utf-8", errors="replace")
    matches = []
    for number, line in enumerate(text.splitlines(), 1):
        if any(re.search(pattern, line, re.I) for pattern in PATH_PATTERNS):
            matches.append({"line": number, "text": line[:700]})
    return {
        "path": relative,
        "exists": True,
        "matches": matches[:500],
    }

def runtime_inventory(root: Path) -> list[dict]:
    rows = []
    for base_name in ("runtime_state", "runtime"):
        base = root / base_name
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            low = str(path).lower()
            if not any(term in low for term in ("solana", "mint", "pool", "swap", "token", "wallet")):
                continue
            stat = path.stat()
            rows.append({
                "path": str(path.relative_to(root)),
                "size": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
                "suffix": path.suffix.lower(),
            })
    rows.sort(key=lambda x: x["mtime_ns"], reverse=True)
    return rows[:500]

def audit(root: Path, targets: list[str]) -> dict:
    sources = [inspect_source(root, target) for target in targets]
    existing = [x for x in sources if x["exists"]]
    return {
        "revision": "OSI_023",
        "purpose": "Locate the exact certified Solana physical persistence/readback boundary for OSI live opportunity intake.",
        "source_modules": sources,
        "existing_source_count": len(existing),
        "runtime_inventory": runtime_inventory(root),
        "execution_authority": False,
        "read_only": True,
        "certification": "LINEAGE_AUDIT_ONLY",
    }

def write_report(root: Path, targets: list[str]) -> Path:
    data = audit(root, targets)
    path = root / "OSI_023_CERTIFIED_SOLANA_PHYSICAL_SOURCE_LINEAGE_AUDIT.json"
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    return path
