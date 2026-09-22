from __future__ import annotations
from datetime import datetime,timezone
from pathlib import Path
import os,time,uuid

from .oph_019_postgresql_universal_ingestion_queue import (
    ensure_postgresql_ingestion_schema,claim_next_request,complete_request,fail_request,queue_counts
)
from .oph_021_exclusive_postgresql_canonical_writer import acquire_writer_lease,build_canonical_router,ADVISORY_LOCK_KEY
from .oph_024_postgresql_stale_claim_recovery import recover_stale_claims
from .oph_029_postgresql_routing_failure_classification import classify_persistence_failure,PersistenceFailureClassification
from .oph_030_postgresql_writer_retry_telemetry import record_writer_event,ensure_retry_telemetry_schema

OPH_031_BUILD_ID="OPH-031"
OPH_031_REVISION="OPH_031_CLASSIFIED_SINGLE_WRITER_RELIABILITY_RUNTIME_V1"

def run_classified_writer_forever(root=None,progress=None,idle_sleep_seconds=0.002):
    root=Path(root or Path.cwd()).resolve()
    ensure_postgresql_ingestion_schema(root)
    ensure_retry_telemetry_schema(root)
    recovered=recover_stale_claims(root)
    lease=acquire_writer_lease(root)
    worker=f"oph031:{os.getpid()}:{uuid.uuid4().hex[:8]}"
    router=build_canonical_router(root)

    if progress:
        progress(f"[OPH-031 RECOVERY] stale_claims_recovered={len(recovered)}")
        progress(f"[OPH-031 WRITER] worker={worker} lease=ACQUIRED queue={queue_counts(root)}")

    try:
        while True:
            item=claim_next_request(worker,root)
            if item is None:
                time.sleep(float(idle_sleep_seconds))
                continue

            request_id,producer,priority,observations=item
            started=time.perf_counter()

            try:
                result=tuple(router.route_batch(tuple(observations),datetime.now(timezone.utc)))
                elapsed=(time.perf_counter()-started)*1000.0
                complete_request(request_id,result,root)
                success=PersistenceFailureClassification("COMMIT_SUCCESS",False,False,"commit")
                record_writer_event(request_id,producer,"COMMIT",success,1,len(observations),root,elapsed,None)
                if progress:
                    progress(
                        f"[OPH-031 COMMIT] request={request_id[:10]} producer={producer} "
                        f"priority={priority} observations={len(observations)} elapsed_ms={elapsed:.2f}"
                    )
            except Exception as exc:
                elapsed=(time.perf_counter()-started)*1000.0
                classification=classify_persistence_failure(exc)
                record_writer_event(
                    request_id,producer,"FAILURE",classification,1,len(observations),
                    root,elapsed,exc
                )

                if classification.terminal:
                    fail_request(request_id,exc,root,max_attempts=1)
                    if progress:
                        progress(
                            f"[OPH-031 TERMINAL] request={request_id[:10]} producer={producer} "
                            f"category={classification.category} type={type(exc).__name__} message={exc}"
                        )
                else:
                    fail_request(request_id,exc,root)
                    if progress:
                        progress(
                            f"[OPH-031 RETRY] request={request_id[:10]} producer={producer} "
                            f"category={classification.category} type={type(exc).__name__} message={exc}"
                        )
                router=build_canonical_router(root)

    except KeyboardInterrupt:
        return 0
    finally:
        try:
            with lease.cursor() as cur:
                cur.execute("SELECT pg_advisory_unlock(%s)",(ADVISORY_LOCK_KEY,))
        finally:
            lease.close()

def verify_oph_031_classified_single_writer_reliability_runtime(root=None):
    from .oph_030_postgresql_writer_retry_telemetry import verify_oph_030_postgresql_writer_retry_telemetry
    return (
        verify_oph_030_postgresql_writer_retry_telemetry(root)
        and OPH_031_BUILD_ID=="OPH-031"
        and callable(run_classified_writer_forever)
    )
