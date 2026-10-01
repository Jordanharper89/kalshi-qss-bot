from __future__ import annotations
import asyncio,time,json
from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict

from meteora_dlmm import PoolState,quote
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import engine
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import persistent_profit_runtime as p
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.dex import raydium_cpmm_mriya_bridge as rc

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
MAX_AGE_MS=750.0
MAX_LEGS=4
PACE_SECONDS=0.90
RETRIES=6
OUT=Path("runtime_state/qseries/qarb_clean_bot/cpmm_connected_live_route_graph.json")
_LAST_RPC=0.0

def _pace():
    global _LAST_RPC
    now=time.monotonic()
    wait=PACE_SECONDS-(now-_LAST_RPC)
    if wait>0:time.sleep(wait)
    _LAST_RPC=time.monotonic()

def _retry(label,fn,*args):
    delay=1.0
    last=None
    for n in range(RETRIES):
        try:
            _pace()
            return fn(*args)
        except Exception as e:
            last=e
            if "429" not in str(e) and "Too Many Requests" not in str(e):
                raise
            print("[RPC_BACKOFF] %s attempt=%d delay=%.1fs error=%s"%(label,n+1,delay,e),flush=True)
            time.sleep(delay);delay=min(delay*2,8.0)
    raise last

def paced_account(addr):
    return _retry("account:"+addr[:10],c.account,addr)

@dataclass
class DLMMState:
    address:str
    token_x:str
    token_y:str
    decimals_x:int
    decimals_y:int
    lb_bytes:bytes
    arrays:list
    state:object
    last_live_ns:int=0

    def watched(self):
        return [self.address]+[x[1] for x in self.arrays]

    def rebuild(self):
        self.state=PoolState.from_accounts(
            self.lb_bytes,[x[2] for x in self.arrays],
            decimals_x=self.decimals_x,decimals_y=self.decimals_y,
            lb_pair_key=c.b58d(self.address),exhaustive=True)

def hydrate_dlmm_for_asset(asset):
    meta=_retry("discover_dlmm:"+asset[:10],c.discover_dlmm,asset)
    if not meta:return None
    if {meta["token_x"],meta["token_y"]}!={asset,c.WSOL}:return None
    lb,_=paced_account(meta["address"])
    arrays=_retry("dlmm_arrays:"+asset[:10],c.dlmm_arrays,meta["address"])
    d=DLMMState(meta["address"],meta["token_x"],meta["token_y"],
                int(meta["decimals_x"]),int(meta["decimals_y"]),
                lb,list(arrays),None,0)
    d.rebuild()
    return d

def dlmm_quote(d,input_mint,amount):
    if input_mint==d.token_x:swap_for_y=True
    elif input_mint==d.token_y:swap_for_y=False
    else:raise RuntimeError("DLMM_DIRECTION")
    q=quote(d.state,amount_in=int(amount),swap_for_y=swap_for_y,strict=True)
    if not getattr(q,"complete",False) or int(getattr(q,"remaining_in",0) or 0):
        raise RuntimeError("DLMM_PARTIAL")
    return int(q.amount_out)

@dataclass
class Edge:
    venue:str
    pool:str
    src:str
    dst:str
    quote_fn:object
    fresh_fn:object

