from __future__ import annotations
from dataclasses import dataclass

from .oad_061_independent_to_canonical_bridge import canonicalize_independent_observation
from .oad_062_independent_canonical_provenance_validation import validate_independent_canonical
from .oad_066_independent_single_writer_ingress_binding import submit_independent_canonical_batch,await_independent_commit
from .oad_068_exact_postgresql_independent_readback import _backend,_query_one,exact_postgresql_readback
from .oad_132_resilient_authoritative_economic_provider_isolation import acquire_resilient_authoritative_economic
from .oad_133_authoritative_economic_source_health_lineage import build_source_health_lineage

READ_ONLY=True
PROBABILITY_ENABLED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class ResilientEconomicPersistenceResult:
    provider_results: tuple
    source_health: tuple
    raw_observations: int
    canonical_observations: int
    provenance_validated: int
    already_present: int
    committed_new: int
    exact_readback: int
    observation_ids: tuple
    rows: tuple
    execution_authority: bool=False

def persist_resilient_authoritative_economic(root=None,timeout_seconds=120.0,acquisition_timeout_seconds=20.0):
    provider_results,raw=acquire_resilient_authoritative_economic(acquisition_timeout_seconds)
    health=build_source_health_lineage(provider_results)
    canonical=tuple(canonicalize_independent_observation(x,"oad134.resilient-authoritative-economic") for x in raw)
    validations=tuple(validate_independent_canonical(x) for x in canonical)
    if not all(v.valid for v in validations):
        raise RuntimeError("resilient economic canonical provenance failed")

    backend=_backend(root)
    existing=0
    missing=[]
    for i,x in enumerate(canonical):
        row=_query_one(backend,x.observation_id,i)
        if row is None:
            missing.append(x)
        else:
            existing+=1

    committed=0
    if missing:
        sub=submit_independent_canonical_batch(tuple(missing),root)
        events=tuple(await_independent_commit(str(sub.request_id),root,timeout_seconds))
        accepted=tuple(x for x in events if getattr(x,"accepted",False) is True)
        if len(accepted)!=len(missing):
            raise RuntimeError("resilient economic single-writer commit mismatch")
        committed=len(accepted)

    ids=tuple(x.observation_id for x in canonical)
    rows=tuple(exact_postgresql_readback(ids,root)) if ids else tuple()
    if len(rows)!=len(ids):
        raise RuntimeError("resilient economic exact PostgreSQL readback mismatch")

    return ResilientEconomicPersistenceResult(
        tuple(provider_results),tuple(health),len(raw),len(canonical),len(validations),
        existing,committed,len(rows),ids,rows,False
    )
