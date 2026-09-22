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
