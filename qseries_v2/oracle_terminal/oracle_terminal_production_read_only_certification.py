from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .oracle_end_to_end_interactive_intelligence_pipeline import (
    OracleInteractiveIntelligencePipelineReport,
    verify_interactive_intelligence_pipeline_report,
)

SCHEMA_VERSION = "OIT-049"
ENGINE_ID = "OIT-049"
POLICY_ID = "oracle-terminal.production-read-only-certification.v3"

REQUIRED_RUNNER_VERSION = "OIT-048"
REQUIRED_PIPELINE_VERSION = "OIT-048"
REQUIRED_COMMANDS = (
    "/help",
    "/status",
    "/ask",
    "/session",
    "/clear",
    "/quit",
)


class OracleTerminalProductionCertificationInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleTerminalCommandRegistryCertification:
    searched_paths: tuple[str, ...]
    discovered_commands: tuple[str, ...]
    required_commands: tuple[str, ...]
    missing_commands: tuple[str, ...]
    command_registry_certified: bool
    certification_hash: str


@dataclass(frozen=True)
class OracleTerminalRunnerCertification:
    runner_path: str
    runner_sha256: str
    runner_byte_count: int
    runner_version: str
    pipeline_version: str
    pipeline_bound: bool
    execute_callable_available: bool
    render_callable_available: bool
    command_registry: OracleTerminalCommandRegistryCertification
    read_only_boundary_present: bool
    publication_disabled: bool
    action_authorization_disabled: bool
    qseries_execution_disabled: bool
    runner_certified: bool
    certification_hash: str


@dataclass(frozen=True)
class OracleTerminalPipelineCertification:
    pipeline_report_hash: str
    pipeline_result_hash: str
    pipeline_completed: bool
    terminal_display_ready: bool
    session_continuation_ready: bool
    exact_stage_order_verified: bool
    exact_cross_stage_lineage_verified: bool
    live_runner_binding_ready: bool
    persistent_memory_enabled: bool
    learning_update_performed: bool
    publication_allowed: bool
    action_authorization_allowed: bool
    qseries_execution_allowed: bool
    pipeline_certified: bool
    certification_hash: str


@dataclass(frozen=True)
class OracleTerminalProductionReadOnlyCertificationReport:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    runner_certification: OracleTerminalRunnerCertification
    pipeline_certification: OracleTerminalPipelineCertification
    production_readiness_certified: bool
    final_freeze_ready: bool
    persistent_memory_enabled: bool
    learning_update_performed: bool
    analytics_execution_performed: bool
    database_access_performed: bool
    runtime_artifact_created: bool
    runtime_artifact_modified: bool
    networking_performed: bool
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
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleTerminalProductionCertificationInvariantError(
        f"unsupported OIT-049 value type: "
        f"{type(value).__module__}.{type(value).__qualname__}"
    )


