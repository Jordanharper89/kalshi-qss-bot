from dataclasses import dataclass
from .opc_011_universal_coverage_scheduler import schedule_uncovered
from .opc_012_coverage_priority_engine import prioritize_coverage
@dataclass(frozen=True)
class ContinuousCoveragePlan:
    open_count:int; covered_count:int; selected_tickers:tuple; bounded_limit:int; read_only:bool=True; execution_allowed:bool=False
def plan_continuous_coverage_cycle(open_tickers,covered_tickers,facts=None,limit=100):
    work=schedule_uncovered(open_tickers,covered_tickers,max(int(limit)*4,int(limit)))
    ranked=prioritize_coverage(work,facts)
    return ContinuousCoveragePlan(len(set(open_tickers)),len(set(covered_tickers)),tuple(x.ticker for x in ranked[:int(limit)]),int(limit))
def verify_opc_014_continuous_coverage_cycle():
    x=plan_continuous_coverage_cycle(("A","B","C"),("A",),{"C":{"active":True}},2)
    return x.selected_tickers==("C","B") and not x.execution_allowed
