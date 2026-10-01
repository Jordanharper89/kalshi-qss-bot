from __future__ import annotations
import asyncio,importlib,json,os,time,urllib.parse,urllib.request
from pathlib import Path

PKG="qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape"
ROUTER=f"{PKG}.usls_046b_shared_multidex_live_event_router"
IDENT=f"{PKG}.usls_047c_batched_retry_safe_multidex_identity_resolver"
ECON=f"{PKG}.usls_048b_shared_universal_economic_normalizer"

WSOL="So11111111111111111111111111111111111111112"
JUPITER=os.getenv("QSB_JUPITER_ULTRA_URL","https://lite-api.jup.ag/ultra/v1")
TAKER=os.getenv("QSB_SOLANA_WALLET","MriyaNN8TMp6qRWjfr723PK7xgQK7yCt7Kg2v2PQu7X")
SIZES_SOL=tuple(float(x) for x in os.getenv("QSB_045_SIZES_SOL","0.01,0.025,0.05").split(",") if x.strip())
MAX_TOKENS=int(os.getenv("QSB_045_MAX_TOKENS","8"))
MIN_NET_BPS=float(os.getenv("QSB_045_MIN_NET_BPS","15"))
MODELED_COST_LAMPORTS=int(os.getenv("QSB_045_MODELED_COST_LAMPORTS","150000"))
PACE=float(os.getenv("QSB_045_PACE_SECONDS","0.12"))

def http_json(url,timeout=20,retries=3):
    last=None
    for i in range(retries):
        try:
            req=urllib.request.Request(url,headers={"accept":"application/json","user-agent":"qseries-qsb045/1.0"})
            with urllib.request.urlopen(req,timeout=timeout) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            last=e
            if i+1<retries:time.sleep(.35*(i+1))
    raise last

def order(input_mint,output_mint,amount,taker=TAKER,http=http_json):
    q=urllib.parse.urlencode({"inputMint":input_mint,"outputMint":output_mint,
                             "amount":str(int(amount)),"taker":taker,"slippageBps":"30"})
    j=http(f"{JUPITER}/order?{q}",20)
    if not isinstance(j,dict):raise RuntimeError("ORDER_NON_OBJECT")
    try:out=int(j.get("outAmount"))
    except Exception:raise RuntimeError("ORDER_OUT_AMOUNT_MISSING")
    if out<=0:raise RuntimeError("ORDER_OUT_NONPOSITIVE")
    return {"in":int(amount),"out":out,"transaction_present":bool(j.get("transaction")),
            "request_id_present":bool(j.get("requestId")),"router":j.get("router"),
            "priceImpactPct":j.get("priceImpactPct"),"raw":j}

def roundtrip(token,start_lamports,http=http_json):
    q1=order(WSOL,token,start_lamports,http=http)
    time.sleep(PACE)
    q2=order(token,WSOL,q1["out"],http=http)
    gross=q2["out"]-int(start_lamports)
    net=gross-MODELED_COST_LAMPORTS
    bps=net/int(start_lamports)*10000.0
    return {"token":token,"start_lamports":int(start_lamports),"token_raw":q1["out"],
            "end_lamports":q2["out"],"gross_lamports":gross,"modeled_cost_lamports":MODELED_COST_LAMPORTS,
            "net_lamports":net,"net_bps":bps,
            "transactions_present":q1["transaction_present"] and q2["transaction_present"],
            "leg1_router":q1["router"],"leg2_router":q2["router"],
            "qualified":bool(net>0 and bps>=MIN_NET_BPS and q1["transaction_present"] and q2["transaction_present"]),
            "leg1":q1,"leg2":q2}

async def capture():
    return await importlib.import_module(ROUTER).capture(seconds=3,max_rows=2600)

def _persist_router(root,d):
    p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/multidex_live_event_router.json"
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2),encoding="utf-8")

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
    live=asyncio.run(capture());rows=list((live or {}).get("rows") or [])
    slots=[]
    for x in rows:
        try:slots.append(int(x.get("slot")))
        except Exception:pass
    mx=max(slots) if slots else None
    _persist_router(root,live)
    _producer(IDENT,root)
    d=_producer(ECON,root)
    erows=(d or {}).get("exact_rows") or (d or {}).get("rows") or []
    cand=[]
    for x in erows:
        if not isinstance(x,dict) or x.get("venue")!="PUMP_SWAP":continue
        t=x.get("token_address")
        if not t or t==WSOL:continue
        try:slot=int(x.get("slot"))
        except Exception:continue
        if mx is not None and 0<=mx-slot<=4:
            cand.append((slot,t))
    out=[];seen=set()
    for slot,t in sorted(cand,reverse=True):
        if t not in seen:
            seen.add(t);out.append(t)
        if len(out)>=MAX_TOKENS:break
    return {"live_rows":len(rows),"max_slot":mx,"tokens":out}

def build(root,http=http_json):
    root=Path(root);src=fresh_tokens(root)
    print("[DISCOVERY] live_rows=%d max_slot=%s tokens=%d"%(src["live_rows"],src["max_slot"],len(src["tokens"])),flush=True)
    results=[];errors=[]
    for token in src["tokens"]:
        for sol in SIZES_SOL:
            start=int(round(sol*1e9))
            try:
                x=roundtrip(token,start,http=http);results.append(x)
                print("[ROUNDTRIP] token=%s size=%.3f SOL end=%.9f net=%+.9f SOL net_bps=%+.2f txs=%s QUALIFIED=%s"%(
                    token[:10],sol,x["end_lamports"]/1e9,x["net_lamports"]/1e9,x["net_bps"],
                    x["transactions_present"],x["qualified"]),flush=True)
            except Exception as e:
                errors.append({"token":token,"size_sol":sol,"error":f"{type(e).__name__}: {e}"})
                print("[QUOTE_ERROR] token=%s size=%.3f %s: %s"%(token[:10],sol,type(e).__name__,e),flush=True)
            time.sleep(PACE)
    results.sort(key=lambda x:x["net_bps"],reverse=True)
    qualified=[x for x in results if x["qualified"]]
    best=qualified[0] if qualified else (results[0] if results else None)
    if qualified:
        x=qualified[0]
        print("[BEST_QUALIFIED] token=%s size=%.3f net=%+.9f SOL net_bps=%+.2f"%(
            x["token"],x["start_lamports"]/1e9,x["net_lamports"]/1e9,x["net_bps"]),flush=True)
    elif best:
        print("[BEST_OBSERVED] token=%s net_bps=%+.2f NOT_QUALIFIED"%(best["token"],best["net_bps"]),flush=True)
    else:print("[NO_QUOTES]",flush=True)
    out={"revision":"QSB_045","source":src,"result_count":len(results),"qualified_count":len(qualified),
         "best":best,"qualified":qualified[:10],"errors":errors,
         "execution_authority":False,"atomic":False,
         "truth":"DIRECT_JUPITER_EXECUTABLE_ROUNDTRIP_HUNTER_NONATOMIC"}
    p=root/"runtime_state/qseries/qsb045_direct_jupiter_roundtrip/report.json"
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,indent=2),encoding="utf-8")
    return out
