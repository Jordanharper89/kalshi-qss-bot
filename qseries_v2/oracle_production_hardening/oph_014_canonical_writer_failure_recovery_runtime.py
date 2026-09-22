from __future__ import annotations
from datetime import datetime,timezone
from pathlib import Path
import time,os,uuid

from .oph_006_durable_cross_process_observation_queue import (
    claim_next_request,
    complete_request,
    fail_request,
    queue_counts,
)
from .oph_007_physical_single_postgresql_writer_runtime import (
    build_existing_canonical_router,
)
from .oph_011_persistence_provenance_ledger import append_provenance

OPH_014_BUILD_ID="OPH-014"
OPH_014_REVISION="OPH_014_CANONICAL_WRITER_FAILURE_RECOVERY_RUNTIME_V1"

TRANSIENT_NAMES={
    "PostgreSQLPersistenceRoutingFailure",
    "OperationalError",
    "InterfaceError",
}

def _is_transient(exc):
    name=type(exc).__name__
    text=str(exc).lower()
    return (
        name in TRANSIENT_NAMES
        or "expected_terminal_chain_hash_mismatch" in text
        or "connection" in text and "postgres" in text
    )

def run_recovering_single_writer_forever(
    root=None,
    progress=None,
    idle_sleep_seconds=0.002,
    retry_limit=5,
):
    root=Path(root or Path.cwd()).resolve()
    worker_id=f"oph014:{os.getpid()}:{uuid.uuid4().hex[:8]}"
    router=build_existing_canonical_router(root)

    if progress:
        progress(
            f"[SINGLE WRITER] worker={worker_id} "
            f"queue={queue_counts(root)} recovery=ENABLED"
        )

    while True:
        try:
            item=claim_next_request(worker_id,root)
            if item is None:
                time.sleep(float(idle_sleep_seconds))
                continue

            request_id,writer_id,priority,observations=item
            attempt=0

            while True:
                attempt+=1
                started=time.perf_counter()

                append_provenance(
                    "WRITER_ATTEMPT",
                    root,
                    request_id=request_id,
                    producer=writer_id,
                    priority=priority,
                    observation_count=len(observations),
                    attempt=attempt,
                )

                try:
                    result=tuple(
                        router.route_batch(
                            tuple(observations),
                            datetime.now(timezone.utc),
                        )
                    )

                    complete_request(
                        request_id,
                        result,
                        root,
                    )

                    append_provenance(
                        "WRITER_SUCCESS",
                        root,
                        request_id=request_id,
                        producer=writer_id,
                        priority=priority,
                        observation_count=len(observations),
                        attempt=attempt,
                        elapsed_ms=round(
                            (time.perf_counter()-started)*1000,
                            2,
                        ),
                    )

                    if progress:
                        progress(
                            f"[SINGLE WRITER] request={request_id[:10]} "
                            f"producer={writer_id} priority={priority} "
                            f"observations={len(observations)} "
                            f"attempt={attempt} "
                            f"elapsed_ms={(time.perf_counter()-started)*1000:.2f}"
                        )

                    break

                except Exception as exc:
                    transient=_is_transient(exc)

                    append_provenance(
                        "WRITER_FAILURE",
                        root,
                        request_id=request_id,
                        producer=writer_id,
                        priority=priority,
                        observation_count=len(observations),
                        attempt=attempt,
                        exception_type=type(exc).__name__,
                        exception_message=str(exc),
                        transient=transient,
                    )

                    if transient and attempt<int(retry_limit):
                        delay=min(
                            0.50,
                            0.01*(2**(attempt-1)),
                        )

                        if progress:
                            progress(
                                f"[SINGLE WRITER RETRY] request={request_id[:10]} "
                                f"producer={writer_id} "
                                f"type={type(exc).__name__} "
                                f"attempt={attempt}/{retry_limit} "
                                f"delay={delay:.3f}s"
                            )

                        time.sleep(delay)

                        # Refresh router after a failed physical append.
                        router=build_existing_canonical_router(root)
                        continue

                    fail_request(
                        request_id,
                        exc,
                        root,
                    )

                    if progress:
                        progress(
                            f"[SINGLE WRITER] FAILED request={request_id[:10]} "
                            f"producer={writer_id} "
                            f"type={type(exc).__name__} "
                            f"attempts={attempt}"
                        )

                    break

        except KeyboardInterrupt:
            return 0

def verify_oph_014_canonical_writer_failure_recovery_runtime():
    class E(Exception): pass
    e=E("x")
    return (
        _is_transient(type("PostgreSQLPersistenceRoutingFailure",(Exception,),{})())
        and not _is_transient(e)
    )
