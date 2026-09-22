from __future__ import annotations
from datetime import datetime,timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_persistence_backend_contract import (
    CanonicalPersistenceQueryRequest,
)
from qseries_v2.oracle_production_hardening.oph_007_physical_single_postgresql_writer_runtime import (
    build_existing_canonical_router,
)
from qseries_v2.oracle_adapters.independent.oad_060_independent_source_bundle import (
    acquire_independent_production_bundle,
)
from qseries_v2.oracle_adapters.independent.oad_065_independent_canonical_batch_gate import (
    build_independent_canonical_batch,
)
from qseries_v2.oracle_adapters.independent.oad_066_independent_single_writer_ingress_binding import (
    submit_independent_canonical_batch,
    await_independent_commit,
)

OAD_068_BUILD_ID="OAD-068"
OAD_068_REVISION="OAD_068_IDEMPOTENT_READBACK_REBUILD_V1"
READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

def _backend(root=None):
    router=build_existing_canonical_router(Path(root or Path.cwd()).resolve())
    backend=getattr(router,"_persistence_backend",None)
    if backend is None or not callable(getattr(backend,"query",None)):
        raise RuntimeError("existing PostgreSQL backend query unavailable")
    return backend

def _query_one(backend,observation_id,index=0):
    oid=str(observation_id)
    request=CanonicalPersistenceQueryRequest.by_observation_id(
        query_id=f"query.oad068.{index}.{oid[:12]}",
        backend_id=backend.backend_id,
        observation_id=oid,
        requested_at=datetime.now(timezone.utc),
        query_metadata={
            "read_only":True,
            "build_id":"OAD-068",
            "query_mode":"exact_by_observation_id",
        },
    )
    rows=tuple(backend.query(request=request))
    if len(rows)>1:
        raise RuntimeError("exact observation query returned multiple rows: "+oid)
    return rows[0] if rows else None

def exact_postgresql_readback(observation_ids,root=None):
    backend=_backend(root)
    found=[]
    for i,oid in enumerate(tuple(str(x) for x in observation_ids)):
        row=_query_one(backend,oid,i)
        if row is None:
            raise RuntimeError("exact PostgreSQL observation missing: "+oid)
        if row.observation_id!=oid:
            raise RuntimeError("exact PostgreSQL observation identity mismatch: "+oid)
        found.append(row)
    return tuple(found)

def verify_or_persist_independent_cohort(root=None,per_source_limit=2,timeout_seconds=120.0):
    root=Path(root or Path.cwd()).resolve()
    raw=acquire_independent_production_bundle(per_source_limit)
    batch=build_independent_canonical_batch(raw,"oad068.idempotent.physical")
    if not batch.ready_for_existing_persistence_router:
        raise RuntimeError("OAD-065 independent canonical batch not ready")

    backend=_backend(root)
    existing=[]
    missing=[]
    for i,obs in enumerate(batch.canonical_observations):
        row=_query_one(backend,obs.observation_id,i)
        if row is None:
            missing.append(obs)
        else:
            existing.append(row)

    committed_new=0
    request_id=None
    if missing:
        submission=submit_independent_canonical_batch(tuple(missing),root)
        request_id=str(submission.request_id)
        evidence=await_independent_commit(request_id,root,timeout_seconds)
        accepted=tuple(x for x in evidence if getattr(x,"accepted",False) is True)
        if len(accepted)!=len(missing):
            raise RuntimeError("missing-only single-writer commit count mismatch")
        committed_new=len(accepted)

    rows=exact_postgresql_readback(
        tuple(x.observation_id for x in batch.canonical_observations),
        root,
    )
    return {
        "cohort_size":len(batch.canonical_observations),
        "already_present":len(existing),
        "missing_before_write":len(missing),
        "committed_new":committed_new,
        "exact_readback":len(rows),
        "request_id":request_id,
        "rows":rows,
    }
