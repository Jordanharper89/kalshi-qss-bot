from __future__ import annotations

import hashlib
import importlib
import inspect
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .oracle_live_intelligence_activation_discovery import (
    OracleLiveIntelligenceActivationDiscoveryInvariantError,
    discover_live_intelligence_activation,
    verify_activation_discovery,
)

SCHEMA_VERSION = "OIT-004"
ENGINE_ID = "OIT-004"
POLICY_ID = "oracle.bounded-live-intelligence-activation.v1"
RUNTIME_ROOT = "runtime"
INTELLIGENCE_ROOT = "runtime/oracle_intelligence"
CONTROL_ROOT = "runtime/oracle_terminal"
CONTROL_RECEIPT = "runtime/oracle_terminal/oit_004_bounded_activation_receipt.json"

PROTECTED_PREFIXES = (
    "qseries_v2/oracle_intelligence/live_acquisition",
    "qseries_v2/oracle_intelligence/analytics",
    "qseries_v2/oracle_intelligence_integration",
    "qseries_v2/oracle_research_runtime",
    "qseries_v2/oracle_operator_runtime",
    "qseries_v2/qseries",
)

SOURCE_SUFFIXES = {".py", ".pyi"}
INPUT_SUFFIXES = {".json", ".jsonl"}
POSITIVE_INPUT_TOKENS = (
    "certified", "artifact", "evidence", "research", "analytics",
    "intelligence", "consumption", "authorization", "attestation",
    "observation", "corpus", "candidate", "work_item", "session",
)
NEGATIVE_INPUT_TOKENS = (
    "oit_003", "oit_004", "oracle_terminal", "test", "fixture",
    "sample", "example", "synthetic", "fake", "mock",
)


class OracleBoundedActivationInvariantError(
    OracleLiveIntelligenceActivationDiscoveryInvariantError
):
    pass


@dataclass(frozen=True)
class GenuineInputCandidate:
    relative_path: str
    sha256: str
    byte_count: int
    modified_ns: int
    payload_kind: str
    record_count: int
    score: int
    score_reasons: tuple[str, ...]


@dataclass(frozen=True)
class RuntimeArtifactState:
    relative_path: str
    sha256: str
    byte_count: int
    modified_ns: int


@dataclass(frozen=True)
class OracleBoundedActivationReceipt:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    analytics_entry_point: str
    required_inputs: tuple[str, ...]
    selected_input: GenuineInputCandidate | None
    candidate_count: int
    persistence_target: str
    activation_readiness: str
    activation_attempted: bool
    analytics_execution_performed: bool
    invocation_completed: bool
    persist_requested: bool
    new_intelligence_artifacts: tuple[RuntimeArtifactState, ...]
    changed_intelligence_artifacts: tuple[RuntimeArtifactState, ...]
    protected_source_unchanged: bool
    outside_target_runtime_unchanged: bool
    database_write_requested: bool
    publication_allowed: bool
    qseries_execution_allowed: bool
    bounded_once: bool
    failure_reason: str | None
    executed_at_utc: str | None
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
        _canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _source_snapshot(root: Path) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    for prefix in PROTECTED_PREFIXES:
        base = root / prefix
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_file() and path.suffix.lower() in SOURCE_SUFFIXES:
                snapshot[_relative(path, root)] = _sha256(path)
    return snapshot


def _runtime_snapshot(root: Path) -> dict[str, RuntimeArtifactState]:
    base = root / RUNTIME_ROOT
    snapshot: dict[str, RuntimeArtifactState] = {}
    if not base.exists():
        return snapshot
    for path in sorted(base.rglob("*")):
        if not path.is_file():
            continue
        relative = _relative(path, root)
        if relative == CONTROL_RECEIPT:
            continue
        stat = path.stat()
        snapshot[relative] = RuntimeArtifactState(
            relative_path=relative,
            sha256=_sha256(path),
            byte_count=stat.st_size,
            modified_ns=stat.st_mtime_ns,
        )
    return snapshot


