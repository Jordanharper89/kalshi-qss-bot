from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Protocol, runtime_checkable

from .oad_001_adapter_foundation import (
    ObservationAdapterDescriptor,
)

BUILD_ID = "OAD-002"
OAD_002_REVISION = "OAD_002_CERTIFIED_ADAPTER_CONTRACT_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False


@dataclass(frozen=True, slots=True)
class ObservationAdapterRequest:
    request_id: str
    subject_hint: str | None
    capability: str
    requested_at: datetime
    metadata: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class ObservationAdapterResult:
    request_id: str
    adapter_id: str
    provider_id: str
    capability: str
    observations: tuple[Mapping[str, Any], ...]
    observed_at: datetime
    success: bool
    error_code: str | None
    read_only: bool
    execution_allowed: bool


@runtime_checkable
class CertifiedObservationAdapter(Protocol):
    descriptor: ObservationAdapterDescriptor
    read_only: bool
    execution_allowed: bool

    def observe(
        self,
        request: ObservationAdapterRequest,
    ) -> ObservationAdapterResult:
        ...


def build_adapter_request(
    *,
    request_id: str,
    subject_hint: str | None,
    capability: str,
    requested_at: datetime,
    metadata: Mapping[str, object] | None = None,
) -> ObservationAdapterRequest:
    request_id_value = str(request_id).strip()
    capability_value = str(capability).strip()

    if not request_id_value:
        raise ValueError(
            "request_id must not be empty"
        )

    if not capability_value:
        raise ValueError(
            "capability must not be empty"
        )

    if not isinstance(
        requested_at,
        datetime,
    ):
        raise TypeError(
            "requested_at must be datetime"
        )

    if requested_at.tzinfo is None:
        raise ValueError(
            "requested_at must be timezone-aware"
        )

    metadata_value = tuple(
        sorted(
            (
                str(key).strip(),
                str(value).strip(),
            )
            for key, value in (metadata or {}).items()
        )
    )

    return ObservationAdapterRequest(
        request_id=request_id_value,
        subject_hint=(
            None
            if subject_hint is None
            else str(subject_hint).strip()
        ),
        capability=capability_value,
        requested_at=requested_at.astimezone(
            timezone.utc
        ),
        metadata=metadata_value,
    )


def verify_certified_adapter(
    adapter: object,
) -> bool:
    if not isinstance(
        adapter,
        CertifiedObservationAdapter,
    ):
        raise TypeError(
            "adapter does not satisfy "
            "CertifiedObservationAdapter"
        )

    if adapter.read_only is not True:
        raise ValueError(
            "adapter must be read-only"
        )

    if adapter.execution_allowed is not False:
        raise ValueError(
            "adapter exposes execution permission"
        )

    if adapter.descriptor.read_only is not True:
        raise ValueError(
            "descriptor must be read-only"
        )

    if adapter.descriptor.execution_allowed is not False:
        raise ValueError(
            "descriptor exposes execution permission"
        )

    return True


def verify_certified_adapter_contract() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    return True


__all__ = [
    "BUILD_ID",
    "OAD_002_REVISION",
    "ObservationAdapterRequest",
    "ObservationAdapterResult",
    "CertifiedObservationAdapter",
    "build_adapter_request",
    "verify_certified_adapter",
    "verify_certified_adapter_contract",
]
