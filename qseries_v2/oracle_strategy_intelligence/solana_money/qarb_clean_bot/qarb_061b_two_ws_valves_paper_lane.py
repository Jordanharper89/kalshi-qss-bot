from __future__ import annotations
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_060b_existing_runtime_multidex_cutover as q60b
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_026f_exact_horizon_scheduler as paper
EXECUTION_AUTHORITY=False
PAPER_ONLY=True
def two_valves(addrs):
    a=list(dict.fromkeys(addrs))
    if len(a)<=1:return [a]
    return [x for x in (a[::2],a[1::2]) if x]
def install():
    q60b.m._shards=two_valves
    q60b.p.m._shards=two_valves
    if hasattr(q60b.m,"SUB_DELAY_MS"): q60b.m.SUB_DELAY_MS=max(int(q60b.m.SUB_DELAY_MS),60)
    q60b.p.SimulationLane=paper.PaperSimulationLane
    return q60b.p
