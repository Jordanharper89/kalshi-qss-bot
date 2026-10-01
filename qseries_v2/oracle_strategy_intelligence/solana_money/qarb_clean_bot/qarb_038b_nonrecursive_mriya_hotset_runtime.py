from __future__ import annotations
import asyncio,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import persistent_profit_runtime as p
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as pd
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_026g_token_freshness_profit_audit as qg
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_026h_fresh_crossvenue_paper_gate as qh

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
BINDINGS=Path("runtime_state/qseries/qarb_clean_bot/mriya_exact_pump_meteora_bindings.json")
_BASE_PREPARE_PAIRS=pd.prepare_pairs

def priority_universe(root):
    if not BINDINGS.is_file():
        raise RuntimeError("QARB-036 bindings missing: "+str(BINDINGS))
    d=json.loads(BINDINGS.read_text(encoding="utf-8"))
    return [{"token":x["token"],"pump_pool":x["pump_pool"],"meteora_meta":x["meteora_meta"]} for x in d.get("rows",[])]

def priority_prepare_pairs(root):
    old_universe=pd.engine.candidate_universe
    old_max=pd.MAX_PAIRS
    pd.engine.candidate_universe=priority_universe
    pd.MAX_PAIRS=16
    try:
        pairs,landing=_BASE_PREPARE_PAIRS(Path(root))
    finally:
        pd.engine.candidate_universe=old_universe
        pd.MAX_PAIRS=old_max
    print("[MRIYA_HOTSET] hydrated_priority_pairs=%d tokens=%s"%(len(pairs),[x.token[:12] for x in pairs]),flush=True)
    return pairs,landing

def install():
    qg.VENUE_TS.clear()
    p.m.pd.prepare_pairs=priority_prepare_pairs
    p.m.pd.apply_account_event=qg.tracked_apply
    p.SimulationLane=qh.FreshOnlyPaperLane
    return p

def main(argv=None):
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--seconds",type=float,default=None)
    a=ap.parse_args(argv)
    runtime=install()
    print("[QARB-038B] NONRECURSIVE MRIYA-HOTSET FRESH PAPER RUNTIME",flush=True)
    print("[FIX] QARB-037 hydration removed from runtime path",flush=True)
    print("[BINDING] frozen original live_account_stream.prepare_pairs called directly",flush=True)
    print("[ENGINE] persistent_profit_runtime.serve unchanged",flush=True)
    print("[PAPER_GATE] both venues live-observed and <=750ms old",flush=True)
    print("[HORIZONS] 2s,5s,15s,30s,60s,90s",flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)
    return asyncio.run(runtime.serve(Path.cwd(),a.seconds))

if __name__=="__main__":
    main()
