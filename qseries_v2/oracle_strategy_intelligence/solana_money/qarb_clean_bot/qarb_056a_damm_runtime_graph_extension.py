from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_052a6_damm_graph_ready_live_adapter as damm

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
MAX_AGE_MS=750.0
WSOL=getattr(c,"WSOL","So11111111111111111111111111111111111111112")
OUT=Path("runtime_state/qseries/qarb_clean_bot/qarb_056a_damm_runtime_graph_extension.json")

def build(root):
    states,reg=damm.prepare(root)
    edges=[];checks=[]
    for d,s in states:
        for src,dst in ((d.token_a,d.token_b),(d.token_b,d.token_a)):
            edges.append({"venue":"METEORA_DAMM_V2","pool":d.pool,"src":src,"dst":dst})
            try:
                q=damm.quote_edge((d,s),src,100000)
                checks.append({"pool":d.pool,"src":src,"dst":dst,"ok":isinstance(q,int) and q>=0})
            except Exception as e:
                checks.append({"pool":d.pool,"src":src,"dst":dst,"ok":False,"error":type(e).__name__+":"+str(e)})
    payload={"revision":"QARB_056A","states":len(states),"watched_accounts":len(reg),
             "edges":edges,"directed_edges":len(edges),
             "direct_sol_edges":sum(1 for e in edges if WSOL in (e["src"],e["dst"])),
             "quote_passes":sum(1 for x in checks if x.get("ok")),
             "quote_checks":checks,
             "priced_live":bool(checks and all(x.get("ok") for x in checks)),
             "next":"CONSUME_DAMM_GRAPH_EXTENSION_IN_EXISTING_051D_HUNTER",
             "execution_authority":False,"paper_only":True}
    p=Path(root)/OUT;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    return payload

def main():
    p=build(Path.cwd())
    print("[QARB-056A] DAMM RUNTIME GRAPH EXTENSION")
    print("[DAMM] states=%d edges=%d direct_sol=%d quote_passes=%d/%d priced_live=%s"%(
        p["states"],p["directed_edges"],p["direct_sol_edges"],p["quote_passes"],len(p["quote_checks"]),p["priced_live"]))
    print("[NEXT]",p["next"])
    print("[REPORT]",OUT)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE")

if __name__=="__main__": main()
