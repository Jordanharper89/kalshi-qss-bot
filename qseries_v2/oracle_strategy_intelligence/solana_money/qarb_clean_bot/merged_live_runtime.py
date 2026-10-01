from __future__ import annotations
import asyncio,base64,json,os,time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter_ns

from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import engine
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as pd
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.dex import raydium_cpmm_mriya_bridge as rc
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.certified_roles import load as load_roles

WS_URL=os.getenv("SOLANA_WS_URL","").strip() or c.RPC.replace("https://","wss://",1).replace("http://","ws://",1)
SHARD_SIZE=int(os.getenv("QARB_WS_SHARD_SIZE","48"))
SUB_DELAY_MS=float(os.getenv("QARB_WS_SUBSCRIBE_DELAY_MS","40"))
STAGGER_SECONDS=float(os.getenv("QARB_WS_SHARD_STAGGER_SECONDS","2.25"))
MAX_AGE_MS=float(os.getenv("QARB_MAX_EVENT_TO_DECISION_MS","750"))
MIN_NET_BPS=float(os.getenv("QARB_MIN_NET_BPS","20"))
MAX_ACCOUNTS=int(os.getenv("QARB_MAX_ACCOUNTS","256"))
SIZES=pd.SIZES

@dataclass
class Endpoint:
    venue:str
    token:str
    pool:str
    buy_fn:object
    sell_fn:object

def _age_ms(ns): return (perf_counter_ns()-int(ns))/1e6

def _pump_ep(p):
    return Endpoint("PUMPSWAP",p.token,p.pump_pool,
                    lambda x: pd._pump_buy(p,int(x)),
                    lambda x: pd._pump_sell(p,int(x)))

def _dlmm_ep(p):
    return Endpoint("METEORA_DLMM",p.token,p.meteora_pool,
                    lambda x: pd._dlmm_quote(p,int(x),c.WSOL),
                    lambda x: pd._dlmm_quote(p,int(x),p.token))

def _cpmm_ep(d,s):
    if c.WSOL not in (d.token_a,d.token_b): return None
    token=d.token_b if d.token_a==c.WSOL else d.token_a
    return Endpoint("RAYDIUM_CPMM",token,d.pool,
                    lambda x: rc.quote(s,c.WSOL,int(x)),
                    lambda x: rc.quote(s,token,int(x)))

def evaluate_token(token,endpoints,landing,received_ns):
    if _age_ms(received_ns)>MAX_AGE_MS: return None
    best=None
    t0=perf_counter_ns()
    for size in SIZES:
        start=int(size*1e9)
        for buy in endpoints:
            for sell in endpoints:
                if buy.venue==sell.venue: continue
                try:
                    mid=int(buy.buy_fn(start))
                    end=int(sell.sell_fn(mid))
                except Exception:
                    continue
                if mid<=0 or end<=0: continue
                net=end-start-int(landing)
                bps=net/start*10000.0
                row={"token":token,"buy_venue":buy.venue,"sell_venue":sell.venue,
                     "buy_pool":buy.pool,"sell_pool":sell.pool,"size_sol":size,
                     "end_sol":end/1e9,"net_sol":net/1e9,"net_bps":bps,
                     "event_to_decision_ms":_age_ms(received_ns),
                     "compute_us":(perf_counter_ns()-t0)/1e3,
                     "qualified":bps>=MIN_NET_BPS and _age_ms(received_ns)<=MAX_AGE_MS,
                     "execution_authority":False}
                if best is None or row["net_sol"]>best["net_sol"]: best=row
    return best

def _parse(msg,submap):
    if not isinstance(msg,dict) or msg.get("method")!="accountNotification": return None
    p=msg.get("params") or {};a=submap.get(p.get("subscription"))
    if not a: return None
    r=p.get("result") or {};v=r.get("value") or {};d=v.get("data")
    if not isinstance(d,list) or not d: return None
    return {"address":a,"slot":int((r.get("context") or {}).get("slot") or 0),
            "raw":base64.b64decode(d[0]),"received_ns":perf_counter_ns()}

