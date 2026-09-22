from __future__ import annotations
from dataclasses import dataclass

OLR_047_BUILD_ID="OLR-047"
OLR_047_REVISION="OLR_047_LIVE_LEARNING_METRICS_CONTRACT_V1"

@dataclass(frozen=True)
class LiveLearningMetrics:
    settled:int
    evidence_matched:int
    evidence_missing:int
    admitted:int
    applied:int
    evidence_coverage:float
    learning_yield:float

def build_live_learning_metrics(settled,evidence_matched,evidence_missing,admitted,applied):
    settled=int(settled);evidence_matched=int(evidence_matched);evidence_missing=int(evidence_missing)
    admitted=int(admitted);applied=int(applied)
    coverage=0.0 if settled<=0 else evidence_matched/settled
    yield_=0.0 if settled<=0 else applied/settled
    return LiveLearningMetrics(settled,evidence_matched,evidence_missing,admitted,applied,coverage,yield_)

def verify_olr_047_live_learning_metrics_contract(root=None):
    m=build_live_learning_metrics(100,25,75,20,10)
    return (
        OLR_047_BUILD_ID=="OLR-047"
        and abs(m.evidence_coverage-.25)<1e-12
        and abs(m.learning_yield-.10)<1e-12
    )
