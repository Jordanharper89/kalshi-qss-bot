from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "OIT-005"
ENGINE_ID = "OIT-005"
POLICY_ID = "oracle.genuine-intelligence-artifact-admission.v2"

INTELLIGENCE_ROOT = "runtime/oracle_intelligence"
ACTIVATION_RECEIPT = (
    "runtime/oracle_terminal/oit_004_bounded_activation_receipt.json"
)
INPUT_SUFFIXES = {".json", ".jsonl"}

REQUIRED_RECEIPT_FIELDS = (
    "schema_version",
    "engine_id",
    "policy_id",
    "status",
    "analytics_entry_point",
    "selected_input",
    "persistence_target",
    "activation_attempted",
    "analytics_execution_performed",
    "invocation_completed",
    "persist_requested",
    "new_intelligence_artifacts",
    "changed_intelligence_artifacts",
    "protected_source_unchanged",
    "outside_target_runtime_unchanged",
    "database_write_requested",
    "publication_allowed",
    "qseries_execution_allowed",
    "bounded_once",
    "receipt_hash",
)


class OracleIntelligenceArtifactAdmissionInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class ActivationArtifactLineage:
    relative_path: str
    expected_sha256: str
    expected_byte_count: int
    expected_modified_ns: int


@dataclass(frozen=True)
class AdmittedIntelligenceArtifact:
    relative_path: str
    sha256: str
    byte_count: int
    modified_ns: int
    payload_kind: str
    record_count: int
    activation_lineage_verified: bool
    content_hash_verified: bool
    byte_count_verified: bool
    readable: bool


@dataclass(frozen=True)
class OracleIntelligenceArtifactAdmissionReceipt:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    intelligence_root: str
    activation_receipt_path: str
    activation_receipt_present: bool
    activation_receipt_valid: bool
    activation_completed: bool
    activation_entry_point: str
    admitted_artifacts: tuple[AdmittedIntelligenceArtifact, ...]
    rejected_artifacts: tuple[str, ...]
    artifact_count: int
    admission_ready: bool
    terminal_consumption_ready: bool
    read_only: bool
    database_access_performed: bool
    analytics_execution_performed: bool
    publication_allowed: bool
    qseries_execution_allowed: bool
    failure_reason: str | None
    receipt_hash: str


