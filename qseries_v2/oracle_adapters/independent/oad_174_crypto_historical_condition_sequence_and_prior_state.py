from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class CryptoConditionSequence:
    asset:str
    source_family:str
    metric_name:str
    points:tuple
    point_count:int

def _dt(v):
    return datetime.fromisoformat(str(v).replace("Z","+00:00"))

def select_latest_prior_comparable_states(current_states,history_states):
    grouped={}
    for h in tuple(history_states):
        grouped.setdefault((h.asset,h.source_family,h.metric_name),[]).append(h)
    selected=[]
    for c in tuple(current_states):
        candidates=[
            h for h in grouped.get((c.asset,c.source_family,c.metric_name),())
            if h.observed_at is not None and c.observed_at is not None and _dt(h.observed_at)<_dt(c.observed_at)
        ]
        if candidates:
            selected.append(max(candidates,key=lambda x:_dt(x.observed_at)))
    return tuple(selected)

def build_crypto_condition_sequences(history_states,max_points_per_metric=32):
    grouped={}
    for h in tuple(history_states):
        grouped.setdefault((h.asset,h.source_family,h.metric_name),[]).append(h)
    out=[]
    for key,rows in sorted(grouped.items()):
        ordered=sorted(rows,key=lambda x:_dt(x.observed_at))
        ordered=ordered[-int(max_points_per_metric):]
        points=tuple((x.observed_at,float(x.value),x.condition) for x in ordered)
        out.append(CryptoConditionSequence(key[0],key[1],key[2],points,len(points)))
    return tuple(out)
