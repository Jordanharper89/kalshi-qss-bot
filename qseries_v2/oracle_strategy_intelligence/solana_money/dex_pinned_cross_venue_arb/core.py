from __future__ import annotations
import asyncio, importlib, json, os, time, urllib.parse, urllib.request
from pathlib import Path

PKG="qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape"
ROUTER=f"{PKG}.usls_046b_shared_multidex_live_event_router"
IDENT=f"{PKG}.usls_047c_batched_retry_safe_multidex_identity_resolver"
ECON=f"{PKG}.usls_048b_shared_universal_economic_normalizer"

WSOL="So11111111111111111111111111111111111111112"

# Exact Jupiter program-id-to-label names verified 2026-09-24.
DEXES=(
    "Pump.fun Amm",
    "Meteora DLMM",
    "Meteora DAMM v2",
    "Raydium CLMM",
    "Raydium CP",
    "Raydium",
    "Whirlpool",
    "PancakeSwap",
)

SIZES_SOL=tuple(float(x) for x in os.getenv("QSB_046_SIZES_SOL","0.025").split(",") if x.strip())
MAX_TOKENS=int(os.getenv("QSB_046_MAX_TOKENS","4"))
TOP_BUYS=int(os.getenv("QSB_046_TOP_BUYS","2"))
MIN_NET_BPS=float(os.getenv("QSB_046_MIN_NET_BPS","12"))
COST_LAMPORTS=int(os.getenv("QSB_046_COST_LAMPORTS","150000"))
MAX_CONTEXT_SLOT_SPREAD=int(os.getenv("QSB_046_MAX_SLOT_SPREAD","3"))
API_KEY=os.getenv("JUPITER_API_KEY","").strip()
BASE=os.getenv("QSB_JUPITER_SWAP_URL", "https://api.jup.ag/swap/v1" if API_KEY else "https://lite-api.jup.ag/swap/v1")
PACE=float(os.getenv("QSB_046_PACE_SECONDS","1.05" if API_KEY else "2.10"))

def http_json(url, timeout=20, retries=3):
    headers={"accept":"application/json","user-agent":"qseries-qsb046/1.0"}
    if API_KEY: headers["x-api-key"]=API_KEY
    last=None
    for i in range(retries):
        try:
            req=urllib.request.Request(url,headers=headers)
            with urllib.request.urlopen(req,timeout=timeout) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            last=e
            if i+1<retries: time.sleep(max(PACE, .75*(i+1)))
    raise last

def quote(input_mint, output_mint, amount, dex, http=http_json):
    q=urllib.parse.urlencode({
        "inputMint":input_mint,
        "outputMint":output_mint,
        "amount":str(int(amount)),
        "swapMode":"ExactIn",
        "slippageBps":"30",
        "dexes":dex,
        "onlyDirectRoutes":"true",
        "restrictIntermediateTokens":"true",
    })
    j=http(f"{BASE}/quote?{q}",20)
    if not isinstance(j,dict): raise RuntimeError("QUOTE_NON_OBJECT")
    try:
        out=int(j["outAmount"])
        floor=int(j["otherAmountThreshold"])
        slot=int(j["contextSlot"])
    except Exception:
        raise RuntimeError("QUOTE_REQUIRED_FIELDS_MISSING:"+json.dumps(j)[:300])
    rp=j.get("routePlan") or []
    if len(rp)!=1: raise RuntimeError("NOT_SINGLE_DIRECT_ROUTE")
    si=(rp[0] or {}).get("swapInfo") or {}
    label=si.get("label")
    if label!=dex:
        raise RuntimeError(f"DEX_PIN_MISMATCH expected={dex!r} got={label!r}")
    if out<=0 or floor<=0: raise RuntimeError("NONPOSITIVE_QUOTE")
    return {
        "dex":dex,"inAmount":int(amount),"outAmount":out,"floorAmount":floor,
        "contextSlot":slot,"ammKey":si.get("ammKey"),"feeAmount":si.get("feeAmount"),
        "feeMint":si.get("feeMint"),"priceImpactPct":j.get("priceImpactPct"),
        "routeLabel":label,
    }

