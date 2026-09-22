from dataclasses import dataclass
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
