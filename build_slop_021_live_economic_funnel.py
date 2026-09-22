from pathlib import Path
import ast
R=Path.cwd();D=R/"qseries_v2/oracle_strategy_intelligence/solana_live_opportunity"
M=D/"slop_021_live_economic_funnel.py"
M.write_text(r"""from dataclasses import dataclass
from .slop_013b_canonical_durable_prediction_ledger_rebuild import read_predictions
from .slop_020_prospective_resolution_ledger import read_resolution_dicts
READ_ONLY=True;EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class EconomicFunnel:
 frozen:int;resolved:int;target_first:int;stop_first:int;timeout:int;unresolved:int
 net_expectancy:float|None;execution_authority:bool=False
def economic_funnel(root=None):
 ps=read_predictions(root);rs=read_resolution_dicts(root)
 outcomes=[str(x["outcome"]) for x in rs];nets=[float(x["net_return"]) for x in rs]
 return EconomicFunnel(len(ps),len(rs),outcomes.count("TARGET_FIRST"),outcomes.count("STOP_FIRST"),
  outcomes.count("TIMEOUT"),max(0,len(ps)-len(rs)),(sum(nets)/len(nets) if nets else None),False)
""",encoding="utf-8")
T=R/"test_slop_021_live_economic_funnel.py"
T.write_text(r"""import unittest
from unittest.mock import patch
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_021_live_economic_funnel import economic_funnel
class T(unittest.TestCase):
 def test_accounting(self):
  with patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_021_live_economic_funnel.read_predictions",return_value=(1,2,3)),patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_021_live_economic_funnel.read_resolution_dicts",return_value=({"outcome":"TARGET_FIRST","net_return":.08},{"outcome":"STOP_FIRST","net_return":-.07})):
   x=economic_funnel()
  print("[SLOP-021]",x);self.assertEqual((x.frozen,x.resolved,x.unresolved),(3,2,1));self.assertAlmostEqual(x.net_expectancy,.005)
if __name__=="__main__":unittest.main(verbosity=2)
""",encoding="utf-8")
ast.parse(M.read_text());ast.parse(T.read_text())
print("[PASS] SLOP-021 installed")
print("[PASS] prospective economic funnel accounting")
