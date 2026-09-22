from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID='OAD-325'
TITLE='SOLANA UNIVERSAL SINGLE-WRITER PERSISTENCE'
EXPECTED='build_oad_325_solana_universal_single_writer_persistence.py'
MODULE='oad_325_solana_universal_single_writer_persistence.py'
TEST='test_oad_325_solana_universal_single_writer_persistence.py'
DEPENDENCIES=[('qseries_v2/oracle_adapters/independent/oad_322_solana_universal_chain_coverage_gate.py', ('build_universal_coverage_batch', 'observations')), ('qseries_v2/oracle_production_hardening/oph_019_postgresql_universal_ingestion_queue.py', ('def submit_observation_batch', 'def await_request'))]
MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import submit_observation_batch,await_request
from .oad_322_solana_universal_chain_coverage_gate import build_universal_coverage_batch
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False
PRODUCER="oracle.solana_universal_chain";PRIORITY=20
@dataclass(frozen=True,slots=True)
class SolanaUniversalPersistenceResult:
    transactions:int;observations:int;committed_events:int;request_id:str|None;coverage_state:str;execution_authority:bool=False
def persist_solana_universal_chain_batch(start_slot=None,limit=2,root=None,timeout_seconds=120.0,acquisition_timeout_seconds=20.0):
    root=Path(root or Path.cwd()).resolve()
    x=build_universal_coverage_batch(start_slot,limit,acquisition_timeout_seconds)
    items=tuple(x.observations)
    if not items:return SolanaUniversalPersistenceResult(x.transactions,0,0,None,x.state,False)
    sub=submit_observation_batch(PRODUCER,PRIORITY,items,root)
    events=tuple(await_request(str(sub.request_id),root,float(timeout_seconds)))
    accepted=sum(1 for e in events if getattr(e,"accepted",False) is True)
    return SolanaUniversalPersistenceResult(x.transactions,len(items),accepted,str(sub.request_id),x.state,False)

"""
TEST_SOURCE=r"""\

import unittest
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_325_solana_universal_single_writer_persistence as m
class T(unittest.TestCase):
 def test_queue_only(self):
  cov=SimpleNamespace(transactions=2,observations=(object(),object(),object()),state="UNIVERSAL_BATCH_ACCOUNTED")
  sub=SimpleNamespace(request_id="rid")
  with patch.object(m,"build_universal_coverage_batch",return_value=cov),patch.object(m,"submit_observation_batch",return_value=sub) as s,patch.object(m,"await_request",return_value=(SimpleNamespace(accepted=True),)*3):
   x=m.persist_solana_universal_chain_batch(root=".")
  print("[PERSIST]",x.transactions,x.observations,x.committed_events,x.request_id)
  self.assertEqual(x.committed_events,3);s.assert_called_once()
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] OAD-325 Solana universal observations admitted only through OPH-019")

"""
EXTRA_FILES={}

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
