from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from qseries_v2.observation_adapters.oad_002_adapter_contract import (
    ObservationAdapterResult,
)
from qseries_v2.observation_adapters.oad_006_default_adapter_bundle import (
    CertifiedDefaultAdapterBundle,
)
from .oar_002_adapter_scheduler import (
    AdapterSchedule,
)

BUILD_ID = "OAR-003"
OAR_003_REVISION = "OAR_003_MULTI_ADAPTER_OBSERVATION_RUNNER_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False


@dataclass(frozen=True, slots=True)
class AdapterRunRecord:
    ordinal: int
    adapter_id: str
    request_id: str
    capability: str
    success: bool
    observation_count: int
    error_code: str | None


@dataclass(frozen=True, slots=True)
class MultiAdapterRunResult:
    iteration_number: int
    started_at: datetime
    completed_at: datetime
    records: tuple[AdapterRunRecord, ...]
    results: tuple[ObservationAdapterResult, ...]
    request_count: int
    success_count: int
    failure_count: int
    observation_count: int
    read_only: bool
    execution_allowed: bool


class MultiAdapterObservationRunner:
    read_only = True
    execution_allowed = False

    def run(
        self,
        *,
        bundle: CertifiedDefaultAdapterBundle,
        schedule: AdapterSchedule,
        clock_callable: Callable[[], datetime],
    ) -> MultiAdapterRunResult:
        if not isinstance(
            bundle,
            CertifiedDefaultAdapterBundle,
        ):
            raise TypeError(
                "bundle must be CertifiedDefaultAdapterBundle"
            )

        if not isinstance(
            schedule,
            AdapterSchedule,
        ):
            raise TypeError(
                "schedule must be AdapterSchedule"
            )

        if not callable(clock_callable):
            raise TypeError(
                "clock_callable must be callable"
            )

        started_at = clock_callable()

        if not isinstance(started_at, datetime):
            raise TypeError(
                "clock_callable must return datetime"
            )

        if started_at.tzinfo is None:
            raise ValueError(
                "clock timestamps must be timezone-aware"
            )

        results = []
        records = []

        for scheduled in schedule.requests:
            adapter = bundle.registry.get(
                scheduled.adapter_id
            )

            if adapter is None:
                result = ObservationAdapterResult(
                    request_id=scheduled.request.request_id,
                    adapter_id=scheduled.adapter_id,
                    provider_id="unknown",
                    capability=scheduled.request.capability,
                    observations=(),
                    observed_at=started_at.astimezone(
                        timezone.utc
                    ),
                    success=False,
                    error_code="adapter_not_registered",
                    read_only=True,
                    execution_allowed=False,
                )
            else:
                try:
                    result = adapter.observe(
                        scheduled.request
                    )
                except Exception as exc:
                    result = ObservationAdapterResult(
                        request_id=scheduled.request.request_id,
                        adapter_id=scheduled.adapter_id,
                        provider_id=(
                            adapter.descriptor.identity.provider_id
                        ),
                        capability=scheduled.request.capability,
                        observations=(),
                        observed_at=started_at.astimezone(
                            timezone.utc
                        ),
                        success=False,
                        error_code=(
                            "adapter_exception:"
                            + type(exc).__name__
                        ),
                        read_only=True,
                        execution_allowed=False,
                    )

            if result.read_only is not True:
                raise RuntimeError(
                    "adapter result violated read-only boundary"
                )

            if result.execution_allowed is not False:
                raise RuntimeError(
                    "adapter result exposed execution permission"
                )

            results.append(result)

            records.append(
                AdapterRunRecord(
                    ordinal=scheduled.ordinal,
                    adapter_id=scheduled.adapter_id,
                    request_id=result.request_id,
                    capability=result.capability,
                    success=result.success,
                    observation_count=len(
                        result.observations
                    ),
                    error_code=result.error_code,
                )
            )

        completed_at = clock_callable()

        if not isinstance(completed_at, datetime):
            raise TypeError(
                "clock_callable must return datetime"
            )

        if completed_at.tzinfo is None:
            raise ValueError(
                "clock timestamps must be timezone-aware"
            )

        results_tuple = tuple(results)
        records_tuple = tuple(records)

        success_count = sum(
            1
            for item in results_tuple
            if item.success
        )

        failure_count = (
            len(results_tuple)
            - success_count
        )

        observation_count = sum(
            len(item.observations)
            for item in results_tuple
        )

        return MultiAdapterRunResult(
            iteration_number=schedule.iteration_number,
            started_at=started_at.astimezone(timezone.utc),
            completed_at=completed_at.astimezone(timezone.utc),
            records=records_tuple,
            results=results_tuple,
            request_count=len(results_tuple),
            success_count=success_count,
            failure_count=failure_count,
            observation_count=observation_count,
            read_only=True,
            execution_allowed=False,
        )


def verify_multi_adapter_observation_runner() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    return True


__all__ = [
    "BUILD_ID",
    "OAR_003_REVISION",
    "AdapterRunRecord",
    "MultiAdapterRunResult",
    "MultiAdapterObservationRunner",
    "verify_multi_adapter_observation_runner",
]
