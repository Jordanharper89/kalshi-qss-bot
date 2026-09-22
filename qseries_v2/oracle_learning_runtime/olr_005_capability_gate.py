from __future__ import annotations
from dataclasses import dataclass
from .olr_001_foundation import verify_olr_001_oracle_learning_runtime_foundation
from .olr_002_settled_outcome_read_model import verify_olr_002_kalshi_settled_outcome_read_model
from .olr_003_learning_event_bridge import verify_olr_003_evidence_outcome_learning_event_bridge
from .olr_004_learning_cycle_state import verify_olr_004_durable_continuous_learning_cycle
OLR_005_BUILD_ID="OLR-005"
OLR_005_REVISION="OLR_005_CONTINUOUS_LEARNING_RUNTIME_GATE_V1"

@dataclass(frozen=True)
class OLR005Certification:
    builds:tuple[str,...]
    capability:str
    runtime_command:str
    certified:bool=True

def certify_olr_001_through_005():
    if not all((
        verify_olr_001_oracle_learning_runtime_foundation(),
        verify_olr_002_kalshi_settled_outcome_read_model(),
        verify_olr_003_evidence_outcome_learning_event_bridge(),
        verify_olr_004_durable_continuous_learning_cycle(),
    )):
        raise RuntimeError("OLR certification failed")
    return OLR005Certification(
        tuple("OLR-%03d"%i for i in range(1,6)),
        "outcome_grounded_continuous_learning_runtime",
        "run_oracle_LIVE.py",
        True,
    )

def verify_olr_005_continuous_learning_runtime_gate():
    return certify_olr_001_through_005().certified
