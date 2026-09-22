from .slop_016b_exact_frozen_prediction_maturity_rebuild import materialize_frozen_prediction_path
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
