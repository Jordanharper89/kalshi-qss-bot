
from __future__ import annotations
from dataclasses import dataclass
from .ohl_006_settled_outcome_inventory_adapter import verify_ohl_006_settled_outcome_inventory_adapter
from .ohl_007_historical_evidence_coverage_scanner import verify_ohl_007_historical_evidence_coverage_scanner
from .ohl_008_settled_market_eligibility_evaluator import verify_ohl_008_settled_market_eligibility_evaluator
from .ohl_009_historical_eligibility_census import verify_ohl_009_historical_eligibility_census

OHL_010_BUILD_ID="OHL-010"
OHL_010_REVISION="OHL_010_PHYSICAL_HISTORICAL_ELIGIBILITY_GATE_V1"

@dataclass(frozen=True)
class OHL010Certification:
    builds:tuple[str,...]
    capability:str
    next_capability:str
    certified:bool=True

def certify_ohl_006_through_010():
    if not all((
        verify_ohl_006_settled_outcome_inventory_adapter(),
        verify_ohl_007_historical_evidence_coverage_scanner(),
        verify_ohl_008_settled_market_eligibility_evaluator(),
        verify_ohl_009_historical_eligibility_census(),
    )):
        raise RuntimeError("OHL-006 through OHL-010 certification failed")
    return OHL010Certification(
        tuple("OHL-%03d"%i for i in range(6,11)),
        "physical_postgresql_historical_learning_eligibility_census",
        "historical_backfill_admission_and_durable_progress",
        True
    )

def verify_ohl_010_physical_historical_eligibility_gate():
    c=certify_ohl_006_through_010()
    return c.certified and len(c.builds)==5
