from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

EXPECTED="build_oad_385_solana_live_learned_case_activation_CERTIFIED_HISTORY_REUSE_REBUILD.py"
MODULE="oad_385_solana_live_learned_case_activation.py"
TEST="test_oad_385_solana_live_learned_case_activation.py"

MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
import json
from pathlib import Path

from .oad_274_solana_multi_horizon_condition_windows import (
    read_pinned_pool_history,
)
from .oad_313_solana_outcome_pending_temporal_cases import (
    build_outcome_pending_solana_cases,
)
from .oad_314_solana_verified_forward_outcome_attribution import (
    attribute_forward_outcomes,
)
from .oad_315_solana_verified_learned_case_contract import (
    build_verified_solana_learned_cases,
)
from .oad_316_solana_comparable_case_statistics import (
    aggregate_comparable_solana_cases,
)
from .oad_317_solana_existing_ocl_learning_handoff import (
    build_solana_learning_handoff,
)

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

OAD384_MANIFEST=Path("runtime_state")/"solana_learning_activation"/"oad_384_verified_outcomes.json"

@dataclass(frozen=True, slots=True)
class SolanaLearnedCaseActivation:
    token_address:str
    anchor_history_records:int
    final_history_records:int
    pending_cases:int
    attributed_outcomes:int
    learned_cases:int
    handoff_type:str
    statistics_type:str
    execution_authority:bool=False

def _load_certified_oad384_manifest(root=None):
    r=Path(root or Path.cwd())
    p=r/OAD384_MANIFEST

    if not p.is_file():
        raise RuntimeError(
            "Certified OAD-384 manifest missing: "+str(p)
        )

    data=json.loads(p.read_text(encoding="utf-8"))

    required=(
        "token_address",
        "anchor_history_records",
        "forward_records_added",
        "final_history_records",
        "verified_outcomes",
    )

    missing=[k for k in required if k not in data]
    if missing:
        raise RuntimeError(
            "OAD-384 manifest missing required fields: "
            +",".join(missing)
        )

    if int(data["verified_outcomes"]) <= 0:
        raise RuntimeError(
            "OAD-384 manifest is not physically certified: verified_outcomes <= 0"
        )

    if int(data["forward_records_added"]) <= 0:
        raise RuntimeError(
            "OAD-384 manifest has no later forward evidence"
        )

    return p,data