def prepare(root):
    root=Path(root)
    desc=rc.discover(root)
    cstates=[]
    cp_seen={}
    for d in desc:
        try:
            s=rc.hydrate(d,paced_account)
            cstates.append((d,s))
            cp_seen[d.pool]={d.vault_a:0,d.vault_b:0}
            print("[CPMM_READY] pool=%s %s<->%s"%(d.pool[:12],d.token_a[:12],d.token_b[:12]),flush=True)
        except Exception as e:
            print("[CPMM_HYDRATE_HOLD] pool=%s %s:%s"%(d.pool[:12],type(e).__name__,e),flush=True)

    assets=sorted({x for d,_ in cstates for x in (d.token_a,d.token_b) if x!=c.WSOL})
    dlmms=[]
    for asset in assets:
        try:
            d=hydrate_dlmm_for_asset(asset)
            if d:
                dlmms.append(d)
                print("[DLMM_BRIDGE] asset=%s pool=%s pair=%s/%s"%(
                    asset[:12],d.address[:12],d.token_x[:12],d.token_y[:12]),flush=True)
            else:
                print("[DLMM_NO_WS0L_BRIDGE] asset=%s"%asset[:12],flush=True)
        except Exception as e:
            print("[DLMM_BRIDGE_HOLD] asset=%s %s:%s"%(asset[:12],type(e).__name__,e),flush=True)

    creg={}
    for i,(d,s) in enumerate(cstates):
        creg[d.vault_a]=(i,d);creg[d.vault_b]=(i,d)
    dreg={}
    for i,d in enumerate(dlmms):
        dreg[d.address]=(i,"POOL")
        for j,a in enumerate(d.arrays):dreg[a[1]]=(i,j)

    landing=engine.landing_cost_lamports()
    addresses=list(dict.fromkeys(list(creg)+list(dreg)))
    return {"landing":landing,"cstates":cstates,"cp_seen":cp_seen,"creg":creg,
            "dlmms":dlmms,"dreg":dreg,"addresses":addresses}

def _cp_fresh(state,d):
    ts=state["cp_seen"].get(d.pool,{})
    if not ts or any(not x for x in ts.values()):return False
    now=time.perf_counter_ns()
    return max((now-x)/1e6 for x in ts.values())<=MAX_AGE_MS

def _dlmm_fresh(d):
    return bool(d.last_live_ns) and (time.perf_counter_ns()-d.last_live_ns)/1e6<=MAX_AGE_MS

def edges(state):
    out=[]
    for d,s in state["cstates"]:
        out.append(Edge("RAYDIUM_CPMM",d.pool,d.token_a,d.token_b,
                        lambda amt,x=d,y=s:rc.quote(y,x.token_a,int(amt)),
                        lambda x=d:_cp_fresh(state,x)))
        out.append(Edge("RAYDIUM_CPMM",d.pool,d.token_b,d.token_a,
                        lambda amt,x=d,y=s:rc.quote(y,x.token_b,int(amt)),
                        lambda x=d:_cp_fresh(state,x)))
    for d in state["dlmms"]:
        out.append(Edge("METEORA_DLMM",d.address,d.token_x,d.token_y,
                        lambda amt,x=d:dlmm_quote(x,x.token_x,int(amt)),
                        lambda x=d:_dlmm_fresh(x)))
        out.append(Edge("METEORA_DLMM",d.address,d.token_y,d.token_x,
                        lambda amt,x=d:dlmm_quote(x,x.token_y,int(amt)),
                        lambda x=d:_dlmm_fresh(x)))
    return out

def cycles(es):
    by=defaultdict(list)
    for e in es:by[e.src].append(e)
    out=[]
    def dfs(asset,path,seen,pools):
        if path and asset==c.WSOL:
            if len(path)>=2 and any(x.venue=="RAYDIUM_CPMM" for x in path):
                out.append(tuple(path))
            return
        if len(path)>=MAX_LEGS:return
        for e in by.get(asset,()):
            if e.pool in pools:continue
            if e.dst!=c.WSOL and e.dst in seen:continue
            dfs(e.dst,path+[e],seen|({e.dst} if e.dst!=c.WSOL else set()),pools|{e.pool})
    dfs(c.WSOL,[],{c.WSOL},set())
    uniq={}
    for r in out:uniq[tuple((e.venue,e.pool,e.src,e.dst) for e in r)]=r
    return list(uniq.values())

def route_text(r):
    s=[r[0].src[:8]]
    for e in r:s.append("%s:%s"%(e.venue,e.dst[:8]))
    return " -> ".join(s)

def apply_event(state,ev):
    a=ev["address"];changed=False
    if a in state["creg"]:
        i,d=state["creg"][a];dd,s=state["cstates"][i]
        if rc.update(s,dd,a,ev["raw"],ev["received_ns"]):
            state["cp_seen"][dd.pool][a]=ev["received_ns"];changed=True
    if a in state["dreg"]:
        i,k=state["dreg"][a];d=state["dlmms"][i]
        if k=="POOL":d.lb_bytes=ev["raw"]
        else:
            arr=list(d.arrays);old=arr[k];arr[k]=(old[0],old[1],ev["raw"]);d.arrays=arr
        try:
            d.rebuild();d.last_live_ns=ev["received_ns"];changed=True
        except Exception:pass
    return changed

