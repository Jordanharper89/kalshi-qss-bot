from dataclasses import dataclass
from datetime import datetime,timezone
READ_ONLY=True; EXECUTION_AUTHORITY=False
def _dt(v): return datetime.fromisoformat(str(v).replace("Z","+00:00"))
@dataclass(frozen=True,slots=True)
class FreshOpportunityState:
 token_address:str; pair_address:str; observed_at:str; age_seconds:float
 window_seconds:int; conditions:tuple; state:str; execution_authority:bool=False
def form_fresh_opportunity_states(cycle,now=None,max_age_seconds=20.0,window_seconds=60):
 now=now or datetime.now(timezone.utc); out=[]
 for w in tuple(cycle.windows):
  if int(w.window_seconds)!=int(window_seconds) or w.state!="WINDOW_READY" or not w.last_observed_at: continue
  age=max(0.0,(now-_dt(w.last_observed_at)).total_seconds())
  for pair,conditions,state in tuple(w.conditions):
   out.append(FreshOpportunityState(str(cycle.token_address),str(pair),str(w.last_observed_at),age,
    int(w.window_seconds),tuple(conditions),"FRESH" if age<=float(max_age_seconds) else "STALE",False))
 return tuple(out)
