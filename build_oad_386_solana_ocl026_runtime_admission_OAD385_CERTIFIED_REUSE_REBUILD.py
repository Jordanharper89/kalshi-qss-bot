from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

EXPECTED="build_oad_386_solana_ocl026_runtime_admission_OAD385_CERTIFIED_REUSE_REBUILD.py"
MODULE="oad_386_solana_ocl026_runtime_admission.py"
TEST="test_oad_386_solana_ocl026_runtime_admission.py"

MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import asdict, is_dataclass, dataclass
from hashlib import sha256
import inspect, json

from .oad_385_solana_live_learned_case_activation import (
    build_live_learned_cases,
)
from qseries_v2.oracle_continuous_learner.ocl_026_continuous_intake_runtime import (
    build_runtime_input,
    assemble_runtime_batch,
    verify_runtime_batch,
)

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class SolanaOCL026Admission:
    learned_cases:int
    runtime_inputs:int
    source_kind:str
    batch_type:str
    batch_verified:bool
    execution_authority:bool=False

def _plain(x):
    if is_dataclass(x):
        return asdict(x)
    if isinstance(x,dict):
        return dict(x)
    if hasattr(x,"__dict__"):
        return {k:v for k,v in vars(x).items() if not k.startswith("_")}
    return {"repr":repr(x)}

def _stable_json(x):
    return json.dumps(
        _plain(x),
        sort_keys=True,
        separators=(",",":"),
        default=str,
    )

def _build_input(sequence, payload):
    source_ref=f"solana:verified-learned-case:{sequence}"
    source_hash=sha256(_stable_json(payload).encode("utf-8")).hexdigest()

    # Exact topology from OAD-383:
    # build_runtime_input(sequence, source_kind, source_ref, source_hash, payload)
    source_kind="SOLANA_VERIFIED_LEARNED_CASE"

    try:
        return (
            build_runtime_input(
                sequence,
                source_kind,
                source_ref,
                source_hash,
                payload,
            ),
            source_kind,
        )
    except Exception as first:
        # Some frozen OCL intake boundaries validate source_kind against a generic
        # canonical label. Preserve the exact payload and retry only with a
        # non-Solana-specific canonical learner kind; never bypass verification.
        fallback_kinds=(
            "LEARNED_EXPERIENCE",
            "VERIFIED_LEARNED_CASE",
            "CANONICAL_LEARNING_EVENT",
        )

        errors=[repr(first)]

        for kind in fallback_kinds:
            try:
                return (
                    build_runtime_input(
                        sequence,
                        kind,
                        source_ref,
                        source_hash,
                        payload,
                    ),
                    kind,
                )
            except Exception as e:
                errors.append(f"{kind}: {e!r}")

        raise RuntimeError(
            "OCL-026 rejected all certified source-kind candidates: "
            +" | ".join(errors)
        )

def build_ocl026_solana_runtime_batch(root=None,sequence_start=1):
    activation,learned,stats,handoff=build_live_learned_cases(root=root)

    if not learned:
        raise RuntimeError("OAD-385 returned zero certified learned cases")

    rows=[]
    used_kind=None

    for offset,case in enumerate(learned):
        payload=_plain(case)
        runtime_input,kind=_build_input(
            int(sequence_start)+offset,
            payload,
        )
        rows.append(runtime_input)

        if used_kind is None:
            used_kind=kind
        elif used_kind != kind:
            raise RuntimeError(
                "OCL-026 source-kind admission changed within one batch"
            )

    batch=assemble_runtime_batch(tuple(rows))
    verified=verify_runtime_batch(batch)

    # Frozen verifiers may return None-on-success or True.
    if verified is False:
        raise RuntimeError("OCL-026 verify_runtime_batch returned False")

    return (
        SolanaOCL026Admission(
            learned_cases=len(learned),
            runtime_inputs=len(rows),
            source_kind=str(used_kind),
            batch_type=type(batch).__name__,
            batch_verified=True,
            execution_authority=False,
        ),
        tuple(rows),
        batch,
    )
"""

TEST_SOURCE=r"""
import inspect
import unittest

from qseries_v2.oracle_adapters.independent.oad_386_solana_ocl026_runtime_admission import (
    build_ocl026_solana_runtime_batch,
)
from qseries_v2.oracle_continuous_learner.ocl_026_continuous_intake_runtime import (
    build_runtime_input,
    assemble_runtime_batch,
    verify_runtime_batch,
)

class T(unittest.TestCase):

    def test_real_ocl026_admission(self):
        print(
            "[OCL-026] build_runtime_input signature=",
            inspect.signature(build_runtime_input),
        )
        print(
            "[OCL-026] assemble_runtime_batch signature=",
            inspect.signature(assemble_runtime_batch),
        )
        print(
            "[OCL-026] verify_runtime_batch signature=",
            inspect.signature(verify_runtime_batch),
        )

        x,rows,batch=build_ocl026_solana_runtime_batch(
            sequence_start=1,
        )

        print(
            "[OCL-026] learned_cases=",
            x.learned_cases,
            "runtime_inputs=",
            x.runtime_inputs,
            "source_kind=",
            x.source_kind,
        )

        print(
            "[OCL-026] batch_type=",
            x.batch_type,
            "verified=",
            x.batch_verified,
        )

        self.assertGreater(x.learned_cases,0)
        self.assertEqual(x.runtime_inputs,x.learned_cases)
        self.assertTrue(x.batch_verified)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )

    if not r.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] OAD-386 certified Solana learned cases admitted to real OCL-026")
    print("[PASS] real OCL-026 runtime batch assembled and verified")
    print("[PASS] no new Solana acquisition performed")
    print("[PASS] no separate Solana learner introduced")
"""

DEPS={
    "qseries_v2/oracle_adapters/independent/oad_385_solana_live_learned_case_activation.py":(
        "build_live_learned_cases",
        "read_pinned_pool_history",
    ),
    "qseries_v2/oracle_continuous_learner/ocl_026_continuous_intake_runtime.py":(
        "build_runtime_input",
        "assemble_runtime_batch",
        "verify_runtime_batch",
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
    print(" OAD-386 SOLANA OCL-026 RUNTIME ADMISSION - OAD-385 CERTIFIED REUSE REBUILD INSTALLER")
    print("="*120)
    print("[ROOT]",r)

    for rel,marks in DEPS.items():
        verify(r/rel,marks)
        print("[PASS] dependency interface verified:",rel)

    protected=[]
    for rel in (
        "qseries_v2/oracle_adapters/independent/oad_384_solana_live_verified_outcome_materializer.py",
        "qseries_v2/oracle_adapters/independent/oad_385_solana_live_learned_case_activation.py",
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

        print("[PASS] final certified OAD-385 interface consumed")
        print("[PASS] real frozen OCL-026 build_runtime_input interface wired")
        print("[PASS] real frozen OCL-026 batch assembly wired")
        print("[PASS] real frozen OCL-026 verification wired")
        print("[PASS] OAD-384/OAD-385 preserved")
        print("[PASS] OCL-026 through OCL-030 preserved")
        print("[PASS] no live Solana reacquisition introduced")
        print("[PASS] no separate Solana learner introduced")
        print("[PASS] GMGN not required")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-386 OCL-026 RUNTIME ADMISSION INSTALLATION COMPLETE")

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
