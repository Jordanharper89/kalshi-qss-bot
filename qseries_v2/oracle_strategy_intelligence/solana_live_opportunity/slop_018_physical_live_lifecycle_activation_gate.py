from pathlib import Path
from .slop_010b_viable_pool_surveillance_rebuild import _viable
from .slop_008_round_robin_hot_token_observer import observe_hot_round
from .slop_015b_concurrent_live_lifecycle_rebuild import lifecycle_pass
from qseries_v2.oracle_adapters.independent.oad_312_solana_continuous_temporal_history_activation_gate import _ensure_certified_writer,_stop_certification_writer
READ_ONLY=True;EXECUTION_AUTHORITY=False
def activate_physical_lifecycle(root=None,token_limit=5,warm_rounds=14,progress=print):
 root=Path(root or Path.cwd()).resolve();proc=None
 try:
  proc,ws=_ensure_certified_writer(root,progress)
  tokens,rejected=_viable(token_limit)
  for r in range(1,int(warm_rounds)+1):
   observe_hot_round(tokens,root=root,cycle_base=r*1000,progress=progress)
  life=lifecycle_pass(tokens,root=root)
  return {"tokens":tokens,"rejected":rejected,"writer_state":ws,"warm_rounds":int(warm_rounds),
   "lifecycle":life,"state":"PHYSICAL_LIFECYCLE_ACTIVE","execution_authority":False}
 finally:_stop_certification_writer(proc,progress)
