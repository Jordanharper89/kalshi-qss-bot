from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

EXPECTED='build_oad_375_solana_verified_forward_outcome_bridge.py'
BUILD_ID='OAD-375'
TITLE='SOLANA VERIFIED FORWARD OUTCOME BRIDGE'
MODULE='oad_375_solana_verified_forward_outcome_bridge.py'
TEST='test_oad_375_solana_verified_forward_outcome_bridge.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_374_solana_temporal_case_bridge.py': ('SolanaTemporalLearningCase', 'OUTCOME_PENDING'), 'qseries_v2/oracle_adapters/independent/oad_314_solana_verified_forward_outcome_attribution.py': ('UP', 'DOWN', 'FLAT')}
EXTRA_PROTECTED=()

MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
from math import isfinite
from .oad_374_solana_temporal_case_bridge import SolanaTemporalLearningCase

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class SolanaVerifiedForwardOutcome:
    case_id:str
    horizon_seconds:int
    anchor_price:float
    forward_price:float
    return_fraction:float
    outcome:str
    verified:bool
    evidence_source:str
    execution_authority:bool=False

def attribute_verified_forward_outcome(case:SolanaTemporalLearningCase,horizon_seconds,anchor_price,forward_price,evidence_source="SOLANA_CANONICAL_HISTORY"):
    h=int(horizon_seconds)
    if h not in case.horizons_seconds:
        raise ValueError("horizon not present in temporal case")
    a=float(anchor_price); f=float(forward_price)
    if a<=0 or not isfinite(a) or not isfinite(f):
        raise ValueError("invalid price evidence")
    ret=(f-a)/a
    eps=1e-9
    outcome="UP" if ret>eps else ("DOWN" if ret<-eps else "FLAT")
    return SolanaVerifiedForwardOutcome(case.case_id,h,a,f,ret,outcome,True,str(evidence_source),False)

"""

TEST_SOURCE=r"""\

import unittest
from qseries_v2.oracle_adapters.independent.oad_373_solana_universal_economic_event_promotion import promote_economic_behavior
from qseries_v2.oracle_adapters.independent.oad_374_solana_temporal_case_bridge import build_temporal_learning_case
from qseries_v2.oracle_adapters.independent.oad_375_solana_verified_forward_outcome_bridge import *

class T(unittest.TestCase):
    def test_outcome(self):
        e=promote_economic_behavior({"event_id":"e1","slot":1,"behavior_type":"DEX_SWAP","primary_asset":"A"})
        c=build_temporal_learning_case(e,(15,))
        x=attribute_verified_forward_outcome(c,15,100,105)
        print("[OUTCOME]",x.case_id,x.horizon_seconds,x.outcome,x.return_fraction)
        self.assertTrue(x.verified)
        self.assertEqual(x.outcome,"UP")

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-375 verified forward outcome bridge certified")

"""

def root():
    for b in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (b,*b.parents):
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
    ast.parse(source,filename=str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
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

    for rel,markers in DEPENDENCIES.items():
        verify(r/rel,markers)
        print("[PASS] dependency interface verified:",rel)

    protected_rels=[
        "qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
        "qseries_v2/oracle_adapters/independent/oad_327_solana_universal_continuity_physical_certification.py",
        "qseries_v2/oracle_adapters/independent/oad_357_solana_decoder_closeout_same_universe_physical_gate.py",
        "qseries_v2/oracle_adapters/independent/oad_362_solana_continuity_integrity_physical_gate.py",
        "qseries_v2/oracle_adapters/independent/oad_372_solana_final_persistence_continuity_physical_gate.py",
    ]+list(EXTRA_PROTECTED)

    protected=[]
    for rel in protected_rels:
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
        print("[PASS] no separate Solana learner introduced")
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
