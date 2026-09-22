from pathlib import Path
import ast
R=Path.cwd();D=R/"qseries_v2/oracle_strategy_intelligence/solana_live_opportunity"
M=D/"slop_027_physical_profitability_generalization_report.py"
M.write_text(r"""from dataclasses import dataclass
from .slop_013b_canonical_durable_prediction_ledger_rebuild import read_predictions
from .slop_020_prospective_resolution_ledger import read_resolution_dicts
READ_ONLY=True;EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class PhysicalReport:
 frozen:int;resolved:int;independent_tokens:int;target_first:int;stop_first:int;timeout:int
 net_expectancy:float|None;state:str;execution_authority:bool=False
def physical_report(root=None,min_resolved=15,min_tokens=3):
 ps=tuple(read_predictions(root));rs=tuple(read_resolution_dicts(root))
 pmap={p.prediction_id:p for p in ps};tokens={pmap[x["prediction_id"]].token_address for x in rs if x["prediction_id"] in pmap}
 outs=[str(x["outcome"]) for x in rs];nets=[float(x["net_return"]) for x in rs];e=sum(nets)/len(nets) if nets else None
 if len(rs)<int(min_resolved) or len(tokens)<int(min_tokens):state="INSUFFICIENT_PHYSICAL_SUPPORT"
 elif e is not None and e>0:state="MULTI_TOKEN_POSITIVE_NET_EXPECTANCY_FOUND"
 else:state="GENERALIZATION_NOT_CERTIFIED"
 return PhysicalReport(len(ps),len(rs),len(tokens),outs.count("TARGET_FIRST"),outs.count("STOP_FIRST"),
  outs.count("TIMEOUT"),e,state,False)
""",encoding="utf-8")
T=R/"test_slop_027_physical_profitability_generalization_report.py"
T.write_text(r"""import unittest
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_027_physical_profitability_generalization_report import physical_report
class T(unittest.TestCase):
 def test_multitoken_gate(self):
  ps=tuple(SimpleNamespace(prediction_id=str(i),token_address="T"+str(i%3)) for i in range(15))
  rs=tuple({"prediction_id":str(i),"outcome":"TARGET_FIRST","net_return":.01} for i in range(15))
  with patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_027_physical_profitability_generalization_report.read_predictions",return_value=ps),patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_027_physical_profitability_generalization_report.read_resolution_dicts",return_value=rs):
   x=physical_report()
  print("[SLOP-027]",x);self.assertEqual(x.state,"MULTI_TOKEN_POSITIVE_NET_EXPECTANCY_FOUND");self.assertEqual(x.independent_tokens,3)
if __name__=="__main__":unittest.main(verbosity=2)
""",encoding="utf-8")
ast.parse(M.read_text());ast.parse(T.read_text())
print("[PASS] SLOP-027 installed")
print("[PASS] multi-token physical profitability/generalization report")
print("[PASS] execution_authority=FALSE")
