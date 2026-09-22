from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import RawSourceObservation,CanonicalObservation
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import submit_observation_batch,await_request
from .oad_068_exact_postgresql_independent_readback import _backend,_query_one,exact_postgresql_readback
from .oad_267_solana_pool_liquidity_historical_state import read_solana_proven_history
from .oad_270_solana_price_volume_liquidity_acceleration_conditions import build_solana_acceleration_conditions

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False
PRODUCER="oracle.solana_experience_candidates"
PRIORITY=20
SOURCE_PREFIX="source.solana.experience."

@dataclass(frozen=True,slots=True)
class SolanaHistoricalExperience:
    experience_id:str
    token_address:str
    pair_address:str
    snapshot_at:str
    conditions:tuple
    evidence_observation_ids:tuple
    evidence_hash:str
    experience_hash:str
    outcome_attached:bool=False
    probability:None=None
    direction:None=None
    execution_authority:bool=False

@dataclass(frozen=True,slots=True)
class SolanaExperienceFormationResult:
    state:str
    experiences:int
    already_present:int
    committed_new:int
    exact_readback:int
    experience_ids:tuple
    execution_authority:bool=False

def _hash(v):
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

def build_solana_historical_experiences(records):
    conditions=build_solana_acceleration_conditions(records)
    by_source={}
    for r in records:
        by_source.setdefault(r.source_id,[]).append(r)
    out=[]
    for c in conditions:
        rows=tuple(sorted(by_source.get(c.source_id,()),key=lambda x:(-1 if x.sequence_number is None else int(x.sequence_number),x.observed_at,x.observation_id)))
        if len(rows)<2: continue
        latest=rows[-1]
        token=str(latest.payload.get("token_address") or "")
        evidence_ids=(rows[-2].observation_id,rows[-1].observation_id)
        evidence_hash=_hash(evidence_ids)
        core=(token,c.pair_address,c.observed_at,c.conditions,evidence_ids,evidence_hash)
        experience_hash=_hash(core)
        experience_id=f"solana-exp:{token}:{c.pair_address}:{experience_hash[:24]}"
        out.append(SolanaHistoricalExperience(experience_id,token,c.pair_address,c.observed_at,c.conditions,evidence_ids,evidence_hash,experience_hash,False,None,None,False))
    return tuple(out)

def canonicalize_solana_experience(x):
    observed=datetime.fromisoformat(str(x.snapshot_at).replace("Z","+00:00")) if "T" in str(x.snapshot_at) else datetime.now(timezone.utc)
    if observed.tzinfo is None: observed=observed.replace(tzinfo=timezone.utc)
    raw=RawSourceObservation.create(
        source_observation_id=x.experience_id,
        observed_at=observed,
        observation_type="solana_historical_experience_candidate",
        payload={
            "experience_id":x.experience_id,
            "token_address":x.token_address,
            "pair_address":x.pair_address,
            "snapshot_at":x.snapshot_at,
            "conditions":x.conditions,
            "evidence_observation_ids":x.evidence_observation_ids,
            "evidence_hash":x.evidence_hash,
            "experience_hash":x.experience_hash,
            "outcome_attached":False,
            "probability":None,
            "direction":None,
        },
        provenance={"producer":PRODUCER,"evidence_hash":x.evidence_hash,"read_only":True},
    )
    return CanonicalObservation.create(
        source_id=SOURCE_PREFIX+x.token_address,
        raw_observation=raw,
        acquired_at=datetime.now(timezone.utc),
        acquisition_batch_id="oad271.solana-experience",
    )

def form_and_persist_solana_historical_experiences(
    root=None,
    timeout_seconds=120.0,
    per_source_limit=64,
    refresh=True,
):
    root=Path(root or Path.cwd()).resolve()
    history=read_solana_proven_history(root=root,per_source_limit=per_source_limit,refresh=refresh,timeout_seconds=timeout_seconds)
    experiences=build_solana_historical_experiences(history.records)
    if not experiences:
        return SolanaExperienceFormationResult("HOLD_TEMPORAL_DEPTH_REQUIRED",0,0,0,0,(),False)

    canonical=tuple(canonicalize_solana_experience(x) for x in experiences)
    backend=_backend(root); missing=[]; existing=0
    for i,x in enumerate(canonical):
        if _query_one(backend,x.observation_id,i) is None: missing.append(x)
        else: existing+=1
    committed=0
    if missing:
        sub=submit_observation_batch(PRODUCER,PRIORITY,tuple(missing),root)
        events=tuple(await_request(str(sub.request_id),root,float(timeout_seconds)))
        accepted=tuple(e for e in events if getattr(e,"accepted",False) is True)
        if len(accepted)!=len(missing):
            raise RuntimeError("Solana historical experience single-writer commit mismatch")
        committed=len(accepted)
    ids=tuple(x.observation_id for x in canonical)
    rows=tuple(exact_postgresql_readback(ids,root))
    if len(rows)!=len(ids):
        raise RuntimeError("Solana historical experience exact readback mismatch")
    return SolanaExperienceFormationResult("EXPERIENCE_CANDIDATES_PERSISTED",len(experiences),existing,committed,len(rows),tuple(x.experience_id for x in experiences),False)
