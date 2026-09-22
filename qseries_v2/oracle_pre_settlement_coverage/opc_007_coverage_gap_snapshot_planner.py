from dataclasses import dataclass
@dataclass(frozen=True)
class SnapshotPlan:
    sampled_markets:int
    already_covered:int
    missing_markets:int
    planned_tickers:tuple
    bounded:bool=True
    execution_authority:bool=False
def plan_missing_market_snapshots(open_markets,recent_canonical_tickers,max_markets=100):
    max_markets=int(max_markets)
    if max_markets<1 or max_markets>1000: raise ValueError("max_markets must be 1..1000")
    recent={str(x) for x in recent_canonical_tickers}; planned=[]; total=covered=0
    for row in open_markets:
        if not isinstance(row,dict): continue
        t=str(row.get("ticker") or "")
        if not t: continue
        total+=1
        if t in recent: covered+=1
        elif len(planned)<max_markets: planned.append(t)
    return SnapshotPlan(total,covered,total-covered,tuple(planned),True,False)
def verify_opc_007_coverage_gap_snapshot_planner():
    p=plan_missing_market_snapshots(({"ticker":"A"},{"ticker":"B"},{"ticker":"C"}),{"B"},2)
    return p.sampled_markets==3 and p.already_covered==1 and p.planned_tickers==("A","C") and not p.execution_authority
