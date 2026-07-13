"""
OLA-028 Oracle Launch Readiness Artifact Store.

Durable production boundary between OLA-026 launch readiness and
OLA-027 controlled unattended launch.

The store:
- accepts only a valid OLA-026 readiness record
- requires launch_ready=True and readiness_status="ready"
- preserves the complete OLA-026 canonical record
- writes immutable hash-addressed readiness evidence
- atomically replaces only the mutable current pointer
- reloads and reconstructs the exact OLA-026 record
- verifies readiness_hash before returning launch evidence
- fails closed on malformed, tampered, missing, or secret-bearing data

This module never starts Oracle.

Oracle remains read-only.
No alerts.
No Q Series intake.
No canonical handoff publication.
No execution capability.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import tempfile
from typing import Any, Mapping

from .oracle_shadow_launch_readiness_gate import (
    OracleShadowLaunchReadinessRecord,
)


SCHEMA_VERSION = "OLA-028"
ENGINE_ID = "OLA-028"

ARTIFACT_DIRECTORY_NAME = "launch_readiness"
CURRENT_POINTER_FILENAME = "current.json"

FORBIDDEN_SECRET_KEYS = frozenset(
    {
        "password",
        "passwd",
        "secret",
        "api_key",
        "private_key",
        "signing_key",
        "dsn",
        "database_url",
        "connection_string",
        "token",
    }
)


class OracleLaunchReadinessArtifactStoreError(
    ValueError
):
    pass


class OracleLaunchReadinessArtifactStoreBlocked(
    RuntimeError
):
    pass


@dataclass(frozen=True)
class OracleLaunchReadinessArtifactReceipt:
    schema_version: str
    engine_id: str
    artifact_status: str
    readiness_schema_version: str
    readiness_engine_id: str
    readiness_hash: str
    artifact_identity: str
    artifact_hash: str
    artifact_relative_path: str
    current_pointer_relative_path: str
    immutable_artifact_written: bool
    current_pointer_updated: bool
    read_only: bool
    alerts_allowed: bool
    qseries_intake_allowed: bool
    canonical_handoff_published: bool
    execution_allowed: bool
    execution_adapter_resolved: bool
    execution_adapter_invoked: bool
    trade_authorization_allowed: bool
    order_placement_allowed: bool
    funds_moved: bool
    portfolio_mutated: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "artifact_status": self.artifact_status,
            "readiness_schema_version": (
                self.readiness_schema_version
            ),
            "readiness_engine_id": (
                self.readiness_engine_id
            ),
            "readiness_hash": self.readiness_hash,
            "artifact_identity": self.artifact_identity,
            "artifact_hash": self.artifact_hash,
            "artifact_relative_path": (
                self.artifact_relative_path
            ),
            "current_pointer_relative_path": (
                self.current_pointer_relative_path
            ),
            "immutable_artifact_written": (
                self.immutable_artifact_written
            ),
            "current_pointer_updated": (
                self.current_pointer_updated
            ),
            "read_only": self.read_only,
            "alerts_allowed": self.alerts_allowed,
            "qseries_intake_allowed": (
                self.qseries_intake_allowed
            ),
            "canonical_handoff_published": (
                self.canonical_handoff_published
            ),
            "execution_allowed": self.execution_allowed,
            "execution_adapter_resolved": (
                self.execution_adapter_resolved
            ),
            "execution_adapter_invoked": (
                self.execution_adapter_invoked
            ),
            "trade_authorization_allowed": (
                self.trade_authorization_allowed
            ),
            "order_placement_allowed": (
                self.order_placement_allowed
            ),
            "funds_moved": self.funds_moved,
            "portfolio_mutated": self.portfolio_mutated,
        }


def _canonicalize(
    value: Any,
) -> Any:
    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        if not math.isfinite(value):
            raise OracleLaunchReadinessArtifactStoreError(
                "non-finite floats are not canonical"
            )

        return json.loads(
            json.dumps(
                value,
                allow_nan=False,
            )
        )

    if isinstance(value, str):
        return value

    if isinstance(value, Path):
        return value.as_posix()

    if isinstance(value, Mapping):
        result = {}

        for key in sorted(value):
            if not isinstance(key, str):
                raise OracleLaunchReadinessArtifactStoreError(
                    "canonical mapping keys must be strings"
                )

            normalized_key = key.strip().lower()

            if normalized_key in FORBIDDEN_SECRET_KEYS:
                raise OracleLaunchReadinessArtifactStoreBlocked(
                    "secret-bearing key rejected: "
                    f"{key}"
                )

            result[key] = _canonicalize(
                value[key]
            )

        return result

    if isinstance(value, (list, tuple)):
        return [
            _canonicalize(item)
            for item in value
        ]

    raise OracleLaunchReadinessArtifactStoreError(
        "unsupported canonical value type: "
        f"{type(value).__name__}"
    )


def canonical_json(
    value: Any,
) -> str:
    return json.dumps(
        _canonicalize(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def stable_hash(
    value: Any,
) -> str:
    return sha256(
        canonical_json(value).encode("utf-8")
    ).hexdigest()


def _validate_runtime_root(
    runtime_root: str | Path,
) -> Path:
    root = Path(
        runtime_root
    )

    if not root.is_absolute():
        raise OracleLaunchReadinessArtifactStoreError(
            "runtime_root must be absolute"
        )

    return root.resolve(
        strict=False
    )


def _validate_readiness_record(
    record: Any,
) -> OracleShadowLaunchReadinessRecord:
    if not isinstance(
        record,
        OracleShadowLaunchReadinessRecord,
    ):
        raise OracleLaunchReadinessArtifactStoreError(
            "readiness_record must be an "
            "OracleShadowLaunchReadinessRecord"
        )

    if record.schema_version != "OLA-026":
        raise OracleLaunchReadinessArtifactStoreBlocked(
            "readiness schema must be OLA-026"
        )

    if record.engine_id != "OLA-026":
        raise OracleLaunchReadinessArtifactStoreBlocked(
            "readiness engine must be OLA-026"
        )

    if record.readiness_status != "ready":
        raise OracleLaunchReadinessArtifactStoreBlocked(
            "readiness_status must be ready"
        )

    if record.launch_ready is not True:
        raise OracleLaunchReadinessArtifactStoreBlocked(
            "launch_ready must be true"
        )

    if record.unattended_collection_started is not False:
        raise OracleLaunchReadinessArtifactStoreBlocked(
            "readiness artifact must predate unattended launch"
        )

    if record.verify_readiness_hash() is not True:
        raise OracleLaunchReadinessArtifactStoreBlocked(
            "readiness hash verification failed"
        )

    if record.read_only is not True:
        raise OracleLaunchReadinessArtifactStoreBlocked(
            "Oracle read_only invariant failed"
        )

    forbidden_values = (
        record.alerts_allowed,
        record.qseries_intake_allowed,
        record.canonical_handoff_published,
        record.execution_allowed,
        record.execution_adapter_resolved,
        record.execution_adapter_invoked,
        record.trade_authorization_allowed,
        record.order_placement_allowed,
        record.funds_moved,
        record.portfolio_mutated,
    )

    if any(
        value is not False
        for value in forbidden_values
    ):
        raise OracleLaunchReadinessArtifactStoreBlocked(
            "readiness record contains forbidden authority"
        )

    return record


def _artifact_directory(
    runtime_root: Path,
) -> Path:
    return (
        runtime_root
        / "state"
        / ARTIFACT_DIRECTORY_NAME
    )


def _assert_confined(
    *,
    runtime_root: Path,
    path: Path,
) -> None:
    resolved = path.resolve(
        strict=False
    )

    expected_root = (
        runtime_root
        / "state"
        / ARTIFACT_DIRECTORY_NAME
    ).resolve(
        strict=False
    )

    try:
        resolved.relative_to(
            expected_root
        )
    except ValueError as exc:
        raise OracleLaunchReadinessArtifactStoreBlocked(
            "launch readiness path escaped runtime/state"
        ) from exc


def _write_immutable_json(
    path: Path,
    value: Mapping[str, Any],
) -> bool:
    payload = canonical_json(
        value
    ).encode("utf-8")

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:
        with path.open("xb") as file_handle:
            file_handle.write(payload)
            file_handle.flush()
            os.fsync(
                file_handle.fileno()
            )

        return True

    except FileExistsError:
        existing = path.read_bytes()

        if existing != payload:
            raise OracleLaunchReadinessArtifactStoreBlocked(
                "immutable readiness artifact conflict"
            )

        return False


def _atomic_replace_json(
    path: Path,
    value: Mapping[str, Any],
) -> None:
    payload = canonical_json(
        value
    ).encode("utf-8")

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".ola028-",
        suffix=".tmp",
        dir=str(path.parent),
    )

    temporary_path = Path(
        temporary_name
    )

    try:
        with os.fdopen(
            descriptor,
            "wb",
        ) as file_handle:
            file_handle.write(payload)
            file_handle.flush()
            os.fsync(
                file_handle.fileno()
            )

        os.replace(
            temporary_path,
            path,
        )

    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def _read_json_mapping(
    path: Path,
) -> dict[str, Any]:
    try:
        raw = path.read_text(
            encoding="utf-8"
        )

        parsed = json.loads(
            raw
        )

    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
    ) as exc:
        raise OracleLaunchReadinessArtifactStoreBlocked(
            "malformed launch readiness artifact"
        ) from exc

    if not isinstance(
        parsed,
        dict,
    ):
        raise OracleLaunchReadinessArtifactStoreBlocked(
            "launch readiness artifact must be a mapping"
        )

    canonical = _canonicalize(
        parsed
    )

    if not isinstance(
        canonical,
        dict,
    ):
        raise OracleLaunchReadinessArtifactStoreBlocked(
            "canonical launch readiness artifact invalid"
        )

    return canonical


def _reconstruct_readiness_record(
    payload: Mapping[str, Any],
) -> OracleShadowLaunchReadinessRecord:
    expected_fields = {
        "schema_version",
        "engine_id",
        "readiness_status",
        "launch_ready",
        "live_read_readiness_passed",
        "public_endpoint_only",
        "authentication_not_used",
        "one_live_get_probe_observed",
        "source_reachable",
        "source_control_acquisition_allowed",
        "service_isolation_passed",
        "oracle_service_id",
        "qseries_service_id",
        "separate_process_required",
        "oracle_execution_authority",
        "direct_execution_import_allowed",
        "qseries_oracle_history_mutation_allowed",
        "bootstrap_readiness_passed",
        "bootstrap_status",
        "service_start_allowed",
        "runtime_state_role_valid",
        "runtime_logs_role_valid",
        "production_evidence_gate_passed",
        "actual_ola_023_runner_proven",
        "ola_025_actual_payload_binding_proven",
        "ola_024_production_persistence_proven",
        "exactly_one_state_write_per_iteration_proven",
        "exactly_one_log_write_per_iteration_proven",
        "current_state_pointer_proven",
        "polling_state_chain_proven",
        "canonical_clock_lineage_proven",
        "deterministic_replay_proven",
        "immutable_evidence_proven",
        "replayable_evidence_proven",
        "audit_evidence_proven",
        "explicit_stop_proven",
        "runtime_root_ready",
        "runtime_state_directory_ready",
        "runtime_logs_directory_ready",
        "unattended_collection_started",
        "alerts_allowed",
        "qseries_intake_allowed",
        "canonical_handoff_published",
        "read_only",
        "execution_allowed",
        "execution_adapter_resolved",
        "execution_adapter_invoked",
        "trade_authorization_allowed",
        "order_placement_allowed",
        "funds_moved",
        "portfolio_mutated",
        "reason_codes",
        "source_evidence_hashes",
        "readiness_hash",
        "immutable",
        "replayable",
        "auditable",
        "explainable",
    }

    if set(payload) != expected_fields:
        raise OracleLaunchReadinessArtifactStoreBlocked(
            "launch readiness artifact field contract mismatch"
        )

    reason_codes = payload[
        "reason_codes"
    ]

    source_evidence_hashes = payload[
        "source_evidence_hashes"
    ]

    if not isinstance(
        reason_codes,
        list,
    ) or not all(
        isinstance(item, str)
        and item.strip()
        for item in reason_codes
    ):
        raise OracleLaunchReadinessArtifactStoreBlocked(
            "reason_codes are malformed"
        )

    if not isinstance(
        source_evidence_hashes,
        dict,
    ) or not all(
        isinstance(key, str)
        and key.strip()
        and isinstance(value, str)
        and value.strip()
        for key, value in source_evidence_hashes.items()
    ):
        raise OracleLaunchReadinessArtifactStoreBlocked(
            "source_evidence_hashes are malformed"
        )

    reconstructed = dict(
        payload
    )

    reconstructed["reason_codes"] = tuple(
        reason_codes
    )

    reconstructed["source_evidence_hashes"] = tuple(
        (
            key,
            source_evidence_hashes[key],
        )
        for key in sorted(
            source_evidence_hashes
        )
    )

    try:
        record = OracleShadowLaunchReadinessRecord(
            **reconstructed
        )

    except TypeError as exc:
        raise OracleLaunchReadinessArtifactStoreBlocked(
            "OLA-026 readiness reconstruction failed"
        ) from exc

    return _validate_readiness_record(
        record
    )


class OracleLaunchReadinessArtifactStore:
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID

    read_only = True
    alerts_allowed = False
    qseries_intake_allowed = False
    canonical_handoff_published = False
    execution_allowed = False
    execution_adapter_resolved = False
    execution_adapter_invoked = False
    trade_authorization_allowed = False
    order_placement_allowed = False
    funds_moved = False
    portfolio_mutated = False

    def __init__(
        self,
        *,
        runtime_root: str | Path,
    ) -> None:
        self._runtime_root = _validate_runtime_root(
            runtime_root
        )

        self._artifact_directory = (
            _artifact_directory(
                self._runtime_root
            )
        )

        self._current_pointer_path = (
            self._artifact_directory
            / CURRENT_POINTER_FILENAME
        )

        _assert_confined(
            runtime_root=self._runtime_root,
            path=self._artifact_directory,
        )

        _assert_confined(
            runtime_root=self._runtime_root,
            path=self._current_pointer_path,
        )

    @property
    def runtime_root(self) -> Path:
        return self._runtime_root

    @property
    def artifact_directory(self) -> Path:
        return self._artifact_directory

    @property
    def current_pointer_path(self) -> Path:
        return self._current_pointer_path

    def persist(
        self,
        *,
        readiness_record: (
            OracleShadowLaunchReadinessRecord
        ),
    ) -> OracleLaunchReadinessArtifactReceipt:
        record = _validate_readiness_record(
            readiness_record
        )

        readiness_payload = record.to_dict()

        artifact_identity = (
            "oracle.launch_readiness."
            + record.readiness_hash
        )

        artifact_envelope_without_hash = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "artifact_identity": artifact_identity,
            "readiness_schema_version": (
                record.schema_version
            ),
            "readiness_engine_id": record.engine_id,
            "readiness_hash": record.readiness_hash,
            "readiness_record": readiness_payload,
            "read_only": True,
            "alerts_allowed": False,
            "qseries_intake_allowed": False,
            "canonical_handoff_published": False,
            "execution_allowed": False,
            "execution_adapter_resolved": False,
            "execution_adapter_invoked": False,
            "trade_authorization_allowed": False,
            "order_placement_allowed": False,
            "funds_moved": False,
            "portfolio_mutated": False,
        }

        artifact_hash = stable_hash(
            artifact_envelope_without_hash
        )

        artifact_envelope = {
            **artifact_envelope_without_hash,
            "artifact_hash": artifact_hash,
        }

        artifact_filename = (
            "readiness--"
            + record.readiness_hash
            + "--"
            + artifact_hash
            + ".json"
        )

        artifact_path = (
            self._artifact_directory
            / artifact_filename
        )

        _assert_confined(
            runtime_root=self._runtime_root,
            path=artifact_path,
        )

        immutable_written = _write_immutable_json(
            artifact_path,
            artifact_envelope,
        )

        pointer = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "artifact_identity": artifact_identity,
            "readiness_hash": record.readiness_hash,
            "artifact_hash": artifact_hash,
            "artifact_filename": artifact_filename,
            "read_only": True,
            "execution_allowed": False,
        }

        _atomic_replace_json(
            self._current_pointer_path,
            pointer,
        )

        return OracleLaunchReadinessArtifactReceipt(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            artifact_status="persisted",
            readiness_schema_version=record.schema_version,
            readiness_engine_id=record.engine_id,
            readiness_hash=record.readiness_hash,
            artifact_identity=artifact_identity,
            artifact_hash=artifact_hash,
            artifact_relative_path=(
                artifact_path.relative_to(
                    self._runtime_root
                ).as_posix()
            ),
            current_pointer_relative_path=(
                self._current_pointer_path.relative_to(
                    self._runtime_root
                ).as_posix()
            ),
            immutable_artifact_written=immutable_written,
            current_pointer_updated=True,
            read_only=True,
            alerts_allowed=False,
            qseries_intake_allowed=False,
            canonical_handoff_published=False,
            execution_allowed=False,
            execution_adapter_resolved=False,
            execution_adapter_invoked=False,
            trade_authorization_allowed=False,
            order_placement_allowed=False,
            funds_moved=False,
            portfolio_mutated=False,
        )

    def load_current(
        self,
    ) -> OracleShadowLaunchReadinessRecord:
        if not self._current_pointer_path.is_file():
            raise OracleLaunchReadinessArtifactStoreBlocked(
                "current launch readiness pointer is missing"
            )

        pointer = _read_json_mapping(
            self._current_pointer_path
        )

        expected_pointer_fields = {
            "schema_version",
            "engine_id",
            "artifact_identity",
            "readiness_hash",
            "artifact_hash",
            "artifact_filename",
            "read_only",
            "execution_allowed",
        }

        if set(pointer) != expected_pointer_fields:
            raise OracleLaunchReadinessArtifactStoreBlocked(
                "current pointer field contract mismatch"
            )

        if (
            pointer["schema_version"] != SCHEMA_VERSION
            or pointer["engine_id"] != ENGINE_ID
            or pointer["read_only"] is not True
            or pointer["execution_allowed"] is not False
        ):
            raise OracleLaunchReadinessArtifactStoreBlocked(
                "current pointer invariant validation failed"
            )

        artifact_filename = pointer[
            "artifact_filename"
        ]

        if (
            not isinstance(
                artifact_filename,
                str,
            )
            or not artifact_filename
            or Path(artifact_filename).name
            != artifact_filename
        ):
            raise OracleLaunchReadinessArtifactStoreBlocked(
                "artifact filename is invalid"
            )

        artifact_path = (
            self._artifact_directory
            / artifact_filename
        )

        _assert_confined(
            runtime_root=self._runtime_root,
            path=artifact_path,
        )

        if not artifact_path.is_file():
            raise OracleLaunchReadinessArtifactStoreBlocked(
                "immutable readiness artifact is missing"
            )

        artifact = _read_json_mapping(
            artifact_path
        )

        artifact_hash = artifact.get(
            "artifact_hash"
        )

        if not isinstance(
            artifact_hash,
            str,
        ) or not artifact_hash:
            raise OracleLaunchReadinessArtifactStoreBlocked(
                "artifact hash is missing"
            )

        artifact_without_hash = dict(
            artifact
        )

        artifact_without_hash.pop(
            "artifact_hash",
            None,
        )

        calculated_artifact_hash = stable_hash(
            artifact_without_hash
        )

        if (
            calculated_artifact_hash
            != artifact_hash
        ):
            raise OracleLaunchReadinessArtifactStoreBlocked(
                "immutable readiness artifact hash mismatch"
            )

        if (
            pointer["artifact_hash"]
            != artifact_hash
        ):
            raise OracleLaunchReadinessArtifactStoreBlocked(
                "current pointer artifact hash mismatch"
            )

        if (
            pointer["readiness_hash"]
            != artifact.get("readiness_hash")
        ):
            raise OracleLaunchReadinessArtifactStoreBlocked(
                "current pointer readiness hash mismatch"
            )

        if (
            pointer["artifact_identity"]
            != artifact.get("artifact_identity")
        ):
            raise OracleLaunchReadinessArtifactStoreBlocked(
                "current pointer artifact identity mismatch"
            )

        readiness_payload = artifact.get(
            "readiness_record"
        )

        if not isinstance(
            readiness_payload,
            dict,
        ):
            raise OracleLaunchReadinessArtifactStoreBlocked(
                "readiness_record payload is malformed"
            )

        record = _reconstruct_readiness_record(
            readiness_payload
        )

        if (
            record.readiness_hash
            != pointer["readiness_hash"]
        ):
            raise OracleLaunchReadinessArtifactStoreBlocked(
                "loaded readiness hash does not match pointer"
            )

        return record
