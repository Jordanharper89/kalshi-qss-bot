from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_shadow_operator_health_attestation import (
    ENGINE_ID as OLA066_ENGINE_ID,
    SCHEMA_VERSION as OLA066_SCHEMA_VERSION,
    OracleLiveShadowOperatorHealthAttestationRecord,
)


SCHEMA_VERSION = "OLA-067"
ENGINE_ID = "OLA-067"
EVIDENCE_TYPE = (
    "oracle_live_shadow_operator_health_evidence"
)

READ_ONLY = True
EXECUTION_ALLOWED = False
ALERTS_ALLOWED = False
QSERIES_HANDOFF_ALLOWED = False
EXECUTION_ADAPTER_RESOLVED = False
EXECUTION_ADAPTER_INVOKED = False
TRADE_AUTHORIZATION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False

DEFAULT_RELATIVE_PATH = Path(
    "runtime"
) / "oracle_live_shadow" / "operator" / "health" / "current.json"


class OracleLiveShadowOperatorHealthEvidenceStoreError(
    RuntimeError
):
    """Base OLA-067 evidence-store error."""


class OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
    OracleLiveShadowOperatorHealthEvidenceStoreError
):
    """Raised when health evidence cannot be stored safely."""


def _canonical_json(payload: Mapping[str, Any]) -> str:
    try:
        return json.dumps(
            dict(payload),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
            "health evidence is not canonically serializable"
        ) from exc


def _require_safe_target(target_path: Path) -> Path:
    if not isinstance(target_path, Path):
        raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
            "target_path must be a pathlib.Path"
        )

    if target_path.name != "current.json":
        raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
            "health evidence target must be current.json"
        )

    if target_path.suffix.lower() != ".json":
        raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
            "health evidence target must use JSON"
        )

    forbidden_parts = {
        ".env",
        ".git",
        "venv",
        ".venv",
        "__pycache__",
    }

    lowered_parts = {
        part.lower()
        for part in target_path.parts
    }

    if lowered_parts.intersection(forbidden_parts):
        raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
            "health evidence target uses a forbidden path"
        )

    return target_path


def _validate_attestation(
    attestation: OracleLiveShadowOperatorHealthAttestationRecord,
) -> None:
    if not isinstance(
        attestation,
        OracleLiveShadowOperatorHealthAttestationRecord,
    ):
        raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
            "OLA-066 health attestation record is required"
        )

    if attestation.schema_version != OLA066_SCHEMA_VERSION:
        raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
            "OLA-066 schema identity mismatch"
        )

    if attestation.engine_id != OLA066_ENGINE_ID:
        raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
            "OLA-066 engine identity mismatch"
        )

    if attestation.read_only is not True:
        raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
            "health attestation is not read-only"
        )

    forbidden_authority = (
        attestation.execution_allowed,
        attestation.alerts_allowed,
        attestation.qseries_handoff_allowed,
        attestation.execution_adapter_resolved,
        attestation.execution_adapter_invoked,
        attestation.trade_authorization_allowed,
        attestation.order_placement_allowed,
        attestation.funds_moved,
        attestation.portfolio_mutated,
    )

    if any(value is True for value in forbidden_authority):
        raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
            "health attestation contains forbidden authority"
        )

    if len(attestation.evidence_hash) != 64:
        raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
            "health attestation evidence hash is invalid"
        )

    try:
        int(attestation.evidence_hash, 16)
    except ValueError as exc:
        raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
            "health attestation evidence hash is invalid"
        ) from exc


