from __future__ import annotations
import asyncio,contextlib,io
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import persistent_profit_runtime as p
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import merged_live_runtime as m
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_026f_exact_horizon_scheduler as qf
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_038b_nonrecursive_mriya_hotset_runtime as hot
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_061d_subscription_cap_aware_ws_valves as q61d

EXECUTION_AUTHORITY=False
PAPER_ONLY=True

def silent_hot_prepare(root):
    buf=io.StringIO()
    with contextlib.redirect_stdout(buf):
        return hot.priority_prepare_pairs(Path(root))

def install():
    m.pd.prepare_pairs=silent_hot_prepare
    p.m.pd.prepare_pairs=silent_hot_prepare
    p.SimulationLane=qf.PaperSimulationLane
    return q61d

def main(argv=None):
    runtime=install()
    print("[QARB-065] PROVEN PROFIT RUNTIME COMPOSITION",flush=True)
    print("[ENGINE] original persistent_profit_runtime; no replacement serve()",flush=True)
    print("[UNIVERSE] Mriya-hot PumpSwap/DLMM intake hidden from console",flush=True)
    print("[VENUES] PumpSwap DLMM CPMM DAMM_V2 CLMM ORCA via existing 061D cutover",flush=True)
    print("[PAPER] native 026F 2/5/15/30/60/90 scheduler",flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)
    return runtime.main(argv)

if __name__=="__main__":
    main()