def _intelligence_snapshot(
    runtime_snapshot: Mapping[str, RuntimeArtifactState],
) -> dict[str, RuntimeArtifactState]:
    prefix = INTELLIGENCE_ROOT + "/"
    return {
        key: value for key, value in runtime_snapshot.items()
        if key == INTELLIGENCE_ROOT or key.startswith(prefix)
    }


def _load_json_candidate(path: Path) -> tuple[Any, str, int]:
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        count = len(payload) if isinstance(payload, list) else 1
        return payload, type(payload).__name__, count
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped:
            records.append(json.loads(stripped))
    return records, "jsonl", len(records)


def _candidate_score(relative: str, payload: Any) -> tuple[int, tuple[str, ...]]:
    lowered = relative.lower()
    score = 0
    reasons: list[str] = []
    for token in POSITIVE_INPUT_TOKENS:
        if token in lowered:
            score += 4
    if any(token in lowered for token in POSITIVE_INPUT_TOKENS):
        reasons.append("runtime path contains certified-intelligence token")
    if any(token in lowered for token in NEGATIVE_INPUT_TOKENS):
        score -= 100
        reasons.append("terminal/test/synthetic path rejected")
    if isinstance(payload, Mapping):
        keys = {str(key).lower() for key in payload}
        if "certified_artifacts" in keys:
            score += 60
            reasons.append("explicit certified_artifacts envelope")
        if any("certif" in key for key in keys):
            score += 20
            reasons.append("certification key present")
        if any(key in keys for key in ("receipt_hash", "attestation_hash", "artifact_hash")):
            score += 15
            reasons.append("integrity hash field present")
        if any(key in keys for key in ("status", "schema_version", "engine_id", "policy_id")):
            score += 8
            reasons.append("production contract metadata present")
    elif isinstance(payload, list) and payload:
        score += 5
        reasons.append("non-empty runtime record collection")
        if all(isinstance(item, Mapping) for item in payload[:20]):
            score += 8
            reasons.append("structured runtime records")
    return score, tuple(reasons)


