from pathlib import Path
import time
from .slop_010b_viable_pool_surveillance_rebuild import _viable
from .slop_008_round_robin_hot_token_observer import observe_hot_round
from .slop_015b_concurrent_live_lifecycle_rebuild import lifecycle_pass
from .slop_014b_pending_token_surveillance_rebuild import pending_surveillance_plan
from qseries_v2.oracle_adapters.independent.oad_312_solana_continuous_temporal_history_activation_gate import _ensure_certified_writer,_stop_certification_writer
READ_ONLY=True;EXECUTION_AUTHORITY=False
def run_engine(root=None,rounds=6,token_limit=5,refresh_every=3,delay_seconds=5.0,progress=print):
 root=Path(root or Path.cwd()).resolve();proc=None;active=();seen=set();admitted=0
 try:
  proc,ws=_ensure_certified_writer(root,progress)
  for r in range(1,int(rounds)+1):
   if r==1 or r%max(1,int(refresh_every))==0:
    fresh,_=_viable(token_limit);seen.update(fresh);active=tuple(fresh)
   pending=pending_surveillance_plan(root)
   surveillance=tuple(sorted(set(active)|set(pending.tokens)))
   observe_hot_round(surveillance,root=root,cycle_base=r*10000,progress=progress)
   life=lifecycle_pass(active,root=root);admitted+=int(life["admitted"])
   progress(f"[ENGINE] round={r} active={len(active)} surveillance={len(surveillance)} admitted={life['admitted']} pending={life['pending_predictions']}")
   if r<int(rounds):time.sleep(float(delay_seconds))
  return {"rounds":int(rounds),"discovered_unique":len(seen),"admitted_events":admitted,
   "pending":len(pending_surveillance_plan(root).prediction_ids),"writer_state":ws,
   "state":"NONBLOCKING_ENGINE_COMPLETE","execution_authority":False}
 finally:_stop_certification_writer(proc,progress)