def evaluate(state,routes,received_ns):
    age=(time.perf_counter_ns()-int(received_ns))/1e6
    if age>MAX_AGE_MS:return None
    best=None
    for r in routes:
        if not all(e.fresh_fn() for e in r):continue
        for size in (0.01,0.025,0.05,0.1,0.18,0.28,0.5):
            start=int(size*1e9);amt=start
            try:
                for e in r:
                    amt=int(e.quote_fn(amt))
                    if amt<=0:raise RuntimeError("NONPOSITIVE")
            except Exception:continue
            net=amt-start-int(state["landing"]);bps=net/start*10000.0
            row={"size_sol":size,"net_sol":net/1e9,"net_bps":bps,"age_ms":age,
                 "route":route_text(r),"qualified":bps>=engine.MIN_NET_BPS,
                 "execution_authority":False}
            if best is None or row["net_sol"]>best["net_sol"]:best=row
    return best

async def serve(root,seconds=120.0):
    state=prepare(Path(root));es=edges(state);rs=cycles(es)
    print("[QARB-049C] CPMM-CONNECTED LIVE ROUTE GRAPH",flush=True)
    print("[GRAPH] cpmm_pools=%d dlmm_wsol_bridges=%d edges=%d cpmm_cycles=%d addresses=%d"%(
        len(state["cstates"]),len(state["dlmms"]),len(es),len(rs),len(state["addresses"])),flush=True)
    for r in rs:print("[CPMM_CYCLE] "+route_text(r),flush=True)
    if not state["cstates"]:raise SystemExit("[HOLD] CPMM hydration still unavailable")
    if not rs:raise SystemExit("[HOLD] no exact CPMM->DLMM->WSOL connectivity yet")

    counters={"acks":0,"notifications":0,"priced_events":0,"observed_only_events":0,"signals":0,
              "event_errors":0,"queue_drops":0,"connections":0,"reconnects":0,
              "rate_limit_disconnects":0,"last_ws_error":None,"lat":[],"best":None}
    shards=p.m._shards(state["addresses"]);q=asyncio.Queue(maxsize=p.QUEUE_MAX);stop=asyncio.Event()
    workers=[asyncio.create_task(p._worker(i,s,q,counters,stop)) for i,s in enumerate(shards)]
    started=time.monotonic();last=started
    try:
        while time.monotonic()-started<float(seconds):
            try:ev=await asyncio.wait_for(q.get(),timeout=.25)
            except asyncio.TimeoutError:ev=None
            if ev and apply_event(state,ev):
                counters["priced_events"]+=1
                row=evaluate(state,rs,ev["received_ns"])
                if row:
                    counters["best"]=row if counters["best"] is None or row["net_sol"]>counters["best"]["net_sol"] else counters["best"]
                    if row["qualified"]:
                        counters["signals"]+=1
                        print("[CPMM_LIVE_SIGNAL] size=%.6f net=%+.9f bps=%+.2f age_ms=%.3f route=%s"%(
                            row["size_sol"],row["net_sol"],row["net_bps"],row["age_ms"],row["route"]),flush=True)
            now=time.monotonic()
            if now-last>=10:
                print("[HEARTBEAT] uptime_s=%d notifications=%d priced_events=%d signals=%d"%(
                    int(now-started),counters["notifications"],counters["priced_events"],counters["signals"]),flush=True)
                last=now
    finally:
        stop.set()
        for w in workers:w.cancel()
        await asyncio.gather(*workers,return_exceptions=True)

    payload={"cpmm_pools":len(state["cstates"]),"dlmm_wsol_bridges":len(state["dlmms"]),
             "cpmm_cycles":len(rs),"signals":counters["signals"],"best":counters["best"],
             "execution_authority":False}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    print("[RESULT] "+json.dumps(payload,sort_keys=True),flush=True)
    print("[MODE] PAPER_OBSERVATION=True execution_authority=FALSE",flush=True)
    return payload

def main(argv=None):
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument("--seconds",type=float,default=120.0);a=ap.parse_args(argv)
    return asyncio.run(serve(Path.cwd(),a.seconds))
if __name__=="__main__":main()
