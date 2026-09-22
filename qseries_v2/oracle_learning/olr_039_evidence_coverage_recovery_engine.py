from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from .olr_037_market_evidence_candidate_matching import match_outcome_to_evidence
from .olr_038_postgresql_outcome_evidence_linkage_ledger import record_linkage
OLR_039_BUILD_ID="OLR-039"
OLR_039_REVISION="OLR_039_EVIDENCE_COVERAGE_RECOVERY_ENGINE_V1"

@dataclass(frozen=True)
class RecoveryMetrics:
    settled:int
    matched:int
    missing:int
    evidence_coverage:float

def recover_evidence_links(outcomes,evidence_provider,root=None):
    settled=matched=missing=0
    results=[]
    for outcome in outcomes:
        settled+=1
        candidates=tuple(evidence_provider(outcome) or ())
        match=match_outcome_to_evidence(outcome,candidates)
        record_linkage(outcome,match,root)
        if match.matched:matched+=1
        else:missing+=1
        results.append(match)
    coverage=0.0 if settled==0 else matched/settled
    return tuple(results),RecoveryMetrics(settled,matched,missing,coverage)

def verify_olr_039_evidence_coverage_recovery_engine(root=None):
    from .olr_038_postgresql_outcome_evidence_linkage_ledger import verify_olr_038_postgresql_outcome_evidence_linkage_ledger
    return verify_olr_038_postgresql_outcome_evidence_linkage_ledger(root) and OLR_039_BUILD_ID=="OLR-039"