def prepare(root):
    landing=engine.landing_cost_lamports()
    pairs,_=pd.prepare_pairs(root)
    preg={};eps=defaultdict(list)
    for i,p in enumerate(pairs):
        preg[p.pump_base_vault]=(i,"PUMP_BASE");preg[p.pump_quote_vault]=(i,"PUMP_QUOTE")
        preg[p.meteora_pool]=(i,"DLMM_POOL")
        for j,a in enumerate(p.arrays): preg[a[1]]=(i,f"DLMM_ARRAY_{j}")
        eps[p.token].extend((_pump_ep(p),_dlmm_ep(p)))

    cstates=[];creg={}
    for d in rc.discover(root):
        try:
            s=rc.hydrate(d,c.account);i=len(cstates);cstates.append((d,s))
            creg[d.vault_a]=(i,d);creg[d.vault_b]=(i,d)
            ep=_cpmm_ep(d,s)
            if ep: eps[ep.token].append(ep)
        except Exception as exc:
            print("[CPMM_WARM_SKIP] pool=%s %s:%s"%(d.pool[:10],type(exc).__name__,exc),flush=True)

    observed={}
    for r in load_roles(root):
        if r.venue in ("RAYDIUM_CLMM","ORCA","ORCA_WHIRLPOOL","METEORA_DAMM","METEORA_DAMM_V2"):
            for a in r.accounts: observed.setdefault(a,set()).add(r.venue)

    addrs=[]
    for a in list(preg)+list(creg)+list(observed):
        if a not in addrs: addrs.append(a)
    return {"landing":landing,"pairs":pairs,"preg":preg,"cstates":cstates,"creg":creg,
            "observed":observed,"eps":eps,"addresses":addrs[:MAX_ACCOUNTS]}

def capability(s):
    obs=set()
    for v in s["observed"].values(): obs.update(v)
    return {
      "PUMPSWAP":{"priced_live":bool(s["pairs"])},
      "METEORA_DLMM":{"priced_live":bool(s["pairs"])},
      "RAYDIUM_CPMM":{"priced_live":bool(s["cstates"])},
      "RAYDIUM_CLMM":{"observed_live":"RAYDIUM_CLMM" in obs,"priced_live":False},
      "ORCA_WHIRLPOOL":{"observed_live":bool({"ORCA","ORCA_WHIRLPOOL"}&obs),"priced_live":False},
      "METEORA_DAMM_V2":{"observed_live":bool({"METEORA_DAMM","METEORA_DAMM_V2"}&obs),"priced_live":False},
    }

def _req(addrs):
    return [{"jsonrpc":"2.0","id":i+1,"method":"accountSubscribe",
             "params":[a,{"encoding":"base64","commitment":"processed"}]} for i,a in enumerate(addrs)]

def _shards(addrs): return [addrs[i:i+SHARD_SIZE] for i in range(0,len(addrs),SHARD_SIZE)]

async def _worker(i,addrs,seconds,q):
    import websockets
    await asyncio.sleep(i*STAGGER_SECONDS)
    res={"subscriptions":len(addrs),"acks":0,"notifications":0,"rate_limited":False,"error":None}
    by_id={n+1:a for n,a in enumerate(addrs)};submap={}
    deadline=time.monotonic()+seconds
    try:
        async with websockets.connect(WS_URL,ping_interval=20,ping_timeout=20,close_timeout=3,max_size=8_000_000) as ws:
            for r in _req(addrs):
                await ws.send(json.dumps(r,separators=(",",":")))
                if SUB_DELAY_MS>0: await asyncio.sleep(SUB_DELAY_MS/1000)
            while time.monotonic()<deadline:
                try: raw=await asyncio.wait_for(ws.recv(),timeout=min(1.0,max(.05,deadline-time.monotonic())))
                except asyncio.TimeoutError: continue
                m=json.loads(raw)
                if "id" in m and isinstance(m.get("result"),int):
                    a=by_id.get(int(m["id"]))
                    if a: submap[int(m["result"])]=a;res["acks"]+=1
                    continue
                ev=_parse(m,submap)
                if ev: res["notifications"]+=1;await q.put(ev)
    except Exception as exc:
        txt=f"{type(exc).__name__}: {exc}";res["error"]=txt
        lo=txt.lower();res["rate_limited"]="1013" in lo or "rate limit" in lo or "too many subscriptions" in lo
    return res

