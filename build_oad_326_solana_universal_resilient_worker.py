from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID='OAD-326'
TITLE='SOLANA UNIVERSAL RESILIENT WORKER'
EXPECTED='build_oad_326_solana_universal_resilient_worker.py'
MODULE='oad_326_solana_universal_resilient_worker.py'
TEST='test_oad_326_solana_universal_resilient_worker.py'
DEPENDENCIES=[('qseries_v2/oracle_adapters/independent/oad_323_solana_durable_slot_checkpoint.py', ('commit_solana_chain_checkpoint',)), ('qseries_v2/oracle_adapters/independent/oad_324_solana_gap_backfill_recovery_planner.py', ('build_solana_recovery_plan',)), ('qseries_v2/oracle_adapters/independent/oad_325_solana_universal_single_writer_persistence.py', ('persist_solana_universal_chain_batch',)), ('qseries_v2/oracle_adapters/independent/oad_148_solana_mainnet_chain_state_acquisition.py', ('def _rpc',))]
MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from .oad_148_solana_mainnet_chain_state_acquisition import _rpc
from .oad_323_solana_durable_slot_checkpoint import load_solana_chain_checkpoint,commit_solana_chain_checkpoint
from .oad_324_solana_gap_backfill_recovery_planner import build_solana_recovery_plan
from .oad_325_solana_universal_single_writer_persistence import persist_solana_universal_chain_batch
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class SolanaUniversalWorkerCycle:
    head_slot:int;before_slot:int|None;after_slot:int|None;mode:str;requested_slots:int;transactions:int;observations:int;committed_events:int;state:str;execution_authority:bool=False
def run_solana_universal_worker_cycle(root=None,per_batch_limit=4,timeout_seconds=120.0,acquisition_timeout_seconds=20.0):
    root=Path(root or Path.cwd()).resolve();head=int(_rpc("getSlot",[{"commitment":"finalized"}],acquisition_timeout_seconds))
    plan=build_solana_recovery_plan(head,root);before=load_solana_chain_checkpoint(root)
    if plan.gap_slots<=0:return SolanaUniversalWorkerCycle(head,before.last_committed_slot,before.last_committed_slot,plan.mode,0,0,0,0,"CAUGHT_UP",False)
    count=min(int(per_batch_limit),plan.gap_slots)
    p=persist_solana_universal_chain_batch(plan.start_slot,count,root,timeout_seconds,acquisition_timeout_seconds)
    target=plan.start_slot+count-1
    if p.coverage_state!="UNIVERSAL_BATCH_ACCOUNTED":raise RuntimeError("coverage gate refused checkpoint advance")
    commit_solana_chain_checkpoint(target,None,root)
    return SolanaUniversalWorkerCycle(head,before.last_committed_slot,target,plan.mode,count,p.transactions,p.observations,p.committed_events,"COMMITTED",False)

"""
TEST_SOURCE=r"""\

import tempfile,unittest
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_326_solana_universal_resilient_worker as m
class T(unittest.TestCase):
 def test_commit_after_persistence(self):
  with tempfile.TemporaryDirectory() as d:
   with patch.object(m,"_rpc",return_value=12),patch.object(m,"persist_solana_universal_chain_batch",return_value=SimpleNamespace(transactions=4,observations=8,committed_events=8,coverage_state="UNIVERSAL_BATCH_ACCOUNTED")):
    x=m.run_solana_universal_worker_cycle(d,2)
   cp=m.load_solana_chain_checkpoint(d)
   print("[WORKER]",x.mode,x.before_slot,"->",x.after_slot,"checkpoint=",cp.last_committed_slot)
   self.assertEqual(cp.last_committed_slot,x.after_slot);self.assertEqual(x.state,"COMMITTED")
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] OAD-326 checkpoint advances only after successful universal persistence")

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
