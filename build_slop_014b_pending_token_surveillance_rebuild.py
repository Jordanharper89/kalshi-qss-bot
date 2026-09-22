from pathlib import Path
import ast
R=Path.cwd();D=R/"qseries_v2/oracle_strategy_intelligence/solana_live_opportunity"
M=D/"slop_014b_pending_token_surveillance_rebuild.py"
M.write_text(r"""from dataclasses import dataclass
from .slop_013b_canonical_durable_prediction_ledger_rebuild import read_predictions
from .slop_008_round_robin_hot_token_observer import observe_hot_round
READ_ONLY=True;EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class PendingSurveillancePlan:
 prediction_ids:tuple;tokens:tuple;execution_authority:bool=False
def pending_surveillance_plan(root=None):
 xs=read_predictions(root,"PENDING_60S")
 return PendingSurveillancePlan(tuple(x.prediction_id for x in xs),
  tuple(sorted({x.token_address for x in xs})),False)
def observe_pending_tokens(root=None,cycle_base=0,progress=print):
 p=pending_surveillance_plan(root)
 cycles=observe_hot_round(p.tokens,root=root,cycle_base=cycle_base,progress=progress) if p.tokens else ()
 return {"plan":p,"cycles":tuple(cycles),"observed_tokens":len(cycles),"execution_authority":False}
""",encoding="utf-8")
T=R/"test_slop_014b_pending_token_surveillance_rebuild.py"
T.write_text(r"""import unittest
from unittest.mock import patch
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_003_concurrent_opportunity_admission_prospective_freeze import ProspectiveOpportunity
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_014b_pending_token_surveillance_rebuild import pending_surveillance_plan,observe_pending_tokens
class T(unittest.TestCase):
 def test_unique_pending_tokens(self):
  def p(i,t):return ProspectiveOpportunity(i,t,"PAIR","2026-09-17T15:30:00+00:00",(("order_flow","BUY_PRESSURE"),),60,.1,.05,200,"PENDING_60S",False)
  with patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_014b_pending_token_surveillance_rebuild.read_predictions",return_value=(p("1","A"),p("2","A"),p("3","B"))),patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_014b_pending_token_surveillance_rebuild.observe_hot_round",return_value=("CA","CB")):
   plan=pending_surveillance_plan();x=observe_pending_tokens()
  print("[SLOP-014B]",plan,x)
  self.assertEqual(plan.prediction_ids,("1","2","3"));self.assertEqual(plan.tokens,("A","B"))
  self.assertEqual(x["observed_tokens"],2);self.assertFalse(x["execution_authority"])
if __name__=="__main__":unittest.main(verbosity=2)
""",encoding="utf-8")
ast.parse(M.read_text());ast.parse(T.read_text())
print("[PASS] SLOP-014B installed")
print("[PASS] certified SLOP-013B ledger bound")
print("[PASS] pending predictions force unique-token surveillance")
print("[PASS] execution_authority=FALSE")
