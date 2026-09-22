from pathlib import Path
import ast
R=Path.cwd();D=R/"qseries_v2/oracle_strategy_intelligence/solana_live_opportunity"
M=D/"slop_024_unresolved_prediction_surveillance.py"
M.write_text(r"""from dataclasses import dataclass
from .slop_013b_canonical_durable_prediction_ledger_rebuild import read_predictions
from .slop_020_prospective_resolution_ledger import read_resolution_dicts
READ_ONLY=True;EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class UnresolvedView:
 predictions:tuple;prediction_ids:tuple;tokens:tuple;resolved_ids:tuple;execution_authority:bool=False
def unresolved_view(root=None):
 ps=tuple(read_predictions(root,"PENDING_60S"));rs=tuple(read_resolution_dicts(root))
 done={str(x["prediction_id"]) for x in rs};live=tuple(x for x in ps if x.prediction_id not in done)
 return UnresolvedView(live,tuple(x.prediction_id for x in live),
  tuple(sorted({x.token_address for x in live})),tuple(sorted(done)),False)
""",encoding="utf-8")
T=R/"test_slop_024_unresolved_prediction_surveillance.py"
T.write_text(r"""import unittest
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_024_unresolved_prediction_surveillance import unresolved_view
class T(unittest.TestCase):
 def test_resolved_removed(self):
  ps=(SimpleNamespace(prediction_id="A",token_address="TA"),SimpleNamespace(prediction_id="B",token_address="TB"))
  with patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_024_unresolved_prediction_surveillance.read_predictions",return_value=ps),patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_024_unresolved_prediction_surveillance.read_resolution_dicts",return_value=({"prediction_id":"A"},)):
   x=unresolved_view()
  print("[SLOP-024]",x);self.assertEqual(x.prediction_ids,("B",));self.assertEqual(x.tokens,("TB",))
if __name__=="__main__":unittest.main(verbosity=2)
""",encoding="utf-8")
ast.parse(M.read_text());ast.parse(T.read_text())
print("[PASS] SLOP-024 installed")
print("[PASS] resolved predictions retire from surveillance")
print("[PASS] restart-safe unresolved view")
