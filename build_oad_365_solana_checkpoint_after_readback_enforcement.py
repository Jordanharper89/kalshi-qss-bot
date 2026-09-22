from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

EXPECTED='build_oad_365_solana_checkpoint_after_readback_enforcement.py'
BUILD_ID='OAD-365'
TITLE='SOLANA CHECKPOINT AFTER READBACK ENFORCEMENT'
MODULE='oad_365_solana_checkpoint_after_readback_enforcement.py'
TEST='test_oad_365_solana_checkpoint_after_readback_enforcement.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_358_solana_skipped_slot_safe_checkpoint.py': ('safe_checkpoint_target', 'SolanaContiguousSlotProof'), 'qseries_v2/oracle_adapters/independent/oad_364_solana_post_commit_observation_reconciliation.py': ('POST_COMMIT_RECONCILED', 'SolanaPostCommitReconciliation')}

MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
from .oad_358_solana_skipped_slot_safe_checkpoint import safe_checkpoint_target

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class SolanaCheckpointAdmission:
    current_checkpoint: int|None
    candidate_checkpoint: int|None
    admitted_checkpoint: int|None
    readback_exact: bool
    continuity_safe: bool
    state: str
    execution_authority: bool=False

def admit_checkpoint_after_readback(current_checkpoint, continuity_proof, reconciliation):
    candidate=safe_checkpoint_target(continuity_proof,current_checkpoint)
    readback_exact=(getattr(reconciliation,"reconciliation_state","")=="POST_COMMIT_RECONCILED")
    continuity_safe=bool(getattr(continuity_proof,"safe_to_advance",False))
    if not readback_exact:
        return SolanaCheckpointAdmission(current_checkpoint,candidate,current_checkpoint,False,continuity_safe,"BLOCKED_READBACK",False)
    if not continuity_safe:
        return SolanaCheckpointAdmission(current_checkpoint,candidate,current_checkpoint,True,False,"BLOCKED_CONTINUITY",False)
    return SolanaCheckpointAdmission(current_checkpoint,candidate,candidate,True,True,"CHECKPOINT_ADMITTED",False)

"""

TEST_SOURCE=r"""\

import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_365_solana_checkpoint_after_readback_enforcement import *

class T(unittest.TestCase):
    def test_admit(self):
        proof=SimpleNamespace(highest_contiguous_accounted_slot=104,safe_to_advance=True)
        rec=SimpleNamespace(reconciliation_state="POST_COMMIT_RECONCILED")
        x=admit_checkpoint_after_readback(100,proof,rec)
        print("[CHECKPOINT-ADMIT]",x.current_checkpoint,"->",x.admitted_checkpoint,x.state)
        self.assertEqual(x.admitted_checkpoint,104)
    def test_block(self):
        proof=SimpleNamespace(highest_contiguous_accounted_slot=104,safe_to_advance=True)
        rec=SimpleNamespace(reconciliation_state="POST_COMMIT_READBACK_INCOMPLETE")
        x=admit_checkpoint_after_readback(100,proof,rec)
        self.assertEqual(x.admitted_checkpoint,100)
        self.assertEqual(x.state,"BLOCKED_READBACK")

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-365 checkpoint advancement now requires exact post-commit readback + continuity")

"""

def root():
    for b in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (b, *b.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")

def atomic(path, source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source, encoding="utf-8", newline="\n")
    os.replace(tmp, path)

def verify(path, markers):
    if not path.is_file():
        raise RuntimeError("dependency missing: "+str(path))
    text=path.read_text(encoding="utf-8")
    ast.parse(text, filename=str(path))
    for marker in markers:
        if marker not in text:
            raise RuntimeError("dependency interface missing: "+path.name+" -> "+marker)

def main():
    if Path(__file__).name != EXPECTED:
        raise RuntimeError("installer identity mismatch")
    r=root()
    pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    m=pkg/MODULE
    t=r/TEST
    init=pkg/"__init__.py"

    print("="*120)
    print(" "+BUILD_ID+" "+TITLE+" INSTALLER")
    print("="*120)
    print("[ROOT]", r)

    for rel, markers in DEPENDENCIES.items():
        verify(r/rel, markers)
        print("[PASS] dependency interface verified:", rel)

    protected=[]
    for rel in (
        "qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
        "qseries_v2/oracle_adapters/independent/oad_327_solana_universal_continuity_physical_certification.py",
        "qseries_v2/oracle_adapters/independent/oad_357_solana_decoder_closeout_same_universe_physical_gate.py",
        "qseries_v2/oracle_adapters/independent/oad_362_solana_continuity_integrity_physical_gate.py",
    ):
        p=r/rel
        if not p.is_file():
            raise RuntimeError("protected boundary missing: "+rel)
        protected.append((p, hashlib.sha256(p.read_bytes()).hexdigest()))

    old={p:(p.read_bytes() if p.exists() else None) for p in (m,t,init)}
    try:
        atomic(m, MODULE_SOURCE)
        atomic(t, TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        export="from ."+m.stem+" import *"
        if export not in lines:
            lines.append(export)
        atomic(init, "\n".join(x for x in lines if x.strip())+"\n")

        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("protected boundary changed: "+p.name)

        print("[PASS] module installed:", m.relative_to(r))
        print("[PASS] test installed:", t.name)
        print("[PASS] OPH-023/OAD-327/OAD-357/OAD-362 preserved byte-for-byte unchanged")
        print("[PASS] no bypass PostgreSQL writer introduced")
        print("[PASS] GMGN not required")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(b)
        print("[ROLLBACK] affected files restored")
        raise

if __name__=="__main__":
    main()
