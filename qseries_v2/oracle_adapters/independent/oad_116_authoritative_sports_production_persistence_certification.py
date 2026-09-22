from __future__ import annotations

from .oad_115_authoritative_sports_idempotent_persistence import persist_current_authoritative_sports

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

def run_authoritative_sports_production_certification(root=None, timeout_seconds=120.0, acquisition_timeout_seconds=20.0):
    r=persist_current_authoritative_sports(root,timeout_seconds,acquisition_timeout_seconds)
    if r.execution_authority is not False:
        raise RuntimeError("execution authority boundary violated")
    if r.cohort_size:
        if r.exact_readback!=r.cohort_size:
            raise RuntimeError("sports persistence certification readback mismatch")
        if r.already_present+r.missing_before_write!=r.cohort_size:
            raise RuntimeError("sports persistence accounting mismatch")
        if r.committed_new!=r.missing_before_write:
            raise RuntimeError("sports missing-only commit mismatch")
    return {
        "certified": True,
        "cohort_size": r.cohort_size,
        "already_present": r.already_present,
        "committed_new": r.committed_new,
        "exact_readback": r.exact_readback,
        "providers": r.providers,
        "read_only": True,
        "probability_enabled": False,
        "execution_authority": False,
    }
