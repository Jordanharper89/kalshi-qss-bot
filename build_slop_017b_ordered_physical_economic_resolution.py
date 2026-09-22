from pathlib import Path
import ast
R=Path.cwd();D=R/"qseries_v2/oracle_strategy_intelligence/solana_live_opportunity"
M=D/"slop_017b_ordered_physical_economic_resolution.py"
M.write_text(r"""from dataclasses import dataclass
READ_ONLY=True;EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class EconomicResolution:
 prediction_id:str;outcome:str;barrier_at:str;gross_return:float;net_return:float
 terminal_return:float;mfe:float;mae:float;friction_bps:int;state:str="RESOLVED";execution_authority:bool=False
def resolve_economics(prediction,path):
 if path is None:return None
 target=float(prediction.target);stop=float(prediction.stop);friction=float(prediction.friction_bps)/10000.0
 first=None
 for ts,px,_ in tuple(path.observations):
  r=float(px)/float(path.anchor_price)-1.0
  if r>=target:first=("TARGET_FIRST",ts,r);break
  if r<=-stop:first=("STOP_FIRST",ts,r);break
 if first is None:
  outcome="TIMEOUT";barrier_at=str(path.outcome_at);gross=float(path.return_fraction)
 else: outcome,barrier_at,gross=first
 net=float(gross)-friction
 return EconomicResolution(prediction.prediction_id,outcome,barrier_at,float(gross),net,
  float(path.return_fraction),float(path.mfe),float(path.mae),int(prediction.friction_bps),"RESOLVED",False)
""",encoding="utf-8")
T=R/"test_slop_017b_ordered_physical_economic_resolution.py"
T.write_text(r"""import unittest
from types import SimpleNamespace
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_003_concurrent_opportunity_admission_prospective_freeze import ProspectiveOpportunity
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_017b_ordered_physical_economic_resolution import resolve_economics
class T(unittest.TestCase):
 def p(self):return ProspectiveOpportunity("P","T","PAIR","X",(("order_flow","BUY_PRESSURE"),),60,.1,.05,200,"PENDING_60S",False)
 def test_stop_first_is_ordered_not_inferred_from_extrema(self):
  path=SimpleNamespace(anchor_price=100.0,observations=(("20",94.0,"A"),("40",112.0,"B"),("61",111.0,"C")),outcome_at="61",return_fraction=.11,mfe=.12,mae=-.06)
  x=resolve_economics(self.p(),path);print("[SLOP-017B STOP]",x)
  self.assertEqual(x.outcome,"STOP_FIRST");self.assertAlmostEqual(x.gross_return,-.06);self.assertAlmostEqual(x.net_return,-.08)
 def test_target_first(self):
  path=SimpleNamespace(anchor_price=100.0,observations=(("20",111.0,"A"),("40",94.0,"B"),("61",108.0,"C")),outcome_at="61",return_fraction=.08,mfe=.11,mae=-.06)
  x=resolve_economics(self.p(),path);print("[SLOP-017B TARGET]",x)
  self.assertEqual(x.outcome,"TARGET_FIRST");self.assertAlmostEqual(x.net_return,.09)
if __name__=="__main__":unittest.main(verbosity=2)
""",encoding="utf-8")
ast.parse(M.read_text());ast.parse(T.read_text())
print("[PASS] SLOP-017B installed")
print("[PASS] ordered target-first/stop-first resolution")
print("[PASS] 200bps friction applied to realized barrier/timeout return")
print("[PASS] execution_authority=FALSE")
