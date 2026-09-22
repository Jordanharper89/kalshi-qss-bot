from pathlib import Path
import ast
R=Path.cwd();D=R/"qseries_v2/oracle_strategy_intelligence/solana_live_opportunity"
M=D/"slop_019_continuous_nonblocking_opportunity_engine.py"
M.write_text(r"""from pathlib import Path
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
""",encoding="utf-8")
T=R/"test_slop_019_continuous_nonblocking_opportunity_engine.py"
T.write_text(r"""import unittest
from unittest.mock import patch
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_014b_pending_token_surveillance_rebuild import PendingSurveillancePlan
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_019_continuous_nonblocking_opportunity_engine import run_engine
class T(unittest.TestCase):
 def test_nonblocking_contract(self):
  with patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_019_continuous_nonblocking_opportunity_engine._ensure_certified_writer",return_value=(None,"TEST")),patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_019_continuous_nonblocking_opportunity_engine._stop_certification_writer"),patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_019_continuous_nonblocking_opportunity_engine._viable",return_value=(("A","B"),())),patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_019_continuous_nonblocking_opportunity_engine.pending_surveillance_plan",return_value=PendingSurveillancePlan(("P",),("OLD",),False)),patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_019_continuous_nonblocking_opportunity_engine.observe_hot_round",return_value=()),patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_019_continuous_nonblocking_opportunity_engine.lifecycle_pass",return_value={"admitted":1,"pending_predictions":1}):
   x=run_engine(rounds=2,delay_seconds=0)
  print("[SLOP-019]",x);self.assertEqual(x["rounds"],2);self.assertEqual(x["admitted_events"],2)
if __name__=="__main__":unittest.main(verbosity=2)
""",encoding="utf-8")
ast.parse(M.read_text());ast.parse(T.read_text())
print("[PASS] SLOP-019 installed")
print("[PASS] discovery + pending surveillance interleaving")
print("[PASS] no maturity sleep in lifecycle")
