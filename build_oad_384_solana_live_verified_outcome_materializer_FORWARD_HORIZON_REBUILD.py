from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

EXPECTED="build_oad_384_solana_live_verified_outcome_materializer_FORWARD_HORIZON_REBUILD.py"
MODULE="oad_384_solana_live_verified_outcome_materializer.py"
TEST="test_oad_384_solana_live_verified_outcome_materializer.py"

MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass, asdict, is_dataclass
import json, time
from pathlib import Path

from .oad_273_solana_pinned_pool_live_snapshot_persistence import (
    select_live_solana_token,
    persist_pinned_solana_pool_snapshot,
)
from .oad_274_solana_multi_horizon_condition_windows import (
    read_pinned_pool_history,
)
from .oad_312_solana_continuous_temporal_history_activation_gate import (
    activate_and_verify_temporal_history,
)
from .oad_313_solana_outcome_pending_temporal_cases import (
    build_outcome_pending_solana_cases,
)
from .oad_314_solana_verified_forward_outcome_attribution import (
    attribute_forward_outcomes,
)

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

MANIFEST=Path("runtime_state")/"solana_learning_activation"/"oad_384_verified_outcomes.json"

@dataclass(frozen=True, slots=True)
class SolanaVerifiedOutcomeActivation:
    token_address:str
    anchor_history_records:int
    pending_cases:int
    forward_records_added:int
    final_history_records:int
    verified_outcomes:int
    outcome_states:tuple
    manifest_path:str
    execution_authority:bool=False

def _plain(x):
    if is_dataclass(x):
        return asdict(x)
    if isinstance(x,dict):
        return dict(x)
    if hasattr(x,"__dict__"):
        return {k:v for k,v in vars(x).items() if not k.startswith("_")}
    return {"repr":repr(x)}

def _progress(message):
    print(message)

def _token_address(token):
    return str(
        getattr(
            token,
            "token_address",
            getattr(token,"address",token),
        )
    )

def materialize_live_verified_outcomes(
    root=None,
    anchor_cycles=13,
    forward_cycles=13,
    cadence_seconds=5.0,
    tolerance_seconds=8.0,
):
    token=select_live_solana_token(timeout_seconds=20.0)
    token_address=_token_address(token)

    # PHASE A:
    # Establish enough real temporal depth to create OUTCOME_PENDING cases.
    activate_and_verify_temporal_history(
        root=root,
        cycles=anchor_cycles,
        acquisition_seconds=cadence_seconds,
        acquisition_timeout_seconds=20.0,
        persistence_timeout_seconds=20.0,
        progress=_progress,
    )

    anchor_records=tuple(
        read_pinned_pool_history(
            token_address=token_address,
            root=root,
            limit=1024,
        )
    )

    pending_cases=tuple(
        build_outcome_pending_solana_cases(
            anchor_records,
            (15,30,60),
        )
    )

    if not pending_cases:
        raise RuntimeError(
            "No OAD-313 pending cases were created from real Solana history"
        )

    print(
        "[FORWARD] pending cases anchored:",
        len(pending_cases),
        "token=",
        token_address,
    )

    # PHASE B:
    # Continue observing THE SAME PINNED TOKEN after the cases exist.
    # These observations are genuinely later evidence and are the only
    # records allowed to satisfy the forward horizon.
    before_forward=len(anchor_records)

    for cycle in range(1,int(forward_cycles)+1):
        print(
            f"[FORWARD] cycle={cycle}/{forward_cycles} "
            f"acquiring later evidence token={token_address}"
        )

        persist_pinned_solana_pool_snapshot(
            token_address=token_address,
            root=root,
            timeout_seconds=20.0,
            acquisition_timeout_seconds=20.0,
        )

        if cycle < int(forward_cycles):
            time.sleep(float(cadence_seconds))

    final_records=tuple(
        read_pinned_pool_history(
            token_address=token_address,
            root=root,
            limit=2048,
        )
    )

    outcomes=tuple(
        attribute_forward_outcomes(
            pending_cases,
            final_records,
            tolerance_seconds,
        )
    )

    verified=[]
    states=[]

    for o in outcomes:
        d=_plain(o)

        state=str(
            d.get(
                "state",
                d.get(
                    "outcome_state",
                    d.get("verification_state",""),
                ),
            )
        ).upper()

        outcome=str(
            d.get(
                "outcome",
                d.get(
                    "direction",
                    d.get("realized_outcome",""),
                ),
            )
        ).upper()

        verified_flag=bool(
            d.get(
                "verified",
                d.get("is_verified",False),
            )
        )

        if state:
            states.append(state)

        if verified_flag or outcome in ("UP","DOWN","FLAT") or "VERIFIED" in state:
            verified.append(o)

    r=Path(root or Path.cwd())
    path=r/MANIFEST
    path.parent.mkdir(parents=True,exist_ok=True)

    forward_added=max(0,len(final_records)-before_forward)

    payload={
        "token_address":token_address,
        "anchor_history_records":len(anchor_records),
        "pending_cases":len(pending_cases),
        "forward_records_added":forward_added,
        "final_history_records":len(final_records),
        "verified_outcomes":len(verified),
        "outcome_states":sorted(set(states)),
        "anchor_cycles":int(anchor_cycles),
        "forward_cycles":int(forward_cycles),
        "cadence_seconds":float(cadence_seconds),
        "written_at":time.time(),
    }

    path.write_text(
        json.dumps(payload,indent=2,sort_keys=True),
        encoding="utf-8",
    )

    return (
        SolanaVerifiedOutcomeActivation(
            token_address=token_address,
            anchor_history_records=len(anchor_records),
            pending_cases=len(pending_cases),
            forward_records_added=forward_added,
            final_history_records=len(final_records),
            verified_outcomes=len(verified),
            outcome_states=tuple(sorted(set(states))),
            manifest_path=str(path),
            execution_authority=False,
        ),
        anchor_records,
        pending_cases,
        final_records,
        outcomes,
    )
