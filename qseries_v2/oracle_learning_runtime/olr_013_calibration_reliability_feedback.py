from __future__ import annotations
from dataclasses import dataclass
from .olr_012_market_learned_context import MarketLearnedContext

@dataclass(frozen=True)
class LearnedFeedback:
    market_ticker: str
    prior_confidence: float
    reliability_multiplier: float
    calibrated_confidence: float

def apply_calibration_reliability(context: MarketLearnedContext, prior_confidence: float) -> LearnedFeedback:
    prior=max(0.0,min(1.0,float(prior_confidence)))
    multiplier=0.5 + context.learned_confidence
    calibrated=max(0.0,min(1.0,0.5 + (prior-0.5)*multiplier))
    return LearnedFeedback(context.market_ticker,prior,multiplier,calibrated)

def verify_olr_013_calibration_reliability_feedback():
    c=MarketLearnedContext("KX",1.0,0.7,100)
    x=apply_calibration_reliability(c,0.6)
    return x.market_ticker=="KX" and 0.0 <= x.calibrated_confidence <= 1.0
