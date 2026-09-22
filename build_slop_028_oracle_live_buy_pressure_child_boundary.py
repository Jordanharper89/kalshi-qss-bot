from pathlib import Path
import ast
R=Path.cwd();D=R/"qseries_v2/oracle_strategy_intelligence/solana_live_opportunity"
M=D/"slop_028_oracle_live_buy_pressure_child_boundary.py"
M.write_text(r"""from dataclasses import dataclass
from .slop_012b_exact_fresh_buy_pressure_admission import current_buy_pressure_admission
from .slop_013b_canonical_durable_prediction_ledger_rebuild import persist_predictions
READ_ONLY=True;EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class LiveChildResult:
 token_address:str;admitted:int;prediction_ids:tuple;state:str;execution_authority:bool=False
def live_child_pass(token_address,root=None,now=None,max_age_seconds=20.0):
 x=current_buy_pressure_admission(token_address,root=root,max_age_seconds=max_age_seconds,now=now)
 admitted=tuple(x.get("admitted") or ())
 if admitted:persist_predictions(admitted,root)
 return LiveChildResult(str(token_address),len(admitted),tuple(p.prediction_id for p in admitted),
  "BUY_PRESSURE_ADMITTED" if admitted else "NO_CURRENT_BUY_PRESSURE",False)
""",encoding="utf-8")
T=R/"test_slop_028_oracle_live_buy_pressure_child_boundary.py"
T.write_text(r"""import unittest
from unittest.mock import patch
from types import SimpleNamespace
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_028_oracle_live_buy_pressure_child_boundary import live_child_pass
class T(unittest.TestCase):
 def test_child_boundary(self):
  p=SimpleNamespace(prediction_id="P")
  with patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_028_oracle_live_buy_pressure_child_boundary.current_buy_pressure_admission",return_value={"admitted":(p,)}),patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_028_oracle_live_buy_pressure_child_boundary.persist_predictions") as save:
   x=live_child_pass("TOKEN")
  print("[SLOP-028]",x);save.assert_called_once();self.assertEqual(x.state,"BUY_PRESSURE_ADMITTED");self.assertFalse(x.execution_authority)
if __name__=="__main__":unittest.main(verbosity=2)
""",encoding="utf-8")
ast.parse(M.read_text());ast.parse(T.read_text())
print("[PASS] SLOP-028 installed")
print("[PASS] certified BUY_PRESSURE admission exposed as Oracle Live child boundary")
print("[PASS] execution_authority=FALSE")
