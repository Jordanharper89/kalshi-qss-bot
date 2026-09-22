from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from pathlib import Path
from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import RawSourceObservation,CanonicalObservation
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import submit_observation_batch,await_request
from .oad_068_exact_postgresql_independent_readback import _backend,_query_one,exact_postgresql_readback
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False
PRODUCER="oracle.crypto_prospective_identity";PRIORITY=20;SOURCE_PREFIX="source.crypto.prospective_binding."
@dataclass(frozen=True,slots=True)
class BindingPersistence:
 bindings:int;already_present:int;committed_new:int;exact_readback:int;observation_ids:tuple;execution_authority:bool=False
def _asset_from_experience_id(x):
 p=str(x).split(":")
 if len(p)<3 or p[0]!="crypto-exp":raise RuntimeError("invalid experience identity")
 return p[1].upper()
def canonicalize_binding(forecast_row,experience_id,cycle_sequence,acquisition_batch_id="oad249.prospective-binding"):
 p=dict(forecast_row.payload);asset=str(p["asset"]).upper()
 if _asset_from_experience_id(experience_id)!=asset:raise RuntimeError("forecast/experience asset mismatch")
 fid=str(p["forecast_id"]);created=str(p["created_at"]);h=int(p["horizon_seconds"])
 raw=RawSourceObservation.create(source_observation_id=f"{fid}:{experience_id}",observed_at=datetime.now(timezone.utc),observation_type="crypto_prospective_exact_identity_binding",payload={"forecast_id":fid,"forecast_observation_id":str(forecast_row.observation_id),"asset":asset,"forecast_created_at":created,"experience_id":str(experience_id),"cycle_sequence":int(cycle_sequence),"horizon_seconds":h,"training_snapshot_hash":str(p["training_snapshot_hash"]),"internal_forecast_probability":float(p["internal_forecast_probability"]),"source_claims":tuple(p.get("source_claims") or ()),"probability_enabled":False,"direction_enabled":False,"publication_allowed":False,"execution_authority":False},provenance={"producer":PRODUCER,"binding_mode":"same_production_cycle_explicit_identity","read_only":True})
 return CanonicalObservation.create(source_id=SOURCE_PREFIX+asset.lower(),raw_observation=raw,acquired_at=datetime.now(timezone.utc),acquisition_batch_id=acquisition_batch_id)
def persist_cycle_bindings(forecast_observation_ids,experience_ids,cycle_sequence,root=None,timeout_seconds=120.0):
 root=Path(root or Path.cwd()).resolve();backend=_backend(root);fr=tuple(exact_postgresql_readback(tuple(forecast_observation_ids),root))
 by_asset={}
 for r in fr:by_asset[str(dict(r.payload)["asset"]).upper()]=r
 xs=[]
 for eid in tuple(experience_ids):
  a=_asset_from_experience_id(eid)
  if a in by_asset:xs.append(canonicalize_binding(by_asset[a],eid,cycle_sequence))
 missing=[];existing=0
 for i,x in enumerate(xs):
  if _query_one(backend,x.observation_id,i) is None:missing.append(x)
  else:existing+=1
 committed=0
 if missing:
  s=submit_observation_batch(PRODUCER,PRIORITY,tuple(missing),root);ev=tuple(await_request(str(s.request_id),root,float(timeout_seconds)));accepted=tuple(x for x in ev if getattr(x,"accepted",False) is True)
  if len(accepted)!=len(missing):raise RuntimeError("prospective binding commit mismatch")
  committed=len(accepted)
 ids=tuple(x.observation_id for x in xs);rows=tuple(exact_postgresql_readback(ids,root)) if ids else ()
 if len(rows)!=len(ids):raise RuntimeError("prospective binding exact readback mismatch")
 return BindingPersistence(len(ids),existing,committed,len(rows),ids,False)
