"""
OLA-056 Production Live Shadow Start Authorization Consumption.

Consumes the immutable OLA-055 pre-start authorization exactly once and emits
an auditable launch token. This boundary still does not invoke the OLA-023
runner or start any process, thread, loop, acquisition, scheduler tick, or
shadow cycle.

The token is intentionally separate from execution. A later controlled launch
module may require this token before invoking the already-bound read-only
live-shadow runner.
"""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Any

SCHEMA_VERSION = "OLA-056"
ENGINE_ID = "OLA-056"
TOKEN_TYPE = "oracle_production_live_shadow_single_use_launch_token"


class OracleProductionLiveShadowStartAuthorizationConsumptionError(ValueError):
    pass


class OracleProductionLiveShadowStartAuthorizationConsumptionBlocked(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class OracleProductionLiveShadowSingleUseLaunchToken:
    schema_version: str
    engine_id: str
    token_type: str
    source_authorization_schema_version: str
    source_authorization_engine_id: str
    source_authorization_identity: int
    authorization_consumed: bool
    launch_token_issued: bool
    launch_invoked: bool = False
    service_started: bool = False
    process_created: bool = False
    thread_created: bool = False
    loop_started: bool = False
    acquisition_invoked: bool = False
    scheduler_tick_invoked: bool = False
    shadow_cycle_invoked: bool = False
    read_only: bool = True
    execution_allowed: bool = False
    alerts_allowed: bool = False
    qseries_handoff_allowed: bool = False
    execution_adapter_resolved: bool = False
    execution_adapter_invoked: bool = False
    trade_authorization_allowed: bool = False
    order_placement_allowed: bool = False
    funds_moved: bool = False
    portfolio_mutated: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION or self.engine_id != ENGINE_ID:
            raise OracleProductionLiveShadowStartAuthorizationConsumptionError(
                "OLA-056 identity mismatch"
            )
        if self.token_type != TOKEN_TYPE:
            raise OracleProductionLiveShadowStartAuthorizationConsumptionError(
                "token_type mismatch"
            )
        if self.authorization_consumed is not True:
            raise OracleProductionLiveShadowStartAuthorizationConsumptionBlocked(
                "OLA-056 token requires consumed authorization"
            )
        if self.launch_token_issued is not True:
            raise OracleProductionLiveShadowStartAuthorizationConsumptionBlocked(
                "OLA-056 token issuance failed closed"
            )
        if self.read_only is not True:
            raise OracleProductionLiveShadowStartAuthorizationConsumptionBlocked(
                "OLA-056 read-only invariant violated"
            )

        forbidden = (
            self.launch_invoked,
            self.service_started,
            self.process_created,
            self.thread_created,
            self.loop_started,
            self.acquisition_invoked,
            self.scheduler_tick_invoked,
            self.shadow_cycle_invoked,
            self.execution_allowed,
            self.alerts_allowed,
            self.qseries_handoff_allowed,
            self.execution_adapter_resolved,
            self.execution_adapter_invoked,
            self.trade_authorization_allowed,
            self.order_placement_allowed,
            self.funds_moved,
            self.portfolio_mutated,
        )
        if any(value is True for value in forbidden):
            raise OracleProductionLiveShadowStartAuthorizationConsumptionBlocked(
                "OLA-056 observed forbidden activity during authorization consumption"
            )


class OracleProductionLiveShadowStartAuthorizationConsumer:
    read_only = True
    execution_allowed = False

    def __init__(self) -> None:
        self._lock = Lock()
        self._consumed_authorization_identities: set[int] = set()

    def consume(
        self,
        *,
        start_authorization: Any,
    ) -> OracleProductionLiveShadowSingleUseLaunchToken:
        with self._lock:
            authorization_identity = id(start_authorization)

            if authorization_identity in self._consumed_authorization_identities:
                raise OracleProductionLiveShadowStartAuthorizationConsumptionBlocked(
                    "OLA-055 start authorization already consumed"
                )

            checks = (
                getattr(start_authorization, "schema_version", None) == "OLA-055",
                getattr(start_authorization, "engine_id", None) == "OLA-055",
                getattr(start_authorization, "start_authorized", None) is True,
                getattr(start_authorization, "authorization_consumed", None) is False,
                getattr(start_authorization, "service_started", None) is False,
                getattr(start_authorization, "loop_started", None) is False,
                getattr(start_authorization, "acquisition_invoked", None) is False,
                getattr(start_authorization, "scheduler_tick_invoked", None) is False,
                getattr(start_authorization, "shadow_cycle_invoked", None) is False,
                getattr(start_authorization, "read_only", None) is True,
                getattr(start_authorization, "execution_allowed", None) is False,
            )
            if not all(checks):
                raise OracleProductionLiveShadowStartAuthorizationConsumptionBlocked(
                    "OLA-055 start authorization is not eligible for consumption"
                )

            self._consumed_authorization_identities.add(
                authorization_identity
            )

            return OracleProductionLiveShadowSingleUseLaunchToken(
                schema_version=SCHEMA_VERSION,
                engine_id=ENGINE_ID,
                token_type=TOKEN_TYPE,
                source_authorization_schema_version=(
                    start_authorization.schema_version
                ),
                source_authorization_engine_id=(
                    start_authorization.engine_id
                ),
                source_authorization_identity=authorization_identity,
                authorization_consumed=True,
                launch_token_issued=True,
            )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "TOKEN_TYPE",
    "OracleProductionLiveShadowStartAuthorizationConsumptionError",
    "OracleProductionLiveShadowStartAuthorizationConsumptionBlocked",
    "OracleProductionLiveShadowSingleUseLaunchToken",
    "OracleProductionLiveShadowStartAuthorizationConsumer",
]
