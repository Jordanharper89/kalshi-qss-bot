from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

from .olf_002_market_learning_context import load_market_learning_context

OLF_003_BUILD_ID="OLF-003"
OLF_003_REVISION="OLF_003_REASONING_LEARNING_CONTEXT_ENVELOPE_V1"

@dataclass(frozen=True)
class LearningAwareReasoningContext:
    market_ticker:str
    learner_state_hash:str
    learned_records:int
    experience_weight:float
    learning_context_consumed:bool
    calibration_applied:bool
    bounded_confidence_adjustment:float
    advisory_only:bool=True
    execution_authority:bool=False

def build_learning_aware_reasoning_context(root=None,market_ticker=""):
    x=load_market_learning_context(root,market_ticker)
    consumed=bool(x.learned_records>0 or x.calibration_available)
    return LearningAwareReasoningContext(
        x.market_ticker,x.learner_state_hash,x.learned_records,x.experience_weight,
        consumed,x.calibration_available,x.bounded_adjustment,True,False
    )

def apply_bounded_confidence_context(base_confidence,context):
    base=max(0.0,min(1.0,float(base_confidence)))
    if not context.calibration_applied:
        return base
    return max(0.0,min(1.0,base+float(context.bounded_confidence_adjustment)))

def verify_olf_003_reasoning_learning_context_envelope():
    x=LearningAwareReasoningContext("KX","h",2,.08,True,False,0.0,True,False)
    return (
        apply_bounded_confidence_context(.6,x)==.6
        and x.learning_context_consumed
        and not x.execution_authority
    )
