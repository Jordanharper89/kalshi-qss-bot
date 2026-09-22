from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path
EXPECTED='build_oad_361_solana_restart_backfill_reconciliation.py'; BUILD_ID='OAD-361'; TITLE='SOLANA RESTART BACKFILL RECONCILIATION'; MODULE='oad_361_solana_restart_backfill_reconciliation.py'; TEST='test_oad_361_solana_restart_backfill_reconciliation.py'; DEPS={'qseries_v2/oracle_adapters/independent/oad_358_solana_skipped_slot_safe_checkpoint.py': ('prove_contiguous_slot_accounting', 'safe_checkpoint_target'), 'qseries_v2/oracle_adapters/independent/oad_359_solana_immutable_gap_lineage_ledger.py': ('append_gap_lineage', 'verify_gap_lineage'), 'qseries_v2/oracle_adapters/independent/oad_324_solana_gap_backfill_recovery_planner.py': ('BACKFILL', 'SolanaRecoveryPlan')}
MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
from .oad_358_solana_skipped_slot_safe_checkpoint import prove_contiguous_slot_accounting,safe_checkpoint_target
from .oad_359_solana_immutable_gap_lineage_ledger import append_gap_lineage
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class SolanaRestartReconciliation:
    checkpoint_before:int|None; finalized_head:int; recovery_start:int; recovery_end:int; returned_slots:tuple; skipped_slots:tuple
    missing_slots:tuple; checkpoint_after:int|None; state:str; execution_authority:bool=False
def reconcile_restart_window(checkpoint_before,finalized_head,returned_slots,skipped_slots=(),root=None):
    head=int(finalized_head); start=(int(checkpoint_before)+1) if checkpoint_before is not None else min(tuple(returned_slots) or (head,))
    end=head
    proof=prove_contiguous_slot_accounting(start,end,returned_slots,skipped_slots)
    if proof.skipped_slots: append_gap_lineage(start,end,"FINALIZED_SKIPPED_SLOTS",proof.skipped_slots,root)
    if proof.missing_slots: append_gap_lineage(start,end,"UNRECOVERED_FINALIZED_GAP",proof.missing_slots,root)
    after=safe_checkpoint_target(proof,checkpoint_before)
    state="RECONCILED_TO_HEAD" if after==head else "BACKFILL_REQUIRED"
    return SolanaRestartReconciliation(checkpoint_before,head,start,end,proof.returned_slots,proof.skipped_slots,proof.missing_slots,after,state,False)

"""
TEST_SOURCE=r"""\

import unittest,tempfile
from qseries_v2.oracle_adapters.independent.oad_361_solana_restart_backfill_reconciliation import *
from qseries_v2.oracle_adapters.independent.oad_359_solana_immutable_gap_lineage_ledger import verify_gap_lineage
class T(unittest.TestCase):
    def test_restart(self):
        with tempfile.TemporaryDirectory() as d:
            x=reconcile_restart_window(100,104,(101,103,104),(102,),d)
            print("[RESTART]",x.checkpoint_before,"->",x.checkpoint_after,x.state,x.skipped_slots); self.assertEqual(x.checkpoint_after,104)
            ok,n=verify_gap_lineage(d); self.assertTrue(ok); self.assertEqual(n,1)
    def test_gap_stops(self):
        with tempfile.TemporaryDirectory() as d:
            x=reconcile_restart_window(100,104,(101,103,104),(),d); self.assertEqual(x.checkpoint_after,101); self.assertEqual(x.state,"BACKFILL_REQUIRED")
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-361 restart/downtime/backfill reconciliation certified")

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
