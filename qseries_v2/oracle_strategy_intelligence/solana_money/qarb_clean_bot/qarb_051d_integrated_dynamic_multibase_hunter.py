from __future__ import annotations
import argparse,asyncio,json,time
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_051b_bounded_dynamic_handoff_episode_gate as handoff
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_051c_rolling_cpmm_identity_ledger as ledger
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_049c_cpmm_connected_live_route_graph as graph

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
OUT=Path("runtime_state/qseries/qarb_clean_bot/qarb_051d_integrated_dynamic_multibase_hunter.json")
REPRICE_BPS=5.0

class GenerationEpisodeGate:
    """Conservative episode accounting.
    Same route+size stays one episode through a generation unless materially repriced.
    A route can become a new episode in a later generation only if it was absent from
    the entire immediately preceding generation.
    """
    def __init__(self):
        self.active={}
        self.admitted=[]
        self.raw_positive=0
        self.duplicates=0
        self.generation=0
        self.seen_this_generation=set()

    @staticmethod
    def key(row):
        return (row.get("route"),float(row.get("size_sol") or 0.0))

    def begin_generation(self,g):
        self.generation=int(g)
        self.seen_this_generation=set()

    def end_generation(self):
        # If an active opportunity was not observed at all in this generation,
        # it is considered closed and may be admitted if it reappears later.
        for k in list(self.active):
            if k not in self.seen_this_generation:
                del self.active[k]

    def admit(self,row):
        if not row or not row.get("qualified"):
            return row
        self.raw_positive+=1
        k=self.key(row)
        self.seen_this_generation.add(k)
        old=self.active.get(k)

        if old is not None:
            old_bps=float(old.get("net_bps") or 0.0)
            new_bps=float(row.get("net_bps") or 0.0)
            if abs(new_bps-old_bps)<REPRICE_BPS:
                self.duplicates+=1
                print("[EPISODE_DUPLICATE] gen=%d route=%s size=%.6f bps=%+.2f"%(
                    self.generation,row.get("route"),row.get("size_sol"),row.get("net_bps")),flush=True)
                return None

        x=dict(row)
        x["episode_id"]="E%06d"%(len(self.admitted)+1)
        x["generation"]=self.generation
        x["execution_authority"]=False
        self.active[k]=x
        self.admitted.append(x)
        print("[EPISODE_ADMIT] id=%s gen=%d size=%.6f net=%+.9f bps=%+.2f route=%s"%(
            x["episode_id"],self.generation,x["size_sol"],x["net_sol"],x["net_bps"],x["route"]),flush=True)
        return x

async def run_graph(root,seconds,gate):
    original_eval=graph.evaluate
    def wrapped(state,routes,received_ns):
        return gate.admit(original_eval(state,routes,received_ns))
    graph.evaluate=wrapped
    try:
        return await graph.serve(Path(root),seconds)
    finally:
        graph.evaluate=original_eval

def run_generation(root,g,dynamic_seconds,graph_seconds,gate):
    print("\n[GENERATION_START] %d"%g,flush=True)

    # 1. Fresh Mriya acquisition + native transaction + exact DEX handoff.
    h=handoff.refresh_handoff(root,dynamic_seconds)

    # 2. Merge any new exact CPMM identity into durable rolling ledger.
    lp=ledger.refresh(root)
    print("[LEDGER] descriptors=%d sources=%s"%(
        lp["descriptor_count"],json.dumps(lp["source_counts"],sort_keys=True)),flush=True)

    # 3. Permanently use rolling identities for this live graph generation.
    original_discover=graph.rc.discover
    graph.rc.discover=lambda r: ledger.discover(r)

    gate.begin_generation(g)
    try:
        gr=asyncio.run(run_graph(root,graph_seconds,gate))
    finally:
        gate.end_generation()
        graph.rc.discover=original_discover

    result={
      "generation":g,
      "handoff":h,
      "ledger_descriptor_count":lp["descriptor_count"],
      "ledger_source_counts":lp["source_counts"],
      "graph_result":gr,
      "execution_authority":False}
    print("[GENERATION_RESULT] gen=%d q027=%s q030=%s ledger=%d pools=%s bridges=%s cycles=%s raw=%d dup=%d independent=%d"%(
        g,h["qarb027_progress"],h["qarb030_progress"],lp["descriptor_count"],
        gr.get("cpmm_pools"),gr.get("dlmm_wsol_bridges"),gr.get("cpmm_cycles"),
        gate.raw_positive,gate.duplicates,len(gate.admitted)),flush=True)
    return result

def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--generations",type=int,default=3)
    ap.add_argument("--dynamic-seconds",type=float,default=30.0)
    ap.add_argument("--graph-seconds",type=float,default=90.0)
    ap.add_argument("--between-seconds",type=float,default=5.0)
    a=ap.parse_args(argv)

    root=Path.cwd()
    gate=GenerationEpisodeGate()
    generations=[]

    print("[QARB-051D] INTEGRATED DYNAMIC MULTIBASE HUNTER",flush=True)
    print("[FLOW] 043B -> 027 -> 030 -> 051C rolling identity -> 049C live graph -> conservative episode gate",flush=True)
    print("[WINDOW] generations=%d dynamic=%.1fs graph=%.1fs"%(
        a.generations,a.dynamic_seconds,a.graph_seconds),flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)

    for g in range(1,a.generations+1):
        generations.append(run_generation(root,g,a.dynamic_seconds,a.graph_seconds,gate))
        if g<a.generations and a.between_seconds>0:
            time.sleep(a.between_seconds)

    payload={
      "revision":"QARB_051D",
      "generation_count":len(generations),
      "generations":generations,
      "raw_positive_emissions":gate.raw_positive,
      "duplicate_emissions":gate.duplicates,
      "independent_episode_count":len(gate.admitted),
      "independent_episodes":gate.admitted,
      "paper_only":True,
      "execution_authority":False}
    p=root/OUT
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")

    print("\n[FINAL_RESULT] generations=%d raw=%d duplicates=%d independent=%d"%(
        len(generations),gate.raw_positive,gate.duplicates,len(gate.admitted)),flush=True)
    print("[REPORT]",OUT,flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)

if __name__=="__main__":
    main()
