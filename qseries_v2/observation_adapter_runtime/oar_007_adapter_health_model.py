from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone

from .oar_003_multi_adapter_runner import MultiAdapterRunResult

BUILD_ID = "OAR-007"
OAR_007_REVISION = "OAR_007_ADAPTER_HEALTH_MODEL_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False

HEALTHY = "healthy"
DEGRADED = "degraded"
FAILED = "failed"


@dataclass(frozen=True, slots=True)
class AdapterHealthRecord:
    adapter_id: str
    request_count: int
    success_count: int
    failure_count: int
    observation_count: int
    health_status: str
    assessed_at: datetime
    read_only: bool


class AdapterHealthModel:
    read_only = True
    execution_allowed = False

    def assess(
        self,
        *,
        run_result: MultiAdapterRunResult,
        assessed_at: datetime,
    ) -> tuple[AdapterHealthRecord, ...]:
        if not isinstance(run_result, MultiAdapterRunResult):
            raise TypeError("run_result must be MultiAdapterRunResult")

        if not isinstance(assessed_at, datetime) or assessed_at.tzinfo is None:
            raise ValueError("assessed_at must be timezone-aware datetime")

        grouped = {}

        for record in run_result.records:
            row = grouped.setdefault(
                record.adapter_id,
                {
                    "request_count": 0,
                    "success_count": 0,
                    "failure_count": 0,
                    "observation_count": 0,
                },
            )

            row["request_count"] += 1
            row["observation_count"] += record.observation_count

            if record.success:
                row["success_count"] += 1
            else:
                row["failure_count"] += 1

        output = []

        for adapter_id in sorted(grouped):
            row = grouped[adapter_id]

            if row["failure_count"] == 0:
                status = HEALTHY
            elif row["success_count"] == 0:
                status = FAILED
            else:
                status = DEGRADED

            output.append(
                AdapterHealthRecord(
                    adapter_id=adapter_id,
                    request_count=row["request_count"],
                    success_count=row["success_count"],
                    failure_count=row["failure_count"],
                    observation_count=row["observation_count"],
                    health_status=status,
                    assessed_at=assessed_at.astimezone(timezone.utc),
                    read_only=True,
                )
            )

        return tuple(output)


def verify_adapter_health_model() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    return True
