from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID='OAD-323'
TITLE='SOLANA DURABLE SLOT CHECKPOINT'
EXPECTED='build_oad_323_solana_durable_slot_checkpoint.py'
MODULE='oad_323_solana_durable_slot_checkpoint.py'
TEST='test_oad_323_solana_durable_slot_checkpoint.py'
DEPENDENCIES=[('qseries_v2/oracle_adapters/independent/oad_322_solana_universal_chain_coverage_gate.py', ('build_universal_coverage_batch', 'SolanaUniversalCoverageReport'))]
MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass,asdict
from datetime import datetime,timezone
from pathlib import Path
import json,os
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class SolanaChainCheckpoint:
    last_committed_slot:int|None
    last_committed_signature:str|None
    updated_at:str
    generation:int
    execution_authority:bool=False
def checkpoint_path(root=None):
    return Path(root or Path.cwd()).resolve()/"runtime_state"/"solana_universal_chain"/"checkpoint.json"
def load_solana_chain_checkpoint(root=None):
    p=checkpoint_path(root)
    if not p.exists(): return SolanaChainCheckpoint(None,None,datetime.now(timezone.utc).isoformat(),0,False)
    d=json.loads(p.read_text(encoding="utf-8"))
    return SolanaChainCheckpoint(d.get("last_committed_slot"),d.get("last_committed_signature"),d["updated_at"],int(d.get("generation",0)),False)
def commit_solana_chain_checkpoint(slot,signature=None,root=None):
    p=checkpoint_path(root);p.parent.mkdir(parents=True,exist_ok=True)
    prior=load_solana_chain_checkpoint(root)
    slot=int(slot)
    if prior.last_committed_slot is not None and slot < prior.last_committed_slot:
        raise ValueError("checkpoint regression rejected")
    x=SolanaChainCheckpoint(slot,str(signature) if signature else None,datetime.now(timezone.utc).isoformat(),prior.generation+1,False)
    q=p.with_suffix(".json.tmp");q.write_text(json.dumps(asdict(x),sort_keys=True,separators=(",",":")),encoding="utf-8");os.replace(q,p)
    return x

"""
TEST_SOURCE=r"""\

import tempfile,unittest
from qseries_v2.oracle_adapters.independent.oad_323_solana_durable_slot_checkpoint import *
class T(unittest.TestCase):
 def test_restart_and_regression(self):
  with tempfile.TemporaryDirectory() as d:
   a=load_solana_chain_checkpoint(d);self.assertIsNone(a.last_committed_slot)
   b=commit_solana_chain_checkpoint(100,"sig100",d);c=load_solana_chain_checkpoint(d)
   print("[CHECKPOINT]",c.last_committed_slot,c.last_committed_signature,"generation=",c.generation)
   self.assertEqual(c.last_committed_slot,100);self.assertEqual(c.generation,1)
   with self.assertRaises(ValueError):commit_solana_chain_checkpoint(99,"old",d)
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] OAD-323 durable Solana slot checkpoint + regression guard certified")

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
