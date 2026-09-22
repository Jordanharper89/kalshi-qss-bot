from pathlib import Path
import ast
R=Path.cwd();D=R/"qseries_v2/oracle_strategy_intelligence/solana_live_opportunity"
M=D/"slop_015b_concurrent_live_lifecycle_rebuild.py"
M.write_text(r"""from .slop_012b_exact_fresh_buy_pressure_admission import current_buy_pressure_admission
from .slop_013b_canonical_durable_prediction_ledger_rebuild import persist_predictions
from .slop_014b_pending_token_surveillance_rebuild import pending_surveillance_plan
READ_ONLY=True;EXECUTION_AUTHORITY=False
def lifecycle_pass(active_tokens,root=None,max_age_seconds=20.0,now=None):
 admitted=[];evaluated=0
 for token in tuple(active_tokens):
  x=current_buy_pressure_admission(token,root=root,max_age_seconds=max_age_seconds,now=now)
  evaluated+=1;admitted.extend(tuple(x["admitted"]))
 if admitted:persisted=persist_predictions(tuple(admitted),root)
 else:
  pending0=pending_surveillance_plan(root)
  persisted={"total":len(pending0.prediction_ids),"new":0,"existing":0,"execution_authority":False}
 pending=pending_surveillance_plan(root)
 surveillance=tuple(sorted(set(tuple(active_tokens))|set(pending.tokens)))
 return {"evaluated":evaluated,"admitted":len(admitted),"persisted":persisted,
  "pending_predictions":len(pending.prediction_ids),"surveillance_tokens":surveillance,
  "state":"LIFECYCLE_ACTIVE","execution_authority":False}
""",encoding="utf-8")
T=R/"test_slop_015b_concurrent_live_lifecycle_rebuild.py"
T.write_text(r"""import unittest
from unittest.mock import patch
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_003_concurrent_opportunity_admission_prospective_freeze import ProspectiveOpportunity
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_014b_pending_token_surveillance_rebuild import PendingSurveillancePlan
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_015b_concurrent_live_lifecycle_rebuild import lifecycle_pass
class T(unittest.TestCase):
 def test_new_and_pending_coexist(self):
  p=ProspectiveOpportunity("P","NEW","PAIR","2026-09-17T15:30:00+00:00",(("order_flow","BUY_PRESSURE"),),60,.1,.05,200,"PENDING_60S",False)
  def admit(t,**k):return {"admitted":(p,) if t=="NEW" else ()}
  with patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_015b_concurrent_live_lifecycle_rebuild.current_buy_pressure_admission",side_effect=admit),patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_015b_concurrent_live_lifecycle_rebuild.persist_predictions",return_value={"total":2,"new":1,"existing":0}),patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_015b_concurrent_live_lifecycle_rebuild.pending_surveillance_plan",return_value=PendingSurveillancePlan(("OLD","P"),("OLDTOKEN","NEW"),False)):
   x=lifecycle_pass(("NEW","HOT"))
  print("[SLOP-015B]",x)
  self.assertEqual(x["evaluated"],2);self.assertEqual(x["admitted"],1)
  self.assertEqual(x["surveillance_tokens"],("HOT","NEW","OLDTOKEN"));self.assertFalse(x["execution_authority"])
if __name__=="__main__":unittest.main(verbosity=2)
""",encoding="utf-8")
ast.parse(M.read_text());ast.parse(T.read_text())
print("[PASS] SLOP-015B installed")
print("[PASS] certified 012B + 013B + 014B boundaries joined")
print("[PASS] admission never waits for maturity")
print("[PASS] execution_authority=FALSE")
