from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class CryptoTemporalConditionChange:
    asset:str
    source_family:str
    metric_name:str
    previous_value:float|None
    current_value:float
    absolute_change:float|None
    percent_change:float|None
    previous_condition:str|None
    current_condition:str
    temporal_state:str
    comparable_history_present:bool

def _dt(v):
    try: return datetime.fromisoformat(str(v).replace("Z","+00:00"))
    except Exception: return None

def evaluate_crypto_temporal_condition_changes(current_states,previous_states=()):
    prev={}
    for x in tuple(previous_states):
        prev[(x.asset,x.source_family,x.metric_name)]=x
    out=[]
    for x in tuple(current_states):
        p=prev.get((x.asset,x.source_family,x.metric_name))
        if p is None:
            out.append(CryptoTemporalConditionChange(
                x.asset,x.source_family,x.metric_name,None,float(x.value),None,None,
                None,x.condition,"NO_COMPARABLE_HISTORY",False
            ))
            continue
        av=float(x.value)-float(p.value)
        pc=None if float(p.value)==0 else av/abs(float(p.value))*100.0
        if av>0: state="INCREASED"
        elif av<0: state="DECREASED"
        else: state="UNCHANGED"
        out.append(CryptoTemporalConditionChange(
            x.asset,x.source_family,x.metric_name,float(p.value),float(x.value),
            av,pc,p.condition,x.condition,state,True
        ))
    return tuple(out)
