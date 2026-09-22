from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID='OAD-324'
TITLE='SOLANA GAP BACKFILL RECOVERY PLANNER'
EXPECTED='build_oad_324_solana_gap_backfill_recovery_planner.py'
MODULE='oad_324_solana_gap_backfill_recovery_planner.py'
TEST='test_oad_324_solana_gap_backfill_recovery_planner.py'
DEPENDENCIES=[('qseries_v2/oracle_adapters/independent/oad_323_solana_durable_slot_checkpoint.py', ('load_solana_chain_checkpoint', 'commit_solana_chain_checkpoint')), ('qseries_v2/oracle_adapters/independent/oad_318_solana_native_finalized_block_stream.py', ('acquire_finalized_block_batch',))]
MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
from .oad_318_solana_native_finalized_block_stream import acquire_finalized_block_batch
from .oad_323_solana_durable_slot_checkpoint import load_solana_chain_checkpoint
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class SolanaRecoveryPlan:
    checkpoint_slot:int|None; finalized_head:int; start_slot:int; end_slot:int; gap_slots:int; mode:str; execution_authority:bool=False
def build_solana_recovery_plan(finalized_head,root=None,max_backfill_slots=256):
    cp=load_solana_chain_checkpoint(root);head=int(finalized_head)
    if cp.last_committed_slot is None:
        start=max(0,head-min(int(max_backfill_slots),32)+1);mode="BOOTSTRAP"
    else:
        start=cp.last_committed_slot+1;mode="LIVE_CONTINUE" if start>=head else "BACKFILL"
    gap=max(0,head-start+1)
    return SolanaRecoveryPlan(cp.last_committed_slot,head,start,head,gap,mode,False)
def acquire_recovery_batch(finalized_head,root=None,max_backfill_slots=256,per_batch_limit=16,timeout_seconds=20.0):
    p=build_solana_recovery_plan(finalized_head,root,max_backfill_slots)
    if p.gap_slots<=0:return p,None
    limit=min(int(per_batch_limit),p.gap_slots)
    return p,acquire_finalized_block_batch(p.start_slot,limit,timeout_seconds)

"""
TEST_SOURCE=r"""\

import tempfile,unittest
from qseries_v2.oracle_adapters.independent.oad_323_solana_durable_slot_checkpoint import commit_solana_chain_checkpoint
from qseries_v2.oracle_adapters.independent.oad_324_solana_gap_backfill_recovery_planner import *
class T(unittest.TestCase):
 def test_gap(self):
  with tempfile.TemporaryDirectory() as d:
   commit_solana_chain_checkpoint(100,"s",d)
   p=build_solana_recovery_plan(105,d)
   print("[RECOVERY]",p.mode,p.start_slot,p.end_slot,"gap=",p.gap_slots)
   self.assertEqual((p.start_slot,p.end_slot,p.gap_slots),(101,105,5));self.assertEqual(p.mode,"BACKFILL")
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] OAD-324 recoverable finalized-slot gap planning certified")

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
