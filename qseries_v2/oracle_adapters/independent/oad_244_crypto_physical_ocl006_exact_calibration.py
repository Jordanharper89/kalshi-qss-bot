from dataclasses import dataclass
from .oad_242_crypto_exact_prospective_forecast_outcome_binding import read_exact_prospective_bindings
from .oad_189_crypto_learned_case_exact_history_readback import read_crypto_learned_case_history
from .oad_218_existing_ocl_state_hash_envelope import envelope
from qseries_v2.oracle_continuous_learner.ocl_006_calibration_learning import CalibrationObservation
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class ExactCalibrationState:
 scored_cases:int;mean_brier:float|None;calibration_state_hash:str|None;state:str;probability_enabled:bool=False;direction_enabled:bool=False;publication_allowed:bool=False;execution_authority:bool=False
def materialize_exact_prospective_calibration(root=None):
 by={x.experience_id:x for x in read_crypto_learned_case_history(root=root,per_asset_limit=512)};rows=[]
 for b in read_exact_prospective_bindings(root):
  x=by.get(b.experience_id)
  if x is None or not b.learning_event_id:continue
  y=float(x.return_fraction)>0;p=float(b.forecast_probability);rows.append(CalibrationObservation(b.learning_event_id,p,y,(p-(1.0 if y else 0.0))**2))
 if not rows:return ExactCalibrationState(0,None,None,"HOLD_EXACT_MATURE_PROSPECTIVE_CASE_REQUIRED")
 return ExactCalibrationState(len(rows),sum(x.brier_score for x in rows)/len(rows),envelope("prospective_exact_calibration",tuple(rows)).state_hash,"MATERIALIZED")
