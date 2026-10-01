from __future__ import annotations
from collections import defaultdict
WSOL="So11111111111111111111111111111111111111112"
USDC="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
USDT="Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"
USD1="USD1ttGY1N17NEEHLmELoaybftRBUSErhqYiQzvEmuB"
ANCHORS=(WSOL,USDC,USDT,USD1)

def observed_cycles(edges,leg_haircut_bps=30,landing_bps=5,min_net_bps=10,max_hops=4):
    by=defaultdict(list)
    for e in edges:
        if e.get("observed_direction") is True:by[e["src"]].append(e)
    out=[];seen=set();hair=1-leg_haircut_bps/10000
    for anchor in ANCHORS:
        def dfs(asset,path,rate,venues,sigs):
            h=len(path)
            if h>=2 and asset==anchor:
                if len(venues)<2:return
                nr=rate*(hair**h)*(1-landing_bps/10000);bps=(nr-1)*10000
                if bps<min_net_bps:return
                key=(anchor,tuple((x["signature"],x["src"],x["dst"]) for x in path))
                if key in seen:return
                seen.add(key);out.append({"anchor":anchor,"hops":h,"net_bps":bps,
                    "venues":tuple(x["venue"] for x in path),"route":list(path),
                    "classification":"OBSERVED_BLOCK_ARB_PATTERN","execution_authority":False})
                return
            if h>=max_hops:return
            for e in by.get(asset,()):
                if e["signature"] in sigs:continue
                nxt=e["dst"]
                if any(x["src"]==nxt for x in path) and nxt!=anchor:continue
                dfs(nxt,path+[e],rate*e["rate"],venues|{e["venue"]},sigs|{e["signature"]})
        dfs(anchor,[],1.0,set(),set())
    out.sort(key=lambda x:x["net_bps"],reverse=True);return out
