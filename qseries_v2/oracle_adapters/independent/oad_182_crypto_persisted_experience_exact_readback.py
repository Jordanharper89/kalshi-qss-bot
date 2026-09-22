from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from .oad_179_crypto_experience_candidate_postgresql_persistence import SOURCE_PREFIX
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;EXECUTION_AUTHORITY=False;ASSETS=('BTC','ETH','SOL');DEFAULT_PER_ASSET_LIMIT=256
@dataclass(frozen=True,slots=True)
class PersistedCryptoExperience:
 observation_id:str;source_id:str;experience_id:str;asset:str;snapshot_at:str;cohort_state:str;condition_vector:tuple;temporal_vector:tuple;evidence_hash:str;condition_hash:str;experience_hash:str;lineage_hash:str;outcome_attached:bool;observed_at:str;sequence_number:int=0
@dataclass(frozen=True,slots=True)
class PersistedCryptoExperienceReadback:queried_assets:int;queried_rows:int;experiences:int;records:tuple;read_only:bool=True
def _record(r):
 if str(r[3])!='crypto_historical_experience_candidate':return None
 p=r[5] if isinstance(r[5],dict) else dict(r[5] or ());
 if bool(p.get('outcome_attached',False)):return None
 observed=r[4].isoformat() if hasattr(r[4],'isoformat') else str(r[4])
 return PersistedCryptoExperience(str(r[1]),str(r[2]),str(p['experience_id']),str(p['asset']),str(p['snapshot_at']),str(p['cohort_state']),tuple(p['condition_vector']),tuple(p['temporal_vector']),str(p['evidence_hash']),str(p['condition_hash']),str(p['experience_hash']),str(p['lineage_hash']),False,observed,int(r[0]))
def _latest(root,source,limit):
 sql="SELECT sequence_number,observation_id,source_id,observation_type,observed_at,COALESCE(canonical_observation_json->'raw_observation'->'payload',canonical_observation_json->'payload','{}'::jsonb) FROM public.oracle_canonical_observations WHERE source_id=%s AND observation_type='crypto_historical_experience_candidate' ORDER BY sequence_number DESC LIMIT %s"
 with connect(Path(root).resolve(),autocommit=False) as c:
  with c.cursor() as q:q.execute("SET TRANSACTION READ ONLY");q.execute("SET LOCAL statement_timeout='10000ms'");q.execute(sql,(source,int(limit)));rows=q.fetchall() or []
  c.rollback()
 return tuple(rows)
def read_persisted_crypto_experiences(root=None,assets=ASSETS,per_asset_limit=DEFAULT_PER_ASSET_LIMIT):
 root=Path(root or Path.cwd()).resolve();rows=[]
 for a in tuple(assets):rows.extend(_latest(root,f'{SOURCE_PREFIX}{str(a).lower()}',per_asset_limit))
 recs=tuple(sorted((x for x in (_record(r) for r in rows) if x is not None),key=lambda x:(x.sequence_number,x.asset,x.experience_id)))
 return PersistedCryptoExperienceReadback(len(tuple(assets)),len(rows),len(recs),recs,True)
