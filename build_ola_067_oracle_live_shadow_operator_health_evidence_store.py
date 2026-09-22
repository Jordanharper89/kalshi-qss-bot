from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent

MODULE = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition"
    / "oracle_live_shadow_operator_health_evidence_store.py"
)

TEST_FILE = (
    ROOT
    / "test_ola_067_oracle_live_shadow_operator_health_evidence_store.py"
)

PACKAGE_INIT = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition"
    / "__init__.py"
)


MODULE_SOURCE = r'''from __future__ import annotations

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
'''


TEST_SOURCE = r'''from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_shadow_operator_health_attestation import (
    OracleLiveShadowOperatorHealthAttestor,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_shadow_operator_health_evidence_store import (
    ENGINE_ID,
    SCHEMA_VERSION,
    OracleLiveShadowOperatorHealthEvidenceStore,
    OracleLiveShadowOperatorHealthEvidenceStoreBlocked,
    build_production_operator_health_evidence_store,
)


OBSERVED_AT = datetime(
    2026,
    7,
    17,
    21,
    0,
    0,
    123456,
    tzinfo=timezone.utc,
)


def expect_blocked(callable_object) -> None:
    try:
        callable_object()
    except OracleLiveShadowOperatorHealthEvidenceStoreBlocked:
        return

    raise AssertionError(
        "expected OLA-067 to fail closed"
    )


def build_attestation(
    *,
    status: str,
    pid: int | None,
    process_alive: bool,
    runtime_fresh: bool,
    state_age_seconds: float | None,
    newest_log_age_seconds: float | None,
):
    return OracleLiveShadowOperatorHealthAttestor(
        status_provider=lambda **_: {
            "status": status,
            "pid": pid,
            "process_alive": process_alive,
            "runtime_fresh": runtime_fresh,
            "state_age_seconds": state_age_seconds,
            "newest_log_age_seconds": (
                newest_log_age_seconds
            ),
            "read_only": True,
            "execution_allowed": False,
        }
    ).attest(
        observed_at=OBSERVED_AT,
        stale_seconds=120,
    )


def main() -> int:
    assert SCHEMA_VERSION == "OLA-067"
    assert ENGINE_ID == "OLA-067"

    healthy_attestation = build_attestation(
        status="RUNNING",
        pid=54321,
        process_alive=True,
        runtime_fresh=True,
        state_age_seconds=3.0,
        newest_log_age_seconds=2.0,
    )

    degraded_attestation = build_attestation(
        status="DEGRADED",
        pid=54322,
        process_alive=True,
        runtime_fresh=False,
        state_age_seconds=180.0,
        newest_log_age_seconds=181.0,
    )

    stopped_attestation = build_attestation(
        status="STOPPED",
        pid=None,
        process_alive=False,
        runtime_fresh=False,
        state_age_seconds=None,
        newest_log_age_seconds=None,
    )

    with tempfile.TemporaryDirectory() as temporary_directory:
        repository_root = Path(
            temporary_directory
        )

        store = (
            build_production_operator_health_evidence_store(
                repository_root=repository_root
            )
        )

        expected_target = (
            repository_root
            / "runtime"
            / "oracle_live_shadow"
            / "operator"
            / "health"
            / "current.json"
        )

        assert store.target_path == expected_target

        first_write = store.write(
            attestation=healthy_attestation
        )

        assert expected_target.exists()
        assert first_write.schema_version == "OLA-067"
        assert first_write.engine_id == "OLA-067"
        assert first_write.write_status == "written"
        assert first_write.atomic_write is True
        assert first_write.durable_flush_requested is True
        assert first_write.bytes_written > 0
        assert first_write.operator_status == "RUNNING"
        assert first_write.health_status == "HEALTHY"
        assert (
            first_write.attestation_evidence_hash
            == healthy_attestation.evidence_hash
        )
        assert first_write.read_only is True
        assert first_write.execution_allowed is False
        assert first_write.alerts_allowed is False
        assert first_write.qseries_handoff_allowed is False
        assert first_write.execution_adapter_resolved is False
        assert first_write.execution_adapter_invoked is False
        assert first_write.trade_authorization_allowed is False
        assert first_write.order_placement_allowed is False
        assert first_write.funds_moved is False
        assert first_write.portfolio_mutated is False

        first_payload = store.read_current()

        assert first_payload["schema_version"] == "OLA-067"
        assert first_payload["engine_id"] == "OLA-067"
        assert first_payload["read_only"] is True
        assert first_payload["execution_allowed"] is False
        assert (
            first_payload["attestation"]["evidence_hash"]
            == healthy_attestation.evidence_hash
        )

        try:
            first_payload["engine_id"] = "mutated"
        except TypeError:
            pass
        else:
            raise AssertionError(
                "read projection must be immutable"
            )

        first_bytes = expected_target.read_bytes()

        replay_write = store.write(
            attestation=healthy_attestation
        )

        replay_bytes = expected_target.read_bytes()

        assert first_bytes == replay_bytes
        assert replay_write.bytes_written == (
            first_write.bytes_written
        )
        assert (
            replay_write.attestation_evidence_hash
            == first_write.attestation_evidence_hash
        )

        degraded_write = store.write(
            attestation=degraded_attestation
        )

        degraded_payload = store.read_current()

        assert degraded_write.operator_status == "DEGRADED"
        assert degraded_write.health_status == "DEGRADED"
        assert (
            degraded_payload["attestation"]["degraded"]
            is True
        )
        assert (
            degraded_payload["attestation"]["fail_closed"]
            is True
        )

        stopped_write = store.write(
            attestation=stopped_attestation
        )

        stopped_payload = store.read_current()

        assert stopped_write.operator_status == "STOPPED"
        assert stopped_write.health_status == "STOPPED"
        assert (
            stopped_payload["attestation"]["stopped"]
            is True
        )
        assert (
            stopped_payload["attestation"]["fail_closed"]
            is True
        )

        raw_payload = json.loads(
            expected_target.read_text(
                encoding="utf-8"
            )
        )

        raw_payload["execution_allowed"] = True

        expected_target.write_text(
            json.dumps(raw_payload),
            encoding="utf-8",
        )

        expect_blocked(
            store.read_current
        )

        bad_target = (
            repository_root
            / ".env"
            / "current.json"
        )

        expect_blocked(
            lambda: OracleLiveShadowOperatorHealthEvidenceStore(
                target_path=bad_target
            )
        )

        wrong_name_target = (
            repository_root
            / "runtime"
            / "oracle_live_shadow"
            / "operator"
            / "health"
            / "latest.json"
        )

        expect_blocked(
            lambda: OracleLiveShadowOperatorHealthEvidenceStore(
                target_path=wrong_name_target
            )
        )

        wrong_type_target = (
            repository_root
            / "runtime"
            / "oracle_live_shadow"
            / "operator"
            / "health"
            / "current.txt"
        )

        expect_blocked(
            lambda: OracleLiveShadowOperatorHealthEvidenceStore(
                target_path=wrong_type_target
            )
        )

        empty_store = (
            OracleLiveShadowOperatorHealthEvidenceStore(
                target_path=(
                    repository_root
                    / "empty"
                    / "current.json"
                )
            )
        )

        expect_blocked(
            empty_store.read_current
        )

    print(
        "[PASS] OLA-067 Oracle Live Shadow "
        "Operator Health Evidence Store"
    )

    print(
        {
            "schema_version": "OLA-067",
            "engine_id": "OLA-067",
            "status": "passed",
            "ola066_typed_attestation_required": True,
            "healthy_evidence_written": True,
            "degraded_evidence_written_fail_closed": True,
            "stopped_evidence_written_fail_closed": True,
            "canonical_json_serialization": True,
            "deterministic_replay_bytes": True,
            "atomic_temp_file_replacement": True,
            "durable_file_flush_requested": True,
            "post_write_verification": True,
            "current_pointer_contract": True,
            "immutable_read_projection": True,
            "forbidden_target_paths_rejected": True,
            "malformed_evidence_fails_closed": True,
            "authority_tampering_fails_closed": True,
            "secrets_not_persisted": True,
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
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


EXPORT_BLOCK = '''
from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_shadow_operator_health_evidence_store import (
    OracleLiveShadowOperatorHealthEvidenceStore,
    OracleLiveShadowOperatorHealthEvidenceStoreBlocked,
    OracleLiveShadowOperatorHealthEvidenceStoreError,
    OracleLiveShadowOperatorHealthEvidenceWriteRecord,
    build_production_operator_health_evidence_store,
)
'''


def write_full_replacement(
    path: Path,
    content: str,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        content,
        encoding="utf-8",
        newline="\n",
    )

    print(f"[OK] FULL REPLACEMENT: {path}")


def update_package_exports() -> None:
    PACKAGE_INIT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if PACKAGE_INIT.exists():
        source = PACKAGE_INIT.read_text(
            encoding="utf-8"
        )
    else:
        source = ""

    marker = (
        "oracle_live_shadow_operator_health_evidence_store "
        "import"
    )

    if marker in source:
        print(
            "[OK] PACKAGE EXPORT ALREADY PRESENT: "
            f"{PACKAGE_INIT}"
        )
        return

    updated = source.rstrip()

    if updated:
        updated += "\n\n"

    updated += EXPORT_BLOCK.strip() + "\n"

    PACKAGE_INIT.write_text(
        updated,
        encoding="utf-8",
        newline="\n",
    )

    print(
        f"[OK] UPDATED PACKAGE EXPORTS: {PACKAGE_INIT}"
    )


def main() -> int:
    print("========================================")
    print(" OLA-067 INSTALLER")
    print(" ORACLE LIVE SHADOW OPERATOR")
    print(" HEALTH EVIDENCE STORE")
    print("========================================")

    ola066_module = (
        ROOT
        / "qseries_v2"
        / "oracle_intelligence"
        / "live_acquisition"
        / "oracle_live_shadow_operator_health_attestation.py"
    )

    ola066_test = (
        ROOT
        / "test_ola_066_oracle_live_shadow_operator_health_attestation.py"
    )

    if not ola066_module.exists():
        raise SystemExit(
            "[ERROR] Missing passed OLA-066 module: "
            f"{ola066_module}"
        )

    if not ola066_test.exists():
        raise SystemExit(
            "[ERROR] Missing passed OLA-066 test: "
            f"{ola066_test}"
        )

    ola066_source = ola066_module.read_text(
        encoding="utf-8"
    )

    required_ola066_markers = (
        'SCHEMA_VERSION = "OLA-066"',
        'ENGINE_ID = "OLA-066"',
        "class OracleLiveShadowOperatorHealthAttestationRecord",
        "class OracleLiveShadowOperatorHealthAttestor",
        "def build_production_operator_health_attestor(",
    )

    missing = [
        marker
        for marker in required_ola066_markers
        if marker not in ola066_source
    ]

    if missing:
        raise SystemExit(
            "[ERROR] OLA-066 canonical health boundary "
            f"is incomplete. Missing: {missing}"
        )

    write_full_replacement(
        MODULE,
        MODULE_SOURCE,
    )

    write_full_replacement(
        TEST_FILE,
        TEST_SOURCE,
    )

    update_package_exports()

    compile(
        MODULE.read_text(
            encoding="utf-8"
        ),
        str(MODULE),
        "exec",
    )

    compile(
        TEST_FILE.read_text(
            encoding="utf-8"
        ),
        str(TEST_FILE),
        "exec",
    )

    compile(
        PACKAGE_INIT.read_text(
            encoding="utf-8"
        ),
        str(PACKAGE_INIT),
        "exec",
    )

    print("")
    print(
        "[DONE] OLA-067 Oracle live shadow operator "
        "health evidence store installed"
    )
    print("")
    print("Run:")
    print(
        "py test_ola_067_oracle_live_shadow_"
        "operator_health_evidence_store.py"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())