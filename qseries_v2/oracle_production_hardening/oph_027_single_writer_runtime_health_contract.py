from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
from .oph_019_postgresql_universal_ingestion_queue import queue_counts
from .oph_026_postgresql_ingestion_pressure_control import read_ingestion_pressure
OPH_027_BUILD_ID="OPH-027"
OPH_027_REVISION="OPH_027_SINGLE_WRITER_RUNTIME_HEALTH_CONTRACT_V1"

@dataclass(frozen=True)
class SingleWriterHealth:
    architecture_verified:bool
    pending:int
    in_progress:int
    failed:int
    pressure_level:str
    execution_authority:bool=False

def single_writer_health(root=None):
    from .oph_023_postgresql_single_writer_production_freeze import verify_oph_023_postgresql_single_writer_production_freeze
    root=Path(root or Path.cwd()).resolve();p=read_ingestion_pressure(root)
    return SingleWriterHealth(bool(verify_oph_023_postgresql_single_writer_production_freeze(root)),p.pending,p.in_progress,p.failed,p.level,False)

def verify_oph_027_single_writer_runtime_health_contract(root=None):
    from .oph_026_postgresql_ingestion_pressure_control import verify_oph_026_postgresql_ingestion_pressure_control
    return verify_oph_026_postgresql_ingestion_pressure_control(root) and single_writer_health(root).architecture_verified
