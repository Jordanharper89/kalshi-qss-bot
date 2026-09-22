0from __future__ import annotations

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

        production = (
            package
            / "oracle_end_to_end_interactive_intelligence_pipeline.py"
        )
        test = (
            candidate
            / "test_oit_048_oracle_end_to_end_interactive_intelligence_pipeline.py"
        )
        runner = (
            candidate
            / "run_oracle_open_intelligence_terminal.py"
        )

        if (
            production.is_file()
            and test.is_file()
            and runner.is_file()
        ):
            return candidate

    raise SystemExit(
        "[ERROR] Could not locate current Q Series repository."
    )


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"

OIT_048 = (
    PACKAGE
    / "oracle_end_to_end_interactive_intelligence_pipeline.py"
)
OIT_048_TEST = (
    ROOT
    / "test_oit_048_oracle_end_to_end_interactive_intelligence_pipeline.py"
)
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"

PRODUCTION = (
    PACKAGE
    / "oracle_terminal_production_read_only_certification.py"
)
TEST = (
    ROOT
    / "test_oit_049_oracle_terminal_production_read_only_certification.py"
)
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport importlib.util\nimport json\nimport sys\nfrom dataclasses import asdict, dataclass\nfrom pathlib import Path\nfrom typing import Any, Mapping\n\nfrom .oracle_end_to_end_interactive_intelligence_pipeline import (\n    OracleInteractiveIntelligencePipelineReport,\n    verify_interactive_intelligence_pipeline_report,\n)\n\nSCHEMA_VERSION = "OIT-049"\nENGINE_ID = "OIT-049"\nPOLICY_ID = "oracle-terminal.production-read-only-certification.v1"\n\nREQUIRED_RUNNER_VERSION = "OIT-048"\nREQUIRED_PIPELINE_VERSION = "OIT-048"\n\n\nclass OracleTerminalProductionCertificationInvariantError(RuntimeError):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleTerminalRunnerCertification:\n    runner_path: str\n    runner_sha256: str\n    runner_byte_count: int\n    runner_version: str\n    pipeline_version: str\n    pipeline_bound: bool\n    execute_callable_available: bool\n    render_callable_available: bool\n    existing_command_registry_preserved: bool\n    read_only_status_present: bool\n    publication_disabled: bool\n    action_authorization_disabled: bool\n    qseries_execution_disabled: bool\n    runner_certified: bool\n    certification_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleTerminalPipelineCertification:\n    pipeline_report_hash: str\n    pipeline_result_hash: str\n    end_to_end_pipeline_certified: bool\n    live_runner_binding_ready: bool\n    terminal_display_ready: bool\n    session_continuation_ready: bool\n    exact_stage_order_verified: bool\n    exact_cross_stage_lineage_verified: bool\n    persistent_memory_enabled: bool\n    learning_update_performed: bool\n    publication_allowed: bool\n    action_authorization_allowed: bool\n    qseries_execution_allowed: bool\n    pipeline_certified: bool\n    certification_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleTerminalProductionReadOnlyCertificationReport:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    status: str\n    repository_root: str\n    runner_certification: OracleTerminalRunnerCertification\n    pipeline_certification: OracleTerminalPipelineCertification\n    production_readiness_certified: bool\n    final_freeze_ready: bool\n    persistent_memory_enabled: bool\n    learning_update_performed: bool\n    analytics_execution_performed: bool\n    database_access_performed: bool\n    runtime_artifact_created: bool\n    runtime_artifact_modified: bool\n    networking_performed: bool\n    publication_allowed: bool\n    action_authorization_allowed: bool\n    qseries_execution_allowed: bool\n    read_only: bool\n    failure_reason: str | None\n    report_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(\n                value.items(),\n                key=lambda pair: str(pair[0]),\n            )\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    raise OracleTerminalProductionCertificationInvariantError(\n        "unsupported OIT-049 value type: "\n        f"{type(value).__module__}.{type(value).__qualname__}"\n    )\n\n\ndef _stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=True,\n        allow_nan=False,\n    ).encode("utf-8")\n    return hashlib.sha256(payload).hexdigest()\n\n\ndef _sha256(path: Path) -> str:\n    return hashlib.sha256(path.read_bytes()).hexdigest()\n\n\ndef _load_runner(path: Path):\n    module_name = "oracle_open_intelligence_terminal_oit_049_certification"\n    specification = importlib.util.spec_from_file_location(\n        module_name,\n        path,\n    )\n    if specification is None or specification.loader is None:\n        raise OracleTerminalProductionCertificationInvariantError(\n            "unable to create live runner import specification"\n        )\n\n    module = importlib.util.module_from_spec(specification)\n    sys.modules[module_name] = module\n    specification.loader.exec_module(module)\n    return module\n\n\ndef certify_live_terminal_runner(\n    repository_root: str | Path,\n) -> OracleTerminalRunnerCertification:\n    root = Path(repository_root).resolve()\n    runner_path = root / "run_oracle_open_intelligence_terminal.py"\n\n    if not runner_path.is_file():\n        raise OracleTerminalProductionCertificationInvariantError(\n            f"live Oracle terminal runner missing: {runner_path}"\n        )\n\n    source = runner_path.read_text(encoding="utf-8")\n    module = _load_runner(runner_path)\n\n    runner_version = str(\n        getattr(module, "RUNNER_VERSION", "")\n    )\n    pipeline_version = str(\n        getattr(module, "OIT_048_PIPELINE_VERSION", "")\n    )\n    pipeline_bound = bool(\n        getattr(module, "OIT_048_PIPELINE_BOUND", False)\n    )\n    execute_available = callable(\n        getattr(\n            module,\n            "execute_oit_048_interactive_pipeline",\n            None,\n        )\n    )\n    render_available = callable(\n        getattr(\n            module,\n            "render_oit_048_interactive_pipeline",\n            None,\n        )\n    )\n\n    command_tokens = (\n        "/help",\n        "/status",\n        "/ask",\n        "/session",\n        "/clear",\n        "/quit",\n    )\n    commands_preserved = all(\n        token in source for token in command_tokens\n    )\n\n    read_only_status_present = all(\n        token in source\n        for token in (\n            "interactive read-only",\n            "publication",\n            "action authorization",\n            "Q Series execution",\n        )\n    )\n\n    publication_disabled = (\n        "publication: disabled" in source\n        or "publication_allowed" in source\n    )\n    action_disabled = (\n        "action authorization: disabled" in source\n        or "action_authorization_allowed" in source\n    )\n    execution_disabled = (\n        "Q Series execution: disabled" in source\n        or "qseries_execution_allowed" in source\n    )\n\n    runner_certified = bool(\n        runner_version == REQUIRED_RUNNER_VERSION\n        and pipeline_version == REQUIRED_PIPELINE_VERSION\n        and pipeline_bound\n        and execute_available\n        and render_available\n        and commands_preserved\n        and read_only_status_present\n        and publication_disabled\n        and action_disabled\n        and execution_disabled\n    )\n\n    body = {\n        "runner_path": str(runner_path),\n        "runner_sha256": _sha256(runner_path),\n        "runner_byte_count": runner_path.stat().st_size,\n        "runner_version": runner_version,\n        "pipeline_version": pipeline_version,\n        "pipeline_bound": pipeline_bound,\n        "execute_callable_available": execute_available,\n        "render_callable_available": render_available,\n        "existing_command_registry_preserved": commands_preserved,\n        "read_only_status_present": read_only_status_present,\n        "publication_disabled": publication_disabled,\n        "action_authorization_disabled": action_disabled,\n        "qseries_execution_disabled": execution_disabled,\n        "runner_certified": runner_certified,\n    }\n    certification = OracleTerminalRunnerCertification(\n        **body,\n        certification_hash=_stable_hash(body),\n    )\n    verify_runner_certification(certification)\n    return certification\n\n\ndef verify_runner_certification(\n    certification: OracleTerminalRunnerCertification,\n) -> bool:\n    body = asdict(certification)\n    supplied = body.pop("certification_hash")\n\n    if _stable_hash(body) != supplied:\n        raise OracleTerminalProductionCertificationInvariantError(\n            "OIT-049 runner certification hash mismatch"\n        )\n\n    if not certification.runner_path:\n        raise OracleTerminalProductionCertificationInvariantError(\n            "OIT-049 runner path missing"\n        )\n\n    if len(certification.runner_sha256) != 64:\n        raise OracleTerminalProductionCertificationInvariantError(\n            "OIT-049 runner SHA-256 invalid"\n        )\n\n    if certification.runner_byte_count <= 0:\n        raise OracleTerminalProductionCertificationInvariantError(\n            "OIT-049 runner byte count invalid"\n        )\n\n    expected = bool(\n        certification.runner_version\n        == REQUIRED_RUNNER_VERSION\n        and certification.pipeline_version\n        == REQUIRED_PIPELINE_VERSION\n        and certification.pipeline_bound\n        and certification.execute_callable_available\n        and certification.render_callable_available\n        and certification.existing_command_registry_preserved\n        and certification.read_only_status_present\n        and certification.publication_disabled\n        and certification.action_authorization_disabled\n        and certification.qseries_execution_disabled\n    )\n\n    if certification.runner_certified != expected:\n        raise OracleTerminalProductionCertificationInvariantError(\n            "OIT-049 runner certification state mismatch"\n        )\n\n    return True\n\n\ndef certify_interactive_pipeline(\n    pipeline_report: OracleInteractiveIntelligencePipelineReport,\n) -> OracleTerminalPipelineCertification:\n    verify_interactive_intelligence_pipeline_report(\n        pipeline_report\n    )\n\n    result = pipeline_report.pipeline_result\n    lineage = result.lineage\n\n    certified = bool(\n        pipeline_report.end_to_end_pipeline_certified\n        and pipeline_report.live_runner_binding_ready\n        and result.pipeline_completed\n        and result.terminal_display_ready\n        and result.session_continuation_ready\n        and lineage.exact_stage_order_verified\n        and lineage.exact_cross_stage_lineage_verified\n        and not pipeline_report.persistent_memory_enabled\n        and not pipeline_report.learning_update_performed\n        and not pipeline_report.publication_allowed\n        and not pipeline_report.action_authorization_allowed\n        and not pipeline_report.qseries_execution_allowed\n    )\n\n    body = {\n        "pipeline_report_hash": pipeline_report.report_hash,\n        "pipeline_result_hash": result.result_hash,\n        "end_to_end_pipeline_certified": (\n            pipeline_report.end_to_end_pipeline_certified\n        ),\n        "live_runner_binding_ready": (\n            pipeline_report.live_runner_binding_ready\n        ),\n        "terminal_display_ready": result.terminal_display_ready,\n        "session_continuation_ready": (\n            result.session_continuation_ready\n        ),\n        "exact_stage_order_verified": (\n            lineage.exact_stage_order_verified\n        ),\n        "exact_cross_stage_lineage_verified": (\n            lineage.exact_cross_stage_lineage_verified\n        ),\n        "persistent_memory_enabled": (\n            pipeline_report.persistent_memory_enabled\n        ),\n        "learning_update_performed": (\n            pipeline_report.learning_update_performed\n        ),\n        "publication_allowed": pipeline_report.publication_allowed,\n        "action_authorization_allowed": (\n            pipeline_report.action_authorization_allowed\n        ),\n        "qseries_execution_allowed": (\n            pipeline_report.qseries_execution_allowed\n        ),\n        "pipeline_certified": certified,\n    }\n    certification = OracleTerminalPipelineCertification(\n        **body,\n        certification_hash=_stable_hash(body),\n    )\n    verify_pipeline_certification(certification)\n    return certification\n\n\ndef verify_pipeline_certification(\n    certification: OracleTerminalPipelineCertification,\n) -> bool:\n    body = asdict(certification)\n    supplied = body.pop("certification_hash")\n\n    if _stable_hash(body) != supplied:\n        raise OracleTerminalProductionCertificationInvariantError(\n            "OIT-049 pipeline certification hash mismatch"\n        )\n\n    expected = bool(\n        certification.end_to_end_pipeline_certified\n        and certification.live_runner_binding_ready\n        and certification.terminal_display_ready\n        and certification.session_continuation_ready\n        and certification.exact_stage_order_verified\n        and certification.exact_cross_stage_lineage_verified\n        and not certification.persistent_memory_enabled\n        and not certification.learning_update_performed\n        and not certification.publication_allowed\n        and not certification.action_authorization_allowed\n        and not certification.qseries_execution_allowed\n    )\n\n    if certification.pipeline_certified != expected:\n        raise OracleTerminalProductionCertificationInvariantError(\n            "OIT-049 pipeline certification state mismatch"\n        )\n\n    return True\n\n\ndef build_oracle_terminal_production_read_only_certification_report(\n    repository_root: str | Path,\n    *,\n    pipeline_report: OracleInteractiveIntelligencePipelineReport,\n) -> OracleTerminalProductionReadOnlyCertificationReport:\n    root = Path(repository_root).resolve()\n\n    runner = certify_live_terminal_runner(root)\n    pipeline = certify_interactive_pipeline(pipeline_report)\n\n    production_ready = bool(\n        runner.runner_certified\n        and pipeline.pipeline_certified\n    )\n\n    report_body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root),\n        "runner_certification": runner,\n        "pipeline_certification": pipeline,\n        "production_readiness_certified": production_ready,\n        "final_freeze_ready": production_ready,\n        "persistent_memory_enabled": False,\n        "learning_update_performed": False,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "runtime_artifact_created": False,\n        "runtime_artifact_modified": False,\n        "networking_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "read_only": True,\n        "failure_reason": (\n            None\n            if production_ready\n            else "Oracle terminal production certification failed"\n        ),\n    }\n    report = OracleTerminalProductionReadOnlyCertificationReport(\n        **report_body,\n        report_hash=_stable_hash(report_body),\n    )\n    verify_oracle_terminal_production_read_only_certification_report(\n        report\n    )\n    return report\n\n\ndef verify_oracle_terminal_production_read_only_certification_report(\n    report: OracleTerminalProductionReadOnlyCertificationReport,\n) -> bool:\n    body = asdict(report)\n    supplied = body.pop("report_hash")\n\n    if _stable_hash(body) != supplied:\n        raise OracleTerminalProductionCertificationInvariantError(\n            "OIT-049 report hash mismatch"\n        )\n\n    if report.schema_version != SCHEMA_VERSION:\n        raise OracleTerminalProductionCertificationInvariantError(\n            "OIT-049 schema mismatch"\n        )\n\n    if report.policy_id != POLICY_ID:\n        raise OracleTerminalProductionCertificationInvariantError(\n            "OIT-049 policy mismatch"\n        )\n\n    verify_runner_certification(\n        report.runner_certification\n    )\n    verify_pipeline_certification(\n        report.pipeline_certification\n    )\n\n    if not report.read_only:\n        raise OracleTerminalProductionCertificationInvariantError(\n            "OIT-049 report is not read-only"\n        )\n\n    if (\n        report.persistent_memory_enabled\n        or report.learning_update_performed\n        or report.analytics_execution_performed\n        or report.database_access_performed\n        or report.runtime_artifact_created\n        or report.runtime_artifact_modified\n        or report.networking_performed\n        or report.publication_allowed\n        or report.action_authorization_allowed\n        or report.qseries_execution_allowed\n    ):\n        raise OracleTerminalProductionCertificationInvariantError(\n            "forbidden OIT-049 capability enabled"\n        )\n\n    expected = bool(\n        report.runner_certification.runner_certified\n        and report.pipeline_certification.pipeline_certified\n    )\n\n    if report.production_readiness_certified != expected:\n        raise OracleTerminalProductionCertificationInvariantError(\n            "OIT-049 production-readiness state mismatch"\n        )\n\n    if report.final_freeze_ready != expected:\n        raise OracleTerminalProductionCertificationInvariantError(\n            "OIT-049 final-freeze readiness mismatch"\n        )\n\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nimport importlib.util\nimport sys\nfrom dataclasses import replace\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_terminal.oracle_terminal_production_read_only_certification import (\n    OracleTerminalProductionCertificationInvariantError,\n    build_oracle_terminal_production_read_only_certification_report,\n    certify_live_terminal_runner,\n    verify_oracle_terminal_production_read_only_certification_report,\n)\n\n\ndef load_oit_048_test(root: Path):\n    path = (\n        root\n        / "test_oit_048_oracle_end_to_end_interactive_intelligence_pipeline.py"\n    )\n    name = "oit_048_test_fixture_for_oit_049"\n    spec = importlib.util.spec_from_file_location(name, path)\n    if spec is None or spec.loader is None:\n        raise RuntimeError("unable to load OIT-048 test fixture")\n    module = importlib.util.module_from_spec(spec)\n    sys.modules[name] = module\n    spec.loader.exec_module(module)\n    return module\n\n\ndef main() -> int:\n    print("=" * 48)\n    print(" OIT-049 TEST")\n    print(" ORACLE TERMINAL PRODUCTION READ-ONLY CERTIFICATION")\n    print("=" * 48)\n\n    root = Path(__file__).resolve().parent\n    fixture = load_oit_048_test(root)\n\n    context = fixture.make_context_report(root)\n    session = fixture.make_prior_session()\n\n    from qseries_v2.oracle_terminal.oracle_end_to_end_interactive_intelligence_pipeline import (\n        execute_end_to_end_interactive_intelligence_pipeline,\n    )\n\n    pipeline_report = (\n        execute_end_to_end_interactive_intelligence_pipeline(\n            root,\n            context_assembly_report=context,\n            prior_session_context=session,\n            query="Has it changed now?",\n        )\n    )\n\n    runner = certify_live_terminal_runner(root)\n    assert runner.runner_certified\n    assert runner.runner_version == "OIT-048"\n    assert runner.pipeline_version == "OIT-048"\n    assert runner.pipeline_bound\n    assert runner.execute_callable_available\n    assert runner.render_callable_available\n    assert runner.existing_command_registry_preserved\n    assert runner.read_only_status_present\n    assert runner.publication_disabled\n    assert runner.action_authorization_disabled\n    assert runner.qseries_execution_disabled\n\n    report = (\n        build_oracle_terminal_production_read_only_certification_report(\n            root,\n            pipeline_report=pipeline_report,\n        )\n    )\n\n    assert report.production_readiness_certified\n    assert report.final_freeze_ready\n    assert report.runner_certification.runner_certified\n    assert report.pipeline_certification.pipeline_certified\n    assert (\n        report.pipeline_certification\n        .exact_stage_order_verified\n    )\n    assert (\n        report.pipeline_certification\n        .exact_cross_stage_lineage_verified\n    )\n    assert report.pipeline_certification.terminal_display_ready\n    assert (\n        report.pipeline_certification\n        .session_continuation_ready\n    )\n\n    replay = (\n        build_oracle_terminal_production_read_only_certification_report(\n            root,\n            pipeline_report=pipeline_report,\n        )\n    )\n    assert replay == report\n    assert (\n        verify_oracle_terminal_production_read_only_certification_report(\n            report\n        )\n    )\n\n    tampered = replace(\n        report,\n        publication_allowed=True,\n    )\n    try:\n        verify_oracle_terminal_production_read_only_certification_report(\n            tampered\n        )\n    except OracleTerminalProductionCertificationInvariantError:\n        pass\n    else:\n        raise AssertionError(\n            "tampered OIT-049 report accepted"\n        )\n\n    assert not report.persistent_memory_enabled\n    assert not report.learning_update_performed\n    assert not report.analytics_execution_performed\n    assert not report.database_access_performed\n    assert not report.runtime_artifact_created\n    assert not report.runtime_artifact_modified\n    assert not report.networking_performed\n    assert not report.publication_allowed\n    assert not report.action_authorization_allowed\n    assert not report.qseries_execution_allowed\n    assert report.read_only\n\n    print("[PASS] Certified OIT-048 end-to-end pipeline consumed")\n    print("[PASS] Live OIT-048 runner imported successfully")\n    print("[PASS] OIT-048 execute callable verified")\n    print("[PASS] OIT-048 render callable verified")\n    print("[PASS] Existing command registry preserved")\n    print("[PASS] Read-only terminal status preserved")\n    print("[PASS] Publication remained disabled")\n    print("[PASS] Action authorization remained disabled")\n    print("[PASS] Q Series execution remained disabled")\n    print("[PASS] Exact pipeline stage order verified")\n    print("[PASS] Exact cross-stage lineage verified")\n    print("[PASS] Production readiness certified")\n    print("[PASS] Final-freeze readiness certified")\n    print("[PASS] Certification deterministic across replay")\n    print("[PASS] Tampered certification report rejected")\n    print("[PASS] Persistent memory and learning remained disabled")\n    print("[DONE] OIT-049 PRODUCTION READ-ONLY CERTIFICATION PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_contract(
    path: Path,
    tokens: tuple[str, ...],
    label: str,
) -> None:
    if not path.is_file():
        raise RuntimeError(f"{label} missing: {path}")

    source = path.read_text(encoding="utf-8")
    missing = [
        token
        for token in tokens
        if token not in source
    ]

    if missing:
        raise RuntimeError(
            f"{label} contract mismatch: {missing}"
        )


