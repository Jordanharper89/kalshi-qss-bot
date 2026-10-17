
from __future__ import annotations
import json, time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qsb_017_early_buyer_wallet_quality_gate import evaluate

ROOT=Path.cwd()
STATE=ROOT/"runtime_state"
OUT=STATE/"solana_opportunities"/"qsb_017_early_buyer_wallet_quality_gate.jsonl"

def _walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values(): yield from _walk(v)
    elif isinstance(x,list):
        for v in x: yield from _walk(v)

def _read(path):
    try:
        if path.suffix.lower()==".jsonl":
            rows=[]
            for ln in path.read_text(encoding="utf-8",errors="ignore").splitlines():
                try: rows.append(json.loads(ln))
                except Exception: pass
            return rows
        return [json.loads(path.read_text(encoding="utf-8",errors="ignore"))]
    except Exception:
        return []

def _mint(r):
    for k in ("mint","token_mint","token_address","address"):
        v=r.get(k)
        if isinstance(v,str) and len(v)>=20: return v
    return ""

def _liq(r):
    for k in ("liquidity_usd","liquidity","pool_liquidity_usd"):
        try: return float(r.get(k))
        except (TypeError,ValueError): pass
    return 0.0

def cycle():
    files=[p for p in STATE.rglob("*") if p.is_file() and p.suffix.lower() in (".json",".jsonl")]
    launch_files=[p for p in files if "qsb_015" in p.name.lower() or "first_seconds" in p.name.lower()]
    gmgn_files=[p for p in files if any(s in str(p).lower() for s in ("gmgn","wallet","trader"))]
    launches=[]; claims=[]
    for p in launch_files:
        for obj in _read(p):
            launches.extend(list(_walk(obj)))
    for p in gmgn_files:
        for obj in _read(p):
            claims.extend(list(_walk(obj)))
    by_mint={}
    for r in launches:
        m=_mint(r)
        if m: by_mint.setdefault(m,[]).append(r)
    emitted=[]
    for mint,rows in by_mint.items():
        liq=max((_liq(r) for r in rows),default=0.0)
        mclaims=[c for c in claims if _mint(c) in ("",mint) or c.get("token_mint")==mint]
        result=evaluate(mint,rows,mclaims,liquidity_usd=liq)
        d=result.to_dict()
        if result.admitted:
            d["strategy"]="FIRST_SECONDS_EARLY_BUYER_WALLET_QUALITY"
            d["mode"]="PAPER_ONLY"
            emitted.append(d)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    if emitted:
        with OUT.open("a",encoding="utf-8") as f:
            for row in emitted:
                f.write(json.dumps(row,sort_keys=True)+"\n")
    print("[QSB-017] launch_files=",len(launch_files),"gmgn_files=",len(gmgn_files),"paper_admissions=",len(emitted))
    for row in emitted[:10]: print("[PAPER_ADMISSION]",json.dumps(row,sort_keys=True))
    print("[PASS] execution_authority=FALSE")
    return emitted

if __name__=="__main__":
    while True:
        cycle()
        time.sleep(1.0)
