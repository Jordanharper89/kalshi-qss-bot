from __future__ import annotations
from collections import defaultdict
from statistics import mean

EXECUTION_AUTHORITY=False

def summarize(cases:list[dict],min_sample:int=5)->list[dict]:
 groups=defaultdict(list)
 for c in cases:
  key=(str(c.get("pattern")),str(c.get("regime")),int(c.get("horizon_seconds",0)))
  groups[key].append(c)
 out=[]
 for (pattern,regime,h),rows in groups.items():
  if len(rows)<min_sample:continue
  net=[float(r["net_return_after_friction"]) for r in rows]
  mfe=[float(r.get("mfe",0)) for r in rows];mae=[float(r.get("mae",0)) for r in rows]
  wins=sum(x>0 for x in net)
  row={
   "pattern":pattern,"regime":regime,"horizon_seconds":h,"sample_size":len(rows),
   "positive_outcome_frequency":wins/len(rows),"mean_net_return_after_friction":mean(net),
   "mean_mfe":mean(mfe),"mean_mae":mean(mae),
   "candidate_strategy":True,"calibrated_probability_claimed":False,
   "execution_authority":False
  }
  out.append(row)
 out.sort(key=lambda x:(-x["sample_size"],x["pattern"],x["regime"],x["horizon_seconds"]))
 return out
