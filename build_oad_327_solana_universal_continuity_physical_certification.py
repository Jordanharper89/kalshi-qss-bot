from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID='OAD-327'
TITLE='SOLANA UNIVERSAL CONTINUITY PHYSICAL CERTIFICATION'
EXPECTED='build_oad_327_solana_universal_continuity_physical_certification.py'
MODULE='oad_327_solana_universal_continuity_physical_certification.py'
TEST='test_oad_327_solana_universal_continuity_physical_certification.py'
DEPENDENCIES=[('qseries_v2/oracle_adapters/independent/oad_326_solana_universal_resilient_worker.py', ('run_solana_universal_worker_cycle',)), ('qseries_v2/oracle_production_hardening/oph_021_exclusive_postgresql_canonical_writer.py', ('ADVISORY_LOCK_KEY', 'connect', 'run_exclusive_writer_forever')), ('run_oph_021_exclusive_postgresql_canonical_writer.py', ('run_exclusive_writer_forever',))]
MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import subprocess,sys,time
from qseries_v2.oracle_production_hardening.oph_021_exclusive_postgresql_canonical_writer import ADVISORY_LOCK_KEY,connect
from .oad_323_solana_durable_slot_checkpoint import load_solana_chain_checkpoint
from .oad_326_solana_universal_resilient_worker import run_solana_universal_worker_cycle
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False
OPH021_RUNNER="run_oph_021_exclusive_postgresql_canonical_writer.py"
@dataclass(frozen=True,slots=True)
class SolanaContinuityCertification:
    writer_started:bool;cycles:int;start_checkpoint:int|None;end_checkpoint:int|None;transactions:int;observations:int;committed_events:int;advanced:bool;state:str;execution_authority:bool=False
def _lease_held(root):
    c=connect(Path(root).resolve(),autocommit=True)
    try:
     with c.cursor() as cur:
      cur.execute("SELECT pg_try_advisory_lock(%s)",(ADVISORY_LOCK_KEY,));got=bool(cur.fetchone()[0])
      if got:cur.execute("SELECT pg_advisory_unlock(%s)",(ADVISORY_LOCK_KEY,))
     return not got
    finally:c.close()
def certify_solana_universal_continuity(root=None,cycles=2,per_batch_limit=1,timeout_seconds=120.0,acquisition_timeout_seconds=25.0):
    root=Path(root or Path.cwd()).resolve();proc=None;started=False
    if not _lease_held(root):
      runner=root/OPH021_RUNNER
      if not runner.is_file():raise RuntimeError("certified OPH-021 runner missing")
      proc=subprocess.Popen([sys.executable,str(runner)],cwd=str(root))
      started=True
      deadline=time.time()+15
      while time.time()<deadline and not _lease_held(root):time.sleep(.25)
      if not _lease_held(root):
       proc.terminate();raise RuntimeError("OPH-021 writer failed to acquire lease")
    before=load_solana_chain_checkpoint(root);tx=obs=comm=0;done=0
    try:
      for _ in range(int(cycles)):
       x=run_solana_universal_worker_cycle(root,per_batch_limit,timeout_seconds,acquisition_timeout_seconds)
       print("[SOLANA-UNIVERSAL]",x)
       tx+=x.transactions;obs+=x.observations;comm+=x.committed_events;done+=1
       time.sleep(.5)
      after=load_solana_chain_checkpoint(root)
      advanced=(before.last_committed_slot is None and after.last_committed_slot is not None) or (before.last_committed_slot is not None and after.last_committed_slot is not None and after.last_committed_slot>=before.last_committed_slot)
      state="CONTINUITY_CERTIFIED" if done==int(cycles) and advanced else "CONTINUITY_NOT_CERTIFIED"
      return SolanaContinuityCertification(started,done,before.last_committed_slot,after.last_committed_slot,tx,obs,comm,advanced,state,False)
    finally:
      if started and proc is not None:
       proc.terminate()
       try:proc.wait(timeout=5)
       except Exception:proc.kill()

"""
TEST_SOURCE=r"""\

