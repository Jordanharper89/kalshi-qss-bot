from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from qseries_v2.oracle_continuous_learner.ocl_026_continuous_intake_runtime import build_runtime_input,assemble_runtime_batch,verify_runtime_batch
from .oad_188_crypto_verified_learned_case_postgresql_persistence import SOURCE_PREFIX
from .oad_189_crypto_learned_case_exact_history_readback import _record
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;EXECUTION_AUTHORITY=False;SOURCE_KIND='crypto_verified_learned_case';ASSETS=('BTC','ETH','SOL')
@dataclass(frozen=True,slots=True)
class CryptoOCLIntake:
 after_sequence:int;cases_read:int;eligible_cases:int;legacy_timing_cases:int;batch:object|None;start_sequence:int;end_sequence:int;intake_ready:bool;state:str;probability_enabled:bool=False;direction_enabled:bool=False;execution_authority:bool=False
def read_crypto_learned_cases_after_sequence(root=None,after_sequence=0,limit=512):
 root=Path(root or Path.cwd()).resolve();source_ids=tuple(f'{SOURCE_PREFIX}{a.lower()}' for a in ASSETS)
 sql="SELECT sequence_number,observation_id,observation_type,COALESCE(canonical_observation_json->'raw_observation'->'payload',canonical_observation_json->'payload','{}'::jsonb) FROM public.oracle_canonical_observations WHERE source_id = ANY(%s::text[]) AND observation_type='crypto_verified_learned_case' AND sequence_number>%s ORDER BY sequence_number ASC LIMIT %s"
 with connect(root,autocommit=False) as c:
  with c.cursor() as q:q.execute('SET TRANSACTION READ ONLY');q.execute("SET LOCAL statement_timeout='10000ms'");q.execute(sql,(list(source_ids),int(after_sequence),int(limit)));rows=q.fetchall() or []
  c.rollback()
 return tuple(x for x in (_record(r) for r in rows) if x is not None)
def build_crypto_ocl_runtime_input(x):
 if int(x.sequence_number)<1:raise ValueError('crypto learned case requires canonical sequence_number')
 payload={'asset':x.asset,'experience_id':x.experience_id,'condition_hash':x.condition_hash,'experience_hash':x.experience_hash,'lineage_hash':x.lineage_hash,'outcome_hash':x.outcome_hash,'learning_event_hash':x.learning_event_hash,'requested_horizon_seconds':x.requested_horizon_seconds or x.horizon_seconds,'realized_horizon_seconds':x.realized_horizon_seconds or x.horizon_seconds,'timing_offset_seconds':x.timing_offset_seconds,'timing_certified':x.timing_certified,'legacy_timing':x.legacy_timing,'exact_interval':x.exact_interval,'return_fraction':x.return_fraction,'probability':None,'direction':None}
 return build_runtime_input(int(x.sequence_number),SOURCE_KIND,str(x.observation_id),str(x.learning_event_hash),payload)
def build_crypto_ocl_intake(root=None,after_sequence=0,limit=512):
 cases=read_crypto_learned_cases_after_sequence(root,after_sequence,limit)
 if not cases:return CryptoOCLIntake(int(after_sequence),0,0,0,None,0,0,True,'NO_NEW_CASES',False,False,False)
 batch=assemble_runtime_batch(tuple(build_crypto_ocl_runtime_input(x) for x in cases))
 if not verify_runtime_batch(batch):raise RuntimeError('OCL-026 crypto batch verification failed')
 return CryptoOCLIntake(int(after_sequence),len(cases),len(cases),sum(1 for x in cases if x.legacy_timing),batch,batch.start_sequence,batch.end_sequence,True,'READY_FOR_OCL_CYCLE',False,False,False)
