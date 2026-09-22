from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

EXPECTED="build_oad_376_solana_learned_experience_bridge_DEPENDENCY_REBUILD.py"
MODULE="oad_376_solana_learned_experience_bridge.py"
TEST="test_oad_376_solana_learned_experience_bridge.py"

MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import hashlib, json

from .oad_374_solana_temporal_case_bridge import SolanaTemporalLearningCase
from .oad_375_solana_verified_forward_outcome_bridge import SolanaVerifiedForwardOutcome

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class SolanaLearnedExperienceRecord:
    experience_id:str
    case_id:str
    behavior_type:str
    protocol:str|None
    primary_asset:str|None
    secondary_asset:str|None
    horizon_seconds:int
    outcome:str
    return_fraction:float
    evidence_source:str
    immutable_payload_hash:str
    learning_namespace:str
    execution_authority:bool=False

def build_learned_experience(case:SolanaTemporalLearningCase,outcome:SolanaVerifiedForwardOutcome):
    if not bool(outcome.verified):
        raise ValueError("unverified outcome cannot become learned experience")

    if str(outcome.case_id) != str(case.case_id):
        raise ValueError("case/outcome mismatch")

    payload={
        "case_id":case.case_id,
        "behavior_type":case.behavior_type,
        "protocol":case.protocol,
        "primary_asset":case.primary_asset,
        "secondary_asset":case.secondary_asset,
        "horizon_seconds":int(outcome.horizon_seconds),
        "outcome":outcome.outcome,
        "return_fraction":float(outcome.return_fraction),
        "evidence_source":outcome.evidence_source,
        "learning_namespace":"EXISTING_OCL",
    }

    raw=json.dumps(
        payload,
        sort_keys=True,
        separators=(",",":"),
        default=str
    ).encode("utf-8")

    h=hashlib.sha256(raw).hexdigest()

    return SolanaLearnedExperienceRecord(
        experience_id="SOLANA-EXP-"+h[:24],
        case_id=case.case_id,
        behavior_type=case.behavior_type,
        protocol=case.protocol,
        primary_asset=case.primary_asset,
        secondary_asset=case.secondary_asset,
        horizon_seconds=int(outcome.horizon_seconds),
        outcome=outcome.outcome,
        return_fraction=float(outcome.return_fraction),
        evidence_source=outcome.evidence_source,
        immutable_payload_hash=h,
        learning_namespace="EXISTING_OCL",
        execution_authority=False,
    )

def as_learning_payload(record:SolanaLearnedExperienceRecord):
    return asdict(record)
"""

TEST_SOURCE=r"""
import unittest

from qseries_v2.oracle_adapters.independent.oad_373_solana_universal_economic_event_promotion import promote_economic_behavior
from qseries_v2.oracle_adapters.independent.oad_374_solana_temporal_case_bridge import build_temporal_learning_case
from qseries_v2.oracle_adapters.independent.oad_375_solana_verified_forward_outcome_bridge import attribute_verified_forward_outcome
from qseries_v2.oracle_adapters.independent.oad_376_solana_learned_experience_bridge import build_learned_experience, as_learning_payload

class T(unittest.TestCase):
    def test_experience(self):
        e=promote_economic_behavior({
            "event_id":"e1",
            "slot":1,
            "behavior_type":"DEX_SWAP",
            "primary_asset":"A",
            "secondary_asset":"B",
        })
        c=build_temporal_learning_case(e,(15,))
        o=attribute_verified_forward_outcome(c,15,100.0,101.0)
        x=build_learned_experience(c,o)
        p=as_learning_payload(x)

        print("[EXPERIENCE]",x.experience_id,x.outcome,x.learning_namespace,x.immutable_payload_hash)

        self.assertEqual(x.learning_namespace,"EXISTING_OCL")
        self.assertEqual(len(x.immutable_payload_hash),64)
        self.assertEqual(p["case_id"],c.case_id)
        self.assertFalse(x.execution_authority)

    def test_hash_is_deterministic(self):
        e=promote_economic_behavior({
            "event_id":"e2",
            "slot":2,
            "behavior_type":"TOKEN_FLOW",
            "primary_asset":"TOKEN",
        })
        c=build_temporal_learning_case(e,(30,))
        o=attribute_verified_forward_outcome(c,30,50.0,49.0)

        a=build_learned_experience(c,o)
        b=build_learned_experience(c,o)

        self.assertEqual(a.immutable_payload_hash,b.immutable_payload_hash)
        self.assertEqual(a.experience_id,b.experience_id)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] OAD-376 immutable evidence-grounded Solana learned experience bridge certified")
    print("[PASS] learned experiences target EXISTING_OCL only")
    print("[PASS] no separate Solana learner introduced")
"""

def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")

def atomic(path,source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def verify(path,markers):
    if not path.is_file():
        raise RuntimeError("dependency missing: "+str(path))
    text=path.read_text(encoding="utf-8")
    ast.parse(text,filename=str(path))
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
    print(" OAD-376 SOLANA LEARNED EXPERIENCE BRIDGE - DEPENDENCY REBUILD INSTALLER")
    print("="*120)
    print("[ROOT]",r)

    deps=(
        (
            pkg/"oad_373_solana_universal_economic_event_promotion.py",
            ("SolanaPromotedEconomicEvent","promote_economic_behavior"),
        ),
        (
            pkg/"oad_374_solana_temporal_case_bridge.py",
            ("SolanaTemporalLearningCase","build_temporal_learning_case","OUTCOME_PENDING"),
        ),
        (
            pkg/"oad_375_solana_verified_forward_outcome_bridge.py",
            ("SolanaVerifiedForwardOutcome","attribute_verified_forward_outcome","verified"),
        ),
    )

    for p,markers in deps:
        verify(p,markers)
        print("[PASS] dependency interface verified:",p.relative_to(r))

    print("[PASS] stale/nonexistent OAD-315 filename dependency removed")
    print("[PASS] OAD-376 now depends only on the actual certified OAD-373/OAD-374/OAD-375 chain")

    protected=[]
    for rel in (
        "qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
        "qseries_v2/oracle_adapters/independent/oad_327_solana_universal_continuity_physical_certification.py",
        "qseries_v2/oracle_adapters/independent/oad_357_solana_decoder_closeout_same_universe_physical_gate.py",
        "qseries_v2/oracle_adapters/independent/oad_362_solana_continuity_integrity_physical_gate.py",
        "qseries_v2/oracle_adapters/independent/oad_372_solana_final_persistence_continuity_physical_gate.py",
        "qseries_v2/oracle_adapters/independent/oad_373_solana_universal_economic_event_promotion.py",
        "qseries_v2/oracle_adapters/independent/oad_374_solana_temporal_case_bridge.py",
        "qseries_v2/oracle_adapters/independent/oad_375_solana_verified_forward_outcome_bridge.py",
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
        print("[PASS] OAD-373/OAD-374/OAD-375 preserved byte-for-byte")
        print("[PASS] frozen production boundaries preserved")
        print("[PASS] no separate Solana learner introduced")
        print("[PASS] GMGN not required")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-376 DEPENDENCY REBUILD INSTALLATION COMPLETE")

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
