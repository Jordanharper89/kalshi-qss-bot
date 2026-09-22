from __future__ import annotations
from dataclasses import dataclass
from .oad_061_independent_to_canonical_bridge import canonicalize_independent_observation
from .oad_062_independent_canonical_provenance_validation import validate_independent_canonical
from .oad_066_independent_single_writer_ingress_binding import submit_independent_canonical_batch,await_independent_commit
from .oad_068_exact_postgresql_independent_readback import _backend,_query_one,exact_postgresql_readback
from .oad_128_official_bls_economic_adapter import acquire_bls_latest_economic_observations
from .oad_129_official_treasury_fiscal_data_adapter import acquire_treasury_debt_observation

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

@dataclass(frozen=True,slots=True)
class AuthoritativeEconomicPersistence:
    raw_observations:int
    canonical_observations:int
    provenance_validated:int
    already_present:int
    committed_new:int
    exact_readback:int
    providers:tuple
    observation_ids:tuple
    rows:tuple
    execution_authority:bool=False

def persist_current_authoritative_economic(root=None,timeout_seconds=120.0,acquisition_timeout_seconds=20.0):
    raw=tuple(acquire_bls_latest_economic_observations(acquisition_timeout_seconds))+tuple(acquire_treasury_debt_observation(acquisition_timeout_seconds))
    canonical=tuple(canonicalize_independent_observation(x,"oad130.authoritative-economic") for x in raw)
    validations=tuple(validate_independent_canonical(x) for x in canonical)
    if not all(v.valid for v in validations): raise RuntimeError("authoritative economic canonical provenance failed")
    backend=_backend(root)
    existing=[]; missing=[]
    for i,x in enumerate(canonical):
        row=_query_one(backend,x.observation_id,i)
        (missing if row is None else existing).append(x if row is None else row)
    committed=0
    if missing:
        sub=submit_independent_canonical_batch(tuple(missing),root)
        ev=tuple(await_independent_commit(str(sub.request_id),root,timeout_seconds))
        accepted=tuple(x for x in ev if getattr(x,"accepted",False) is True)
        if len(accepted)!=len(missing): raise RuntimeError("economic single-writer commit count mismatch")
        committed=len(accepted)
    ids=tuple(x.observation_id for x in canonical)
    rows=tuple(exact_postgresql_readback(ids,root)) if ids else tuple()
    if len(rows)!=len(ids): raise RuntimeError("economic exact PostgreSQL readback mismatch")
    return AuthoritativeEconomicPersistence(
        len(raw),len(canonical),len(validations),len(existing),committed,len(rows),
        tuple(sorted({x.provider for x in raw})),ids,rows,False)
