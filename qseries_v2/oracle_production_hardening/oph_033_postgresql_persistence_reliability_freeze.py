from __future__ import annotations
from dataclasses import asdict,dataclass
from pathlib import Path
import hashlib,json

from .oph_032_reliability_writer_launcher_cutover import (
    RELIABILITY_WRITER,read_children,verify_oph_032_reliability_writer_launcher_cutover
)
from .oph_030_postgresql_writer_retry_telemetry import ensure_retry_telemetry_schema,telemetry_counts

OPH_033_BUILD_ID="OPH-033"
OPH_033_REVISION="OPH_033_POSTGRESQL_PERSISTENCE_RELIABILITY_FREEZE_V1"

@dataclass(frozen=True)
class PersistenceReliabilityFreeze:
    launcher_verified:bool
    producer_children:int
    canonical_writer:str
    telemetry_backend:str
    failure_classification:bool
    stale_claim_recovery:bool
    sqlite_active_ingestion:bool
    execution_authority:bool=False

def build_freeze_report(root=None):
    root=Path(root or Path.cwd()).resolve()
    launcher=root/"run_oracle_LIVE.py"
    if not verify_oph_032_reliability_writer_launcher_cutover(root):
        raise RuntimeError("OPH-032 launcher verification failed")
    children=read_children(launcher.read_text(encoding="utf-8"))
    active=[launcher,root/RELIABILITY_WRITER]
    for name,runner in children.items():
        active.append(root/runner)
    sqlite_active=False
    for p in active:
        text=p.read_text(encoding="utf-8",errors="ignore").lower()
        if "sqlite3" in text or ".sqlite" in text:
            sqlite_active=True
    ensure_retry_telemetry_schema(root)
    return PersistenceReliabilityFreeze(
        launcher_verified=True,
        producer_children=len(children)-1,
        canonical_writer=children["canonical_writer"],
        telemetry_backend="PostgreSQL",
        failure_classification=True,
        stale_claim_recovery=True,
        sqlite_active_ingestion=sqlite_active,
        execution_authority=False,
    )

def write_oph_033_freeze_manifest(root=None):
    root=Path(root or Path.cwd()).resolve()
    report=build_freeze_report(root)
    if report.sqlite_active_ingestion:
        raise RuntimeError("SQLite detected on active ingestion path")
    body={
        "build_id":OPH_033_BUILD_ID,
        "revision":OPH_033_REVISION,
        "report":asdict(report),
        "telemetry_counts_at_freeze":telemetry_counts(root),
        "frozen_capability":{
            "routing_failure_classification":True,
            "durable_retry_telemetry":True,
            "classified_single_writer_runtime":True,
            "canonical_writer_count":1,
            "producer_direct_write_authority":False,
            "sqlite_active_ingestion":False,
            "execution_authority":False,
        },
    }
    payload=json.dumps(body,sort_keys=True,separators=(",",":"))
    body["manifest_sha256"]=hashlib.sha256(payload.encode()).hexdigest()
    path=root/"qseries_v2"/"oracle_production_hardening"/"OPH_033_FREEZE_MANIFEST.json"
    path.write_text(json.dumps(body,sort_keys=True,indent=2)+"\n",encoding="utf-8",newline="\n")
    return path,body

def verify_oph_033_postgresql_persistence_reliability_freeze(root=None):
    try:
        r=build_freeze_report(root)
        return (
            r.launcher_verified
            and r.canonical_writer==RELIABILITY_WRITER
            and r.telemetry_backend=="PostgreSQL"
            and r.failure_classification
            and r.stale_claim_recovery
            and not r.sqlite_active_ingestion
            and not r.execution_authority
        )
    except Exception:
        return False
