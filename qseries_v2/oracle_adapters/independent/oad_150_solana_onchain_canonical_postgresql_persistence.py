from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from pathlib import Path
from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import RawSourceObservation,CanonicalObservation
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import submit_observation_batch,await_request
from .oad_068_exact_postgresql_independent_readback import _backend,_query_one,exact_postgresql_readback
from .oad_148_solana_mainnet_chain_state_acquisition import acquire_solana_mainnet_chain_state
from .oad_149_solana_finalized_block_activity_acquisition import acquire_solana_finalized_block_activity

READ_ONLY=True
PROBABILITY_ENABLED=False
EXECUTION_AUTHORITY=False
PRODUCER="oracle.solana_onchain"
PRIORITY=20

def _dt(v):
    if isinstance(v,datetime): return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
    d=datetime.fromisoformat(str(v).replace("Z","+00:00"))
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)

def canonicalize_solana_onchain_observation(x,acquisition_batch_id):
    raw=RawSourceObservation.create(
        source_observation_id=x.source_id,
        observed_at=_dt(x.observed_at),
        observation_type=x.observation_type,
        payload={
            "source_class":x.source_class,
            "independent_evidence":True,
            "provider":x.provider,
            "chain":x.chain,
            "network":x.network,
            "subject":x.subject,
            "source_url":x.source_url,
            "provenance_hash":x.provenance_hash,
            "onchain_payload":dict(x.payload),
        },
        provenance={
            "provider":x.provider,
            "source_url":x.source_url,
            "source_class":x.source_class,
            "independent_evidence":True,
            "read_only":True,
        },
    )
    return CanonicalObservation.create(
        source_id="source.onchain.solana.mainnet",
        raw_observation=raw,
        acquired_at=datetime.now(timezone.utc),
        acquisition_batch_id=str(acquisition_batch_id),
    )

@dataclass(frozen=True,slots=True)
class SolanaPersistenceResult:
    raw_observations:int
    canonical_observations:int
    already_present:int
    committed_new:int
    exact_readback:int
    rows:tuple
    execution_authority:bool=False

def persist_current_solana_onchain(root=None,timeout_seconds=120.0,acquisition_timeout_seconds=20.0):
    root=Path(root or Path.cwd()).resolve()
    raw=tuple(acquire_solana_mainnet_chain_state(acquisition_timeout_seconds))+tuple(acquire_solana_finalized_block_activity(acquisition_timeout_seconds))
    canonical=tuple(canonicalize_solana_onchain_observation(x,"oad150.solana-onchain") for x in raw)
    backend=_backend(root); existing=0; missing=[]
    for i,x in enumerate(canonical):
        if _query_one(backend,x.observation_id,i) is None: missing.append(x)
        else: existing+=1
    committed=0
    if missing:
        sub=submit_observation_batch(PRODUCER,PRIORITY,tuple(missing),root)
        events=tuple(await_request(str(sub.request_id),root,float(timeout_seconds)))
        accepted=tuple(x for x in events if getattr(x,"accepted",False) is True)
        if len(accepted)!=len(missing): raise RuntimeError("Solana universal single-writer commit mismatch")
        committed=len(accepted)
    ids=tuple(x.observation_id for x in canonical)
    rows=tuple(exact_postgresql_readback(ids,root)) if ids else tuple()
    if len(rows)!=len(ids): raise RuntimeError("Solana exact readback mismatch")
    return SolanaPersistenceResult(len(raw),len(canonical),existing,committed,len(rows),rows,False)
