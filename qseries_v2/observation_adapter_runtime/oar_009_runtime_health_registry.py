from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone

from .oar_007_adapter_health_model import (
    AdapterHealthRecord,
    HEALTHY,
    DEGRADED,
    FAILED,
)
from .oar_008_failure_isolation_controller import (
    AdapterIsolationDecision,
)

BUILD_ID = "OAR-009"
OAR_009_REVISION = "OAR_009_RUNTIME_HEALTH_REGISTRY_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False

RUNTIME_HEALTHY = "healthy"
RUNTIME_DEGRADED = "degraded"
RUNTIME_FAILED = "failed"


@dataclass(frozen=True, slots=True)
class RuntimeHealthSnapshot:
    runtime_id: str
    adapter_health: tuple[AdapterHealthRecord, ...]
    isolation_decisions: tuple[AdapterIsolationDecision, ...]
    healthy_count: int
    degraded_count: int
    failed_count: int
    isolated_count: int
    runtime_health_status: str
    assessed_at: datetime
    read_only: bool


class RuntimeHealthRegistry:
    read_only = True
    execution_allowed = False

    def build_snapshot(
        self,
        *,
        runtime_id: str,
        adapter_health: tuple[AdapterHealthRecord, ...],
        isolation_decisions: tuple[AdapterIsolationDecision, ...],
        assessed_at: datetime,
    ) -> RuntimeHealthSnapshot:
        runtime_id_value = str(runtime_id).strip()

        if not runtime_id_value:
            raise ValueError("runtime_id must not be empty")

        if not isinstance(assessed_at, datetime) or assessed_at.tzinfo is None:
            raise ValueError("assessed_at must be timezone-aware datetime")

        health_ids = tuple(
            x.adapter_id
            for x in sorted(
                adapter_health,
                key=lambda x: x.adapter_id,
            )
        )

        decision_ids = tuple(
            x.adapter_id
            for x in sorted(
                isolation_decisions,
                key=lambda x: x.adapter_id,
            )
        )

        if health_ids != decision_ids:
            raise ValueError(
                "health/isolation adapter identity mismatch"
            )

        healthy_count = sum(
            1 for x in adapter_health
            if x.health_status == HEALTHY
        )
        degraded_count = sum(
            1 for x in adapter_health
            if x.health_status == DEGRADED
        )
        failed_count = sum(
            1 for x in adapter_health
            if x.health_status == FAILED
        )
        isolated_count = sum(
            1 for x in isolation_decisions
            if x.isolated
        )

        if failed_count == len(adapter_health) and adapter_health:
            runtime_status = RUNTIME_FAILED
        elif failed_count or degraded_count:
            runtime_status = RUNTIME_DEGRADED
        else:
            runtime_status = RUNTIME_HEALTHY

        return RuntimeHealthSnapshot(
            runtime_id=runtime_id_value,
            adapter_health=tuple(
                sorted(
                    adapter_health,
                    key=lambda x: x.adapter_id,
                )
            ),
            isolation_decisions=tuple(
                sorted(
                    isolation_decisions,
                    key=lambda x: x.adapter_id,
                )
            ),
            healthy_count=healthy_count,
            degraded_count=degraded_count,
            failed_count=failed_count,
            isolated_count=isolated_count,
            runtime_health_status=runtime_status,
            assessed_at=assessed_at.astimezone(timezone.utc),
            read_only=True,
        )


def verify_runtime_health_registry() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    return True
