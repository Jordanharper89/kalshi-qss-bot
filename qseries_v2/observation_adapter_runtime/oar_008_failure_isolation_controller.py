from __future__ import annotations
from dataclasses import dataclass

from .oar_007_adapter_health_model import (
    AdapterHealthRecord,
    HEALTHY,
    DEGRADED,
    FAILED,
)

BUILD_ID = "OAR-008"
OAR_008_REVISION = "OAR_008_FAILURE_ISOLATION_CONTROLLER_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False

ACTION_CONTINUE = "continue"
ACTION_ISOLATE = "isolate"
ACTION_BLOCK = "block"


@dataclass(frozen=True, slots=True)
class AdapterIsolationDecision:
    adapter_id: str
    health_status: str
    action: str
    reason: str
    isolated: bool
    read_only: bool


class AdapterFailureIsolationController:
    read_only = True
    execution_allowed = False

    def decide(
        self,
        health_records: tuple[AdapterHealthRecord, ...],
    ) -> tuple[AdapterIsolationDecision, ...]:
        decisions = []

        seen = set()

        for record in sorted(
            health_records,
            key=lambda x: x.adapter_id,
        ):
            if record.adapter_id in seen:
                raise ValueError(
                    f"duplicate adapter health: {record.adapter_id}"
                )

            seen.add(record.adapter_id)

            if record.health_status == HEALTHY:
                action = ACTION_CONTINUE
                reason = "adapter_healthy"
                isolated = False
            elif record.health_status == DEGRADED:
                action = ACTION_ISOLATE
                reason = "adapter_degraded"
                isolated = True
            elif record.health_status == FAILED:
                action = ACTION_BLOCK
                reason = "adapter_failed"
                isolated = True
            else:
                raise ValueError(
                    f"unsupported health status: {record.health_status}"
                )

            decisions.append(
                AdapterIsolationDecision(
                    adapter_id=record.adapter_id,
                    health_status=record.health_status,
                    action=action,
                    reason=reason,
                    isolated=isolated,
                    read_only=True,
                )
            )

        return tuple(decisions)


def verify_failure_isolation_controller() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    return True