@dataclass(frozen=True, slots=True)
class OracleLiveShadowOperatorHealthEvidenceWriteRecord:
    schema_version: str
    engine_id: str
    evidence_type: str
    target_path: str
    attestation_schema_version: str
    attestation_engine_id: str
    attestation_evidence_hash: str
    operator_status: str
    health_status: str
    bytes_written: int
    write_status: str
    atomic_write: bool
    durable_flush_requested: bool
    read_only: bool = True
    execution_allowed: bool = False
    alerts_allowed: bool = False
    qseries_handoff_allowed: bool = False
    execution_adapter_resolved: bool = False
    execution_adapter_invoked: bool = False
    trade_authorization_allowed: bool = False
    order_placement_allowed: bool = False
    funds_moved: bool = False
    portfolio_mutated: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
                "write-record schema version mismatch"
            )

        if self.engine_id != ENGINE_ID:
            raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
                "write-record engine id mismatch"
            )

        if self.evidence_type != EVIDENCE_TYPE:
            raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
                "write-record evidence type mismatch"
            )

        if self.attestation_schema_version != OLA066_SCHEMA_VERSION:
            raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
                "write-record OLA-066 schema mismatch"
            )

        if self.attestation_engine_id != OLA066_ENGINE_ID:
            raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
                "write-record OLA-066 engine mismatch"
            )

        if self.operator_status not in {
            "RUNNING",
            "DEGRADED",
            "STOPPED",
        }:
            raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
                "unsupported operator status"
            )

        if self.health_status not in {
            "HEALTHY",
            "DEGRADED",
            "STOPPED",
        }:
            raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
                "unsupported health status"
            )

        if self.write_status != "written":
            raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
                "write status must be written"
            )

        if (
            isinstance(self.bytes_written, bool)
            or not isinstance(self.bytes_written, int)
            or self.bytes_written < 1
        ):
            raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
                "bytes_written must be a positive integer"
            )

        if self.atomic_write is not True:
            raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
                "health evidence write must be atomic"
            )

        if self.durable_flush_requested is not True:
            raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
                "durable flush must be requested"
            )

        if self.read_only is not True:
            raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
                "OLA-067 must remain read-only"
            )

        forbidden_authority = (
            self.execution_allowed,
            self.alerts_allowed,
            self.qseries_handoff_allowed,
            self.execution_adapter_resolved,
            self.execution_adapter_invoked,
            self.trade_authorization_allowed,
            self.order_placement_allowed,
            self.funds_moved,
            self.portfolio_mutated,
        )

        if any(value is True for value in forbidden_authority):
            raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
                "OLA-067 authority boundary violated"
            )

    def to_dict(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "schema_version": self.schema_version,
                "engine_id": self.engine_id,
                "evidence_type": self.evidence_type,
                "target_path": self.target_path,
                "attestation_schema_version": (
                    self.attestation_schema_version
                ),
                "attestation_engine_id": (
                    self.attestation_engine_id
                ),
                "attestation_evidence_hash": (
                    self.attestation_evidence_hash
                ),
                "operator_status": self.operator_status,
                "health_status": self.health_status,
                "bytes_written": self.bytes_written,
                "write_status": self.write_status,
                "atomic_write": self.atomic_write,
                "durable_flush_requested": (
                    self.durable_flush_requested
                ),
                "read_only": self.read_only,
                "execution_allowed": self.execution_allowed,
                "alerts_allowed": self.alerts_allowed,
                "qseries_handoff_allowed": (
                    self.qseries_handoff_allowed
                ),
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
        )


