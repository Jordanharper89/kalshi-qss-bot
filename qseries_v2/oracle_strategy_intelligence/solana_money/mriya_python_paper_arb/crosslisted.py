from __future__ import annotations
import asyncio,json,os,time
from collections import Counter
from pathlib import Path
from . import core
from . import scanner as prior

CAPTURE_SECONDS=5
MAX_INTERSECTIONS=6
SIZES_SOL=(0.03,0.05,0.10,0.20,0.35,0.50,0.75,1.00)
MIN_NET_BPS=15.0
MAX_SLOT_SPREAD=4
TX_COST_SOL=0.0001

def _artifact(root,name):
    return Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"/name

def live_pumpswap_identities(root,capture_seconds=CAPTURE_SECONDS):
    from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_046b_shared_multidex_live_event_router import capture
    from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_047c_batched_retry_safe_multidex_identity_resolver import resolve
    ret=asyncio.run(capture(seconds=int(capture_seconds),max_rows=1600))
    rows=list(ret.get("rows") or [])
    base=_artifact(root,"multidex_live_event_router.json")
    base.parent.mkdir(parents=True,exist_ok=True)
    base.write_text(json.dumps(ret,indent=2),encoding="utf-8")
    active=Counter()
    for r in rows:
        if r.get("venue")!="PUMP_SWAP":continue
        ev=r.get("event") or {}
        pool=ev.get("pool") or r.get("pool") or r.get("market_address")
        if pool:active[str(pool)]+=1
    if not active:
        return {"router_rows":len(rows),"active_pools":0,
                "resolver_identity_rows":0,"active_overlap":0,"identities":[]}
    resolved=resolve(Path(root))
    ids=list((resolved or {}).get("identity_rows") or (resolved or {}).get("rows") or (resolved or {}).get("identities") or [])
    resolver_identity_rows=len(ids)
    out=[]
    for x in ids:
        if x.get("venue")!="PUMP_SWAP" or x.get("identity_state")!="EXACT":continue
        pool=str(x.get("pool") or "")
        if pool not in active:continue
        base_mint=str(x.get("base_mint") or "");quote_mint=str(x.get("quote_mint") or "")
        if quote_mint==core.WSOL and base_mint and base_mint!=core.WSOL:
            token=base_mint;token_dec=x.get("base_decimals");wsol_dec=x.get("quote_decimals")
        elif base_mint==core.WSOL and quote_mint and quote_mint!=core.WSOL:
            token=quote_mint;token_dec=x.get("quote_decimals");wsol_dec=x.get("base_decimals")
        else:continue
        out.append({"pump_pool":pool,"token":token,"token_decimals":int(token_dec),
                    "wsol_decimals":int(wsol_dec),"activity":int(active[pool])})
    out.sort(key=lambda z:z["activity"],reverse=True)
    return {"router_rows":len(rows),"active_pools":len(active),
            "resolver_identity_rows":resolver_identity_rows,
            "active_overlap":len(out),"identities":out}

def _rows(j):
    if isinstance(j,list):return j
    if isinstance(j,dict):
        for k in ("data","pools","items","results"):
            if isinstance(j.get(k),list):return j[k]
    return []

def _mint(o):
    if isinstance(o,str):return o
    if isinstance(o,dict):
        for k in ("address","mint","token_address"):
            if isinstance(o.get(k),str):return o[k]
    return ""

def _dec(o):
    if isinstance(o,dict):
        for k in ("decimals","decimal"):
            try:return int(o[k])
            except Exception:pass
    return None

def meteora_matches(token,http=core.http_json):
    j=http(f"{core.METEORA_API}/pools?page=1&page_size=100&query={token}")
    found=[]
    for x in _rows(j):
        tx=x.get("token_x") or x.get("tokenX") or {}
        ty=x.get("token_y") or x.get("tokenY") or {}
        mx,my=_mint(tx),_mint(ty)
        if {mx,my}!={core.WSOL,token}:continue
        addr=x.get("address") or x.get("pool_address") or x.get("pubkey")
        dx,dy=_dec(tx),_dec(ty)
        if not addr or dx is None or dy is None:continue
        score=0.0
        for k in ("tvl","liquidity","liquidity_usd"):
            try:score=max(score,float(x.get(k) or 0))
            except Exception:pass
        found.append({"address":str(addr),"token_x":mx,"token_y":my,
                      "decimals_x":dx,"decimals_y":dy,"token":token,"score":score})
    found.sort(key=lambda z:z["score"],reverse=True)
    return found

