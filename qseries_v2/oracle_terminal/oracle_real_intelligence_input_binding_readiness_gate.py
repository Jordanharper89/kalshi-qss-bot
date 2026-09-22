from __future__ import annotations

import hashlib
import importlib
import inspect
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "OIT-033"
ENGINE_ID = "OIT-033"
POLICY_ID = "oracle.real-intelligence-input-binding-readiness.v1"

CANONICAL_RUNTIME_RELATIVE = Path("runtime") / "oracle_intelligence"
CANDIDATE_MODULES = (
    "qseries_v2.oracle_terminal.oracle_genuine_intelligence_artifact_admission",
    "qseries_v2.oracle_terminal.oracle_queryable_intelligence_read_model",
    "qseries_v2.oracle_terminal.oracle_natural_language_query_planning_and_execution",
)
FORBIDDEN_RUNTIME_SUFFIXES = (
    ".tmp",
    ".partial",
    ".lock",
    ".bak",
)


class OracleRealIntelligenceBindingInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleRealIntelligenceArtifactCandidate:
    relative_path: str
    byte_count: int
    sha256: str
    suffix: str
    hidden: bool
    forbidden_suffix: bool
    readable: bool
    candidate_eligible: bool
    candidate_hash: str


@dataclass(frozen=True)
class OracleRealIntelligenceCallableCandidate:
    module_name: str
    callable_name: str
    signature: tuple[str, ...]
    importable: bool
    callable_resolved: bool
    read_only_name_signal: bool
    persistence_name_signal: bool
    candidate_eligible: bool
    candidate_hash: str


@dataclass(frozen=True)
class OracleRealIntelligenceBindingReadinessReport:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    runtime_root: str
    runtime_root_exists: bool
    artifact_candidates: tuple[OracleRealIntelligenceArtifactCandidate, ...]
    artifact_candidate_count: int
    eligible_artifact_count: int
    callable_candidates: tuple[OracleRealIntelligenceCallableCandidate, ...]
    callable_candidate_count: int
    eligible_callable_count: int
    canonical_runtime_target_verified: bool
    genuine_artifact_available: bool
    read_only_callable_available: bool
    real_input_binding_ready: bool
    analytics_execution_performed: bool
    database_access_performed: bool
    runtime_artifact_created: bool
    publication_allowed: bool
    action_authorization_allowed: bool
    qseries_execution_allowed: bool
    read_only: bool
    failure_reason: str | None
    report_hash: str


def _canonical(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (tuple, list)):
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
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _safe_relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def discover_runtime_artifacts(
    repository_root: str | Path,
) -> tuple[OracleRealIntelligenceArtifactCandidate, ...]:
    root = Path(repository_root).resolve()
    runtime_root = (root / CANONICAL_RUNTIME_RELATIVE).resolve()
    if not runtime_root.is_dir():
        return ()

    candidates = []
    for path in sorted(runtime_root.rglob("*")):
        if not path.is_file():
            continue
        relative = _safe_relative(path, root)
        suffix = path.suffix.lower()
        hidden = any(part.startswith(".") for part in path.relative_to(runtime_root).parts)
        forbidden_suffix = any(
            path.name.lower().endswith(item)
            for item in FORBIDDEN_RUNTIME_SUFFIXES
        )
        readable = False
        byte_count = 0
        digest = ""
        try:
            byte_count = path.stat().st_size
            digest = _sha256(path)
            readable = True
        except OSError:
            readable = False

        eligible = bool(
            readable
            and byte_count > 0
            and digest
            and not hidden
            and not forbidden_suffix
        )
        body = {
            "relative_path": relative,
            "byte_count": byte_count,
            "sha256": digest,
            "suffix": suffix,
            "hidden": hidden,
            "forbidden_suffix": forbidden_suffix,
            "readable": readable,
            "candidate_eligible": eligible,
        }
        candidate = OracleRealIntelligenceArtifactCandidate(
            **body,
            candidate_hash=_stable_hash(body),
        )
        verify_artifact_candidate(candidate)
        candidates.append(candidate)

    return tuple(candidates)


