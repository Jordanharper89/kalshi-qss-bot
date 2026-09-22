
from dataclasses import dataclass
OLR_008_BUILD_ID="OLR-008";OLR_008_REVISION="OLR_008_LEARNING_COVERAGE_METRICS_V1"
@dataclass(frozen=True)
class LearningCoverageMetrics:
    settled_scanned:int;duplicate_settlements:int;evidence_matched:int;evidence_missing:int;learning_events_admitted:int;learning_events_applied:int;evidence_coverage:float;learning_yield:float
def build_learning_coverage_metrics(scanned,duplicates,matched,missing,admitted,applied):
    vals=tuple(int(x) for x in (scanned,duplicates,matched,missing,admitted,applied))
    if any(x<0 for x in vals):raise ValueError("nonnegative metrics required")
    s,d,m,mi,a,ap=vals;eligible=max(0,s-d)
    return LearningCoverageMetrics(s,d,m,mi,a,ap,0.0 if not eligible else m/eligible,0.0 if not m else ap/m)
def verify_olr_008_learning_coverage_metrics():
    x=build_learning_coverage_metrics(10,2,6,2,6,5);return abs(x.evidence_coverage-.75)<1e-9