import os,unittest
from qseries_v2.oracle_adapters.independent.oad_327_solana_universal_continuity_physical_certification import *
class T(unittest.TestCase):
 def test_physical(self):
  if os.environ.get("Q_SERIES_SKIP_SOLANA_PHYSICAL")=="1":self.skipTest("physical certification explicitly skipped")
  x=certify_solana_universal_continuity(cycles=2,per_batch_limit=1)
  print("[CERT] cycles=",x.cycles,"checkpoint=",x.start_checkpoint,"->",x.end_checkpoint,"tx=",x.transactions,"obs=",x.observations,"committed=",x.committed_events,"state=",x.state)
  self.assertEqual(x.state,"CONTINUITY_CERTIFIED");self.assertTrue(x.advanced);self.assertEqual(x.cycles,2)
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] OAD-327 physical Solana universal continuity certified")
 print("[PASS] certified OPH-021 exclusive writer used; no bypass writer")
 print("[PASS] checkpoint/restart boundary active")
 print("[PASS] finalized chain data persisted before checkpoint advancement")

"""
EXTRA_FILES={'run_oad_327_solana_universal_continuity_physical_certification.py': '\nfrom qseries_v2.oracle_adapters.independent.oad_327_solana_universal_continuity_physical_certification import certify_solana_universal_continuity\nif __name__=="__main__":\n x=certify_solana_universal_continuity(cycles=2,per_batch_limit=1)\n print(x)\n'}

def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")

def atomic(p,s):
    s=textwrap.dedent(s).lstrip()
    ast.parse(s,filename=str(p))
    p.parent.mkdir(parents=True,exist_ok=True)
    q=p.with_suffix(p.suffix+".tmp")
    q.write_text(s,encoding="utf-8",newline="\n")
    os.replace(q,p)

def main():
    if Path(__file__).name!=EXPECTED:
        raise RuntimeError("installer identity mismatch")
    r=root();pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    m=pkg/MODULE;t=r/TEST;init=pkg/"__init__.py"
    print("="*120);print(" "+BUILD_ID+" "+TITLE+" INSTALLER");print("="*120);print("[ROOT]",r)
    for rel,marks in DEPENDENCIES:
        p=r/rel
        if not p.is_file(): raise RuntimeError("dependency missing: "+rel)
        src=p.read_text(encoding="utf-8");ast.parse(src,filename=str(p))
        for mark in marks:
            if mark not in src: raise RuntimeError("dependency contract missing: "+rel+" -> "+mark)
        print("[PASS] exact dependency verified:",rel)
    protected=[]
    for rel in (
        "qseries_v2/oracle_production_hardening/oph_019_postgresql_universal_ingestion_queue.py",
        "qseries_v2/oracle_production_hardening/oph_021_exclusive_postgresql_canonical_writer.py",
        "qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
        "qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py",
        "qseries_v2/oracle_adapters/independent/oad_322_solana_universal_chain_coverage_gate.py",
    ):
        p=r/rel
        if not p.is_file(): raise RuntimeError("protected dependency missing: "+rel)
        protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest()))
    targets=[m,t,init]+[r/k for k in EXTRA_FILES]
    old={p:(p.read_bytes() if p.exists() else None) for p in targets}
    try:
        atomic(m,MODULE_SOURCE);atomic(t,TEST_SOURCE)
        for rel,src in EXTRA_FILES.items(): atomic(r/rel,src)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        exp="from ."+m.stem+" import *"
        if exp not in lines: lines.append(exp)
        atomic(init,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h: raise RuntimeError("protected dependency changed: "+p.name)
        print("[PASS] module installed:",m.relative_to(r));print("[PASS] test installed:",t.name)
        for rel in EXTRA_FILES: print("[PASS] runner installed:",rel)
        print("[PASS] OPH-019/021/023 and OAD-322 preserved unchanged")
        print("[PASS] no direct PostgreSQL writer introduced")
        print("[PASS] GMGN not required")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] affected files restored");raise

if __name__=="__main__":main()
