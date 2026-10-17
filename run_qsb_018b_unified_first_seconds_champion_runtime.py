
from __future__ import annotations
import json, time, subprocess, sys
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qsb_018b_unified_first_seconds_champion_runtime import evaluate

ROOT=Path.cwd()
STATE=ROOT/"runtime_state"
QSB015=ROOT/"run_qsb_015_first_seconds_launch_impulse.py"
OUT=STATE/"solana_opportunities"/"qsb_018b_unified_first_seconds_champion_runtime.jsonl"

def _read(p):
    out=[]
    try:
        if p.suffix.lower()==".jsonl":
            for line in p.read_text(encoding="utf-8",errors="ignore").splitlines():
                try: out.append(json.loads(line))
                except Exception: pass
        else:
            out.append(json.loads(p.read_text(encoding="utf-8",errors="ignore")))
    except Exception:
        pass
    return out

def _walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values():
            yield from _walk(v)
    elif isinstance(x,list):
        for v in x:
            yield from _walk(v)

def _mint(r):
    for k in ("mint","token_mint","token_address","address"):
        v=r.get(k)
        if isinstance(v,str) and len(v)>=20:
            return v
    return ""

def _num(r,*keys):
    for k in keys:
        if k in r:
            try: return float(r[k])
            except (TypeError,ValueError): pass
    return 0.0

def _collect():
    launch=[]
    gmgn=[]
    if not STATE.exists():
        return launch,gmgn

    for p in STATE.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in (".json",".jsonl"):
            continue
        s=str(p).lower()
        target=None
        if "qsb_015" in s or "first_seconds" in s or "buy_pressure" in s:
            target=launch
        elif "gmgn" in s or "wallet" in s or "trader" in s:
            target=gmgn
        if target is None:
            continue
        for obj in _read(p):
            target.extend(list(_walk(obj)))
    return launch,gmgn

def cycle():
    launch,gmgn=_collect()
    by_mint={}
    for r in launch:
        m=_mint(r)
        if m:
            by_mint.setdefault(m,[]).append(r)

    admitted=[]
    for mint,rows in by_mint.items():
        bp=max((_num(r,"buy_pressure_score","pressure_score","buy_pressure","acceleration_score") for r in rows),default=0.0)
        liq=max((_num(r,"liquidity_usd","liquidity","pool_liquidity_usd") for r in rows),default=0.0)

        relevant_claims=[]
        for c in gmgn:
            cm=_mint(c)
            if not cm or cm==mint or c.get("token_mint")==mint:
                relevant_claims.append(c)

        d=evaluate(
            mint,
            rows,
            relevant_claims,
            buy_pressure_score=bp,
            liquidity_usd=liq,
        )

        if d.admitted:
            row=d.to_dict()
            row["strategy"]="FIRST_SECONDS+BUY_PRESSURE_ACCELERATION+GMGN_EARLY_WALLET_QUALITY"
            row["mode"]="PAPER_ONLY"
            admitted.append(row)

    OUT.parent.mkdir(parents=True,exist_ok=True)
    if admitted:
        with OUT.open("a",encoding="utf-8") as f:
            for row in admitted:
                f.write(json.dumps(row,sort_keys=True)+"\n")

    print("[QSB-018B] markets=",len(by_mint)," paper_admissions=",len(admitted))
    for row in admitted[:10]:
        print("[PAPER_ADMISSION]",json.dumps(row,sort_keys=True))
    print("[PASS] execution_authority=FALSE")
    return admitted

def main():
    if not QSB015.is_file():
        raise SystemExit("[FAIL] missing QSB-015 runtime")

    child=subprocess.Popen([sys.executable,str(QSB015)],cwd=str(ROOT))
    print("[QSB-018B] SINGLE SOLANA MONEY RUNTIME")
    print("[QSB-018B] QSB-015 + BUY_PRESSURE + GMGN EARLY WALLET QUALITY")
    print("[QSB-018B] PAPER ONLY / execution_authority=FALSE")

    try:
        while True:
            if child.poll() is not None:
                raise SystemExit("[FAIL] QSB-015 child exited rc="+str(child.returncode))
            cycle()
            time.sleep(1.0)
    finally:
        if child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()

if __name__=="__main__":
    main()
