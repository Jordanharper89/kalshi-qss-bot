from __future__ import annotations
from dataclasses import dataclass
from statistics import mean,median

READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; EXECUTION_AUTHORITY=False

def condition_signature(case):
    cond=tuple(sorted((str(x[0]),str(x[1]),str(x[3])) for x in tuple(case.condition_vector)))
    temp=tuple(sorted((str(x[0]),str(x[1]),str(x[2])) for x in tuple(case.temporal_vector) if len(tuple(x))>=6 and bool(tuple(x)[5])))
    return cond,temp

@dataclass(frozen=True,slots=True)
class ComparableConditionOutcomeStats:
    asset:str; horizon_seconds:int; condition_signature:tuple; sample_size:int
    positive:int; negative:int; unchanged:int; raw_positive_frequency:float
    mean_return_percent:float; median_return_percent:float; minimum_return_percent:float; maximum_return_percent:float
    probability_enabled:bool=False; direction_enabled:bool=False; execution_authority:bool=False

def build_comparable_condition_outcome_statistics(cases,unchanged_epsilon_percent=0.000001):
    groups={}
    for c in tuple(cases):
        key=(c.asset,int(c.horizon_seconds),condition_signature(c))
        groups.setdefault(key,[]).append(c)
    out=[]
    for (asset,horizon,sig),rows in sorted(groups.items(),key=lambda x:(x[0][0],x[0][1],str(x[0][2]))):
        vals=[float(x.return_percent) for x in rows]
        pos=sum(v>unchanged_epsilon_percent for v in vals); neg=sum(v<-unchanged_epsilon_percent for v in vals); un=len(vals)-pos-neg
        out.append(ComparableConditionOutcomeStats(asset,horizon,sig,len(vals),pos,neg,un,pos/len(vals),mean(vals),median(vals),min(vals),max(vals),False,False,False))
    return tuple(out)