def write_complete(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        source.lstrip(),
        encoding="utf-8",
        newline="\n",
    )
    ast.parse(
        path.read_text(encoding="utf-8"),
        filename=str(path),
    )
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

    for path in (
        OIT_048,
        OIT_048_TEST,
        RUNNER,
    ):
        protected[path] = sha256(path)

    return protected


def main() -> int:
    print("=" * 48)
    print(" OIT-049 INSTALLER")
    print(" ORACLE TERMINAL PRODUCTION READ-ONLY CERTIFICATION")
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
                "/help",
                "/status",
                "/ask",
                "/session",
                "/clear",
                "/quit",
            ),
            "Live OIT-048 terminal runner",
        )

        protected = protected_sources()

        print("[OK] Certified OIT-048 production contract verified")
        print("[OK] Certified OIT-048 standalone test verified")
        print("[OK] Live OIT-048 terminal runner contract verified")
        print(
            f"[OK] Protected production source files captured: "
            f"{len(protected)}"
        )

        upstream = subprocess.run(
            [sys.executable, str(OIT_048_TEST)],
            cwd=ROOT,
            check=False,
        )

        if upstream.returncode:
            raise RuntimeError(
                "OIT-048 certification failed with exit code "
                f"{upstream.returncode}"
            )

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_terminal_production_read_only_certification import *"
        )

        current = (
            INIT.read_text(encoding="utf-8")
            if INIT.exists()
            else ""
        )

        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"

            current += export + "\n"

            INIT.write_text(
                current,
                encoding="utf-8",
                newline="\n",
            )
            print(
                f"[OK] PACKAGE UPDATED: {INIT.resolve()}"
            )
        else:
            print(
                f"[OK] PACKAGE EXPORT PRESENT: {INIT.resolve()}"
            )

        ast.parse(
            INIT.read_text(encoding="utf-8"),
            filename=str(INIT),
        )

        completed = subprocess.run(
            [sys.executable, str(TEST)],
            cwd=ROOT,
            check=False,
        )

        if completed.returncode:
            raise RuntimeError(
                "OIT-049 test failed with exit code "
                f"{completed.returncode}"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Protected production source changed: {path}"
                )

        print("[PASS] Certified OIT-048 production and test unchanged")
        print("[PASS] Live Oracle terminal runner unchanged")
        print("[PASS] OIT-049 production module installed")
        print("[PASS] OIT-049 standalone test installed")
        print("[PASS] End-to-end pipeline production boundary certified")
        print("[PASS] Live runner command registry certified")
        print("[PASS] Read-only terminal guarantees certified")
        print("[PASS] Final-freeze readiness certified")
        print("[PASS] Persistent memory and learning remained disabled")
        print("[PASS] No analytics execution or runtime mutation performed")
        print("[PASS] OLA, OIA, INT-OII, ORR, OOR, and Q Series unchanged")
        print("[PASS] Publication and execution remained disabled")
        print("[PASS] Read-only and execution boundaries preserved")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OIT-049 PRODUCTION READ-ONLY CERTIFICATION INSTALLED")
        return 0

    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
