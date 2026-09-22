from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

BUILD_ID = "OAD-001"
OAD_001_REVISION = "OAD_001_OBSERVATION_ADAPTER_FOUNDATION_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False

SUPPORTED_ADAPTER_STATES = (
    "enabled",
    "disabled",
    "unavailable",
)


@dataclass(frozen=True, slots=True)
class ObservationAdapterIdentity:
    adapter_id: str
    provider_id: str
    source_domain: str
    version: str


@dataclass(frozen=True, slots=True)
class ObservationAdapterDescriptor:
    identity: ObservationAdapterIdentity
    capabilities: tuple[str, ...]
    state: str
    read_only: bool
    execution_allowed: bool
    order_placement_allowed: bool
    metadata: tuple[tuple[str, str], ...]


def canonical_metadata(
    metadata: Mapping[str, object] | None,
) -> tuple[tuple[str, str], ...]:
    if metadata is None:
        return ()

    return tuple(
        sorted(
            (
                str(key).strip(),
                str(value).strip(),
            )
            for key, value in metadata.items()
        )
    )


def build_adapter_descriptor(
    *,
    adapter_id: str,
    provider_id: str,
    source_domain: str,
    version: str,
    capabilities: tuple[str, ...],
    state: str = "enabled",
    metadata: Mapping[str, object] | None = None,
) -> ObservationAdapterDescriptor:
    values = {
        "adapter_id": adapter_id,
        "provider_id": provider_id,
        "source_domain": source_domain,
        "version": version,
    }

    normalized = {
        key: str(value).strip()
        for key, value in values.items()
    }

    for key, value in normalized.items():
        if not value:
            raise ValueError(
                f"{key} must not be empty"
            )

    capability_values = tuple(
        sorted(
            {
                str(value).strip()
                for value in capabilities
                if str(value).strip()
            }
        )
    )

    if not capability_values:
        raise ValueError(
            "capabilities must not be empty"
        )

    state_value = str(state).strip().lower()

    if state_value not in SUPPORTED_ADAPTER_STATES:
        raise ValueError(
            f"unsupported adapter state: {state}"
        )

    return ObservationAdapterDescriptor(
        identity=ObservationAdapterIdentity(
            adapter_id=normalized["adapter_id"],
            provider_id=normalized["provider_id"],
            source_domain=normalized["source_domain"],
            version=normalized["version"],
        ),
        capabilities=capability_values,
        state=state_value,
        read_only=True,
        execution_allowed=False,
        order_placement_allowed=False,
        metadata=canonical_metadata(metadata),
    )


def verify_observation_adapter_foundation() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert ORDER_PLACEMENT_ALLOWED is False
    assert FUNDS_MOVED is False
    assert PORTFOLIO_MUTATED is False
    return True


__all__ = [
    "BUILD_ID",
    "OAD_001_REVISION",
    "SUPPORTED_ADAPTER_STATES",
    "ObservationAdapterIdentity",
    "ObservationAdapterDescriptor",
    "canonical_metadata",
    "build_adapter_descriptor",
    "verify_observation_adapter_foundation",
]
