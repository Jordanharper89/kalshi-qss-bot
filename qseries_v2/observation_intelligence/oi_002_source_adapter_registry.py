from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

from .oi_001_universal_observation_intake import (
    ObservationSourceIdentity,
    deterministic_sha256,
    verify_universal_observation_intake,
)

BUILD_ID = "OI-002"
OI_002_REVISION = "OI_002_SOURCE_ADAPTER_REGISTRY_V1"
READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False


class SourceAdapterRegistryError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class SourceAdapterDescriptor:
    adapter_id: str
    source_id: str
    source_kind: str
    provider: str
    adapter_version: str
    capabilities: tuple[str, ...]
    enabled_for_intake: bool

    def __post_init__(self) -> None:
        identity = ObservationSourceIdentity(
            source_id=self.source_id,
            source_kind=self.source_kind,
            provider=self.provider,
            adapter_id=self.adapter_id,
        )
        object.__setattr__(self, "adapter_id", identity.adapter_id)
        object.__setattr__(self, "source_id", identity.source_id)
        object.__setattr__(self, "source_kind", identity.source_kind)
        object.__setattr__(self, "provider", identity.provider)

        version = " ".join(str(self.adapter_version).strip().split())
        if not version:
            raise SourceAdapterRegistryError("adapter_version must not be empty")
        object.__setattr__(self, "adapter_version", version)

        capabilities = tuple(sorted({
            " ".join(str(item).strip().lower().split())
            for item in self.capabilities
            if str(item).strip()
        }))
        if not capabilities:
            raise SourceAdapterRegistryError("capabilities must not be empty")
        object.__setattr__(self, "capabilities", capabilities)

    @property
    def descriptor_hash(self) -> str:
        return deterministic_sha256({
            "adapter_id": self.adapter_id,
            "source_id": self.source_id,
            "source_kind": self.source_kind,
            "provider": self.provider,
            "adapter_version": self.adapter_version,
            "capabilities": self.capabilities,
            "enabled_for_intake": self.enabled_for_intake,
        })

    def source_identity(self) -> ObservationSourceIdentity:
        return ObservationSourceIdentity(
            source_id=self.source_id,
            source_kind=self.source_kind,
            provider=self.provider,
            adapter_id=self.adapter_id,
        )


class SourceAdapterRegistry:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False

    def __init__(self, adapters: tuple[SourceAdapterDescriptor, ...]) -> None:
        values = tuple(adapters)
        if any(not isinstance(item, SourceAdapterDescriptor) for item in values):
            raise TypeError("all adapters must be SourceAdapterDescriptor")

        ordered = tuple(sorted(values, key=lambda item: item.adapter_id))
        if values != ordered:
            raise SourceAdapterRegistryError("adapters must be deterministically sorted")

        adapter_ids = tuple(item.adapter_id for item in values)
        if len(adapter_ids) != len(set(adapter_ids)):
            raise SourceAdapterRegistryError("duplicate adapter_id")

        bindings = tuple((item.source_id, item.adapter_id) for item in values)
        if len(bindings) != len(set(bindings)):
            raise SourceAdapterRegistryError("duplicate source-adapter binding")

        self._adapters = values
        self._by_id = MappingProxyType({item.adapter_id: item for item in values})
        kinds = sorted({item.source_kind for item in values})
        self._by_kind = MappingProxyType({
            kind: tuple(item for item in values if item.source_kind == kind)
            for kind in kinds
        })

    @property
    def adapters(self) -> tuple[SourceAdapterDescriptor, ...]:
        return self._adapters

    @property
    def registry_hash(self) -> str:
        return deterministic_sha256(tuple(item.descriptor_hash for item in self._adapters))

    def get(self, adapter_id: str) -> SourceAdapterDescriptor | None:
        return self._by_id.get(str(adapter_id).strip().lower())

    def by_kind(self, source_kind: str) -> tuple[SourceAdapterDescriptor, ...]:
        return self._by_kind.get(str(source_kind).strip().lower(), ())

    def enabled(self) -> tuple[SourceAdapterDescriptor, ...]:
        return tuple(item for item in self._adapters if item.enabled_for_intake)


def verify_source_adapter_registry() -> bool:
    verify_universal_observation_intake()
    if READ_ONLY is not True:
        raise AssertionError("OI-002 must remain read-only")
    if any((NETWORK_ALLOWED, PERSISTENCE_ALLOWED, PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED, QSERIES_EXECUTION_ALLOWED)):
        raise AssertionError("OI-002 forbidden capability enabled")
    return True


__all__ = [
    "BUILD_ID",
    "OI_002_REVISION",
    "SourceAdapterRegistryError",
    "SourceAdapterDescriptor",
    "SourceAdapterRegistry",
    "verify_source_adapter_registry",
]
