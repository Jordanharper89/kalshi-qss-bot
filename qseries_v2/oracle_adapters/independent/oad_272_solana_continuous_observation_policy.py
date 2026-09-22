from __future__ import annotations
from dataclasses import dataclass

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SolanaContinuousObservationPolicy:
    tick_seconds:float
    acquisition_seconds:float
    history_limit:int
    windows_seconds:tuple
    acquisition_timeout_seconds:float
    persistence_timeout_seconds:float
    failure_backoff_base_seconds:float
    failure_backoff_max_seconds:float
    rotate_after_seconds:float
    execution_authority:bool=False

def build_solana_continuous_observation_policy(
    tick_seconds=1.0,
    acquisition_seconds=5.0,
    history_limit=512,
    windows_seconds=(5,15,30,60),
    acquisition_timeout_seconds=20.0,
    persistence_timeout_seconds=120.0,
    failure_backoff_base_seconds=2.0,
    failure_backoff_max_seconds=60.0,
    rotate_after_seconds=300.0,
):
    if tick_seconds <= 0: raise ValueError("tick_seconds must be > 0")
    if acquisition_seconds < tick_seconds:
        raise ValueError("acquisition_seconds must be >= tick_seconds")
    if history_limit < 2: raise ValueError("history_limit must be >= 2")
    windows=tuple(sorted({int(x) for x in windows_seconds}))
    if not windows or any(x <= 0 for x in windows):
        raise ValueError("windows_seconds must contain positive values")
    if acquisition_timeout_seconds <= 0 or persistence_timeout_seconds <= 0:
        raise ValueError("timeouts must be > 0")
    if failure_backoff_base_seconds <= 0 or failure_backoff_max_seconds < failure_backoff_base_seconds:
        raise ValueError("invalid backoff")
    if rotate_after_seconds < acquisition_seconds:
        raise ValueError("rotate_after_seconds must be >= acquisition_seconds")
    return SolanaContinuousObservationPolicy(
        float(tick_seconds),float(acquisition_seconds),int(history_limit),windows,
        float(acquisition_timeout_seconds),float(persistence_timeout_seconds),
        float(failure_backoff_base_seconds),float(failure_backoff_max_seconds),
        float(rotate_after_seconds),False
    )

def verify_solana_continuous_observation_policy(policy):
    return (
        isinstance(policy,SolanaContinuousObservationPolicy)
        and policy.tick_seconds>0
        and policy.acquisition_seconds>=policy.tick_seconds
        and policy.history_limit>=2
        and bool(policy.windows_seconds)
        and policy.execution_authority is False
    )
