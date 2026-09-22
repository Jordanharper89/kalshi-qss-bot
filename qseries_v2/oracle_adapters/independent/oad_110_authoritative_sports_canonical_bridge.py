from __future__ import annotations

from qseries_v2.oracle_adapters.independent.oad_061_independent_to_canonical_bridge import (
    canonicalize_independent_observation,
)

READ_ONLY = True
EXECUTION_AUTHORITY = False
PROBABILITY_ENABLED = False

def canonicalize_authoritative_sports_observation(observation, acquisition_batch_id):
    if getattr(observation, "source_class", None) != "authoritative_real_world":
        raise ValueError("authoritative_real_world source required")
    if getattr(observation, "independent_evidence", None) is not True:
        raise ValueError("independent evidence required")
    if getattr(observation, "execution_authority", None) is not False:
        raise ValueError("execution authority must remain false")
    return canonicalize_independent_observation(observation, acquisition_batch_id)

def bridge_contract_record():
    return {
        "module": "qseries_v2.oracle_adapters.independent.oad_061_independent_to_canonical_bridge",
        "callable": "canonicalize_independent_observation",
        "read_only": True,
        "execution_authority": False,
        "probability_enabled": False,
    }
