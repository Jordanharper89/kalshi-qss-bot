from __future__ import annotations

import importlib
import inspect
from dataclasses import dataclass

from .oar_015_oml_memory_intake_handoff import (
    OMLMemoryIntakeRequest,
)

BUILD_ID = "OAR-020"
OAR_020_REVISION = (
    "OAR_020_EXACT_OML_OBSERVATION_INTAKE_BINDING_V1"
)

READ_ONLY = True
EXECUTION_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False

TARGET_CLASS = (
    "OracleMemoryCertifiedMarketBehavior"
    "ObservationIntakeBinding"
)

PREFERRED_METHODS = (
    "bind",
    "build",
    "admit",
    "intake",
    "consume",
    "project",
)


@dataclass(frozen=True, slots=True)
class ExactOMLBinding:
    module_name: str
    class_name: str
    binding_mode: str
    callable_name: str
    public_methods: tuple[str, ...]
    read_only: bool


class ExactOMLObservationIntakeBinding:
    read_only = True
    execution_allowed = False
    persistence_allowed = False
    publication_allowed = False

    def resolve_binding(
        self,
        module_name: str,
    ) -> ExactOMLBinding:
        module = importlib.import_module(
            module_name
        )

        target_class = getattr(
            module,
            TARGET_CLASS,
            None,
        )

        if target_class is None:
            raise RuntimeError(
                "Certified OML target class missing"
            )

        if not inspect.isclass(
            target_class
        ):
            raise TypeError(
                "Certified OML target is not a class"
            )

        public_methods = tuple(
            sorted(
                name
                for name, value
                in inspect.getmembers(
                    target_class
                )
                if (
                    callable(value)
                    and not name.startswith("_")
                )
            )
        )

        callable_name = None

        for name in PREFERRED_METHODS:
            if name in public_methods:
                callable_name = name
                break

        if callable_name is not None:
            binding_mode = "public_method"
        else:
            # The certified OML object can legitimately be a pure
            # immutable binding/data contract with no public methods.
            # In that case the exact class constructor itself is the
            # certified boundary. Do not invent a method or mutate OML.
            binding_mode = "constructor_contract"
            callable_name = "__init__"

        return ExactOMLBinding(
            module_name=module_name,
            class_name=TARGET_CLASS,
            binding_mode=binding_mode,
            callable_name=callable_name,
            public_methods=public_methods,
            read_only=True,
        )

    def validate_request(
        self,
        request: OMLMemoryIntakeRequest,
    ) -> bool:
        if not isinstance(
            request,
            OMLMemoryIntakeRequest,
        ):
            raise TypeError(
                "request must be OMLMemoryIntakeRequest"
            )

        if (
            request
            .requires_market_identity_resolution
            is not True
        ):
            raise ValueError(
                "market identity resolution required"
            )

        if (
            request
            .requires_evidence_lineage_preservation
            is not True
        ):
            raise ValueError(
                "evidence lineage preservation required"
            )

        if (
            request
            .requires_contradiction_preservation
            is not True
        ):
            raise ValueError(
                "contradiction preservation required"
            )

        if request.read_only is not True:
            raise ValueError(
                "OML request must be read-only"
            )

        return True


def verify_exact_oml_observation_intake_binding() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert PERSISTENCE_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    return True


__all__ = [
    "BUILD_ID",
    "OAR_020_REVISION",
    "TARGET_CLASS",
    "ExactOMLBinding",
    "ExactOMLObservationIntakeBinding",
    "verify_exact_oml_observation_intake_binding",
]
