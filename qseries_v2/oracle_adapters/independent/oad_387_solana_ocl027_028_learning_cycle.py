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

_RESULT_FIELDS=(
    "cycle_sequence",
    "input_batch_hash",
    "prior_state_hash",
    "new_state_hash",
    "processed_through_sequence",
)

@dataclass(frozen=True, slots=True)
class SolanaOCLLearningCycleActivation:
    runtime_inputs:int
    pre_state_type:str
    applied_state_type:str
    raw_cycle_return_type:str
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

def _is_learning_cycle_result(x):
    return all(hasattr(x,name) for name in _RESULT_FIELDS)

def _extract_learning_cycle_result(raw):
    if _is_learning_cycle_result(raw):
        return raw

    if isinstance(raw,(tuple,list)):
        matches=[x for x in raw if _is_learning_cycle_result(x)]
        if len(matches)==1:
            return matches[0]
        if len(matches)>1:
            raise RuntimeError(
                "OCL-028 returned multiple LearningCycleResult-like objects"
            )

    raise RuntimeError(
        "Unable to locate OCL-028 LearningCycleResult in return shape: "
        +type(raw).__name__
    )

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

    raw_result=run_learning_cycle(
        cycle_sequence,
        state0,
        batch,
    )

    result=_extract_learning_cycle_result(raw_result)

    result_verified=verify_learning_cycle_result(result)
    if result_verified is False:
        raise RuntimeError("OCL-028 verify_learning_cycle_result returned False")

    return (
        SolanaOCLLearningCycleActivation(
            runtime_inputs=admission.runtime_inputs,
            pre_state_type=type(state0).__name__,
            applied_state_type=type(state1).__name__,
            raw_cycle_return_type=type(raw_result).__name__,
            cycle_result_type=type(result).__name__,
            applied_state_verified=True,
            cycle_result_verified=True,
            result_hash=_stable_hash(result),
            execution_authority=False,
        ),
        state0,
        state1,
        raw_result,
        result,
    )
