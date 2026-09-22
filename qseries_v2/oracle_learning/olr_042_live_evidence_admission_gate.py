from __future__ import annotations
from dataclasses import dataclass
from .olr_037_market_evidence_candidate_matching import match_outcome_to_evidence
from .olr_041_postgresql_live_evidence_lookup import lookup_market_evidence

OLR_042_BUILD_ID="OLR-042"
OLR_042_REVISION="OLR_042_LIVE_EVIDENCE_ADMISSION_GATE_V1"

@dataclass(frozen=True)
class EvidenceAdmission:
    admitted:bool
    reason:str
    score:int
    match_method:str
    candidate:object|None

def admit_outcome_evidence(outcome,root=None,min_score=50):
    candidates=lookup_market_evidence(outcome,root)
    match=match_outcome_to_evidence(outcome,candidates)
    if not match.matched:
        return EvidenceAdmission(False,"EVIDENCE_MISSING",0,"NONE",None)
    if match.score<int(min_score):
        return EvidenceAdmission(False,"EVIDENCE_SCORE_BELOW_THRESHOLD",match.score,match.method,match.candidate)
    return EvidenceAdmission(True,"ADMITTED",match.score,match.method,match.candidate)

def verify_olr_042_live_evidence_admission_gate(root=None):
    from .olr_041_postgresql_live_evidence_lookup import verify_olr_041_postgresql_live_evidence_lookup
    return verify_olr_041_postgresql_live_evidence_lookup(root) and OLR_042_BUILD_ID=="OLR-042"
