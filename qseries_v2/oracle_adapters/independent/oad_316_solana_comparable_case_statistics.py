\

from __future__ import annotations
from dataclasses import dataclass
from math import exp

READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SolanaComparableCaseStatistics:
    horizon_seconds:int; conditions:tuple; sample_size:int; effective_sample_size:float
    up_count:int; down_count:int; flat_count:int; raw_up_frequency:float
    weighted_up_frequency:float; contradictions:int; state:str
    execution_authority:bool=False

def aggregate_comparable_solana_cases(cases,half_life_cases=100.0):
    groups={}
    for c in cases:
        if not c.verified: continue
        groups.setdefault((c.horizon_seconds,tuple(c.conditions)),[]).append(c)
    out=[]
    for (h,cond),rows in sorted(groups.items(),key=lambda x:(x[0][0],str(x[0][1]))):
        n=len(rows); up=sum(x.outcome_class=="UP" for x in rows); down=sum(x.outcome_class=="DOWN" for x in rows); flat=n-up-down
        weights=[exp(-max(0,n-1-i)*0.6931471805599453/max(1.0,float(half_life_cases))) for i in range(n)]
        total=sum(weights); wup=sum(w for w,x in zip(weights,rows) if x.outcome_class=="UP")
        contradictions=min(up,down)
        out.append(SolanaComparableCaseStatistics(h,cond,n,total,up,down,flat,up/n,wup/total if total else 0.0,contradictions,"COMPARABLE_CASES_READY" if n>=2 else "INSUFFICIENT_SAMPLE",False))
    return tuple(out)

