
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any, Dict, Mapping, Optional, Tuple

from .market_regime_pipeline_gate import (
    MarketRegimePipelineGateResult,
    validate_market_regime_pipeline_gate,
)


READ_ONLY = True
SCHEMA_VERSION = "RGD-005"

ENGINE_ID = (
    "oracle.discovery.market_regime."
    "registry_bridge"
)

REGISTRY_NAMESPACE = (
    "oracle.discovery.market_regime"
)

REGISTRY_ENTRY_ID = (
    "oracle.discovery.market_regime."
    "subsystem"
)

REGISTRY_STATUSES = frozenset(
    {
        "registered",
        "empty",
        "rejected",
    }
)

SUBSYSTEM_CAPABILITIES = (
    "market_regime_signal_normalization",
    "market_regime_classification",
    "market_regime_transition_detection",
    "market_regime_evidence_attribution",
    "deterministic_replay",
    "read_only_discovery",
)

SUBSYSTEM_MODULES = (
    "RGD-001",
    "RGD-002",
    "RGD-003",
    "RGD-004",
    "RGD-005",
)


def _stable_value(
    value: Any,
) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _stable_value(value[key])
            for key in sorted(
                value.keys(),
                key=str,
            )
        }

    if isinstance(value, tuple):
        return tuple(
            _stable_value(item)
            for item in value
        )

    if isinstance(value, list):
        return tuple(
            _stable_value(item)
            for item in value
        )

    if isinstance(value, set):
        return tuple(
            sorted(
                (
                    _stable_value(item)
                    for item in value
                ),
                key=repr,
            )
        )

    if hasattr(value, "as_dict") and callable(
        value.as_dict
    ):
        return _stable_value(
            value.as_dict()
        )

    return value


def _stable_hash(
    value: Any,
) -> str:
    return sha256(
        repr(
            _stable_value(value)
        ).encode("utf-8")
    ).hexdigest()


def _normalize_metadata(
    metadata: Optional[
        Mapping[str, Any]
    ],
) -> Tuple[
    Tuple[str, Any],
    ...,
]:
    if metadata is None:
        return tuple()

    if not isinstance(metadata, Mapping):
        raise TypeError(
            "metadata must be a mapping"
        )

    return tuple(
        (
            str(key),
            _stable_value(value),
        )
        for key, value in sorted(
            metadata.items(),
            key=lambda item: str(
                item[0]
            ),
        )
    )


def _metadata_dict(
    metadata: Tuple[
        Tuple[str, Any],
        ...,
    ],
) -> Dict[str, Any]:
    return {
        str(key): _stable_value(value)
        for key, value in metadata
    }


