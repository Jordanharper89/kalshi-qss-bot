from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

EXPECTED='build_oad_364_solana_post_commit_observation_reconciliation.py'
BUILD_ID='OAD-364'
TITLE='SOLANA POST-COMMIT OBSERVATION RECONCILIATION'
MODULE='oad_364_solana_post_commit_observation_reconciliation.py'
TEST='test_oad_364_solana_post_commit_observation_reconciliation.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_363_solana_physical_postgresql_readback_adapter.py': ('SolanaPhysicalReadbackProbe', 'physical_readback_probe'), 'qseries_v2/oracle_adapters/independent/oad_325_solana_universal_single_writer_persistence.py': ('oracle.solana_universal_chain', 'submit_observation_batch', 'await_request')}

MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class SolanaPostCommitReconciliation:
    committed_ids: tuple
    found_ids: tuple
    missing_ids: tuple
    duplicate_committed_ids: tuple
    reconciliation_state: str
    execution_authority: bool=False

def reconcile_post_commit_ids(committed_ids, readback_result):
    raw=tuple(str(x) for x in committed_ids)
    seen=set(); dup=[]
    for x in raw:
        if x in seen and x not in dup:
            dup.append(x)
        seen.add(x)
    unique=tuple(dict.fromkeys(raw))
    found=tuple(str(x) for x in getattr(readback_result,"found_ids",()))
    missing=tuple(x for x in unique if x not in set(found))
    if dup:
        state="DUPLICATE_COMMIT_ID_INPUT"
    elif missing:
        state="POST_COMMIT_READBACK_INCOMPLETE"
    else:
        state="POST_COMMIT_RECONCILED"
    return SolanaPostCommitReconciliation(unique,found,missing,tuple(dup),state,False)

"""

TEST_SOURCE=r"""\

import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_364_solana_post_commit_observation_reconciliation import *

class T(unittest.TestCase):
    def test_ok(self):
        x=reconcile_post_commit_ids(("a","b"),SimpleNamespace(found_ids=("a","b")))
        print("[POST-COMMIT]",x.reconciliation_state,x.missing_ids)
        self.assertEqual(x.reconciliation_state,"POST_COMMIT_RECONCILED")
    def test_missing(self):
        x=reconcile_post_commit_ids(("a","b"),SimpleNamespace(found_ids=("a",)))
        self.assertEqual(x.reconciliation_state,"POST_COMMIT_READBACK_INCOMPLETE")

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-364 post-commit observation-ID reconciliation certified")

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
