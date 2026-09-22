from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from pathlib import Path
from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import RawSourceObservation,CanonicalObservation
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import submit_observation_batch,await_request
from .oad_068_exact_postgresql_independent_readback import _backend,_query_one,exact_postgresql_readback
from .oad_232_crypto_prospective_empirical_forecast_foundation import build_prospective_crypto_forecasts

READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False
PRODUCER="oracle.crypto_prospective_learning";PRIORITY=20;SOURCE_PREFIX="source.crypto.prospective_forecast."

@dataclass(frozen=True,slots=True)
class ForecastPersistence:
    forecasts:int;already_present:int;committed_new:int;exact_readback:int;observation_ids:tuple;execution_authority:bool=False

def canonicalize_prospective_forecast(f,acquisition_batch_id="oad233.prospective"):
    payload={"forecast_id":f.forecast_id,"asset":f.asset,"created_at":f.created_at,"training_as_of_sequence":f.training_as_of_sequence,
             "training_snapshot_hash":f.training_snapshot_hash,"sample_size":f.sample_size,"positive_count":f.positive_count,
             "negative_or_flat_count":f.negative_or_flat_count,"internal_forecast_probability":f.internal_forecast_probability,
             "source_claims":f.source_claims,"horizon_seconds":f.horizon_seconds,
             "probability_enabled":False,"direction_enabled":False,"publication_allowed":False,"execution_authority":False}
    raw=RawSourceObservation.create(source_observation_id=f.forecast_id,observed_at=datetime.fromisoformat(f.created_at.replace("Z","+00:00")),
        observation_type="crypto_prospective_internal_forecast",payload=payload,
        provenance={"producer":PRODUCER,"read_only":True,"operator_probability":False})
    return CanonicalObservation.create(source_id=SOURCE_PREFIX+f.asset.lower(),raw_observation=raw,acquired_at=datetime.now(timezone.utc),acquisition_batch_id=acquisition_batch_id)

def persist_prospective_forecasts(root=None,timeout_seconds=120.0):
    root=Path(root or Path.cwd()).resolve();fs=build_prospective_crypto_forecasts(root);xs=tuple(canonicalize_prospective_forecast(f) for f in fs)
    backend=_backend(root);missing=[];existing=0
    for i,x in enumerate(xs):
        if _query_one(backend,x.observation_id,i) is None:missing.append(x)
        else:existing+=1
    committed=0
    if missing:
        s=submit_observation_batch(PRODUCER,PRIORITY,tuple(missing),root)
        ev=tuple(await_request(str(s.request_id),root,float(timeout_seconds)))
        accepted=tuple(x for x in ev if getattr(x,"accepted",False) is True)
        if len(accepted)!=len(missing):raise RuntimeError("prospective forecast commit mismatch")
        committed=len(accepted)
    ids=tuple(x.observation_id for x in xs);rows=tuple(exact_postgresql_readback(ids,root)) if ids else ()
    if len(rows)!=len(ids):raise RuntimeError("prospective forecast exact readback mismatch")
    return ForecastPersistence(len(ids),existing,committed,len(rows),ids,False)