def build_live_learned_cases(root=None,tolerance_seconds=8.0):
    manifest_path,m=_load_certified_oad384_manifest(root)

    token_address=str(m["token_address"])
    anchor_count=int(m["anchor_history_records"])
    final_count=int(m["final_history_records"])

    history=tuple(
        read_pinned_pool_history(
            token_address=token_address,
            root=root,
            limit=max(2048,final_count+64),
        )
    )

    if len(history) < final_count:
        raise RuntimeError(
            f"Certified OAD-384 history incomplete for token {token_address}: "
            f"expected at least {final_count}, found {len(history)}"
        )

    # Reconstruct the exact two-phase proof:
    # the first anchor_count records existed when pending cases were created;
    # the remaining records are later evidence only.
    anchor_records=tuple(history[:anchor_count])
    final_records=tuple(history[:final_count])

    pending_cases=tuple(
        build_outcome_pending_solana_cases(
            anchor_records,
            (15,30,60),
        )
    )

    if not pending_cases:
        raise RuntimeError(
            "OAD-313 produced zero pending cases from certified OAD-384 anchor history"
        )

    outcomes=tuple(
        attribute_forward_outcomes(
            pending_cases,
            final_records,
            tolerance_seconds,
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
            "OAD-315 produced zero learned cases from certified OAD-384 forward outcomes"
        )

    stats=aggregate_comparable_solana_cases(learned)
    handoff=build_solana_learning_handoff(learned)

    return (
        SolanaLearnedCaseActivation(
            token_address=token_address,
            anchor_history_records=len(anchor_records),
            final_history_records=len(final_records),
            pending_cases=len(pending_cases),
            attributed_outcomes=len(outcomes),
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

    def test_certified_history_reuse(self):
        x,learned,stats,handoff=build_live_learned_cases()

        print(
            "[LEARNED-CASES] token=",
            x.token_address,
            "anchor_history=",
            x.anchor_history_records,
            "final_history=",
            x.final_history_records,
        )

        print(
            "[LEARNED-CASES] pending=",
            x.pending_cases,
            "outcomes=",
            x.attributed_outcomes,
            "learned=",
            x.learned_cases,
        )

        print(
            "[LEARNED-CASES] stats=",
            x.statistics_type,
            "handoff=",
            x.handoff_type,
        )

        self.assertGreaterEqual(x.anchor_history_records,13)
        self.assertGreater(x.final_history_records,x.anchor_history_records)
        self.assertGreater(x.pending_cases,0)
        self.assertGreater(x.attributed_outcomes,0)
        self.assertGreater(x.learned_cases,0)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )

    if not r.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] OAD-385 certified OAD-384 history reused without reacquisition")
    print("[PASS] OAD-315 real learned cases physically built")
    print("[PASS] OAD-316 comparable-case statistics physically built")
    print("[PASS] OAD-317 existing learning handoff physically built")
    print("[PASS] no new live token selected")
    print("[PASS] no additional OPH-019 acquisition required")
"""

DEPS={
    "qseries_v2/oracle_adapters/independent/oad_274_solana_multi_horizon_condition_windows.py":(
        "read_pinned_pool_history",
    ),
    "qseries_v2/oracle_adapters/independent/oad_313_solana_outcome_pending_temporal_cases.py":(
        "build_outcome_pending_solana_cases",
    ),
    "qseries_v2/oracle_adapters/independent/oad_314_solana_verified_forward_outcome_attribution.py":(
        "attribute_forward_outcomes",
    ),
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
        "OAD384_MANIFEST",
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
    print(" OAD-385 SOLANA LIVE LEARNED CASE ACTIVATION - CERTIFIED HISTORY REUSE REBUILD INSTALLER")
    print("="*120)
    print("[ROOT]",r)

    for rel,marks in DEPS.items():
        verify(r/rel,marks)
        print("[PASS] dependency interface verified:",rel)

    manifest=r/"runtime_state"/"solana_learning_activation"/"oad_384_verified_outcomes.json"
    if not manifest.is_file():
        raise RuntimeError(
            "Required physically certified OAD-384 manifest missing: "+str(manifest)
        )

    data=__import__("json").loads(manifest.read_text(encoding="utf-8"))

    if int(data.get("verified_outcomes",0)) <= 0:
        raise RuntimeError(
            "OAD-384 manifest exists but has no verified outcomes"
        )

    print(
        "[PASS] certified OAD-384 manifest verified:",
        "token=",data.get("token_address"),
        "verified_outcomes=",data.get("verified_outcomes"),
    )

    protected=[]
    for rel in (
        "qseries_v2/oracle_adapters/independent/oad_274_solana_multi_horizon_condition_windows.py",
        "qseries_v2/oracle_adapters/independent/oad_313_solana_outcome_pending_temporal_cases.py",
        "qseries_v2/oracle_adapters/independent/oad_314_solana_verified_forward_outcome_attribution.py",
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

        print("[PASS] OAD-385 now consumes already-certified OAD-384 history")
        print("[PASS] redundant live reacquisition removed")
        print("[PASS] no new token selection")
        print("[PASS] no OPH-019 write required for this downstream stage")
        print("[PASS] OAD-315/OAD-316/OAD-317 preserved")
        print("[PASS] OAD-384 preserved")
        print("[PASS] frozen OCL-026 through OCL-030 preserved")
        print("[PASS] no fabricated outcome introduced")
        print("[PASS] no separate Solana learner introduced")
        print("[PASS] GMGN not required")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-385 CERTIFIED HISTORY REUSE REBUILD COMPLETE")

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
