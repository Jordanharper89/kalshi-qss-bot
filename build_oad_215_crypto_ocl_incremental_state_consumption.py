from __future__ import annotations
import ast,os,subprocess,sys,textwrap
from pathlib import Path
REVISION='OAD_215_CRYPTO_OCL_INCREMENTAL_STATE_CONSUMPTION_V1'
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
MODULE=r"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from qseries_v2.oracle_continuous_learner.ocl_027_incremental_state_runtime import IncrementalLearnerState,genesis_incremental_state,verify_incremental_state
from qseries_v2.oracle_continuous_learner.ocl_028_learning_cycle_orchestrator import run_learning_cycle,verify_learning_cycle_result
from .oad_214_crypto_verified_learned_case_ocl_intake import build_crypto_ocl_intake
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;EXECUTION_AUTHORITY=False;TABLE='oracle_crypto_ocl_learning_state'
@dataclass(frozen=True,slots=True)
class CryptoOCLConsumption:
 prior_cycle_sequence:int;new_cycle_sequence:int;prior_applied_through_sequence:int;new_applied_through_sequence:int;cases_consumed:int;legacy_timing_cases:int;learner_state_hash:str;cycle_hash:str;state:str;physical_ready:bool;probability_enabled:bool=False;direction_enabled:bool=False;execution_authority:bool=False
def ensure_schema(root=None):
 root=Path(root or Path.cwd()).resolve();sql=f"CREATE TABLE IF NOT EXISTS public.{TABLE}(state_id SMALLINT PRIMARY KEY CHECK(state_id=1),cycle_sequence BIGINT NOT NULL,applied_through_sequence BIGINT NOT NULL,applied_batches BIGINT NOT NULL,last_batch_hash TEXT NOT NULL,parent_state_hash TEXT NOT NULL,learner_state_hash TEXT NOT NULL,last_cycle_hash TEXT NOT NULL,updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp())"
 with connect(root,autocommit=True) as c:
  with c.cursor() as q:q.execute(sql)
def _row(row):
 if row is None:return 0,genesis_incremental_state(),'0'*64
 cyc,through,batches,last,parent,h,lastcyc=row;s=IncrementalLearnerState(int(through),int(batches),str(last),str(parent),str(h))
 if not verify_incremental_state(s):raise RuntimeError('stored OCL learner state hash invalid')
 return int(cyc),s,str(lastcyc)
def read_crypto_ocl_state(root=None):
 root=Path(root or Path.cwd()).resolve();ensure_schema(root)
 with connect(root,autocommit=False) as c:
  with c.cursor() as q:q.execute(f'SELECT cycle_sequence,applied_through_sequence,applied_batches,last_batch_hash,parent_state_hash,learner_state_hash,last_cycle_hash FROM public.{TABLE} WHERE state_id=1');row=q.fetchone()
  c.rollback()
 return _row(row)
def consume_crypto_learned_cases_into_ocl(root=None,limit=512):
 root=Path(root or Path.cwd()).resolve();ensure_schema(root)
 with connect(root,autocommit=False) as c:
  with c.cursor() as q:
   q.execute(f'SELECT cycle_sequence,applied_through_sequence,applied_batches,last_batch_hash,parent_state_hash,learner_state_hash,last_cycle_hash FROM public.{TABLE} WHERE state_id=1 FOR UPDATE');row=q.fetchone();cycle,prior,lastcycle=_row(row);intake=build_crypto_ocl_intake(root,prior.applied_through_sequence,limit)
   if intake.batch is None:
    c.rollback();return CryptoOCLConsumption(cycle,cycle,prior.applied_through_sequence,prior.applied_through_sequence,0,0,prior.state_hash,lastcycle,'NO_NEW_CASES',True,False,False,False)
   result,new=run_learning_cycle(cycle+1,prior,intake.batch)
   if not verify_learning_cycle_result(result) or not verify_incremental_state(new):raise RuntimeError('frozen OCL state transition verification failed')
   q.execute(f"INSERT INTO public.{TABLE}(state_id,cycle_sequence,applied_through_sequence,applied_batches,last_batch_hash,parent_state_hash,learner_state_hash,last_cycle_hash,updated_at) VALUES(1,%s,%s,%s,%s,%s,%s,%s,clock_timestamp()) ON CONFLICT(state_id) DO UPDATE SET cycle_sequence=EXCLUDED.cycle_sequence,applied_through_sequence=EXCLUDED.applied_through_sequence,applied_batches=EXCLUDED.applied_batches,last_batch_hash=EXCLUDED.last_batch_hash,parent_state_hash=EXCLUDED.parent_state_hash,learner_state_hash=EXCLUDED.learner_state_hash,last_cycle_hash=EXCLUDED.last_cycle_hash,updated_at=clock_timestamp()",(cycle+1,new.applied_through_sequence,new.applied_batches,new.last_batch_hash,new.parent_state_hash,new.state_hash,result.cycle_hash))
  c.commit()
 sc,ss,sh=read_crypto_ocl_state(root);ready=sc==cycle+1 and ss.state_hash==new.state_hash and ss.applied_through_sequence==intake.end_sequence and sh==result.cycle_hash
 if not ready:raise RuntimeError('OCL crypto state exact readback mismatch')
 return CryptoOCLConsumption(cycle,sc,prior.applied_through_sequence,ss.applied_through_sequence,intake.eligible_cases,intake.legacy_timing_cases,ss.state_hash,result.cycle_hash,'CONSUMED_NEW_CASES',True,False,False,False)
