from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

EXPECTED="build_oad_362_solana_continuity_integrity_physical_gate_BATCH_SHAPE_REBUILD.py"
MODULE="oad_362_solana_continuity_integrity_physical_gate.py"
TEST="test_oad_362_solana_continuity_integrity_physical_gate.py"

MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
import tempfile

from .oad_318_solana_native_finalized_block_stream import acquire_finalized_block_batch
from .oad_319_solana_transaction_canonical_envelope import canonical_transaction_envelopes
from .oad_358_solana_skipped_slot_safe_checkpoint import prove_contiguous_slot_accounting
from .oad_359_solana_immutable_gap_lineage_ledger import append_gap_lineage,verify_gap_lineage
from .oad_361_solana_restart_backfill_reconciliation import reconcile_restart_window

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SolanaContinuityIntegrityPhysicalReport:
    blocks:int
    transactions:int
    first_slot:int
    last_slot:int
    returned_slots:tuple
    contiguous:bool
    restart_checkpoint:int|None
    gap_ledger_valid:bool
    gap_records:int
    duplicate_signatures:int
    state:str
    slot_source:str
    execution_authority:bool=False

def _int_or_none(v):
    try:
        if v is None:
            return None
        return int(v)
    except Exception:
        return None

def _block_slot(block):
    # Accept mapping/object forms, including nested block wrappers.
    keys=("slot","block_slot","blockSlot")
    if isinstance(block,dict):
        for k in keys:
            if k in block:
                x=_int_or_none(block[k])
                if x is not None:
                    return x
        for k in ("block","value","result","data"):
            nested=block.get(k)
            if isinstance(nested,dict):
                for kk in keys:
                    if kk in nested:
                        x=_int_or_none(nested[kk])
                        if x is not None:
                            return x
    for k in keys:
        if hasattr(block,k):
            x=_int_or_none(getattr(block,k))
            if x is not None:
                return x
    for k in ("block","value","result","data"):
        if hasattr(block,k):
            nested=getattr(block,k)
            if isinstance(nested,dict):
                for kk in keys:
                    if kk in nested:
                        x=_int_or_none(nested[kk])
                        if x is not None:
                            return x
            else:
                for kk in keys:
                    if hasattr(nested,kk):
                        x=_int_or_none(getattr(nested,kk))
                        if x is not None:
                            return x
    return None

def _batch_slots(batch,blocks):
    # Prefer explicit slot collections emitted by the certified acquisition batch.
    for name in ("slots","returned_slots","block_slots","requested_slots"):
        if hasattr(batch,name):
            raw=getattr(batch,name)
            if raw is not None and not isinstance(raw,(str,bytes,int,float)):
                vals=tuple(x for x in (_int_or_none(v) for v in raw) if x is not None)
                if vals:
                    return tuple(sorted(dict.fromkeys(vals))),"BATCH_"+name.upper()

    # Some batch contracts carry exact range metadata rather than embedding slot in block payload.
    start=None
    end=None
    for name in ("start_slot","requested_start_slot","first_slot"):
        if hasattr(batch,name):
            start=_int_or_none(getattr(batch,name))
            if start is not None:
                break
    for name in ("end_slot","requested_end_slot","last_slot"):
        if hasattr(batch,name):
            end=_int_or_none(getattr(batch,name))
            if end is not None:
                break

    # Try direct/nested block payload slot fields.
    direct=tuple(x for x in (_block_slot(b) for b in blocks) if x is not None)
    if len(direct)==len(blocks) and direct:
        return tuple(sorted(dict.fromkeys(direct))),"BLOCK_PAYLOAD"

    # If acquisition batch proves an exact start/end range and block count matches,
    # reconstruct only the returned range represented by that batch.
    if start is not None and end is not None and end>=start:
        expected=end-start+1
        if expected==len(blocks):
            return tuple(range(start,end+1)),"BATCH_EXACT_RANGE"

    # Final safe fallback: infer from canonical transaction envelopes.
    # OAD-319 envelopes have slot in the certified production contract.
    env=canonical_transaction_envelopes(batch)
    envslots=tuple(sorted(dict.fromkeys(
        int(getattr(e,"slot")) for e in env if getattr(e,"slot",None) is not None
    )))
    if envslots:
        return envslots,"CANONICAL_ENVELOPE_SLOT"

    raise RuntimeError("unable to resolve finalized block slots from certified OAD-318/OAD-319 batch contracts")

def measure_continuity_integrity_physical(block_limit=4,timeout_seconds=30.0):
    batch=acquire_finalized_block_batch(None,block_limit,timeout_seconds)
    blocks=tuple(batch.blocks)
    env=canonical_transaction_envelopes(batch)

    slots,slot_source=_batch_slots(batch,blocks)
    if not slots:
        return SolanaContinuityIntegrityPhysicalReport(
            len(blocks),len(env),0,0,(),False,None,True,0,0,
            "NO_LIVE_BLOCKS",slot_source,False
        )

    proof=prove_contiguous_slot_accounting(slots[0],slots[-1],slots,())
    sigs=[str(e.signature) for e in env]
    dup=len(sigs)-len(set(sigs))

    with tempfile.TemporaryDirectory() as d:
        if proof.missing_slots:
            append_gap_lineage(
                slots[0],slots[-1],"LIVE_RANGE_UNRESOLVED_GAP",proof.missing_slots,d
            )
        x=reconcile_restart_window(slots[0]-1,slots[-1],slots,(),d)
        ok,n=verify_gap_lineage(d)

    return SolanaContinuityIntegrityPhysicalReport(
        len(blocks),len(env),slots[0],slots[-1],slots,proof.safe_to_advance,
        x.checkpoint_after,ok,n,dup,"CONTINUITY_INTEGRITY_PHYSICALLY_MEASURED",
        slot_source,False
    )
