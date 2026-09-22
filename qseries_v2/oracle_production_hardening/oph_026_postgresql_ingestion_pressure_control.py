from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from .oph_019_postgresql_universal_ingestion_queue import connect,ensure_postgresql_ingestion_schema,TABLE
OPH_026_BUILD_ID="OPH-026"
OPH_026_REVISION="OPH_026_POSTGRESQL_INGESTION_PRESSURE_CONTROL_V1"

@dataclass(frozen=True)
class IngestionPressure:
    pending:int
    in_progress:int
    failed:int
    total_open:int
    level:str

def read_ingestion_pressure(root=None):
    root=Path(root or Path.cwd()).resolve();ensure_postgresql_ingestion_schema(root)
    counts={"PENDING":0,"IN_PROGRESS":0,"FAILED":0}
    with connect(root) as conn:
        with conn.cursor() as cur:
            cur.execute(f"""SELECT status,COUNT(*) FROM public.{TABLE}
                            WHERE status<>'DONE' GROUP BY status""")
            for status,count in cur.fetchall():counts[str(status)]=int(count)
    open_=counts["PENDING"]+counts["IN_PROGRESS"]
    level="NORMAL" if open_<100 else ("ELEVATED" if open_<1000 else "HIGH")
    return IngestionPressure(counts["PENDING"],counts["IN_PROGRESS"],counts["FAILED"],open_,level)

def producer_delay_seconds(pressure):
    if pressure.level=="HIGH":return 0.050
    if pressure.level=="ELEVATED":return 0.010
    return 0.0

def verify_oph_026_postgresql_ingestion_pressure_control(root=None):
    from .oph_025_exclusive_writer_recovery_bootstrap import verify_oph_025_exclusive_writer_recovery_bootstrap
    return verify_oph_025_exclusive_writer_recovery_bootstrap(root) and producer_delay_seconds(IngestionPressure(0,0,0,0,"NORMAL"))==0.0
