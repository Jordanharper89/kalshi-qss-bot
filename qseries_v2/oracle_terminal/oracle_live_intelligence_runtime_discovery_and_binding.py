from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .oracle_open_intelligence_terminal_foundation import (
    OracleOpenIntelligenceTerminalInvariantError,
    OracleTerminalCommand,
    OracleTerminalDependencyReceipt,
    OracleTerminalResponse,
    execute_terminal_command,
    stable_hash,
    verify_dependency_receipt,
)

SCHEMA_VERSION = "OIT-002"
ENGINE_ID = "OIT-002"
POLICY_ID = "oracle.live-intelligence-runtime-discovery-and-binding.v1"
BINDING_STATUS = "live_intelligence_runtime_discovery_ready"

RUNTIME_CANDIDATES = (
    "runtime/oracle_intelligence",
    "runtime/oracle_intelligence/forward_shadow_evaluations",
    "runtime/oracle_intelligence/forward_shadow_calibration",
    "runtime/oracle_intelligence/forward_shadow_reliability",
    "runtime/oracle_intelligence/forward_shadow_confidence",
    "runtime/oracle_live_shadow",
    "runtime/oracle_research_response",
)

SYSTEM_BINDING_COMMANDS = {
    "status",
    "health",
    "runtime",
    "certification",
    "freshness",
    "coverage",
    "capabilities",
}

_RUNTIME_LITERAL = re.compile(
    r"runtime[\\/]+oracle_intelligence(?:[\\/]+[A-Za-z0-9_.-]+)*",
    re.IGNORECASE,
)


class OracleLiveIntelligenceBindingInvariantError(
    OracleOpenIntelligenceTerminalInvariantError
):
    pass


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _canonical(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if isinstance(value, Path):
        return value.as_posix()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"unsupported canonical type: {type(value)!r}")


def _hash_payload(value: Any) -> str:
    payload = json.dumps(
        _canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _safe_relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _iter_files(root: Path) -> Iterable[Path]:
    if not root.is_dir():
        return ()
    return (path for path in root.rglob("*") if path.is_file())


def _count_files(root: Path) -> int:
    return sum(1 for _ in _iter_files(root))


def _latest_file(root: Path) -> tuple[Path | None, int | None]:
    latest: Path | None = None
    latest_ns: int | None = None
    for path in _iter_files(root):
        try:
            modified = path.stat().st_mtime_ns
        except OSError:
            continue
        if latest_ns is None or modified > latest_ns:
            latest = path
            latest_ns = modified
    return latest, latest_ns


def _iso_from_ns(value: int | None) -> str | None:
    if value is None:
        return None
    return datetime.fromtimestamp(value / 1_000_000_000, tz=timezone.utc).isoformat()


def _discover_declared_runtime_targets(analytics_root: Path, repository_root: Path) -> tuple[str, ...]:
    discovered: set[str] = set()
    if analytics_root.is_dir():
        for module in analytics_root.rglob("*.py"):
            try:
                text = module.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for match in _RUNTIME_LITERAL.findall(text):
                normalized = match.replace("\\", "/").rstrip("/")
                discovered.add(normalized)
    for candidate in RUNTIME_CANDIDATES:
        discovered.add(candidate)
    return tuple(sorted(discovered))


@dataclass(frozen=True)
class OracleRuntimeLocation:
    relative_path: str
    exists: bool
    file_count: int
    latest_file: str | None
    latest_modified_utc: str | None
    read_only_binding: bool
    location_hash: str


@dataclass(frozen=True)
class OracleLiveIntelligenceBindingReceipt:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    analytics_package_present: bool
    analytics_module_count: int
    declared_runtime_targets: tuple[str, ...]
    runtime_locations: tuple[OracleRuntimeLocation, ...]
    intelligence_runtime_present: bool
    intelligence_runtime_file_count: int
    bindable_artifact_count: int
    binding_active: bool
    live_shadow_runtime_present: bool
    research_response_runtime_present: bool
    read_only: bool
    execution_allowed: bool
    publication_allowed: bool
    qseries_mutation_allowed: bool
    receipt_hash: str


def _location_record(repository_root: Path, relative_path: str) -> OracleRuntimeLocation:
    path = repository_root / Path(relative_path)
    file_count = _count_files(path)
    latest, latest_ns = _latest_file(path)
    body = {
        "relative_path": relative_path,
        "exists": path.is_dir(),
        "file_count": file_count,
        "latest_file": _safe_relative(latest, repository_root) if latest else None,
        "latest_modified_utc": _iso_from_ns(latest_ns),
        "read_only_binding": True,
    }
    return OracleRuntimeLocation(**body, location_hash=_hash_payload(body))


def discover_live_intelligence_binding(
    *, repository_root: Path
) -> OracleLiveIntelligenceBindingReceipt:
    root = repository_root.resolve()
    analytics_root = root / "qseries_v2" / "oracle_intelligence" / "analytics"
    analytics_module_count = sum(1 for _ in analytics_root.rglob("*.py")) if analytics_root.is_dir() else 0
    targets = _discover_declared_runtime_targets(analytics_root, root)
    locations = tuple(_location_record(root, target) for target in targets)

    intelligence_locations = tuple(
        item for item in locations
        if item.relative_path == "runtime/oracle_intelligence"
        or item.relative_path.startswith("runtime/oracle_intelligence/")
    )
    intelligence_root = next(
        (item for item in intelligence_locations if item.relative_path == "runtime/oracle_intelligence"),
        None,
    )
    intelligence_runtime_present = bool(intelligence_root and intelligence_root.exists)
    intelligence_runtime_file_count = intelligence_root.file_count if intelligence_root else 0
    bindable_artifact_count = sum(item.file_count for item in intelligence_locations)
    binding_active = intelligence_runtime_present and intelligence_runtime_file_count > 0

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": BINDING_STATUS,
        "repository_root": root.as_posix(),
        "analytics_package_present": analytics_root.is_dir(),
        "analytics_module_count": analytics_module_count,
        "declared_runtime_targets": targets,
        "runtime_locations": locations,
        "intelligence_runtime_present": intelligence_runtime_present,
        "intelligence_runtime_file_count": intelligence_runtime_file_count,
        "bindable_artifact_count": bindable_artifact_count,
        "binding_active": binding_active,
        "live_shadow_runtime_present": (root / "runtime" / "oracle_live_shadow").is_dir(),
        "research_response_runtime_present": (root / "runtime" / "oracle_research_response").is_dir(),
        "read_only": True,
        "execution_allowed": False,
        "publication_allowed": False,
        "qseries_mutation_allowed": False,
    }
    return OracleLiveIntelligenceBindingReceipt(
        **body, receipt_hash=_hash_payload(body)
    )


