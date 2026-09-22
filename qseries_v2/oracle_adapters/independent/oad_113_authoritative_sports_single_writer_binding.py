from __future__ import annotations

from .oad_066_independent_single_writer_ingress_binding import (
    submit_independent_canonical_batch,
    await_independent_commit,
    verify_oad_066_independent_single_writer_ingress_binding,
)
from .oad_112_authoritative_sports_canonical_batch_gate import AuthoritativeSportsCanonicalBatch

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

def submit_authoritative_sports_batch(batch: AuthoritativeSportsCanonicalBatch, root=None):
    if not isinstance(batch, AuthoritativeSportsCanonicalBatch):
        raise TypeError("AuthoritativeSportsCanonicalBatch required")
    if not batch.ready_for_existing_single_writer:
        raise RuntimeError("sports canonical batch is not ready for existing single writer")
    if batch.execution_authority is not False:
        raise RuntimeError("execution authority must remain false")
    return submit_independent_canonical_batch(batch.canonical_observations,root)

def await_authoritative_sports_commit(request_id, root=None, timeout_seconds=120.0):
    return await_independent_commit(request_id,root,timeout_seconds)

def verify_existing_single_writer_boundary():
    return (
        verify_oad_066_independent_single_writer_ingress_binding() is True
        and READ_ONLY
        and not EXECUTION_AUTHORITY
        and not PROBABILITY_ENABLED
    )
