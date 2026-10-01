from __future__ import annotations
import json,math,time
from collections import defaultdict
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_economic_bridge.bridge import build as build_bridge

ANCHORS={
 "So11111111111111111111111111111111111111112":"WSOL",
 "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v":"USDC",
 "Es9vMFrzaCERmJfrF4H2FYD9zX6Y2pZPbBZ5w4M7ZC9":"USDT",
}
TARGET_VENUES={"PUMP_SWAP","METEORA_DLMM","METEORA_DAMM_V2","RAYDIUM_CLMM","RAYDIUM_CPMM","ORCA"}
MAX_EDGE_SLOT_AGE=4
MAX_ROUTE_SLOT_SPREAD=2
MIN_GROSS_BPS=20.0

def edge_from_trade(t):
    try:
        ia=float(t["input_amount"]); oa=float(t["output_amount"])
        if ia<=0 or oa<=0:return None
        slot=int(t["slot"])
    except Exception:return None
    v=str(t.get("venue") or "")
    if v not in TARGET_VENUES:return None
    return {
      "src":t["input_mint"],"dst":t["output_mint"],"rate":oa/ia,
      "venue":v,"slot":slot,"pool":t.get("pool"),"signature":t.get("signature"),
      "source_module":t.get("source_module"),"input_amount":ia,"output_amount":oa,
    }

def latest_edges(rows):
    d={}
    for t in rows:
        e=edge_from_trade(t)
        if not e:continue
        k=(e["venue"],e["src"],e["dst"],e.get("pool"))
        if k not in d or e["slot"]>=d[k]["slot"]:d[k]=e
    return list(d.values())

def _route_record(edges):
    slots=[e["slot"] for e in edges]
    gross=1.0
    for e in edges:gross*=e["rate"]
    bps=(gross-1.0)*10000.0
    return {
      "legs":len(edges),"start_mint":edges[0]["src"],"end_mint":edges[-1]["dst"],
      "gross_multiplier":gross,"gross_bps":bps,
      "slot_min":min(slots),"slot_max":max(slots),"slot_spread":max(slots)-min(slots),
      "venues":[e["venue"] for e in edges],
      "pools":[e.get("pool") for e in edges],
      "path":[edges[0]["src"]]+[e["dst"] for e in edges],
      "edges":edges,
      "fresh":(max(slots)-min(slots))<=MAX_ROUTE_SLOT_SPREAD,
      "distinct_venues":len({e["venue"] for e in edges})==len(edges),
    }

def search_two_leg(edges):
    bysrc=defaultdict(list)
    for e in edges:bysrc[e["src"]].append(e)
    out=[]
    for a in ANCHORS:
        for e1 in bysrc.get(a,[]):
            if e1["dst"]==a:continue
            for e2 in bysrc.get(e1["dst"],[]):
                if e2["dst"]!=a or e1["venue"]==e2["venue"]:continue
                r=_route_record([e1,e2])
                if r["fresh"] and r["gross_bps"]>=MIN_GROSS_BPS:out.append(r)
    return out

def search_three_leg(edges):
    bysrc=defaultdict(list)
    for e in edges:bysrc[e["src"]].append(e)
    out=[]
    for a in ANCHORS:
        for e1 in bysrc.get(a,[]):
            x=e1["dst"]
            if x==a:continue
            for e2 in bysrc.get(x,[]):
                y=e2["dst"]
                if y in (a,x):continue
                for e3 in bysrc.get(y,[]):
                    if e3["dst"]!=a:continue
                    if len({e1["venue"],e2["venue"],e3["venue"]})<2:continue
                    r=_route_record([e1,e2,e3])
                    if r["fresh"] and r["gross_bps"]>=MIN_GROSS_BPS:out.append(r)
    return out

def dedupe(routes):
    best={}
    for r in routes:
        k=(tuple(r["path"]),tuple(r["venues"]),tuple(r["pools"]))
        if k not in best or r["gross_bps"]>best[k]["gross_bps"]:best[k]=r
    return sorted(best.values(),key=lambda x:x["gross_bps"],reverse=True)

def build(root,bridge_fn=build_bridge):
    root=Path(root)
    b=bridge_fn(root)
    rows=list(b.get("fresh_economic_rows") or [])
    live_max=b.get("live_max_slot")
    edges=latest_edges(rows)
    if live_max is not None:
        edges=[e for e in edges if 0<=int(live_max)-e["slot"]<=MAX_EDGE_SLOT_AGE]
    two=dedupe(search_two_leg(edges))
    three=dedupe(search_three_leg(edges))
    routes=dedupe(two+three)
    vc=defaultdict(int)
    for e in edges:vc[e["venue"]]+=1
    print("[GRAPH] fresh_rows=%d edges=%d venues=%s"%(len(rows),len(edges),json.dumps(dict(sorted(vc.items())))),flush=True)
    print("[ROUTES] two_leg=%d three_leg=%d total=%d"%(len(two),len(three),len(routes)),flush=True)
    for i,r in enumerate(routes[:10],1):
        names=[ANCHORS.get(x,x[:8]) for x in r["path"]]
        print("[ROUTE %d] legs=%d path=%s venues=%s gross_bps=%+.2f slots=%d fresh=%s"%(
          i,r["legs"]," -> ".join(names)," -> ".join(r["venues"]),r["gross_bps"],r["slot_spread"],r["fresh"]),flush=True)
    out={
      "revision":"QSB_041","bridge_revision":b.get("revision"),"live_max_slot":live_max,
      "edge_count":len(edges),"venue_edge_counts":dict(vc),
      "two_leg_routes":two,"three_leg_routes":three,"routes":routes,
      "execution_authority":False,
      "truth":"OBSERVED_ECONOMIC_ROUTE_CANDIDATES_NOT_EXECUTABLE_QUOTES",
      "next_boundary":"EXACT_ROUTE_REQUOTE_AND_ATOMIC_SIMULATION"
    }
    p=root/"runtime_state/qseries/qsb041_mriya_route_engine/report.json"
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,indent=2),encoding="utf-8")
    return out
