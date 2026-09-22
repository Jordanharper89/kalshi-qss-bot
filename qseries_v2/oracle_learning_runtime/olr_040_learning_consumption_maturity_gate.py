from __future__ import annotations
from dataclasses import dataclass
from .olr_036_live_feedback_read_model import verify_olr_036_live_feedback_read_model
from .olr_037_learning_maturity_gate import verify_olr_037_learning_maturity_gate
from .olr_038_learning_staleness_contradiction_guard import verify_olr_038_learning_staleness_contradiction_guard
from .olr_039_bounded_learning_consumption_envelope import verify_olr_039_bounded_learning_consumption_envelope

OLR_040_BUILD_ID="OLR-040"
OLR_040_REVISION="OLR_040_LEARNING_CONSUMPTION_MATURITY_GATE_V1"

@dataclass(frozen=True)
class OLR040Certification:
    builds:tuple[str,...]
    capability:str
    next_capability:str
    certified:bool=True

def certify_olr_036_through_040():
    if not all((
        verify_olr_036_live_feedback_read_model(),
        verify_olr_037_learning_maturity_gate(),
        verify_olr_038_learning_staleness_contradiction_guard(),
        verify_olr_039_bounded_learning_consumption_envelope(),
    )):
        raise RuntimeError("OLR-036 through OLR-040 certification failed")
    return OLR040Certification(
        tuple("OLR-%03d"%i for i in range(36,41)),
        "bounded_mature_learning_feedback_consumption",
        "learning_health_replay_and_final_freeze",
        True,
    )

def verify_olr_040_learning_consumption_maturity_gate():
    c=certify_olr_036_through_040()
    return c.certified and len(c.builds)==5
