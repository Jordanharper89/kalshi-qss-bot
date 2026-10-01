from __future__ import annotations
import asyncio,time,json
from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import merged_live_runtime as m
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import persistent_profit_runtime as p
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_048_dynamic_multivenue_state_probe as dyn

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
MAX_LEGS=4
MAX_AGE_MS=750.0
OUT=Path("runtime_state/qseries/qarb_clean_bot/live_multibase_asset_graph.json")

@dataclass
class Edge:
    venue:str
    pool:str
    src:str
    dst:str
    quote:object

def build_edges(state):
    edges=[]
    for pair in state.get("pairs",()):
        edges.append(Edge("PUMPSWAP",pair.pump_pool,m.c.WSOL,pair.token,
                          lambda amt,x=pair:m.pd._pump_buy(x,int(amt))))
        edges.append(Edge("PUMPSWAP",pair.pump_pool,pair.token,m.c.WSOL,
                          lambda amt,x=pair:m.pd._pump_sell(x,int(amt))))
        edges.append(Edge("METEORA_DLMM",pair.meteora_pool,m.c.WSOL,pair.token,
                          lambda amt,x=pair:m.pd._dlmm_quote(x,int(amt),m.c.WSOL)))
        edges.append(Edge("METEORA_DLMM",pair.meteora_pool,pair.token,m.c.WSOL,
                          lambda amt,x=pair:m.pd._dlmm_quote(x,int(amt),x.token)))
    for desc,state0 in state.get("cstates",()):
        edges.append(Edge("RAYDIUM_CPMM",desc.pool,desc.token_a,desc.token_b,
                          lambda amt,d=desc,s=state0:m.rc.quote(s,d.token_a,int(amt))))
        edges.append(Edge("RAYDIUM_CPMM",desc.pool,desc.token_b,desc.token_a,
                          lambda amt,d=desc,s=state0:m.rc.quote(s,d.token_b,int(amt))))
    return edges

def enumerate_cycles(edges,max_legs=MAX_LEGS):
    by=defaultdict(list)
    for e in edges:by[e.src].append(e)
    out=[]
    def dfs(asset,path,seen_assets,used_pools):
        if len(path)>=2 and asset==m.c.WSOL:
            if len({x.venue for x in path})>=2:
                out.append(tuple(path))
            return
        if len(path)>=max_legs:return
        for e in by.get(asset,()):
            if e.pool in used_pools:continue
            if e.dst==m.c.WSOL:
                if len(path)+1>=2:
                    dfs(e.dst,path+[e],seen_assets,used_pools|{e.pool})
                continue
            if e.dst in seen_assets:continue
            dfs(e.dst,path+[e],seen_assets|{e.dst},used_pools|{e.pool})
    dfs(m.c.WSOL,[],{m.c.WSOL},set())
    uniq={}
    for r in out:
        k=tuple((x.venue,x.pool,x.src,x.dst) for x in r);uniq[k]=r
    return list(uniq.values())

def _route_text(route):
    parts=[route[0].src[:8]]
    for e in route:parts.append("%s:%s"%(e.venue,e.dst[:8]))
    return " -> ".join(parts)

def evaluate(state,edges,received_ns):
    age=(time.perf_counter_ns()-int(received_ns))/1e6
    if age>MAX_AGE_MS:return None
    cycles=enumerate_cycles(edges)
    best=None
    for size in m.SIZES:
        start=int(float(size)*1e9)
        for route in cycles:
            amt=start
            try:
                for e in route:
                    amt=int(e.quote(amt))
                    if amt<=0:raise RuntimeError("NONPOSITIVE_QUOTE")
            except Exception:
                continue
            net=amt-start-int(state["landing"])
            bps=net/start*10000.0
            row={"size_sol":float(size),"start_sol":start/1e9,"end_sol":amt/1e9,
                 "net_sol":net/1e9,"net_bps":bps,"event_to_decision_ms":age,
                 "legs":[{"venue":e.venue,"pool":e.pool,"src":e.src,"dst":e.dst} for e in route],
                 "route_text":_route_text(route),
                 "contains_cpmm":any(e.venue=="RAYDIUM_CPMM" for e in route),
                 "qualified":bool(bps>=m.MIN_NET_BPS and age<=MAX_AGE_MS),
                 "execution_authority":False}
            if best is None or row["net_sol"]>best["net_sol"]:best=row
    return best

