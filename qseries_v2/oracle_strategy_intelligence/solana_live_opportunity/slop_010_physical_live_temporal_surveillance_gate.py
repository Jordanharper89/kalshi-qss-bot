from pathlib import Path
import time
from .slop_001_live_universe_discovery_boundary import discover_live_universe
from .slop_006_live_hot_token_surveillance_registry import HotTokenRegistry
from .slop_008_round_robin_hot_token_observer import observe_hot_round
from .slop_009_continuous_discovery_refresh_controller import plan_refresh
from qseries_v2.oracle_adapters.independent.oad_274_solana_multi_horizon_condition_windows import read_pinned_pool_history
from qseries_v2.oracle_adapters.independent.oad_312_solana_continuous_temporal_history_activation_gate import _ensure_certified_writer,_stop_certification_writer
READ_ONLY=True;EXECUTION_AUTHORITY=False
def certify_temporal_surveillance(root=None,hot_limit=5,rounds=14,delay_seconds=5.0,refresh_every=3,progress=print):
 root=Path(root or Path.cwd()).resolve();reg=HotTokenRegistry();proc=None;scans=refreshes=0
 try:
  proc,ws=_ensure_certified_writer(root,progress)
  for r in range(1,int(rounds)+1):
   if plan_refresh(r,refresh_every).refresh_discovery:
    u=discover_live_universe(limit=hot_limit);reg.refresh(u.tokens);refreshes+=1
   active=reg.tokens()[-int(hot_limit):]
   observe_hot_round(active,root=root,cycle_base=r*100,progress=progress);scans+=len(active)
   if r<int(rounds):time.sleep(float(delay_seconds))
  ready=[];states=[]
  for t in reg.tokens():
   h=read_pinned_pool_history(t,root=root,limit=4096)
   span=0 if len(h)<2 else (max(x.observed_at for x in h),min(x.observed_at for x in h))
   from .slop_007_temporal_readiness_gate import temporal_readiness
   q=temporal_readiness(t,h);states.append(q)
   if q.ready:ready.append(t)
   progress(f"[READY] token={t} records={q.records} span={q.span_seconds:.3f} state={q.state}")
  return {"refreshes":refreshes,"observations":scans,"tracked":len(reg.tokens()),"ready_60s":len(ready),
   "states":tuple(states),"writer_state":ws,"execution_authority":False}
 finally:_stop_certification_writer(proc,progress)
