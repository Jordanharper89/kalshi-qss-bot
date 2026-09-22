from __future__ import annotations
from dataclasses import dataclass

from .oad_218_existing_ocl_state_hash_envelope import envelope

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
EXECUTION_AUTHORITY=False

REQUIRED_STATE_HASHES=(
    "calibration_state_hash",
    "source_reliability_state_hash",
    "market_behavior_state_hash",
    "causal_state_hash",
    "narrative_state_hash",
    "entity_relationship_state_hash",
    "maturity_state_hash",
    "adaptive_weight_state_hash",
)

CAPABILITY_BY_HASH={
    "calibration_state_hash":"calibration",
    "source_reliability_state_hash":"source_reliability",
    "market_behavior_state_hash":"market_behavior",
    "causal_state_hash":"causal",
    "narrative_state_hash":"narrative",
    "entity_relationship_state_hash":"entity_relationship",
    "maturity_state_hash":"maturity",
    "adaptive_weight_state_hash":"adaptive_weight",
}

@dataclass(frozen=True,slots=True)
class ScientificReasoningStateHashRegistry:
    hashes:dict
    missing:tuple[str,...]
    complete:bool
    fabricated:bool=False
    read_only:bool=True
    probability_enabled:bool=False
    direction_enabled:bool=False
    execution_authority:bool=False

def build_state_hash_registry(states):
    if states is None:
        states={}
    hashes={}
    for hash_name in REQUIRED_STATE_HASHES:
        capability=CAPABILITY_BY_HASH[hash_name]
        state=states.get(capability)
        if state is not None:
            hashes[hash_name]=envelope(capability,state).state_hash

    missing=tuple(
        name for name in REQUIRED_STATE_HASHES
        if name not in hashes
    )

    return ScientificReasoningStateHashRegistry(
        hashes=hashes,
        missing=missing,
        complete=(len(missing)==0),
        fabricated=False,
        read_only=True,
        probability_enabled=False,
        direction_enabled=False,
        execution_authority=False,
    )
