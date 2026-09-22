from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import (
    RawSourceObservation,CanonicalObservation,
)
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import (
    submit_observation_batch,await_request,
)
from .oad_068_exact_postgresql_independent_readback import _backend,_query_one,exact_postgresql_readback
from .oad_168_crypto_condition_state_normalization import CryptoConditionState

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
EXECUTION_AUTHORITY=False
PRODUCER="oracle.crypto_condition_history"
PRIORITY=20
SOURCE_PREFIX="source.crypto.condition."

@dataclass(frozen=True,slots=True)
class CryptoConditionSnapshotPersistenceResult:
    snapshot_at:str
    condition_states:int
    canonical_observations:int
    already_present:int
    committed_new:int
    exact_readback:int
    observation_ids:tuple
    execution_authority:bool=False

def _dt(v):
    if isinstance(v,datetime):
        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
    d=datetime.fromisoformat(str(v).replace("Z","+00:00"))
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)

def stamp_crypto_condition_states(states,snapshot_at):
    stamp=_dt(snapshot_at).astimezone(timezone.utc).isoformat()
    out=[]
    for x in tuple(states):
        out.append(CryptoConditionState(
            asset=str(x.asset),
            source_family=str(x.source_family),
            metric_name=str(x.metric_name),
            value=float(x.value),
            unit=str(x.unit),
            condition=str(x.condition),
            basis=str(x.basis),
            independent_evidence=bool(x.independent_evidence),
            market_native_reference=bool(x.market_native_reference),
            observed_at=stamp,
        ))
    return tuple(out)

def canonicalize_crypto_condition_state(x,acquisition_batch_id,snapshot_at,evidence_observed_at=None):
    stamp=_dt(snapshot_at)
    metric_token=str(x.metric_name).replace(" ","_").lower()
    family_token=str(x.source_family).replace(" ","_").lower()
    asset=str(x.asset).upper()
    source_id=f"{SOURCE_PREFIX}{asset.lower()}.{family_token}.{metric_token}"
    raw=RawSourceObservation.create(
        source_observation_id=f"crypto-condition:{asset}:{family_token}:{metric_token}:{stamp.isoformat()}",
        observed_at=stamp,
        observation_type="crypto_condition_snapshot",
        payload={
            "asset":asset,
            "source_family":str(x.source_family),
            "metric_name":str(x.metric_name),
            "value":float(x.value),
            "unit":str(x.unit),
            "condition":str(x.condition),
            "basis":str(x.basis),
            "independent_evidence":bool(x.independent_evidence),
            "market_native_reference":bool(x.market_native_reference),
            "evidence_observed_at":None if evidence_observed_at is None else str(evidence_observed_at),
            "snapshot_at":stamp.isoformat(),
            "direction":None,
            "probability":None,
        },
        provenance={
            "producer":PRODUCER,
            "source_family":str(x.source_family),
            "independent_evidence":bool(x.independent_evidence),
            "market_native_reference":bool(x.market_native_reference),
            "read_only":True,
        },
    )
    return CanonicalObservation.create(
        source_id=source_id,
        raw_observation=raw,
        acquired_at=datetime.now(timezone.utc),
        acquisition_batch_id=str(acquisition_batch_id),
    )

def persist_crypto_condition_snapshot(states,root=None,timeout_seconds=120.0,snapshot_at=None,evidence_observed_at_by_key=None):
    root=Path(root or Path.cwd()).resolve()
    stamp=_dt(snapshot_at or datetime.now(timezone.utc))
    stamped=stamp_crypto_condition_states(states,stamp)
    evidence_observed_at_by_key=dict(evidence_observed_at_by_key or {})
    canonical=tuple(
        canonicalize_crypto_condition_state(
            x,"oad172.crypto-condition-history",stamp,
            evidence_observed_at_by_key.get((x.asset,x.source_family,x.metric_name)),
        )
        for x in stamped
    )
    backend=_backend(root)
    existing=0
    missing=[]
    for i,x in enumerate(canonical):
        if _query_one(backend,x.observation_id,i) is None:
            missing.append(x)
        else:
            existing+=1
    committed=0
    if missing:
        sub=submit_observation_batch(PRODUCER,PRIORITY,tuple(missing),root)
        events=tuple(await_request(str(sub.request_id),root,float(timeout_seconds)))
        accepted=tuple(x for x in events if getattr(x,"accepted",False) is True)
        if len(accepted)!=len(missing):
            raise RuntimeError("crypto condition snapshot single-writer commit mismatch")
        committed=len(accepted)
    ids=tuple(x.observation_id for x in canonical)
    rows=tuple(exact_postgresql_readback(ids,root)) if ids else tuple()
    if len(rows)!=len(ids):
        raise RuntimeError("crypto condition snapshot exact readback mismatch")
    return CryptoConditionSnapshotPersistenceResult(
        stamp.isoformat(),len(stamped),len(canonical),existing,committed,len(rows),ids,False
    )