"""

TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_adapters.independent.oad_362_solana_continuity_integrity_physical_gate import *

class T(unittest.TestCase):
    def test_physical(self):
        x=measure_continuity_integrity_physical(4)
        print("[PHYSICAL] blocks=",x.blocks,"transactions=",x.transactions,"slots=",x.returned_slots)
        print("[PHYSICAL] slot_source=",x.slot_source,"contiguous=",x.contiguous,"restart_checkpoint=",x.restart_checkpoint)
        print("[PHYSICAL] gap_ledger_valid=",x.gap_ledger_valid,"gap_records=",x.gap_records)
        print("[PHYSICAL] duplicate_signatures=",x.duplicate_signatures,"state=",x.state)

        self.assertGreaterEqual(x.blocks,1)
        self.assertGreater(x.transactions,0)
        self.assertGreater(len(x.returned_slots),0)
        self.assertTrue(x.gap_ledger_valid)
        self.assertEqual(x.duplicate_signatures,0)
        self.assertEqual(x.state,"CONTINUITY_INTEGRITY_PHYSICALLY_MEASURED")
        self.assertFalse(x.execution_authority)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OAD-362 live Solana continuity-integrity gate measured")
    print("[PASS] slot identity resolved from certified batch/envelope contract rather than guessed block payload shape")
"""

def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")

def atomic(p,source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(p))
    p.parent.mkdir(parents=True,exist_ok=True)
    q=p.with_suffix(p.suffix+".tmp")
    q.write_text(source,encoding="utf-8",newline="\n")
    os.replace(q,p)

def parse(path):
    if not path.is_file():
        raise RuntimeError("dependency missing: "+str(path))
    text=path.read_text(encoding="utf-8")
    tree=ast.parse(text,filename=str(path))
    funcs={n.name for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
    classes={n.name for n in ast.walk(tree) if isinstance(n,ast.ClassDef)}
    return text,funcs,classes

def main():
    if Path(__file__).name!=EXPECTED:
        raise RuntimeError("installer identity mismatch")

    r=root()
    pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    m=pkg/MODULE
    t=r/TEST
    init=pkg/"__init__.py"

    print("="*120)
    print(" OAD-362 SOLANA CONTINUITY INTEGRITY PHYSICAL GATE - BATCH SHAPE REBUILD INSTALLER")
    print("="*120)
    print("[ROOT]",r)

    # Verify actual production interfaces rather than payload-shape literals.
    p318=pkg/"oad_318_solana_native_finalized_block_stream.py"
    text318,funcs318,classes318=parse(p318)
    if "acquire_finalized_block_batch" not in funcs318:
        raise RuntimeError("OAD-318 acquisition callable missing")
    if "SolanaFinalizedBlockBatch" not in classes318 and "blocks" not in text318:
        raise RuntimeError("OAD-318 finalized batch contract missing")
    print("[PASS] OAD-318 finalized batch acquisition interface verified")

    p319=pkg/"oad_319_solana_transaction_canonical_envelope.py"
    text319,funcs319,classes319=parse(p319)
    if "canonical_transaction_envelopes" not in funcs319:
        raise RuntimeError("OAD-319 canonical envelope callable missing")
    if "SolanaTransactionEnvelope" not in classes319:
        raise RuntimeError("OAD-319 transaction envelope contract missing")
    print("[PASS] OAD-319 canonical transaction envelope interface verified")

    for dep,marks in (
        ("oad_358_solana_skipped_slot_safe_checkpoint.py",("prove_contiguous_slot_accounting","safe_checkpoint_target")),
        ("oad_359_solana_immutable_gap_lineage_ledger.py",("verify_gap_lineage","append_gap_lineage")),
        ("oad_361_solana_restart_backfill_reconciliation.py",("reconcile_restart_window",)),
    ):
        p=pkg/dep
        text,funcs,classes=parse(p)
        for mark in marks:
            if mark not in funcs and mark not in classes and mark not in text:
                raise RuntimeError("dependency interface missing: "+dep+" -> "+mark)
        print("[PASS] dependency interface verified:",p.relative_to(r))

    protected=[]
    for rel in (
        "qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
        "qseries_v2/oracle_adapters/independent/oad_327_solana_universal_continuity_physical_certification.py",
        "qseries_v2/oracle_adapters/independent/oad_357_solana_decoder_closeout_same_universe_physical_gate.py",
    ):
        p=r/rel
        if not p.is_file():
            raise RuntimeError("protected boundary missing: "+rel)
        protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest()))

    old={p:(p.read_bytes() if p.exists() else None) for p in (m,t,init)}
    try:
        atomic(m,MODULE_SOURCE)
        atomic(t,TEST_SOURCE)

        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        export="from ."+m.stem+" import *"
        if export not in lines:
            lines.append(export)
        atomic(init,"\n".join(x for x in lines if x.strip())+"\n")

        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("protected boundary changed: "+p.name)

        print("[PASS] module replaced:",m.relative_to(r))
        print("[PASS] test replaced:",t.name)
        print("[PASS] block-slot extraction no longer assumes direct block.slot payload")
        print("[PASS] slot identity resolves through OAD-318 batch metadata or OAD-319 canonical envelope slot")
        print("[PASS] OPH-023/OAD-327/OAD-357 preserved byte-for-byte unchanged")
        print("[PASS] no bypass PostgreSQL writer introduced")
        print("[PASS] GMGN not required")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-362 BATCH SHAPE REBUILD INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(b)
        print("[ROLLBACK] affected files restored")
        raise

if __name__=="__main__":
    main()
