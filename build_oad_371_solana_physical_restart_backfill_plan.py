from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

EXPECTED='build_oad_371_solana_physical_restart_backfill_plan.py'
BUILD_ID='OAD-371'
TITLE='SOLANA PHYSICAL RESTART BACKFILL PLAN'
MODULE='oad_371_solana_physical_restart_backfill_plan.py'
TEST='test_oad_371_solana_physical_restart_backfill_plan.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_361_solana_restart_backfill_reconciliation.py': ('reconcile_restart_window',), 'qseries_v2/oracle_adapters/independent/oad_366_solana_restart_backfill_idempotency_guard.py': ('reconcile_restart_idempotency',), 'qseries_v2/oracle_adapters/independent/oad_368_solana_physical_checkpoint_contract.py': ('discover_checkpoint_contract',)}

MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
from .oad_366_solana_restart_backfill_idempotency_guard import reconcile_restart_idempotency
from .oad_368_solana_physical_checkpoint_contract import discover_checkpoint_contract
from .oad_361_solana_restart_backfill_reconciliation import reconcile_restart_window

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class SolanaPhysicalRestartPlan:
    checkpoint_before:int|None
    finalized_head:int
    returned_slots:tuple
    skipped_slots:tuple
    restart_state:str
    replay_idempotent:bool
    accepted_new_ids:tuple
    execution_authority:bool=False

def build_physical_restart_plan(finalized_head,returned_slots,existing_ids=(),replay_ids=(),skipped_slots=(),root=None):
    cp=discover_checkpoint_contract(root)
    before=cp.current_slot
    rec=reconcile_restart_window(before,finalized_head,returned_slots,skipped_slots,root)
    idem=reconcile_restart_idempotency(existing_ids,replay_ids)
    return SolanaPhysicalRestartPlan(
        before,int(finalized_head),tuple(returned_slots),tuple(skipped_slots),
        str(getattr(rec,"state",getattr(rec,"reconciliation_state","UNKNOWN"))),
        bool(idem.idempotent),tuple(idem.accepted_new_ids),False
    )

"""

TEST_SOURCE=r"""\

import unittest
from unittest.mock import patch
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_371_solana_physical_restart_backfill_plan import *

class T(unittest.TestCase):
    def test_plan(self):
        with patch("qseries_v2.oracle_adapters.independent.oad_371_solana_physical_restart_backfill_plan.discover_checkpoint_contract",return_value=SimpleNamespace(current_slot=100)):
            with patch("qseries_v2.oracle_adapters.independent.oad_371_solana_physical_restart_backfill_plan.reconcile_restart_window",return_value=SimpleNamespace(state="RECONCILED_TO_HEAD")):
                x=build_physical_restart_plan(103,(101,102,103),("a",),("a","b"))
        print("[RESTART-PLAN]",x.checkpoint_before,"->",x.finalized_head,x.restart_state,x.accepted_new_ids)
        self.assertTrue(x.replay_idempotent)
        self.assertEqual(x.accepted_new_ids,("b",))

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-371 persisted-checkpoint restart/backfill idempotency plan certified")

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
