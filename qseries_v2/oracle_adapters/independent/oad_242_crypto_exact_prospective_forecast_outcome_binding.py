from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False
ASSETS=("BTC","ETH","SOL")
@dataclass(frozen=True,slots=True)
class ExactProspectiveBinding:
 forecast_id:str;asset:str;experience_id:str;condition_hash:str;forecast_sequence:int;learned_sequence:int;forecast_created_at:str;outcome_observed_at:str;horizon_seconds:int;forecast_probability:float;source_claims:tuple;learning_event_id:str;learning_event_hash:str;outcome_hash:str;execution_authority:bool=False
def _p(x):return x if isinstance(x,dict) else dict(x or ())
def read_exact_prospective_bindings(root=None,per_source_limit=512):
 root=Path(root or Path.cwd()).resolve();bindings=[];learned=[]
 with connect(root,autocommit=False) as c:
  with c.cursor() as q:
   q.execute("SET TRANSACTION READ ONLY");q.execute("SET LOCAL statement_timeout='10000ms'")
   for a in ASSETS:
    q.execute("""SELECT sequence_number,COALESCE(canonical_observation_json->'raw_observation'->'payload',canonical_observation_json->'payload','{}'::jsonb) FROM public.oracle_canonical_observations WHERE source_id=%s ORDER BY sequence_number DESC LIMIT %s""",("source.crypto.prospective_binding."+a.lower(),int(per_source_limit)));bindings.extend(q.fetchall() or ())
    q.execute("""SELECT sequence_number,COALESCE(canonical_observation_json->'raw_observation'->'payload',canonical_observation_json->'payload','{}'::jsonb) FROM public.oracle_canonical_observations WHERE source_id=%s ORDER BY sequence_number DESC LIMIT %s""",("source.crypto.learned_case."+a.lower(),int(per_source_limit)));learned.extend(q.fetchall() or ())
  c.rollback()
 by_exp={}
 for seq,raw in learned:
  p=_p(raw)
  if p.get("experience_id") and bool(p.get("exact_interval")):by_exp.setdefault(str(p["experience_id"]),[]).append((int(seq),p))
 out=[]
 for fseq,raw in bindings:
  b=_p(raw);eid=str(b.get("experience_id") or "");matches=by_exp.get(eid,())
  if len(matches)!=1:continue
  lseq,l=matches[0]
  if str(l.get("asset") or "").upper()!=str(b.get("asset") or "").upper():continue
  if int(l.get("horizon_seconds") or 0)!=int(b.get("horizon_seconds") or 0):continue
  out.append(ExactProspectiveBinding(str(b["forecast_id"]),str(b["asset"]).upper(),eid,str(l.get("condition_hash") or ""),int(fseq),lseq,str(b["forecast_created_at"]),str(l["outcome_observed_at"]),int(b["horizon_seconds"]),float(b["internal_forecast_probability"]),tuple(tuple(x) for x in b.get("source_claims") or ()),str(l.get("learning_event_id") or ""),str(l.get("learning_event_hash") or ""),str(l.get("outcome_hash") or ""),False))
 return tuple(sorted(out,key=lambda x:(x.forecast_sequence,x.learned_sequence)))
