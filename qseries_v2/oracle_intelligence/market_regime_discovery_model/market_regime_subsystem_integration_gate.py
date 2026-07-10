
from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from hashlib import sha256
from typing import Any, Dict, Mapping, Optional, Tuple

from .market_regime_discovery_contract import (
    validate_market_regime_discovery_result,
)

from .market_regime_discovery_engine import (
    discover_market_regimes,
)

from .market_regime_pipeline_gate import (
    evaluate_market_regime_pipeline,
    validate_market_regime_pipeline_gate,
)

from .market_regime_registry_bridge import (
    bridge_market_regime_to_registry,
    validate_market_regime_registry_bridge,
)

from .market_regime_pipeline_bridge import (
    run_market_regime_pipeline,
    validate_market_regime_pipeline_bridge,
)

from .market_regime_oos_runtime_gate import (
    MarketRegimeOOSWindow,
    evaluate_market_regime_oos_runtime,
    validate_market_regime_oos_runtime_gate,
)

from .market_regime_replay_ledger import (
    build_market_regime_replay_ledger,
    replay_market_regime_entry,
    validate_market_regime_replay_ledger,
)


READ_ONLY = True
SCHEMA_VERSION = "RGD-009"

ENGINE_ID = (
    "oracle.discovery.market_regime."
    "subsystem_integration_gate"
)

INTEGRATION_STATUSES = frozenset(
    {
        "passed",
        "empty",
        "failed",
    }
)

EXPECTED_MODULES = (
    "RGD-001",
    "RGD-002",
    "RGD-003",
    "RGD-004",
    "RGD-005",
    "RGD-006",
    "RGD-007",
    "RGD-008",
    "RGD-009",
)


def _stable_value(value: Any) -> Any:
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

    if is_dataclass(value):
        return _stable_value(
            asdict(value)
        )

    return value


def _stable_hash(value: Any) -> str:
    return sha256(
        repr(
            _stable_value(value)
        ).encode("utf-8")
    ).hexdigest()


def _artifact_dict(value: Any) -> Dict[str, Any]:
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
        "artifact must be a mapping, dataclass, "
        "or expose as_dict()"
    )


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
class MarketRegimeIntegrationCheck:
    check_id: str
    accepted: bool
    explanation: str
    artifact_hash: str
    details: Tuple[
        Tuple[str, Any],
        ...,
    ] = field(
        default_factory=tuple
    )

    def __post_init__(self) -> None:
        if not str(self.check_id).strip():
            raise ValueError(
                "check_id must not be empty"
            )

        if not str(self.explanation).strip():
            raise ValueError(
                "explanation must not be empty"
            )

        if not str(self.artifact_hash).strip():
            raise ValueError(
                "artifact_hash must not be empty"
            )

        object.__setattr__(
            self,
            "details",
            tuple(
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
            ),
        )

    def as_dict(self) -> Dict[str, Any]:
        return {
            "check_id": self.check_id,
            "accepted": self.accepted,
            "explanation": self.explanation,
            "artifact_hash": (
                self.artifact_hash
            ),
            "details": {
                key: _stable_value(value)
                for key, value in self.details
            },
        }