@dataclass(frozen=True)
class MarketRegimeRegistryDescriptor:
    registry_entry_id: str
    namespace: str
    subsystem_name: str
    subsystem_version: str
    contract_schema_version: str
    source_adapter_schema_version: str
    discovery_engine_schema_version: str
    pipeline_gate_schema_version: str
    registry_bridge_schema_version: str
    capabilities: Tuple[str, ...]
    modules: Tuple[str, ...]
    read_only: bool
    deterministic: bool
    replayable: bool
    explainable: bool
    auditable: bool
    descriptor_hash: str

    def __post_init__(self) -> None:
        required = {
            "registry_entry_id": (
                self.registry_entry_id
            ),
            "namespace": self.namespace,
            "subsystem_name": (
                self.subsystem_name
            ),
            "subsystem_version": (
                self.subsystem_version
            ),
            "contract_schema_version": (
                self.contract_schema_version
            ),
            "source_adapter_schema_version": (
                self.source_adapter_schema_version
            ),
            "discovery_engine_schema_version": (
                self.discovery_engine_schema_version
            ),
            "pipeline_gate_schema_version": (
                self.pipeline_gate_schema_version
            ),
            "registry_bridge_schema_version": (
                self.registry_bridge_schema_version
            ),
            "descriptor_hash": (
                self.descriptor_hash
            ),
        }

        for field_name, value in required.items():
            if not str(value).strip():
                raise ValueError(
                    f"{field_name} must not "
                    "be empty"
                )

        if self.read_only is not True:
            raise ValueError(
                "registry descriptor must be "
                "read-only"
            )

        if self.deterministic is not True:
            raise ValueError(
                "registry descriptor must be "
                "deterministic"
            )

        if self.replayable is not True:
            raise ValueError(
                "registry descriptor must be "
                "replayable"
            )

        if self.explainable is not True:
            raise ValueError(
                "registry descriptor must be "
                "explainable"
            )

        if self.auditable is not True:
            raise ValueError(
                "registry descriptor must be "
                "auditable"
            )

        if not self.capabilities:
            raise ValueError(
                "capabilities must not be empty"
            )

        if len(self.capabilities) != len(
            set(self.capabilities)
        ):
            raise ValueError(
                "capabilities must be unique"
            )

        if not self.modules:
            raise ValueError(
                "modules must not be empty"
            )

        if len(self.modules) != len(
            set(self.modules)
        ):
            raise ValueError(
                "modules must be unique"
            )

    def payload(self) -> Dict[str, Any]:
        return {
            "registry_entry_id": (
                self.registry_entry_id
            ),
            "namespace": self.namespace,
            "subsystem_name": (
                self.subsystem_name
            ),
            "subsystem_version": (
                self.subsystem_version
            ),
            "contract_schema_version": (
                self.contract_schema_version
            ),
            "source_adapter_schema_version": (
                self.source_adapter_schema_version
            ),
            "discovery_engine_schema_version": (
                self.discovery_engine_schema_version
            ),
            "pipeline_gate_schema_version": (
                self.pipeline_gate_schema_version
            ),
            "registry_bridge_schema_version": (
                self.registry_bridge_schema_version
            ),
            "capabilities": (
                self.capabilities
            ),
            "modules": self.modules,
            "read_only": self.read_only,
            "deterministic": (
                self.deterministic
            ),
            "replayable": self.replayable,
            "explainable": self.explainable,
            "auditable": self.auditable,
        }

    def as_dict(self) -> Dict[str, Any]:
        payload = self.payload()

        payload["descriptor_hash"] = (
            self.descriptor_hash
        )

        return payload

    def verify_descriptor_hash(self) -> bool:
        return (
            self.descriptor_hash
            == _stable_hash(
                self.payload()
            )
        )