def verify_live_intelligence_binding(
    receipt: OracleLiveIntelligenceBindingReceipt,
) -> bool:
    body = asdict(receipt)
    supplied = body.pop("receipt_hash")
    for location in receipt.runtime_locations:
        location_body = asdict(location)
        location_hash = location_body.pop("location_hash")
        if _hash_payload(location_body) != location_hash:
            raise OracleLiveIntelligenceBindingInvariantError(
                "runtime location hash mismatch"
            )
    if _hash_payload(body) != supplied:
        raise OracleLiveIntelligenceBindingInvariantError("binding receipt hash mismatch")
    if not receipt.read_only:
        raise OracleLiveIntelligenceBindingInvariantError("binding is not read-only")
    if receipt.execution_allowed or receipt.publication_allowed:
        raise OracleLiveIntelligenceBindingInvariantError("unsafe Oracle binding boundary")
    if receipt.qseries_mutation_allowed:
        raise OracleLiveIntelligenceBindingInvariantError("Q Series mutation enabled")
    if receipt.binding_active and not receipt.intelligence_runtime_present:
        raise OracleLiveIntelligenceBindingInvariantError("active binding without runtime")
    return True


def _line_for_location(location: OracleRuntimeLocation) -> str:
    state = "available" if location.exists else "not found"
    return f"{location.relative_path}: {state} ({location.file_count} files)"


