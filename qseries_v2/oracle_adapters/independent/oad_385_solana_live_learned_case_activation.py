from __future__ import annotations
from dataclasses import dataclass
import json
from pathlib import Path

from .oad_274_solana_multi_horizon_condition_windows import read_pinned_pool_history
from .oad_313_solana_outcome_pending_temporal_cases import build_outcome_pending_solana_cases
from .oad_314_solana_verified_forward_outcome_attribution import attribute_forward_outcomes
from .oad_315_solana_verified_learned_case_contract import build_verified_solana_learned_cases
from .oad_316_solana_comparable_case_statistics import aggregate_comparable_solana_cases
from .oad_317_solana_existing_ocl_learning_handoff import build_solana_learning_handoff

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

MANIFEST_REL=Path("runtime_state")/"solana_learning_activation"/"oad_384_verified_outcomes.json"

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

def _load_manifest(root=None):
    r=Path(root or Path.cwd())
    p=r/MANIFEST_REL
    if not p.is_file():
        raise RuntimeError("Certified OAD-384 manifest missing: "+str(p))
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
        raise RuntimeError("OAD-384 manifest missing fields: "+",".join(missing))
    if int(data["verified_outcomes"]) <= 0:
        raise RuntimeError("OAD-384 manifest has zero verified outcomes")
    if int(data["forward_records_added"]) <= 0:
        raise RuntimeError("OAD-384 manifest has no forward evidence")
    return p,data

def build_live_learned_cases(root=None,tolerance_seconds=8.0):
    _,m=_load_manifest(root)

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
            f"Certified history incomplete for {token_address}: "
            f"expected >= {final_count}, found {len(history)}"
        )

    anchor_records=tuple(history[:anchor_count])
    final_records=tuple(history[:final_count])

    pending_cases=tuple(
        build_outcome_pending_solana_cases(
            anchor_records,
            (15,30,60),
        )
    )
    if not pending_cases:
        raise RuntimeError("OAD-313 produced zero pending cases")

    outcomes=tuple(
        attribute_forward_outcomes(
            pending_cases,
            final_records,
            tolerance_seconds,
        )
    )
    if not outcomes:
        raise RuntimeError("OAD-314 produced zero attributed outcomes")

    learned=tuple(
        build_verified_solana_learned_cases(
            pending_cases,
            outcomes,
        )
    )
    if not learned:
        raise RuntimeError("OAD-315 produced zero learned cases")

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
