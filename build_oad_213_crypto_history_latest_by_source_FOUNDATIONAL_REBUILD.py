from __future__ import annotations
import ast,os,subprocess,sys,textwrap
from pathlib import Path
REVISION='OAD_213_CRYPTO_HISTORY_LATEST_BY_SOURCE_FOUNDATIONAL_REBUILD'
def root():
 for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
  for x in (b,*b.parents):
   if (x/'qseries_v2').is_dir():return x
 raise RuntimeError('Q Series repository root not found')
def w(p,s):
 s=textwrap.dedent(s).lstrip();ast.parse(s,filename=str(p));q=p.with_suffix(p.suffix+'.tmp');q.write_text(s,encoding='utf-8',newline='\n');os.replace(q,p)
def run(r,t):
 z=subprocess.run([sys.executable,str(t)],cwd=str(r));
 if z.returncode:raise RuntimeError('test failed: '+t.name)
M182=r"""
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
"""
M189=r"""
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
"""
TEST=r"""
import unittest
from unittest.mock import patch
from datetime import datetime,timezone
from qseries_v2.oracle_adapters.independent import oad_182_crypto_persisted_experience_exact_readback as a
from qseries_v2.oracle_adapters.independent import oad_189_crypto_learned_case_exact_history_readback as b
class Cur:
 def __init__(self,rows):self.rows=rows;self.sql=''
 def __enter__(self):return self
 def __exit__(self,*x):return False
 def execute(self,s,args=None):
  if 'SELECT sequence_number' in s:self.sql=s
 def fetchall(self):return self.rows
class Conn:
 def __init__(self,rows):self.c=Cur(rows)
 def __enter__(self):return self
 def __exit__(self,*x):return False
 def cursor(self):return self.c
 def rollback(self):pass
class T(unittest.TestCase):
 def test_latest_experience(self):
  p={'experience_id':'e','asset':'BTC','snapshot_at':'x','cohort_state':'FULL_COVERAGE','condition_vector':(),'temporal_vector':(),'evidence_hash':'a'*64,'condition_hash':'b'*64,'experience_hash':'c'*64,'lineage_hash':'d'*64,'outcome_attached':False};c=Conn([(900,'o','source.crypto.experience.btc','crypto_historical_experience_candidate',datetime.now(timezone.utc),p)])
  with patch.object(a,'connect',return_value=c):r=a.read_persisted_crypto_experiences(assets=('BTC',),per_asset_limit=16)
  print('[SEQ]',r.records[0].sequence_number);self.assertIn('ORDER BY sequence_number DESC',c.c.sql)
 def test_legacy_cannot_claim_exact(self):
  p={'asset':'BTC','experience_id':'old','snapshot_at':'x','condition_vector':(),'temporal_vector':(),'condition_hash':'a'*64,'experience_hash':'b'*64,'lineage_hash':'c'*64,'horizon_seconds':60,'outcome_observed_at':'y','return_fraction':.01,'return_percent':1,'outcome_hash':'d'*64,'learning_event_hash':'e'*64,'exact_interval':True};c=Conn([(901,'o','crypto_verified_learned_case',p)])
  with patch.object(b,'connect',return_value=c):r=b.read_crypto_learned_case_history(assets=('BTC',),per_asset_limit=16)
  print('[LEGACY]',r[0].legacy_timing,'[EXACT]',r[0].exact_interval);self.assertTrue(r[0].legacy_timing);self.assertFalse(r[0].exact_interval);self.assertIn('ORDER BY sequence_number DESC',c.c.sql)
if __name__=='__main__':
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T));
 if not r.wasSuccessful():raise SystemExit(1)
 print('[PASS] OAD-213 latest-by-source history certified')
"""
def main():
 r=root();pkg=r/'qseries_v2/oracle_adapters/independent';targets=[pkg/'oad_182_crypto_persisted_experience_exact_readback.py',pkg/'oad_189_crypto_learned_case_exact_history_readback.py',r/'test_oad_213_crypto_latest_history_read_paths.py'];deps=[r/'qseries_v2/oracle_production_hardening/oph_019_postgresql_universal_ingestion_queue.py',pkg/'oad_179_crypto_experience_candidate_postgresql_persistence.py',pkg/'oad_188_crypto_verified_learned_case_postgresql_persistence.py']
 print('='*112);print(' OAD-213 CRYPTO HISTORY LATEST-BY-SOURCE FOUNDATIONAL REBUILD');print('='*112);print('[BOOT]',REVISION);print('[ROOT]',r)
 for d in deps:
  if not d.is_file():raise RuntimeError('Required dependency missing: '+str(d))
 old={x:(x.read_bytes() if x.exists() else None) for x in targets}
 try:w(targets[0],M182);w(targets[1],M189);w(targets[2],TEST);run(r,targets[2]);print('[PASS] newest rows cannot be starved by earliest-first LIMIT');print('[PASS] probability=FALSE direction=FALSE execution=FALSE');print('[DONE] OAD-213 INSTALLATION COMPLETE')
 except Exception:
  for x,v in old.items():
   if v is None:
    if x.exists():x.unlink()
   else:x.write_bytes(v)
  print('[ROLLBACK] OAD-213 rolled back');raise
if __name__=='__main__':main()
