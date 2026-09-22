from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from .oad_061_independent_to_canonical_bridge import canonicalize_independent_observation
from .oad_062_independent_canonical_provenance_validation import validate_independent_canonical
from .oad_066_independent_single_writer_ingress_binding import submit_independent_canonical_batch,await_independent_commit
from .oad_068_exact_postgresql_independent_readback import _backend,_query_one,exact_postgresql_readback
from .oad_138_official_cdc_public_health_adapter import acquire_cdc_public_health_observations
from .oad_139_official_openfda_enforcement_adapter import acquire_openfda_enforcement_observations

READ_ONLY=True
PROBABILITY_ENABLED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class PublicHealthProviderResult:
    provider:str
    state:str
    observations:tuple
    observation_count:int
    error_type:str|None
    error_message:str|None
    checked_at:str
    execution_authority:bool=False

@dataclass(frozen=True,slots=True)
class ResilientPublicHealthPersistence:
    provider_results:tuple
    raw_observations:int
    canonical_observations:int
    provenance_validated:int
    already_present:int
    committed_new:int
    exact_readback:int
    rows:tuple
    execution_authority:bool=False

def _run(provider,fn,timeout_seconds):
    now=datetime.now(timezone.utc).isoformat()
    try:
        obs=tuple(fn(timeout_seconds))
        return PublicHealthProviderResult(provider,"AVAILABLE",obs,len(obs),None,None,now,False)
    except Exception as exc:
        return PublicHealthProviderResult(provider,"UNAVAILABLE",tuple(),0,type(exc).__name__,str(exc),now,False)

def persist_resilient_public_health(root=None,timeout_seconds=120.0,acquisition_timeout_seconds=20.0):
    providers=(
        _run("tools.cdc.gov",acquire_cdc_public_health_observations,acquisition_timeout_seconds),
        _run("api.fda.gov",acquire_openfda_enforcement_observations,acquisition_timeout_seconds),
    )
    raw=tuple(o for p in providers if p.state=="AVAILABLE" for o in p.observations)
    canonical=tuple(canonicalize_independent_observation(x,"oad140.resilient-public-health") for x in raw)
    validations=tuple(validate_independent_canonical(x) for x in canonical)
    if not all(v.valid for v in validations): raise RuntimeError("public-health canonical provenance failed")

    backend=_backend(root)
    existing=0; missing=[]
    for i,x in enumerate(canonical):
        if _query_one(backend,x.observation_id,i) is None: missing.append(x)
        else: existing+=1
    committed=0
    if missing:
        sub=submit_independent_canonical_batch(tuple(missing),root)
        events=tuple(await_independent_commit(str(sub.request_id),root,timeout_seconds))
        accepted=tuple(x for x in events if getattr(x,"accepted",False) is True)
        if len(accepted)!=len(missing): raise RuntimeError("public-health single-writer commit mismatch")
        committed=len(accepted)
    ids=tuple(x.observation_id for x in canonical)
    rows=tuple(exact_postgresql_readback(ids,root)) if ids else tuple()
    if len(rows)!=len(ids): raise RuntimeError("public-health exact readback mismatch")
    return ResilientPublicHealthPersistence(tuple(providers),len(raw),len(canonical),len(validations),existing,committed,len(rows),rows,False)
