from __future__ import annotations
from dataclasses import dataclass
from .olr_027_accumulated_calibration_state import AccumulatedCalibrationState

OLR_028_BUILD_ID="OLR-028"
OLR_028_REVISION="OLR_028_MARKET_BEHAVIOR_HISTORY_V1"

@dataclass(frozen=True)
class MarketBehaviorHistory:
    market_ticker:str
    samples:int
    calibration_bias:float
    mean_brier_score:float
    reliability_weight:float
    behavior_class:str
    stable:bool
    advisory_only:bool=True
    execution_authority:bool=False

def classify_market_behavior(state:AccumulatedCalibrationState):
    if not state.mature:
        behavior="insufficient_history"
        stable=False
    else:
        b=state.calibration_bias
        if abs(b)<.03:behavior="well_calibrated"
        elif b>=.03:behavior="historically_underpriced_yes"
        else:behavior="historically_overpriced_yes"
        stable=state.reliability_weight>=.2
    return MarketBehaviorHistory(
        state.market_ticker,state.samples,state.calibration_bias,
        state.mean_brier_score,state.reliability_weight,
        behavior,stable,True,False
    )

def verify_olr_028_market_behavior_history():
    s=AccumulatedCalibrationState("KX",10,.55,.60,.2,.3,.05,.2,True,False)
    x=classify_market_behavior(s)
    return x.behavior_class=="historically_underpriced_yes" and x.advisory_only and not x.execution_authority