@dataclass(frozen=True)
class MarketRegimeRegistryBridgeResult:
    schema_version: str
    engine_id: str
    status: str
    accepted: bool
    observed_at: str
    registry_namespace: str
    registration_count: int
    registrations: Tuple[
        MarketRegimeRegistryDescriptor,
        ...,
    ]
    pipeline_gate_schema_version: str
    pipeline_gate_engine_id: str
    pipeline_gate_status: str
    pipeline_gate_hash: str
    rejection_reasons: Tuple[str, ...]
    metadata: Tuple[
        Tuple[str, Any],
        ...,
    ] = field(
        default_factory=tuple
    )
    result_hash: str = ""
    read_only: bool = True

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(
                "invalid registry bridge "
                "schema_version"
            )

        if self.engine_id != ENGINE_ID:
            raise ValueError(
                "invalid registry bridge "
                "engine_id"
            )

        if self.status not in REGISTRY_STATUSES:
            raise ValueError(
                "invalid registry bridge "
                "status"
            )

        if not str(self.observed_at).strip():
            raise ValueError(
                "observed_at must not be empty"
            )

        if (
            self.registry_namespace
            != REGISTRY_NAMESPACE
        ):
            raise ValueError(
                "invalid registry namespace"
            )

        if self.registration_count < 0:
            raise ValueError(
                "registration_count cannot "
                "be negative"
            )

        if self.registration_count != len(
            self.registrations
        ):
            raise ValueError(
                "registration_count does not "
                "match registrations"
            )

        if self.read_only is not True:
            raise ValueError(
                "registry bridge result must "
                "be read-only"
            )

        registration_ids = [
            registration.registry_entry_id
            for registration
            in self.registrations
        ]

        if len(registration_ids) != len(
            set(registration_ids)
        ):
            raise ValueError(
                "registry entry identifiers "
                "must be unique"
            )

        if self.accepted:
            if self.status not in {
                "registered",
                "empty",
            }:
                raise ValueError(
                    "accepted bridge must be "
                    "registered or empty"
                )

            if self.rejection_reasons:
                raise ValueError(
                    "accepted bridge cannot "
                    "contain rejection reasons"
                )

            if self.registration_count != 1:
                raise ValueError(
                    "accepted bridge must "
                    "contain one registration"
                )

        else:
            if self.status != "rejected":
                raise ValueError(
                    "rejected bridge must have "
                    "rejected status"
                )

            if not self.rejection_reasons:
                raise ValueError(
                    "rejected bridge must "
                    "contain rejection reasons"
                )

            if self.registration_count != 0:
                raise ValueError(
                    "rejected bridge cannot "
                    "contain registrations"
                )

        if not str(
            self.pipeline_gate_hash
        ).strip():
            raise ValueError(
                "pipeline_gate_hash must not "
                "be empty"
            )

        if not str(self.result_hash).strip():
            raise ValueError(
                "result_hash must not be empty"
            )

        normalized_metadata = tuple(
            sorted(
                (
                    (
                        str(key),
                        _stable_value(value),
                    )
                    for key, value
                    in self.metadata
                ),
                key=lambda item: item[0],
            )
        )

        object.__setattr__(
            self,
            "metadata",
            normalized_metadata,
        )

    def payload(self) -> Dict[str, Any]:
        return {
            "schema_version": (
                self.schema_version
            ),
            "engine_id": self.engine_id,
            "status": self.status,
            "accepted": self.accepted,
            "observed_at": self.observed_at,
            "registry_namespace": (
                self.registry_namespace
            ),
            "registration_count": (
                self.registration_count
            ),
            "registrations": tuple(
                registration.as_dict()
                for registration
                in self.registrations
            ),
            "pipeline_gate_schema_version": (
                self.pipeline_gate_schema_version
            ),
            "pipeline_gate_engine_id": (
                self.pipeline_gate_engine_id
            ),
            "pipeline_gate_status": (
                self.pipeline_gate_status
            ),
            "pipeline_gate_hash": (
                self.pipeline_gate_hash
            ),
            "rejection_reasons": (
                self.rejection_reasons
            ),
            "metadata": _metadata_dict(
                self.metadata
            ),
            "read_only": self.read_only,
        }

    def as_dict(self) -> Dict[str, Any]:
        payload = self.payload()

        payload["result_hash"] = (
            self.result_hash
        )

        return payload

    def verify_result_hash(self) -> bool:
        return (
            self.result_hash
            == _stable_hash(
                self.payload()
            )
        )


def build_market_regime_registry_descriptor(
) -> MarketRegimeRegistryDescriptor:
    payload = {
        "registry_entry_id": (
            REGISTRY_ENTRY_ID
        ),
        "namespace": REGISTRY_NAMESPACE,
        "subsystem_name": (
            "Market Regime Discovery"
        ),
        "subsystem_version": "1.0.0",
        "contract_schema_version": (
            "RGD-001"
        ),
        "source_adapter_schema_version": (
            "RGD-002"
        ),
        "discovery_engine_schema_version": (
            "RGD-003"
        ),
        "pipeline_gate_schema_version": (
            "RGD-004"
        ),
        "registry_bridge_schema_version": (
            "RGD-005"
        ),
        "capabilities": tuple(
            sorted(
                SUBSYSTEM_CAPABILITIES
            )
        ),
        "modules": tuple(
            sorted(
                SUBSYSTEM_MODULES
            )
        ),
        "read_only": True,
        "deterministic": True,
        "replayable": True,
        "explainable": True,
        "auditable": True,
    }

    descriptor = (
        MarketRegimeRegistryDescriptor(
            registry_entry_id=(
                payload[
                    "registry_entry_id"
                ]
            ),
            namespace=payload["namespace"],
            subsystem_name=(
                payload["subsystem_name"]
            ),
            subsystem_version=(
                payload["subsystem_version"]
            ),
            contract_schema_version=(
                payload[
                    "contract_schema_version"
                ]
            ),
            source_adapter_schema_version=(
                payload[
                    "source_adapter_schema_version"
                ]
            ),
            discovery_engine_schema_version=(
                payload[
                    "discovery_engine_schema_version"
                ]
            ),
            pipeline_gate_schema_version=(
                payload[
                    "pipeline_gate_schema_version"
                ]
            ),
            registry_bridge_schema_version=(
                payload[
                    "registry_bridge_schema_version"
                ]
            ),
            capabilities=(
                payload["capabilities"]
            ),
            modules=payload["modules"],
            read_only=True,
            deterministic=True,
            replayable=True,
            explainable=True,
            auditable=True,
            descriptor_hash=_stable_hash(
                payload
            ),
        )
    )

    if not descriptor.verify_descriptor_hash():
        raise AssertionError(
            "registry descriptor produced "
            "an invalid hash"
        )

    return descriptor


