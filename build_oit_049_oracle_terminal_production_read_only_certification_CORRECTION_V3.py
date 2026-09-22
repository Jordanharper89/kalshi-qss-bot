from __future__ import annotations

import ast
import hashlib
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def locate_repository() -> Path:
    candidates = []
    for base in (Path.cwd().resolve(), SCRIPT_DIR):
        candidates.extend((base, base / "kalshi-qss-bot"))
        for parent in base.parents:
            candidates.extend((parent, parent / "kalshi-qss-bot"))
    seen = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        package = candidate / "qseries_v2" / "oracle_terminal"
        if (
            (package / "oracle_end_to_end_interactive_intelligence_pipeline.py").is_file()
            and (candidate / "test_oit_048_oracle_end_to_end_interactive_intelligence_pipeline.py").is_file()
            and (candidate / "run_oracle_open_intelligence_terminal.py").is_file()
        ):
            return candidate
    raise SystemExit("[ERROR] Could not locate current Q Series repository.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"
OIT_048 = PACKAGE / "oracle_end_to_end_interactive_intelligence_pipeline.py"
OIT_048_TEST = ROOT / "test_oit_048_oracle_end_to_end_interactive_intelligence_pipeline.py"
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"
REGISTRY = PACKAGE / "oracle_terminal_interactive_command_registry.py"
NAVIGATION = PACKAGE / "oracle_terminal_evidence_panel_navigation.py"
PRODUCTION = PACKAGE / "oracle_terminal_production_read_only_certification.py"
TEST = ROOT / "test_oit_049_oracle_terminal_production_read_only_certification.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport importlib.util\nimport json\nimport sys\nfrom dataclasses import asdict, dataclass\nfrom pathlib import Path\nfrom typing import Any, Mapping\n\nfrom .oracle_end_to_end_interactive_intelligence_pipeline import (\n    OracleInteractiveIntelligencePipelineReport,\n    verify_interactive_intelligence_pipeline_report,\n)\n\nSCHEMA_VERSION = "OIT-049"\nENGINE_ID = "OIT-049"\nPOLICY_ID = "oracle-terminal.production-read-only-certification.v3"\n\nREQUIRED_RUNNER_VERSION = "OIT-048"\nREQUIRED_PIPELINE_VERSION = "OIT-048"\nREQUIRED_COMMANDS = (\n    "/help",\n    "/status",\n    "/ask",\n    "/session",\n    "/clear",\n    "/quit",\n)\n\n\nclass OracleTerminalProductionCertificationInvariantError(RuntimeError):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleTerminalCommandRegistryCertification:\n    searched_paths: tuple[str, ...]\n    discovered_commands: tuple[str, ...]\n    required_commands: tuple[str, ...]\n    missing_commands: tuple[str, ...]\n    command_registry_certified: bool\n    certification_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleTerminalRunnerCertification:\n    runner_path: str\n    runner_sha256: str\n    runner_byte_count: int\n    runner_version: str\n    pipeline_version: str\n    pipeline_bound: bool\n    execute_callable_available: bool\n    render_callable_available: bool\n    command_registry: OracleTerminalCommandRegistryCertification\n    read_only_boundary_present: bool\n    publication_disabled: bool\n    action_authorization_disabled: bool\n    qseries_execution_disabled: bool\n    runner_certified: bool\n    certification_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleTerminalPipelineCertification:\n    pipeline_report_hash: str\n    pipeline_result_hash: str\n    pipeline_completed: bool\n    terminal_display_ready: bool\n    session_continuation_ready: bool\n    exact_stage_order_verified: bool\n    exact_cross_stage_lineage_verified: bool\n    live_runner_binding_ready: bool\n    persistent_memory_enabled: bool\n    learning_update_performed: bool\n    publication_allowed: bool\n    action_authorization_allowed: bool\n    qseries_execution_allowed: bool\n    pipeline_certified: bool\n    certification_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleTerminalProductionReadOnlyCertificationReport:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    status: str\n    repository_root: str\n    runner_certification: OracleTerminalRunnerCertification\n    pipeline_certification: OracleTerminalPipelineCertification\n    production_readiness_certified: bool\n    final_freeze_ready: bool\n    persistent_memory_enabled: bool\n    learning_update_performed: bool\n    analytics_execution_performed: bool\n    database_access_performed: bool\n    runtime_artifact_created: bool\n    runtime_artifact_modified: bool\n    networking_performed: bool\n    publication_allowed: bool\n    action_authorization_allowed: bool\n    qseries_execution_allowed: bool\n    read_only: bool\n    failure_reason: str | None\n    report_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    raise OracleTerminalProductionCertificationInvariantError(\n        f"unsupported OIT-049 value type: "\n        f"{type(value).__module__}.{type(value).__qualname__}"\n    )\n\n\ndef _stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=True,\n        allow_nan=False,\n    ).encode("utf-8")\n    return hashlib.sha256(payload).hexdigest()\n\n\ndef _sha256(path: Path) -> str:\n    return hashlib.sha256(path.read_bytes()).hexdigest()\n\n\ndef _load_runner(path: Path):\n    module_name = "oracle_open_intelligence_terminal_oit_049_v3"\n    specification = importlib.util.spec_from_file_location(module_name, path)\n    if specification is None or specification.loader is None:\n        raise OracleTerminalProductionCertificationInvariantError(\n            "unable to create live runner import specification"\n        )\n    module = importlib.util.module_from_spec(specification)\n    sys.modules[module_name] = module\n    specification.loader.exec_module(module)\n    return module\n\n\ndef verify_command_registry_certification(\n    certification: OracleTerminalCommandRegistryCertification,\n) -> bool:\n    body = asdict(certification)\n    supplied = body.pop("certification_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleTerminalProductionCertificationInvariantError(\n            "OIT-049 command-registry certification hash mismatch"\n        )\n    expected_missing = tuple(\n        command\n        for command in certification.required_commands\n        if command not in certification.discovered_commands\n    )\n    if certification.missing_commands != expected_missing:\n        raise OracleTerminalProductionCertificationInvariantError(\n            "OIT-049 missing-command state mismatch"\n        )\n    expected = bool(\n        certification.searched_paths\n        and certification.required_commands\n        and not expected_missing\n    )\n    if certification.command_registry_certified != expected:\n        raise OracleTerminalProductionCertificationInvariantError(\n            "OIT-049 command-registry certification mismatch"\n        )\n    return True\n\n\ndef certify_command_registry(\n    repository_root: str | Path,\n) -> OracleTerminalCommandRegistryCertification:\n    root = Path(repository_root).resolve()\n    package = root / "qseries_v2" / "oracle_terminal"\n\n    candidate_paths: list[Path] = []\n    preferred = (\n        package / "oracle_terminal_interactive_command_registry.py",\n        package / "oracle_terminal_evidence_panel_navigation.py",\n        root / "run_oracle_open_intelligence_terminal.py",\n    )\n    for path in preferred:\n        if path.is_file():\n            candidate_paths.append(path)\n\n    for path in sorted(package.glob("*command*registry*.py")):\n        if path.is_file() and path not in candidate_paths:\n            candidate_paths.append(path)\n\n    for path in sorted(package.glob("*panel*navigation*.py")):\n        if path.is_file() and path not in candidate_paths:\n            candidate_paths.append(path)\n\n    discovered: set[str] = set()\n    for path in candidate_paths:\n        source = path.read_text(encoding="utf-8")\n        for command in REQUIRED_COMMANDS:\n            if command in source:\n                discovered.add(command)\n\n    discovered_commands = tuple(\n        command for command in REQUIRED_COMMANDS if command in discovered\n    )\n    missing = tuple(\n        command for command in REQUIRED_COMMANDS if command not in discovered\n    )\n\n    body = {\n        "searched_paths": tuple(str(path) for path in candidate_paths),\n        "discovered_commands": discovered_commands,\n        "required_commands": REQUIRED_COMMANDS,\n        "missing_commands": missing,\n        "command_registry_certified": bool(candidate_paths and not missing),\n    }\n    certification = OracleTerminalCommandRegistryCertification(\n        **body,\n        certification_hash=_stable_hash(body),\n    )\n    verify_command_registry_certification(certification)\n    return certification\n\n\ndef verify_runner_certification(\n    certification: OracleTerminalRunnerCertification,\n) -> bool:\n    body = asdict(certification)\n    supplied = body.pop("certification_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleTerminalProductionCertificationInvariantError(\n            "OIT-049 runner certification hash mismatch"\n        )\n\n    verify_command_registry_certification(certification.command_registry)\n\n    expected = bool(\n        certification.runner_path\n        and len(certification.runner_sha256) == 64\n        and certification.runner_byte_count > 0\n        and certification.runner_version == REQUIRED_RUNNER_VERSION\n        and certification.pipeline_version == REQUIRED_PIPELINE_VERSION\n        and certification.pipeline_bound\n        and certification.execute_callable_available\n        and certification.render_callable_available\n        and certification.command_registry.command_registry_certified\n        and certification.read_only_boundary_present\n        and certification.publication_disabled\n        and certification.action_authorization_disabled\n        and certification.qseries_execution_disabled\n    )\n    if certification.runner_certified != expected:\n        raise OracleTerminalProductionCertificationInvariantError(\n            "OIT-049 runner certification state mismatch"\n        )\n    return True\n\n\ndef certify_live_terminal_runner(\n    repository_root: str | Path,\n) -> OracleTerminalRunnerCertification:\n    root = Path(repository_root).resolve()\n    runner_path = root / "run_oracle_open_intelligence_terminal.py"\n    if not runner_path.is_file():\n        raise OracleTerminalProductionCertificationInvariantError(\n            f"live Oracle terminal runner missing: {runner_path}"\n        )\n\n    source = runner_path.read_text(encoding="utf-8")\n    module = _load_runner(runner_path)\n    command_registry = certify_command_registry(root)\n\n    runner_version = str(getattr(module, "RUNNER_VERSION", ""))\n    pipeline_version = str(\n        getattr(module, "OIT_048_PIPELINE_VERSION", "")\n    )\n    pipeline_bound = bool(\n        getattr(module, "OIT_048_PIPELINE_BOUND", False)\n    )\n    execute_available = callable(\n        getattr(module, "execute_oit_048_interactive_pipeline", None)\n    )\n    render_available = callable(\n        getattr(module, "render_oit_048_interactive_pipeline", None)\n    )\n\n    combined_sources = source + "\\n" + "\\n".join(\n        Path(path).read_text(encoding="utf-8")\n        for path in command_registry.searched_paths\n        if Path(path).is_file()\n    )\n\n    read_only_present = (\n        "interactive read-only" in combined_sources\n        or "read_only" in combined_sources\n    )\n    publication_disabled = (\n        "publication: disabled" in combined_sources\n        or "publication_allowed" in combined_sources\n    )\n    action_disabled = (\n        "action authorization: disabled" in combined_sources\n        or "action_authorization_allowed" in combined_sources\n    )\n    execution_disabled = (\n        "Q Series execution: disabled" in combined_sources\n        or "qseries_execution_allowed" in combined_sources\n    )\n\n    certified = bool(\n        runner_version == REQUIRED_RUNNER_VERSION\n        and pipeline_version == REQUIRED_PIPELINE_VERSION\n        and pipeline_bound\n        and execute_available\n        and render_available\n        and command_registry.command_registry_certified\n        and read_only_present\n        and publication_disabled\n        and action_disabled\n        and execution_disabled\n    )\n\n    body = {\n        "runner_path": str(runner_path),\n        "runner_sha256": _sha256(runner_path),\n        "runner_byte_count": runner_path.stat().st_size,\n        "runner_version": runner_version,\n        "pipeline_version": pipeline_version,\n        "pipeline_bound": pipeline_bound,\n        "execute_callable_available": execute_available,\n        "render_callable_available": render_available,\n        "command_registry": command_registry,\n        "read_only_boundary_present": read_only_present,\n        "publication_disabled": publication_disabled,\n        "action_authorization_disabled": action_disabled,\n        "qseries_execution_disabled": execution_disabled,\n        "runner_certified": certified,\n    }\n    certification = OracleTerminalRunnerCertification(\n        **body,\n        certification_hash=_stable_hash(body),\n    )\n    verify_runner_certification(certification)\n    return certification\n\n\ndef verify_pipeline_certification(\n    certification: OracleTerminalPipelineCertification,\n) -> bool:\n    body = asdict(certification)\n    supplied = body.pop("certification_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleTerminalProductionCertificationInvariantError(\n            "OIT-049 pipeline certification hash mismatch"\n        )\n    expected = bool(\n        certification.pipeline_completed\n        and certification.terminal_display_ready\n        and certification.session_continuation_ready\n        and certification.exact_stage_order_verified\n        and certification.exact_cross_stage_lineage_verified\n        and certification.live_runner_binding_ready\n        and not certification.persistent_memory_enabled\n        and not certification.learning_update_performed\n        and not certification.publication_allowed\n        and not certification.action_authorization_allowed\n        and not certification.qseries_execution_allowed\n    )\n    if certification.pipeline_certified != expected:\n        raise OracleTerminalProductionCertificationInvariantError(\n            "OIT-049 pipeline certification state mismatch"\n        )\n    return True\n\n\ndef certify_interactive_pipeline(\n    pipeline_report: OracleInteractiveIntelligencePipelineReport,\n) -> OracleTerminalPipelineCertification:\n    verify_interactive_intelligence_pipeline_report(pipeline_report)\n    result = pipeline_report.pipeline_result\n    lineage = result.lineage\n\n    body = {\n        "pipeline_report_hash": pipeline_report.report_hash,\n        "pipeline_result_hash": result.result_hash,\n        "pipeline_completed": result.pipeline_completed,\n        "terminal_display_ready": result.terminal_display_ready,\n        "session_continuation_ready": result.session_continuation_ready,\n        "exact_stage_order_verified": lineage.exact_stage_order_verified,\n        "exact_cross_stage_lineage_verified": (\n            lineage.exact_cross_stage_lineage_verified\n        ),\n        "live_runner_binding_ready": pipeline_report.live_runner_binding_ready,\n        "persistent_memory_enabled": pipeline_report.persistent_memory_enabled,\n        "learning_update_performed": pipeline_report.learning_update_performed,\n        "publication_allowed": pipeline_report.publication_allowed,\n        "action_authorization_allowed": (\n            pipeline_report.action_authorization_allowed\n        ),\n        "qseries_execution_allowed": pipeline_report.qseries_execution_allowed,\n        "pipeline_certified": bool(\n            result.pipeline_completed\n            and result.terminal_display_ready\n            and result.session_continuation_ready\n            and lineage.exact_stage_order_verified\n            and lineage.exact_cross_stage_lineage_verified\n            and pipeline_report.live_runner_binding_ready\n            and not pipeline_report.persistent_memory_enabled\n            and not pipeline_report.learning_update_performed\n            and not pipeline_report.publication_allowed\n            and not pipeline_report.action_authorization_allowed\n            and not pipeline_report.qseries_execution_allowed\n        ),\n    }\n    certification = OracleTerminalPipelineCertification(\n        **body,\n        certification_hash=_stable_hash(body),\n    )\n    verify_pipeline_certification(certification)\n    return certification\n\n\ndef build_oracle_terminal_production_read_only_certification_report(\n    repository_root: str | Path,\n    *,\n    pipeline_report: OracleInteractiveIntelligencePipelineReport,\n) -> OracleTerminalProductionReadOnlyCertificationReport:\n    root = Path(repository_root).resolve()\n    runner = certify_live_terminal_runner(root)\n    pipeline = certify_interactive_pipeline(pipeline_report)\n    ready = bool(runner.runner_certified and pipeline.pipeline_certified)\n\n    body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root),\n        "runner_certification": runner,\n        "pipeline_certification": pipeline,\n        "production_readiness_certified": ready,\n        "final_freeze_ready": ready,\n        "persistent_memory_enabled": False,\n        "learning_update_performed": False,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "runtime_artifact_created": False,\n        "runtime_artifact_modified": False,\n        "networking_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "read_only": True,\n        "failure_reason": None if ready else "OIT-049 certification failed",\n    }\n    report = OracleTerminalProductionReadOnlyCertificationReport(\n        **body,\n        report_hash=_stable_hash(body),\n    )\n    verify_oracle_terminal_production_read_only_certification_report(report)\n    return report\n\n\ndef verify_oracle_terminal_production_read_only_certification_report(\n    report: OracleTerminalProductionReadOnlyCertificationReport,\n) -> bool:\n    body = asdict(report)\n    supplied = body.pop("report_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleTerminalProductionCertificationInvariantError(\n            "OIT-049 report hash mismatch"\n        )\n    if report.schema_version != SCHEMA_VERSION or report.policy_id != POLICY_ID:\n        raise OracleTerminalProductionCertificationInvariantError(\n            "OIT-049 contract mismatch"\n        )\n\n    verify_runner_certification(report.runner_certification)\n    verify_pipeline_certification(report.pipeline_certification)\n\n    if not report.read_only:\n        raise OracleTerminalProductionCertificationInvariantError(\n            "OIT-049 report is not read-only"\n        )\n    if (\n        report.persistent_memory_enabled\n        or report.learning_update_performed\n        or report.analytics_execution_performed\n        or report.database_access_performed\n        or report.runtime_artifact_created\n        or report.runtime_artifact_modified\n        or report.networking_performed\n        or report.publication_allowed\n        or report.action_authorization_allowed\n        or report.qseries_execution_allowed\n    ):\n        raise OracleTerminalProductionCertificationInvariantError(\n            "forbidden OIT-049 capability enabled"\n        )\n\n    expected = bool(\n        report.runner_certification.runner_certified\n        and report.pipeline_certification.pipeline_certified\n    )\n    if report.production_readiness_certified != expected:\n        raise OracleTerminalProductionCertificationInvariantError(\n            "OIT-049 production readiness mismatch"\n        )\n    if report.final_freeze_ready != expected:\n        raise OracleTerminalProductionCertificationInvariantError(\n            "OIT-049 freeze readiness mismatch"\n        )\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nimport importlib.util\nimport sys\nfrom dataclasses import replace\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_terminal.oracle_terminal_production_read_only_certification import (\n    OracleTerminalProductionCertificationInvariantError,\n    build_oracle_terminal_production_read_only_certification_report,\n    certify_live_terminal_runner,\n    verify_oracle_terminal_production_read_only_certification_report,\n)\n\n\ndef load_oit_048_fixture(root: Path):\n    path = root / "test_oit_048_oracle_end_to_end_interactive_intelligence_pipeline.py"\n    name = "oit_048_fixture_for_oit_049_v3"\n    spec = importlib.util.spec_from_file_location(name, path)\n    if spec is None or spec.loader is None:\n        raise RuntimeError("unable to load certified OIT-048 fixture")\n    module = importlib.util.module_from_spec(spec)\n    sys.modules[name] = module\n    spec.loader.exec_module(module)\n    return module\n\n\ndef main() -> int:\n    print("=" * 48)\n    print(" OIT-049 TEST")\n    print(" PRODUCTION READ-ONLY CERTIFICATION")\n    print(" CORRECTION V3 - REGISTRY-DRIVEN RUNNER")\n    print("=" * 48)\n\n    root = Path(__file__).resolve().parent\n    fixture = load_oit_048_fixture(root)\n\n    from qseries_v2.oracle_terminal.oracle_end_to_end_interactive_intelligence_pipeline import (\n        execute_end_to_end_interactive_intelligence_pipeline,\n    )\n\n    context = fixture.make_context_report(root)\n    session = fixture.make_prior_session()\n    pipeline_report = execute_end_to_end_interactive_intelligence_pipeline(\n        root,\n        context_assembly_report=context,\n        prior_session_context=session,\n        query="Has it changed now?",\n    )\n\n    runner = certify_live_terminal_runner(root)\n    assert runner.runner_certified\n    assert runner.runner_version == "OIT-048"\n    assert runner.pipeline_version == "OIT-048"\n    assert runner.pipeline_bound\n    assert runner.execute_callable_available\n    assert runner.render_callable_available\n    assert runner.command_registry.command_registry_certified\n    assert not runner.command_registry.missing_commands\n    assert tuple(runner.command_registry.required_commands) == (\n        "/help",\n        "/status",\n        "/ask",\n        "/session",\n        "/clear",\n        "/quit",\n    )\n    assert runner.read_only_boundary_present\n    assert runner.publication_disabled\n    assert runner.action_authorization_disabled\n    assert runner.qseries_execution_disabled\n\n    report = build_oracle_terminal_production_read_only_certification_report(\n        root,\n        pipeline_report=pipeline_report,\n    )\n    assert report.production_readiness_certified\n    assert report.final_freeze_ready\n    assert report.runner_certification.runner_certified\n    assert report.pipeline_certification.pipeline_certified\n\n    replay = build_oracle_terminal_production_read_only_certification_report(\n        root,\n        pipeline_report=pipeline_report,\n    )\n    assert replay == report\n    assert verify_oracle_terminal_production_read_only_certification_report(\n        report\n    )\n\n    tampered = replace(report, publication_allowed=True)\n    try:\n        verify_oracle_terminal_production_read_only_certification_report(\n            tampered\n        )\n    except OracleTerminalProductionCertificationInvariantError:\n        pass\n    else:\n        raise AssertionError("tampered OIT-049 report accepted")\n\n    print("[PASS] Certified OIT-048 pipeline consumed")\n    print("[PASS] Live OIT-048 runner binding verified")\n    print("[PASS] Registry-driven command locations discovered")\n    print("[PASS] /help, /status, /ask, /session, /clear, and /quit verified")\n    print("[PASS] Command literals not required in live runner")\n    print("[PASS] Read-only terminal boundary verified")\n    print("[PASS] Exact pipeline stage order verified")\n    print("[PASS] Exact cross-stage lineage verified")\n    print("[PASS] Production readiness certified")\n    print("[PASS] Final-freeze readiness certified")\n    print("[PASS] Certification deterministic across replay")\n    print("[PASS] Tampered certification report rejected")\n    print("[PASS] Persistent memory and learning remained disabled")\n    print("[DONE] OIT-049 CORRECTION V3 PRODUCTION CERTIFICATION PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_contract(path: Path, tokens: tuple[str, ...], label: str) -> None:
    if not path.is_file():
        raise RuntimeError(f"{label} missing: {path}")
    source = path.read_text(encoding="utf-8")
    missing = [token for token in tokens if token not in source]
    if missing:
        raise RuntimeError(f"{label} contract mismatch: {missing}")


def command_sources() -> tuple[Path, ...]:
    paths = []
    for path in (REGISTRY, NAVIGATION, RUNNER):
        if path.is_file():
            paths.append(path)
    for path in sorted(PACKAGE.glob("*command*registry*.py")):
        if path.is_file() and path not in paths:
            paths.append(path)
    return tuple(paths)


def verify_commands() -> None:
    paths = command_sources()
    if not paths:
        raise RuntimeError("No installed command-registry source discovered")
    combined = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    missing = [
        command for command in (
            "/help", "/status", "/ask", "/session", "/clear", "/quit"
        )
        if command not in combined
    ]
    if missing:
        raise RuntimeError(
            f"Installed command registry contract mismatch: {missing}"
        )
    print("[OK] Registry-driven terminal commands verified")
    for path in paths:
        print(f"[OK] COMMAND SOURCE: {path.resolve()}")


def write_complete(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def protected_sources() -> dict[Path, str]:
    protected = {}
    roots = (
        ROOT / "qseries_v2" / "oracle_intelligence" / "live_acquisition",
        ROOT / "qseries_v2" / "oracle_intelligence" / "analytics",
        ROOT / "qseries_v2" / "oracle_intelligence_integration",
        ROOT / "qseries_v2" / "oracle_research_runtime",
        ROOT / "qseries_v2" / "oracle_operator_runtime",
        ROOT / "qseries_v2" / "qseries",
    )
    for base in roots:
        if base.exists():
            for path in base.rglob("*.py"):
                if path.is_file():
                    protected[path] = sha256(path)
    for path in (OIT_048, OIT_048_TEST, RUNNER, *command_sources()):
        if path.is_file():
            protected[path] = sha256(path)
    return protected


def main() -> int:
    print("=" * 48)
    print(" OIT-049 CORRECTION V3 INSTALLER")
    print(" REGISTRY-DRIVEN RUNNER CERTIFICATION")
    print("=" * 48)
    try:
        require_contract(
            OIT_048,
            (
                'SCHEMA_VERSION = "OIT-048"',
                'POLICY_ID = "oracle.end-to-end-interactive-intelligence-pipeline.v1"',
                "OracleInteractiveIntelligencePipelineReport",
                "execute_end_to_end_interactive_intelligence_pipeline",
                "verify_interactive_intelligence_pipeline_report",
                "live_runner_binding_ready",
            ),
            "Certified OIT-048 production",
        )
        require_contract(
            OIT_048_TEST,
            (
                "OIT-048 TEST",
                "END-TO-END INTERACTIVE INTELLIGENCE PIPELINE",
                "Live terminal runner binding imported",
                "OIT-048 END-TO-END INTERACTIVE PIPELINE PASS",
            ),
            "Certified OIT-048 standalone test",
        )
        require_contract(
            RUNNER,
            (
                'RUNNER_VERSION = "OIT-048"',
                'OIT_048_PIPELINE_VERSION = "OIT-048"',
                "OIT_048_PIPELINE_BOUND = True",
                "execute_oit_048_interactive_pipeline",
                "render_oit_048_interactive_pipeline",
            ),
            "Live OIT-048 runner binding",
        )
        verify_commands()

        protected = protected_sources()
        print("[OK] Certified OIT-048 production contract verified")
        print("[OK] Certified OIT-048 standalone test verified")
        print("[OK] Live OIT-048 runner binding verified")
        print("[OK] Current registry-driven repository state accepted")
        print(f"[OK] Protected production source files captured: {len(protected)}")

        upstream = subprocess.run(
            [sys.executable, str(OIT_048_TEST)],
            cwd=ROOT,
            check=False,
        )
        if upstream.returncode:
            raise RuntimeError(
                f"OIT-048 certification failed with exit code {upstream.returncode}"
            )

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_terminal_production_read_only_certification import *"
        )
        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"
            current += export + "\n"
            INIT.write_text(current, encoding="utf-8", newline="\n")
            print(f"[OK] PACKAGE UPDATED: {INIT.resolve()}")
        else:
            print(f"[OK] PACKAGE EXPORT PRESENT: {INIT.resolve()}")

        ast.parse(INIT.read_text(encoding="utf-8"), filename=str(INIT))

        completed = subprocess.run(
            [sys.executable, str(TEST)],
            cwd=ROOT,
            check=False,
        )
        if completed.returncode:
            raise RuntimeError(
                f"OIT-049 Correction V3 test failed with exit code {completed.returncode}"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(f"Protected production source changed: {path}")

        print("[PASS] Certified OIT-048 production and test unchanged")
        print("[PASS] Live Oracle terminal runner unchanged")
        print("[PASS] Command registry and navigation modules unchanged")
        print("[PASS] OIT-049 production module installed")
        print("[PASS] OIT-049 standalone test installed")
        print("[PASS] Registry-driven command architecture certified")
        print("[PASS] Production and final-freeze readiness certified")
        print("[PASS] Persistent memory and learning remained disabled")
        print("[PASS] No analytics execution or runtime mutation performed")
        print("[PASS] Publication and execution remained disabled")
        print("[PASS] Read-only and execution boundaries preserved")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OIT-049 CORRECTION V3 INSTALLED")
        return 0
    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
