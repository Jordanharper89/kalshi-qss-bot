from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from qseries_v2.observation_adapters.oad_002_adapter_contract import (
    ObservationAdapterRequest,
    build_adapter_request,
)
from qseries_v2.observation_adapters.oad_006_default_adapter_bundle import (
    CertifiedDefaultAdapterBundle,
)

BUILD_ID = "OAR-002"
OAR_002_REVISION = "OAR_002_DETERMINISTIC_ADAPTER_SCHEDULER_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False


@dataclass(frozen=True, slots=True)
class ScheduledAdapterRequest:
    ordinal: int
    adapter_id: str
    request: ObservationAdapterRequest


@dataclass(frozen=True, slots=True)
class AdapterSchedule:
    iteration_number: int
    requests: tuple[ScheduledAdapterRequest, ...]
    request_count: int
    scheduled_at: datetime
    read_only: bool
    execution_allowed: bool


class DeterministicAdapterScheduler:
    read_only = True
    execution_allowed = False

    def schedule(
        self,
        *,
        bundle: CertifiedDefaultAdapterBundle,
        iteration_number: int,
        scheduled_at: datetime,
        subject_hints: dict[str, str | None] | None = None,
    ) -> AdapterSchedule:
        if not isinstance(bundle, CertifiedDefaultAdapterBundle):
            raise TypeError(
                "bundle must be CertifiedDefaultAdapterBundle"
            )

        if not isinstance(iteration_number, int):
            raise TypeError(
                "iteration_number must be int"
            )

        if iteration_number < 1:
            raise ValueError(
                "iteration_number must be positive"
            )

        if not isinstance(scheduled_at, datetime):
            raise TypeError(
                "scheduled_at must be datetime"
            )

        if scheduled_at.tzinfo is None:
            raise ValueError(
                "scheduled_at must be timezone-aware"
            )

        scheduled_at = scheduled_at.astimezone(timezone.utc)
        subject_hints = dict(subject_hints or {})

        rows = []

        for adapter_id in bundle.adapter_ids:
            adapter = bundle.registry.get(adapter_id)

            if adapter is None:
                raise RuntimeError(
                    f"registered adapter missing: {adapter_id}"
                )

            provider_id = (
                adapter.descriptor.identity.provider_id
            )

            subject_hint = subject_hints.get(provider_id)

            for capability in adapter.descriptor.capabilities:
                request = build_adapter_request(
                    request_id=(
                        f"runtime.iteration.{iteration_number}."
                        f"{adapter_id}.{capability}"
                    ),
                    subject_hint=subject_hint,
                    capability=capability,
                    requested_at=scheduled_at,
                    metadata={
                        "iteration_number": iteration_number,
                        "adapter_id": adapter_id,
                        "provider_id": provider_id,
                    },
                )

                rows.append(
                    (
                        adapter_id,
                        capability,
                        request,
                    )
                )

        rows.sort(
            key=lambda item: (
                item[0],
                item[1],
            )
        )

        requests = tuple(
            ScheduledAdapterRequest(
                ordinal=index,
                adapter_id=adapter_id,
                request=request,
            )
            for index, (
                adapter_id,
                _,
                request,
            ) in enumerate(rows, start=1)
        )

        return AdapterSchedule(
            iteration_number=iteration_number,
            requests=requests,
            request_count=len(requests),
            scheduled_at=scheduled_at,
            read_only=True,
            execution_allowed=False,
        )


def verify_deterministic_adapter_scheduler() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    return True


__all__ = [
    "BUILD_ID",
    "OAR_002_REVISION",
    "ScheduledAdapterRequest",
    "AdapterSchedule",
    "DeterministicAdapterScheduler",
    "verify_deterministic_adapter_scheduler",
]