def discover_genuine_input_candidates(
    *, repository_root: Path,
) -> tuple[GenuineInputCandidate, ...]:
    root = repository_root.resolve()
    runtime = root / RUNTIME_ROOT
    candidates: list[GenuineInputCandidate] = []
    if not runtime.is_dir():
        return ()
    intelligence = (root / INTELLIGENCE_ROOT).resolve()
    for path in sorted(runtime.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in INPUT_SUFFIXES:
            continue
        try:
            resolved = path.resolve()
            if resolved == intelligence or intelligence in resolved.parents:
                continue
            relative = _relative(path, root)
            payload, kind, count = _load_json_candidate(path)
            score, reasons = _candidate_score(relative, payload)
            if score <= 0:
                continue
            stat = path.stat()
            candidates.append(GenuineInputCandidate(
                relative_path=relative,
                sha256=_sha256(path),
                byte_count=stat.st_size,
                modified_ns=stat.st_mtime_ns,
                payload_kind=kind,
                record_count=count,
                score=score,
                score_reasons=reasons,
            ))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
    return tuple(sorted(
        candidates,
        key=lambda item: (-item.score, -item.modified_ns, item.relative_path),
    ))


def _unwrap_certified_artifacts(payload: Any) -> Any:
    if isinstance(payload, Mapping):
        for key in (
            "certified_artifacts", "artifacts", "certified_evidence",
            "certified_research", "payload",
        ):
            if key in payload:
                return payload[key]
    return payload


def _resolve_callable(module_name: str, callable_name: str) -> Any:
    module = importlib.import_module(module_name)
    parts = callable_name.split(".")
    target: Any = module
    for part in parts:
        target = getattr(target, part)
    if inspect.isfunction(target) and len(parts) > 1:
        owner = getattr(module, parts[0])
        descriptor = inspect.getattr_static(owner, parts[-1])
        if isinstance(descriptor, staticmethod):
            return getattr(owner, parts[-1])
        if isinstance(descriptor, classmethod):
            return getattr(owner, parts[-1])
        instance = owner()
        return getattr(instance, parts[-1])
    return target


def _build_execution_context(
    *, candidate: GenuineInputCandidate, executed_at: datetime,
) -> dict[str, Any]:
    return {
        "activation_id": f"OIT-004:{candidate.sha256[:16]}",
        "activation_mode": "bounded_read_only_once",
        "source_artifact_path": candidate.relative_path,
        "source_artifact_sha256": candidate.sha256,
        "executed_at_utc": executed_at.isoformat(),
        "persistence_root": INTELLIGENCE_ROOT,
        "publication_allowed": False,
        "qseries_execution_allowed": False,
        "database_write_requested": False,
    }


def _invoke(
    callable_object: Any,
    *,
    certified_artifacts: Any,
    execution_context: Mapping[str, Any],
    executed_at: datetime,
) -> Any:
    signature = inspect.signature(callable_object)
    available = {
        "certified_artifacts": certified_artifacts,
        "execution_context": execution_context,
        "executed_at": executed_at,
        "persist": True,
    }
    kwargs: dict[str, Any] = {}
    unresolved: list[str] = []
    for name, parameter in signature.parameters.items():
        if name in available:
            kwargs[name] = available[name]
        elif parameter.default is inspect.Signature.empty and parameter.kind not in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            unresolved.append(name)
    if unresolved:
        raise OracleBoundedActivationInvariantError(
            "canonical callable has unresolved required parameters: "
            + ", ".join(unresolved)
        )
    return callable_object(**kwargs)


def _diff(
    before: Mapping[str, RuntimeArtifactState],
    after: Mapping[str, RuntimeArtifactState],
) -> tuple[tuple[RuntimeArtifactState, ...], tuple[RuntimeArtifactState, ...]]:
    new = tuple(after[key] for key in sorted(set(after) - set(before)))
    changed = tuple(
        after[key] for key in sorted(set(after) & set(before))
        if after[key].sha256 != before[key].sha256
        or after[key].byte_count != before[key].byte_count
    )
    return new, changed


def _write_control_receipt(root: Path, receipt: OracleBoundedActivationReceipt) -> None:
    path = root / CONTROL_RECEIPT
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(_canonical(receipt), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _receipt(
    *,
    root: Path,
    entry: str,
    required_inputs: tuple[str, ...],
    selected: GenuineInputCandidate | None,
    candidate_count: int,
    readiness: str,
    attempted: bool,
    executed: bool,
    completed: bool,
    new: tuple[RuntimeArtifactState, ...] = (),
    changed: tuple[RuntimeArtifactState, ...] = (),
    protected_unchanged: bool = True,
    outside_unchanged: bool = True,
    failure: str | None = None,
    executed_at: str | None = None,
) -> OracleBoundedActivationReceipt:
    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": "bounded_activation_completed" if completed else "bounded_activation_not_completed",
        "repository_root": root.as_posix(),
        "analytics_entry_point": entry,
        "required_inputs": required_inputs,
        "selected_input": selected,
        "candidate_count": candidate_count,
        "persistence_target": INTELLIGENCE_ROOT,
        "activation_readiness": readiness,
        "activation_attempted": attempted,
        "analytics_execution_performed": executed,
        "invocation_completed": completed,
        "persist_requested": attempted,
        "new_intelligence_artifacts": new,
        "changed_intelligence_artifacts": changed,
        "protected_source_unchanged": protected_unchanged,
        "outside_target_runtime_unchanged": outside_unchanged,
        "database_write_requested": False,
        "publication_allowed": False,
        "qseries_execution_allowed": False,
        "bounded_once": True,
        "failure_reason": failure,
        "executed_at_utc": executed_at,
    }
    return OracleBoundedActivationReceipt(**body, receipt_hash=_stable_hash(body))


def verify_bounded_activation_receipt(
    receipt: OracleBoundedActivationReceipt,
) -> bool:
    body = asdict(receipt)
    supplied = body.pop("receipt_hash")
    if _stable_hash(body) != supplied:
        raise OracleBoundedActivationInvariantError("OIT-004 receipt hash mismatch")
    if receipt.database_write_requested:
        raise OracleBoundedActivationInvariantError("database write requested")
    if receipt.publication_allowed or receipt.qseries_execution_allowed:
        raise OracleBoundedActivationInvariantError("unsafe execution boundary")
    if not receipt.bounded_once:
        raise OracleBoundedActivationInvariantError("activation is not bounded once")
    if receipt.invocation_completed:
        if not receipt.analytics_execution_performed:
            raise OracleBoundedActivationInvariantError("completion without execution")
        if not (
            receipt.new_intelligence_artifacts
            or receipt.changed_intelligence_artifacts
        ):
            raise OracleBoundedActivationInvariantError(
                "completion without genuine intelligence persistence"
            )
        if not receipt.protected_source_unchanged:
            raise OracleBoundedActivationInvariantError("protected source changed")
        if not receipt.outside_target_runtime_unchanged:
            raise OracleBoundedActivationInvariantError(
                "runtime changed outside canonical intelligence target"
            )
    return True


def inspect_bounded_activation(
    *, repository_root: Path,
) -> OracleBoundedActivationReceipt:
    root = repository_root.resolve()
    discovery = discover_live_intelligence_activation(repository_root=root)
    verify_activation_discovery(discovery)
    entry = (
        f"{discovery.canonical_entry_module}:{discovery.canonical_entry_callable}"
        if discovery.canonical_entry_module and discovery.canonical_entry_callable
        else "not identified"
    )
    candidates = discover_genuine_input_candidates(repository_root=root)
    selected = candidates[0] if candidates else None
    ready = bool(
        discovery.static_chain_executable
        and discovery.canonical_entry_module
        and discovery.canonical_entry_callable
        and selected is not None
    )
    return _receipt(
        root=root,
        entry=entry,
        required_inputs=discovery.required_inputs,
        selected=selected,
        candidate_count=len(candidates),
        readiness="ready_for_activate_once" if ready else "blocked_no_genuine_certified_input",
        attempted=False,
        executed=False,
        completed=False,
        failure=None if ready else "no eligible genuine runtime input was discovered",
    )


def activate_once(
    *, repository_root: Path,
) -> OracleBoundedActivationReceipt:
    root = repository_root.resolve()
    control = root / CONTROL_RECEIPT
    if control.exists():
        try:
            prior = json.loads(control.read_text(encoding="utf-8"))
            if prior.get("invocation_completed") is True:
                raise OracleBoundedActivationInvariantError(
                    "OIT-004 bounded activation already completed"
                )
        except json.JSONDecodeError as exc:
            raise OracleBoundedActivationInvariantError(
                "existing OIT-004 control receipt is invalid"
            ) from exc

    discovery = discover_live_intelligence_activation(repository_root=root)
    verify_activation_discovery(discovery)
    if not (
        discovery.static_chain_executable
        and discovery.canonical_entry_module
        and discovery.canonical_entry_callable
    ):
        raise OracleBoundedActivationInvariantError(
            "OIT-003 did not certify an executable analytics entry point"
        )

    candidates = discover_genuine_input_candidates(repository_root=root)
    if not candidates:
        raise OracleBoundedActivationInvariantError(
            "no eligible genuine certified runtime input found; activation refused"
        )
    selected = candidates[0]
    selected_path = root / selected.relative_path
    if _sha256(selected_path) != selected.sha256:
        raise OracleBoundedActivationInvariantError(
            "selected input changed after discovery"
        )

    payload, _, _ = _load_json_candidate(selected_path)
    certified_artifacts = _unwrap_certified_artifacts(payload)
    if certified_artifacts in (None, {}, []):
        raise OracleBoundedActivationInvariantError(
            "selected certified input is empty"
        )

    source_before = _source_snapshot(root)
    runtime_before = _runtime_snapshot(root)
    intelligence_before = _intelligence_snapshot(runtime_before)
    executed_at = datetime.now(timezone.utc)
    entry = (
        f"{discovery.canonical_entry_module}:{discovery.canonical_entry_callable}"
    )

    try:
        callable_object = _resolve_callable(
            discovery.canonical_entry_module,
            discovery.canonical_entry_callable,
        )
        context = _build_execution_context(
            candidate=selected,
            executed_at=executed_at,
        )
        _invoke(
            callable_object,
            certified_artifacts=certified_artifacts,
            execution_context=context,
            executed_at=executed_at,
        )
    except Exception as exc:
        source_after = _source_snapshot(root)
        runtime_after = _runtime_snapshot(root)
        outside_before = {
            key: value for key, value in runtime_before.items()
            if not key.startswith(INTELLIGENCE_ROOT + "/")
        }
        outside_after = {
            key: value for key, value in runtime_after.items()
            if not key.startswith(INTELLIGENCE_ROOT + "/")
        }
        receipt = _receipt(
            root=root,
            entry=entry,
            required_inputs=discovery.required_inputs,
            selected=selected,
            candidate_count=len(candidates),
            readiness="activation_failed_closed",
            attempted=True,
            executed=True,
            completed=False,
            protected_unchanged=source_before == source_after,
            outside_unchanged=outside_before == outside_after,
            failure=f"{type(exc).__name__}: {exc}",
            executed_at=executed_at.isoformat(),
        )
        verify_bounded_activation_receipt(receipt)
        raise OracleBoundedActivationInvariantError(receipt.failure_reason or "activation failed") from exc

    source_after = _source_snapshot(root)
    runtime_after = _runtime_snapshot(root)
    intelligence_after = _intelligence_snapshot(runtime_after)
    new, changed = _diff(intelligence_before, intelligence_after)

    outside_before = {
        key: value for key, value in runtime_before.items()
        if not key.startswith(INTELLIGENCE_ROOT + "/")
    }
    outside_after = {
        key: value for key, value in runtime_after.items()
        if not key.startswith(INTELLIGENCE_ROOT + "/")
    }
    protected_unchanged = source_before == source_after
    outside_unchanged = outside_before == outside_after

    if not protected_unchanged:
        raise OracleBoundedActivationInvariantError(
            "protected subsystem source changed during activation"
        )
    if not outside_unchanged:
        raise OracleBoundedActivationInvariantError(
            "runtime changed outside runtime/oracle_intelligence"
        )
    if not new and not changed:
        raise OracleBoundedActivationInvariantError(
            "analytics invocation returned without producing a genuine "
            "runtime/oracle_intelligence artifact"
        )

    receipt = _receipt(
        root=root,
        entry=entry,
        required_inputs=discovery.required_inputs,
        selected=selected,
        candidate_count=len(candidates),
        readiness="activation_completed",
        attempted=True,
        executed=True,
        completed=True,
        new=new,
        changed=changed,
        protected_unchanged=True,
        outside_unchanged=True,
        executed_at=executed_at.isoformat(),
    )
    verify_bounded_activation_receipt(receipt)
    _write_control_receipt(root, receipt)
    return receipt


def bounded_activation_lines(
    receipt: OracleBoundedActivationReceipt,
) -> tuple[str, ...]:
    verify_bounded_activation_receipt(receipt)
    selected = receipt.selected_input.relative_path if receipt.selected_input else "none"
    new = ", ".join(item.relative_path for item in receipt.new_intelligence_artifacts) or "none"
    changed = ", ".join(item.relative_path for item in receipt.changed_intelligence_artifacts) or "none"
    return (
        "ORACLE BOUNDED LIVE INTELLIGENCE ACTIVATION",
        f"analytics_entry_point: {receipt.analytics_entry_point}",
        f"required_inputs: {', '.join(receipt.required_inputs) or 'none'}",
        f"selected_genuine_input: {selected}",
        f"eligible_input_candidates: {receipt.candidate_count}",
        f"persistence_target: {receipt.persistence_target}",
        f"activation_readiness: {receipt.activation_readiness}",
        f"activation_attempted: {str(receipt.activation_attempted).lower()}",
        f"analytics_execution_performed: {str(receipt.analytics_execution_performed).lower()}",
        f"invocation_completed: {str(receipt.invocation_completed).lower()}",
        f"new_intelligence_artifacts: {new}",
        f"changed_intelligence_artifacts: {changed}",
        f"protected_source_unchanged: {str(receipt.protected_source_unchanged).lower()}",
        f"outside_target_runtime_unchanged: {str(receipt.outside_target_runtime_unchanged).lower()}",
        f"failure_reason: {receipt.failure_reason or 'none'}",
        "database_write_requested: false",
        "publication_allowed: false",
        "qseries_execution_allowed: false",
        "bounded_once: true",
    )
