from __future__ import annotations

from .oad_068_exact_postgresql_independent_readback import (
    _backend as _existing_backend,
    _query_one as _existing_query_one,
    exact_postgresql_readback as _existing_exact_readback,
)

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

def find_authoritative_sports_observation(observation_id, root=None, index=0):
    backend=_existing_backend(root)
    return _existing_query_one(backend,str(observation_id),int(index))

def exact_authoritative_sports_readback(observation_ids, root=None):
    return _existing_exact_readback(tuple(str(x) for x in observation_ids),root)