def _canonical(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _canonical(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    if isinstance(value, Path):
        return value.as_posix()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return repr(value)


def _stable_hash(value: Any) -> str:
    payload = json.dumps(
        _canonical(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> tuple[Any, str, int]:
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        return (
            payload,
            type(payload).__name__,
            len(payload) if isinstance(payload, list) else 1,
        )
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped:
            records.append(json.loads(stripped))
    return records, "jsonl", len(records)


def _verify_activation_receipt_hash(payload: Mapping[str, Any]) -> bool:
    if not all(field in payload for field in REQUIRED_RECEIPT_FIELDS):
        return False
    supplied = payload.get("receipt_hash")
    body = dict(payload)
    body.pop("receipt_hash", None)
    return isinstance(supplied, str) and _stable_hash(body) == supplied


def _lineage_records(
    payload: Mapping[str, Any],
) -> tuple[ActivationArtifactLineage, ...]:
    records: list[ActivationArtifactLineage] = []
    seen: set[str] = set()
    for field in (
        "new_intelligence_artifacts",
        "changed_intelligence_artifacts",
    ):
        values = payload.get(field, ())
        if not isinstance(values, list):
            continue
        for item in values:
            if not isinstance(item, Mapping):
                continue
            relative = item.get("relative_path")
            expected_sha256 = item.get("sha256")
            expected_byte_count = item.get("byte_count")
            expected_modified_ns = item.get("modified_ns")
            if not (
                isinstance(relative, str)
                and isinstance(expected_sha256, str)
                and len(expected_sha256) == 64
                and isinstance(expected_byte_count, int)
                and expected_byte_count >= 0
                and isinstance(expected_modified_ns, int)
                and expected_modified_ns >= 0
            ):
                continue
            normalized = relative.replace("\\", "/")
            if normalized in seen:
                continue
            seen.add(normalized)
            records.append(
                ActivationArtifactLineage(
                    relative_path=normalized,
                    expected_sha256=expected_sha256,
                    expected_byte_count=expected_byte_count,
                    expected_modified_ns=expected_modified_ns,
                )
            )
    return tuple(records)


def _safe_artifact_path(root: Path, relative: str) -> Path:
    target = (root / relative).resolve()
    intelligence = (root / INTELLIGENCE_ROOT).resolve()
    if target == intelligence or intelligence not in target.parents:
        raise OracleIntelligenceArtifactAdmissionInvariantError(
            f"artifact escaped canonical intelligence root: {relative}"
        )
    return target


def discover_and_admit_intelligence_artifacts(
    *, repository_root: Path,
) -> OracleIntelligenceArtifactAdmissionReceipt:
    root = repository_root.resolve()
    receipt_path = root / ACTIVATION_RECEIPT

    activation_present = receipt_path.is_file()
    activation_valid = False
    activation_completed = False
    activation_entry = "not available"
    failure: str | None = None
    lineage: tuple[ActivationArtifactLineage, ...] = ()

    if activation_present:
        try:
            payload = json.loads(receipt_path.read_text(encoding="utf-8"))
            if not isinstance(payload, Mapping):
                raise ValueError("activation receipt is not a JSON object")
            activation_valid = _verify_activation_receipt_hash(payload)
            activation_completed = bool(
                activation_valid
                and payload.get("invocation_completed") is True
                and payload.get("analytics_execution_performed") is True
                and payload.get("persist_requested") is True
                and payload.get("protected_source_unchanged") is True
                and payload.get("outside_target_runtime_unchanged") is True
                and payload.get("database_write_requested") is False
                and payload.get("publication_allowed") is False
                and payload.get("qseries_execution_allowed") is False
                and payload.get("bounded_once") is True
                and payload.get("persistence_target") == INTELLIGENCE_ROOT
            )
            activation_entry = str(
                payload.get("analytics_entry_point", "not available")
            )
            lineage = _lineage_records(payload)
            if not activation_valid:
                failure = "OIT-004 activation receipt hash or contract is invalid"
            elif not activation_completed:
                failure = "OIT-004 bounded activation is not completed"
            elif not lineage:
                failure = (
                    "OIT-004 receipt contains no complete persisted artifact "
                    "hash lineage"
                )
        except (
            OSError,
            UnicodeError,
            json.JSONDecodeError,
            ValueError,
        ) as exc:
            failure = (
                f"activation receipt unreadable: "
                f"{type(exc).__name__}: {exc}"
            )
    else:
        failure = "OIT-004 activation receipt not found"

    admitted: list[AdmittedIntelligenceArtifact] = []
    rejected: list[str] = []

    if activation_completed and lineage:
        for expected in sorted(
            lineage, key=lambda item: item.relative_path
        ):
            normalized = expected.relative_path
            try:
                if not normalized.startswith(INTELLIGENCE_ROOT + "/"):
                    raise OracleIntelligenceArtifactAdmissionInvariantError(
                        "lineage path is outside canonical intelligence root"
                    )
                path = _safe_artifact_path(root, normalized)
                if not path.is_file():
                    raise FileNotFoundError(normalized)
                if path.suffix.lower() not in INPUT_SUFFIXES:
                    raise ValueError(
                        "unsupported intelligence artifact format"
                    )

                stat = path.stat()
                current_sha256 = _sha256(path)
                hash_verified = (
                    current_sha256 == expected.expected_sha256
                )
                byte_count_verified = (
                    stat.st_size == expected.expected_byte_count
                )
                if not hash_verified:
                    raise ValueError(
                        "artifact SHA-256 differs from OIT-004 lineage"
                    )
                if not byte_count_verified:
                    raise ValueError(
                        "artifact byte count differs from OIT-004 lineage"
                    )

                artifact_payload, kind, count = _load_json(path)
                if artifact_payload in (None, {}, []):
                    raise ValueError("empty intelligence artifact")

                admitted.append(
                    AdmittedIntelligenceArtifact(
                        relative_path=normalized,
                        sha256=current_sha256,
                        byte_count=stat.st_size,
                        modified_ns=stat.st_mtime_ns,
                        payload_kind=kind,
                        record_count=count,
                        activation_lineage_verified=True,
                        content_hash_verified=True,
                        byte_count_verified=True,
                        readable=True,
                    )
                )
            except (
                OSError,
                UnicodeError,
                json.JSONDecodeError,
                ValueError,
                OracleIntelligenceArtifactAdmissionInvariantError,
            ) as exc:
                rejected.append(
                    f"{normalized}: {type(exc).__name__}: {exc}"
                )

    ready = bool(
        activation_present
        and activation_valid
        and activation_completed
        and admitted
        and not rejected
        and len(admitted) == len(lineage)
    )
    if not ready and failure is None:
        failure = (
            "one or more activation-lineage artifacts failed immutable "
            "content verification"
        )

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": (
            "genuine_intelligence_artifacts_admitted"
            if ready
            else "genuine_intelligence_artifact_admission_blocked"
        ),
        "repository_root": root.as_posix(),
        "intelligence_root": INTELLIGENCE_ROOT,
        "activation_receipt_path": ACTIVATION_RECEIPT,
        "activation_receipt_present": activation_present,
        "activation_receipt_valid": activation_valid,
        "activation_completed": activation_completed,
        "activation_entry_point": activation_entry,
        "admitted_artifacts": tuple(admitted),
        "rejected_artifacts": tuple(rejected),
        "artifact_count": len(admitted),
        "admission_ready": ready,
        "terminal_consumption_ready": ready,
        "read_only": True,
        "database_access_performed": False,
        "analytics_execution_performed": False,
        "publication_allowed": False,
        "qseries_execution_allowed": False,
        "failure_reason": failure,
    }
    result = OracleIntelligenceArtifactAdmissionReceipt(
        **body,
        receipt_hash=_stable_hash(body),
    )
    verify_intelligence_artifact_admission(result)
    return result


def verify_intelligence_artifact_admission(
    receipt: OracleIntelligenceArtifactAdmissionReceipt,
) -> bool:
    body = asdict(receipt)
    supplied = body.pop("receipt_hash")
    if _stable_hash(body) != supplied:
        raise OracleIntelligenceArtifactAdmissionInvariantError(
            "OIT-005 admission receipt hash mismatch"
        )
    if not receipt.read_only:
        raise OracleIntelligenceArtifactAdmissionInvariantError(
            "OIT-005 is not read-only"
        )
    if receipt.database_access_performed:
        raise OracleIntelligenceArtifactAdmissionInvariantError(
            "database access was performed"
        )
    if receipt.analytics_execution_performed:
        raise OracleIntelligenceArtifactAdmissionInvariantError(
            "analytics execution was performed"
        )
    if receipt.publication_allowed or receipt.qseries_execution_allowed:
        raise OracleIntelligenceArtifactAdmissionInvariantError(
            "unsafe terminal boundary"
        )
    if receipt.admission_ready:
        if not receipt.activation_receipt_valid:
            raise OracleIntelligenceArtifactAdmissionInvariantError(
                "admission without valid activation receipt"
            )
        if not receipt.activation_completed:
            raise OracleIntelligenceArtifactAdmissionInvariantError(
                "admission without completed activation"
            )
        if not receipt.admitted_artifacts:
            raise OracleIntelligenceArtifactAdmissionInvariantError(
                "admission without artifacts"
            )
        if receipt.rejected_artifacts:
            raise OracleIntelligenceArtifactAdmissionInvariantError(
                "admission contains rejected lineage artifacts"
            )
        for artifact in receipt.admitted_artifacts:
            if not (
                artifact.activation_lineage_verified
                and artifact.content_hash_verified
                and artifact.byte_count_verified
                and artifact.readable
            ):
                raise OracleIntelligenceArtifactAdmissionInvariantError(
                    "artifact lacks immutable activation-lineage verification"
                )
    return True


def load_admitted_artifact(
    *,
    repository_root: Path,
    relative_path: str,
) -> Any:
    receipt = discover_and_admit_intelligence_artifacts(
        repository_root=repository_root
    )
    if not receipt.admission_ready:
        raise OracleIntelligenceArtifactAdmissionInvariantError(
            receipt.failure_reason or "intelligence admission is blocked"
        )
    normalized = relative_path.replace("\\", "/")
    admitted = {
        item.relative_path: item for item in receipt.admitted_artifacts
    }
    artifact = admitted.get(normalized)
    if artifact is None:
        raise OracleIntelligenceArtifactAdmissionInvariantError(
            "requested artifact is not admitted"
        )
    root = repository_root.resolve()
    path = _safe_artifact_path(root, artifact.relative_path)
    stat = path.stat()
    if _sha256(path) != artifact.sha256:
        raise OracleIntelligenceArtifactAdmissionInvariantError(
            "admitted artifact changed after verification"
        )
    if stat.st_size != artifact.byte_count:
        raise OracleIntelligenceArtifactAdmissionInvariantError(
            "admitted artifact size changed after verification"
        )
    payload, _, _ = _load_json(path)
    return payload


def intelligence_admission_lines(
    receipt: OracleIntelligenceArtifactAdmissionReceipt,
) -> tuple[str, ...]:
    verify_intelligence_artifact_admission(receipt)
    artifacts = (
        ", ".join(item.relative_path for item in receipt.admitted_artifacts)
        or "none"
    )
    rejected = "; ".join(receipt.rejected_artifacts) or "none"
    immutable = all(
        item.content_hash_verified and item.byte_count_verified
        for item in receipt.admitted_artifacts
    )
    return (
        "ORACLE GENUINE INTELLIGENCE ARTIFACT ADMISSION",
        f"activation_receipt: {receipt.activation_receipt_path}",
        f"activation_receipt_present: {str(receipt.activation_receipt_present).lower()}",
        f"activation_receipt_valid: {str(receipt.activation_receipt_valid).lower()}",
        f"activation_completed: {str(receipt.activation_completed).lower()}",
        f"analytics_entry_point: {receipt.activation_entry_point}",
        f"intelligence_root: {receipt.intelligence_root}",
        f"admitted_artifacts: {artifacts}",
        f"rejected_artifacts: {rejected}",
        f"artifact_count: {receipt.artifact_count}",
        f"immutable_lineage_verified: {str(immutable).lower()}",
        f"admission_ready: {str(receipt.admission_ready).lower()}",
        f"terminal_consumption_ready: {str(receipt.terminal_consumption_ready).lower()}",
        f"failure_reason: {receipt.failure_reason or 'none'}",
        "analytics_execution_performed: false",
        "database_access_performed: false",
        "publication_allowed: false",
        "qseries_execution_allowed: false",
        "read_only: true",
    )
