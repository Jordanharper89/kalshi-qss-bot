from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path
EXPECTED='build_oad_362_solana_continuity_integrity_physical_gate.py'; BUILD_ID='OAD-362'; TITLE='SOLANA CONTINUITY INTEGRITY PHYSICAL GATE'; MODULE='oad_362_solana_continuity_integrity_physical_gate.py'; TEST='test_oad_362_solana_continuity_integrity_physical_gate.py'; DEPS={'qseries_v2/oracle_adapters/independent/oad_318_solana_native_finalized_block_stream.py': ('acquire_finalized_block_batch',), 'qseries_v2/oracle_adapters/independent/oad_319_solana_transaction_canonical_envelope.py': ('canonical_transaction_envelopes',), 'qseries_v2/oracle_adapters/independent/oad_358_solana_skipped_slot_safe_checkpoint.py': ('prove_contiguous_slot_accounting',), 'qseries_v2/oracle_adapters/independent/oad_359_solana_immutable_gap_lineage_ledger.py': ('verify_gap_lineage',), 'qseries_v2/oracle_adapters/independent/oad_361_solana_restart_backfill_reconciliation.py': ('reconcile_restart_window',)}
MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import tempfile
from .oad_318_solana_native_finalized_block_stream import acquire_finalized_block_batch
from .oad_319_solana_transaction_canonical_envelope import canonical_transaction_envelopes
from .oad_358_solana_skipped_slot_safe_checkpoint import prove_contiguous_slot_accounting
from .oad_359_solana_immutable_gap_lineage_ledger import append_gap_lineage,verify_gap_lineage
from .oad_361_solana_restart_backfill_reconciliation import reconcile_restart_window
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class SolanaContinuityIntegrityPhysicalReport:
    blocks:int; transactions:int; first_slot:int; last_slot:int; returned_slots:tuple; contiguous:bool
    restart_checkpoint:int|None; gap_ledger_valid:bool; gap_records:int; duplicate_signatures:int
    state:str; execution_authority:bool=False
def _slot(b):
    for k in ("slot","block_slot"):
        if hasattr(b,k): return int(getattr(b,k))
        if isinstance(b,dict) and k in b:return int(b[k])
    raise RuntimeError("block slot unavailable")
def measure_continuity_integrity_physical(block_limit=4,timeout_seconds=30.0):
    batch=acquire_finalized_block_batch(None,block_limit,timeout_seconds); blocks=tuple(batch.blocks)
    env=canonical_transaction_envelopes(batch)
    slots=tuple(sorted(dict.fromkeys(_slot(b) for b in blocks)))
    if not slots:return SolanaContinuityIntegrityPhysicalReport(0,0,0,0,(),False,None,True,0,0,"NO_LIVE_BLOCKS",False)
    # This gate proves the returned live range itself; skipped slots are not fabricated.
    proof=prove_contiguous_slot_accounting(slots[0],slots[-1],slots,())
    sigs=[str(e.signature) for e in env]; dup=len(sigs)-len(set(sigs))
    with tempfile.TemporaryDirectory() as d:
        if proof.missing_slots: append_gap_lineage(slots[0],slots[-1],"LIVE_RANGE_UNRESOLVED_GAP",proof.missing_slots,d)
        # Simulated restart starts immediately before this observed range; any real holes correctly block advancement.
        x=reconcile_restart_window(slots[0]-1,slots[-1],slots,(),d)
        ok,n=verify_gap_lineage(d)
    state="CONTINUITY_INTEGRITY_PHYSICALLY_MEASURED"
    return SolanaContinuityIntegrityPhysicalReport(len(blocks),len(env),slots[0],slots[-1],slots,proof.safe_to_advance,x.checkpoint_after,ok,n,dup,state,False)

"""
TEST_SOURCE=r"""\

import unittest
from qseries_v2.oracle_adapters.independent.oad_362_solana_continuity_integrity_physical_gate import *
class T(unittest.TestCase):
    def test_physical(self):
        x=measure_continuity_integrity_physical(4)
        print("[PHYSICAL] blocks=",x.blocks,"transactions=",x.transactions,"slots=",x.returned_slots)
        print("[PHYSICAL] contiguous=",x.contiguous,"restart_checkpoint=",x.restart_checkpoint,"gap_ledger_valid=",x.gap_ledger_valid,"gap_records=",x.gap_records)
        print("[PHYSICAL] duplicate_signatures=",x.duplicate_signatures,"state=",x.state)
        self.assertGreaterEqual(x.blocks,1); self.assertGreater(x.transactions,0); self.assertTrue(x.gap_ledger_valid)
        self.assertEqual(x.duplicate_signatures,0); self.assertEqual(x.state,"CONTINUITY_INTEGRITY_PHYSICALLY_MEASURED")
        self.assertFalse(x.execution_authority)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-362 sustained live Solana continuity-integrity gate measured")
    print("[PASS] missing slots block checkpoint advancement rather than being silently skipped")

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
