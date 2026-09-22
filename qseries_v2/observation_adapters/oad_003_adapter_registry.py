from __future__ import annotations

from dataclasses import dataclass

from .oad_001_adapter_foundation import (
    ObservationAdapterDescriptor,
)
from .oad_002_adapter_contract import (
    CertifiedObservationAdapter,
    verify_certified_adapter,
)

BUILD_ID = "OAD-003"
OAD_003_REVISION = "OAD_003_ADAPTER_REGISTRY_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False


@dataclass(frozen=True, slots=True)
class RegisteredObservationAdapter:
    descriptor: ObservationAdapterDescriptor
    adapter: CertifiedObservationAdapter


class ObservationAdapterRegistry:
    read_only = True
    execution_allowed = False

    def __init__(
        self,
        adapters: tuple[
            CertifiedObservationAdapter,
            ...
        ] = (),
    ) -> None:
        mapping = {}

        for adapter in adapters:
            verify_certified_adapter(adapter)

            adapter_id = (
                adapter
                .descriptor
                .identity
                .adapter_id
            )

            if adapter_id in mapping:
                raise ValueError(
                    f"duplicate adapter_id: {adapter_id}"
                )

            mapping[adapter_id] = adapter

        self._mapping = dict(
            sorted(mapping.items())
        )

    def adapter_ids(self) -> tuple[str, ...]:
        return tuple(
            self._mapping.keys()
        )

    def get(
        self,
        adapter_id: str,
    ):
        return self._mapping.get(
            str(adapter_id).strip()
        )

    def by_capability(
        self,
        capability: str,
    ) -> tuple[
        CertifiedObservationAdapter,
        ...
    ]:
        capability_value = str(
            capability
        ).strip()

        if not capability_value:
            raise ValueError(
                "capability must not be empty"
            )

        return tuple(
            adapter
            for adapter in self._mapping.values()
            if (
                adapter.descriptor.state == "enabled"
                and capability_value
                in adapter.descriptor.capabilities
            )
        )

    def by_provider(
        self,
        provider_id: str,
    ) -> tuple[
        CertifiedObservationAdapter,
        ...
    ]:
        provider_value = str(
            provider_id
        ).strip()

        return tuple(
            adapter
            for adapter in self._mapping.values()
            if (
                adapter
                .descriptor
                .identity
                .provider_id
                == provider_value
            )
        )

    def descriptors(
        self,
    ) -> tuple[
        ObservationAdapterDescriptor,
        ...
    ]:
        return tuple(
            adapter.descriptor
            for adapter in self._mapping.values()
        )


def verify_adapter_registry_foundation() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    return True


__all__ = [
    "BUILD_ID",
    "OAD_003_REVISION",
    "RegisteredObservationAdapter",
    "ObservationAdapterRegistry",
    "verify_adapter_registry_foundation",
]
