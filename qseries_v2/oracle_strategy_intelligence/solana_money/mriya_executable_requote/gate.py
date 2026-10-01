from __future__ import annotations
import json,os,urllib.parse,urllib.request
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_multidex_route_engine.engine import build as build_routes

JUPITER_ULTRA=os.getenv("QSB_JUPITER_ULTRA_URL","https://lite-api.jup.ag/ultra/v1")
DEFAULT_TAKER=os.getenv("QSB_SOLANA_WALLET","MriyaNN8TMp6qRWjfr723PK7xgQK7yCt7Kg2v2PQu7X")
DEFAULT_START_RAW=int(os.getenv("QSB_042_START_RAW","10000000"))  # 0.01 WSOL when WSOL is 9 decimals
MIN_NET_BPS=float(os.getenv("QSB_042_MIN_NET_BPS","20"))

def http_json(url,timeout=20):
    req=urllib.request.Request(url,headers={"accept":"application/json","user-agent":"qseries-qsb042/1.0"})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        return json.loads(r.read().decode())

def ultra_order(input_mint,output_mint,amount,taker=DEFAULT_TAKER,http=http_json):
    q=urllib.parse.urlencode({
      "inputMint":input_mint,"outputMint":output_mint,
      "amount":str(int(amount)),"taker":taker,"slippageBps":"50",
    })
    j=http(f"{JUPITER_ULTRA}/order?{q}",20)
    if not isinstance(j,dict): raise RuntimeError("JUPITER_NON_OBJECT")
    out=j.get("outAmount")
    tx=j.get("transaction")
    rid=j.get("requestId")
    if out is None: raise RuntimeError("JUPITER_OUT_AMOUNT_MISSING:"+json.dumps(j)[:300])
    try: out=int(out)
    except Exception: raise RuntimeError("JUPITER_OUT_AMOUNT_INVALID")
    if out<=0: raise RuntimeError("JUPITER_OUT_AMOUNT_NONPOSITIVE")
    return {
      "inputMint":input_mint,"outputMint":output_mint,"inAmount":int(amount),"outAmount":out,
      "transaction_present":bool(tx),"requestId_present":bool(rid),
      "router":j.get("router"),"priceImpactPct":j.get("priceImpactPct"),
      "raw":j,
    }

def requote_route(route,start_raw=DEFAULT_START_RAW,taker=DEFAULT_TAKER,http=http_json):
    path=list(route.get("path") or [])
    if len(path) not in (3,4): raise RuntimeError("UNSUPPORTED_ROUTE_LENGTH")
    amount=int(start_raw)
    legs=[]
    for a,b in zip(path,path[1:]):
        q=ultra_order(a,b,amount,taker,http)
        legs.append(q)
        amount=q["outAmount"]
    if path[0]!=path[-1]: raise RuntimeError("ROUTE_NOT_CLOSED")
    net=amount-int(start_raw)
    bps=(net/int(start_raw))*10000.0
    txs=all(x["transaction_present"] for x in legs)
    return {
      "start_raw":int(start_raw),"end_raw":amount,"net_raw":net,"net_bps":bps,
      "legs":legs,"all_transactions_present":txs,
      "qualified":bool(txs and bps>=MIN_NET_BPS),
      "atomic_composer_present":False,
      "execution_authority":False,
    }

def build(root,http=http_json):
    root=Path(root)
    rr=build_routes(root)
    routes=list(rr.get("routes") or [])
    results=[];errors=[]
    for r in routes[:8]:
        try:
            x=requote_route(r,http=http)
            x["route"]=r
            results.append(x)
            print("[REQUOTE] legs=%d venues=%s net_bps=%+.2f txs=%s QUALIFIED=%s"%(
              r["legs"]," -> ".join(r["venues"]),x["net_bps"],x["all_transactions_present"],x["qualified"]),flush=True)
        except Exception as e:
            errors.append({"route":r,"error":f"{type(e).__name__}: {e}"})
            print("[REQUOTE_ERROR] %s: %s"%(type(e).__name__,e),flush=True)
    results.sort(key=lambda x:x["net_bps"],reverse=True)
    best=results[0] if results else None
    out={
      "revision":"QSB_042","route_count":len(routes),"requote_count":len(results),
      "best":best,"results":results,"errors":errors,
      "execution_authority":False,
      "atomic_composer_present":False,
      "truth":"EXECUTABLE_ULTRA_LEG_TRANSACTIONS_REQUOTED_BUT_NOT_ATOMICALLY_COMPOSED",
      "next_boundary":"VENUE_NATIVE_ATOMIC_MULTI_LEG_COMPOSER"
    }
    p=root/"runtime_state/qseries/qsb042_executable_requote/report.json"
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(out,indent=2),encoding="utf-8")
    if best:
        print("[BEST_EXECUTABLE_REQUOTE] net_bps=%+.2f txs=%s QUALIFIED=%s"%(
          best["net_bps"],best["all_transactions_present"],best["qualified"]),flush=True)
    else:
        print("[NO_EXECUTABLE_REQUOTE]",flush=True)
    return out
