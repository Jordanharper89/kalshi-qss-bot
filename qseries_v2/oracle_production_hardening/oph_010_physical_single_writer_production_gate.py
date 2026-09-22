from __future__ import annotations
import importlib
from dataclasses import dataclass

OPH_010_BUILD_ID="OPH-010"
OPH_010_REVISION="OPH_010_PHYSICAL_SINGLE_WRITER_PRODUCTION_GATE_CORRECTION_V2"

@dataclass(frozen=True)
class SingleWriterProductionReport:
    writer_child:str
    fast_lane_queued:bool
    coverage_queued:bool
    direct_adapter_postgresql_authority:bool=False
    execution_authority:bool=False

def verify_oph_010_physical_single_writer_production_gate():
    checks=(
        ("oph_006_durable_cross_process_observation_queue","verify_oph_006_durable_cross_process_observation_queue"),
        ("oph_007_physical_single_postgresql_writer_runtime","verify_oph_007_physical_single_postgresql_writer_runtime"),
        ("oph_008_fast_lane_queue_migration","verify_oph_008_fast_lane_queue_migration"),
        ("oph_009_coverage_queue_migration","verify_oph_009_coverage_queue_migration"),
    )
    return all(
        getattr(
            importlib.import_module(
                "qseries_v2.oracle_production_hardening."+mod
            ),
            fn,
        )()
        for mod,fn in checks
    )

def production_report():
    if not verify_oph_010_physical_single_writer_production_gate():
        raise RuntimeError("OPH-006 through OPH-010 verification failed")
    return SingleWriterProductionReport(
        "canonical_writer",
        True,
        True,
        False,
        False,
    )
