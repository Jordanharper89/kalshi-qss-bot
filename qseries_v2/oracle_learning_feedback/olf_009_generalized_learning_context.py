from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

from .olf_008_related_market_learning_resolver import resolve_related_market_learning
from qseries_v2.oracle_learning_runtime.olr_036_live_feedback_read_model import load_live_feedback_snapshot
from qseries_v2.oracle_learning_runtime.olr_039_bounded_learning_consumption_envelope import build_bounded_learning_consumption

OLF_009_BUILD_ID="OLF-009"
OLF_009_REVISION="OLF_009_GENERALIZED_REASONING_LEARNING_CONTEXT_V1"

@dataclass(frozen=True)
class GeneralizedLearningContext:
    market_ticker:str
    relationship_type:str
    relationship_strength:float
    source_markets:tuple
    learned_records:int
    experience_weight:float
    learner_state_hash:str
    learning_context_consumed:bool
    calibration_applied:bool
    bounded_confidence_adjustment:float
    advisory_only:bool=True
    execution_authority:bool=False

def build_generalized_learning_context(root=None,market_ticker=""):
    root=Path(root or Path.cwd()).resolve()
    r=resolve_related_market_learning(root,market_ticker)
    calibration=False;adjustment=0.0

    # Calibration is intentionally exact-market only.
    # Historical same-series experience may inform reasoning context, but cannot
    # transfer a directional calibration bias to a different contract.
    if r.relationship_type=="EXACT_TICKER":
        feedback=load_live_feedback_snapshot(root).get(r.market_ticker)
        if feedback is not None:
            bounded=build_bounded_learning_consumption(feedback)
            calibration=bool(bounded.available)
            adjustment=float(bounded.bounded_adjustment) if bounded.available else 0.0

    return GeneralizedLearningContext(
        r.market_ticker,r.relationship_type,r.relationship_strength,r.source_markets,
        r.learned_records,r.generalized_experience_weight,r.learner_state_hash,
        r.available,calibration,adjustment,True,False
    )

def apply_generalized_confidence_context(base_confidence,context):
    base=max(0.0,min(1.0,float(base_confidence)))
    if not context.calibration_applied:return base
    return max(0.0,min(1.0,base+context.bounded_confidence_adjustment))

def verify_olf_009_generalized_reasoning_learning_context():
    x=GeneralizedLearningContext("KX","SAME_KALSHI_SERIES",.75,("A",),4,.12,"h",True,False,0.0,True,False)
    return x.learning_context_consumed and apply_generalized_confidence_context(.6,x)==.6 and not x.execution_authority
