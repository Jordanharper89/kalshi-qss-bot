from __future__ import annotations
import asyncio,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import persistent_profit_runtime as p
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_026g_token_freshness_profit_audit as qg
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_026h_fresh_crossvenue_paper_gate as qh
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_037_mriya_priority_pair_hydration as h

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
_ORIG_PREPARE_PAIRS=p.m.pd.prepare_pairs

def priority_prepare_pairs(root):
    pairs,landing,_=h.hydrate(Path(root))
    print("[MRIYA_HOTSET] hydrated_priority_pairs=%d tokens=%s"%(
        len(pairs),[x.token[:12] for x in pairs]),flush=True)
    return pairs,landing

def install():
    qg.VENUE_TS.clear()
    p.m.pd.prepare_pairs=priority_prepare_pairs
    p.m.pd.apply_account_event=qg.tracked_apply
    p.SimulationLane=qh.FreshOnlyPaperLane
    return p

def main(argv=None):
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument("--seconds",type=float,default=None);a=ap.parse_args(argv)
    runtime=install()
    print("[QARB-038] MRIYA-HOTSET FRESH PAPER PROFIT RUNTIME",flush=True)
    print("[ENGINE] original persistent_profit_runtime.serve unchanged",flush=True)
    print("[UNIVERSE] QARB-036 exact top PumpSwap/Meteora bindings",flush=True)
    print("[PAPER_GATE] both venues live-observed and <=750ms old",flush=True)
    print("[HORIZONS] 2s,5s,15s,30s,60s,90s",flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)
    return asyncio.run(runtime.serve(Path.cwd(),a.seconds))
if __name__=="__main__":main()
