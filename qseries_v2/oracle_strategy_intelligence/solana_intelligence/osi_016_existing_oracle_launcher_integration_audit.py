from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path

EXECUTION_AUTHORITY = False
READ_ONLY = True

ANCHOR_PATTERNS = (
    r'if\s+__name__\s*==\s*["\']__main__["\']',
    r'subprocess\.Popen',
    r'threading\.Thread',
    r'multiprocessing',
    r'run_slop_buy_pressure_live',
    r'oracle_live',
)

def _sha256_raw(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def audit(root: Path) -> dict:
    launcher = root / "run_oracle_live.py"
    if not launcher.is_file():
        raise RuntimeError("Missing existing production launcher: run_oracle_live.py")

    raw = launcher.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    lines = text.splitlines()
    anchors = []

    for number, line in enumerate(lines, 1):
        matched = [pattern for pattern in ANCHOR_PATTERNS if re.search(pattern, line, re.I)]
        if matched:
            anchors.append({
                "line": number,
                "text": line[:500],
                "matched": matched,
            })

    existing_osi_refs = [
        {"line": n, "text": line[:500]}
        for n, line in enumerate(lines, 1)
        if "solana_intelligence" in line.lower() or "osi_" in line.lower()
    ]

    report = {
        "revision": "OSI_016",
        "purpose": "Capture the exact existing Oracle production launcher before OSI 24/7 registration.",
        "launcher": "run_oracle_live.py",
        "launcher_sha256_raw_windows_bytes": _sha256_raw(launcher),
        "launcher_size_bytes": len(raw),
        "anchors": anchors,
        "existing_osi_refs": existing_osi_refs,
        "osi_already_registered": bool(existing_osi_refs),
        "safe_to_patch_claimed": False,
        "execution_authority": False,
        "read_only": True,
        "certification": "SOURCE_CAPTURE_ONLY",
    }
    return report

def write_report(root: Path) -> Path:
    data = audit(root)
    path = root / "OSI_016_EXISTING_ORACLE_LAUNCHER_INTEGRATION_AUDIT.json"
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    return path
