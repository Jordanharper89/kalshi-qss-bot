from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from pathlib import Path
import os,time,uuid
from .oph_019_postgresql_universal_ingestion_queue import connect,ensure_postgresql_ingestion_schema,claim_next_request,complete_request,fail_request,queue_counts
OPH_021_BUILD_ID="OPH-021"
OPH_021_REVISION="OPH_021_EXCLUSIVE_POSTGRESQL_CANONICAL_WRITER_V1"
ADVISORY_LOCK_KEY=578721019023

@dataclass(frozen=True)
class ExclusiveWriterContract:
    postgresql_queue:bool=True
    one_writer_lease:bool=True
    direct_producer_write_authority:bool=False
    execution_authority:bool=False

def acquire_writer_lease(root=None):
    conn=connect(root,autocommit=True)
    with conn.cursor() as cur:
        cur.execute("SELECT pg_try_advisory_lock(%s)",(ADVISORY_LOCK_KEY,))
        locked=bool(cur.fetchone()[0])
    if not locked:
        conn.close();raise RuntimeError("Another OPH canonical writer already holds the PostgreSQL writer lease")
    return conn

def build_canonical_router(root=None):
    from qseries_v2.oracle_production_hardening.oph_007_physical_single_postgresql_writer_runtime import build_existing_canonical_router
    return build_existing_canonical_router(Path(root or Path.cwd()).resolve())

def run_exclusive_writer_forever(root=None,progress=None,idle_sleep_seconds=0.002):
    root=Path(root or Path.cwd()).resolve();ensure_postgresql_ingestion_schema(root);lease=acquire_writer_lease(root)
    worker=f"oph021:{os.getpid()}:{uuid.uuid4().hex[:8]}";router=build_canonical_router(root)
    if progress:progress(f"[OPH-021 WRITER] worker={worker} lease=ACQUIRED queue={queue_counts(root)}")
    try:
        while True:
            item=claim_next_request(worker,root)
            if item is None:time.sleep(float(idle_sleep_seconds));continue
            request_id,producer,priority,observations=item;started=time.perf_counter()
            try:
                result=tuple(router.route_batch(tuple(observations),datetime.now(timezone.utc)))
                complete_request(request_id,result,root)
                if progress:progress(f"[OPH-021 COMMIT] request={request_id[:10]} producer={producer} priority={priority} observations={len(observations)} elapsed_ms={(time.perf_counter()-started)*1000:.2f}")
            except Exception as exc:
                fail_request(request_id,exc,root);router=build_canonical_router(root)
                if progress:progress(f"[OPH-021 RETRY] request={request_id[:10]} producer={producer} type={type(exc).__name__} message={exc}")
    except KeyboardInterrupt:return 0
    finally:
        try:
            with lease.cursor() as cur:cur.execute("SELECT pg_advisory_unlock(%s)",(ADVISORY_LOCK_KEY,))
        finally:lease.close()

def verify_oph_021_exclusive_postgresql_canonical_writer():
    x=ExclusiveWriterContract()
    return x.postgresql_queue and x.one_writer_lease and not x.direct_producer_write_authority and not x.execution_authority
