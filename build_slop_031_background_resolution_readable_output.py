from pathlib import Path
import ast
R=Path.cwd();D=R/"qseries_v2/oracle_strategy_intelligence/solana_live_opportunity"
M=D/"slop_031_background_resolution_readable_output.py"
M.write_text(r"""from .slop_016b_exact_frozen_prediction_maturity_rebuild import materialize_frozen_prediction_path
from .slop_017b_ordered_physical_economic_resolution import resolve_economics
from .slop_020_prospective_resolution_ledger import persist_resolutions
from .slop_024_unresolved_prediction_surveillance import unresolved_view
READ_ONLY=True;EXECUTION_AUTHORITY=False
def resolution_lines(e):
 return ("[ORACLE RESOLUTION]",f"Prediction: {e.prediction_id}",f"Outcome: {e.outcome}",
  f"Gross Return: {e.gross_return:+.6f}",f"Net After {e.friction_bps}bps: {e.net_return:+.6f}",
  f"Terminal Return: {e.terminal_return:+.6f}",f"MFE: {e.mfe:+.6f}",f"MAE: {e.mae:+.6f}",
  "Execution Authority: FALSE")
def resolve_background(root=None,progress=print):
 done=[]
 for p in unresolved_view(root).predictions:
  path=materialize_frozen_prediction_path(p,root=root)
  if path is None:continue
  e=resolve_economics(p,path)
  if e is None:continue
  persist_resolutions((e,),root);done.append(e)
  for line in resolution_lines(e):progress(line)
 return {"resolved":len(done),"prediction_ids":tuple(e.prediction_id for e in done),
  "state":"BACKGROUND_RESOLUTION_COMPLETE","execution_authority":False}
""",encoding="utf-8")
T=R/"test_slop_031_background_resolution_readable_output.py"
T.write_text(r"""import unittest
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_024_unresolved_prediction_surveillance import UnresolvedView
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_031_background_resolution_readable_output import resolve_background
class T(unittest.TestCase):
 def test_resolution_print(self):
  p=SimpleNamespace(prediction_id="P");e=SimpleNamespace(prediction_id="P",outcome="TARGET_FIRST",gross_return=.11,net_return=.09,friction_bps=200,terminal_return=.08,mfe=.12,mae=-.01)
  u=UnresolvedView((p,),("P",),("T",),(),False);lines=[]
  with patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_031_background_resolution_readable_output.unresolved_view",return_value=u),patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_031_background_resolution_readable_output.materialize_frozen_prediction_path",return_value=object()),patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_031_background_resolution_readable_output.resolve_economics",return_value=e),patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_031_background_resolution_readable_output.persist_resolutions"):
   x=resolve_background(progress=lines.append)
  print("\n".join(lines));self.assertEqual(x["resolved"],1);self.assertIn("[ORACLE RESOLUTION]",lines)
if __name__=="__main__":unittest.main(verbosity=2)
""",encoding="utf-8")
ast.parse(M.read_text());ast.parse(T.read_text())
print("[PASS] SLOP-031 installed")
print("[PASS] background maturity/resolution + readable Oracle output")
