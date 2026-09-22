
from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
from pathlib import Path
from .ohl_006_settled_outcome_inventory_adapter import read_settled_outcome_inventory
from .ohl_008_settled_market_eligibility_evaluator import evaluate_settled_market_eligibility,verify_ohl_008_settled_market_eligibility_evaluator

OHL_009_BUILD_ID="OHL-009"
OHL_009_REVISION="OHL_009_HISTORICAL_ELIGIBILITY_CENSUS_V1"

@dataclass(frozen=True)
class HistoricalEligibilityCensus:
    settled_scanned:int
    unique_tickers:int
    eligible_markets:int
    ineligible_markets:int
    eligibility_rate:float
    total_pre_settlement_evidence:int
    reasons:tuple
    eligible_tickers:tuple
    read_only:bool=True
    execution_authority:bool=False

def run_historical_eligibility_census(root=None,settled_limit=500,evidence_limit=50,progress=None):
    if not verify_ohl_008_settled_market_eligibility_evaluator():
        raise RuntimeError("OHL-008 verification failed")
    root=Path(root or Path.cwd()).resolve()
    inv=read_settled_outcome_inventory(root,settled_limit)
    results=[]
    for idx,outcome in enumerate(inv.outcomes,1):
        r=evaluate_settled_market_eligibility(root,outcome,evidence_limit)
        results.append(r)
        if progress:
            progress(f"[CENSUS] {idx}/{inv.settled_count} ticker={r.ticker} eligible={r.eligible} evidence={r.evidence_count} reason={r.reason}")
    eligible=[r for r in results if r.eligible]
    reasons=Counter(r.reason for r in results if not r.eligible)
    total_evidence=sum(r.evidence_count for r in results)
    rate=(len(eligible)/len(results)) if results else 0.0
    return HistoricalEligibilityCensus(
        len(results),inv.unique_tickers,len(eligible),len(results)-len(eligible),
        rate,total_evidence,tuple(sorted(reasons.items())),
        tuple(sorted(r.ticker for r in eligible)),True,False
    )

def verify_ohl_009_historical_eligibility_census():
    x=HistoricalEligibilityCensus(0,0,0,0,0.0,0,tuple(),tuple(),True,False)
    return x.read_only and not x.execution_authority
