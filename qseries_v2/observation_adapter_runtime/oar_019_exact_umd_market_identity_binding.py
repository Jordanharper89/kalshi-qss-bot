from __future__ import annotations

import importlib
import inspect
from dataclasses import dataclass
from typing import Any, Callable

from .oar_014_umd_market_correlation_handoff import (
    UMDMarketCorrelationRequest,
)

BUILD_ID = "OAR-019"
OAR_019_REVISION = "OAR_019_EXACT_UMD_MARKET_IDENTITY_BINDING_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False

TARGET_MODULE = (
    "qseries_v2.universal_market_discovery."
    "umd_095_market_identity"
)
TARGET_CLASS = "CanonicalMarketIdentityResolver"

PREFERRED_METHODS = (
    "resolve",
    "resolve_market",
    "resolve_identity",
    "canonicalize",
)


@dataclass(frozen=True, slots=True)
class ExactUMDBinding:
    module_name: str
    class_name: str
    callable_name: str
    read_only: bool


class ExactUMDMarketIdentityBinding:
    read_only = True
    execution_allowed = False
    persistence_allowed = False
    publication_allowed = False

    def resolve_binding(self) -> ExactUMDBinding:
        module = importlib.import_module(
            TARGET_MODULE
        )

        target_class = getattr(
            module,
            TARGET_CLASS,
            None,
        )

        if target_class is None:
            raise RuntimeError(
                f"Certified UMD target class missing: "
                f"{TARGET_CLASS}"
            )

        if not inspect.isclass(
            target_class
        ):
            raise TypeError(
                "Certified UMD target is not a class"
            )

        callable_name = None

        for name in PREFERRED_METHODS:
            candidate = getattr(
                target_class,
                name,
                None,
            )

            if callable(candidate):
                callable_name = name
                break

        if callable_name is None:
            public = [
                name
                for name, value
                in inspect.getmembers(
                    target_class
                )
                if (
                    callable(value)
                    and not name.startswith("_")
                )
            ]

            if len(public) == 1:
                callable_name = public[0]
            else:
                raise RuntimeError(
                    "Unable to resolve exact callable "
                    "on CanonicalMarketIdentityResolver"
                )

        return ExactUMDBinding(
            module_name=TARGET_MODULE,
            class_name=TARGET_CLASS,
            callable_name=callable_name,
            read_only=True,
        )

    def validate_request(
        self,
        request: UMDMarketCorrelationRequest,
    ) -> bool:
        if not isinstance(
            request,
            UMDMarketCorrelationRequest,
        ):
            raise TypeError(
                "request must be UMDMarketCorrelationRequest"
            )

        if (
            request.market_identity_required
            is not True
        ):
            raise ValueError(
                "market identity resolution must be required"
            )

        if request.read_only is not True:
            raise ValueError(
                "UMD request must be read-only"
            )

        return True


def verify_exact_umd_market_identity_binding() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert PERSISTENCE_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    return True