class OracleLiveShadowOperatorHealthEvidenceStore:
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    read_only = True
    execution_allowed = False

    def __init__(
        self,
        *,
        target_path: Path,
    ) -> None:
        self._target_path = _require_safe_target(
            target_path
        )

    @property
    def target_path(self) -> Path:
        return self._target_path

    def _payload(
        self,
        *,
        attestation: (
            OracleLiveShadowOperatorHealthAttestationRecord
        ),
    ) -> Mapping[str, Any]:
        _validate_attestation(attestation)

        attestation_payload = dict(
            attestation.to_dict()
        )

        payload = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "evidence_type": EVIDENCE_TYPE,
            "attestation": attestation_payload,
            "read_only": True,
            "execution_allowed": False,
            "alerts_allowed": False,
            "qseries_handoff_allowed": False,
            "execution_adapter_resolved": False,
            "execution_adapter_invoked": False,
            "trade_authorization_allowed": False,
            "order_placement_allowed": False,
            "funds_moved": False,
            "portfolio_mutated": False,
        }

        return MappingProxyType(payload)

    def write(
        self,
        *,
        attestation: (
            OracleLiveShadowOperatorHealthAttestationRecord
        ),
    ) -> OracleLiveShadowOperatorHealthEvidenceWriteRecord:
        payload = self._payload(
            attestation=attestation
        )

        serialized = (
            _canonical_json(payload)
            + "\n"
        )

        encoded = serialized.encode("utf-8")

        target = self._target_path
        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_path: Path | None = None

        try:
            descriptor, raw_temporary_path = tempfile.mkstemp(
                prefix=f".{target.name}.",
                suffix=".tmp",
                dir=str(target.parent),
            )

            temporary_path = Path(
                raw_temporary_path
            )

            with os.fdopen(
                descriptor,
                "wb",
            ) as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())

            os.replace(
                temporary_path,
                target,
            )

            temporary_path = None

        except BaseException as exc:
            if (
                temporary_path is not None
                and temporary_path.exists()
            ):
                try:
                    temporary_path.unlink()
                except OSError:
                    pass

            raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
                "health evidence atomic write failed"
            ) from exc

        try:
            persisted_text = target.read_text(
                encoding="utf-8"
            )

            persisted_payload = json.loads(
                persisted_text
            )
        except (
            OSError,
            UnicodeError,
            json.JSONDecodeError,
        ) as exc:
            raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
                "written health evidence could not be verified"
            ) from exc

        if not isinstance(persisted_payload, dict):
            raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
                "written health evidence is not a JSON object"
            )

        if persisted_payload != dict(payload):
            raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
                "written health evidence does not match source"
            )

        persisted_attestation = persisted_payload.get(
            "attestation"
        )

        if not isinstance(
            persisted_attestation,
            dict,
        ):
            raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
                "written OLA-066 attestation is missing"
            )

        if persisted_attestation.get(
            "evidence_hash"
        ) != attestation.evidence_hash:
            raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
                "written OLA-066 evidence hash mismatch"
            )

        return OracleLiveShadowOperatorHealthEvidenceWriteRecord(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            evidence_type=EVIDENCE_TYPE,
            target_path=str(target.resolve()),
            attestation_schema_version=(
                attestation.schema_version
            ),
            attestation_engine_id=(
                attestation.engine_id
            ),
            attestation_evidence_hash=(
                attestation.evidence_hash
            ),
            operator_status=(
                attestation.operator_status
            ),
            health_status=(
                attestation.health_status
            ),
            bytes_written=len(encoded),
            write_status="written",
            atomic_write=True,
            durable_flush_requested=True,
        )

    def read_current(
        self,
    ) -> Mapping[str, Any]:
        target = self._target_path

        if not target.exists():
            raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
                "current health evidence does not exist"
            )

        try:
            payload = json.loads(
                target.read_text(
                    encoding="utf-8"
                )
            )
        except (
            OSError,
            UnicodeError,
            json.JSONDecodeError,
        ) as exc:
            raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
                "current health evidence is unreadable"
            ) from exc

        if not isinstance(payload, dict):
            raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
                "current health evidence is not a JSON object"
            )

        if payload.get("schema_version") != SCHEMA_VERSION:
            raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
                "current health evidence schema mismatch"
            )

        if payload.get("engine_id") != ENGINE_ID:
            raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
                "current health evidence engine mismatch"
            )

        if payload.get("evidence_type") != EVIDENCE_TYPE:
            raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
                "current health evidence type mismatch"
            )

        if payload.get("read_only") is not True:
            raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
                "current health evidence is not read-only"
            )

        forbidden_authority = (
            payload.get("execution_allowed"),
            payload.get("alerts_allowed"),
            payload.get("qseries_handoff_allowed"),
            payload.get("execution_adapter_resolved"),
            payload.get("execution_adapter_invoked"),
            payload.get("trade_authorization_allowed"),
            payload.get("order_placement_allowed"),
            payload.get("funds_moved"),
            payload.get("portfolio_mutated"),
        )

        if any(value is not False for value in forbidden_authority):
            raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
                "current health evidence authority boundary violated"
            )

        attestation = payload.get(
            "attestation"
        )

        if not isinstance(attestation, dict):
            raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
                "current OLA-066 attestation is missing"
            )

        if attestation.get(
            "schema_version"
        ) != OLA066_SCHEMA_VERSION:
            raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
                "current OLA-066 schema mismatch"
            )

        if attestation.get(
            "engine_id"
        ) != OLA066_ENGINE_ID:
            raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
                "current OLA-066 engine mismatch"
            )

        if attestation.get("read_only") is not True:
            raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
                "current OLA-066 record is not read-only"
            )

        return MappingProxyType(payload)


def build_production_operator_health_evidence_store(
    *,
    repository_root: Path,
) -> OracleLiveShadowOperatorHealthEvidenceStore:
    if not isinstance(repository_root, Path):
        raise OracleLiveShadowOperatorHealthEvidenceStoreBlocked(
            "repository_root must be a pathlib.Path"
        )

    target_path = (
        repository_root
        / DEFAULT_RELATIVE_PATH
    )

    return OracleLiveShadowOperatorHealthEvidenceStore(
        target_path=target_path
    )


__all__ = [
    "ALERTS_ALLOWED",
    "DEFAULT_RELATIVE_PATH",
    "ENGINE_ID",
    "EVIDENCE_TYPE",
    "EXECUTION_ADAPTER_INVOKED",
    "EXECUTION_ADAPTER_RESOLVED",
    "EXECUTION_ALLOWED",
    "FUNDS_MOVED",
    "ORDER_PLACEMENT_ALLOWED",
    "PORTFOLIO_MUTATED",
    "QSERIES_HANDOFF_ALLOWED",
    "READ_ONLY",
    "SCHEMA_VERSION",
    "TRADE_AUTHORIZATION_ALLOWED",
    "OracleLiveShadowOperatorHealthEvidenceStore",
    "OracleLiveShadowOperatorHealthEvidenceStoreBlocked",
    "OracleLiveShadowOperatorHealthEvidenceStoreError",
    "OracleLiveShadowOperatorHealthEvidenceWriteRecord",
    "build_production_operator_health_evidence_store",
]