def cross_venue(token, start_lamports, buy_dex, sell_dex, http=http_json):
    if buy_dex==sell_dex: raise ValueError("SAME_DEX_NOT_ARBITRAGE")
    buy=quote(WSOL,token,start_lamports,buy_dex,http)
    time.sleep(PACE)
    # Re-quote the exact token output on a different DEX.
    sell=quote(token,WSOL,buy["outAmount"],sell_dex,http)
    spread=abs(sell["contextSlot"]-buy["contextSlot"])
    gross=sell["outAmount"]-int(start_lamports)
    # Conservative: use second leg's slippage floor, then subtract modeled tx/priority/tip costs.
    floor_net=sell["floorAmount"]-int(start_lamports)-COST_LAMPORTS
    floor_bps=floor_net/int(start_lamports)*10000.0
    return {
        "token":token,"buy_dex":buy_dex,"sell_dex":sell_dex,
        "start_lamports":int(start_lamports),"token_raw":buy["outAmount"],
        "gross_end_lamports":sell["outAmount"],"floor_end_lamports":sell["floorAmount"],
        "gross_lamports":gross,"modeled_cost_lamports":COST_LAMPORTS,
        "floor_net_lamports":floor_net,"floor_net_bps":floor_bps,
        "context_slot_spread":spread,
        "buy":buy,"sell":sell,
        "qualified":bool(floor_net>0 and floor_bps>=MIN_NET_BPS and spread<=MAX_CONTEXT_SLOT_SPREAD),
        "execution_authority":False,
    }

async def _capture():
    return await importlib.import_module(ROUTER).capture(seconds=3,max_rows=2600)

def _persist_router(root,d):
    p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/multidex_live_event_router.json"
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,indent=2),encoding="utf-8")

def _producer(modname,root):
    m=importlib.import_module(modname)
    for n in ("write","build","resolve"):
        fn=getattr(m,n,None)
        if callable(fn):
            x=fn(root)
            if isinstance(x,tuple) and len(x)>1:return x[1]
            return x
    raise RuntimeError("NO_PRODUCER:"+modname)

def fresh_tokens(root):
    live=asyncio.run(_capture())
    rows=list((live or {}).get("rows") or [])
    slots=[]
    for x in rows:
        try: slots.append(int(x.get("slot")))
        except Exception: pass
    mx=max(slots) if slots else None
    _persist_router(root,live)
    _producer(IDENT,root)
    d=_producer(ECON,root)
    erows=(d or {}).get("exact_rows") or (d or {}).get("rows") or []
    cand=[]
    for x in erows:
        if not isinstance(x,dict) or x.get("venue")!="PUMP_SWAP": continue
        t=x.get("token_address")
        if not t or t==WSOL: continue
        try: slot=int(x.get("slot"))
        except Exception: continue
        if mx is not None and 0<=mx-slot<=4: cand.append((slot,t))
    out=[];seen=set()
    for slot,t in sorted(cand,reverse=True):
        if t not in seen:
            seen.add(t);out.append(t)
        if len(out)>=MAX_TOKENS:break
    return {"live_rows":len(rows),"max_slot":mx,"tokens":out}

