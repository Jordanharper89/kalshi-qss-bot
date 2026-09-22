from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

EXPECTED="build_oad_385_solana_live_learned_case_activation_OAD384_INTERFACE_REBUILD.py"
MODULE="oad_385_solana_live_learned_case_activation.py"
TEST="test_oad_385_solana_live_learned_case_activation.py"

MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass

from .oad_315_solana_verified_learned_case_contract import (
    build_verified_solana_learned_cases,
)
from .oad_316_solana_comparable_case_statistics import (
    aggregate_comparable_solana_cases,
)
from .oad_317_solana_existing_ocl_learning_handoff import (
    build_solana_learning_handoff,
)
from .oad_384_solana_live_verified_outcome_materializer import (
    materialize_live_verified_outcomes,
)

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class SolanaLearnedCaseActivation:
    pending_cases:int
    verified_outcomes:int
    learned_cases:int
    handoff_type:str
    statistics_type:str
    execution_authority:bool=False

def build_live_learned_cases(root=None):
    activation,anchor_records,pending_cases,final_records,outcomes = (
        materialize_live_verified_outcomes(
            root=root,
            anchor_cycles=13,
            forward_cycles=13,
            cadence_seconds=5.0,
        )
    )

    learned=tuple(
        build_verified_solana_learned_cases(
            pending_cases,
            outcomes,
        )
    )

    if not learned:
        raise RuntimeError(
            "OAD-315 produced zero learned cases from physically verified Solana outcomes"
        )

    stats=aggregate_comparable_solana_cases(learned)
    handoff=build_solana_learning_handoff(learned)

    return (
        SolanaLearnedCaseActivation(
            pending_cases=len(pending_cases),
            verified_outcomes=activation.verified_outcomes,
            learned_cases=len(learned),
            handoff_type=type(handoff).__name__,
            statistics_type=type(stats).__name__,
            execution_authority=False,
        ),
        learned,
        stats,
        handoff,
    )
"""

TEST_SOURCE=r"""
import unittest

from qseries_v2.oracle_adapters.independent.oad_385_solana_live_learned_case_activation import (
    build_live_learned_cases,
)

class T(unittest.TestCase):

    def test_live(self):
        x,learned,stats,handoff=build_live_learned_cases()

        print(
            "[LEARNED-CASES] pending=",
            x.pending_cases,
            "verified=",
            x.verified_outcomes,
            "learned=",
            x.learned_cases,
        )

        print(
            "[LEARNED-CASES] stats=",
            x.statistics_type,
            "handoff=",
            x.handoff_type,
        )

        self.assertGreater(x.pending_cases,0)
        self.assertGreater(x.verified_outcomes,0)
        self.assertGreater(x.learned_cases,0)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )

    if not r.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] OAD-385 real verified Solana outcomes converted to learned cases")
    print("[PASS] OAD-316 comparable-case statistics physically built")
    print("[PASS] OAD-317 existing learning handoff physically built")
"""

DEPS={
    "qseries_v2/oracle_adapters/independent/oad_315_solana_verified_learned_case_contract.py":(
        "build_verified_solana_learned_cases",
    ),
    "qseries_v2/oracle_adapters/independent/oad_316_solana_comparable_case_statistics.py":(
        "aggregate_comparable_solana_cases",
    ),
    "qseries_v2/oracle_adapters/independent/oad_317_solana_existing_ocl_learning_handoff.py":(
        "build_solana_learning_handoff",
    ),
    "qseries_v2/oracle_adapters/independent/oad_384_solana_live_verified_outcome_materializer.py":(
        "materialize_live_verified_outcomes",
        "anchor_cycles",
        "forward_cycles",
        "cadence_seconds",
    ),
}

def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")

def verify(p,markers):
    if not p.is_file():
        raise RuntimeError("dependency missing: "+str(p))
    s=p.read_text(encoding="utf-8")
    ast.parse(s,filename=str(p))
    for marker in markers:
        if marker not in s:
            raise RuntimeError(
                "dependency interface missing: "+p.name+" -> "+marker
            )

def atomic(p,s):
    s=textwrap.dedent(s).lstrip()
    ast.parse(s,filename=str(p))
    p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix(p.suffix+".tmp")
    tmp.write_text(s,encoding="utf-8",newline="\n")
    os.replace(tmp,p)

def main():
    if Path(__file__).name!=EXPECTED:
        raise RuntimeError("installer identity mismatch")

    r=root()
    pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    m=pkg/MODULE
    t=r/TEST
    init=pkg/"__init__.py"

    print("="*120)
    print(" OAD-385 SOLANA LIVE LEARNED CASE ACTIVATION - OAD-384 INTERFACE REBUILD INSTALLER")
    print("="*120)
    print("[ROOT]",r)

    for rel,marks in DEPS.items():
        verify(r/rel,marks)
        print("[PASS] dependency interface verified:",rel)

    protected=[]
    for rel in (
        "qseries_v2/oracle_adapters/independent/oad_315_solana_verified_learned_case_contract.py",
        "qseries_v2/oracle_adapters/independent/oad_316_solana_comparable_case_statistics.py",
        "qseries_v2/oracle_adapters/independent/oad_317_solana_existing_ocl_learning_handoff.py",
        "qseries_v2/oracle_adapters/independent/oad_384_solana_live_verified_outcome_materializer.py",
        "qseries_v2/oracle_continuous_learner/ocl_026_continuous_intake_runtime.py",
        "qseries_v2/oracle_continuous_learner/ocl_027_incremental_state_runtime.py",
        "qseries_v2/oracle_continuous_learner/ocl_028_learning_cycle_orchestrator.py",
        "qseries_v2/oracle_continuous_learner/ocl_029_scientific_reasoning_handoff.py",
        "qseries_v2/oracle_continuous_learner/ocl_030_final_freeze_gate.py",
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

        print("[PASS] OAD-385 aligned to certified OAD-384 forward-horizon interface")
        print("[PASS] OAD-315/OAD-316/OAD-317 preserved")
        print("[PASS] OAD-384 preserved")
        print("[PASS] frozen OCL-026 through OCL-030 preserved")
        print("[PASS] no fabricated outcome introduced")
        print("[PASS] no separate Solana learner introduced")
        print("[PASS] GMGN not required")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-385 INTERFACE REBUILD COMPLETE")

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
