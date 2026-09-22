from __future__ import annotations
from dataclasses import dataclass
from .oad_218_existing_ocl_state_hash_envelope import envelope
from .oad_234_crypto_prospective_outcome_calibration_scoring import read_and_score_mature_prospective_cases
from qseries_v2.oracle_continuous_learner.ocl_006_calibration_learning import CalibrationObservation
from qseries_v2.oracle_continuous_learner.ocl_007_source_reliability import update_source_reliability

READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class ProspectiveCalibrationReliabilityState:
    scored_cases:int;calibration_state_hash:str|None;source_reliability_state_hash:str|None;source_states:tuple;state:str
    probability_enabled:bool=False;direction_enabled:bool=False;publication_allowed:bool=False;execution_authority:bool=False

def materialize_prospective_calibration_source_reliability(root=None):
    rows=read_and_score_mature_prospective_cases(root)
    if not rows:return ProspectiveCalibrationReliabilityState(0,None,None,(),"HOLD_FUTURE_PROSPECTIVE_OUTCOME_REQUIRED")
    cal=tuple(CalibrationObservation(x.learning_event_hash,x.forecast_probability,x.outcome_positive,x.brier_score) for x in rows)
    states={}
    for x in rows:
        for source,correct in x.source_correctness:states[source]=update_source_reliability(states.get(source),source,correct)
    ss=tuple(states[k] for k in sorted(states))
    return ProspectiveCalibrationReliabilityState(len(rows),envelope("calibration",cal).state_hash,envelope("source_reliability",ss).state_hash if ss else None,ss,"MATERIALIZED")
