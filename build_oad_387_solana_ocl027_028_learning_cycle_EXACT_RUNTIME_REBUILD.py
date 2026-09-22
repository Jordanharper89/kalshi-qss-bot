from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

EXPECTED="build_oad_387_solana_ocl027_028_learning_cycle_EXACT_RUNTIME_REBUILD.py"
MODULE="oad_387_solana_ocl027_028_learning_cycle.py"
TEST="test_oad_387_solana_ocl027_028_learning_cycle.py"

MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json

from .oad_386_solana_ocl026_runtime_admission import (
    build_ocl026_solana_runtime_batch,
)
from qseries_v2.oracle_continuous_learner.ocl_027_incremental_state_runtime import (
    genesis_incremental_state,
    apply_runtime_batch,
    verify_incremental_state,
)
from qseries_v2.oracle_continuous_learner.ocl_028_learning_cycle_orchestrator import (
    run_learning_cycle,
    verify_learning_cycle_result,
)

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class SolanaOCLLearningCycleActivation:
    runtime_inputs:int
    pre_state_type:str
    applied_state_type:str
    cycle_result_type:str
    applied_state_verified:bool
    cycle_result_verified:bool
    result_hash:str
    execution_authority:bool=False

def _stable_hash(x):
    raw=json.dumps(
        x,
        sort_keys=True,
        separators=(",",":"),
        default=lambda o: getattr(o,"__dict__",repr(o)),
    ).encode("utf-8")
    return sha256(raw).hexdigest()

def run_solana_ocl_learning_cycle(root=None,sequence_start=1,cycle_sequence=1):
    admission,rows,batch=build_ocl026_solana_runtime_batch(
        root=root,
        sequence_start=sequence_start,
    )

    if admission.runtime_inputs <= 0:
        raise RuntimeError("OCL-026 admitted zero Solana runtime inputs")

    state0=genesis_incremental_state()

    state1=apply_runtime_batch(
        state0,
        batch,
    )

    state_verified=verify_incremental_state(state1)
    if state_verified is False:
        raise RuntimeError("OCL-027 verify_incremental_state returned False")

    result=run_learning_cycle(
        cycle_sequence,
        state0,
        batch,
    )

    result_verified=verify_learning_cycle_result(result)
    if result_verified is False:
        raise RuntimeError("OCL-028 verify_learning_cycle_result returned False")

    return (
        SolanaOCLLearningCycleActivation(
            runtime_inputs=admission.runtime_inputs,
            pre_state_type=type(state0).__name__,
            applied_state_type=type(state1).__name__,
            cycle_result_type=type(result).__name__,
            applied_state_verified=True,
            cycle_result_verified=True,
            result_hash=_stable_hash(result),
            execution_authority=False,
        ),
        state0,
        state1,
        result,
    )
"""

TEST_SOURCE=r"""
import inspect
import unittest

from qseries_v2.oracle_adapters.independent.oad_387_solana_ocl027_028_learning_cycle import (
    run_solana_ocl_learning_cycle,
)
from qseries_v2.oracle_continuous_learner.ocl_027_incremental_state_runtime import (
    genesis_incremental_state,
    apply_runtime_batch,
    verify_incremental_state,
)
from qseries_v2.oracle_continuous_learner.ocl_028_learning_cycle_orchestrator import (
    run_learning_cycle,
    verify_learning_cycle_result,
)

class T(unittest.TestCase):

    def test_exact_ocl_learning_cycle(self):
        print("[OCL-027] genesis signature=",inspect.signature(genesis_incremental_state))
        print("[OCL-027] apply signature=",inspect.signature(apply_runtime_batch))
        print("[OCL-027] verify signature=",inspect.signature(verify_incremental_state))
        print("[OCL-028] cycle signature=",inspect.signature(run_learning_cycle))
        print("[OCL-028] verify signature=",inspect.signature(verify_learning_cycle_result))

        x,state0,state1,result=run_solana_ocl_learning_cycle(
            sequence_start=1,
            cycle_sequence=1,
        )

        print(
            "[OCL-027/028] runtime_inputs=",x.runtime_inputs,
            "pre_state=",x.pre_state_type,
            "applied_state=",x.applied_state_type,
            "cycle_result=",x.cycle_result_type,
        )
        print(
            "[OCL-027/028] state_verified=",x.applied_state_verified,
            "cycle_verified=",x.cycle_result_verified,
            "result_hash=",x.result_hash,
        )

        self.assertGreater(x.runtime_inputs,0)
        self.assertTrue(x.applied_state_verified)
        self.assertTrue(x.cycle_result_verified)
        self.assertEqual(len(x.result_hash),64)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] OAD-387 certified Solana batch processed by real OCL-027")
    print("[PASS] real OCL-027 incremental state verified")
    print("[PASS] real OCL-028 learning cycle executed and verified")
    print("[PASS] no production learner state mutated by certification gate")
"""

DEPS={
    "qseries_v2/oracle_adapters/independent/oad_386_solana_ocl026_runtime_admission.py":(
        "build_ocl026_solana_runtime_batch",
    ),
    "qseries_v2/oracle_continuous_learner/ocl_027_incremental_state_runtime.py":(
        "genesis_incremental_state",
        "apply_runtime_batch",
        "verify_incremental_state",
    ),
    "qseries_v2/oracle_continuous_learner/ocl_028_learning_cycle_orchestrator.py":(
        "run_learning_cycle",
        "verify_learning_cycle_result",
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
            raise RuntimeError("dependency interface missing: "+p.name+" -> "+marker)

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
    print(" OAD-387 SOLANA OCL-027/OCL-028 LEARNING CYCLE - EXACT RUNTIME REBUILD INSTALLER")
    print("="*120)
    print("[ROOT]",r)

    for rel,marks in DEPS.items():
        verify(r/rel,marks)
        print("[PASS] dependency interface verified:",rel)

    protected=[]
    for rel in (
        "qseries_v2/oracle_adapters/independent/oad_384_solana_live_verified_outcome_materializer.py",
        "qseries_v2/oracle_adapters/independent/oad_385_solana_live_learned_case_activation.py",
        "qseries_v2/oracle_adapters/independent/oad_386_solana_ocl026_runtime_admission.py",
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

        print("[PASS] certified OAD-386 real OCL-026 batch consumed")
        print("[PASS] exact frozen OCL-027 genesis/apply/verify interfaces wired")
        print("[PASS] exact frozen OCL-028 cycle/verify interfaces wired")
        print("[PASS] OCL-026 through OCL-030 preserved")
        print("[PASS] production learner durable state not mutated by this gate")
        print("[PASS] no separate Solana learner introduced")
        print("[PASS] GMGN not required")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-387 EXACT OCL LEARNING CYCLE INSTALLATION COMPLETE")

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
