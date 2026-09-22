from __future__ import annotations
from dataclasses import dataclass
from .olr_011_learned_state_read_projection import LearnedStateProjection
from .olr_012_market_learned_context import build_market_learned_context
from .olr_013_calibration_reliability_feedback import apply_calibration_reliability
from .olr_014_scientific_reasoning_context_injection import inject_learned_feedback

@dataclass(frozen=True)
class LearnedStateFeedbackRuntimeSummary:
    market_ticker: str
    learning_applied: bool
    learned_confidence: float
    execution_authority: bool

def run_learned_state_feedback_cycle(projection: LearnedStateProjection, base_confidence: float) -> LearnedStateFeedbackRuntimeSummary:
    context=build_market_learned_context(projection)
    feedback=apply_calibration_reliability(context,base_confidence)
    reasoning=inject_learned_feedback(projection.market_ticker,base_confidence,feedback)
    return LearnedStateFeedbackRuntimeSummary(reasoning.market_ticker,reasoning.learning_applied,reasoning.learned_confidence,False)

def verify_olr_015_learned_state_feedback_runtime_gate():
    p=LearnedStateProjection("KXTEST",10,6,4,0.6,0.9)
    x=run_learned_state_feedback_cycle(p,0.55)
    return x.learning_applied and x.execution_authority is False