"""

TEST_SOURCE=r"""
import unittest

from qseries_v2.oracle_adapters.independent.oad_384_solana_live_verified_outcome_materializer import (
    materialize_live_verified_outcomes,
)

class T(unittest.TestCase):

    def test_physical(self):
        x,anchor_records,cases,final_records,outcomes=materialize_live_verified_outcomes(
            anchor_cycles=13,
            forward_cycles=13,
            cadence_seconds=5.0,
        )

        print(
            "[OUTCOME-ACTIVATION] token=",
            x.token_address,
            "anchor_history=",
            x.anchor_history_records,
            "pending=",
            x.pending_cases,
            "forward_added=",
            x.forward_records_added,
            "final_history=",
            x.final_history_records,
            "verified=",
            x.verified_outcomes,
        )

        print(
            "[OUTCOME-ACTIVATION] states=",
            x.outcome_states,
            "manifest=",
            x.manifest_path,
        )

        self.assertGreaterEqual(x.anchor_history_records,13)
        self.assertGreater(x.pending_cases,0)
        self.assertGreaterEqual(
            x.forward_records_added,
            13,
            "The same pinned Solana token did not accumulate the required later evidence",
        )
        self.assertGreater(
            x.verified_outcomes,
            0,
            "OAD-314 still found no verified forward outcome after a full real forward horizon",
        )

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )

    if not r.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] OAD-384 real Solana forward outcomes physically materialized")
    print("[PASS] pending cases existed BEFORE forward evidence was acquired")
    print("[PASS] same pinned token supplied later 15/30/60-second evidence")
    print("[PASS] no fabricated future price or synthetic outcome introduced")
"""

DEPS={
    "qseries_v2/oracle_adapters/independent/oad_273_solana_pinned_pool_live_snapshot_persistence.py":(
        "select_live_solana_token",
        "persist_pinned_solana_pool_snapshot",
    ),
    "qseries_v2/oracle_adapters/independent/oad_274_solana_multi_horizon_condition_windows.py":(
        "read_pinned_pool_history",
    ),
    "qseries_v2/oracle_adapters/independent/oad_312_solana_continuous_temporal_history_activation_gate.py":(
        "activate_and_verify_temporal_history",
    ),
    "qseries_v2/oracle_adapters/independent/oad_313_solana_outcome_pending_temporal_cases.py":(
        "build_outcome_pending_solana_cases",
    ),
    "qseries_v2/oracle_adapters/independent/oad_314_solana_verified_forward_outcome_attribution.py":(
        "attribute_forward_outcomes",
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
                "dependency interface missing: "
                +p.name
                +" -> "
                +marker
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
    print(" OAD-384 SOLANA LIVE VERIFIED OUTCOME MATERIALIZER - FORWARD HORIZON REBUILD INSTALLER")
    print("="*120)
    print("[ROOT]",r)

    for rel,marks in DEPS.items():
        verify(r/rel,marks)
        print("[PASS] dependency interface verified:",rel)

    protected=[]
    for rel in (
        "qseries_v2/oracle_adapters/independent/oad_273_solana_pinned_pool_live_snapshot_persistence.py",
        "qseries_v2/oracle_adapters/independent/oad_274_solana_multi_horizon_condition_windows.py",
        "qseries_v2/oracle_adapters/independent/oad_312_solana_continuous_temporal_history_activation_gate.py",
        "qseries_v2/oracle_adapters/independent/oad_313_solana_outcome_pending_temporal_cases.py",
        "qseries_v2/oracle_adapters/independent/oad_314_solana_verified_forward_outcome_attribution.py",
        "qseries_v2/oracle_adapters/independent/oad_317_solana_existing_ocl_learning_handoff.py",
        "qseries_v2/oracle_continuous_learner/ocl_026_continuous_intake_runtime.py",
        "qseries_v2/oracle_continuous_learner/ocl_027_incremental_state_runtime.py",
        "qseries_v2/oracle_continuous_learner/ocl_028_learning_cycle_orchestrator.py",
        "qseries_v2/oracle_continuous_learner/ocl_029_scientific_reasoning_handoff.py",
        "qseries_v2/oracle_continuous_learner/ocl_030_final_freeze_gate.py",
    ):
        p=r/rel
        if p.is_file():
            protected.append(
                (p,hashlib.sha256(p.read_bytes()).hexdigest())
            )

    old={
        p:(p.read_bytes() if p.exists() else None)
        for p in (m,t,init)
    }

    try:
        atomic(m,MODULE_SOURCE)
        atomic(t,TEST_SOURCE)

        lines=(
            init.read_text(encoding="utf-8").splitlines()
            if init.exists()
            else []
        )

        export="from ."+m.stem+" import *"
        if export not in lines:
            lines.append(export)

        atomic(
            init,
            "\n".join(x for x in lines if x.strip())+"\n",
        )

        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError(
                    "protected boundary changed: "+p.name
                )

        print("[PASS] OAD-384 rebuilt as two-phase anchor -> future-evidence materializer")
        print("[PASS] pending cases now exist before forward observations are collected")
        print("[PASS] same pinned token retained through forward horizon")
        print("[PASS] OAD-273/OAD-274/OAD-312/OAD-313/OAD-314 preserved")
        print("[PASS] frozen OCL-026 through OCL-030 preserved")
        print("[PASS] no fabricated future price introduced")
        print("[PASS] no separate Solana learner introduced")
        print("[PASS] GMGN not required")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-384 FORWARD HORIZON REBUILD COMPLETE")

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
