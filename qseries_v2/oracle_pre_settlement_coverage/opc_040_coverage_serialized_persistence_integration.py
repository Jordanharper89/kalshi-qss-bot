from __future__ import annotations
from pathlib import Path
import time

from .opc_037_canonical_writer_arbiter_foundation import writer_policy
from .opc_038_atomic_cross_process_writer_lease import (
    acquire_canonical_writer_lease,
)
from .opc_039_fast_lane_serialized_admission import (
    RetryableTerminalChainMismatch,
    _install_retryable_mismatch_validator,
)

OPC_040_BUILD_ID="OPC-040"
OPC_040_REVISION="OPC_040_COVERAGE_SERIALIZED_PERSISTENCE_INTEGRATION_V1"

COVERAGE_SERIAL_MICROBATCH=25

def install_coverage_serialized_persistence(root=None):
    from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_router import (
        OraclePostgreSQLCanonicalObservationPersistenceRouter,
    )

    cls=OraclePostgreSQLCanonicalObservationPersistenceRouter
    marker="_opc040_coverage_serialized"

    if getattr(cls,marker,False):
        return False

    _install_retryable_mismatch_validator(cls)

    original=cls.route_batch
    root=Path(root or Path.cwd()).resolve()
    policy=writer_policy("COVERAGE")

    def serialized_route(self,observations,routed_at,*args,**kwargs):
        items=tuple(observations)

        if not items:
            return original(
                self,
                items,
                routed_at,
                *args,
                **kwargs,
            )

        all_evidence=[]

        for start in range(0,len(items),COVERAGE_SERIAL_MICROBATCH):
            chunk=items[
                start:start+COVERAGE_SERIAL_MICROBATCH
            ]
            attempt=0

            while True:
                try:
                    with acquire_canonical_writer_lease(
                        "COVERAGE",
                        root=root,
                        timeout_seconds=policy.lease_timeout_seconds,
                    ):
                        result=original(
                            self,
                            chunk,
                            routed_at,
                            *args,
                            **kwargs,
                        )

                    all_evidence.extend(tuple(result))
                    break

                except RetryableTerminalChainMismatch:
                    if attempt>=policy.retry_limit:
                        raise

                    attempt+=1
                    delay=min(
                        0.500,
                        policy.retry_base_seconds*(2**(attempt-1)),
                    )
                    if delay:
                        time.sleep(delay)

        return tuple(all_evidence)

    cls.route_batch=serialized_route
    setattr(cls,marker,True)
    setattr(cls,"_opc040_original_route_batch",original)
    return True

def verify_opc_040_coverage_serialized_persistence_integration():
    p=writer_policy("COVERAGE")
    return (
        COVERAGE_SERIAL_MICROBATCH==25
        and p.priority<writer_policy("FAST_LANE").priority
        and p.retry_limit>=5
        and not p.execution_authority
    )
