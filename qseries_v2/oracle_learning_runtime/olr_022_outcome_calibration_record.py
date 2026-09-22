from __future__ import annotations
from dataclasses import dataclass
from .olr_021_pre_settlement_probability_recovery import recover_pre_settlement_probability

OLR_022_BUILD_ID="OLR-022"
OLR_022_REVISION="OLR_022_OUTCOME_CALIBRATION_RECORD_V1"

@dataclass(frozen=True)
class OutcomeCalibrationRecord:
    market_ticker:str
    probability:float
    outcome:float
    brier_score:float
    absolute_error:float
    source_key:str
    eligible:bool=True
    execution_authority:bool=False

def build_outcome_calibration_record(market_ticker:str,observation:dict,result:str):
    recovery=recover_pre_settlement_probability(observation)
    if not recovery.recovered:
        return None
    r=str(result or "").strip().lower()
    if r=="yes":outcome=1.0
    elif r=="no":outcome=0.0
    else:return None
    p=float(recovery.probability)
    return OutcomeCalibrationRecord(
        str(market_ticker),p,outcome,(p-outcome)**2,abs(p-outcome),
        recovery.source_key,True,False
    )

def verify_olr_022_outcome_calibration_record():
    x=build_outcome_calibration_record("KX",{"yes_price":80},"yes")
    return x is not None and abs(x.brier_score-.04)<1e-12 and not x.execution_authority