def bridge_market_regime_to_registry(
    pipeline_gate_result: (
        MarketRegimePipelineGateResult
    ),
    observed_at: Optional[str] = None,
    metadata: Optional[
        Mapping[str, Any]
    ] = None,
) -> MarketRegimeRegistryBridgeResult:
    if not isinstance(
        pipeline_gate_result,
        MarketRegimePipelineGateResult,
    ):
        raise TypeError(
            "pipeline_gate_result must be a "
            "MarketRegimePipelineGateResult"
        )

    validation = (
        validate_market_regime_pipeline_gate(
            pipeline_gate_result
        )
    )

    resolved_observed_at = str(
        observed_at
        if observed_at is not None
        else pipeline_gate_result.observed_at
    ).strip()

    if not resolved_observed_at:
        raise ValueError(
            "observed_at must not be empty"
        )

    rejection_reasons = []

    if validation["accepted"] is not True:
        rejection_reasons.append(
            "invalid_pipeline_gate_result"
        )

    if (
        pipeline_gate_result
        .verify_gate_hash()
        is not True
    ):
        rejection_reasons.append(
            "invalid_pipeline_gate_hash"
        )

    if (
        pipeline_gate_result.read_only
        is not True
    ):
        rejection_reasons.append(
            "pipeline_gate_not_read_only"
        )

    if (
        pipeline_gate_result.accepted
        is not True
    ):
        rejection_reasons.append(
            "pipeline_gate_rejected"
        )

    normalized_rejections = tuple(
        sorted(
            set(rejection_reasons)
        )
    )

    if normalized_rejections:
        status = "rejected"
        accepted = False
        registrations = tuple()
    else:
        accepted = True

        if (
            pipeline_gate_result.status
            == "empty"
        ):
            status = "empty"
        else:
            status = "registered"

        registrations = (
            build_market_regime_registry_descriptor(),
        )

    bridge_metadata = {
        "bridge_mode": (
            "read_only_registration_projection"
        ),
        "external_state_mutated": False,
        "registry_write_performed": False,
        "pipeline_gate_accepted": (
            pipeline_gate_result.accepted
        ),
        "pipeline_gate_check_count": len(
            pipeline_gate_result.checks
        ),
        "source_record_count": (
            pipeline_gate_result
            .source_record_count
        ),
        "opportunity_count": (
            pipeline_gate_result
            .opportunity_count
        ),
        "deterministic": True,
        "immutable": True,
        "replayable": True,
        "explainable": True,
        "auditable": True,
        "read_only": True,
    }

    if metadata:
        for key, value in metadata.items():
            bridge_metadata[str(key)] = (
                _stable_value(value)
            )

    normalized_metadata = _normalize_metadata(
        bridge_metadata
    )

    payload = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "status": status,
        "accepted": accepted,
        "observed_at": (
            resolved_observed_at
        ),
        "registry_namespace": (
            REGISTRY_NAMESPACE
        ),
        "registration_count": len(
            registrations
        ),
        "registrations": tuple(
            registration.as_dict()
            for registration
            in registrations
        ),
        "pipeline_gate_schema_version": (
            pipeline_gate_result
            .schema_version
        ),
        "pipeline_gate_engine_id": (
            pipeline_gate_result.engine_id
        ),
        "pipeline_gate_status": (
            pipeline_gate_result.status
        ),
        "pipeline_gate_hash": (
            pipeline_gate_result.gate_hash
        ),
        "rejection_reasons": (
            normalized_rejections
        ),
        "metadata": _metadata_dict(
            normalized_metadata
        ),
        "read_only": True,
    }

    result = MarketRegimeRegistryBridgeResult(
        schema_version=SCHEMA_VERSION,
        engine_id=ENGINE_ID,
        status=status,
        accepted=accepted,
        observed_at=resolved_observed_at,
        registry_namespace=(
            REGISTRY_NAMESPACE
        ),
        registration_count=len(
            registrations
        ),
        registrations=registrations,
        pipeline_gate_schema_version=(
            pipeline_gate_result
            .schema_version
        ),
        pipeline_gate_engine_id=(
            pipeline_gate_result.engine_id
        ),
        pipeline_gate_status=(
            pipeline_gate_result.status
        ),
        pipeline_gate_hash=(
            pipeline_gate_result.gate_hash
        ),
        rejection_reasons=(
            normalized_rejections
        ),
        metadata=normalized_metadata,
        result_hash=_stable_hash(
            payload
        ),
        read_only=True,
    )

    if not result.verify_result_hash():
        raise AssertionError(
            "registry bridge produced an "
            "invalid deterministic hash"
        )

    return result


