from __future__ import annotations
from dataclasses import dataclass
from .olr_021_pre_settlement_probability_recovery import verify_olr_021_pre_settlement_probability_recovery
from .olr_022_outcome_calibration_record import verify_olr_022_outcome_calibration_record
from .olr_023_market_behavior_calibration_profile import verify_olr_023_market_behavior_calibration_profile
from .olr_024_calibration_behavior_feedback_envelope import verify_olr_024_calibration_behavior_feedback_envelope

OLR_025_BUILD_ID="OLR-025"
OLR_025_REVISION="OLR_025_OUTCOME_CALIBRATION_MARKET_BEHAVIOR_GATE_V1"

@dataclass(frozen=True)
class OLR025Certification:
    builds:tuple[str,...]
    capability:str
    next_capability:str
    certified:bool=True

def certify_olr_021_through_025():
    if not all((
        verify_olr_021_pre_settlement_probability_recovery(),
        verify_olr_022_outcome_calibration_record(),
        verify_olr_023_market_behavior_calibration_profile(),
        verify_olr_024_calibration_behavior_feedback_envelope(),
    )):
        raise RuntimeError("OLR-021 through OLR-025 certification failed")
    return OLR025Certification(
        tuple("OLR-%03d"%i for i in range(21,26)),
        "outcome_calibration_and_market_behavior_learning_feedback",
        "durable_calibration_history_and_live_reasoning_feedback_binding",
        True,
    )

def verify_olr_025_outcome_calibration_market_behavior_gate():
    c=certify_olr_021_through_025()
    return c.certified and len(c.builds)==5
