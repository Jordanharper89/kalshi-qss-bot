from __future__ import annotations
import importlib
from dataclasses import dataclass

OPH_015_BUILD_ID="OPH-015"
OPH_015_REVISION="OPH_015_STRICT_SINGLE_WRITER_PRODUCTION_GATE_V1"

@dataclass(frozen=True)
class StrictSingleWriterReport:
    fast_lane_queue_only:bool
    coverage_queue_only:bool
    writer_recovery_enabled:bool
    provenance_enabled:bool
    direct_adapter_postgresql_authority:bool=False
    execution_authority:bool=False

def verify_oph_015_strict_single_writer_production_gate():
    checks=(
        ("oph_011_persistence_provenance_ledger","verify_oph_011_persistence_provenance_ledger"),
        ("oph_012_strict_fast_lane_queue_only_admission","verify_oph_012_strict_fast_lane_queue_only_admission"),
        ("oph_013_strict_coverage_queue_only_admission","verify_oph_013_strict_coverage_queue_only_admission"),
        ("oph_014_canonical_writer_failure_recovery_runtime","verify_oph_014_canonical_writer_failure_recovery_runtime"),
    )
    return all(
        getattr(
            importlib.import_module(
                "qseries_v2.oracle_production_hardening."+m
            ),
            fn,
        )()
        for m,fn in checks
    )

def strict_single_writer_report():
    if not verify_oph_015_strict_single_writer_production_gate():
        raise RuntimeError("OPH-011 through OPH-015 verification failed")
    return StrictSingleWriterReport(
        True,True,True,True,False,False
    )
