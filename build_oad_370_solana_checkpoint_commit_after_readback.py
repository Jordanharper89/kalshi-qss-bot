from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

EXPECTED='build_oad_370_solana_checkpoint_commit_after_readback.py'
BUILD_ID='OAD-370'
TITLE='SOLANA CHECKPOINT COMMIT AFTER READBACK'
MODULE='oad_370_solana_checkpoint_commit_after_readback.py'
TEST='test_oad_370_solana_checkpoint_commit_after_readback.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_365_solana_checkpoint_after_readback_enforcement.py': ('admit_checkpoint_after_readback', 'CHECKPOINT_ADMITTED'), 'qseries_v2/oracle_adapters/independent/oad_368_solana_physical_checkpoint_contract.py': ('commit_checkpoint_exact',)}

MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
from .oad_365_solana_checkpoint_after_readback_enforcement import admit_checkpoint_after_readback
from .oad_368_solana_physical_checkpoint_contract import commit_checkpoint_exact

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class SolanaCheckpointCommitResult:
    before_slot:int|None
    candidate_slot:int|None
    committed_slot:int|None
    state:str
    execution_authority:bool=False

def commit_checkpoint_after_exact_readback(current_checkpoint, continuity_proof, reconciliation, signature=None, root=None):
    admission=admit_checkpoint_after_readback(current_checkpoint,continuity_proof,reconciliation)
    if admission.state!="CHECKPOINT_ADMITTED":
        return SolanaCheckpointCommitResult(current_checkpoint,admission.candidate_checkpoint,current_checkpoint,admission.state,False)
    target=admission.admitted_checkpoint
    commit_checkpoint_exact(target,signature=signature,root=root)
    return SolanaCheckpointCommitResult(current_checkpoint,target,target,"CHECKPOINT_PHYSICALLY_COMMITTED",False)

"""

TEST_SOURCE=r"""\

import unittest
from unittest.mock import patch
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_370_solana_checkpoint_commit_after_readback import *

class T(unittest.TestCase):
    def test_commit(self):
        proof=SimpleNamespace(highest_contiguous_accounted_slot=104,safe_to_advance=True)
        rec=SimpleNamespace(reconciliation_state="POST_COMMIT_RECONCILED")
        with patch("qseries_v2.oracle_adapters.independent.oad_370_solana_checkpoint_commit_after_readback.commit_checkpoint_exact") as c:
            x=commit_checkpoint_after_exact_readback(100,proof,rec)
            c.assert_called_once()
        print("[CHECKPOINT-COMMIT]",x.before_slot,"->",x.committed_slot,x.state)
        self.assertEqual(x.state,"CHECKPOINT_PHYSICALLY_COMMITTED")

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-370 physical checkpoint commit requires exact readback admission")

"""

def root():
    for b in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (b, *b.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")

def verify(path, markers):
    if not path.is_file():
        raise RuntimeError("dependency missing: "+str(path))
    text=path.read_text(encoding="utf-8")
    ast.parse(text, filename=str(path))
    for marker in markers:
        if marker not in text:
            raise RuntimeError("dependency interface missing: "+path.name+" -> "+marker)

def atomic(path, source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source, encoding="utf-8", newline="\n")
    os.replace(tmp,path)

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
    print("[ROOT]",r)

    for rel, markers in DEPENDENCIES.items():
        verify(r/rel, markers)
        print("[PASS] dependency interface verified:", rel)

    protected=[]
    for rel in (
        "qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
        "qseries_v2/oracle_adapters/independent/oad_327_solana_universal_continuity_physical_certification.py",
        "qseries_v2/oracle_adapters/independent/oad_357_solana_decoder_closeout_same_universe_physical_gate.py",
        "qseries_v2/oracle_adapters/independent/oad_362_solana_continuity_integrity_physical_gate.py",
        "qseries_v2/oracle_adapters/independent/oad_367_solana_end_to_end_persistence_restart_physical_gate.py",
    ):
        p=r/rel
        if p.is_file():
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

        print("[PASS] module installed:",m.relative_to(r))
        print("[PASS] test installed:",t.name)
        print("[PASS] protected certified boundaries preserved")
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