def scan_token(token,start_lamports,http=http_json):
    buys=[];errors=[]
    # Step 1: compare the exact same WSOL input across every DEX.
    for dex in DEXES:
        try:
            q=quote(WSOL,token,start_lamports,dex,http)
            buys.append(q)
            print("[BUY_QUOTE] dex=%s token=%s out=%d slot=%d"%(dex,token[:10],q["outAmount"],q["contextSlot"]),flush=True)
        except Exception as e:
            errors.append({"side":"BUY","dex":dex,"error":f"{type(e).__name__}: {e}"})
        time.sleep(PACE)
    buys.sort(key=lambda x:x["outAmount"],reverse=True)
    # Most token output for same SOL = cheapest venue(s).
    buys=buys[:TOP_BUYS]
    routes=[]
    for b in buys:
        for sell_dex in DEXES:
            if sell_dex==b["dex"]: continue
            try:
                s=quote(token,WSOL,b["outAmount"],sell_dex,http)
                spread=abs(s["contextSlot"]-b["contextSlot"])
                floor_net=s["floorAmount"]-start_lamports-COST_LAMPORTS
                bps=floor_net/start_lamports*10000.0
                r={
                    "token":token,"buy_dex":b["dex"],"sell_dex":sell_dex,
                    "start_lamports":start_lamports,"token_raw":b["outAmount"],
                    "floor_end_lamports":s["floorAmount"],"gross_end_lamports":s["outAmount"],
                    "floor_net_lamports":floor_net,"floor_net_bps":bps,
                    "context_slot_spread":spread,"buy":b,"sell":s,
                    "qualified":bool(floor_net>0 and bps>=MIN_NET_BPS and spread<=MAX_CONTEXT_SLOT_SPREAD),
                    "execution_authority":False,
                }
                routes.append(r)
                print("[CROSS_DEX] BUY=%s SELL=%s token=%s net=%+.9f SOL net_bps=%+.2f slots=%d QUALIFIED=%s"%(
                    b["dex"],sell_dex,token[:10],floor_net/1e9,bps,spread,r["qualified"]),flush=True)
            except Exception as e:
                errors.append({"side":"SELL","buy_dex":b["dex"],"sell_dex":sell_dex,"error":f"{type(e).__name__}: {e}"})
            time.sleep(PACE)
    return routes,errors

def build(root,http=http_json):
    root=Path(root);src=fresh_tokens(root)
    print("[DISCOVERY] live_rows=%d max_slot=%s tokens=%d"%(src["live_rows"],src["max_slot"],len(src["tokens"])),flush=True)
    print("[DEXES] "+json.dumps(DEXES),flush=True)
    all_routes=[];errors=[]
    for token in src["tokens"]:
        for sol in SIZES_SOL:
            rs,es=scan_token(token,int(round(sol*1e9)),http)
            all_routes.extend(rs);errors.extend(es)
    all_routes.sort(key=lambda x:x["floor_net_bps"],reverse=True)
    qualified=[x for x in all_routes if x["qualified"]]
    if qualified:
        x=qualified[0]
        print("[BEST_ARB] BUY_LOW=%s SELL_HIGH=%s token=%s size=%.3f net=%+.9f SOL net_bps=%+.2f slots=%d"%(
            x["buy_dex"],x["sell_dex"],x["token"],x["start_lamports"]/1e9,
            x["floor_net_lamports"]/1e9,x["floor_net_bps"],x["context_slot_spread"]),flush=True)
    elif all_routes:
        x=all_routes[0]
        print("[BEST_SPREAD] BUY=%s SELL=%s net_bps=%+.2f NOT_QUALIFIED"%(x["buy_dex"],x["sell_dex"],x["floor_net_bps"]),flush=True)
    else:
        print("[NO_CROSS_DEX_QUOTES]",flush=True)
    out={"revision":"QSB_046","source":src,"dexes":list(DEXES),
         "route_count":len(all_routes),"qualified_count":len(qualified),
         "best":qualified[0] if qualified else (all_routes[0] if all_routes else None),
         "qualified":qualified[:20],"errors":errors,
         "execution_authority":False,"atomic":False,
         "truth":"DEX_PINNED_DIRECT_CROSS_VENUE_ARBITRAGE_DETECTION"}
    p=root/"runtime_state/qseries/qsb046_dex_pinned_cross_venue_arb/report.json"
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(out,indent=2),encoding="utf-8")
    return out