def verify_artifact_candidate(
    candidate: OracleRealIntelligenceArtifactCandidate,
) -> bool:
    body = asdict(candidate)
    supplied = body.pop("candidate_hash")
    if _stable_hash(body) != supplied:
        raise OracleRealIntelligenceBindingInvariantError(
            "artifact candidate hash mismatch"
        )
    expected = bool(
        candidate.readable
        and candidate.byte_count > 0
        and candidate.sha256
        and not candidate.hidden
        and not candidate.forbidden_suffix
    )
    if candidate.candidate_eligible != expected:
        raise OracleRealIntelligenceBindingInvariantError(
            "artifact eligibility mismatch"
        )
    return True


def _public_callables(module: Any) -> tuple[tuple[str, Any], ...]:
    values = []
    for name, value in inspect.getmembers(module):
        if name.startswith("_"):
            continue
        if inspect.isfunction(value) or inspect.isclass(value):
            values.append((name, value))
    return tuple(values)


def discover_read_only_callables() -> tuple[OracleRealIntelligenceCallableCandidate, ...]:
    candidates = []
    for module_name in CANDIDATE_MODULES:
        try:
            module = importlib.import_module(module_name)
            importable = True
        except Exception:
            module = None
            importable = False

        if module is None:
            body = {
                "module_name": module_name,
                "callable_name": "",
                "signature": (),
                "importable": False,
                "callable_resolved": False,
                "read_only_name_signal": False,
                "persistence_name_signal": False,
                "candidate_eligible": False,
            }
            candidates.append(
                OracleRealIntelligenceCallableCandidate(
                    **body,
                    candidate_hash=_stable_hash(body),
                )
            )
            continue

        public = _public_callables(module)
        if not public:
            body = {
                "module_name": module_name,
                "callable_name": "",
                "signature": (),
                "importable": True,
                "callable_resolved": False,
                "read_only_name_signal": False,
                "persistence_name_signal": False,
                "candidate_eligible": False,
            }
            candidates.append(
                OracleRealIntelligenceCallableCandidate(
                    **body,
                    candidate_hash=_stable_hash(body),
                )
            )
            continue

        for callable_name, value in public:
            try:
                signature = tuple(inspect.signature(value).parameters)
            except (TypeError, ValueError):
                signature = ()
            lowered = callable_name.lower()
            read_only_signal = any(
                token in lowered
                for token in (
                    "read",
                    "query",
                    "inspect",
                    "verify",
                    "admission",
                    "load",
                    "resolve",
                )
            )
            persistence_signal = any(
                token in lowered
                for token in (
                    "persist",
                    "write",
                    "save",
                    "delete",
                    "publish",
                    "execute",
                )
            )
            eligible = bool(
                importable
                and callable(value)
                and read_only_signal
                and not persistence_signal
            )
            body = {
                "module_name": module_name,
                "callable_name": callable_name,
                "signature": signature,
                "importable": importable,
                "callable_resolved": callable(value),
                "read_only_name_signal": read_only_signal,
                "persistence_name_signal": persistence_signal,
                "candidate_eligible": eligible,
            }
            candidate = OracleRealIntelligenceCallableCandidate(
                **body,
                candidate_hash=_stable_hash(body),
            )
            verify_callable_candidate(candidate)
            candidates.append(candidate)

    return tuple(candidates)


def verify_callable_candidate(
    candidate: OracleRealIntelligenceCallableCandidate,
) -> bool:
    body = asdict(candidate)
    supplied = body.pop("candidate_hash")
    if _stable_hash(body) != supplied:
        raise OracleRealIntelligenceBindingInvariantError(
            "callable candidate hash mismatch"
        )
    expected = bool(
        candidate.importable
        and candidate.callable_resolved
        and candidate.read_only_name_signal
        and not candidate.persistence_name_signal
    )
    if candidate.candidate_eligible != expected:
        raise OracleRealIntelligenceBindingInvariantError(
            "callable eligibility mismatch"
        )
    return True


