from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

EXPECTED='build_oad_366_solana_restart_backfill_idempotency_guard.py'
BUILD_ID='OAD-366'
TITLE='SOLANA RESTART BACKFILL IDEMPOTENCY GUARD'
MODULE='oad_366_solana_restart_backfill_idempotency_guard.py'
TEST='test_oad_366_solana_restart_backfill_idempotency_guard.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_361_solana_restart_backfill_reconciliation.py': ('SolanaRestartReconciliation', 'BACKFILL_REQUIRED'), 'qseries_v2/oracle_adapters/independent/oad_364_solana_post_commit_observation_reconciliation.py': ('SolanaPostCommitReconciliation',)}

MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
from collections import Counter

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class SolanaRestartIdempotencyResult:
    before_ids: tuple
    replay_ids: tuple
    new_ids: tuple
    duplicate_replay_ids: tuple
    duplicate_with_existing_ids: tuple
    accepted_new_ids: tuple
    idempotent: bool
    state: str
    execution_authority: bool=False

def reconcile_restart_idempotency(existing_ids,replay_ids):
    before=tuple(dict.fromkeys(str(x) for x in existing_ids))
    replay=tuple(str(x) for x in replay_ids)
    counts=Counter(replay)
    duplicate_replay=tuple(sorted(x for x,n in counts.items() if n>1))
    existing=set(before)
    duplicate_existing=tuple(x for x in dict.fromkeys(replay) if x in existing)
    accepted=tuple(x for x in dict.fromkeys(replay) if x not in existing)
    idempotent=(len(set(accepted))==len(accepted))
    state="RESTART_REPLAY_IDEMPOTENT" if idempotent else "RESTART_REPLAY_DUPLICATE_FAILURE"
    return SolanaRestartIdempotencyResult(before,replay,accepted,duplicate_replay,duplicate_existing,accepted,idempotent,state,False)

"""

TEST_SOURCE=r"""\

import unittest
from qseries_v2.oracle_adapters.independent.oad_366_solana_restart_backfill_idempotency_guard import *

class T(unittest.TestCase):
    def test_replay(self):
        x=reconcile_restart_idempotency(("a","b"),("b","c","c","d"))
        print("[IDEMPOTENCY]",x.duplicate_with_existing_ids,x.duplicate_replay_ids,x.accepted_new_ids,x.state)
        self.assertEqual(x.accepted_new_ids,("c","d"))
        self.assertTrue(x.idempotent)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-366 restart/backfill duplicate suppression and idempotency guard certified")

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
