from pathlib import Path
import json
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_051c_rolling_cpmm_identity_ledger as ledger
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_049c_cpmm_connected_live_route_graph as graph

def main():
    root=Path.cwd()
    p=ledger.refresh(root)
    original=graph.rc.discover
    graph.rc.discover=lambda r: ledger.discover(r)
    try:
        state=graph.prepare(root)
    finally:
        graph.rc.discover=original
    print("[QARB-051C-CERT] ROLLING IDENTITY -> LIVE GRAPH")
    print("[LEDGER_DESCRIPTORS]",p["descriptor_count"])
    print("[CPMM_HYDRATED]",len(state["cstates"]))
    print("[DLMM_BRIDGES]",len(state["dlmms"]))
    es=graph.edges(state);rs=graph.cycles(es)
    print("[CPMM_CYCLES]",len(rs))
    for r in rs[:20]:print("[CPMM_CYCLE]",graph.route_text(r))
    print("[MODE] PAPER_OBSERVATION=True execution_authority=FALSE")
    if not p["descriptor_count"]:raise SystemExit("[HOLD] no retained exact CPMM identities")
    if not state["cstates"]:raise SystemExit("[HOLD] retained identities could not hydrate")
    print("[PASS] sparse fresh capture no longer deletes certified CPMM identity pavement")

if __name__=="__main__":main()
