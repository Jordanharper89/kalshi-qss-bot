from __future__ import annotations
from dataclasses import dataclass
from .olr_017_market_feedback_resolver import MarketFeedbackResolution

OLR_018_BUILD_ID="OLR-018"
OLR_018_REVISION="OLR_018_SCIENTIFIC_REASONING_FEEDBACK_ENVELOPE_V1"

@dataclass(frozen=True)
class ScientificReasoningFeedbackEnvelope:
    market_ticker:str
    learned_records:int
    experience_weight:float
    feedback_eligible:bool
    directional_adjustment:float
    advisory_only:bool=True
    execution_authority:bool=False

def build_scientific_reasoning_feedback_envelope(resolution:MarketFeedbackResolution):
    # Current durable OLR ledger proves experience, not directional calibration.
    # Therefore adjustment remains exactly zero until a later certified calibration source exists.
    return ScientificReasoningFeedbackEnvelope(
        resolution.market_ticker,
        resolution.learned_records,
        resolution.experience_weight,
        resolution.eligible,
        0.0,
        True,
        False,
    )

def verify_olr_018_scientific_reasoning_feedback_envelope():
    r=MarketFeedbackResolution("KX",3,10,.12,True,False,False)
    x=build_scientific_reasoning_feedback_envelope(r)
    return x.advisory_only and x.directional_adjustment==0.0 and not x.execution_authority
