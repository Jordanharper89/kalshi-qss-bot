from __future__ import annotations

import importlib
import inspect
from dataclasses import dataclass
from datetime import datetime, timezone
from types import ModuleType
from typing import Any, Callable, Mapping

from .oad_001_adapter_foundation import (
    build_adapter_descriptor,
)
from .oad_002_adapter_contract import (
    ObservationAdapterRequest,
    ObservationAdapterResult,
)

BUILD_ID = "OAD-005"
OAD_005_REVISION = "OAD_005_CRYPTO_OBSERVATION_BRIDGE_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False

FROZEN_OI_MODULE = (
    "qseries_v2.observation_intelligence."
    "oi_005_public_market_data_adapter"
)

ADAPTER_ID = "adapter.crypto.observe.v1"
PROVIDER_ID = "coinbase"
SOURCE_DOMAIN = "crypto_market_data"

CAPABILITIES = (
    "market_snapshot",
    "spot_price",
)

_DISCOVERY_NAMES = (
    "observe",
    "collect",
    "acquire",
    "fetch",
    "snapshot",
    "get_spot_price",
    "get_market_snapshot",
)


def _safe_payload(value: Any) -> tuple[Mapping[str, Any], ...]:
    if value is None:
        return ()

    if isinstance(value, Mapping):
        return (dict(value),)

    if isinstance(value, (list, tuple)):
        result = []
        for item in value:
            if isinstance(item, Mapping):
                result.append(dict(item))
            elif hasattr(item, "__dict__"):
                result.append(dict(vars(item)))
            else:
                result.append({"value": item})
        return tuple(result)

    if hasattr(value, "__dict__"):
        return (dict(vars(value)),)

    return ({"value": value},)


def _resolve_callable(
    module: ModuleType,
    capability: str,
) -> Callable[..., Any]:
    preferred = []

    if capability == "spot_price":
        preferred.extend(
            (
                "get_spot_price",
                "spot_price",
                "fetch_spot_price",
                "collect_spot_price",
            )
        )
    elif capability == "market_snapshot":
        preferred.extend(
            (
                "market_snapshot",
                "fetch_market_snapshot",
                "collect_market_snapshot",
                "get_market_snapshot",
            )
        )

    preferred.extend(_DISCOVERY_NAMES)

    for name in preferred:
        candidate = getattr(module, name, None)
        if callable(candidate):
            return candidate

    for _, value in inspect.getmembers(module):
        if inspect.isclass(value):
            try:
                instance = value()
            except Exception:
                continue

            for name in preferred:
                candidate = getattr(instance, name, None)
                if callable(candidate):
                    return candidate

    raise RuntimeError(
        "Frozen OI-005 crypto adapter exposes no supported "
        f"callable for capability {capability!r}"
    )


def _invoke(
    callable_object: Callable[..., Any],
    request: ObservationAdapterRequest,
) -> Any:
    signature = inspect.signature(callable_object)
    params = signature.parameters

    aliases = {
        "request": request,
        "request_id": request.request_id,
        "subject_hint": request.subject_hint,
        "subject": request.subject_hint,
        "asset": request.subject_hint,
        "symbol": request.subject_hint,
        "capability": request.capability,
        "requested_at": request.requested_at,
        "metadata": dict(request.metadata),
    }

    kwargs = {}

    for name, parameter in params.items():
        if name in aliases:
            kwargs[name] = aliases[name]
        elif (
            parameter.default is inspect.Parameter.empty
            and parameter.kind
            not in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            )
        ):
            raise RuntimeError(
                "Frozen OI-005 callable has unsupported "
                f"required parameter: {name}"
            )

    return callable_object(**kwargs)


@dataclass(frozen=True, slots=True)
class FrozenOICryptoObservationBridge:
    descriptor = build_adapter_descriptor(
        adapter_id=ADAPTER_ID,
        provider_id=PROVIDER_ID,
        source_domain=SOURCE_DOMAIN,
        version="1",
        capabilities=CAPABILITIES,
        metadata={
            "upstream": "OI-005",
            "mode": "frozen_read_only_bridge",
        },
    )

    read_only: bool = True
    execution_allowed: bool = False
    order_placement_allowed: bool = False

    def observe(
        self,
        request: ObservationAdapterRequest,
    ) -> ObservationAdapterResult:
        if not isinstance(
            request,
            ObservationAdapterRequest,
        ):
            raise TypeError(
                "request must be ObservationAdapterRequest"
            )

        if request.capability not in self.descriptor.capabilities:
            return ObservationAdapterResult(
                request_id=request.request_id,
                adapter_id=ADAPTER_ID,
                provider_id=PROVIDER_ID,
                capability=request.capability,
                observations=(),
                observed_at=datetime.now(timezone.utc),
                success=False,
                error_code="unsupported_capability",
                read_only=True,
                execution_allowed=False,
            )

        try:
            module = importlib.import_module(
                FROZEN_OI_MODULE
            )

            callable_object = _resolve_callable(
                module,
                request.capability,
            )

            raw = _invoke(
                callable_object,
                request,
            )

            observations = _safe_payload(raw)

            return ObservationAdapterResult(
                request_id=request.request_id,
                adapter_id=ADAPTER_ID,
                provider_id=PROVIDER_ID,
                capability=request.capability,
                observations=observations,
                observed_at=datetime.now(timezone.utc),
                success=True,
                error_code=None,
                read_only=True,
                execution_allowed=False,
            )

        except Exception as exc:
            return ObservationAdapterResult(
                request_id=request.request_id,
                adapter_id=ADAPTER_ID,
                provider_id=PROVIDER_ID,
                capability=request.capability,
                observations=(),
                observed_at=datetime.now(timezone.utc),
                success=False,
                error_code=(
                    "upstream_failure:"
                    + type(exc).__name__
                ),
                read_only=True,
                execution_allowed=False,
            )


def verify_crypto_observation_bridge() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert ORDER_PLACEMENT_ALLOWED is False
    assert (
        FrozenOICryptoObservationBridge
        .descriptor
        .identity
        .provider_id
        == PROVIDER_ID
    )
    return True


__all__ = [
    "BUILD_ID",
    "OAD_005_REVISION",
    "FROZEN_OI_MODULE",
    "ADAPTER_ID",
    "PROVIDER_ID",
    "CAPABILITIES",
    "FrozenOICryptoObservationBridge",
    "verify_crypto_observation_bridge",
]
