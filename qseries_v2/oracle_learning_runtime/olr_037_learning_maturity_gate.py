from __future__ import annotations
from dataclasses import dataclass
from .olr_036_live_feedback_read_model import LiveCalibrationFeedback

OLR_037_BUILD_ID="OLR-037"
OLR_037_REVISION="OLR_037_LEARNING_MATURITY_GATE_V1"

@dataclass(frozen=True)
class LearningMaturityDecision:
    market_ticker:str
    eligible:bool
    reason:str
    samples:int
    reliability_weight:float
    execution_authority:bool=False

def evaluate_learning_maturity(feedback:LiveCalibrationFeedback,min_samples=5,min_reliability=.10):
    if feedback.samples<int(min_samples):
        return LearningMaturityDecision(feedback.market_ticker,False,"insufficient_samples",feedback.samples,feedback.reliability_weight,False)
    if not feedback.mature:
        return LearningMaturityDecision(feedback.market_ticker,False,"not_mature",feedback.samples,feedback.reliability_weight,False)
    if feedback.reliability_weight<float(min_reliability):
        return LearningMaturityDecision(feedback.market_ticker,False,"insufficient_reliability",feedback.samples,feedback.reliability_weight,False)
    if not feedback.stable:
        return LearningMaturityDecision(feedback.market_ticker,False,"unstable_history",feedback.samples,feedback.reliability_weight,False)
    return LearningMaturityDecision(feedback.market_ticker,True,"eligible",feedback.samples,feedback.reliability_weight,False)

def verify_olr_037_learning_maturity_gate():
    f=LiveCalibrationFeedback("KX",10,.01,.2,.2,True,"well_calibrated",True,False)
    return evaluate_learning_maturity(f).eligible
