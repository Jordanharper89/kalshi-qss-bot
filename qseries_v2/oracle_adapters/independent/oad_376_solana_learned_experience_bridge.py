from __future__ import annotations
from dataclasses import dataclass, asdict
import hashlib, json

from .oad_374_solana_temporal_case_bridge import SolanaTemporalLearningCase
from .oad_375_solana_verified_forward_outcome_bridge import SolanaVerifiedForwardOutcome

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class SolanaLearnedExperienceRecord:
    experience_id:str
    case_id:str
    behavior_type:str
    protocol:str|None
    primary_asset:str|None
    secondary_asset:str|None
    horizon_seconds:int
    outcome:str
    return_fraction:float
    evidence_source:str
    immutable_payload_hash:str
    learning_namespace:str
    execution_authority:bool=False

def build_learned_experience(case:SolanaTemporalLearningCase,outcome:SolanaVerifiedForwardOutcome):
    if not bool(outcome.verified):
        raise ValueError("unverified outcome cannot become learned experience")

    if str(outcome.case_id) != str(case.case_id):
        raise ValueError("case/outcome mismatch")

    payload={
        "case_id":case.case_id,
        "behavior_type":case.behavior_type,
        "protocol":case.protocol,
        "primary_asset":case.primary_asset,
        "secondary_asset":case.secondary_asset,
        "horizon_seconds":int(outcome.horizon_seconds),
        "outcome":outcome.outcome,
        "return_fraction":float(outcome.return_fraction),
        "evidence_source":outcome.evidence_source,
        "learning_namespace":"EXISTING_OCL",
    }

    raw=json.dumps(
        payload,
        sort_keys=True,
        separators=(",",":"),
        default=str
    ).encode("utf-8")

    h=hashlib.sha256(raw).hexdigest()

    return SolanaLearnedExperienceRecord(
        experience_id="SOLANA-EXP-"+h[:24],
        case_id=case.case_id,
        behavior_type=case.behavior_type,
        protocol=case.protocol,
        primary_asset=case.primary_asset,
        secondary_asset=case.secondary_asset,
        horizon_seconds=int(outcome.horizon_seconds),
        outcome=outcome.outcome,
        return_fraction=float(outcome.return_fraction),
        evidence_source=outcome.evidence_source,
        immutable_payload_hash=h,
        learning_namespace="EXISTING_OCL",
        execution_authority=False,
    )

def as_learning_payload(record:SolanaLearnedExperienceRecord):
    return asdict(record)
