import time
from .slop_025_live_freeze_maturity_resolution_worker import worker_round
from .slop_021_live_economic_funnel import economic_funnel
READ_ONLY=True;EXECUTION_AUTHORITY=False
def accumulate(root=None,rounds=20,token_limit=5,delay_seconds=5.0,progress=print):
 admitted=matured=0
 for r in range(1,int(rounds)+1):
  x=worker_round(root=root,token_limit=token_limit,cycle_base=r*100000,progress=progress)
  admitted+=int(x["admitted"]);matured+=int(x["resolution_new"])
  f=economic_funnel(root)
  progress(f"[SAMPLE] round={r} frozen={f.frozen} resolved={f.resolved} unresolved={f.unresolved} expectancy={f.net_expectancy}")
  if r<int(rounds):time.sleep(float(delay_seconds))
 f=economic_funnel(root)
 return {"rounds":int(rounds),"admitted_this_run":admitted,"resolved_this_run":matured,
  "funnel":f,"state":"PROSPECTIVE_SAMPLE_ACCUMULATED","execution_authority":False}
