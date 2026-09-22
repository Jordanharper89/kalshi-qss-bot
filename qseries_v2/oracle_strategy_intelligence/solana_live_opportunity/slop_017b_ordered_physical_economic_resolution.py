from dataclasses import dataclass
READ_ONLY=True;EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class EconomicResolution:
 prediction_id:str;outcome:str;barrier_at:str;gross_return:float;net_return:float
 terminal_return:float;mfe:float;mae:float;friction_bps:int;state:str="RESOLVED";execution_authority:bool=False
def resolve_economics(prediction,path):
 if path is None:return None
 target=float(prediction.target);stop=float(prediction.stop);friction=float(prediction.friction_bps)/10000.0
 first=None
 for ts,px,_ in tuple(path.observations):
  r=float(px)/float(path.anchor_price)-1.0
  if r>=target:first=("TARGET_FIRST",ts,r);break
  if r<=-stop:first=("STOP_FIRST",ts,r);break
 if first is None:
  outcome="TIMEOUT";barrier_at=str(path.outcome_at);gross=float(path.return_fraction)
 else: outcome,barrier_at,gross=first
 net=float(gross)-friction
 return EconomicResolution(prediction.prediction_id,outcome,barrier_at,float(gross),net,
  float(path.return_fraction),float(path.mfe),float(path.mae),int(prediction.friction_bps),"RESOLVED",False)
