from pathlib import Path
from .slop_010b_viable_pool_surveillance_rebuild import _viable
from .slop_008_round_robin_hot_token_observer import observe_hot_round
from .slop_015b_concurrent_live_lifecycle_rebuild import lifecycle_pass
from .slop_016b_exact_frozen_prediction_maturity_rebuild import materialize_frozen_prediction_path
from .slop_017b_ordered_physical_economic_resolution import resolve_economics
from .slop_020_prospective_resolution_ledger import persist_resolutions
from .slop_024_unresolved_prediction_surveillance import unresolved_view
from qseries_v2.oracle_adapters.independent.oad_312_solana_continuous_temporal_history_activation_gate import _ensure_certified_writer,_stop_certification_writer
READ_ONLY=True;EXECUTION_AUTHORITY=False
def worker_round(root=None,token_limit=5,cycle_base=0,progress=print):
 root=Path(root or Path.cwd()).resolve();proc=None
 try:
  proc,ws=_ensure_certified_writer(root,progress);active,_=_viable(token_limit)
  before=unresolved_view(root);pending=tuple(before.tokens);fresh=tuple(x for x in active if x not in set(pending));watch=pending+fresh[:max(0,int(token_limit)-len(pending))]
  observe_hot_round(watch,root=root,cycle_base=cycle_base,progress=progress)
  life=lifecycle_pass(fresh[:int(token_limit)],root=root);after=unresolved_view(root);resolved=[]
  for p in after.predictions:
   path=materialize_frozen_prediction_path(p,root=root)
   if path is not None:
    econ=resolve_economics(p,path)
    if econ is not None:resolved.append(econ)
  persisted=persist_resolutions(tuple(resolved),root) if resolved else {"new":0,"existing":0}
  final=unresolved_view(root)
  return {"active_tokens":len(active),"surveillance_tokens":len(watch),"admitted":life["admitted"],
   "matured":len(resolved),"resolution_new":persisted["new"],"unresolved":len(final.prediction_ids),
   "writer_state":ws,"state":"LIVE_WORKER_ROUND_COMPLETE","execution_authority":False}
 finally:
  if proc is not None:_stop_certification_writer(proc,progress)
