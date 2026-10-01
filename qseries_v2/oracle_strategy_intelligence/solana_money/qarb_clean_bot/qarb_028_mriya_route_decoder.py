from __future__ import annotations
import json
from collections import Counter
from pathlib import Path

SRC=Path("runtime_state/qseries/qarb_clean_bot/mriya_recent_transactions.json")
OUT=Path("runtime_state/qseries/qarb_clean_bot/mriya_route_decode.json")

FALLBACK={
"pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA":"PUMPSWAP",
"LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo":"METEORA_DLMM",
"JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4":"JUPITER_V6",
}

def program_registry():
    reg=dict(FALLBACK)
    try:
        from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_045b_universal_multidex_decoder_framework import PROGRAMS
        for name,pid in dict(PROGRAMS).items():
            if isinstance(pid,str): reg[pid]=str(name).upper()
    except Exception: pass
    return reg

def decode(payload):
    reg=program_registry(); rows=[]; venues=Counter(); mints=Counter()
    for x in payload.get("rows") or []:
        if x.get("error") or x.get("err") is not None: continue
        names=sorted({reg[p] for p in x.get("program_ids") or [] if p in reg})
        td=x.get("wallet_token_deltas") or {}
        bought=sorted([m for m,v in td.items() if v>0]); sold=sorted([m for m,v in td.items() if v<0])
        for n in names: venues[n]+=1
        for m in td: mints[m]+=1
        route_class="UNKNOWN"
        if len(names)>=2: route_class="MULTI_DEX"
        elif len(names)==1: route_class="SINGLE_DEX"
        if bought and sold: econ="TOKEN_TO_TOKEN"
        elif bought and (x.get("wallet_sol_delta") or 0)<0: econ="SOL_TO_TOKEN"
        elif sold and (x.get("wallet_sol_delta") or 0)>0: econ="TOKEN_TO_SOL"
        else: econ="COMPLEX_OR_ROUTER"
        rows.append({"signature":x["signature"],"slot":x.get("slot"),"block_time":x.get("block_time"),
                     "venues":names,"route_class":route_class,"economic_shape":econ,
                     "bought_mints":bought,"sold_mints":sold,"token_deltas":td,
                     "wallet_sol_delta":x.get("wallet_sol_delta")})
    return {"target":payload.get("target"),"decoded":len(rows),"rows":rows,
            "venue_counts":dict(venues),"mint_counts":dict(mints),"execution_authority":False}

def run():
    if not SRC.is_file(): raise SystemExit("[FAIL] run QARB-027 first: "+str(SRC))
    r=decode(json.loads(SRC.read_text(encoding="utf-8")))
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(r,indent=2,sort_keys=True),encoding="utf-8")
    print("[QARB-028] MRIYA ROUTE / FLOW DECODER")
    print("[VENUES]",json.dumps(r["venue_counts"],sort_keys=True))
    print("[TOKENS] unique=%d"%len(r["mint_counts"]))
    for x in r["rows"][:15]:
        print("[ROUTE] slot=%s class=%s econ=%s venues=%s buy=%s sell=%s"%(
            x["slot"],x["route_class"],x["economic_shape"],x["venues"],
            [m[:10] for m in x["bought_mints"]],[m[:10] for m in x["sold_mints"]]))
    print("[REPORT]",OUT)
    print("[MODE] READ_ONLY=True execution_authority=FALSE")
    return r
