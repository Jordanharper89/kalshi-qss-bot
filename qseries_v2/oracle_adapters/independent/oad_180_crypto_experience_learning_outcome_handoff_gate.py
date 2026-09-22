from __future__ import annotations
from dataclasses import dataclass
from qseries_v2.oracle_continuous_learner.ocl_003_outcome_observation import verify_outcome_observation
from qseries_v2.oracle_continuous_learner.ocl_004_learning_event import assemble_learning_event,verify_learning_event

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class CryptoLearningHandoffGate:
    experience_id:str
    evidence_ready:bool
    lineage_ready:bool
    outcome_ready:bool
    learning_event_ready:bool
    learning_event_hash:str|None
    gate_state:str
    read_only:bool=True
    execution_authority:bool=False

def evaluate_crypto_learning_handoff(candidate,lineage,outcome=None):
    evidence_ready=len(candidate.evidence_hash)==64 and len(candidate.condition_hash)==64
    lineage_ready=len(lineage.lineage_hash)==64 and lineage.experience_id==candidate.experience_id
    outcome_ready=bool(outcome is not None and verify_outcome_observation(outcome))
    event=None
    if evidence_ready and lineage_ready and outcome_ready:
        if outcome.subject_id!=candidate.asset:
            raise ValueError("crypto outcome subject must match experience asset")
        event=assemble_learning_event(candidate.asset,candidate.evidence_hash,lineage.lineage_hash,outcome)
        if not verify_learning_event(event):
            raise RuntimeError("OCL learning event verification failed")
    ready=event is not None
    state="READY_FOR_OCL_LEARNING_EVENT" if ready else "HOLD_OUTCOME_REQUIRED"
    return CryptoLearningHandoffGate(
        candidate.experience_id,evidence_ready,lineage_ready,outcome_ready,ready,
        None if event is None else event.event_hash,state,True,False
    )
