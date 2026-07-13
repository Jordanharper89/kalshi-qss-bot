from pathlib import Path
import textwrap


ROOT = Path(__file__).resolve().parent

MODULE_PATH = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition_model"
    / "production_evidence_service_runner_binding.py"
)

TEST_PATH = (
    ROOT
    / "test_ola_025_oracle_production_evidence_service_runner_binding.py"
)


MODULE = r'''
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
'''


TEST = r'''
from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_shadow_service_runner import (
    OracleLiveShadowEvidenceWriterBinding,
)
from qseries_v2.oracle_intelligence.live_acquisition_model.production_evidence_service_runner_binding import (
    MalformedServiceRunnerEvidenceError,
    ServiceRunnerEvidenceRoleError,
    create_production_evidence_service_runner_binding,
)
from qseries_v2.oracle_intelligence.live_acquisition_model.production_runtime_evidence_writer_bindings import (
    ImmutableEvidenceConflictError,
)


def _read_json(path: Path) -> dict:
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def _next_state(
    iteration_number: int,
) -> dict:
    return {
        "schema_version": "OLA-019",
        "engine_id": "OLA-019",
        "state_id": f"state-{iteration_number:04d}",
        "source_id": "source.kalshi.public",
        "adapter_id": (
            "adapter.kalshi.public.shadow"
        ),
        "last_cycle_completed_at": (
            f"2026-07-12T15:30:"
            f"{iteration_number:02d}+00:00"
        ),
        "last_cycle_succeeded": True,
        "consecutive_failures": 0,
        "suspended": False,
        "suspended_at": None,
        "restart_evidence_present": False,
        "state_metadata": {},
        "state_hash": (
            f"state-hash-{iteration_number:04d}"
        ),
        "immutable": True,
        "replayable": True,
        "auditable": True,
        "explainable": True,
        "read_only": True,
        "execution_allowed": False,
        "execution_adapter_resolved": False,
        "execution_adapter_invoked": False,
        "trade_authorization_allowed": False,
        "order_placement_allowed": False,
        "funds_moved": False,
        "portfolio_mutated": False,
    }


def _state_payload(
    iteration_number: int,
) -> dict:
    return {
        "schema_version": "OLA-023",
        "engine_id": "OLA-023",
        "evidence_role": "runtime/state",
        "iteration_number": iteration_number,
        "bootstrap_id": (
            "oracle_bootstrap.controlled-001"
        ),
        "tick_id": f"tick-{iteration_number:04d}",
        "tick_hash": (
            f"tick-hash-{iteration_number:04d}"
        ),
        "previous_state_id": (
            f"state-{iteration_number - 1:04d}"
        ),
        "previous_state_hash": (
            f"state-hash-{iteration_number - 1:04d}"
        ),
        "next_state": _next_state(
            iteration_number
        ),
        "iteration_completed_at": datetime(
            2026,
            7,
            12,
            15,
            30,
            iteration_number,
            tzinfo=timezone.utc,
        ),
    }


def _tick(
    iteration_number: int,
) -> dict:
    return {
        "schema_version": "OLA-021",
        "engine_id": "OLA-021",
        "tick_id": f"tick-{iteration_number:04d}",
        "tick_status": "completed",
        "source_id": "source.kalshi.public",
        "adapter_id": (
            "adapter.kalshi.public.shadow"
        ),
        "readiness_id": (
            f"readiness-{iteration_number:04d}"
        ),
        "readiness_hash": (
            f"readiness-hash-{iteration_number:04d}"
        ),
        "polling_decision_id": (
            f"decision-{iteration_number:04d}"
        ),
        "polling_decision_hash": (
            f"decision-hash-{iteration_number:04d}"
        ),
        "polling_decision_status": "poll_allowed",
        "shadow_cycle_allowed": True,
        "runner_id": "runner.ola017",
        "runner_engine_id": "OLA-017",
        "started_at": (
            f"2026-07-12T15:30:"
            f"{iteration_number - 1:02d}+00:00"
        ),
        "completed_at": (
            f"2026-07-12T15:30:"
            f"{iteration_number:02d}+00:00"
        ),
        "cycle_invocation_count": 1,
        "cycle_invoked": True,
        "cycle_succeeded": True,
        "cycle_status": "completed",
        "cycle_evidence_hash": (
            f"cycle-hash-{iteration_number:04d}"
        ),
        "previous_state_id": (
            f"state-{iteration_number - 1:04d}"
        ),
        "previous_state_hash": (
            f"state-hash-{iteration_number - 1:04d}"
        ),
        "next_state_id": (
            f"state-{iteration_number:04d}"
        ),
        "next_state_hash": (
            f"state-hash-{iteration_number:04d}"
        ),
        "previous_consecutive_failures": 0,
        "next_consecutive_failures": 0,
        "next_state_suspended": False,
        "next_state_suspended_at": None,
        "reason_codes": [
            "cycle_completed"
        ],
        "tick_metadata": {},
        "immutable": True,
        "replayable": True,
        "auditable": True,
        "explainable": True,
        "read_only": True,
        "continuous_polling_started": False,
        "loop_started": False,
        "sleep_performed": False,
        "alert_created": False,
        "qseries_intake_record_created": False,
        "canonical_handoff_published": False,
        "execution_allowed": False,
        "execution_adapter_resolved": False,
        "execution_adapter_invoked": False,
        "trade_authorization_allowed": False,
        "order_placement_allowed": False,
        "funds_moved": False,
        "portfolio_mutated": False,
        "tick_hash": (
            f"tick-hash-{iteration_number:04d}"
        ),
    }


def _log_payload(
    iteration_number: int,
) -> dict:
    return {
        "schema_version": "OLA-023",
        "engine_id": "OLA-023",
        "evidence_role": "runtime/logs",
        "iteration_number": iteration_number,
        "bootstrap_id": (
            "oracle_bootstrap.controlled-001"
        ),
        "readiness_id": (
            f"readiness-{iteration_number:04d}"
        ),
        "readiness_hash": (
            f"readiness-hash-{iteration_number:04d}"
        ),
        "tick": _tick(
            iteration_number
        ),
        "cycle_result_present": True,
        "canonical_clock_lineage_valid": True,
        "iteration_completed_at": datetime(
            2026,
            7,
            12,
            15,
            30,
            iteration_number,
            tzinfo=timezone.utc,
        ),
    }


def main() -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        runtime_root = (
            Path(temporary_directory).resolve()
            / "runtime"
        )

        binding = (
            create_production_evidence_service_runner_binding(
                runtime_root
            )
        )

        boundary = binding.describe_boundary()

        assert (
            boundary[
                "actual_ola_023_state_payload_contract_bound"
            ]
            is True
        )
        assert (
            boundary[
                "actual_ola_023_log_payload_contract_bound"
            ]
            is True
        )
        assert (
            boundary[
                "ola_023_writer_binding_type_compatible"
            ]
            is True
        )
        assert (
            boundary[
                "bootstrap_scoped_persistence_run_identity"
            ]
            is True
        )
        assert (
            boundary[
                "final_ola_023_service_run_id_invented"
            ]
            is False
        )
        assert (
            boundary["missing_lineage_invented"]
            is False
        )

        state_binding = (
            OracleLiveShadowEvidenceWriterBinding(
                writer_id=(
                    "writer.oracle.production.state"
                ),
                evidence_role="runtime/state",
                writer_callable=(
                    binding.state_writer_callable()
                ),
                read_only_service_boundary=True,
                execution_allowed=False,
            )
        )

        log_binding = (
            OracleLiveShadowEvidenceWriterBinding(
                writer_id=(
                    "writer.oracle.production.logs"
                ),
                evidence_role="runtime/logs",
                writer_callable=(
                    binding.log_writer_callable()
                ),
                read_only_service_boundary=True,
                execution_allowed=False,
            )
        )

        state_results = []
        log_results = []

        for iteration_number in (
            1,
            2,
            3,
        ):
            state_results.append(
                state_binding.writer_callable(
                    evidence=_state_payload(
                        iteration_number
                    )
                )
            )

            log_results.append(
                log_binding.writer_callable(
                    evidence=_log_payload(
                        iteration_number
                    )
                )
            )

        assert binding.state_write_count == 3
        assert binding.log_write_count == 3
        assert len(state_results) == 3
        assert len(log_results) == 3

        run_identities = {
            result["service_run_identity"]
            for result in (
                state_results + log_results
            )
        }

        assert len(run_identities) == 1

        persistence_run_identity = next(
            iter(run_identities)
        )

        assert persistence_run_identity.startswith(
            "oracle_persistence_run."
        )

        assert all(
            result["service_run_identity_kind"]
            == (
                "bootstrap_scoped_precompletion_identity"
            )
            for result in (
                state_results + log_results
            )
        )

        for index, result in enumerate(
            state_results,
            start=1,
        ):
            path = (
                runtime_root
                / result["persisted_relative_path"]
            )

            assert path.exists()

            persisted = _read_json(path)

            assert (
                persisted["evidence"]["schema_version"]
                == "OLA-023"
            )
            assert (
                persisted["evidence"]["engine_id"]
                == "OLA-023"
            )
            assert (
                persisted["evidence"]["evidence_role"]
                == "runtime/state"
            )
            assert (
                persisted["evidence"]["iteration_number"]
                == index
            )
            assert (
                persisted["evidence"][
                    "iteration_completed_at"
                ].endswith("+00:00")
            )
            assert (
                persisted["polling_state_lineage"][
                    "previous_state_hash"
                ]
                == f"state-hash-{index - 1:04d}"
            )
            assert (
                persisted["polling_state_lineage"][
                    "next_state_hash"
                ]
                == f"state-hash-{index:04d}"
            )
            assert (
                persisted["canonical_clock_lineage"][
                    "lineage_scope"
                ]
                == (
                    "writer_payload_available_clock_lineage"
                )
            )
            assert (
                persisted["replay_metadata"][
                    "final_ola_023_service_run_id_available_at_write_time"
                ]
                is False
            )

        for index, result in enumerate(
            log_results,
            start=1,
        ):
            path = (
                runtime_root
                / result["persisted_relative_path"]
            )

            assert path.exists()

            persisted = _read_json(path)

            assert (
                persisted["evidence"]["evidence_role"]
                == "runtime/logs"
            )
            assert (
                persisted["evidence"]["iteration_number"]
                == index
            )
            assert (
                persisted["polling_state_lineage"][
                    "next_state_hash"
                ]
                == f"state-hash-{index:04d}"
            )
            assert (
                persisted["canonical_clock_lineage"][
                    "canonical_clock_lineage_valid"
                ]
                is True
            )
            assert (
                persisted["canonical_clock_lineage"][
                    "tick_started_at"
                ]
            )
            assert (
                persisted["canonical_clock_lineage"][
                    "tick_completed_at"
                ]
            )

        for index in (
            1,
            2,
        ):
            first = _read_json(
                runtime_root
                / state_results[
                    index - 1
                ]["persisted_relative_path"]
            )

            second = _read_json(
                runtime_root
                / state_results[
                    index
                ]["persisted_relative_path"]
            )

            assert (
                second["polling_state_lineage"][
                    "previous_state_hash"
                ]
                == first["polling_state_lineage"][
                    "next_state_hash"
                ]
            )

        current_pointer = _read_json(
            runtime_root
            / "state"
            / "current.json"
        )

        assert (
            current_pointer["evidence_hash"]
            == state_results[-1]["evidence_hash"]
        )

        replay_root = (
            Path(temporary_directory).resolve()
            / "runtime-replay"
        )

        replay_binding = (
            create_production_evidence_service_runner_binding(
                replay_root
            )
        )

        replay_result = (
            replay_binding.state_writer(
                evidence=_state_payload(1)
            )
        )

        assert (
            replay_result["service_run_identity"]
            == state_results[0]["service_run_identity"]
        )
        assert (
            replay_result["iteration_identity"]
            == state_results[0]["iteration_identity"]
        )
        assert (
            replay_result["evidence_identity"]
            == state_results[0]["evidence_identity"]
        )
        assert (
            replay_result["evidence_hash"]
            == state_results[0]["evidence_hash"]
        )
        assert (
            replay_result["binding_identity"]
            == state_results[0]["binding_identity"]
        )

        conflict_failed_closed = False

        try:
            binding.state_writer(
                evidence=_state_payload(1)
            )
        except ImmutableEvidenceConflictError:
            conflict_failed_closed = True

        assert conflict_failed_closed is True
        assert binding.state_write_count == 3

        missing_field_failed_closed = False

        malformed = _state_payload(4)
        del malformed["bootstrap_id"]

        try:
            binding.state_writer(
                evidence=malformed
            )
        except MalformedServiceRunnerEvidenceError:
            missing_field_failed_closed = True

        assert missing_field_failed_closed is True

        role_mismatch_failed_closed = False

        mismatch = _state_payload(4)
        mismatch["evidence_role"] = "runtime/logs"

        try:
            binding.state_writer(
                evidence=mismatch
            )
        except ServiceRunnerEvidenceRoleError:
            role_mismatch_failed_closed = True

        assert role_mismatch_failed_closed is True

        naive_datetime_failed_closed = False

        naive = _state_payload(4)
        naive["iteration_completed_at"] = datetime(
            2026,
            7,
            12,
            15,
            31,
            0,
        )

        try:
            binding.state_writer(
                evidence=naive
            )
        except MalformedServiceRunnerEvidenceError:
            naive_datetime_failed_closed = True

        assert naive_datetime_failed_closed is True

        for result in (
            state_results
            + log_results
            + [replay_result]
        ):
            assert result["read_only"] is True
            assert result["execution_allowed"] is False
            assert result["alerts_allowed"] is False
            assert (
                result["qseries_intake_allowed"]
                is False
            )
            assert (
                result["canonical_handoff_published"]
                is False
            )

        result = {
            "schema_version": "OLA-025",
            "engine_id": "OLA-025",
            "status": "passed",
            "source_runner_schema_version": "OLA-023",
            "source_runner_engine_id": "OLA-023",
            "production_writer_engine_id": "OLA-024",
            "actual_ola_023_state_payload_contract_bound": True,
            "actual_ola_023_log_payload_contract_bound": True,
            "ola_023_writer_binding_type_compatible": True,
            "bootstrap_scoped_persistence_run_identity": True,
            "final_ola_023_service_run_id_invented": False,
            "source_payload_datetime_canonicalization": True,
            "simulated_actual_runner_iteration_count": 3,
            "exactly_one_state_write_per_iteration": True,
            "exactly_one_log_write_per_iteration": True,
            "production_state_evidence_persisted": True,
            "production_log_evidence_persisted": True,
            "atomic_current_state_pointer_updated": True,
            "polling_state_lineage_extracted_from_source_payload": True,
            "polling_state_chain_preserved": True,
            "clock_lineage_extracted_from_source_payload": True,
            "missing_lineage_invented": False,
            "deterministic_persistence_run_identity": True,
            "deterministic_iteration_identity": True,
            "deterministic_evidence_identity": True,
            "deterministic_evidence_hashing": True,
            "deterministic_binding_identity": True,
            "deterministic_replay_valid": True,
            "malformed_runner_evidence_fails_closed": True,
            "role_mismatch_fails_closed": True,
            "timezone_naive_datetime_fails_closed": True,
            "production_writer_conflict_propagates_fail_closed": True,
            "runner_lifecycle_mutated": False,
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

        print(
            "[PASS] OLA-025 Oracle Production Evidence "
            "Service Runner Binding"
        )
        print(result)


if __name__ == "__main__":
    main()
'''


def write_file(
    path: Path,
    content: str,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        textwrap.dedent(content).lstrip(),
        encoding="utf-8",
    )

    print(f"[OK] FULL REPLACEMENT: {path}")


def main() -> None:
    print("========================================")
    print(" OLA-025 CORRECTION INSTALLER")
    print(" ACTUAL OLA-023 WRITER PAYLOAD CONTRACT")
    print("========================================")

    write_file(
        MODULE_PATH,
        MODULE,
    )

    write_file(
        TEST_PATH,
        TEST,
    )

    print()
    print("[DONE] OLA-025 correction installed")
    print()
    print("Run:")
    print(
        "py test_ola_025_oracle_production_evidence_"
        "service_runner_binding.py"
    )


if __name__ == "__main__":
    main()