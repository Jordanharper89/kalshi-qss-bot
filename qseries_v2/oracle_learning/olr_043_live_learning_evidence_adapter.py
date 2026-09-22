from __future__ import annotations
from dataclasses import dataclass
from .olr_038_postgresql_outcome_evidence_linkage_ledger import record_linkage
from .olr_042_live_evidence_admission_gate import admit_outcome_evidence

OLR_043_BUILD_ID="OLR-043"
OLR_043_REVISION="OLR_043_LIVE_LEARNING_EVIDENCE_ADAPTER_V1"

@dataclass(frozen=True)
class LearningEvidenceMetrics:
    settled:int
    evidence_matched:int
    evidence_missing:int
    admitted:int
    evidence_coverage:float

def adapt_learning_batch(outcomes,root=None,min_score=50):
    admitted=[]
    settled=matched=missing=0
    for outcome in outcomes:
        settled+=1
        gate=admit_outcome_evidence(outcome,root,min_score)
        class Match:
            pass
        match=Match()
        match.matched=gate.admitted
        match.method=gate.match_method
        match.score=gate.score
        match.candidate=gate.candidate
        record_linkage(outcome,match,root)
        if gate.admitted:
            matched+=1
            admitted.append((outcome,gate.candidate,gate))
        else:
            missing+=1
    coverage=0.0 if settled==0 else matched/settled
    return tuple(admitted),LearningEvidenceMetrics(settled,matched,missing,len(admitted),coverage)

def verify_olr_043_live_learning_evidence_adapter(root=None):
    from .olr_042_live_evidence_admission_gate import verify_olr_042_live_evidence_admission_gate
    return verify_olr_042_live_evidence_admission_gate(root) and OLR_043_BUILD_ID=="OLR-043"