def _binding_lines(
    command: str,
    receipt: OracleLiveIntelligenceBindingReceipt,
) -> tuple[str, ...]:
    intelligence_state = "available" if receipt.intelligence_runtime_present else "not found"
    binding_state = "active" if receipt.binding_active else "waiting for persisted analytics output"
    latest = next(
        (
            location
            for location in receipt.runtime_locations
            if location.relative_path == "runtime/oracle_intelligence"
        ),
        None,
    )

    if command == "status":
        return (
            f"live_intelligence_binding: {binding_state}",
            f"intelligence_runtime: {intelligence_state} ({receipt.intelligence_runtime_file_count} files)",
            f"analytics_runtime_targets_discovered: {len(receipt.declared_runtime_targets)}",
            f"bindable_intelligence_artifacts: {receipt.bindable_artifact_count}",
            "terminal_binding_mode: read-only filesystem discovery",
        )
    if command == "health":
        return (
            "OIT-002 binding health: READY",
            f"analytics_package: {'available' if receipt.analytics_package_present else 'not found'} ({receipt.analytics_module_count} modules)",
            f"live_shadow_runtime: {'available' if receipt.live_shadow_runtime_present else 'not found'}",
            f"research_response_runtime: {'available' if receipt.research_response_runtime_present else 'not found'}",
            f"intelligence_binding: {binding_state}",
            "execution/publication/Q Series mutation: disabled",
        )
    if command == "runtime":
        lines = [
            "CANONICAL ORACLE RUNTIME DISCOVERY",
            *(_line_for_location(location) for location in receipt.runtime_locations),
            f"binding: {binding_state}",
        ]
        return tuple(lines)
    if command == "freshness":
        return (
            "INTELLIGENCE RUNTIME FRESHNESS",
            f"latest_artifact: {latest.latest_file if latest and latest.latest_file else 'not available'}",
            f"latest_modified_utc: {latest.latest_modified_utc if latest and latest.latest_modified_utc else 'not available'}",
            f"binding: {binding_state}",
            "No timestamp was invented when no persisted artifact existed.",
        )
    if command == "coverage":
        return (
            "INTELLIGENCE RUNTIME COVERAGE",
            f"analytics_modules_installed: {receipt.analytics_module_count}",
            f"declared_runtime_targets: {len(receipt.declared_runtime_targets)}",
            f"existing_runtime_targets: {sum(1 for item in receipt.runtime_locations if item.exists)}",
            f"bindable_artifacts: {receipt.bindable_artifact_count}",
            f"live_intelligence_output: {'present' if receipt.binding_active else 'not yet present'}",
        )
    if command == "capabilities":
        return (
            "LIVE BINDING CAPABILITIES",
            "discover canonical analytics persistence targets",
            "count and locate persisted intelligence artifacts",
            "report latest intelligence artifact without mutation",
            "bind system inspection commands to live filesystem state",
            "defer analysis when no real intelligence artifact exists",
            "execution, publication, order, funds, and portfolio mutation remain disabled",
        )
    if command == "certification":
        return (
            "OIT-002 LIVE INTELLIGENCE RUNTIME DISCOVERY AND BINDING",
            f"status: {receipt.status}",
            f"receipt_hash: {receipt.receipt_hash}",
            "read_only: true",
            "execution_allowed: false",
            "publication_allowed: false",
            "qseries_mutation_allowed: false",
        )
    return ()


def execute_bound_terminal_command(
    command: OracleTerminalCommand,
    *,
    repository_root: Path,
    dependency_receipt: OracleTerminalDependencyReceipt,
) -> OracleTerminalResponse:
    if not verify_dependency_receipt(dependency_receipt):
        raise OracleLiveIntelligenceBindingInvariantError(
            "OIT-001 dependency receipt verification failed"
        )
    base = execute_terminal_command(
        command,
        repository_root=repository_root,
        dependency_receipt=dependency_receipt,
    )
    if command.command not in SYSTEM_BINDING_COMMANDS:
        return base

    binding = discover_live_intelligence_binding(repository_root=repository_root)
    verify_live_intelligence_binding(binding)
    appended = _binding_lines(command.command, binding)
    body = asdict(base)
    body.pop("response_hash")
    body["lines"] = tuple(base.lines) + ("",) + appended
    body["data_available"] = base.data_available or binding.binding_active
    return OracleTerminalResponse(**body, response_hash=stable_hash(body))


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "BINDING_STATUS",
    "RUNTIME_CANDIDATES",
    "SYSTEM_BINDING_COMMANDS",
    "OracleLiveIntelligenceBindingInvariantError",
    "OracleRuntimeLocation",
    "OracleLiveIntelligenceBindingReceipt",
    "discover_live_intelligence_binding",
    "verify_live_intelligence_binding",
    "execute_bound_terminal_command",
]
