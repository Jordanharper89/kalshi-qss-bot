
from __future__ import annotations
import json, math, time
from pathlib import Path

READ_ONLY=True
EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REVISION="QSB_019B_BUY_PRESSURE_LIVE_SCAN_REPAIR_V1"

def fresh_candidate_files(root: Path, max_files=300, max_age_seconds=7200):
    roots=(
        root/"runtime_state/solana_opportunities",
        root/"runtime/solana",
        root/"runtime/strategy_discovery",
    )
    now=time.time()
    found=[]
    for base in roots:
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in (".json",".jsonl"):
                continue
            try:
                age=now-p.stat().st_mtime
                if age<=max_age_seconds:
                    found.append((p.stat().st_mtime,p))
            except OSError:
                continue
    found.sort(key=lambda x:x[0],reverse=True)
    return [p for _,p in found[:max_files]]

def load_tail_objects(path: Path, max_lines=400):
    out=[]
    try:
        if path.suffix.lower()==".jsonl":
            lines=path.read_text(encoding="utf-8",errors="ignore").splitlines()
            for ln in lines[-max_lines:]:
                try: out.append(json.loads(ln))
                except Exception: pass
        else:
            out.append(json.loads(path.read_text(encoding="utf-8",errors="ignore")))
    except Exception:
        pass
    return out
