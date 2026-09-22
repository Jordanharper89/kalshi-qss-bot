from __future__ import annotations
from dataclasses import dataclass
from uuid import uuid4

from .oad_110_authoritative_sports_canonical_bridge import canonicalize_authoritative_sports_observation
from .oad_062_independent_canonical_provenance_validation import validate_independent_canonical

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

@dataclass(frozen=True, slots=True)
class AuthoritativeSportsCanonicalBatch:
    canonical_observations: tuple
    provenance_validated: int
    ready_for_existing_single_writer: bool
    acquisition_batch_id: str
    execution_authority: bool=False

def build_authoritative_sports_canonical_batch(observations, acquisition_batch_id=None):
    items=tuple(observations)
    if not items:
        raise ValueError("non-empty authoritative sports observation batch required")
    batch_id=str(acquisition_batch_id or ("oad112-"+uuid4().hex))
    canonical=tuple(canonicalize_authoritative_sports_observation(x,batch_id) for x in items)
    validations=tuple(validate_independent_canonical(x) for x in canonical)
    valid=sum(1 for x in validations if x.valid)
    ready=bool(canonical) and valid==len(canonical)
    return AuthoritativeSportsCanonicalBatch(
        canonical_observations=canonical,
        provenance_validated=valid,
        ready_for_existing_single_writer=ready,
        acquisition_batch_id=batch_id,
        execution_authority=False,
    )
