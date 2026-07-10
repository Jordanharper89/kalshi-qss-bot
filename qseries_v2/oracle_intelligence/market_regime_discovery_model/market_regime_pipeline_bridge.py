
from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from hashlib import sha256
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from .market_regime_discovery_contract import (
    MarketRegimeDiscoveryResult,
    validate_market_regime_discovery_result,
)

from .market_regime_discovery_engine import (
    MarketRegimeEngineConfig,
    discover_market_regimes,
)

from .market_regime_pipeline_gate import (
    MarketRegimePipelineGateResult,
    evaluate_market_regime_pipeline,
    validate_market_regime_pipeline_gate,
)

from .market_regime_registry_bridge import (
    MarketRegimeRegistryBridgeResult,
    bridge_market_regime_to_registry,
    validate_market_regime_registry_bridge,
)


READ_ONLY = True
SCHEMA_VERSION = "RGD-006"

ENGINE_ID = (
    "oracle.discovery.market_regime."
    "pipeline_bridge"
)

PIPELINE_STATUSES = frozenset(
    {
        "completed",
        "empty",
        "rejected",
    }
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


def _artifact_dict(
    value: Any,
) -> Dict[str, Any]:
    if isinstance(value, Mapping):
        return {
            str(key): _stable_value(item)
            for key, item in sorted(
                value.items(),
                key=lambda pair: str(
                    pair[0]
                ),
            )
        }

    if hasattr(value, "as_dict") and callable(
        value.as_dict
    ):
        result = value.as_dict()

        if not isinstance(result, Mapping):
            raise TypeError(
                "as_dict() must return a mapping"
            )

        return {
            str(key): _stable_value(item)
            for key, item in sorted(
                result.items(),
                key=lambda pair: str(
                    pair[0]
                ),
            )
        }

    if is_dataclass(value):
        result = asdict(value)

        return {
            str(key): _stable_value(item)
            for key, item in sorted(
                result.items(),
                key=lambda pair: str(
                    pair[0]
                ),
            )
        }

    raise TypeError(
        "artifact must be a mapping, "
        "dataclass, or expose as_dict()"
    )


def _read_value(
    value: Any,
    key: str,
    default: Any = None,
) -> Any:
    if isinstance(value, Mapping):
        return value.get(
            key,
            default,
        )

    return getattr(
        value,
        key,
        default,
    )


def _first_value(
    value: Any,
    keys: Sequence[str],
    default: Any = None,
) -> Any:
    for key in keys:
        result = _read_value(
            value,
            key,
            None,
        )

        if result is not None:
            return result

    return default


def _extract_records(
    source_result: Any,
) -> Tuple[Any, ...]:
    records = _first_value(
        source_result,
        (
            "records",
            "signals",
            "items",
            "observations",
            "source_records",
        ),
        tuple(),
    )

    if records is None:
        return tuple()

    return tuple(records)



def _canonical_source_payload(
    source_result: Any,
) -> Dict[str, Any]:
    try:
        payload = _artifact_dict(
            source_result
        )
    except TypeError:
        payload = {
            "value": _stable_value(
                source_result
            )
        }

    records = _extract_records(
        source_result
    )

    if records:
        canonical_records = tuple(
            sorted(
                (
                    _stable_value(record)
                    for record in records
                ),
                key=repr,
            )
        )

        for key in (
            "records",
            "signals",
            "items",
            "observations",
            "source_records",
        ):
            if key in payload:
                payload[key] = (
                    canonical_records
                )
                break

    return {
        str(key): _stable_value(value)
        for key, value in sorted(
            payload.items(),
            key=lambda item: str(
                item[0]
            ),
        )
    }



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


def _resolve_observed_at(
    source_result: Any,
    observed_at: Optional[str],
) -> str:
    if observed_at is not None:
        resolved = str(observed_at).strip()

        if not resolved:
            raise ValueError(
                "observed_at must not be empty"
            )

        return resolved

    source_time = _first_value(
        source_result,
        (
            "observed_at",
            "generated_at",
            "as_of",
            "captured_at",
        ),
        None,
    )

    if source_time is not None:
        resolved = str(source_time).strip()

        if resolved:
            return resolved

    timestamps = sorted(
        {
            str(
                _first_value(
                    record,
                    (
                        "observed_at",
                        "timestamp",
                        "as_of",
                        "captured_at",
                    ),
                    "",
                )
            ).strip()
            for record in _extract_records(
                source_result
            )
            if str(
                _first_value(
                    record,
                    (
                        "observed_at",
                        "timestamp",
                        "as_of",
                        "captured_at",
                    ),
                    "",
                )
            ).strip()
        }
    )

    if timestamps:
        return timestamps[-1]

    return "1970-01-01T00:00:00+00:00"


@dataclass(frozen=True)
class MarketRegimePipelineStage:
    stage_id: str
    schema_version: str
    engine_id: str
    status: str
    accepted: bool
    artifact_hash: str
    input_hash: str
    output_count: int
    read_only: bool
    details: Tuple[
        Tuple[str, Any],
        ...,
    ] = field(
        default_factory=tuple
    )

    def __post_init__(self) -> None:
        required = {
            "stage_id": self.stage_id,
            "schema_version": (
                self.schema_version
            ),
            "engine_id": self.engine_id,
            "status": self.status,
            "artifact_hash": (
                self.artifact_hash
            ),
            "input_hash": self.input_hash,
        }

        for field_name, value in required.items():
            if not str(value).strip():
                raise ValueError(
                    f"{field_name} must not "
                    "be empty"
                )

        if self.output_count < 0:
            raise ValueError(
                "output_count cannot be "
                "negative"
            )

        if self.read_only is not True:
            raise ValueError(
                "pipeline stage must be "
                "read-only"
            )

        normalized_details = tuple(
            sorted(
                (
                    (
                        str(key),
                        _stable_value(value),
                    )
                    for key, value
                    in self.details
                ),
                key=lambda item: item[0],
            )
        )

        object.__setattr__(
            self,
            "details",
            normalized_details,
        )

    def as_dict(self) -> Dict[str, Any]:
        return {
            "stage_id": self.stage_id,
            "schema_version": (
                self.schema_version
            ),
            "engine_id": self.engine_id,
            "status": self.status,
            "accepted": self.accepted,
            "artifact_hash": (
                self.artifact_hash
            ),
            "input_hash": self.input_hash,
            "output_count": (
                self.output_count
            ),
            "read_only": self.read_only,
            "details": {
                key: _stable_value(value)
                for key, value
                in self.details
            },
        }


@dataclass(frozen=True)
class MarketRegimePipelineBridgeResult:
    schema_version: str
    engine_id: str
    status: str
    accepted: bool
    observed_at: str
    source_schema_version: str
    source_engine_id: str
    source_status: str
    source_record_count: int
    discovery_result: (
        MarketRegimeDiscoveryResult
    )
    gate_result: (
        MarketRegimePipelineGateResult
    )
    registry_result: (
        MarketRegimeRegistryBridgeResult
    )
    stages: Tuple[
        MarketRegimePipelineStage,
        ...,
    ]
    rejection_reasons: Tuple[str, ...]
    metadata: Tuple[
        Tuple[str, Any],
        ...,
    ] = field(
        default_factory=tuple
    )
    pipeline_hash: str = ""
    read_only: bool = True

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(
                "invalid pipeline bridge "
                "schema_version"
            )

        if self.engine_id != ENGINE_ID:
            raise ValueError(
                "invalid pipeline bridge "
                "engine_id"
            )

        if self.status not in PIPELINE_STATUSES:
            raise ValueError(
                "invalid pipeline bridge "
                "status"
            )

        if not str(self.observed_at).strip():
            raise ValueError(
                "observed_at must not be empty"
            )

        if self.source_record_count < 0:
            raise ValueError(
                "source_record_count cannot "
                "be negative"
            )

        if self.read_only is not True:
            raise ValueError(
                "pipeline bridge result must "
                "be read-only"
            )

        if not isinstance(
            self.discovery_result,
            MarketRegimeDiscoveryResult,
        ):
            raise TypeError(
                "discovery_result must be a "
                "MarketRegimeDiscoveryResult"
            )

        if not isinstance(
            self.gate_result,
            MarketRegimePipelineGateResult,
        ):
            raise TypeError(
                "gate_result must be a "
                "MarketRegimePipelineGateResult"
            )

        if not isinstance(
            self.registry_result,
            MarketRegimeRegistryBridgeResult,
        ):
            raise TypeError(
                "registry_result must be a "
                "MarketRegimeRegistryBridgeResult"
            )

        stage_ids = [
            stage.stage_id
            for stage in self.stages
        ]

        if len(stage_ids) != len(
            set(stage_ids)
        ):
            raise ValueError(
                "pipeline stage identifiers "
                "must be unique"
            )

        if len(self.stages) != 3:
            raise ValueError(
                "pipeline bridge must contain "
                "exactly three stages"
            )

        if self.accepted:
            if self.status not in {
                "completed",
                "empty",
            }:
                raise ValueError(
                    "accepted pipeline must be "
                    "completed or empty"
                )

            if self.rejection_reasons:
                raise ValueError(
                    "accepted pipeline cannot "
                    "contain rejection reasons"
                )

            if not all(
                stage.accepted
                for stage in self.stages
            ):
                raise ValueError(
                    "accepted pipeline requires "
                    "all stages accepted"
                )

        else:
            if self.status != "rejected":
                raise ValueError(
                    "rejected pipeline must "
                    "have rejected status"
                )

            if not self.rejection_reasons:
                raise ValueError(
                    "rejected pipeline must "
                    "contain rejection reasons"
                )

        if not str(self.pipeline_hash).strip():
            raise ValueError(
                "pipeline_hash must not be "
                "empty"
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

    @property
    def opportunity_count(self) -> int:
        return (
            self.discovery_result
            .opportunity_count
        )

    @property
    def registration_count(self) -> int:
        return (
            self.registry_result
            .registration_count
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
            "source_schema_version": (
                self.source_schema_version
            ),
            "source_engine_id": (
                self.source_engine_id
            ),
            "source_status": (
                self.source_status
            ),
            "source_record_count": (
                self.source_record_count
            ),
            "discovery_result": (
                _artifact_dict(self.discovery_result)
            ),
            "gate_result": (
                _artifact_dict(self.gate_result)
            ),
            "registry_result": (
                _artifact_dict(self.registry_result)
            ),
            "stages": tuple(
                stage.as_dict()
                for stage in self.stages
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

        payload["pipeline_hash"] = (
            self.pipeline_hash
        )

        payload["opportunity_count"] = (
            self.opportunity_count
        )

        payload["registration_count"] = (
            self.registration_count
        )

        return payload

    def verify_pipeline_hash(self) -> bool:
        return (
            self.pipeline_hash
            == _stable_hash(
                self.payload()
            )
        )


def _build_stage(
    stage_id: str,
    schema_version: str,
    engine_id: str,
    status: str,
    accepted: bool,
    artifact_hash: str,
    input_hash: str,
    output_count: int,
    details: Optional[
        Mapping[str, Any]
    ] = None,
) -> MarketRegimePipelineStage:
    return MarketRegimePipelineStage(
        stage_id=stage_id,
        schema_version=schema_version,
        engine_id=engine_id,
        status=status,
        accepted=accepted,
        artifact_hash=artifact_hash,
        input_hash=input_hash,
        output_count=output_count,
        read_only=True,
        details=_normalize_metadata(
            details or {}
        ),
    )


def run_market_regime_pipeline(
    source_result: Any,
    observed_at: Optional[str] = None,
    config: Optional[
        MarketRegimeEngineConfig
    ] = None,
    metadata: Optional[
        Mapping[str, Any]
    ] = None,
) -> MarketRegimePipelineBridgeResult:
    if source_result is None:
        raise TypeError(
            "source_result must not be None"
        )

    resolved_observed_at = (
        _resolve_observed_at(
            source_result=source_result,
            observed_at=observed_at,
        )
    )

    source_records = _extract_records(
        source_result
    )

    source_schema_version = str(
        _first_value(
            source_result,
            ("schema_version",),
            "unknown",
        )
    )

    source_engine_id = str(
        _first_value(
            source_result,
            ("engine_id",),
            "unknown",
        )
    )

    source_status = str(
        _first_value(
            source_result,
            ("status",),
            "unknown",
        )
    )

    source_payload = (
        _canonical_source_payload(
            source_result
        )
    )

    source_hash = str(
        _first_value(
            source_result,
            (
                "source_hash",
                "result_hash",
                "adapter_hash",
            ),
            "",
        )
    ).strip()

    if not source_hash:
        source_hash = _stable_hash(
            source_payload
        )

    discovery_result = discover_market_regimes(
        source_result=source_result,
        observed_at=resolved_observed_at,
        config=config,
    )

    discovery_validation = (
        validate_market_regime_discovery_result(
            discovery_result
        )
    )

    gate_result = (
        evaluate_market_regime_pipeline(
            source_result=source_result,
            discovery_result=(
                discovery_result
            ),
            observed_at=resolved_observed_at,
            config=config,
        )
    )

    gate_validation = (
        validate_market_regime_pipeline_gate(
            gate_result
        )
    )

    registry_result = (
        bridge_market_regime_to_registry(
            pipeline_gate_result=gate_result,
            observed_at=resolved_observed_at,
            metadata={
                "pipeline_bridge_schema": (
                    SCHEMA_VERSION
                ),
                "pipeline_bridge_engine": (
                    ENGINE_ID
                ),
            },
        )
    )

    registry_validation = (
        validate_market_regime_registry_bridge(
            registry_result
        )
    )

    discovery_accepted = (
        discovery_validation["accepted"]
        is True
    )

    gate_accepted = (
        gate_validation["accepted"]
        is True
        and gate_result.accepted is True
    )

    registry_accepted = (
        registry_validation["accepted"]
        is True
        and registry_result.accepted is True
    )

    stages = (
        _build_stage(
            stage_id="discovery",
            schema_version=(
                discovery_result
                .schema_version
            ),
            engine_id=(
                discovery_result.engine_id
            ),
            status=discovery_result.status,
            accepted=discovery_accepted,
            artifact_hash=(
                discovery_result.result_hash
            ),
            input_hash=source_hash,
            output_count=(
                discovery_result
                .opportunity_count
            ),
            details={
                "contract_valid": (
                    discovery_validation[
                        "accepted"
                    ]
                ),
                "result_hash_valid": (
                    discovery_result
                    .verify_result_hash()
                ),
            },
        ),
        _build_stage(
            stage_id="pipeline_gate",
            schema_version=(
                gate_result.schema_version
            ),
            engine_id=gate_result.engine_id,
            status=gate_result.status,
            accepted=gate_accepted,
            artifact_hash=gate_result.gate_hash,
            input_hash=(
                discovery_result.result_hash
            ),
            output_count=len(
                gate_result.checks
            ),
            details={
                "gate_valid": (
                    gate_validation["accepted"]
                ),
                "gate_accepted": (
                    gate_result.accepted
                ),
                "rejection_count": len(
                    gate_result
                    .rejection_reasons
                ),
            },
        ),
        _build_stage(
            stage_id="registry_bridge",
            schema_version=(
                registry_result
                .schema_version
            ),
            engine_id=(
                registry_result.engine_id
            ),
            status=registry_result.status,
            accepted=registry_accepted,
            artifact_hash=(
                registry_result.result_hash
            ),
            input_hash=gate_result.gate_hash,
            output_count=(
                registry_result
                .registration_count
            ),
            details={
                "registry_valid": (
                    registry_validation[
                        "accepted"
                    ]
                ),
                "registry_accepted": (
                    registry_result.accepted
                ),
                "external_state_mutated": (
                    False
                ),
            },
        ),
    )

    rejection_reasons = []

    if not discovery_accepted:
        rejection_reasons.append(
            "discovery_result_rejected"
        )

    if not gate_accepted:
        rejection_reasons.append(
            "pipeline_gate_rejected"
        )

    if not registry_accepted:
        rejection_reasons.append(
            "registry_bridge_rejected"
        )

    rejection_reasons.extend(
        gate_result.rejection_reasons
    )

    rejection_reasons.extend(
        registry_result.rejection_reasons
    )

    normalized_rejections = tuple(
        sorted(
            set(rejection_reasons)
        )
    )

    accepted = not normalized_rejections

    if not accepted:
        status = "rejected"
    elif discovery_result.status == "empty":
        status = "empty"
    else:
        status = "completed"

    pipeline_metadata = {
        "pipeline_family": (
            "market_regime_discovery"
        ),
        "source_hash": source_hash,
        "stage_count": len(stages),
        "discovery_valid": (
            discovery_accepted
        ),
        "gate_valid": gate_accepted,
        "registry_valid": (
            registry_accepted
        ),
        "external_state_mutated": False,
        "order_placement_performed": False,
        "transaction_signed": False,
        "deterministic": True,
        "immutable": True,
        "replayable": True,
        "explainable": True,
        "auditable": True,
        "read_only": True,
    }

    if metadata:
        for key, value in metadata.items():
            pipeline_metadata[str(key)] = (
                _stable_value(value)
            )

    normalized_metadata = _normalize_metadata(
        pipeline_metadata
    )

    payload = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "status": status,
        "accepted": accepted,
        "observed_at": (
            resolved_observed_at
        ),
        "source_schema_version": (
            source_schema_version
        ),
        "source_engine_id": (
            source_engine_id
        ),
        "source_status": source_status,
        "source_record_count": len(
            source_records
        ),
        "discovery_result": (
            _artifact_dict(discovery_result)
        ),
        "gate_result": (
            _artifact_dict(gate_result)
        ),
        "registry_result": (
            _artifact_dict(registry_result)
        ),
        "stages": tuple(
            stage.as_dict()
            for stage in stages
        ),
        "rejection_reasons": (
            normalized_rejections
        ),
        "metadata": _metadata_dict(
            normalized_metadata
        ),
        "read_only": True,
    }

    result = (
        MarketRegimePipelineBridgeResult(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            status=status,
            accepted=accepted,
            observed_at=(
                resolved_observed_at
            ),
            source_schema_version=(
                source_schema_version
            ),
            source_engine_id=(
                source_engine_id
            ),
            source_status=source_status,
            source_record_count=len(
                source_records
            ),
            discovery_result=(
                discovery_result
            ),
            gate_result=gate_result,
            registry_result=(
                registry_result
            ),
            stages=stages,
            rejection_reasons=(
                normalized_rejections
            ),
            metadata=normalized_metadata,
            pipeline_hash=_stable_hash(
                payload
            ),
            read_only=True,
        )
    )

    if not result.verify_pipeline_hash():
        raise AssertionError(
            "pipeline bridge produced an "
            "invalid deterministic hash"
        )

    return result


def bridge_market_regime_pipeline(
    source_result: Any,
    observed_at: Optional[str] = None,
    config: Optional[
        MarketRegimeEngineConfig
    ] = None,
    metadata: Optional[
        Mapping[str, Any]
    ] = None,
) -> MarketRegimePipelineBridgeResult:
    return run_market_regime_pipeline(
        source_result=source_result,
        observed_at=observed_at,
        config=config,
        metadata=metadata,
    )


def validate_market_regime_pipeline_bridge(
    result: Any,
) -> Dict[str, Any]:
    checks = {
        "result_type": isinstance(
            result,
            MarketRegimePipelineBridgeResult,
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
            in PIPELINE_STATUSES
        ),
        "read_only": (
            getattr(
                result,
                "read_only",
                None,
            )
            is True
        ),
        "pipeline_hash_valid": (
            isinstance(
                result,
                MarketRegimePipelineBridgeResult,
            )
            and result.verify_pipeline_hash()
        ),
        "discovery_valid": (
            isinstance(
                result,
                MarketRegimePipelineBridgeResult,
            )
            and (
                validate_market_regime_discovery_result(
                    result.discovery_result
                )["accepted"]
                is True
            )
        ),
        "gate_valid": (
            isinstance(
                result,
                MarketRegimePipelineBridgeResult,
            )
            and (
                validate_market_regime_pipeline_gate(
                    result.gate_result
                )["accepted"]
                is True
            )
        ),
        "registry_valid": (
            isinstance(
                result,
                MarketRegimePipelineBridgeResult,
            )
            and (
                validate_market_regime_registry_bridge(
                    result.registry_result
                )["accepted"]
                is True
            )
        ),
        "stage_count": (
            isinstance(
                result,
                MarketRegimePipelineBridgeResult,
            )
            and len(result.stages) == 3
        ),
        "stage_hash_chain": (
            isinstance(
                result,
                MarketRegimePipelineBridgeResult,
            )
            and (
                result.stages[0].input_hash
                == dict(
                    result.metadata
                )["source_hash"]
            )
            and (
                result.stages[1].input_hash
                == result.stages[0]
                .artifact_hash
            )
            and (
                result.stages[2].input_hash
                == result.stages[1]
                .artifact_hash
            )
        ),
    }

    return {
        "accepted": all(
            checks.values()
        ),
        "checks": checks,
    }


def assert_market_regime_pipeline_bridge_read_only(
    result: MarketRegimePipelineBridgeResult,
) -> bool:
    if not isinstance(
        result,
        MarketRegimePipelineBridgeResult,
    ):
        raise TypeError(
            "result must be a "
            "MarketRegimePipelineBridgeResult"
        )

    if READ_ONLY is not True:
        raise AssertionError(
            "market regime pipeline bridge "
            "must be read-only"
        )

    if result.read_only is not True:
        raise AssertionError(
            "pipeline bridge result must be "
            "read-only"
        )

    metadata = dict(
        result.metadata
    )

    protected_flags = {
        "external_state_mutated": False,
        "order_placement_performed": False,
        "transaction_signed": False,
        "read_only": True,
    }

    for key, expected in (
        protected_flags.items()
    ):
        if metadata.get(key) is not expected:
            raise AssertionError(
                f"invalid read-only flag: {key}"
            )

    if not all(
        stage.read_only
        for stage in result.stages
    ):
        raise AssertionError(
            "all pipeline stages must be "
            "read-only"
        )

    return True


__all__ = [
    "READ_ONLY",
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "PIPELINE_STATUSES",
    "MarketRegimePipelineStage",
    "MarketRegimePipelineBridgeResult",
    "run_market_regime_pipeline",
    "bridge_market_regime_pipeline",
    "validate_market_regime_pipeline_bridge",
    "assert_market_regime_pipeline_bridge_read_only",
]