def apply_event(state,ev):
    a=ev["address"];changed=False
    if a in state["preg"]:
        i,k=state["preg"][a];pair=state["pairs"][i]
        try:
            changed=bool(m.pd.apply_account_event(pair,k,a,ev["raw"],ev["slot"],ev["received_ns"])) or changed
        except Exception:pass
    if a in state["creg"]:
        i,d=state["creg"][a];dd,st=state["cstates"][i]
        try:
            changed=bool(m.rc.update(st,dd,a,ev["raw"],ev["received_ns"])) or changed
        except Exception:pass
    return changed

async def serve(root,seconds=120.0):
    root=Path(root)
    state=dyn.prepare_multivenue(root)
    edges=build_edges(state);cycles=enumerate_cycles(edges)
    assets=sorted({e.src for e in edges}|{e.dst for e in edges})
    cpmm=sum(e.venue=="RAYDIUM_CPMM" for e in edges)
    cpmm_cycles=sum(any(e.venue=="RAYDIUM_CPMM" for e in r) for r in cycles)

    print("[QARB-049B] LIVE MULTI-BASE ASSET GRAPH",flush=True)
    print("[GRAPH] assets=%d directed_edges=%d cycles=%d cpmm_edges=%d cpmm_cycles=%d max_legs=%d"%(
        len(assets),len(edges),len(cycles),cpmm,cpmm_cycles,MAX_LEGS),flush=True)
    for r in cycles[:30]:print("[CYCLE] "+_route_text(r),flush=True)

    c={"acks":0,"notifications":0,"priced_events":0,"observed_only_events":0,"signals":0,
       "event_errors":0,"queue_drops":0,"connections":0,"reconnects":0,
       "rate_limit_disconnects":0,"last_ws_error":None,"lat":[],"best":None}
    shards=m._shards(state["addresses"]);q=asyncio.Queue(maxsize=p.QUEUE_MAX);stop=asyncio.Event()
    workers=[asyncio.create_task(p._worker(i,s,q,c,stop)) for i,s in enumerate(shards)]
    started=time.monotonic();last=started
    try:
        while time.monotonic()-started<float(seconds):
            try:ev=await asyncio.wait_for(q.get(),timeout=.25)
            except asyncio.TimeoutError:ev=None
            if ev and apply_event(state,ev):
                c["priced_events"]+=1
                row=evaluate(state,edges,ev["received_ns"])
                if row:
                    c["lat"].append(row["event_to_decision_ms"])
                    if c["best"] is None or row["net_sol"]>c["best"]["net_sol"]:c["best"]=row
                    if row["qualified"]:
                        c["signals"]+=1
                        print("[MULTIBASE_SIGNAL] size=%.6f net=%+.9f bps=%+.2f age_ms=%.3f cpmm=%s route=%s"%(
                            row["size_sol"],row["net_sol"],row["net_bps"],row["event_to_decision_ms"],
                            row["contains_cpmm"],row["route_text"]),flush=True)
            now=time.monotonic()
            if now-last>=10:
                best="None" if c["best"] is None else "%+.9f_SOL %+.2f_bps %s"%(c["best"]["net_sol"],c["best"]["net_bps"],c["best"]["route_text"])
                print("[HEARTBEAT] uptime_s=%d notifications=%d priced_events=%d signals=%d best=%s"%(
                    int(now-started),c["notifications"],c["priced_events"],c["signals"],best),flush=True)
                last=now
    finally:
        stop.set()
        for w in workers:w.cancel()
        await asyncio.gather(*workers,return_exceptions=True)

    payload={"assets":len(assets),"directed_edges":len(edges),"cycles":len(cycles),
             "cpmm_edges":cpmm,"cpmm_cycles":cpmm_cycles,"signals":c["signals"],
             "best":c["best"],"execution_authority":False}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    print("[RESULT] "+json.dumps(payload,sort_keys=True),flush=True)
    print("[MODE] PAPER_OBSERVATION=True execution_authority=FALSE",flush=True)
    if cpmm==0:raise SystemExit("[HOLD] CPMM state missing from asset graph")
    if cpmm_cycles==0:raise SystemExit("[HOLD] CPMM is priced but no SOL-returning multi-base cycle currently connects it")
    print("[PASS] CPMM participates in at least one SOL-returning multi-base cycle",flush=True)
    return payload

def main(argv=None):
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument("--seconds",type=float,default=120.0);a=ap.parse_args(argv)
    return asyncio.run(serve(Path.cwd(),a.seconds))

if __name__=="__main__":main()
