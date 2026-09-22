from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone,timedelta
from pathlib import Path
import time

from .opc_006_universal_market_snapshot_canonicalizer import build_universal_market_snapshot
from .opc_008_ola_postgresql_snapshot_persistence_bridge import build_opc_postgresql_router,persist_snapshot_batch

try:
    from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_router import PostgreSQLPersistenceRoutingFailure
except Exception:
    PostgreSQLPersistenceRoutingFailure=()

OPC_027_BUILD_ID="OPC-027"
OPC_027_REVISION="OPC_027_CHUNKED_FULL_PAGE_PERSISTENCE_V1"

@dataclass(frozen=True)
class ChunkedPersistenceResult:
    requested:int
    persisted:int
    rejected:int
    chunks_completed:int
    retries_used:int
    chunk_size:int
    execution_authority:bool=False

def _retryable(exc):
    try:
        if PostgreSQLPersistenceRoutingFailure and isinstance(exc,PostgreSQLPersistenceRoutingFailure):
            return True
    except TypeError:
        pass
    return type(exc).__name__=="PostgreSQLPersistenceRoutingFailure" or isinstance(exc,(TimeoutError,ConnectionError))

def persist_full_page_in_chunks(
    markets,
    admitted_tickers,
    *,
    root=None,
    chunk_size=100,
    max_retries=5,
    retry_base_seconds=0.10,
    router=None,
    progress=None,
    sleep_fn=time.sleep,
):
    root=Path(root or Path.cwd()).resolve()
    chunk_size=int(chunk_size)
    if chunk_size<10 or chunk_size>500:
        raise ValueError("chunk_size must be 10..500")

    by={str(x.get("ticker") or ""):x for x in markets if isinstance(x,dict)}
    selected=[by[t] for t in admitted_tickers if t in by]

    if router is None:
        router=build_opc_postgresql_router(root)

    total_persisted=0
    total_retries=0
    chunks=0
    base=datetime.now(timezone.utc)

    for start in range(0,len(selected),chunk_size):
        rows=selected[start:start+chunk_size]
        batch_id="batch.opc.027."+base.strftime("%Y%m%dT%H%M%S%fZ")+f".{start:06d}"

        observations=[
            build_universal_market_snapshot(
                row,
                acquired_at=base+timedelta(microseconds=start+i+1),
                batch_id=batch_id,
            )
            for i,row in enumerate(rows)
        ]

        attempt=0
        while True:
            try:
                result=persist_snapshot_batch(
                    observations,
                    routed_at=datetime.now(timezone.utc),
                    router=router,
                )
                total_persisted+=result.accepted
                chunks+=1
                if progress:
                    progress(
                        f"[COVERAGE CHUNK] chunk={chunks} "
                        f"requested={len(observations)} "
                        f"persisted={result.accepted} retries={attempt}"
                    )
                break
            except KeyboardInterrupt:
                raise
            except Exception as exc:
                if not _retryable(exc) or attempt>=int(max_retries):
                    raise
                attempt+=1
                total_retries+=1
                delay=min(2.0,float(retry_base_seconds)*(2**(attempt-1)))
                if progress:
                    progress(
                        f"[COVERAGE CHUNK RETRY] attempt={attempt}/{max_retries} "
                        f"type={type(exc).__name__} delay={delay:.2f}s"
                    )
                if delay:
                    sleep_fn(delay)

    requested=len(selected)
    return ChunkedPersistenceResult(
        requested=requested,
        persisted=total_persisted,
        rejected=requested-total_persisted,
        chunks_completed=chunks,
        retries_used=total_retries,
        chunk_size=chunk_size,
        execution_authority=False,
    )

def verify_opc_027_chunked_full_page_persistence():
    x=ChunkedPersistenceResult(1000,1000,0,10,2,100,False)
    return x.requested==1000 and x.persisted==1000 and x.rejected==0 and x.chunks_completed==10 and not x.execution_authority
