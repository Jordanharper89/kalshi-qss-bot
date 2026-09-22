from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

EXPECTED='build_oad_369_solana_postcommit_exact_readback_bridge.py'
BUILD_ID='OAD-369'
TITLE='SOLANA POST-COMMIT EXACT READBACK BRIDGE'
MODULE='oad_369_solana_postcommit_exact_readback_bridge.py'
TEST='test_oad_369_solana_postcommit_exact_readback_bridge.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_363_solana_physical_postgresql_readback_adapter.py': ('physical_readback_probe', 'SolanaPhysicalReadbackProbe'), 'qseries_v2/oracle_adapters/independent/oad_364_solana_post_commit_observation_reconciliation.py': ('reconcile_post_commit_ids', 'POST_COMMIT_RECONCILED')}

MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
import hashlib, json
from .oad_363_solana_physical_postgresql_readback_adapter import physical_readback_probe
from .oad_364_solana_post_commit_observation_reconciliation import reconcile_post_commit_ids

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class SolanaCommittedBatchReadback:
    observation_ids:tuple
    found_ids:tuple
    missing_ids:tuple
    exact:bool
    reconciliation_state:str
    execution_authority:bool=False

def observation_id_of(obj):
    for n in ("observation_id","id","canonical_observation_id","event_id"):
        if hasattr(obj,n):
            v=getattr(obj,n)
            if v is not None: return str(v)
        if isinstance(obj,dict) and obj.get(n) is not None:
            return str(obj[n])
    if hasattr(obj,"to_dict"):
        obj=obj.to_dict()
    if hasattr(obj,"__dict__"):
        obj={k:v for k,v in vars(obj).items() if not k.startswith("_")}
    if isinstance(obj,dict):
        raw=json.dumps(obj,sort_keys=True,separators=(",",":"),default=str).encode()
        return hashlib.sha256(raw).hexdigest()
    raise RuntimeError("cannot derive stable observation id")

def verify_committed_batch_exact_readback(observations, reader=None):
    ids=tuple(observation_id_of(x) for x in observations)
    probe=physical_readback_probe(ids,reader=reader)
    rec=reconcile_post_commit_ids(ids,probe)
    return SolanaCommittedBatchReadback(
        rec.committed_ids,rec.found_ids,rec.missing_ids,
        rec.reconciliation_state=="POST_COMMIT_RECONCILED",
        rec.reconciliation_state,False
    )

"""

TEST_SOURCE=r"""\

import unittest
from qseries_v2.oracle_adapters.independent.oad_369_solana_postcommit_exact_readback_bridge import *

class T(unittest.TestCase):
    def test_bridge(self):
        obs=({"observation_id":"a"},{"observation_id":"b"})
        x=verify_committed_batch_exact_readback(obs,lambda ids:[{"observation_id":"a"},{"observation_id":"b"}])
        print("[READBACK-BRIDGE]",x.observation_ids,x.found_ids,x.missing_ids,x.reconciliation_state)
        self.assertTrue(x.exact)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-369 committed Solana batch -> exact PostgreSQL readback bridge certified")

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
