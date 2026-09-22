from dataclasses import dataclass
from hashlib import sha256
READ_ONLY=True; EXECUTION_AUTHORITY=False
FROZEN_THESIS={"horizon":60,"target":0.10,"stop":0.05,"condition":("order_flow","BUY_PRESSURE"),"friction_bps":200}
@dataclass(frozen=True,slots=True)
class ProspectiveOpportunity:
 prediction_id:str; token_address:str; pair_address:str; frozen_at:str; conditions:tuple
 horizon_seconds:int; target:float; stop:float; friction_bps:int
 state:str="PENDING_60S"; execution_authority:bool=False
def admit_and_freeze(states,thesis=FROZEN_THESIS):
 out=[]
 for x in states:
  if x.state!="FRESH" or thesis["condition"] not in tuple(x.conditions): continue
  raw="|".join((x.token_address,x.pair_address,x.observed_at,repr(tuple(x.conditions))))
  out.append(ProspectiveOpportunity(sha256(raw.encode()).hexdigest(),x.token_address,x.pair_address,
   x.observed_at,tuple(x.conditions),int(thesis["horizon"]),float(thesis["target"]),
   float(thesis["stop"]),int(thesis["friction_bps"]),"PENDING_60S",False))
 return tuple(out)
