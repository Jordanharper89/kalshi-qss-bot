from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from pathlib import Path
from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import RawSourceObservation,CanonicalObservation
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import submit_observation_batch,await_request
from .oad_068_exact_postgresql_independent_readback import _backend,_query_one,exact_postgresql_readback

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
EXECUTION_AUTHORITY=False
PRODUCER="oracle.crypto_experience_candidates"
PRIORITY=20
SOURCE_PREFIX="source.crypto.experience."

@dataclass(frozen=True,slots=True)
class CryptoExperiencePersistenceResult:
    candidates:int
    already_present:int
    committed_new:int
    exact_readback:int
    observation_ids:tuple
    execution_authority:bool=False

def canonicalize_crypto_experience_candidate(candidate,lineage,acquisition_batch_id="oad179.crypto-experience"):
    observed_at=datetime.fromisoformat(str(candidate.snapshot_at).replace("Z","+00:00"))
    if observed_at.tzinfo is None: observed_at=observed_at.replace(tzinfo=timezone.utc)
    source_id=f"{SOURCE_PREFIX}{candidate.asset.lower()}"
    raw=RawSourceObservation.create(
        source_observation_id=candidate.experience_id,
        observed_at=observed_at,
        observation_type="crypto_historical_experience_candidate",
        payload={
            "experience_id":candidate.experience_id,"asset":candidate.asset,
            "snapshot_at":candidate.snapshot_at,"cohort_state":candidate.cohort_state,
            "condition_vector":candidate.condition_vector,"temporal_vector":candidate.temporal_vector,
            "evidence_state":candidate.evidence_state,"consistency_state":candidate.consistency_state,
            "market_native_metrics":candidate.market_native_metrics,
            "independent_chain_metrics":candidate.independent_chain_metrics,
            "comparable_temporal_metrics":candidate.comparable_temporal_metrics,
            "evidence_hash":candidate.evidence_hash,"condition_hash":candidate.condition_hash,
            "experience_hash":candidate.experience_hash,"lineage_hash":lineage.lineage_hash,
            "outcome_attached":False,"probability":None,"direction":None,
        },
        provenance={"producer":PRODUCER,"lineage_hash":lineage.lineage_hash,"read_only":True},
    )
    return CanonicalObservation.create(source_id=source_id,raw_observation=raw,acquired_at=datetime.now(timezone.utc),acquisition_batch_id=acquisition_batch_id)

def persist_crypto_experience_candidates(pairs,root=None,timeout_seconds=120.0):
    root=Path(root or Path.cwd()).resolve()
    canonical=tuple(canonicalize_crypto_experience_candidate(c,l) for c,l in tuple(pairs))
    backend=_backend(root); missing=[]; existing=0
    for i,x in enumerate(canonical):
        if _query_one(backend,x.observation_id,i) is None: missing.append(x)
        else: existing+=1
    committed=0
    if missing:
        sub=submit_observation_batch(PRODUCER,PRIORITY,tuple(missing),root)
        events=tuple(await_request(str(sub.request_id),root,float(timeout_seconds)))
        accepted=tuple(x for x in events if getattr(x,"accepted",False) is True)
        if len(accepted)!=len(missing): raise RuntimeError("crypto experience single-writer commit mismatch")
        committed=len(accepted)
    ids=tuple(x.observation_id for x in canonical)
    rows=tuple(exact_postgresql_readback(ids,root)) if ids else tuple()
    if len(rows)!=len(ids): raise RuntimeError("crypto experience exact readback mismatch")
    return CryptoExperiencePersistenceResult(len(canonical),existing,committed,len(rows),ids,False)