def crosslisted(root,http=core.http_json,capture_seconds=CAPTURE_SECONDS,max_intersections=MAX_INTERSECTIONS):
    p=live_pumpswap_identities(root,capture_seconds)
    pairs=[]
    seen=set()
    for ident in p["identities"]:
        tok=ident["token"]
        if tok in seen:continue
        seen.add(tok)
        try:ms=meteora_matches(tok,http)
        except Exception:continue
        if not ms:continue
        pairs.append({"token":tok,"pump_pool":ident["pump_pool"],"pump_activity":ident["activity"],
                      "meteora":ms[0]})
        if len(pairs)>=int(max_intersections):break
    return p,pairs

def optimize_pair(root,pair,http=core.http_json,rpc_fn=core.rpc):
    rpc_url=os.getenv("SOLANA_RPC_URL",core.DEFAULT_RPC)
    meta=pair["meteora"]
    # Hydrate only after cross-list is proven.
    state=prior.pool_state(rpc_url,meta)
    best=None;all_rows=[]
    for size in SIZES_SOL:
        for fn in (prior.direction_a,prior.direction_b):
            try:
                x=fn(rpc_url,state,meta,size,http,rpc_fn)
                x["pump_pool"]=pair["pump_pool"];x["pump_activity"]=pair["pump_activity"]
                all_rows.append(x)
                if best is None or x["net_bps"]>best["net_bps"]:best=x
            except Exception as e:
                all_rows.append({"direction":fn.__name__,"token":pair["token"],"pool":meta["address"],
                                 "pump_pool":pair["pump_pool"],"start_sol":size,
                                 "error":f"{type(e).__name__}: {e}","paper_trade":False})
    return best,all_rows

def scan(root,http=core.http_json,rpc_fn=core.rpc,capture_seconds=CAPTURE_SECONDS,max_intersections=MAX_INTERSECTIONS):
    pump,pairs=crosslisted(root,http,capture_seconds,max_intersections)
    print("[LIVE_PUMPSWAP] router_rows=%d active_pools=%d resolver_identity_rows=%d active_wsol_overlap=%d"%(
      pump["router_rows"],pump["active_pools"],pump.get("resolver_identity_rows",0),
      pump.get("active_overlap",len(pump["identities"]))),flush=True)
    print("[CROSSLIST] pump_meteora_pairs=%d"%len(pairs),flush=True)
    results=[];best=None
    for i,pair in enumerate(pairs,1):
        print("[PAIR %d/%d] token=%s pump_pool=%s meteora_pool=%s pump_activity=%d"%(
          i,len(pairs),pair["token"],pair["pump_pool"],pair["meteora"]["address"],pair["pump_activity"]),flush=True)
        try:b,rows=optimize_pair(root,pair,http,rpc_fn)
        except Exception as e:
            print("[PAIR_ERROR] token=%s %s: %s"%(pair["token"],type(e).__name__,e),flush=True)
            continue
        results.extend(rows)
        if b:
            print("[PAIR_BEST] dir=%s size=%.6f end=%.9f net=%+.9f bps=%+.2f fresh=%s PAPER_TRADE=%s"%(
              b["direction"],b["start_sol"],b["end_sol"],b["net_sol"],b["net_bps"],b["fresh"],
              "YES" if b["paper_trade"] else "NO"),flush=True)
            if best is None or b["net_bps"]>best["net_bps"]:best=b
        time.sleep(.35)
    out={"revision":"QSB_038D","live_pumpswap":pump,"crosslisted_pairs":pairs,
         "quotes":results,"best":best,"execution_authority":False}
    rp=Path(root)/"runtime_state/qseries/qsb038d_crosslisted_atomic_arb/report.json"
    rp.parent.mkdir(parents=True,exist_ok=True);rp.write_text(json.dumps(out,indent=2),encoding="utf-8")
    return out
