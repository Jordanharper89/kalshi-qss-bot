from __future__ import annotations
from dataclasses import dataclass

from .oad_235_prospective_calibration_source_reliability_materialization import (
    materialize_prospective_calibration_source_reliability,
)
from .oad_236_prospective_adaptive_ocl029_readmission import (
    run_prospective_adaptive_ocl029_readmission,
)

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class ProspectiveLearningStateRefresh:
    calibration_state_hash:str|None
    source_reliability_state_hash:str|None
    adaptive_weight_state_hash:str|None
    calibration_state:str
    adaptive_state:str
    admission_state:str
    handoff_verified:bool
    probability_enabled:bool=False
    direction_enabled:bool=False
    publication_allowed:bool=False
    execution_authority:bool=False

def refresh_prospective_learning_states(root=None):
    calibration=materialize_prospective_calibration_source_reliability(root)
    adaptive=run_prospective_adaptive_ocl029_readmission(root)
    return ProspectiveLearningStateRefresh(
        calibration_state_hash=calibration.calibration_state_hash,
        source_reliability_state_hash=calibration.source_reliability_state_hash,
        adaptive_weight_state_hash=adaptive.adaptive_weight_state_hash,
        calibration_state=str(calibration.state),
        adaptive_state=str(adaptive.adaptive_state),
        admission_state=str(adaptive.admission_state),
        handoff_verified=bool(adaptive.handoff_verified),
    )
