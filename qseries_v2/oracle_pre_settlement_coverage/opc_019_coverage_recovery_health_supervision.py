
from __future__ import annotations
from dataclasses import dataclass
import socket, ssl, urllib.error

@dataclass(frozen=True)
class CoverageHealth:
    health:str
    restart_recommended:bool
    reason:str
    consecutive_failures:int
    execution_authority:bool=False

def is_transient_coverage_exception(exc):
    return isinstance(
        exc,
        (
            TimeoutError,
            ConnectionError,
            socket.timeout,
            ssl.SSLError,
            urllib.error.URLError,
        ),
    )

def evaluate_coverage_health(state,max_consecutive_failures=3):
    failures=int(getattr(state,"consecutive_failures",0))
    status=str(getattr(state,"last_cycle_status","NEVER_RUN"))
    if failures>=int(max_consecutive_failures):
        return CoverageHealth("DEGRADED",True,"CONSECUTIVE_FAILURE_THRESHOLD",failures,False)
    if status in ("SUCCESS","NEVER_RUN"):
        return CoverageHealth("HEALTHY",False,status,failures,False)
    return CoverageHealth("OBSERVE",False,status,failures,False)

def bounded_retry_delays(attempts=3,base_seconds=1.0,max_seconds=30.0):
    attempts=int(attempts)
    return tuple(min(float(max_seconds),float(base_seconds)*(2**i)) for i in range(attempts))

def verify_opc_019_coverage_recovery_health_supervision():
    class S:
        consecutive_failures=3
        last_cycle_status="FAILED"
    h=evaluate_coverage_health(S(),3)
    return h.health=="DEGRADED" and h.restart_recommended and is_transient_coverage_exception(TimeoutError())
