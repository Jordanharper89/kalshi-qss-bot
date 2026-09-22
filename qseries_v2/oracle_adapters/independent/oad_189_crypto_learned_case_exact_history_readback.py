from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from .oad_188_crypto_verified_learned_case_postgresql_persistence import SOURCE_PREFIX
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;EXECUTION_AUTHORITY=False;ASSETS=('BTC','ETH','SOL')
@dataclass(frozen=True,slots=True)
class LearnedCase:
 observation_id:str;asset:str;experience_id:str;snapshot_at:str;condition_vector:tuple;temporal_vector:tuple;condition_hash:str;experience_hash:str;lineage_hash:str;horizon_seconds:int;outcome_observed_at:str;return_fraction:float;return_percent:float;outcome_hash:str;learning_event_hash:str;exact_interval:bool;sequence_number:int=0;timing_certified:bool=False;requested_horizon_seconds:int=0;realized_horizon_seconds:int=0;timing_offset_seconds:int=0;sampling_method:str='';legacy_timing:bool=False
def _record(r):
 if str(r[2])!='crypto_verified_learned_case':return None
 p=r[3] if isinstance(r[3],dict) else dict(r[3] or ());req=int(p.get('requested_horizon_seconds',p.get('horizon_seconds',0)) or 0);real=int(p.get('realized_horizon_seconds',req) or req);off=int(p.get('timing_offset_seconds',max(0,real-req)) or 0);cert=bool(p.get('timing_certified',False));method=str(p.get('sampling_method',''));legacy=not(cert and method);exact=bool(p.get('exact_interval',False)) if not legacy else False
 return LearnedCase(str(r[1]),str(p['asset']),str(p['experience_id']),str(p['snapshot_at']),tuple(p['condition_vector']),tuple(p['temporal_vector']),str(p['condition_hash']),str(p['experience_hash']),str(p['lineage_hash']),int(p.get('horizon_seconds',req)),str(p['outcome_observed_at']),float(p['return_fraction']),float(p['return_percent']),str(p['outcome_hash']),str(p['learning_event_hash']),exact,int(r[0]),cert,req,real,off,method,legacy)
def _latest(root,source,limit):
 sql="SELECT sequence_number,observation_id,observation_type,COALESCE(canonical_observation_json->'raw_observation'->'payload',canonical_observation_json->'payload','{}'::jsonb) FROM public.oracle_canonical_observations WHERE source_id=%s AND observation_type='crypto_verified_learned_case' ORDER BY sequence_number DESC LIMIT %s"
 with connect(Path(root).resolve(),autocommit=False) as c:
  with c.cursor() as q:q.execute("SET TRANSACTION READ ONLY");q.execute("SET LOCAL statement_timeout='10000ms'");q.execute(sql,(source,int(limit)));rows=q.fetchall() or []
  c.rollback()
 return tuple(rows)
def read_crypto_learned_case_history(root=None,assets=ASSETS,per_asset_limit=512,include_legacy=True):
 root=Path(root or Path.cwd()).resolve();out=[]
 for a in tuple(assets):
  for row in _latest(root,f'{SOURCE_PREFIX}{str(a).lower()}',per_asset_limit):
   x=_record(row)
   if x is not None and (include_legacy or not x.legacy_timing):out.append(x)
 return tuple(sorted(out,key=lambda x:(x.sequence_number,x.asset,x.experience_id)))
