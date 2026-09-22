from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone

OLR_038_BUILD_ID="OLR-038"
OLR_038_REVISION="OLR_038_LEARNING_STALENESS_CONTRADICTION_GUARD_V1"

@dataclass(frozen=True)
class LearningGuardDecision:
    allowed:bool
    reason:str
    contradiction_score:float
    stale:bool
    execution_authority:bool=False

def evaluate_learning_guard(updated_at=None,max_age_seconds=86400.0,contradiction_score=0.0,max_contradiction=.50,now=None):
    stale=False
    if updated_at:
        try:
            ts=datetime.fromisoformat(str(updated_at).replace("Z","+00:00"))
            if ts.tzinfo is None:ts=ts.replace(tzinfo=timezone.utc)
            ref=now or datetime.now(timezone.utc)
            stale=(ref-ts).total_seconds()>float(max_age_seconds)
        except Exception:
            return LearningGuardDecision(False,"invalid_timestamp",float(contradiction_score),True,False)
    c=max(0.0,min(1.0,float(contradiction_score)))
    if stale:return LearningGuardDecision(False,"stale_learning",c,True,False)
    if c>float(max_contradiction):return LearningGuardDecision(False,"contradictory_learning",c,False,False)
    return LearningGuardDecision(True,"allowed",c,False,False)

def verify_olr_038_learning_staleness_contradiction_guard():
    return evaluate_learning_guard(None,contradiction_score=.1).allowed and not evaluate_learning_guard(None,contradiction_score=.9).allowed