async def run(root,seconds=30.0):
    s=prepare(root);caps=capability(s)
    print("[CAPABILITY] "+json.dumps(caps,sort_keys=True),flush=True)
    print("[LIVE] accounts=%d shards=%d priced_tokens=%d"%(len(s["addresses"]),len(_shards(s["addresses"])),len(s["eps"])),flush=True)
    q=asyncio.Queue()
    tasks=[asyncio.create_task(_worker(i,x,seconds,q)) for i,x in enumerate(_shards(s["addresses"]))]
    priced=observed=signals=0;best=None;lat=[]
    while any(not t.done() for t in tasks) or not q.empty():
        try: ev=await asyncio.wait_for(q.get(),timeout=.25)
        except asyncio.TimeoutError: continue
        a=ev["address"];tokens=set();did=False
        if a in s["preg"]:
            i,k=s["preg"][a];p=s["pairs"][i]
            try:
                if pd.apply_account_event(p,k,a,ev["raw"],ev["slot"],ev["received_ns"]):
                    tokens.add(p.token);did=True
            except Exception: pass
        if a in s["creg"]:
            i,d=s["creg"][a];dd,st=s["cstates"][i]
            try:
                if rc.update(st,dd,a,ev["raw"],ev["received_ns"]):
                    ep=_cpmm_ep(dd,st)
                    if ep: tokens.add(ep.token);did=True
            except Exception: pass
        if did:
            priced+=1
            for token in tokens:
                r=evaluate_token(token,s["eps"].get(token,()),s["landing"],ev["received_ns"])
                if not r: continue
                lat.append(r["event_to_decision_ms"])
                if best is None or r["net_sol"]>best["net_sol"]: best=r
                if r["qualified"]:
                    signals+=1
                    print("[HOT_SIGNAL] token=%s buy=%s sell=%s size=%.6f net=%+.9f SOL bps=%+.2f event_to_decision_ms=%.3f"%(
                        token[:10],r["buy_venue"],r["sell_venue"],r["size_sol"],r["net_sol"],r["net_bps"],r["event_to_decision_ms"]),flush=True)
        elif a in s["observed"]:
            observed+=1
    rr=await asyncio.gather(*tasks)
    lat.sort();p99=lat[min(len(lat)-1,int(len(lat)*.99))] if lat else None
    return {"subscriptions":sum(x["subscriptions"] for x in rr),"acks":sum(x["acks"] for x in rr),
            "notifications":sum(x["notifications"] for x in rr),"priced_events":priced,
            "observed_only_events":observed,"signals":signals,"best":best,
            "connections":len(rr),"rate_limited_connections":sum(1 for x in rr if x["rate_limited"]),
            "p99_event_to_decision_ms":p99,"errors":[x["error"] for x in rr if x["error"]],
            "capability":caps,"execution_authority":False}

def main(argv=None):
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument("--seconds",type=float,default=30.0);a=ap.parse_args(argv)
    print("[QARB-021] MERGED SIX-DEX LIVE PROFIT RUNTIME",flush=True)
    print("[PRICED] PumpSwap | Meteora DLMM | Raydium CPMM",flush=True)
    print("[OBSERVED FAIL-CLOSED] Raydium CLMM | Orca Whirlpool | Meteora DAMM V2",flush=True)
    print("[RATE_LIMIT] sharded processed accountSubscribe",flush=True)
    print("[GATE] event_to_decision <=750ms",flush=True)
    r=asyncio.run(run(Path.cwd(),a.seconds))
    print("[RESULT] "+json.dumps(r,sort_keys=True),flush=True)
    print("[MODE] scanner/handoff only execution_authority=FALSE",flush=True)

if __name__=="__main__": main()
