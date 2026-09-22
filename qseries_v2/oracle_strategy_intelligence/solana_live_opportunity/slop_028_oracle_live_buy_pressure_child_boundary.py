from dataclasses import dataclass
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
