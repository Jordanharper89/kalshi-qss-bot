from pathlib import Path


ROOT = Path.cwd()

PACKAGE = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "market_regime_discovery_model"
)

PACKAGE.mkdir(
    parents=True,
    exist_ok=True,
)

MODULE = PACKAGE / "market_regime_pipeline_bridge.py"

TEST = ROOT / "test_rgd_006_market_regime_pipeline_bridge.py"

INIT = PACKAGE / "__init__.py"


MODULE.write_text(
r"""
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

    try:
        source_payload = _artifact_dict(
            source_result
        )
    except TypeError:
        source_payload = _stable_value(
            source_result
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
""",
    encoding="utf-8",
)


TEST.write_text(
r"""
from dataclasses import FrozenInstanceError

from qseries_v2.oracle_intelligence.market_regime_discovery_model.market_regime_pipeline_bridge import (
    ENGINE_ID,
    READ_ONLY,
    SCHEMA_VERSION,
    MarketRegimePipelineBridgeResult,
    MarketRegimePipelineStage,
    assert_market_regime_pipeline_bridge_read_only,
    bridge_market_regime_pipeline,
    run_market_regime_pipeline,
    validate_market_regime_pipeline_bridge,
)


OBSERVED_AT = "2026-07-10T00:00:00+00:00"


def _record(
    signal_id,
    signal_type,
    value,
    source_family,
    reliability=0.90,
    prior_regime="stable",
):
    return {
        "signal_id": signal_id,
        "market_id": "KXREGIME",
        "venue": "kalshi",
        "asset": "binary_event",
        "source_family": source_family,
        "signal_type": signal_type,
        "value": value,
        "reliability": reliability,
        "observed_at": OBSERVED_AT,
        "prior_regime": prior_regime,
        "source_hash": (
            f"source-hash-{signal_id}"
        ),
        "details": {
            "fixture": True,
        },
    }


def _valid_source():
    return {
        "schema_version": "RGD-002",
        "engine_id": (
            "oracle.discovery.market_regime."
            "source_adapter"
        ),
        "status": "ok",
        "records": (
            _record(
                signal_id="volatility-001",
                signal_type="volatility",
                value=0.95,
                reliability=0.95,
                source_family=(
                    "volatility_discovery"
                ),
            ),
            _record(
                signal_id="dispersion-001",
                signal_type="dispersion",
                value=0.90,
                source_family=(
                    "correlation_discovery"
                ),
            ),
            _record(
                signal_id="correlation-001",
                signal_type=(
                    "correlation_breakdown"
                ),
                value=0.85,
                source_family=(
                    "correlation_discovery"
                ),
            ),
            _record(
                signal_id="liquidity-001",
                signal_type="liquidity",
                value=-0.50,
                reliability=0.85,
                source_family=(
                    "liquidity_discovery"
                ),
            ),
        ),
        "observed_at": OBSERVED_AT,
        "read_only": True,
    }


def _empty_source():
    return {
        "schema_version": "RGD-002",
        "engine_id": (
            "oracle.discovery.market_regime."
            "source_adapter"
        ),
        "status": "empty",
        "records": tuple(),
        "observed_at": OBSERVED_AT,
        "read_only": True,
    }


def _invalid_source():
    source = dict(
        _valid_source()
    )

    source["schema_version"] = "BAD-001"

    return source


def test_pipeline_bridge_constants():
    assert SCHEMA_VERSION == "RGD-006"

    assert ENGINE_ID == (
        "oracle.discovery.market_regime."
        "pipeline_bridge"
    )

    assert READ_ONLY is True


def test_pipeline_bridge_completed():
    result = run_market_regime_pipeline(
        source_result=_valid_source(),
        observed_at=OBSERVED_AT,
    )

    assert isinstance(
        result,
        MarketRegimePipelineBridgeResult,
    )

    assert result.schema_version == "RGD-006"
    assert result.engine_id == ENGINE_ID
    assert result.status == "completed"
    assert result.accepted is True
    assert result.source_record_count == 4
    assert result.opportunity_count == 1
    assert result.registration_count == 1
    assert result.rejection_reasons == tuple()
    assert len(result.stages) == 3
    assert result.read_only is True
    assert result.verify_pipeline_hash() is True

    assert [
        stage.stage_id
        for stage in result.stages
    ] == [
        "discovery",
        "pipeline_gate",
        "registry_bridge",
    ]

    assert all(
        stage.accepted
        for stage in result.stages
    )


def test_pipeline_bridge_empty():
    result = run_market_regime_pipeline(
        source_result=_empty_source(),
        observed_at=OBSERVED_AT,
    )

    assert result.status == "empty"
    assert result.accepted is True
    assert result.source_record_count == 0
    assert result.opportunity_count == 0
    assert result.registration_count == 1
    assert result.rejection_reasons == tuple()
    assert result.verify_pipeline_hash() is True


def test_pipeline_bridge_rejected():
    result = run_market_regime_pipeline(
        source_result=_invalid_source(),
        observed_at=OBSERVED_AT,
    )

    assert result.status == "rejected"
    assert result.accepted is False

    assert (
        "invalid_source_schema_version"
        in result.rejection_reasons
    )

    assert (
        "pipeline_gate_rejected"
        in result.rejection_reasons
    )

    assert (
        "registry_bridge_rejected"
        in result.rejection_reasons
    )

    assert result.verify_pipeline_hash() is True


def test_pipeline_bridge_hash_chain():
    result = run_market_regime_pipeline(
        source_result=_valid_source(),
        observed_at=OBSERVED_AT,
    )

    metadata = dict(
        result.metadata
    )

    discovery_stage = result.stages[0]
    gate_stage = result.stages[1]
    registry_stage = result.stages[2]

    assert discovery_stage.input_hash == (
        metadata["source_hash"]
    )

    assert gate_stage.input_hash == (
        discovery_stage.artifact_hash
    )

    assert registry_stage.input_hash == (
        gate_stage.artifact_hash
    )

    assert discovery_stage.artifact_hash == (
        result.discovery_result.result_hash
    )

    assert gate_stage.artifact_hash == (
        result.gate_result.gate_hash
    )

    assert registry_stage.artifact_hash == (
        result.registry_result.result_hash
    )


def test_pipeline_bridge_deterministic():
    result_1 = (
        bridge_market_regime_pipeline(
            source_result=_valid_source(),
            observed_at=OBSERVED_AT,
        )
    )

    result_2 = (
        bridge_market_regime_pipeline(
            source_result=_valid_source(),
            observed_at=OBSERVED_AT,
        )
    )

    assert result_1 == result_2

    assert result_1.pipeline_hash == (
        result_2.pipeline_hash
    )

    assert (
        result_1.discovery_result
        .result_hash
        == result_2.discovery_result
        .result_hash
    )

    assert (
        result_1.gate_result.gate_hash
        == result_2.gate_result.gate_hash
    )

    assert (
        result_1.registry_result
        .result_hash
        == result_2.registry_result
        .result_hash
    )


def test_pipeline_bridge_input_order_independent():
    source = _valid_source()

    reversed_source = dict(source)

    reversed_source["records"] = tuple(
        reversed(
            source["records"]
        )
    )

    result_1 = run_market_regime_pipeline(
        source_result=source,
        observed_at=OBSERVED_AT,
    )

    result_2 = run_market_regime_pipeline(
        source_result=reversed_source,
        observed_at=OBSERVED_AT,
    )

    assert (
        result_1.discovery_result
        .result_hash
        == result_2.discovery_result
        .result_hash
    )

    assert result_1.opportunity_count == (
        result_2.opportunity_count
    )

    assert result_1.status == result_2.status


def test_pipeline_bridge_metadata():
    result = run_market_regime_pipeline(
        source_result=_valid_source(),
        observed_at=OBSERVED_AT,
        metadata={
            "environment": "unit_test",
            "build": "RGD-006",
        },
    )

    metadata = dict(
        result.metadata
    )

    assert metadata["environment"] == (
        "unit_test"
    )

    assert metadata["build"] == "RGD-006"

    assert (
        metadata[
            "external_state_mutated"
        ]
        is False
    )

    assert (
        metadata[
            "order_placement_performed"
        ]
        is False
    )

    assert (
        metadata[
            "transaction_signed"
        ]
        is False
    )

    assert metadata["read_only"] is True


def test_pipeline_bridge_validation():
    result = run_market_regime_pipeline(
        source_result=_valid_source(),
        observed_at=OBSERVED_AT,
    )

    validation = (
        validate_market_regime_pipeline_bridge(
            result
        )
    )

    assert validation["accepted"] is True

    assert all(
        validation["checks"].values()
    )


def test_pipeline_bridge_read_only():
    result = run_market_regime_pipeline(
        source_result=_valid_source(),
        observed_at=OBSERVED_AT,
    )

    assert (
        assert_market_regime_pipeline_bridge_read_only(
            result
        )
        is True
    )

    try:
        result.status = "rejected"
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError(
            "pipeline result must be "
            "immutable"
        )

    stage = result.stages[0]

    assert isinstance(
        stage,
        MarketRegimePipelineStage,
    )

    try:
        stage.status = "rejected"
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError(
            "pipeline stage must be "
            "immutable"
        )


def test_pipeline_bridge_as_dict():
    result = run_market_regime_pipeline(
        source_result=_valid_source(),
        observed_at=OBSERVED_AT,
    )

    payload = result.as_dict()

    assert payload["schema_version"] == (
        "RGD-006"
    )

    assert payload["engine_id"] == ENGINE_ID
    assert payload["status"] == "completed"
    assert payload["accepted"] is True

    assert payload["opportunity_count"] == 1
    assert payload["registration_count"] == 1

    assert payload["pipeline_hash"] == (
        result.pipeline_hash
    )

    assert len(payload["stages"]) == 3


def test_pipeline_bridge_requires_source():
    try:
        run_market_regime_pipeline(
            source_result=None,
            observed_at=OBSERVED_AT,
        )
    except TypeError as exc:
        assert str(exc) == (
            "source_result must not be None"
        )
    else:
        raise AssertionError(
            "expected source requirement"
        )


if __name__ == "__main__":
    test_pipeline_bridge_constants()
    test_pipeline_bridge_completed()
    test_pipeline_bridge_empty()
    test_pipeline_bridge_rejected()
    test_pipeline_bridge_hash_chain()
    test_pipeline_bridge_deterministic()
    test_pipeline_bridge_input_order_independent()
    test_pipeline_bridge_metadata()
    test_pipeline_bridge_validation()
    test_pipeline_bridge_read_only()
    test_pipeline_bridge_as_dict()
    test_pipeline_bridge_requires_source()

    result = run_market_regime_pipeline(
        source_result=_valid_source(),
        observed_at=OBSERVED_AT,
    )

    print(
        "[PASS] RGD-006 "
        "Market Regime Pipeline Bridge"
    )

    print(
        {
            "schema_version": (
                result.schema_version
            ),
            "engine_id": result.engine_id,
            "status": result.status,
            "accepted": result.accepted,
            "source_records": (
                result.source_record_count
            ),
            "opportunities": (
                result.opportunity_count
            ),
            "registrations": (
                result.registration_count
            ),
            "stages": len(
                result.stages
            ),
            "read_only": result.read_only,
        }
    )
""",
    encoding="utf-8",
)


