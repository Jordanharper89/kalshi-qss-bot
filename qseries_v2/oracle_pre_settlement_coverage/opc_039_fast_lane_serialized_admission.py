from __future__ import annotations
from pathlib import Path
import time

from .opc_037_canonical_writer_arbiter_foundation import writer_policy
from .opc_038_atomic_cross_process_writer_lease import (
    acquire_canonical_writer_lease,
)

OPC_039_BUILD_ID="OPC-039"
OPC_039_REVISION="OPC_039_FAST_LANE_SERIALIZED_ADMISSION_V1"

class RetryableTerminalChainMismatch(RuntimeError):
    pass

def _install_retryable_mismatch_validator(cls):
    marker="_opc039_retryable_validator_installed"
    if getattr(cls,marker,False):
        return

    original=cls._validate_batch_append_result

    def validated(*,observations,append_result,expected_terminal_chain_hash,**kwargs):
        reasons=tuple(
            getattr(append_result,"reason_codes",()) or ()
        )
        if (
            getattr(append_result,"committed",None) is False
            and "expected_terminal_chain_hash_mismatch" in reasons
        ):
            raise RetryableTerminalChainMismatch(
                "expected_terminal_chain_hash_mismatch"
            )

        return original(
            observations=observations,
            append_result=append_result,
            expected_terminal_chain_hash=expected_terminal_chain_hash,
            **kwargs,
        )

    cls._validate_batch_append_result=staticmethod(validated)
    setattr(cls,marker,True)

def install_fast_lane_serialized_admission(root=None):
    from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_router import (
        OraclePostgreSQLCanonicalObservationPersistenceRouter,
    )

    cls=OraclePostgreSQLCanonicalObservationPersistenceRouter
    marker="_opc039_fast_lane_serialized"

    if getattr(cls,marker,False):
        return False

    _install_retryable_mismatch_validator(cls)

    original=cls.route_batch
    root=Path(root or Path.cwd()).resolve()
    policy=writer_policy("FAST_LANE")

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

        attempt=0

        while True:
            try:
                with acquire_canonical_writer_lease(
                    "FAST_LANE",
                    root=root,
                    timeout_seconds=policy.lease_timeout_seconds,
                ):
                    return original(
                        self,
                        items,
                        routed_at,
                        *args,
                        **kwargs,
                    )

            except RetryableTerminalChainMismatch:
                if attempt>=policy.retry_limit:
                    raise

                attempt+=1
                delay=min(
                    0.100,
                    policy.retry_base_seconds*(2**(attempt-1)),
                )
                if delay:
                    time.sleep(delay)

    cls.route_batch=serialized_route
    setattr(cls,marker,True)
    setattr(cls,"_opc039_original_route_batch",original)
    return True

def verify_opc_039_fast_lane_serialized_admission():
    p=writer_policy("FAST_LANE")
    return (
        p.priority==100
        and p.retry_limit>=5
        and p.retry_base_seconds<=0.01
        and not p.execution_authority
    )
