
from __future__ import annotations
import json, os, subprocess, sys
from pathlib import Path

READ_ONLY=True
EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REVISION="QSB_020C_UNIVERSAL_BUY_PRESSURE_FORWARD_SUPERVISOR_V1"
TARGET="BUY_PRESSURE_ACCELERATION"

def parse_leader(line: str):
    if not line.startswith("[LEADERS]"):
        return None
    try:
        rows=json.loads(line.split("]",1)[1].strip())
    except Exception:
        return None
    if not isinstance(rows,list):
        return None
    for r in rows:
        if isinstance(r,dict) and r.get("strategy")==TARGET:
            return {
                "closed": int(r.get("closed") or 0),
                "wins": int(r.get("wins") or 0),
                "losses": int(r.get("losses") or 0),
                "net": float(r.get("net") if r.get("net") is not None else r.get("net_pnl_usdc") or 0.0),
                "win_rate": r.get("win_rate"),
            }
    return None

def delta(current, baseline):
    return {
        "closed": max(0,current["closed"]-baseline["closed"]),
        "wins": max(0,current["wins"]-baseline["wins"]),
        "losses": max(0,current["losses"]-baseline["losses"]),
        "net": current["net"]-baseline["net"],
    }

def milestone(d):
    return d["wins"] >= 10 and d["net"] > 0.0

def child_env():
    e=os.environ.copy()
    e["PYTHONUNBUFFERED"]="1"
    return e

def start_child(script: Path, cwd: Path):
    return subprocess.Popen(
        [sys.executable,"-u",str(script)],
        cwd=str(cwd),
        env=child_env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
