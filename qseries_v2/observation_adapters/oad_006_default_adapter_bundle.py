from __future__ import annotations

from dataclasses import dataclass

from .oad_003_adapter_registry import (
    ObservationAdapterRegistry,
)
from .oad_004_kalshi_observation_bridge import (
    FrozenOIKalshiObservationBridge,
)
from .oad_005_crypto_observation_bridge import (
    FrozenOICryptoObservationBridge,
)

BUILD_ID = "OAD-006"
OAD_006_REVISION = "OAD_006_DEFAULT_ADAPTER_BUNDLE_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False


@dataclass(frozen=True, slots=True)
class CertifiedDefaultAdapterBundle:
    registry: ObservationAdapterRegistry
    adapter_ids: tuple[str, ...]
    provider_ids: tuple[str, ...]
    capability_union: tuple[str, ...]
    read_only: bool
    execution_allowed: bool


def build_default_adapter_bundle() -> CertifiedDefaultAdapterBundle:
    adapters = (
        FrozenOIKalshiObservationBridge(),
        FrozenOICryptoObservationBridge(),
    )

    registry = ObservationAdapterRegistry(
        adapters
    )

    adapter_ids = registry.adapter_ids()

    provider_ids = tuple(
        sorted(
            {
                descriptor.identity.provider_id
                for descriptor
                in registry.descriptors()
            }
        )
    )

    capability_union = tuple(
        sorted(
            {
                capability
                for descriptor
                in registry.descriptors()
                for capability
                in descriptor.capabilities
            }
        )
    )

    return CertifiedDefaultAdapterBundle(
        registry=registry,
        adapter_ids=adapter_ids,
        provider_ids=provider_ids,
        capability_union=capability_union,
        read_only=True,
        execution_allowed=False,
    )


def verify_default_adapter_bundle() -> bool:
    bundle = build_default_adapter_bundle()

    if bundle.adapter_ids != (
        "adapter.crypto.observe.v1",
        "adapter.kalshi.observe.v1",
    ):
        raise AssertionError(
            "default adapter identities changed"
        )

    if bundle.provider_ids != (
        "coinbase",
        "kalshi",
    ):
        raise AssertionError(
            "default provider identities changed"
        )

    if bundle.read_only is not True:
        raise AssertionError(
            "default bundle must remain read-only"
        )

    if bundle.execution_allowed is not False:
        raise AssertionError(
            "default bundle exposes execution"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OAD_006_REVISION",
    "CertifiedDefaultAdapterBundle",
    "build_default_adapter_bundle",
    "verify_default_adapter_bundle",
]