def run_market_regime_registry_bridge(
    pipeline_gate_result: (
        MarketRegimePipelineGateResult
    ),
    observed_at: Optional[str] = None,
    metadata: Optional[
        Mapping[str, Any]
    ] = None,
) -> MarketRegimeRegistryBridgeResult:
    return bridge_market_regime_to_registry(
        pipeline_gate_result=(
            pipeline_gate_result
        ),
        observed_at=observed_at,
        metadata=metadata,
    )


def validate_market_regime_registry_bridge(
    result: Any,
) -> Dict[str, Any]:
    checks = {
        "result_type": isinstance(
            result,
            MarketRegimeRegistryBridgeResult,
        ),
        "schema_version": (
            getattr(
                result,
                "schema_version",
                None,
            )
            == SCHEMA_VERSION
        ),
        "engine_id": (
            getattr(
                result,
                "engine_id",
                None,
            )
            == ENGINE_ID
        ),
        "status": (
            getattr(
                result,
                "status",
                None,
            )
            in REGISTRY_STATUSES
        ),
        "namespace": (
            getattr(
                result,
                "registry_namespace",
                None,
            )
            == REGISTRY_NAMESPACE
        ),
        "read_only": (
            getattr(
                result,
                "read_only",
                None,
            )
            is True
        ),
        "hash_valid": (
            isinstance(
                result,
                MarketRegimeRegistryBridgeResult,
            )
            and result.verify_result_hash()
        ),
        "descriptor_hashes_valid": (
            isinstance(
                result,
                MarketRegimeRegistryBridgeResult,
            )
            and all(
                descriptor
                .verify_descriptor_hash()
                for descriptor
                in result.registrations
            )
        ),
    }

    return {
        "accepted": all(
            checks.values()
        ),
        "checks": checks,
    }


def assert_market_regime_registry_read_only(
    result: MarketRegimeRegistryBridgeResult,
) -> bool:
    if not isinstance(
        result,
        MarketRegimeRegistryBridgeResult,
    ):
        raise TypeError(
            "result must be a "
            "MarketRegimeRegistryBridgeResult"
        )

    if READ_ONLY is not True:
        raise AssertionError(
            "market regime registry bridge "
            "must be read-only"
        )

    if result.read_only is not True:
        raise AssertionError(
            "registry bridge result must be "
            "read-only"
        )

    metadata = _metadata_dict(
        result.metadata
    )

    if (
        metadata.get(
            "external_state_mutated"
        )
        is not False
    ):
        raise AssertionError(
            "registry bridge cannot mutate "
            "external state"
        )

    if (
        metadata.get(
            "registry_write_performed"
        )
        is not False
    ):
        raise AssertionError(
            "registry bridge cannot perform "
            "registry writes"
        )

    return True


__all__ = [
    "READ_ONLY",
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "REGISTRY_NAMESPACE",
    "REGISTRY_ENTRY_ID",
    "REGISTRY_STATUSES",
    "SUBSYSTEM_CAPABILITIES",
    "SUBSYSTEM_MODULES",
    "MarketRegimeRegistryDescriptor",
    "MarketRegimeRegistryBridgeResult",
    "build_market_regime_registry_descriptor",
    "bridge_market_regime_to_registry",
    "run_market_regime_registry_bridge",
    "validate_market_regime_registry_bridge",
    "assert_market_regime_registry_read_only",
]
