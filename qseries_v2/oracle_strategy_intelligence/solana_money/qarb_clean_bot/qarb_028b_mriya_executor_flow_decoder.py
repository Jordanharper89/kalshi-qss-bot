from __future__ import annotations
import json
from collections import Counter
from pathlib import Path
SRC=Path("runtime_state/qseries/qarb_clean_bot/mriya_recent_transactions.json")
OUT=Path("runtime_state/qseries/qarb_clean_bot/mriya_route_decode.json")
FALLBACK={"pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA":"PUMP_SWAP",
"LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo":"METEORA_DLMM",
"JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4":"JUPITER_V6"}
def registry():
    r=dict(FALLBACK)
    try:
        from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_045b_universal_multidex_decoder_framework import PROGRAMS
        for k,v in dict(PROGRAMS).items():
            if isinstance(v,str):r[v]=str(k).upper()
    except Exception:pass
    return r
def deltas(rows):
    pre={};post={}
    for x in rows or []:
        key=(x.get("account_index"),x.get("mint"))
        (pre if x.get("side")=="pre" else post)[key]=float(x.get("amount") or 0)
    out={}
    for key in set(pre)|set(post):
        d=post.get(key,0)-pre.get(key,0)
        if abs(d)>0:out[key]=d
    return out
def decode(payload):
    reg=registry();vc=Counter();mc=Counter();rows=[]
    for x in payload.get("rows") or []:
        if x.get("error") or x.get("err") is not None:continue
        ds=deltas(x.get("token_balance_rows"));bymint={}
        for (_,m),d in ds.items():bymint[m]=bymint.get(m,0)+d
        names=sorted({reg[p] for p in x.get("program_ids") or [] if p in reg})
        for n in names:vc[n]+=1
        for m,d in bymint.items():
            if abs(d)>0:mc[m]+=1
        bought=sorted(m for m,d in bymint.items() if d>0);sold=sorted(m for m,d in bymint.items() if d<0)
        route="MULTI_DEX" if len(names)>=2 else ("SINGLE_DEX" if len(names)==1 else "UNKNOWN")
        econ="TOKEN_TO_TOKEN" if bought and sold else ("TOKEN_INFLOW" if bought else ("TOKEN_OUTFLOW" if sold else "CLOSED_OR_INTERNAL_FLOW"))
        rows.append({"signature":x["signature"],"slot":x.get("slot"),"block_time":x.get("block_time"),
                     "venues":names,"route_class":route,"economic_shape":econ,"mint_deltas":bymint,
                     "bought_mints":bought,"sold_mints":sold,"sol_deltas":x.get("sol_deltas") or {}})
    return {"target":payload.get("target"),"executor":payload.get("executor"),"decoded":len(rows),
            "rows":rows,"venue_counts":dict(vc),"mint_counts":dict(mc),"execution_authority":False}
def run():
    if not SRC.is_file():raise SystemExit("[FAIL] run QARB-027B first")
    r=decode(json.loads(SRC.read_text(encoding="utf-8")))
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(r,indent=2,sort_keys=True),encoding="utf-8")
    print("[QARB-028B] MRIYA EXECUTOR / CPI FLOW DECODER")
    print("[VENUES]",json.dumps(r["venue_counts"],sort_keys=True));print("[TOKENS] unique=%d"%len(r["mint_counts"]))
    for x in r["rows"][:20]:print("[ROUTE] slot=%s class=%s econ=%s venues=%s buys=%s sells=%s"%(x["slot"],x["route_class"],x["economic_shape"],x["venues"],[m[:10] for m in x["bought_mints"]],[m[:10] for m in x["sold_mints"]]))
    print("[REPORT]",OUT);print("[MODE] READ_ONLY=True execution_authority=FALSE");return r
