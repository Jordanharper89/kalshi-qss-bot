from __future__ import annotations
from collections import defaultdict
from .profile import OBSERVED_MOTIFS
WSOL="So11111111111111111111111111111111111111112"
USDC="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
USDT="Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"
USD1="USD1ttGY1N17NEEHLmELoaybftRBUSErhqYiQzvEmuB"
ANCHORS=(WSOL,USDC,USDT,USD1)
def motif_match(venues):
    s=frozenset(venues)
    return max((len(s&m)/len(s|m) for m in OBSERVED_MOTIFS if s|m),default=0.0)
def scan_cycles(edges,now,max_age=.75,max_hops=4,leg_haircut_bps=30,landing_cost_bps=5,min_net_bps=10):
    usable=[]
    chain_stale=0
    for e in edges:
        if e.get("observed_direction") is not True:continue
        arrival_age=now-float(e["t"])
        if arrival_age<0 or arrival_age>max_age:continue
        bt=e.get("chain_block_time")
        if isinstance(bt,(int,float)) and bt>0 and now-float(bt)>3.0:
            chain_stale+=1;continue
        usable.append(e)
    by=defaultdict(list)
    for e in usable:by[e["src"]].append(e)
    out=[];seen=set();hair=1-leg_haircut_bps/10000
    for anchor in ANCHORS:
        def dfs(asset,path,rate,tmin,tmax):
            h=len(path)
            if h>=2 and asset==anchor:
                if tmax-tmin>max_age:return
                if len({x["market"] for x in path})<2:return
                nr=rate*(hair**h)*(1-landing_cost_bps/10000);bps=(nr-1)*10000
                if bps<min_net_bps:return
                key=(anchor,tuple((x["signature"],x["src"],x["dst"]) for x in path))
                if key in seen:return
                seen.add(key);vs=tuple(x["venue"] for x in path)
                out.append({"anchor":anchor,"hops":h,"net_bps":bps,"net_return":nr-1,"route":list(path),
                            "venues":vs,"motif_match":motif_match(vs),"time_spread_seconds":tmax-tmin,
                            "execution_authority":False})
                return
            if h>=max_hops:return
            for e in by.get(asset,()):
                if path and e["signature"]==path[-1]["signature"]:continue
                if any(x["signature"]==e["signature"] for x in path):continue
                nxt=e["dst"]
                if any(x["src"]==nxt for x in path) and nxt!=anchor:continue
                a=e["t"] if not path else min(tmin,e["t"]);b=e["t"] if not path else max(tmax,e["t"])
                if b-a<=max_age:dfs(nxt,path+[e],rate*e["rate"],a,b)
        dfs(anchor,[],1.0,0.0,0.0)
    out.sort(key=lambda x:(x["net_bps"],x["motif_match"]),reverse=True)
    return out,{"fresh_edges":len(usable),"chain_stale_rejected":chain_stale,
                "venues":sorted(set(e["venue"] for e in usable))}
