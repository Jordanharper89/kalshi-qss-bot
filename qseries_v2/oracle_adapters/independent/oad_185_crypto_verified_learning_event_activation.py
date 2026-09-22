from __future__ import annotations
from dataclasses import dataclass
from qseries_v2.oracle_continuous_learner.ocl_004_learning_event import assemble_learning_event,verify_learning_event
from qseries_v2.oracle_continuous_learner.ocl_026_continuous_intake_runtime import build_runtime_input,assemble_runtime_batch,verify_runtime_batch
from .oad_180_crypto_experience_learning_outcome_handoff_gate import evaluate_crypto_learning_handoff

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class CryptoVerifiedLearningActivation:
    experience_id:str
    asset:str
    outcome_hash:str
    learning_event:object
    runtime_batch:object
    gate_state:str
    intake_ready:bool
    probability_enabled:bool=False
    direction_enabled:bool=False
    execution_authority:bool=False

def activate_verified_crypto_learning_event(candidate,lineage,future_outcome):
    outcome=future_outcome.outcome_observation
    gate=evaluate_crypto_learning_handoff(candidate,lineage,outcome)
    if not gate.learning_event_ready:
        raise RuntimeError("crypto experience not ready for OCL LearningEvent")
    event=assemble_learning_event(candidate.asset,candidate.evidence_hash,lineage.lineage_hash,outcome)
    if not verify_learning_event(event): raise RuntimeError("OCL-004 LearningEvent verification failed")
    outcome_input=build_runtime_input(
        1,"outcome",future_outcome.source_ref,outcome.outcome_hash,
        {"subject_id":outcome.subject_id,"outcome_type":outcome.outcome_type,"observed_value":outcome.observed_value,
         "observed_at":outcome.observed_at,"experience_id":candidate.experience_id}
    )
    event_input=build_runtime_input(
        2,"learning_event",event.event_id,event.event_hash,
        {"subject_id":event.subject_id,"evidence_hash":event.evidence_hash,"outcome_hash":event.outcome_hash,
         "lineage_hash":event.lineage_hash,"outcome_type":event.outcome_type,"experience_id":candidate.experience_id}
    )
    batch=assemble_runtime_batch((outcome_input,event_input))
    if not verify_runtime_batch(batch): raise RuntimeError("OCL-026 runtime batch verification failed")
    return CryptoVerifiedLearningActivation(
        candidate.experience_id,candidate.asset,outcome.outcome_hash,event,batch,gate.gate_state,True,False,False,False
    )