existing_init = (
    INIT.read_text(
        encoding="utf-8"
    )
    if INIT.exists()
    else ""
)

pipeline_import = r"""
from .market_regime_pipeline_bridge import (
    ENGINE_ID as PIPELINE_BRIDGE_ENGINE_ID,
    PIPELINE_STATUSES,
    READ_ONLY as PIPELINE_BRIDGE_READ_ONLY,
    SCHEMA_VERSION as PIPELINE_BRIDGE_SCHEMA_VERSION,
    MarketRegimePipelineBridgeResult,
    MarketRegimePipelineStage,
    assert_market_regime_pipeline_bridge_read_only,
    bridge_market_regime_pipeline,
    run_market_regime_pipeline,
    validate_market_regime_pipeline_bridge,
)
"""

if (
    "from .market_regime_pipeline_bridge import"
    not in existing_init
):
    updated_init = (
        existing_init.rstrip()
        + "\n\n"
        + pipeline_import.strip()
        + "\n"
    )

    INIT.write_text(
        updated_init,
        encoding="utf-8",
    )


print("========================================")
print(" RGD-006 REWRITE INSTALLER")
print(" Market Regime Pipeline Bridge")
print("========================================")
print(f"[OK] Wrote {MODULE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] RGD-006 rewritten")
print()
print("Run:")
print(
    "py "
    "test_rgd_006_market_regime_"
    "pipeline_bridge.py"
)
