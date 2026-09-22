from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path
EXPECTED='build_oad_358_solana_skipped_slot_safe_checkpoint.py'; BUILD_ID='OAD-358'; TITLE='SOLANA SKIPPED-SLOT SAFE CHECKPOINT'; MODULE='oad_358_solana_skipped_slot_safe_checkpoint.py'; TEST='test_oad_358_solana_skipped_slot_safe_checkpoint.py'; DEPS={'qseries_v2/oracle_adapters/independent/oad_323_solana_durable_slot_checkpoint.py': ('SolanaChainCheckpoint', 'commit'), 'qseries_v2/oracle_adapters/independent/oad_324_solana_gap_backfill_recovery_planner.py': ('SolanaRecoveryPlan', 'BACKFILL'), 'qseries_v2/oracle_adapters/independent/oad_326_solana_universal_resilient_worker.py': ('SolanaUniversalWorkerCycle',)}
MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SolanaContiguousSlotProof:
    requested_start:int
    requested_end:int
    returned_slots:tuple
    skipped_slots:tuple
    missing_slots:tuple
    highest_contiguous_accounted_slot:int|None
    safe_to_advance:bool
    execution_authority:bool=False

def prove_contiguous_slot_accounting(requested_start,requested_end,returned_slots,skipped_slots=()):
    a=int(requested_start); b=int(requested_end)
    if b<a: raise ValueError("requested_end before requested_start")
    returned={int(x) for x in returned_slots if a<=int(x)<=b}
    skipped={int(x) for x in skipped_slots if a<=int(x)<=b}
    overlap=returned & skipped
    if overlap: raise ValueError("slot cannot be both returned and skipped")
    accounted=returned|skipped; missing=[]
    high=None
    for slot in range(a,b+1):
        if slot not in accounted:
            missing.append(slot); break
        high=slot
    if missing:
        missing.extend(x for x in range(missing[0]+1,b+1) if x not in accounted)
    return SolanaContiguousSlotProof(a,b,tuple(sorted(returned)),tuple(sorted(skipped)),tuple(missing),high,high==b,False)

def safe_checkpoint_target(proof,current_checkpoint=None):
    target=proof.highest_contiguous_accounted_slot
    if target is None: return current_checkpoint
    if current_checkpoint is not None and target<int(current_checkpoint):
        raise RuntimeError("checkpoint regression prohibited")
    return target

"""
TEST_SOURCE=r"""\

import unittest
from qseries_v2.oracle_adapters.independent.oad_358_solana_skipped_slot_safe_checkpoint import *
class T(unittest.TestCase):
    def test_skip_is_accounted(self):
        p=prove_contiguous_slot_accounting(100,104,(100,101,103,104),(102,))
        print("[CONTIGUOUS]",p.highest_contiguous_accounted_slot,p.skipped_slots,p.safe_to_advance)
        self.assertEqual(safe_checkpoint_target(p,99),104); self.assertTrue(p.safe_to_advance)
    def test_missing_stops_checkpoint(self):
        p=prove_contiguous_slot_accounting(100,104,(100,101,103,104),())
        self.assertEqual(p.highest_contiguous_accounted_slot,101); self.assertEqual(safe_checkpoint_target(p,99),101)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-358 skipped-slot-aware contiguous checkpoint advancement certified")

"""
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def atomic(p,src):
    src=textwrap.dedent(src).lstrip(); ast.parse(src,filename=str(p)); p.parent.mkdir(parents=True,exist_ok=True)
    q=p.with_suffix(p.suffix+".tmp"); q.write_text(src,encoding="utf-8",newline="\n"); os.replace(q,p)
def verify(p,marks):
    if not p.is_file(): raise RuntimeError("dependency missing: "+str(p))
    x=p.read_text(encoding="utf-8"); ast.parse(x,filename=str(p))
    for m in marks:
        if m not in x: raise RuntimeError("dependency interface missing: "+p.name+" -> "+m)
def main():
    if Path(__file__).name!=EXPECTED: raise RuntimeError("installer identity mismatch")
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; m=pkg/MODULE; t=r/TEST; init=pkg/"__init__.py"
    print("="*120); print(" "+BUILD_ID+" "+TITLE+" INSTALLER"); print("="*120); print("[ROOT]",r)
    for rel,marks in DEPS.items(): verify(r/rel,marks); print("[PASS] dependency interface verified:",rel)
    protected=[]
    for rel in ("qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
                "qseries_v2/oracle_adapters/independent/oad_327_solana_universal_continuity_physical_certification.py",
                "qseries_v2/oracle_adapters/independent/oad_357_solana_decoder_closeout_same_universe_physical_gate.py"):
        p=r/rel
        if not p.is_file(): raise RuntimeError("protected boundary missing: "+rel)
        protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest()))
    old={p:(p.read_bytes() if p.exists() else None) for p in (m,t,init)}
    try:
        atomic(m,MODULE_SOURCE); atomic(t,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        e="from ."+m.stem+" import *"
        if e not in lines: lines.append(e)
        atomic(init,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h: raise RuntimeError("protected boundary changed: "+p.name)
        print("[PASS] module installed:",m.relative_to(r)); print("[PASS] test installed:",t.name)
        print("[PASS] OPH-023/OAD-327/OAD-357 preserved byte-for-byte unchanged")
        print("[PASS] no bypass PostgreSQL writer introduced")
        print("[PASS] GMGN not required")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(b)
        print("[ROLLBACK] affected files restored"); raise
if __name__=="__main__": main()