def _stable_hash(value: Any) -> str:
    payload = json.dumps(
        _canonical(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_runner(path: Path):
    module_name = "oracle_open_intelligence_terminal_oit_049_v3"
    specification = importlib.util.spec_from_file_location(module_name, path)
    if specification is None or specification.loader is None:
        raise OracleTerminalProductionCertificationInvariantError(
            "unable to create live runner import specification"
        )
    module = importlib.util.module_from_spec(specification)
    sys.modules[module_name] = module
    specification.loader.exec_module(module)
    return module


def verify_command_registry_certification(
    certification: OracleTerminalCommandRegistryCertification,
) -> bool:
    body = asdict(certification)
    supplied = body.pop("certification_hash")
    if _stable_hash(body) != supplied:
        raise OracleTerminalProductionCertificationInvariantError(
            "OIT-049 command-registry certification hash mismatch"
        )
    expected_missing = tuple(
        command
        for command in certification.required_commands
        if command not in certification.discovered_commands
    )
    if certification.missing_commands != expected_missing:
        raise OracleTerminalProductionCertificationInvariantError(
            "OIT-049 missing-command state mismatch"
        )
    expected = bool(
        certification.searched_paths
        and certification.required_commands
        and not expected_missing
    )
    if certification.command_registry_certified != expected:
        raise OracleTerminalProductionCertificationInvariantError(
            "OIT-049 command-registry certification mismatch"
        )
    return True


def certify_command_registry(
    repository_root: str | Path,
) -> OracleTerminalCommandRegistryCertification:
    root = Path(repository_root).resolve()
    package = root / "qseries_v2" / "oracle_terminal"

    candidate_paths: list[Path] = []
    preferred = (
        package / "oracle_terminal_interactive_command_registry.py",
        package / "oracle_terminal_evidence_panel_navigation.py",
        root / "run_oracle_open_intelligence_terminal.py",
    )
    for path in preferred:
        if path.is_file():
            candidate_paths.append(path)

    for path in sorted(package.glob("*command*registry*.py")):
        if path.is_file() and path not in candidate_paths:
            candidate_paths.append(path)

    for path in sorted(package.glob("*panel*navigation*.py")):
        if path.is_file() and path not in candidate_paths:
            candidate_paths.append(path)

    discovered: set[str] = set()
    for path in candidate_paths:
        source = path.read_text(encoding="utf-8")
        for command in REQUIRED_COMMANDS:
            if command in source:
                discovered.add(command)

    discovered_commands = tuple(
        command for command in REQUIRED_COMMANDS if command in discovered
    )
    missing = tuple(
        command for command in REQUIRED_COMMANDS if command not in discovered
    )

    body = {
        "searched_paths": tuple(str(path) for path in candidate_paths),
        "discovered_commands": discovered_commands,
        "required_commands": REQUIRED_COMMANDS,
        "missing_commands": missing,
        "command_registry_certified": bool(candidate_paths and not missing),
    }
    certification = OracleTerminalCommandRegistryCertification(
        **body,
        certification_hash=_stable_hash(body),
    )
    verify_command_registry_certification(certification)
    return certification


def verify_runner_certification(
    certification: OracleTerminalRunnerCertification,
) -> bool:
    body = asdict(certification)
    supplied = body.pop("certification_hash")
    if _stable_hash(body) != supplied:
        raise OracleTerminalProductionCertificationInvariantError(
            "OIT-049 runner certification hash mismatch"
        )

    verify_command_registry_certification(certification.command_registry)

    expected = bool(
        certification.runner_path
        and len(certification.runner_sha256) == 64
        and certification.runner_byte_count > 0
        and certification.runner_version == REQUIRED_RUNNER_VERSION
        and certification.pipeline_version == REQUIRED_PIPELINE_VERSION
        and certification.pipeline_bound
        and certification.execute_callable_available
        and certification.render_callable_available
        and certification.command_registry.command_registry_certified
        and certification.read_only_boundary_present
        and certification.publication_disabled
        and certification.action_authorization_disabled
        and certification.qseries_execution_disabled
    )
    if certification.runner_certified != expected:
        raise OracleTerminalProductionCertificationInvariantError(
            "OIT-049 runner certification state mismatch"
        )
    return True


def certify_live_terminal_runner(
    repository_root: str | Path,
) -> OracleTerminalRunnerCertification:
    root = Path(repository_root).resolve()
    runner_path = root / "run_oracle_open_intelligence_terminal.py"
    if not runner_path.is_file():
        raise OracleTerminalProductionCertificationInvariantError(
            f"live Oracle terminal runner missing: {runner_path}"
        )

    source = runner_path.read_text(encoding="utf-8")
    module = _load_runner(runner_path)
    command_registry = certify_command_registry(root)

    runner_version = str(getattr(module, "RUNNER_VERSION", ""))
    pipeline_version = str(
        getattr(module, "OIT_048_PIPELINE_VERSION", "")
    )
    pipeline_bound = bool(
        getattr(module, "OIT_048_PIPELINE_BOUND", False)
    )
    execute_available = callable(
        getattr(module, "execute_oit_048_interactive_pipeline", None)
    )
    render_available = callable(
        getattr(module, "render_oit_048_interactive_pipeline", None)
    )

    combined_sources = source + "\n" + "\n".join(
        Path(path).read_text(encoding="utf-8")
        for path in command_registry.searched_paths
        if Path(path).is_file()
    )

    read_only_present = (
        "interactive read-only" in combined_sources
        or "read_only" in combined_sources
    )
    publication_disabled = (
        "publication: disabled" in combined_sources
        or "publication_allowed" in combined_sources
    )
    action_disabled = (
        "action authorization: disabled" in combined_sources
        or "action_authorization_allowed" in combined_sources
    )
    execution_disabled = (
        "Q Series execution: disabled" in combined_sources
        or "qseries_execution_allowed" in combined_sources
    )

    certified = bool(
        runner_version == REQUIRED_RUNNER_VERSION
        and pipeline_version == REQUIRED_PIPELINE_VERSION
        and pipeline_bound
        and execute_available
        and render_available
        and command_registry.command_registry_certified
        and read_only_present
        and publication_disabled
        and action_disabled
        and execution_disabled
    )

    body = {
        "runner_path": str(runner_path),
        "runner_sha256": _sha256(runner_path),
        "runner_byte_count": runner_path.stat().st_size,
        "runner_version": runner_version,
        "pipeline_version": pipeline_version,
        "pipeline_bound": pipeline_bound,
        "execute_callable_available": execute_available,
        "render_callable_available": render_available,
        "command_registry": command_registry,
        "read_only_boundary_present": read_only_present,
        "publication_disabled": publication_disabled,
        "action_authorization_disabled": action_disabled,
        "qseries_execution_disabled": execution_disabled,
        "runner_certified": certified,
    }
    certification = OracleTerminalRunnerCertification(
        **body,
        certification_hash=_stable_hash(body),
    )
    verify_runner_certification(certification)
    return certification


def verify_pipeline_certification(
    certification: OracleTerminalPipelineCertification,
) -> bool:
    body = asdict(certification)
    supplied = body.pop("certification_hash")
    if _stable_hash(body) != supplied:
        raise OracleTerminalProductionCertificationInvariantError(
            "OIT-049 pipeline certification hash mismatch"
        )
    expected = bool(
        certification.pipeline_completed
        and certification.terminal_display_ready
        and certification.session_continuation_ready
        and certification.exact_stage_order_verified
        and certification.exact_cross_stage_lineage_verified
        and certification.live_runner_binding_ready
        and not certification.persistent_memory_enabled
        and not certification.learning_update_performed
        and not certification.publication_allowed
        and not certification.action_authorization_allowed
        and not certification.qseries_execution_allowed
    )
    if certification.pipeline_certified != expected:
        raise OracleTerminalProductionCertificationInvariantError(
            "OIT-049 pipeline certification state mismatch"
        )
    return True


def certify_interactive_pipeline(
    pipeline_report: OracleInteractiveIntelligencePipelineReport,
) -> OracleTerminalPipelineCertification:
    verify_interactive_intelligence_pipeline_report(pipeline_report)
    result = pipeline_report.pipeline_result
    lineage = result.lineage

    body = {
        "pipeline_report_hash": pipeline_report.report_hash,
        "pipeline_result_hash": result.result_hash,
        "pipeline_completed": result.pipeline_completed,
        "terminal_display_ready": result.terminal_display_ready,
        "session_continuation_ready": result.session_continuation_ready,
        "exact_stage_order_verified": lineage.exact_stage_order_verified,
        "exact_cross_stage_lineage_verified": (
            lineage.exact_cross_stage_lineage_verified
        ),
        "live_runner_binding_ready": pipeline_report.live_runner_binding_ready,
        "persistent_memory_enabled": pipeline_report.persistent_memory_enabled,
        "learning_update_performed": pipeline_report.learning_update_performed,
        "publication_allowed": pipeline_report.publication_allowed,
        "action_authorization_allowed": (
            pipeline_report.action_authorization_allowed
        ),
        "qseries_execution_allowed": pipeline_report.qseries_execution_allowed,
        "pipeline_certified": bool(
            result.pipeline_completed
            and result.terminal_display_ready
            and result.session_continuation_ready
            and lineage.exact_stage_order_verified
            and lineage.exact_cross_stage_lineage_verified
            and pipeline_report.live_runner_binding_ready
            and not pipeline_report.persistent_memory_enabled
            and not pipeline_report.learning_update_performed
            and not pipeline_report.publication_allowed
            and not pipeline_report.action_authorization_allowed
            and not pipeline_report.qseries_execution_allowed
        ),
    }
    certification = OracleTerminalPipelineCertification(
        **body,
        certification_hash=_stable_hash(body),
    )
    verify_pipeline_certification(certification)
    return certification


def build_oracle_terminal_production_read_only_certification_report(
    repository_root: str | Path,
    *,
    pipeline_report: OracleInteractiveIntelligencePipelineReport,
) -> OracleTerminalProductionReadOnlyCertificationReport:
    root = Path(repository_root).resolve()
    runner = certify_live_terminal_runner(root)
    pipeline = certify_interactive_pipeline(pipeline_report)
    ready = bool(runner.runner_certified and pipeline.pipeline_certified)

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root),
        "runner_certification": runner,
        "pipeline_certification": pipeline,
        "production_readiness_certified": ready,
        "final_freeze_ready": ready,
        "persistent_memory_enabled": False,
        "learning_update_performed": False,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "runtime_artifact_created": False,
        "runtime_artifact_modified": False,
        "networking_performed": False,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
        "read_only": True,
        "failure_reason": None if ready else "OIT-049 certification failed",
    }
    report = OracleTerminalProductionReadOnlyCertificationReport(
        **body,
        report_hash=_stable_hash(body),
    )
    verify_oracle_terminal_production_read_only_certification_report(report)
    return report


