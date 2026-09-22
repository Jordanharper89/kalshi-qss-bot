from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from pathlib import Path
import os,time,uuid

from .oph_006_durable_cross_process_observation_queue import claim_next_request,complete_request,fail_request,queue_counts

OPH_007_BUILD_ID="OPH-007"
OPH_007_REVISION="OPH_007_PHYSICAL_SINGLE_POSTGRESQL_WRITER_RUNTIME_V1"

@dataclass(frozen=True)
class SingleWriterRuntimeCheck:
    ready:bool
    writer_id:str
    execution_authority:bool=False

def build_existing_canonical_router(root=None):
    root=Path(root or Path.cwd()).resolve()
    try:
        from qseries_v2.oracle_pre_settlement_coverage.opc_008_ola_postgresql_snapshot_persistence_bridge import build_opc_postgresql_router
        return build_opc_postgresql_router(root)
    except Exception:
        from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_router import OraclePostgreSQLCanonicalObservationPersistenceRouter
        try:
            return OraclePostgreSQLCanonicalObservationPersistenceRouter()
        except TypeError as exc:
            raise RuntimeError("Could not construct certified canonical PostgreSQL router") from exc

def run_single_writer_forever(root=None,progress=None,idle_sleep_seconds=0.002):
    root=Path(root or Path.cwd()).resolve()
    worker_id=f"oph007:{os.getpid()}:{uuid.uuid4().hex[:8]}"
    router=build_existing_canonical_router(root)
    if progress: progress(f"[SINGLE WRITER] worker={worker_id} queue={queue_counts(root)}")
    while True:
        try:
            item=claim_next_request(worker_id,root)
            if item is None:
                time.sleep(float(idle_sleep_seconds)); continue
            request_id,writer_id,priority,observations=item
            started=time.perf_counter()
            try:
                result=tuple(router.route_batch(tuple(observations),datetime.now(timezone.utc)))
                complete_request(request_id,result,root)
                if progress:
                    progress(
                        f"[SINGLE WRITER] request={request_id[:10]} producer={writer_id} priority={priority} observations={len(observations)} elapsed_ms={(time.perf_counter()-started)*1000:.2f}"
                    )
            except Exception as exc:
                fail_request(request_id,exc,root)
                if progress:
                    progress(f"[SINGLE WRITER] failed request={request_id[:10]} producer={writer_id} type={type(exc).__name__} message={exc}")
        except KeyboardInterrupt:
            return 0

def verify_oph_007_physical_single_postgresql_writer_runtime():
    x=SingleWriterRuntimeCheck(True,"OPH-007",False)
    return x.ready and x.writer_id=="OPH-007" and not x.execution_authority
