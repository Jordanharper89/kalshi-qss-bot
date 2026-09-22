from dataclasses import dataclass
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