def verify_oracle_terminal_production_read_only_certification_report(
    report: OracleTerminalProductionReadOnlyCertificationReport,
) -> bool:
    body = asdict(report)
    supplied = body.pop("report_hash")
    if _stable_hash(body) != supplied:
        raise OracleTerminalProductionCertificationInvariantError(
            "OIT-049 report hash mismatch"
        )
    if report.schema_version != SCHEMA_VERSION or report.policy_id != POLICY_ID:
        raise OracleTerminalProductionCertificationInvariantError(
            "OIT-049 contract mismatch"
        )

    verify_runner_certification(report.runner_certification)
    verify_pipeline_certification(report.pipeline_certification)

    if not report.read_only:
        raise OracleTerminalProductionCertificationInvariantError(
            "OIT-049 report is not read-only"
        )
    if (
        report.persistent_memory_enabled
        or report.learning_update_performed
        or report.analytics_execution_performed
        or report.database_access_performed
        or report.runtime_artifact_created
        or report.runtime_artifact_modified
        or report.networking_performed
        or report.publication_allowed
        or report.action_authorization_allowed
        or report.qseries_execution_allowed
    ):
        raise OracleTerminalProductionCertificationInvariantError(
            "forbidden OIT-049 capability enabled"
        )

    expected = bool(
        report.runner_certification.runner_certified
        and report.pipeline_certification.pipeline_certified
    )
    if report.production_readiness_certified != expected:
        raise OracleTerminalProductionCertificationInvariantError(
            "OIT-049 production readiness mismatch"
        )
    if report.final_freeze_ready != expected:
        raise OracleTerminalProductionCertificationInvariantError(
            "OIT-049 freeze readiness mismatch"
        )
    return True