def build_real_intelligence_binding_readiness_report(
    repository_root: str | Path,
) -> OracleRealIntelligenceBindingReadinessReport:
    root = Path(repository_root).resolve()
    runtime_root = (root / CANONICAL_RUNTIME_RELATIVE).resolve()
    artifacts = discover_runtime_artifacts(root)
    callables = discover_read_only_callables()

    eligible_artifacts = sum(item.candidate_eligible for item in artifacts)
    eligible_callables = sum(item.candidate_eligible for item in callables)
    canonical_target = runtime_root == (root / "runtime" / "oracle_intelligence").resolve()
    ready = bool(
        canonical_target
        and runtime_root.is_dir()
        and eligible_artifacts > 0
        and eligible_callables > 0
    )

    failure_reason = None
    if not runtime_root.is_dir():
        failure_reason = "canonical_runtime_root_missing"
    elif eligible_artifacts == 0:
        failure_reason = "no_genuine_runtime_artifact_available"
    elif eligible_callables == 0:
        failure_reason = "no_read_only_terminal_callable_available"

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root),
        "runtime_root": str(runtime_root),
        "runtime_root_exists": runtime_root.is_dir(),
        "artifact_candidates": artifacts,
        "artifact_candidate_count": len(artifacts),
        "eligible_artifact_count": eligible_artifacts,
        "callable_candidates": callables,
        "callable_candidate_count": len(callables),
        "eligible_callable_count": eligible_callables,
        "canonical_runtime_target_verified": canonical_target,
        "genuine_artifact_available": eligible_artifacts > 0,
        "read_only_callable_available": eligible_callables > 0,
        "real_input_binding_ready": ready,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "runtime_artifact_created": False,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
        "read_only": True,
        "failure_reason": failure_reason,
    }
    report = OracleRealIntelligenceBindingReadinessReport(
        **body,
        report_hash=_stable_hash(body),
    )
    verify_real_intelligence_binding_readiness_report(report)
    return report


def verify_real_intelligence_binding_readiness_report(
    report: OracleRealIntelligenceBindingReadinessReport,
) -> bool:
    body = asdict(report)
    supplied = body.pop("report_hash")
    if _stable_hash(body) != supplied:
        raise OracleRealIntelligenceBindingInvariantError(
            "binding readiness report hash mismatch"
        )
    if report.schema_version != SCHEMA_VERSION:
        raise OracleRealIntelligenceBindingInvariantError("schema mismatch")
    if report.policy_id != POLICY_ID:
        raise OracleRealIntelligenceBindingInvariantError("policy mismatch")
    if not report.read_only:
        raise OracleRealIntelligenceBindingInvariantError(
            "binding readiness report is not read-only"
        )
    if (
        report.analytics_execution_performed
        or report.database_access_performed
        or report.runtime_artifact_created
        or report.publication_allowed
        or report.action_authorization_allowed
        or report.qseries_execution_allowed
    ):
        raise OracleRealIntelligenceBindingInvariantError(
            "forbidden capability enabled"
        )
    if report.artifact_candidate_count != len(report.artifact_candidates):
        raise OracleRealIntelligenceBindingInvariantError(
            "artifact candidate count mismatch"
        )
    if report.callable_candidate_count != len(report.callable_candidates):
        raise OracleRealIntelligenceBindingInvariantError(
            "callable candidate count mismatch"
        )
    for item in report.artifact_candidates:
        verify_artifact_candidate(item)
    for item in report.callable_candidates:
        verify_callable_candidate(item)
    if report.eligible_artifact_count != sum(
        item.candidate_eligible for item in report.artifact_candidates
    ):
        raise OracleRealIntelligenceBindingInvariantError(
            "eligible artifact count mismatch"
        )
    if report.eligible_callable_count != sum(
        item.candidate_eligible for item in report.callable_candidates
    ):
        raise OracleRealIntelligenceBindingInvariantError(
            "eligible callable count mismatch"
        )
    expected_ready = bool(
        report.canonical_runtime_target_verified
        and report.runtime_root_exists
        and report.genuine_artifact_available
        and report.read_only_callable_available
    )
    if report.real_input_binding_ready != expected_ready:
        raise OracleRealIntelligenceBindingInvariantError(
            "real input binding readiness mismatch"
        )
    return True
