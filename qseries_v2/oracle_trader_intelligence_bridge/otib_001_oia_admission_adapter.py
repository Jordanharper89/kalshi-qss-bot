from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from qseries_v2.oracle_intelligence.analytics.oracle_opportunity_admission_gate import OracleOpportunityAdmissionGate

OTIB_001_BUILD_ID="OTIB-001"

@dataclass(frozen=True)
class OIAAdmissionSnapshot:
    reviewed_market_count:int
    admitted_market_count:int
    denied_market_count:int
    not_candidate_market_count:int
    markets:tuple
    report_hash:str
    read_only:bool=True
    execution_authority:bool=False

def load_oia_admission_snapshot(root=None):
    root=Path(root or Path.cwd()).resolve()
    def connection_factory():
        return connect(root,autocommit=False)
    report=OracleOpportunityAdmissionGate(connection_factory=connection_factory).evaluate()
    if report.read_only is not True or report.execution_allowed:
        raise RuntimeError("OIA-007 read-only boundary violation")
    return OIAAdmissionSnapshot(
        int(report.reviewed_market_count),
        int(report.admitted_market_count),
        int(report.denied_market_count),
        int(report.not_candidate_market_count),
        tuple(report.markets),
        str(report.report_hash),
        True,
        False,
    )

def verify_oia_admission_snapshot(x):
    if not x.read_only or x.execution_authority:
        raise RuntimeError("OTIB-001 read-only boundary violation")
    if x.reviewed_market_count != len(x.markets):
        raise RuntimeError("OTIB-001 reviewed count mismatch")
    return True
