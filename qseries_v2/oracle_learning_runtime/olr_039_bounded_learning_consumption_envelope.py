from __future__ import annotations
from dataclasses import dataclass
from .olr_036_live_feedback_read_model import LiveCalibrationFeedback
from .olr_037_learning_maturity_gate import evaluate_learning_maturity
from .olr_038_learning_staleness_contradiction_guard import evaluate_learning_guard

OLR_039_BUILD_ID="OLR-039"
OLR_039_REVISION="OLR_039_BOUNDED_LEARNING_CONSUMPTION_ENVELOPE_V1"

@dataclass(frozen=True)
class BoundedLearningConsumptionEnvelope:
    market_ticker:str
    available:bool
    reason:str
    bounded_adjustment:float
    samples:int
    behavior_class:str
    advisory_only:bool=True
    execution_authority:bool=False

def build_bounded_learning_consumption(feedback:LiveCalibrationFeedback,updated_at=None,contradiction_score=0.0,max_adjustment=.05):
    maturity=evaluate_learning_maturity(feedback)
    if not maturity.eligible:
        return BoundedLearningConsumptionEnvelope(feedback.market_ticker,False,maturity.reason,0.0,feedback.samples,feedback.behavior_class,True,False)
    guard=evaluate_learning_guard(updated_at,contradiction_score=contradiction_score)
    if not guard.allowed:
        return BoundedLearningConsumptionEnvelope(feedback.market_ticker,False,guard.reason,0.0,feedback.samples,feedback.behavior_class,True,False)
    cap=abs(float(max_adjustment))
    raw=feedback.calibration_bias*feedback.reliability_weight
    adj=max(-cap,min(cap,raw))
    return BoundedLearningConsumptionEnvelope(feedback.market_ticker,True,"eligible",adj,feedback.samples,feedback.behavior_class,True,False)

def verify_olr_039_bounded_learning_consumption_envelope():
    f=LiveCalibrationFeedback("KX",20,.10,.2,.4,True,"historically_underpriced_yes",True,False)
    x=build_bounded_learning_consumption(f)
    return x.available and 0 < x.bounded_adjustment <= .05 and not x.execution_authority