@dataclass(frozen=True)
class MarketRegimeSubsystemIntegrationResult:
    schema_version: str
    engine_id: str
    status: str
    accepted: bool
    observed_at: str
    modules: Tuple[str, ...]
    checks: Tuple[
        MarketRegimeIntegrationCheck,
        ...,
    ]
    passed_check_count: int
    failed_check_count: int
    rejection_reasons: Tuple[str, ...]
    discovery_hash: str
    gate_hash: str
    registry_hash: str
    pipeline_hash: str
    oos_hash: str
    replay_ledger_hash: str
    metadata: Tuple[
        Tuple[str, Any],
        ...,
    ] = field(
        default_factory=tuple
    )
    integration_hash: str = ""
    read_only: bool = True

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(
                "invalid integration "
                "schema_version"
            )

        if self.engine_id != ENGINE_ID:
            raise ValueError(
                "invalid integration engine_id"
            )

        if self.status not in (
            INTEGRATION_STATUSES
        ):
            raise ValueError(
                "invalid integration status"
            )

        if not str(self.observed_at).strip():
            raise ValueError(
                "observed_at must not be empty"
            )

        if self.modules != EXPECTED_MODULES:
            raise ValueError(
                "integration modules do not "
                "match expected subsystem"
            )

        if self.passed_check_count < 0:
            raise ValueError(
                "passed_check_count cannot "
                "be negative"
            )

        if self.failed_check_count < 0:
            raise ValueError(
                "failed_check_count cannot "
                "be negative"
            )

        if (
            self.passed_check_count
            + self.failed_check_count
            != len(self.checks)
        ):
            raise ValueError(
                "integration check counts do "
                "not reconcile"
            )

        check_ids = [
            check.check_id
            for check in self.checks
        ]

        if len(check_ids) != len(
            set(check_ids)
        ):
            raise ValueError(
                "integration check identifiers "
                "must be unique"
            )

        required_hashes = {
            "discovery_hash": (
                self.discovery_hash
            ),
            "gate_hash": self.gate_hash,
            "registry_hash": (
                self.registry_hash
            ),
            "pipeline_hash": (
                self.pipeline_hash
            ),
            "oos_hash": self.oos_hash,
            "replay_ledger_hash": (
                self.replay_ledger_hash
            ),
            "integration_hash": (
                self.integration_hash
            ),
        }

        for field_name, value in (
            required_hashes.items()
        ):
            if not str(value).strip():
                raise ValueError(
                    f"{field_name} must not "
                    "be empty"
                )

        if self.read_only is not True:
            raise ValueError(
                "integration result must be "
                "read-only"
            )

        if self.accepted:
            if self.status not in {
                "passed",
                "empty",
            }:
                raise ValueError(
                    "accepted integration must "
                    "be passed or empty"
                )

            if self.failed_check_count != 0:
                raise ValueError(
                    "accepted integration cannot "
                    "have failed checks"
                )

            if self.rejection_reasons:
                raise ValueError(
                    "accepted integration cannot "
                    "contain rejection reasons"
                )
        else:
            if self.status != "failed":
                raise ValueError(
                    "rejected integration must "
                    "have failed status"
                )

            if self.failed_check_count < 1:
                raise ValueError(
                    "failed integration requires "
                    "at least one failed check"
                )

            if not self.rejection_reasons:
                raise ValueError(
                    "failed integration must "
                    "contain rejection reasons"
                )

        object.__setattr__(
            self,
            "metadata",
            tuple(
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
            ),
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
            "modules": self.modules,
            "checks": tuple(
                check.as_dict()
                for check in self.checks
            ),
            "passed_check_count": (
                self.passed_check_count
            ),
            "failed_check_count": (
                self.failed_check_count
            ),
            "rejection_reasons": (
                self.rejection_reasons
            ),
            "discovery_hash": (
                self.discovery_hash
            ),
            "gate_hash": self.gate_hash,
            "registry_hash": (
                self.registry_hash
            ),
            "pipeline_hash": (
                self.pipeline_hash
            ),
            "oos_hash": self.oos_hash,
            "replay_ledger_hash": (
                self.replay_ledger_hash
            ),
            "metadata": _metadata_dict(
                self.metadata
            ),
            "read_only": self.read_only,
        }

    def as_dict(self) -> Dict[str, Any]:
        payload = self.payload()

        payload["integration_hash"] = (
            self.integration_hash
        )

        return payload

    def verify_integration_hash(self) -> bool:
        return (
            self.integration_hash
            == _stable_hash(
                self.payload()
            )
        )


def _make_check(
    check_id: str,
    accepted: bool,
    explanation: str,
    artifact: Any,
    details: Optional[
        Mapping[str, Any]
    ] = None,
) -> MarketRegimeIntegrationCheck:
    return MarketRegimeIntegrationCheck(
        check_id=check_id,
        accepted=bool(accepted),
        explanation=explanation,
        artifact_hash=_stable_hash(
            artifact
        ),
        details=_normalize_metadata(
            details or {}
        ),
    )


