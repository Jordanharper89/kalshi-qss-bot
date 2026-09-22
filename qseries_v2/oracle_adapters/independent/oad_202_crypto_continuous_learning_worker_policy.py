from __future__ import annotations
from dataclasses import dataclass

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class CryptoContinuousLearningWorkerPolicy:
    cadence_seconds:float
    horizon_seconds:int
    acquisition_timeout_seconds:float
    persistence_timeout_seconds:float
    failure_backoff_base_seconds:float
    failure_backoff_multiplier:float
    failure_backoff_max_seconds:float
    max_consecutive_failures_before_degraded:int
    execution_authority:bool=False

def build_crypto_continuous_learning_worker_policy(
    cadence_seconds:float=60.0,
    horizon_seconds:int=60,
    acquisition_timeout_seconds:float=20.0,
    persistence_timeout_seconds:float=120.0,
    failure_backoff_base_seconds:float=2.0,
    failure_backoff_multiplier:float=2.0,
    failure_backoff_max_seconds:float=60.0,
    max_consecutive_failures_before_degraded:int=3,
):
    c=float(cadence_seconds); h=int(horizon_seconds)
    aq=float(acquisition_timeout_seconds); ps=float(persistence_timeout_seconds)
    b=float(failure_backoff_base_seconds); m=float(failure_backoff_multiplier); mx=float(failure_backoff_max_seconds)
    f=int(max_consecutive_failures_before_degraded)
    if c<=0 or h<=0 or aq<=0 or ps<=0 or b<=0 or m<1 or mx<b or f<1:
        raise ValueError("invalid continuous-learning worker policy")
    return CryptoContinuousLearningWorkerPolicy(c,h,aq,ps,b,m,mx,f,False)

def failure_backoff_seconds(policy,consecutive_failures:int):
    n=max(0,int(consecutive_failures))
    if n<=0: return 0.0
    return min(policy.failure_backoff_max_seconds,
               policy.failure_backoff_base_seconds*(policy.failure_backoff_multiplier**(n-1)))
