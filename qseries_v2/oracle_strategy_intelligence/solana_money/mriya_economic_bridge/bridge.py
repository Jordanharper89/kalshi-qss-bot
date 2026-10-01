from __future__ import annotations
import asyncio,importlib,json
from collections import Counter
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_broad_same_window.live import hydrate

PKG="qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape"
ROUTER=f"{PKG}.usls_046b_shared_multidex_live_event_router"
ID=f"{PKG}.usls_047c_batched_retry_safe_multidex_identity_resolver"
PUMP=f"{PKG}.usls_048b_shared_universal_economic_normalizer"
REPAIR=f"{PKG}.usls_101d_pumpswap_048b_direct_rematerialization_repair"
MAX_AGE=4

def _rows(o):
    if isinstance(o,list):return [x for x in o if isinstance(x,dict)]
    out=[]
    if isinstance(o,dict):
        for k in ("rows","exact_rows","trades","exact_trades","economic_rows","universal_trades"):
            if isinstance(o.get(k),list):out.extend(x for x in o[k] if isinstance(x,dict))
    return out

def _call(name,root):
    m=importlib.import_module(name);errs=[]
    for fnn in ("write","build","repair","rematerialize","exact_rows"):
        fn=getattr(m,fnn,None)
        if not callable(fn):continue
        try:
            x=fn(root)
            if isinstance(x,tuple) and len(x)>1 and isinstance(x[1],dict):return x[1]
            if isinstance(x,(dict,list)):return x
        except Exception as e:errs.append(f"{fnn}:{type(e).__name__}:{e}")
    raise RuntimeError("; ".join(errs) if errs else "NO_PRODUCER")

async def _capture():
    return await importlib.import_module(ROUTER).capture(seconds=3,max_rows=2800)

def build(root):
    root=Path(root);live=asyncio.run(_capture());rr=list((live or {}).get("rows") or [])
    slots=[]
    for x in rr:
        try:slots.append(int(x.get("slot")))
        except Exception:pass
    mx=max(slots) if slots else None
    print(f"[LIVE_ROUTER] rows={len(rr)} max_slot={mx}",flush=True)
    pump=[]
    try:_call(ID,root)
    except Exception as e:print("[PUMP_ID_FAIL]",e,flush=True)
    for mod in (PUMP,REPAIR):
        try:pump.extend(_rows(_call(mod,root)))
        except Exception as e:print("[PUMP_ECON_FAIL]",mod.rsplit(".",1)[-1],e,flush=True)
    h=hydrate(rr)
    print("[HYDRATE_ATTEMPTED] "+json.dumps(h["attempted"],sort_keys=True),flush=True)
    print("[EXACT_TOKEN_TOKEN] "+json.dumps(h["exact_token_token"],sort_keys=True),flush=True)
    print("[NATIVE_SOL_DISCOVERY] "+json.dumps(h["native_sol_discovery"],sort_keys=True),flush=True)
    print("[HYDRATE_REJECTED] "+json.dumps(h["rejected"],sort_keys=True),flush=True)
    econ=[];seen=set()
    for x in pump+h["rows"]:
        if not isinstance(x,dict):continue
        if not all(k in x for k in ("venue","input_mint","output_mint","input_amount","output_amount","slot")):continue
        try:slot=int(x["slot"]);ia=float(x["input_amount"]);oa=float(x["output_amount"])
        except Exception:continue
        if ia<=0 or oa<=0:continue
        k=(x["venue"],x.get("signature"),x["input_mint"],x["output_mint"],ia,oa,slot)
        if k in seen:continue
        seen.add(k);y=dict(x);y["slot"]=slot;econ.append(y)
    fresh=[]
    for x in econ:
        if mx is None:continue
        age=mx-x["slot"];x["slot_age"]=age
        if 0<=age<=MAX_AGE:fresh.append(x)
    vc=Counter(x["venue"] for x in fresh)
    print("[ECONOMIC_COUNTS] "+json.dumps(dict(sorted(vc.items())),sort_keys=True),flush=True)
    print(f"[BRIDGE] total_economic={len(econ)} fresh_economic={len(fresh)}",flush=True)
    out={"revision":"QSB_044","live_router_rows":len(rr),"live_max_slot":mx,"fresh_economic_rows":fresh,
         "fresh_venue_counts":dict(vc),"hydration":h,"execution_authority":False,
         "truth":"BROAD_SAME_WINDOW_DISCOVERY_ROWS_REQUIRE_QSB042_EXECUTABLE_REQUOTE"}
    p=root/"runtime_state/qseries/qsb044_broad_same_window/report.json";p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,indent=2),encoding="utf-8")
    return out
