from __future__ import annotations
from dataclasses import dataclass

from .oad_216_crypto_scientific_reasoning_handoff_gate import (
    REQUIRED_NON_LEARNER_HASHES,
    evaluate_crypto_scientific_reasoning_handoff,
)
from .oad_217_certified_ocl_state_contract_resolution import (
    resolve_certified_ocl_contracts,
)
from .oad_220_scientific_reasoning_state_hash_registry import (
    REQUIRED_STATE_HASHES,
)
from qseries_v2.oracle_continuous_learner.ocl_029_scientific_reasoning_handoff import (
    verify_ocl_029_scientific_reasoning_handoff_contract,
)

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class AdmissionCertification:
    learner_state_hash:str
    learner_state_verified:bool
    certified_existing_contracts:tuple[str,...]
    unavailable_existing_contracts:tuple[str,...]
    required_non_learner_hashes:tuple[str,...]
    supplied_certified_state_hashes:tuple[str,...]
    missing_state_hashes:tuple[str,...]
    handoff_hash:str|None
    handoff_verified:bool
    state:str
    physical_ready:bool
    probability_enabled:bool=False
    direction_enabled:bool=False
    execution_authority:bool=False

def certify_crypto_scientific_reasoning_admission(certified_state_hashes=None):
    if not verify_ocl_029_scientific_reasoning_handoff_contract():
        raise RuntimeError("Frozen OCL-029 handoff contract failed verification")

    contracts=resolve_certified_ocl_contracts()

    supplied=dict(certified_state_hashes or {})
    accepted=tuple(
        name for name in REQUIRED_NON_LEARNER_HASHES
        if len(str(supplied.get(name,"")))==64
    )

    gate=evaluate_crypto_scientific_reasoning_handoff(
        certified_state_hashes=supplied
    )

    handoff_hash=(
        str(gate.handoff.handoff_hash)
        if gate.handoff is not None
        else None
    )

    return AdmissionCertification(
        learner_state_hash=gate.learner_state_hash,
        learner_state_verified=bool(gate.learner_state_verified),
        certified_existing_contracts=contracts.certified_contracts,
        unavailable_existing_contracts=contracts.unavailable_contracts,
        required_non_learner_hashes=tuple(REQUIRED_NON_LEARNER_HASHES),
        supplied_certified_state_hashes=accepted,
        missing_state_hashes=tuple(gate.missing_state_hashes),
        handoff_hash=handoff_hash,
        handoff_verified=bool(gate.handoff_verified),
        state=str(gate.state),
        physical_ready=bool(gate.physical_ready),
        probability_enabled=False,
        direction_enabled=False,
        execution_authority=False,
    )
