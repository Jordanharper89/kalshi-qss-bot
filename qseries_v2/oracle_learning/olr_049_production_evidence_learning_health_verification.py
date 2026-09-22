from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from .olr_046_oracle_live_evidence_learner_launcher_cutover import verify_olr_046_oracle_live_evidence_learner_launcher_cutover
from .olr_048_postgresql_live_learning_metrics_read_model import read_linkage_metrics

OLR_049_BUILD_ID="OLR-049"
OLR_049_REVISION="OLR_049_PRODUCTION_EVIDENCE_LEARNING_HEALTH_VERIFICATION_V1"

@dataclass(frozen=True)
class EvidenceLearningHealth:
    launcher_active:bool
    settled:int
    evidence_matched:int
    evidence_missing:int
    evidence_coverage:float
    learning_yield:float
    healthy:bool

def production_evidence_learning_health(root=None,settled_limit=100):
    root=Path(root or Path.cwd()).resolve()
    active=verify_olr_046_oracle_live_evidence_learner_launcher_cutover(root)
    metrics=read_linkage_metrics(root,settled_limit)
    healthy=bool(active and metrics.settled>=0)
    return EvidenceLearningHealth(
        active,metrics.settled,metrics.evidence_matched,metrics.evidence_missing,
        metrics.evidence_coverage,metrics.learning_yield,healthy
    )

def verify_olr_049_production_evidence_learning_health_verification(root=None):
    h=production_evidence_learning_health(root,100)
    return OLR_049_BUILD_ID=="OLR-049" and h.launcher_active and h.healthy
