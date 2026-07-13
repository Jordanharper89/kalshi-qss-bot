"""
OLA-024 Oracle Production Runtime Evidence Writer Bindings.

Production-safe filesystem persistence for Oracle runtime evidence.

Canonical logical identities remain inside persisted records.
Physical directory components are deterministic bounded hash tokens.

Oracle remains read-only.
No execution, alerts, Q Series intake, or handoff publication.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping


SCHEMA_VERSION = "OLA-024"
ENGINE_ID = "OLA-024"

STATE_ROLE = "runtime/state"
LOG_ROLE = "runtime/logs"

IDENTIFIER_PATTERN = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$"
)

FORBIDDEN_SECRET_KEYS = frozenset(
    {
        "secret",
        "password",
        "passwd",
        "pwd",
        "api_key",
        "apikey",
        "api_secret",
        "private_key",
        "privatekey",
        "access_token",
        "refresh_token",
        "auth_token",
        "authorization",
        "bearer",
        "credential",
        "credentials",
        "connection_string",
        "database_url",
        "db_url",
        "dsn",
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


class ProductionRuntimeEvidenceWriterError(ValueError):
    pass


class RuntimeRootValidationError(
    ProductionRuntimeEvidenceWriterError
):
    pass


class EvidencePathValidationError(
    ProductionRuntimeEvidenceWriterError
):
    pass


class MalformedEvidenceError(
    ProductionRuntimeEvidenceWriterError
):
    pass


class SecretEvidenceRejectedError(
    ProductionRuntimeEvidenceWriterError
):
    pass


class ImmutableEvidenceConflictError(
    ProductionRuntimeEvidenceWriterError
):
    pass


@dataclass(frozen=True)
class EvidenceWriteReceipt:
    schema_version: str
    engine_id: str
    evidence_role: str
    evidence_identity: str
    service_run_identity: str
    iteration_identity: str
    caller_supplied_timestamp: str
    evidence_hash: str
    relative_path: str
    current_pointer_relative_path: str | None
    immutable_record: bool
    atomic_current_pointer: bool
    bounded_physical_storage_path: bool
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
            "evidence_identity": self.evidence_identity,
            "service_run_identity": self.service_run_identity,
            "iteration_identity": self.iteration_identity,
            "caller_supplied_timestamp": self.caller_supplied_timestamp,
            "evidence_hash": self.evidence_hash,
            "relative_path": self.relative_path,
            "current_pointer_relative_path": (
                self.current_pointer_relative_path
            ),
            "immutable_record": self.immutable_record,
            "atomic_current_pointer": self.atomic_current_pointer,
            "bounded_physical_storage_path": (
                self.bounded_physical_storage_path
            ),
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "alerts_allowed": self.alerts_allowed,
            "qseries_intake_allowed": self.qseries_intake_allowed,
            "canonical_handoff_published": (
                self.canonical_handoff_published
            ),
        }


def _validate_json(value: Any, *, path: str) -> None:
    if value is None or isinstance(value, (str, bool, int)):
        return

    if isinstance(value, float):
        if not math.isfinite(value):
            raise MalformedEvidenceError(
                f"Non-finite numeric value forbidden at {path}"
            )
        return

    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_json(
                item,
                path=f"{path}[{index}]",
            )
        return

    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise MalformedEvidenceError(
                    f"Non-string object key at {path}"
                )

            _validate_json(
                item,
                path=f"{path}.{key}",
            )
        return

    raise MalformedEvidenceError(
        f"Unsupported evidence type at {path}: "
        f"{type(value).__name__}"
    )


def canonical_json_bytes(value: Any) -> bytes:
    _validate_json(value, path="$")

    try:
        serialized = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise MalformedEvidenceError(
            f"Canonical JSON serialization failed: {exc}"
        ) from exc

    return serialized.encode("utf-8")


def stable_hash(value: Any) -> str:
    return hashlib.sha256(
        canonical_json_bytes(value)
    ).hexdigest()


def _storage_token(
    *,
    prefix: str,
    identity_material: Mapping[str, Any],
) -> str:
    return (
        f"{prefix}-"
        f"{stable_hash(dict(identity_material))[:32]}"
    )


def _reject_secret_fields(
    value: Any,
    *,
    path: str,
) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = (
                key.strip()
                .lower()
                .replace("-", "_")
                .replace(" ", "_")
            )

            for token in FORBIDDEN_SECRET_KEYS:
                if (
                    normalized == token
                    or normalized.startswith(f"{token}_")
                    or normalized.endswith(f"_{token}")
                ):
                    raise SecretEvidenceRejectedError(
                        f"Secret-bearing field rejected at "
                        f"{path}.{key}"
                    )

            _reject_secret_fields(
                item,
                path=f"{path}.{key}",
            )

    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_secret_fields(
                item,
                path=f"{path}[{index}]",
            )


def _normalize_mapping(
    value: Mapping[str, Any],
    *,
    field_name: str,
) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise MalformedEvidenceError(
            f"{field_name} must be a mapping"
        )

    normalized = dict(value)

    _validate_json(
        normalized,
        path=f"$.{field_name}",
    )

    _reject_secret_fields(
        normalized,
        path=f"$.{field_name}",
    )

    return normalized


def _validate_identifier(
    value: str,
    *,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise EvidencePathValidationError(
            f"{field_name} must be a string"
        )

    if not IDENTIFIER_PATTERN.fullmatch(value):
        raise EvidencePathValidationError(
            f"{field_name} contains unsafe characters "
            "or invalid length"
        )

    if value in {".", ".."}:
        raise EvidencePathValidationError(
            f"{field_name} is unsafe"
        )

    return value


def _validate_timestamp(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MalformedEvidenceError(
            "caller_supplied_timestamp must be non-empty"
        )

    parsed_value = (
        f"{value[:-1]}+00:00"
        if value.endswith("Z")
        else value
    )

    try:
        parsed = datetime.fromisoformat(parsed_value)
    except ValueError as exc:
        raise MalformedEvidenceError(
            "caller_supplied_timestamp must be ISO-8601"
        ) from exc

    if (
        parsed.tzinfo is None
        or parsed.utcoffset() is None
    ):
        raise MalformedEvidenceError(
            "caller_supplied_timestamp must include timezone"
        )

    return value


def _confined_child(
    root: Path,
    *parts: str,
) -> Path:
    candidate = root.joinpath(*parts).resolve(
        strict=False
    )

    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise EvidencePathValidationError(
            "Evidence path escaped runtime root"
        ) from exc

    return candidate


def _write_immutable_json(
    path: Path,
    value: Mapping[str, Any],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = canonical_json_bytes(
        dict(value)
    ) + b"\n"

    try:
        with path.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as exc:
        raise ImmutableEvidenceConflictError(
            f"Immutable evidence already exists: {path.name}"
        ) from exc


def _atomic_replace_json(
    path: Path,
    value: Mapping[str, Any],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = canonical_json_bytes(
        dict(value)
    ) + b"\n"

    temporary_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=".current.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as temporary_file:
            temporary_file.write(data)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())

            temporary_path = Path(
                temporary_file.name
            )

        os.replace(
            temporary_path,
            path,
        )

        temporary_path = None

    finally:
        if (
            temporary_path is not None
            and temporary_path.exists()
        ):
            temporary_path.unlink()


class OracleProductionRuntimeEvidenceWriterBindings:

    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID

    def __init__(
        self,
        runtime_root: str | Path,
    ) -> None:
        raw_root = Path(runtime_root)

        if not raw_root.is_absolute():
            raise RuntimeRootValidationError(
                "runtime_root must be absolute"
            )

        self._runtime_root = raw_root.resolve(
            strict=False
        )

        self._state_root = _confined_child(
            self._runtime_root,
            "state",
        )

        self._logs_root = _confined_child(
            self._runtime_root,
            "logs",
        )

        self._state_root.mkdir(
            parents=True,
            exist_ok=True,
        )
        self._logs_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        if self._state_root == self._logs_root:
            raise RuntimeRootValidationError(
                "State and log roles must remain separate"
            )

        if self._state_root.parent != self._runtime_root:
            raise RuntimeRootValidationError(
                "State role escaped runtime root"
            )

        if self._logs_root.parent != self._runtime_root:
            raise RuntimeRootValidationError(
                "Log role escaped runtime root"
            )

    @property
    def runtime_root(self) -> Path:
        return self._runtime_root

    @property
    def state_root(self) -> Path:
        return self._state_root

    @property
    def logs_root(self) -> Path:
        return self._logs_root

    def describe_boundary(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "state_role": STATE_ROLE,
            "log_role": LOG_ROLE,
            "runtime_root_confinement": True,
            "strict_state_log_role_separation": True,
            "immutable_evidence_records": True,
            "canonical_json_serialization": True,
            "deterministic_stable_hashing": True,
            "canonical_logical_identities_preserved": True,
            "bounded_physical_storage_paths": True,
            "deterministic_physical_storage_paths": True,
            "atomic_current_state_pointer_replacement": True,
            "immutable_log_evidence": True,
            "caller_supplied_timestamps_required": True,
            "evidence_identity_required": True,
            "service_run_identity_required": True,
            "iteration_identity_required": True,
            "polling_state_lineage_preserved": True,
            "canonical_clock_lineage_preserved": True,
            "replay_metadata_preserved": True,
            "audit_metadata_preserved": True,
            "fail_closed_path_validation": True,
            "fail_closed_malformed_evidence": True,
            "secret_bearing_evidence_rejected": True,
            **dict(ARCHITECTURE_FLAGS),
        }

    def write_state_evidence(
        self,
        *,
        evidence_identity: str,
        service_run_identity: str,
        iteration_identity: str,
        caller_supplied_timestamp: str,
        evidence: Mapping[str, Any],
        polling_state_lineage: Mapping[str, Any],
        canonical_clock_lineage: Mapping[str, Any],
        replay_metadata: Mapping[str, Any],
        audit_metadata: Mapping[str, Any],
    ) -> EvidenceWriteReceipt:
        return self._write_evidence(
            evidence_role=STATE_ROLE,
            evidence_identity=evidence_identity,
            service_run_identity=service_run_identity,
            iteration_identity=iteration_identity,
            caller_supplied_timestamp=caller_supplied_timestamp,
            evidence=evidence,
            polling_state_lineage=polling_state_lineage,
            canonical_clock_lineage=canonical_clock_lineage,
            replay_metadata=replay_metadata,
            audit_metadata=audit_metadata,
            current_pointer_required=True,
        )

    def write_log_evidence(
        self,
        *,
        evidence_identity: str,
        service_run_identity: str,
        iteration_identity: str,
        caller_supplied_timestamp: str,
        evidence: Mapping[str, Any],
        polling_state_lineage: Mapping[str, Any],
        canonical_clock_lineage: Mapping[str, Any],
        replay_metadata: Mapping[str, Any],
        audit_metadata: Mapping[str, Any],
    ) -> EvidenceWriteReceipt:
        return self._write_evidence(
            evidence_role=LOG_ROLE,
            evidence_identity=evidence_identity,
            service_run_identity=service_run_identity,
            iteration_identity=iteration_identity,
            caller_supplied_timestamp=caller_supplied_timestamp,
            evidence=evidence,
            polling_state_lineage=polling_state_lineage,
            canonical_clock_lineage=canonical_clock_lineage,
            replay_metadata=replay_metadata,
            audit_metadata=audit_metadata,
            current_pointer_required=False,
        )

    def _write_evidence(
        self,
        *,
        evidence_role: str,
        evidence_identity: str,
        service_run_identity: str,
        iteration_identity: str,
        caller_supplied_timestamp: str,
        evidence: Mapping[str, Any],
        polling_state_lineage: Mapping[str, Any],
        canonical_clock_lineage: Mapping[str, Any],
        replay_metadata: Mapping[str, Any],
        audit_metadata: Mapping[str, Any],
        current_pointer_required: bool,
    ) -> EvidenceWriteReceipt:
        evidence_identity = _validate_identifier(
            evidence_identity,
            field_name="evidence_identity",
        )

        service_run_identity = _validate_identifier(
            service_run_identity,
            field_name="service_run_identity",
        )

        iteration_identity = _validate_identifier(
            iteration_identity,
            field_name="iteration_identity",
        )

        caller_supplied_timestamp = _validate_timestamp(
            caller_supplied_timestamp
        )

        evidence = _normalize_mapping(
            evidence,
            field_name="evidence",
        )

        polling_state_lineage = _normalize_mapping(
            polling_state_lineage,
            field_name="polling_state_lineage",
        )

        canonical_clock_lineage = _normalize_mapping(
            canonical_clock_lineage,
            field_name="canonical_clock_lineage",
        )

        replay_metadata = _normalize_mapping(
            replay_metadata,
            field_name="replay_metadata",
        )

        audit_metadata = _normalize_mapping(
            audit_metadata,
            field_name="audit_metadata",
        )

        record_without_hash = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "evidence_role": evidence_role,
            "evidence_identity": evidence_identity,
            "service_run_identity": service_run_identity,
            "iteration_identity": iteration_identity,
            "caller_supplied_timestamp": (
                caller_supplied_timestamp
            ),
            "polling_state_lineage": polling_state_lineage,
            "canonical_clock_lineage": (
                canonical_clock_lineage
            ),
            "replay_metadata": replay_metadata,
            "audit_metadata": audit_metadata,
            "evidence": evidence,
            **dict(ARCHITECTURE_FLAGS),
        }

        evidence_hash = stable_hash(
            record_without_hash
        )

        record = {
            **record_without_hash,
            "evidence_hash": evidence_hash,
        }

        if evidence_role == STATE_ROLE:
            role_root = self._state_root
            filename_prefix = "state"

        elif evidence_role == LOG_ROLE:
            role_root = self._logs_root
            filename_prefix = "log"

        else:
            raise EvidencePathValidationError(
                f"Unsupported evidence role: {evidence_role}"
            )

        run_token = _storage_token(
            prefix="run",
            identity_material={
                "service_run_identity": service_run_identity,
            },
        )

        iteration_token = _storage_token(
            prefix="iteration",
            identity_material={
                "service_run_identity": service_run_identity,
                "iteration_identity": iteration_identity,
            },
        )

        run_root = _confined_child(
            role_root,
            run_token,
        )

        iteration_root = _confined_child(
            run_root,
            iteration_token,
        )

        immutable_path = _confined_child(
            iteration_root,
            f"{filename_prefix}--{evidence_hash}.json",
        )

        _write_immutable_json(
            immutable_path,
            record,
        )

        current_pointer_path: Path | None = None

        if current_pointer_required:
            current_pointer_path = _confined_child(
                self._state_root,
                "current.json",
            )

            relative_evidence_path = (
                immutable_path.relative_to(
                    self._runtime_root
                ).as_posix()
            )

            pointer_without_hash = {
                "schema_version": SCHEMA_VERSION,
                "engine_id": ENGINE_ID,
                "pointer_role": "runtime/state/current",
                "evidence_role": evidence_role,
                "evidence_identity": evidence_identity,
                "service_run_identity": service_run_identity,
                "iteration_identity": iteration_identity,
                "caller_supplied_timestamp": (
                    caller_supplied_timestamp
                ),
                "evidence_hash": evidence_hash,
                "evidence_relative_path": (
                    relative_evidence_path
                ),
                **dict(ARCHITECTURE_FLAGS),
            }

            pointer = {
                **pointer_without_hash,
                "pointer_hash": stable_hash(
                    pointer_without_hash
                ),
            }

            _atomic_replace_json(
                current_pointer_path,
                pointer,
            )

        return EvidenceWriteReceipt(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            evidence_role=evidence_role,
            evidence_identity=evidence_identity,
            service_run_identity=service_run_identity,
            iteration_identity=iteration_identity,
            caller_supplied_timestamp=(
                caller_supplied_timestamp
            ),
            evidence_hash=evidence_hash,
            relative_path=immutable_path.relative_to(
                self._runtime_root
            ).as_posix(),
            current_pointer_relative_path=(
                current_pointer_path.relative_to(
                    self._runtime_root
                ).as_posix()
                if current_pointer_path is not None
                else None
            ),
            immutable_record=True,
            atomic_current_pointer=(
                current_pointer_required
            ),
            bounded_physical_storage_path=True,
            read_only=True,
            execution_allowed=False,
            alerts_allowed=False,
            qseries_intake_allowed=False,
            canonical_handoff_published=False,
        )


def create_production_runtime_evidence_writer_bindings(
    runtime_root: str | Path,
) -> OracleProductionRuntimeEvidenceWriterBindings:
    return OracleProductionRuntimeEvidenceWriterBindings(
        runtime_root
    )
