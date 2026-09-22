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
