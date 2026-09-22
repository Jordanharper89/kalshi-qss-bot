from __future__ import annotations
from dataclasses import dataclass
from .olr_023_market_behavior_calibration_profile import MarketBehaviorCalibrationProfile

OLR_024_BUILD_ID="OLR-024"
OLR_024_REVISION="OLR_024_CALIBRATION_BEHAVIOR_FEEDBACK_ENVELOPE_V1"

@dataclass(frozen=True)
class CalibrationBehaviorFeedbackEnvelope:
    market_ticker:str
    samples:int
    reliability_weight:float
    calibration_bias:float
    bounded_probability_adjustment:float
    behavior_signal_available:bool
    advisory_only:bool=True
    execution_authority:bool=False

def build_calibration_behavior_feedback(profile:MarketBehaviorCalibrationProfile,max_adjustment=.05,min_samples=5):
    if profile.samples < int(min_samples):
        adjustment=0.0
        available=False
    else:
        raw=profile.calibration_bias*profile.reliability_weight
        cap=abs(float(max_adjustment))
        adjustment=max(-cap,min(cap,raw))
        available=True
    return CalibrationBehaviorFeedbackEnvelope(
        profile.market_ticker,profile.samples,profile.reliability_weight,
        profile.calibration_bias,adjustment,available,True,False
    )

def verify_olr_024_calibration_behavior_feedback_envelope():
    p=MarketBehaviorCalibrationProfile("KX",50,.55,.60,.2,.3,.05,1.0,True,False)
    x=build_calibration_behavior_feedback(p)
    return x.behavior_signal_available and 0 < x.bounded_probability_adjustment <= .05 and not x.execution_authority
