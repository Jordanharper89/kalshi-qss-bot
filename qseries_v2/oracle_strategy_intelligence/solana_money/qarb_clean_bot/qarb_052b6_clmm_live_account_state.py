from __future__ import annotations
import base64,json,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
MAX_AGE_MS=750.0
SRC=Path("runtime_state/qseries/qarb_clean_bot/qarb_052b5_clmm_exact_descriptor_pavement.json")
OUT=Path("runtime_state/qseries/qarb_clean_bot/qarb_052b6_clmm_live_account_state.json")

def load_desc(root):
    p=Path(root)/SRC
    if not p.is_file(): raise RuntimeError("QARB_052B5_ARTIFACT_MISSING")
    o=json.loads(p.read_text(encoding="utf-8"))
    return list(o.get("descriptors") or [])

def materialize(root):
    rows=[];errors=[]
    for d in load_desc(root):
        accounts=list(d.get("watched_accounts") or [])
        live=[]
        for a in accounts:
            addr=a.get("pubkey") if isinstance(a,dict) else a
            if not isinstance(addr,str) or not addr: continue
            try:
                raw,slot=c.account(addr)
                live.append({"address":addr,"bytes":len(raw),"slot":slot})
            except Exception as e:
                errors.append({"pool":d.get("pool"),"address":addr,"error":type(e).__name__+":"+str(e)})
        rows.append({"pool":d.get("pool"),"token_a":d.get("token_a"),"token_b":d.get("token_b"),
                     "account_count":len(accounts),"live_accounts":live,
                     "live_account_count":len(live),"observed_ns":time.perf_counter_ns()})
    return rows,errors

def main():
    root=Path.cwd();rows,errors=materialize(root)
    payload={"revision":"QARB_052B6","pool_count":len(rows),
             "live_pool_count":sum(1 for r in rows if r["live_account_count"]>0),
             "rows":rows,"errors":errors[:30],"local_quote_bound":False,
             "next_boundary":"RAYDIUM_CLMM_LOCAL_MATH_FROM_LIVE_POOL_TICK_STATE",
             "execution_authority":False}
    p=root/OUT;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    print("[QARB-052B6] RAYDIUM CLMM LIVE ACCOUNT STATE")
    print("[CLMM_POOLS]",payload["pool_count"])
    print("[CLMM_LIVE_POOLS]",payload["live_pool_count"])
    for r in rows: print("[CLMM_LIVE_STATE]",str(r["pool"])[:12],"accounts=%d/%d"%(r["live_account_count"],r["account_count"]))
    print("[LOCAL_QUOTE_BOUND]",False)
    print("[NEXT]",payload["next_boundary"])
    print("[REPORT]",OUT)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE")
