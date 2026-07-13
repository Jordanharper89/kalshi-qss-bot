"""
OLA-025 Oracle Production Evidence Service Runner Binding.

Actual OLA-023 writer-payload contract correction.

This module binds the real OLA-023 runtime/state and runtime/logs writer
payloads to the OLA-024 production filesystem evidence writer.

Permanent rules:
- OLA-023 service lifecycle remains unchanged.
- OLA-024 production persistence remains authoritative.
- Exact OLA-023 writer payload shapes are validated by role.
- Datetime values are canonically converted to timezone-aware ISO-8601.
- A deterministic bootstrap-scoped persistence run identity is derived
  because OLA-023 final service_run_id is created only after iteration
  evidence writes complete.
- The derived persistence identity is never represented as the final
  OLA-023 service_run_id.
- Polling state lineage is extracted only from supplied OLA-023 evidence.
- Clock lineage is extracted only from supplied OLA-023 evidence.
- No missing lineage is invented.
- Oracle remains permanently read-only.
- No alerts, Q Series intake, handoff publication, or execution capability.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import math
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, Mapping

from .production_runtime_evidence_writer_bindings import (
    EvidenceWriteReceipt,
    OracleProductionRuntimeEvidenceWriterBindings,
    create_production_runtime_evidence_writer_bindings,
    stable_hash,
)


SCHEMA_VERSION = "OLA-025"
ENGINE_ID = "OLA-025"
SOURCE_RUNNER_SCHEMA_VERSION = "OLA-023"
SOURCE_RUNNER_ENGINE_ID = "OLA-023"
PRODUCTION_WRITER_ENGINE_ID = "OLA-024"

STATE_ROLE = "runtime/state"
LOG_ROLE = "runtime/logs"

STATE_REQUIRED_FIELDS = frozenset(
    {
        "schema_version",
        "engine_id",
        "evidence_role",
        "iteration_number",
        "bootstrap_id",
        "tick_id",
        "tick_hash",
        "previous_state_id",
        "previous_state_hash",
        "next_state",
        "iteration_completed_at",
    }
)

LOG_REQUIRED_FIELDS = frozenset(
    {
        "schema_version",
        "engine_id",
        "evidence_role",
        "iteration_number",
        "bootstrap_id",
        "readiness_id",
        "readiness_hash",
        "tick",
        "cycle_result_present",
        "canonical_clock_lineage_valid",
        "iteration_completed_at",
    }
)

ARCHITECTURE_FLAGS = MappingProxyType(
    {
        "alerts_allowed": False,
        "qseries_intake_allowed": False,
        "canonical_handoff_published": False,
        "read_only": True,
        "execution_allowed": False,
        "execution_adapter_resolved": False,
        "execution_adapter_invoked": False,
        "trade_authorization_allowed": False,
        "order_placement_allowed": False,
        "funds_moved": False,
        "portfolio_mutated": False,
    }
)


class ProductionEvidenceServiceRunnerBindingError(ValueError):
    pass


class MalformedServiceRunnerEvidenceError(
    ProductionEvidenceServiceRunnerBindingError
):
    pass


class ServiceRunnerEvidenceRoleError(
    ProductionEvidenceServiceRunnerBindingError
):
    pass


@dataclass(frozen=True)
class BoundEvidenceWriteResult:
    schema_version: str
    engine_id: str
    evidence_role: str
    binding_identity: str
    source_runner_engine_id: str
    production_writer_engine_id: str
    evidence_identity: str
    service_run_identity: str
    service_run_identity_kind: str
    iteration_identity: str
    caller_supplied_timestamp: str
    evidence_hash: str
    persisted_relative_path: str
    current_pointer_relative_path: str | None
    read_only: bool
    execution_allowed: bool
    alerts_allowed: bool
    qseries_intake_allowed: bool
    canonical_handoff_published: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "evidence_role": self.evidence_role,
            "binding_identity": self.binding_identity,
            "source_runner_engine_id": self.source_runner_engine_id,
            "production_writer_engine_id": self.production_writer_engine_id,
            "evidence_identity": self.evidence_identity,
            "service_run_identity": self.service_run_identity,
            "service_run_identity_kind": self.service_run_identity_kind,
            "iteration_identity": self.iteration_identity,
            "caller_supplied_timestamp": self.caller_supplied_timestamp,
            "evidence_hash": self.evidence_hash,
            "persisted_relative_path": self.persisted_relative_path,
            "current_pointer_relative_path": self.current_pointer_relative_path,
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "alerts_allowed": self.alerts_allowed,
            "qseries_intake_allowed": self.qseries_intake_allowed,
            "canonical_handoff_published": self.canonical_handoff_published,
        }


def _require_mapping(
    value: Any,
    *,
    field_name: str,
) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise MalformedServiceRunnerEvidenceError(
            f"{field_name} must be a mapping"
        )

    return dict(value)


def _require_non_empty_string(
    value: Any,
    *,
    field_name: str,
) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MalformedServiceRunnerEvidenceError(
            f"{field_name} must be a non-empty string"
        )

    return value.strip()


def _require_positive_int(
    value: Any,
    *,
    field_name: str,
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value <= 0
    ):
        raise MalformedServiceRunnerEvidenceError(
            f"{field_name} must be an int greater than zero"
        )

    return value


def _canonicalize_runner_value(
    value: Any,
    *,
    field_name: str,
) -> Any:
    if value is None or isinstance(
        value,
        (str, bool, int),
    ):
        return value

    if isinstance(value, float):
        if not math.isfinite(value):
            raise MalformedServiceRunnerEvidenceError(
                f"{field_name} contains non-finite float"
            )

        return value

    if isinstance(value, datetime):
        if (
            value.tzinfo is None
            or value.utcoffset() is None
        ):
            raise MalformedServiceRunnerEvidenceError(
                f"{field_name} contains timezone-naive datetime"
            )

        return value.astimezone(
            timezone.utc
        ).isoformat()

    if isinstance(value, Mapping):
        result: dict[str, Any] = {}

        for key in sorted(value):
            if not isinstance(key, str):
                raise MalformedServiceRunnerEvidenceError(
                    f"{field_name} contains non-string mapping key"
                )

            result[key] = _canonicalize_runner_value(
                value[key],
                field_name=f"{field_name}.{key}",
            )

        return result

    if isinstance(value, (list, tuple)):
        return [
            _canonicalize_runner_value(
                item,
                field_name=f"{field_name}[{index}]",
            )
            for index, item in enumerate(value)
        ]

    raise MalformedServiceRunnerEvidenceError(
        f"{field_name} contains unsupported type: "
        f"{type(value).__name__}"
    )


def _require_source_contract(
    envelope: Mapping[str, Any],
    *,
    role: str,
) -> None:
    expected_fields = (
        STATE_REQUIRED_FIELDS
        if role == STATE_ROLE
        else LOG_REQUIRED_FIELDS
        if role == LOG_ROLE
        else None
    )

    if expected_fields is None:
        raise ServiceRunnerEvidenceRoleError(
            f"Unsupported evidence role: {role}"
        )

    missing = sorted(
        expected_fields - set(envelope)
    )

    if missing:
        raise MalformedServiceRunnerEvidenceError(
            "Missing required OLA-023 writer payload fields: "
            + ", ".join(missing)
        )

    if (
        envelope["schema_version"]
        != SOURCE_RUNNER_SCHEMA_VERSION
    ):
        raise MalformedServiceRunnerEvidenceError(
            "writer payload schema_version must be OLA-023"
        )

    if (
        envelope["engine_id"]
        != SOURCE_RUNNER_ENGINE_ID
    ):
        raise MalformedServiceRunnerEvidenceError(
            "writer payload engine_id must be OLA-023"
        )

    if envelope["evidence_role"] != role:
        raise ServiceRunnerEvidenceRoleError(
            "writer payload evidence_role does not match "
            "bound writer role"
        )


def _derive_persistence_run_identity(
    bootstrap_id: str,
) -> str:
    identity_hash = stable_hash(
        {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "identity_type": (
                "bootstrap_scoped_persistence_run_identity"
            ),
            "source_runner_engine_id": (
                SOURCE_RUNNER_ENGINE_ID
            ),
            "bootstrap_id": bootstrap_id,
        }
    )

    return (
        f"oracle_persistence_run.{identity_hash}"
    )


def _derive_iteration_identity(
    *,
    bootstrap_id: str,
    iteration_number: int,
) -> str:
    identity_hash = stable_hash(
        {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "identity_type": (
                "runner_iteration_persistence_identity"
            ),
            "bootstrap_id": bootstrap_id,
            "iteration_number": iteration_number,
        }
    )

    return f"oracle_iteration.{identity_hash}"


def _derive_evidence_identity(
    *,
    role: str,
    persistence_run_identity: str,
    iteration_identity: str,
    canonical_payload: Mapping[str, Any],
) -> str:
    identity_hash = stable_hash(
        {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "evidence_role": role,
            "service_run_identity": (
                persistence_run_identity
            ),
            "iteration_identity": iteration_identity,
            "source_payload_hash": stable_hash(
                dict(canonical_payload)
            ),
        }
    )

    prefix = (
        "evidence.oracle.shadow.state"
        if role == STATE_ROLE
        else "evidence.oracle.shadow.log"
        if role == LOG_ROLE
        else None
    )

    if prefix is None:
        raise ServiceRunnerEvidenceRoleError(
            f"Unsupported evidence role: {role}"
        )

    return f"{prefix}.{identity_hash}"


def _extract_state_lineage(
    canonical_payload: Mapping[str, Any],
) -> dict[str, Any]:
    next_state = _require_mapping(
        canonical_payload["next_state"],
        field_name="next_state",
    )

    next_state_id = _require_non_empty_string(
        next_state.get("state_id"),
        field_name="next_state.state_id",
    )

    next_state_hash = _require_non_empty_string(
        next_state.get("state_hash"),
        field_name="next_state.state_hash",
    )

    return {
        "lineage_source": (
            "ola_023_runtime_state_writer_payload"
        ),
        "previous_state_id": _require_non_empty_string(
            canonical_payload["previous_state_id"],
            field_name="previous_state_id",
        ),
        "previous_state_hash": _require_non_empty_string(
            canonical_payload["previous_state_hash"],
            field_name="previous_state_hash",
        ),
        "next_state_id": next_state_id,
        "next_state_hash": next_state_hash,
        "next_consecutive_failures": next_state.get(
            "consecutive_failures"
        ),
        "next_state_suspended": next_state.get(
            "suspended"
        ),
    }


def _extract_log_lineage(
    canonical_payload: Mapping[str, Any],
) -> dict[str, Any]:
    tick = _require_mapping(
        canonical_payload["tick"],
        field_name="tick",
    )

    return {
        "lineage_source": (
            "ola_023_runtime_log_writer_payload"
        ),
        "previous_state_id": _require_non_empty_string(
            tick.get("previous_state_id"),
            field_name="tick.previous_state_id",
        ),
        "previous_state_hash": _require_non_empty_string(
            tick.get("previous_state_hash"),
            field_name="tick.previous_state_hash",
        ),
        "next_state_id": _require_non_empty_string(
            tick.get("next_state_id"),
            field_name="tick.next_state_id",
        ),
        "next_state_hash": _require_non_empty_string(
            tick.get("next_state_hash"),
            field_name="tick.next_state_hash",
        ),
        "next_consecutive_failures": tick.get(
            "next_consecutive_failures"
        ),
        "next_state_suspended": tick.get(
            "next_state_suspended"
        ),
    }


def _extract_clock_lineage(
    *,
    role: str,
    canonical_payload: Mapping[str, Any],
) -> dict[str, Any]:
    iteration_completed_at = _require_non_empty_string(
        canonical_payload["iteration_completed_at"],
        field_name="iteration_completed_at",
    )

    if role == STATE_ROLE:
        return {
            "lineage_source": (
                "ola_023_runtime_state_writer_payload"
            ),
            "lineage_scope": (
                "writer_payload_available_clock_lineage"
            ),
            "iteration_completed_at": (
                iteration_completed_at
            ),
        }

    if role == LOG_ROLE:
        tick = _require_mapping(
            canonical_payload["tick"],
            field_name="tick",
        )

        return {
            "lineage_source": (
                "ola_023_runtime_log_writer_payload"
            ),
            "lineage_scope": (
                "writer_payload_available_clock_lineage"
            ),
            "tick_started_at": _require_non_empty_string(
                tick.get("started_at"),
                field_name="tick.started_at",
            ),
            "tick_completed_at": _require_non_empty_string(
                tick.get("completed_at"),
                field_name="tick.completed_at",
            ),
            "iteration_completed_at": (
                iteration_completed_at
            ),
            "canonical_clock_lineage_valid": (
                canonical_payload[
                    "canonical_clock_lineage_valid"
                ]
            ),
        }

    raise ServiceRunnerEvidenceRoleError(
        f"Unsupported evidence role: {role}"
    )


class OracleProductionEvidenceServiceRunnerBinding:

    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    source_runner_engine_id = (
        SOURCE_RUNNER_ENGINE_ID
    )
    production_writer_engine_id = (
        PRODUCTION_WRITER_ENGINE_ID
    )

    def __init__(
        self,
        production_writer: (
            OracleProductionRuntimeEvidenceWriterBindings
        ),
    ) -> None:
        if not isinstance(
            production_writer,
            OracleProductionRuntimeEvidenceWriterBindings,
        ):
            raise ProductionEvidenceServiceRunnerBindingError(
                "production_writer must be an "
                "OLA-024 production writer"
            )

        self._production_writer = production_writer
        self._state_write_count = 0
        self._log_write_count = 0
        self._last_state_result: (
            BoundEvidenceWriteResult | None
        ) = None
        self._last_log_result: (
            BoundEvidenceWriteResult | None
        ) = None

    @property
    def production_writer(
        self,
    ) -> OracleProductionRuntimeEvidenceWriterBindings:
        return self._production_writer

    @property
    def state_write_count(self) -> int:
        return self._state_write_count

    @property
    def log_write_count(self) -> int:
        return self._log_write_count

    @property
    def last_state_result(
        self,
    ) -> BoundEvidenceWriteResult | None:
        return self._last_state_result

    @property
    def last_log_result(
        self,
    ) -> BoundEvidenceWriteResult | None:
        return self._last_log_result

    def describe_boundary(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "source_runner_schema_version": (
                SOURCE_RUNNER_SCHEMA_VERSION
            ),
            "source_runner_engine_id": (
                SOURCE_RUNNER_ENGINE_ID
            ),
            "production_writer_engine_id": (
                PRODUCTION_WRITER_ENGINE_ID
            ),
            "state_role": STATE_ROLE,
            "log_role": LOG_ROLE,
            "actual_ola_023_state_payload_contract_bound": True,
            "actual_ola_023_log_payload_contract_bound": True,
            "ola_023_writer_binding_type_compatible": True,
            "bootstrap_scoped_persistence_run_identity": True,
            "final_ola_023_service_run_id_invented": False,
            "source_payload_datetime_canonicalization": True,
            "polling_state_lineage_extracted_from_source_payload": True,
            "clock_lineage_extracted_from_source_payload": True,
            "missing_lineage_invented": False,
            "ola_024_production_writer_bound": True,
            "malformed_runner_evidence_fails_closed": True,
            "runner_lifecycle_mutated": False,
            **dict(ARCHITECTURE_FLAGS),
        }

    def state_writer(
        self,
        *,
        evidence: Mapping[str, Any],
    ) -> dict[str, Any]:
        result = self._bind_and_write(
            evidence_role=STATE_ROLE,
            evidence=evidence,
        )

        self._state_write_count += 1
        self._last_state_result = result

        return result.to_dict()

    def log_writer(
        self,
        *,
        evidence: Mapping[str, Any],
    ) -> dict[str, Any]:
        result = self._bind_and_write(
            evidence_role=LOG_ROLE,
            evidence=evidence,
        )

        self._log_write_count += 1
        self._last_log_result = result

        return result.to_dict()

    def state_writer_callable(
        self,
    ) -> Callable[..., dict[str, Any]]:
        return self.state_writer

    def log_writer_callable(
        self,
    ) -> Callable[..., dict[str, Any]]:
        return self.log_writer

    def _bind_and_write(
        self,
        *,
        evidence_role: str,
        evidence: Mapping[str, Any],
    ) -> BoundEvidenceWriteResult:
        envelope = _require_mapping(
            evidence,
            field_name="evidence",
        )

        _require_source_contract(
            envelope,
            role=evidence_role,
        )

        canonical_payload = _canonicalize_runner_value(
            envelope,
            field_name="evidence",
        )

        if not isinstance(canonical_payload, dict):
            raise MalformedServiceRunnerEvidenceError(
                "canonical writer payload must remain "
                "a mapping"
            )

        iteration_number = _require_positive_int(
            canonical_payload["iteration_number"],
            field_name="iteration_number",
        )

        bootstrap_id = _require_non_empty_string(
            canonical_payload["bootstrap_id"],
            field_name="bootstrap_id",
        )

        caller_supplied_timestamp = (
            _require_non_empty_string(
                canonical_payload[
                    "iteration_completed_at"
                ],
                field_name="iteration_completed_at",
            )
        )

        persistence_run_identity = (
            _derive_persistence_run_identity(
                bootstrap_id
            )
        )

        iteration_identity = _derive_iteration_identity(
            bootstrap_id=bootstrap_id,
            iteration_number=iteration_number,
        )

        evidence_identity = _derive_evidence_identity(
            role=evidence_role,
            persistence_run_identity=(
                persistence_run_identity
            ),
            iteration_identity=iteration_identity,
            canonical_payload=canonical_payload,
        )

        polling_state_lineage = (
            _extract_state_lineage(
                canonical_payload
            )
            if evidence_role == STATE_ROLE
            else _extract_log_lineage(
                canonical_payload
            )
        )

        canonical_clock_lineage = (
            _extract_clock_lineage(
                role=evidence_role,
                canonical_payload=canonical_payload,
            )
        )

        replay_metadata = {
            "replayable": True,
            "source_runner_schema_version": (
                SOURCE_RUNNER_SCHEMA_VERSION
            ),
            "source_runner_engine_id": (
                SOURCE_RUNNER_ENGINE_ID
            ),
            "binding_engine_id": ENGINE_ID,
            "source_payload_hash": stable_hash(
                canonical_payload
            ),
            "identity_derivation": (
                "bootstrap_scoped_precompletion_identity"
            ),
            "final_ola_023_service_run_id_available_at_write_time": (
                False
            ),
        }

        audit_metadata = {
            "oracle_service_id": (
                "service.oracle.intelligence"
            ),
            "source_runner_schema_version": (
                SOURCE_RUNNER_SCHEMA_VERSION
            ),
            "source_runner_engine_id": (
                SOURCE_RUNNER_ENGINE_ID
            ),
            "production_writer_engine_id": (
                PRODUCTION_WRITER_ENGINE_ID
            ),
            "binding_engine_id": ENGINE_ID,
            "source_evidence_role": evidence_role,
            "bootstrap_id": bootstrap_id,
            "iteration_number": iteration_number,
        }

        if evidence_role == STATE_ROLE:
            receipt = (
                self._production_writer.write_state_evidence(
                    evidence_identity=evidence_identity,
                    service_run_identity=(
                        persistence_run_identity
                    ),
                    iteration_identity=iteration_identity,
                    caller_supplied_timestamp=(
                        caller_supplied_timestamp
                    ),
                    evidence=canonical_payload,
                    polling_state_lineage=(
                        polling_state_lineage
                    ),
                    canonical_clock_lineage=(
                        canonical_clock_lineage
                    ),
                    replay_metadata=replay_metadata,
                    audit_metadata=audit_metadata,
                )
            )

        elif evidence_role == LOG_ROLE:
            receipt = (
                self._production_writer.write_log_evidence(
                    evidence_identity=evidence_identity,
                    service_run_identity=(
                        persistence_run_identity
                    ),
                    iteration_identity=iteration_identity,
                    caller_supplied_timestamp=(
                        caller_supplied_timestamp
                    ),
                    evidence=canonical_payload,
                    polling_state_lineage=(
                        polling_state_lineage
                    ),
                    canonical_clock_lineage=(
                        canonical_clock_lineage
                    ),
                    replay_metadata=replay_metadata,
                    audit_metadata=audit_metadata,
                )
            )

        else:
            raise ServiceRunnerEvidenceRoleError(
                f"Unsupported evidence role: {evidence_role}"
            )

        return self._result_from_receipt(
            receipt
        )

    def _result_from_receipt(
        self,
        receipt: EvidenceWriteReceipt,
    ) -> BoundEvidenceWriteResult:
        binding_identity = stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "engine_id": ENGINE_ID,
                "source_runner_engine_id": (
                    SOURCE_RUNNER_ENGINE_ID
                ),
                "production_writer_engine_id": (
                    PRODUCTION_WRITER_ENGINE_ID
                ),
                "evidence_role": receipt.evidence_role,
                "evidence_identity": (
                    receipt.evidence_identity
                ),
                "service_run_identity": (
                    receipt.service_run_identity
                ),
                "service_run_identity_kind": (
                    "bootstrap_scoped_precompletion_identity"
                ),
                "iteration_identity": (
                    receipt.iteration_identity
                ),
                "caller_supplied_timestamp": (
                    receipt.caller_supplied_timestamp
                ),
                "evidence_hash": receipt.evidence_hash,
                "relative_path": receipt.relative_path,
            }
        )

        return BoundEvidenceWriteResult(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            evidence_role=receipt.evidence_role,
            binding_identity=binding_identity,
            source_runner_engine_id=(
                SOURCE_RUNNER_ENGINE_ID
            ),
            production_writer_engine_id=(
                PRODUCTION_WRITER_ENGINE_ID
            ),
            evidence_identity=receipt.evidence_identity,
            service_run_identity=(
                receipt.service_run_identity
            ),
            service_run_identity_kind=(
                "bootstrap_scoped_precompletion_identity"
            ),
            iteration_identity=(
                receipt.iteration_identity
            ),
            caller_supplied_timestamp=(
                receipt.caller_supplied_timestamp
            ),
            evidence_hash=receipt.evidence_hash,
            persisted_relative_path=receipt.relative_path,
            current_pointer_relative_path=(
                receipt.current_pointer_relative_path
            ),
            read_only=True,
            execution_allowed=False,
            alerts_allowed=False,
            qseries_intake_allowed=False,
            canonical_handoff_published=False,
        )


def create_production_evidence_service_runner_binding(
    runtime_root: str | Path,
) -> OracleProductionEvidenceServiceRunnerBinding:
    production_writer = (
        create_production_runtime_evidence_writer_bindings(
            runtime_root
        )
    )

    return OracleProductionEvidenceServiceRunnerBinding(
        production_writer
    )