"""
TEST=r"""
import unittest
from qseries_v2.oracle_continuous_learner.ocl_026_continuous_intake_runtime import build_runtime_input,assemble_runtime_batch
from qseries_v2.oracle_continuous_learner.ocl_027_incremental_state_runtime import genesis_incremental_state,verify_incremental_state
from qseries_v2.oracle_continuous_learner.ocl_028_learning_cycle_orchestrator import run_learning_cycle,verify_learning_cycle_result
class T(unittest.TestCase):
 def test_chain(self):
  g=genesis_incremental_state();b=assemble_runtime_batch((build_runtime_input(101,'crypto_verified_learned_case','o1','a'*64,{'probability':None}),build_runtime_input(105,'crypto_verified_learned_case','o2','b'*64,{'probability':None})));r,s=run_learning_cycle(1,g,b);print('[STATE]',g.applied_through_sequence,'->',s.applied_through_sequence);self.assertTrue(verify_learning_cycle_result(r));self.assertTrue(verify_incremental_state(s));self.assertEqual(s.parent_state_hash,g.state_hash)
if __name__=='__main__':
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T));
 if not r.wasSuccessful():raise SystemExit(1)
 print('[PASS] OAD-215 frozen OCL-027/028 transition certified')
"""
PHYSICAL=r"""
import unittest
from qseries_v2.oracle_adapters.independent.oad_215_crypto_ocl_incremental_state_consumption import consume_crypto_learned_cases_into_ocl
class T(unittest.TestCase):
 def test_physical(self):
  r=consume_crypto_learned_cases_into_ocl(limit=512);print('[PHYSICAL] cycle=',r.prior_cycle_sequence,'->',r.new_cycle_sequence);print('[PHYSICAL] through=',r.prior_applied_through_sequence,'->',r.new_applied_through_sequence);print('[PHYSICAL] cases=',r.cases_consumed,'legacy=',r.legacy_timing_cases);print('[PHYSICAL] learner_state_hash=',r.learner_state_hash);print('[PHYSICAL] state=',r.state,'ready=',r.physical_ready);self.assertTrue(r.physical_ready);self.assertEqual(len(r.learner_state_hash),64);self.assertFalse(r.probability_enabled);self.assertFalse(r.execution_authority)
if __name__=='__main__':
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T));
 if not r.wasSuccessful():raise SystemExit(1)
 print('[PASS] OAD-215 persisted crypto cases consumed into frozen OCL state')
"""
def main():
 r=root();pkg=r/'qseries_v2/oracle_adapters/independent';m=pkg/'oad_215_crypto_ocl_incremental_state_consumption.py';t=r/'test_oad_215_crypto_ocl_incremental_state_consumption.py';pt=r/'test_oad_215_crypto_ocl_incremental_state_consumption_PHYSICAL.py';deps=[pkg/'oad_214_crypto_verified_learned_case_ocl_intake.py',r/'qseries_v2/oracle_continuous_learner/ocl_027_incremental_state_runtime.py',r/'qseries_v2/oracle_continuous_learner/ocl_028_learning_cycle_orchestrator.py']
 print('='*112);print(' OAD-215 CRYPTO LEARNED CASE -> FROZEN OCL-027/028 DURABLE STATE');print('='*112);print('[BOOT]',REVISION);print('[ROOT]',r)
 for d in deps:
  if not d.is_file():raise RuntimeError('Required dependency missing: '+str(d))
 old={x:(x.read_bytes() if x.exists() else None) for x in (m,t,pt)}
 try:w(m,MODULE);w(t,TEST);w(pt,PHYSICAL);run(r,t);print('[PASS] physical consumption test installed');print('[PASS] no frozen OCL module modified');print('[PASS] probability=FALSE direction=FALSE execution=FALSE');print('[DONE] OAD-215 INSTALLATION COMPLETE')
 except Exception:
  for x,v in old.items():
   if v is None:
    if x.exists():x.unlink()
   else:x.write_bytes(v)
  print('[ROLLBACK] OAD-215 rolled back');raise
if __name__=='__main__':main()