def run_market_regime_subsystem_integration_gate(
    source_result: Any,
    window: MarketRegimeOOSWindow,
    observed_at: str,
    metadata: Optional[
        Mapping[str, Any]
    ] = None,
) -> MarketRegimeSubsystemIntegrationResult:
    if source_result is None:
        raise TypeError(
            "source_result must not be None"
        )

    if not isinstance(
        window,
        MarketRegimeOOSWindow,
    ):
        raise TypeError(
            "window must be a "
            "MarketRegimeOOSWindow"
        )

    resolved_observed_at = str(
        observed_at
    ).strip()

    if not resolved_observed_at:
        raise ValueError(
            "observed_at must not be empty"
        )

    discovery_result = (
        discover_market_regimes(
            source_result=source_result,
            observed_at=(
                resolved_observed_at
            ),
        )
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
            observed_at=(
                resolved_observed_at
            ),
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
            observed_at=(
                resolved_observed_at
            ),
        )
    )

    registry_validation = (
        validate_market_regime_registry_bridge(
            registry_result
        )
    )

    pipeline_result = (
        run_market_regime_pipeline(
            source_result=source_result,
            observed_at=(
                resolved_observed_at
            ),
        )
    )

    pipeline_validation = (
        validate_market_regime_pipeline_bridge(
            pipeline_result
        )
    )

    oos_result = (
        evaluate_market_regime_oos_runtime(
            source_result=source_result,
            window=window,
            observed_at=(
                resolved_observed_at
            ),
        )
    )

    oos_validation = (
        validate_market_regime_oos_runtime_gate(
            oos_result
        )
    )

    replay_ledger = (
        build_market_regime_replay_ledger(
            replay_runs=(
                (
                    source_result,
                    window,
                    resolved_observed_at,
                ),
            ),
        )
    )

    replay_validation = (
        validate_market_regime_replay_ledger(
            replay_ledger
        )
    )

    replay_result = (
        replay_market_regime_entry(
            entry=replay_ledger.entries[0],
            source_result=source_result,
            window=window,
        )
        if replay_ledger.entries
        else {
            "accepted": True,
            "checks": {},
        }
    )

    second_pipeline_result = (
        run_market_regime_pipeline(
            source_result=source_result,
            observed_at=(
                resolved_observed_at
            ),
        )
    )

    second_oos_result = (
        evaluate_market_regime_oos_runtime(
            source_result=source_result,
            window=window,
            observed_at=(
                resolved_observed_at
            ),
        )
    )

    checks = []

    checks.append(
        _make_check(
            check_id="discovery_contract",
            accepted=(
                discovery_validation[
                    "accepted"
                ]
                is True
            ),
            explanation=(
                "RGD-003 discovery output "
                "satisfies the RGD-001 "
                "contract."
            ),
            artifact=discovery_result,
            details={
                "status": (
                    discovery_result.status
                ),
                "opportunity_count": (
                    discovery_result
                    .opportunity_count
                ),
            },
        )
    )

    checks.append(
        _make_check(
            check_id="pipeline_gate",
            accepted=(
                gate_validation["accepted"]
                is True
                and gate_result.accepted
                is True
            ),
            explanation=(
                "RGD-004 pipeline gate "
                "accepted the discovery flow."
            ),
            artifact=gate_result,
            details={
                "status": gate_result.status,
                "check_count": len(
                    gate_result.checks
                ),
            },
        )
    )

    checks.append(
        _make_check(
            check_id="registry_bridge",
            accepted=(
                registry_validation[
                    "accepted"
                ]
                is True
                and registry_result.accepted
                is True
            ),
            explanation=(
                "RGD-005 registry projection "
                "is valid and read-only."
            ),
            artifact=registry_result,
            details={
                "status": (
                    registry_result.status
                ),
                "registration_count": (
                    registry_result
                    .registration_count
                ),
            },
        )
    )

    checks.append(
        _make_check(
            check_id="pipeline_bridge",
            accepted=(
                pipeline_validation[
                    "accepted"
                ]
                is True
                and pipeline_result.accepted
                is True
            ),
            explanation=(
                "RGD-006 end-to-end pipeline "
                "bridge completed successfully."
            ),
            artifact=pipeline_result,
            details={
                "status": (
                    pipeline_result.status
                ),
                "stage_count": len(
                    pipeline_result.stages
                ),
            },
        )
    )

    checks.append(
        _make_check(
            check_id="oos_runtime_gate",
            accepted=(
                oos_validation["accepted"]
                is True
                and oos_result.accepted
                is True
            ),
            explanation=(
                "RGD-007 OOS runtime gate "
                "accepted the evaluation window."
            ),
            artifact=oos_result,
            details={
                "status": oos_result.status,
                "in_window_records": (
                    oos_result
                    .in_window_record_count
                ),
                "invalid_timestamps": (
                    oos_result
                    .invalid_timestamp_record_count
                ),
            },
        )
    )

    checks.append(
        _make_check(
            check_id="replay_ledger",
            accepted=(
                replay_validation["accepted"]
                is True
                and replay_ledger.accepted
                is True
                and replay_ledger
                .verify_chain()
                is True
            ),
            explanation=(
                "RGD-008 replay ledger and "
                "hash chain are valid."
            ),
            artifact=replay_ledger,
            details={
                "status": (
                    replay_ledger.status
                ),
                "entry_count": (
                    replay_ledger.entry_count
                ),
                "chain_valid": (
                    replay_ledger
                    .verify_chain()
                ),
            },
        )
    )

    checks.append(
        _make_check(
            check_id="replay_reproduction",
            accepted=(
                replay_result["accepted"]
                is True
            ),
            explanation=(
                "Recorded OOS runtime output "
                "reproduces exactly."
            ),
            artifact=replay_result,
            details={
                "replay_checks": (
                    replay_result["checks"]
                ),
            },
        )
    )

    deterministic_pipeline = (
        pipeline_result.pipeline_hash
        == second_pipeline_result.pipeline_hash
    )

    checks.append(
        _make_check(
            check_id="pipeline_determinism",
            accepted=(
                deterministic_pipeline
            ),
            explanation=(
                "Repeated RGD-006 execution "
                "produced the same pipeline "
                "hash."
            ),
            artifact={
                "first": (
                    pipeline_result
                    .pipeline_hash
                ),
                "second": (
                    second_pipeline_result
                    .pipeline_hash
                ),
            },
            details={
                "first_hash": (
                    pipeline_result
                    .pipeline_hash
                ),
                "second_hash": (
                    second_pipeline_result
                    .pipeline_hash
                ),
            },
        )
    )

    deterministic_oos = (
        oos_result.result_hash
        == second_oos_result.result_hash
    )

    checks.append(
        _make_check(
            check_id="oos_determinism",
            accepted=deterministic_oos,
            explanation=(
                "Repeated RGD-007 execution "
                "produced the same OOS hash."
            ),
            artifact={
                "first": oos_result.result_hash,
                "second": (
                    second_oos_result
                    .result_hash
                ),
            },
            details={
                "first_hash": (
                    oos_result.result_hash
                ),
                "second_hash": (
                    second_oos_result
                    .result_hash
                ),
            },
        )
    )

    hash_chain_valid = (
        gate_result.discovery_hash
        == discovery_result.result_hash
        and registry_result
        .pipeline_gate_hash
        == gate_result.gate_hash
        and pipeline_result
        .discovery_result.result_hash
        == discovery_result.result_hash
        and pipeline_result
        .gate_result.gate_hash
        == gate_result.gate_hash
        and pipeline_result
        .registry_result.pipeline_gate_hash
        == pipeline_result
        .gate_result.gate_hash
        and registry_result
        .pipeline_gate_hash
        == gate_result.gate_hash
        and oos_result
        .pipeline_result.discovery_result
        .result_hash
        == discovery_result.result_hash
        and oos_result
        .pipeline_result.gate_result
        .discovery_hash
        == oos_result
        .pipeline_result.discovery_result
        .result_hash
        and oos_result
        .pipeline_result.registry_result
        .pipeline_gate_hash
        == oos_result
        .pipeline_result.gate_result.gate_hash
        and (
            replay_ledger.entries[0]
            .source_hash
            == _stable_hash(
                _artifact_dict(
                    source_result
                )
            )
            if replay_ledger.entries
            else True
        )
        and (
            replay_ledger.entries[0]
            .window_hash
            == _stable_hash(
                window.as_dict()
            )
            if replay_ledger.entries
            else True
        )
        and replay_ledger.verify_chain()
    )

    checks.append(
        _make_check(
            check_id="artifact_hash_chain",
            accepted=hash_chain_valid,
            explanation=(
                "All subsystem artifact hashes "
                "link across RGD-003 through "
                "RGD-008."
            ),
            artifact={
                "discovery": (
                    discovery_result.result_hash
                ),
                "gate": gate_result.gate_hash,
                "registry": (
                    registry_result.result_hash
                ),
                "pipeline": (
                    pipeline_result
                    .pipeline_hash
                ),
                "oos": oos_result.result_hash,
                "replay": (
                    replay_ledger.ledger_hash
                ),
            },
        )
    )

    read_only_valid = all(
        (
            discovery_result.read_only,
            gate_result.read_only,
            registry_result.read_only,
            pipeline_result.read_only,
            oos_result.read_only,
            replay_ledger.read_only,
            all(
                stage.read_only
                for stage
                in pipeline_result.stages
            ),
            all(
                entry.read_only
                for entry
                in replay_ledger.entries
            ),
        )
    )

    checks.append(
        _make_check(
            check_id="subsystem_read_only",
            accepted=read_only_valid,
            explanation=(
                "Every Market Regime artifact "
                "and stage is read-only."
            ),
            artifact={
                "discovery": (
                    discovery_result.read_only
                ),
                "gate": gate_result.read_only,
                "registry": (
                    registry_result.read_only
                ),
                "pipeline": (
                    pipeline_result.read_only
                ),
                "oos": oos_result.read_only,
                "replay": (
                    replay_ledger.read_only
                ),
            },
        )
    )

    checks = tuple(
        sorted(
            checks,
            key=lambda item: item.check_id,
        )
    )

    passed_check_count = sum(
        1
        for check in checks
        if check.accepted
    )

    failed_checks = tuple(
        check.check_id
        for check in checks
        if not check.accepted
    )

    failed_check_count = len(
        failed_checks
    )

    accepted = failed_check_count == 0

    if not accepted:
        status = "failed"
    elif (
        discovery_result.status == "empty"
        and oos_result.status == "empty"
    ):
        status = "empty"
    else:
        status = "passed"

    rejection_reasons = tuple(
        sorted(
            f"integration_check_failed:{check_id}"
            for check_id in failed_checks
        )
    )

    integration_metadata = {
        "subsystem": (
            "market_regime_discovery"
        ),
        "module_count": len(
            EXPECTED_MODULES
        ),
        "integration_check_count": len(
            checks
        ),
        "contract_version": "RGD-001",
        "source_adapter_version": "RGD-002",
        "discovery_engine_version": (
            "RGD-003"
        ),
        "pipeline_gate_version": "RGD-004",
        "registry_bridge_version": (
            "RGD-005"
        ),
        "pipeline_bridge_version": (
            "RGD-006"
        ),
        "oos_runtime_gate_version": (
            "RGD-007"
        ),
        "replay_ledger_version": (
            "RGD-008"
        ),
        "integration_gate_version": (
            "RGD-009"
        ),
        "external_state_mutated": False,
        "order_placement_performed": False,
        "transaction_signed": False,
        "persistent_write_performed": False,
        "deterministic": True,
        "immutable": True,
        "replayable": True,
        "explainable": True,
        "auditable": True,
        "read_only": True,
    }

    if metadata:
        for key, value in metadata.items():
            integration_metadata[str(key)] = (
                _stable_value(value)
            )

    normalized_metadata = _normalize_metadata(
        integration_metadata
    )

    payload = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "status": status,
        "accepted": accepted,
        "observed_at": (
            resolved_observed_at
        ),
        "modules": EXPECTED_MODULES,
        "checks": tuple(
            check.as_dict()
            for check in checks
        ),
        "passed_check_count": (
            passed_check_count
        ),
        "failed_check_count": (
            failed_check_count
        ),
        "rejection_reasons": (
            rejection_reasons
        ),
        "discovery_hash": (
            discovery_result.result_hash
        ),
        "gate_hash": gate_result.gate_hash,
        "registry_hash": (
            registry_result.result_hash
        ),
        "pipeline_hash": (
            pipeline_result.pipeline_hash
        ),
        "oos_hash": oos_result.result_hash,
        "replay_ledger_hash": (
            replay_ledger.ledger_hash
        ),
        "metadata": _metadata_dict(
            normalized_metadata
        ),
        "read_only": True,
    }

    result = (
        MarketRegimeSubsystemIntegrationResult(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            status=status,
            accepted=accepted,
            observed_at=(
                resolved_observed_at
            ),
            modules=EXPECTED_MODULES,
            checks=checks,
            passed_check_count=(
                passed_check_count
            ),
            failed_check_count=(
                failed_check_count
            ),
            rejection_reasons=(
                rejection_reasons
            ),
            discovery_hash=(
                discovery_result.result_hash
            ),
            gate_hash=(
                gate_result.gate_hash
            ),
            registry_hash=(
                registry_result.result_hash
            ),
            pipeline_hash=(
                pipeline_result.pipeline_hash
            ),
            oos_hash=(
                oos_result.result_hash
            ),
            replay_ledger_hash=(
                replay_ledger.ledger_hash
            ),
            metadata=normalized_metadata,
            integration_hash=_stable_hash(
                payload
            ),
            read_only=True,
        )
    )

    if not result.verify_integration_hash():
        raise AssertionError(
            "integration gate produced an "
            "invalid deterministic hash"
        )

    return result


