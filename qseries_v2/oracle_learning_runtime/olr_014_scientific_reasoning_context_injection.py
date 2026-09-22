from __future__ import annotations
from dataclasses import dataclass
from .olr_013_calibration_reliability_feedback import LearnedFeedback

@dataclass(frozen=True)
class ScientificReasoningContext:
    market_ticker: str
    base_confidence: float
    learned_confidence: float
    learning_applied: bool
    execution_authority: bool=False

def inject_learned_feedback(market_ticker: str, base_confidence: float, feedback: LearnedFeedback|None) -> ScientificReasoningContext:
    base=max(0.0,min(1.0,float(base_confidence)))
    learned=feedback.calibrated_confidence if feedback and feedback.market_ticker==market_ticker else base
    return ScientificReasoningContext(market_ticker,base,learned,feedback is not None and feedback.market_ticker==market_ticker,False)

def verify_olr_014_scientific_reasoning_context_injection():
    return inject_learned_feedback("KX",0.5,None).execution_authority is False
