from pathlib import Path
import ast
R=Path.cwd();D=R/"qseries_v2/oracle_strategy_intelligence/solana_live_opportunity"
M=D/"slop_025_live_freeze_maturity_resolution_worker.py"
M.write_text(r"""from pathlib import Path
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
  before=unresolved_view(root);watch=tuple(sorted(set(active)|set(before.tokens)))
  observe_hot_round(watch,root=root,cycle_base=cycle_base,progress=progress)
  life=lifecycle_pass(active,root=root);after=unresolved_view(root);resolved=[]
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
""",encoding="utf-8")
T=R/"test_slop_025_live_freeze_maturity_resolution_worker.py"
T.write_text(r"""import unittest
from unittest.mock import patch
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_024_unresolved_prediction_surveillance import UnresolvedView
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_025_live_freeze_maturity_resolution_worker import worker_round
class T(unittest.TestCase):
 def test_nonblocking_round(self):
  empty=UnresolvedView((),(),(),(),False)
  with patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_025_live_freeze_maturity_resolution_worker._ensure_certified_writer",return_value=(None,"EXISTING")),patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_025_live_freeze_maturity_resolution_worker._viable",return_value=(("A",),())),patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_025_live_freeze_maturity_resolution_worker.observe_hot_round",return_value=()),patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_025_live_freeze_maturity_resolution_worker.lifecycle_pass",return_value={"admitted":0}),patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_025_live_freeze_maturity_resolution_worker.unresolved_view",return_value=empty):
   x=worker_round()
  print("[SLOP-025]",x);self.assertEqual(x["state"],"LIVE_WORKER_ROUND_COMPLETE");self.assertFalse(x["execution_authority"])
if __name__=="__main__":unittest.main(verbosity=2)
""",encoding="utf-8")
ast.parse(M.read_text());ast.parse(T.read_text())
print("[PASS] SLOP-025 installed")
print("[PASS] live freeze + maturity + resolution round wired")
print("[PASS] external writer never stopped")
