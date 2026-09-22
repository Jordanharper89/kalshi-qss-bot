
from dataclasses import dataclass
from datetime import datetime,timezone
from qseries_v2.oracle_adapters.independent.oad_314_solana_verified_forward_outcome_attribution import _price_for_pair
def _dt(v):
 if isinstance(v,datetime): return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
 return datetime.fromisoformat(str(v).replace("Z","+00:00"))
@dataclass(frozen=True)
class PricePath:
 pair_address:str; anchor_at:str; anchor_price:float; horizon_seconds:int
 observations:int; outcome_at:str; outcome_price:float; return_fraction:float
 mfe:float; mae:float; time_to_mfe_seconds:float; time_to_mae_seconds:float
 mfe_before_mae:bool; evidence_observation_ids:tuple
 read_only:bool=True; execution_authority:bool=False
def materialize_exact_future_price_paths(cases,records,horizons=(5,15,30,60,300,900,3600),tolerance_seconds=8.0):
 rows=tuple(sorted(records,key=lambda r:_dt(r.observed_at))); out=[]
 wanted=tuple(sorted({int(h) for h in horizons if int(h)>0}))
 for c in cases:
  evidence=set(c.evidence_observation_ids)
  anchors=[r for r in rows if r.observation_id in evidence]
  if not anchors: continue
  anchor=anchors[-1]; ap=_price_for_pair(anchor,c.pair_address)
  if ap is None or ap<=0: continue
  at=_dt(c.snapshot_at)
  future=[r for r in rows if _dt(r.observed_at)>at and _price_for_pair(r,c.pair_address) is not None]
  for h in wanted:
   end=at.timestamp()+h
   path=[r for r in future if _dt(r.observed_at).timestamp()<=end+float(tolerance_seconds)]
   eligible=[r for r in path if _dt(r.observed_at).timestamp()>=end]
   if not eligible: continue
   terminal=eligible[0]; terminal_t=_dt(terminal.observed_at)
   path=[r for r in path if _dt(r.observed_at)<=terminal_t]
   pts=[(r,_price_for_pair(r,c.pair_address)) for r in path]
   pts=[(r,float(px)) for r,px in pts if px is not None and float(px)>0]
   if not pts: continue
   rets=[(px/ap)-1.0 for _,px in pts]; hi=max(range(len(rets)),key=rets.__getitem__); lo=min(range(len(rets)),key=rets.__getitem__)
   op=pts[-1][1]
   out.append(PricePath(c.pair_address,str(c.snapshot_at),float(ap),h,len(pts),
    str(pts[-1][0].observed_at),op,(op/ap)-1.0,rets[hi],rets[lo],
    (_dt(pts[hi][0].observed_at)-at).total_seconds(),(_dt(pts[lo][0].observed_at)-at).total_seconds(),
    hi<lo,tuple(c.evidence_observation_ids)+tuple(r.observation_id for r,_ in pts)))
 return tuple(out)
