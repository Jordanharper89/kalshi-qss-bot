
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from qseries_v2.oracle_learning_runtime.olr_006_historical_evidence_matcher import find_historical_market_evidence
from .ohl_006_settled_outcome_inventory_adapter import verify_ohl_006_settled_outcome_inventory_adapter

OHL_007_BUILD_ID="OHL-007"
OHL_007_REVISION="OHL_007_HISTORICAL_EVIDENCE_COVERAGE_SCANNER_V1"

@dataclass(frozen=True)
class MarketEvidenceCoverage:
    ticker:str
    evidence_count:int
    earliest_observation_id:str
    latest_observation_id:str
    has_evidence:bool

def scan_market_evidence_coverage(root,ticker,limit=50):
    if not verify_ohl_006_settled_outcome_inventory_adapter():
        raise RuntimeError("OHL-006 verification failed")
    limit=int(limit)
    if limit<1 or limit>1000:raise ValueError("evidence limit must be 1..1000")
    rows=tuple(find_historical_market_evidence(Path(root).resolve(),str(ticker),limit=limit))
    return MarketEvidenceCoverage(
        str(ticker),len(rows),
        str(getattr(rows[0],"observation_id","")) if rows else "",
        str(getattr(rows[-1],"observation_id","")) if rows else "",
        bool(rows),
    )

def verify_ohl_007_historical_evidence_coverage_scanner():
    x=MarketEvidenceCoverage("KX",0,"","",False)
    return not x.has_evidence and x.evidence_count==0
