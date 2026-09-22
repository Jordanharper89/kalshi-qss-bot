from dataclasses import dataclass
from .oad_242_crypto_exact_prospective_forecast_outcome_binding import read_exact_prospective_bindings
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class MatureProspectiveCase:
 forecast_id:str;asset:str;experience_id:str;condition_hash:str;forecast_probability:float;source_claims:tuple;learning_event_id:str;learning_event_hash:str;outcome_hash:str;state:str="MATURE_EXACT";execution_authority:bool=False
def build_mature_prospective_case_registry(root=None):
 return tuple(MatureProspectiveCase(x.forecast_id,x.asset,x.experience_id,x.condition_hash,x.forecast_probability,x.source_claims,x.learning_event_id,x.learning_event_hash,x.outcome_hash) for x in read_exact_prospective_bindings(root) if x.learning_event_id and len(x.learning_event_hash)==64 and len(x.outcome_hash)==64)