def validate_market_regime_subsystem_integration_gate(
    result: Any,
) -> Dict[str, Any]:
    checks = {
        "result_type": isinstance(
            result,
            MarketRegimeSubsystemIntegrationResult,
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
            in INTEGRATION_STATUSES
        ),
        "modules": (
            getattr(
                result,
                "modules",
                None,
            )
            == EXPECTED_MODULES
        ),
        "read_only": (
            getattr(
                result,
                "read_only",
                None,
            )
            is True
        ),
        "integration_hash_valid": (
            isinstance(
                result,
                MarketRegimeSubsystemIntegrationResult,
            )
            and result
            .verify_integration_hash()
        ),
        "check_counts_valid": (
            isinstance(
                result,
                MarketRegimeSubsystemIntegrationResult,
            )
            and (
                result.passed_check_count
                + result.failed_check_count
                == len(result.checks)
            )
        ),
    }

    return {
        "accepted": all(
            checks.values()
        ),
        "checks": checks,
    }


def assert_market_regime_subsystem_read_only(
    result: MarketRegimeSubsystemIntegrationResult,
) -> bool:
    if not isinstance(
        result,
        MarketRegimeSubsystemIntegrationResult,
    ):
        raise TypeError(
            "result must be a "
            "MarketRegimeSubsystemIntegrationResult"
        )

    if READ_ONLY is not True:
        raise AssertionError(
            "market regime subsystem gate "
            "must be read-only"
        )

    if result.read_only is not True:
        raise AssertionError(
            "integration result must be "
            "read-only"
        )

    metadata = dict(
        result.metadata
    )

    protected_flags = {
        "external_state_mutated": False,
        "order_placement_performed": False,
        "transaction_signed": False,
        "persistent_write_performed": False,
        "read_only": True,
    }

    for key, expected in (
        protected_flags.items()
    ):
        if metadata.get(key) is not expected:
            raise AssertionError(
                f"invalid read-only flag: {key}"
            )

    return True


__all__ = [
    "READ_ONLY",
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "INTEGRATION_STATUSES",
    "EXPECTED_MODULES",
    "MarketRegimeIntegrationCheck",
    "MarketRegimeSubsystemIntegrationResult",
    "run_market_regime_subsystem_integration_gate",
    "validate_market_regime_subsystem_integration_gate",
    "assert_market_regime_subsystem_read_only",
]
