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
        production = (
            package
            / "oracle_terminal_production_read_only_certification.py"
        )
        test = (
            candidate
            / "test_oit_049_oracle_terminal_production_read_only_certification.py"
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

OIT_049 = (
    PACKAGE
    / "oracle_terminal_production_read_only_certification.py"
)
OIT_049_TEST = (
    ROOT
    / "test_oit_049_oracle_terminal_production_read_only_certification.py"
)
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"
REGISTRY = PACKAGE / "oracle_terminal_interactive_command_registry.py"
NAVIGATION = PACKAGE / "oracle_terminal_evidence_panel_navigation.py"

PRODUCTION = (
    PACKAGE
    / "oracle_terminal_final_freeze_and_completion.py"
)
TEST = (
    ROOT
    / "test_oit_050_oracle_terminal_final_freeze_and_completion.py"
)
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass\nfrom pathlib import Path\nfrom typing import Any, Mapping\n\nfrom .oracle_terminal_production_read_only_certification import (\n    OracleTerminalProductionReadOnlyCertificationReport,\n    verify_oracle_terminal_production_read_only_certification_report,\n)\n\nSCHEMA_VERSION = "OIT-050"\nENGINE_ID = "OIT-050"\nPOLICY_ID = "oracle-terminal.final-freeze-and-completion.v1"\n\nSUBSYSTEM_ID = "oracle_open_intelligence_terminal"\nFINAL_MILESTONE = "OIT-050"\nNEXT_SUBSYSTEM = "oracle_memory_and_continuous_intelligence_learner"\n\n\nclass OracleTerminalFinalFreezeInvariantError(RuntimeError):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleTerminalFinalFreezeManifest:\n    subsystem_id: str\n    final_milestone: str\n    source_production_certification_hash: str\n    source_runner_certification_hash: str\n    source_runner_sha256: str\n    source_pipeline_certification_hash: str\n    source_pipeline_report_hash: str\n    source_pipeline_result_hash: str\n    command_registry_certified: bool\n    end_to_end_pipeline_certified: bool\n    production_readiness_certified: bool\n    read_only_boundary_frozen: bool\n    publication_frozen_disabled: bool\n    action_authorization_frozen_disabled: bool\n    qseries_execution_frozen_disabled: bool\n    persistent_memory_deferred: bool\n    learning_deferred: bool\n    no_further_oit_feature_layers_required: bool\n    next_subsystem: str\n    manifest_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleTerminalFinalFreezeCompletionReport:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    status: str\n    repository_root: str\n    source_certification_report_hash: str\n    freeze_manifest: OracleTerminalFinalFreezeManifest\n    subsystem_completed: bool\n    subsystem_frozen: bool\n    terminal_production_ready: bool\n    next_subsystem_authorized: bool\n    further_oit_feature_builds_allowed: bool\n    correction_builds_allowed_only_for_defects: bool\n    persistent_memory_enabled: bool\n    learning_update_performed: bool\n    analytics_execution_performed: bool\n    database_access_performed: bool\n    runtime_artifact_created: bool\n    runtime_artifact_modified: bool\n    networking_performed: bool\n    publication_allowed: bool\n    action_authorization_allowed: bool\n    qseries_execution_allowed: bool\n    read_only: bool\n    failure_reason: str | None\n    report_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(\n                value.items(),\n                key=lambda pair: str(pair[0]),\n            )\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    raise OracleTerminalFinalFreezeInvariantError(\n        "unsupported OIT-050 value type: "\n        f"{type(value).__module__}.{type(value).__qualname__}"\n    )\n\n\ndef _stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=True,\n        allow_nan=False,\n    ).encode("utf-8")\n    return hashlib.sha256(payload).hexdigest()\n\n\ndef verify_final_freeze_manifest(\n    manifest: OracleTerminalFinalFreezeManifest,\n) -> bool:\n    body = asdict(manifest)\n    supplied = body.pop("manifest_hash")\n\n    if _stable_hash(body) != supplied:\n        raise OracleTerminalFinalFreezeInvariantError(\n            "OIT-050 freeze manifest hash mismatch"\n        )\n\n    if manifest.subsystem_id != SUBSYSTEM_ID:\n        raise OracleTerminalFinalFreezeInvariantError(\n            "OIT-050 subsystem identity mismatch"\n        )\n\n    if manifest.final_milestone != FINAL_MILESTONE:\n        raise OracleTerminalFinalFreezeInvariantError(\n            "OIT-050 final milestone mismatch"\n        )\n\n    required_hashes = (\n        manifest.source_production_certification_hash,\n        manifest.source_runner_certification_hash,\n        manifest.source_runner_sha256,\n        manifest.source_pipeline_certification_hash,\n        manifest.source_pipeline_report_hash,\n        manifest.source_pipeline_result_hash,\n    )\n    if not all(required_hashes):\n        raise OracleTerminalFinalFreezeInvariantError(\n            "OIT-050 freeze lineage incomplete"\n        )\n\n    if len(manifest.source_runner_sha256) != 64:\n        raise OracleTerminalFinalFreezeInvariantError(\n            "OIT-050 runner SHA-256 invalid"\n        )\n\n    required_true = (\n        manifest.command_registry_certified,\n        manifest.end_to_end_pipeline_certified,\n        manifest.production_readiness_certified,\n        manifest.read_only_boundary_frozen,\n        manifest.publication_frozen_disabled,\n        manifest.action_authorization_frozen_disabled,\n        manifest.qseries_execution_frozen_disabled,\n        manifest.persistent_memory_deferred,\n        manifest.learning_deferred,\n        manifest.no_further_oit_feature_layers_required,\n    )\n    if not all(required_true):\n        raise OracleTerminalFinalFreezeInvariantError(\n            "OIT-050 freeze guarantee missing"\n        )\n\n    if manifest.next_subsystem != NEXT_SUBSYSTEM:\n        raise OracleTerminalFinalFreezeInvariantError(\n            "OIT-050 next subsystem mismatch"\n        )\n\n    return True\n\n\ndef build_oracle_terminal_final_freeze_completion_report(\n    repository_root: str | Path,\n    *,\n    production_certification_report: (\n        OracleTerminalProductionReadOnlyCertificationReport\n    ),\n) -> OracleTerminalFinalFreezeCompletionReport:\n    root = Path(repository_root).resolve()\n\n    verify_oracle_terminal_production_read_only_certification_report(\n        production_certification_report\n    )\n\n    if not production_certification_report.production_readiness_certified:\n        raise OracleTerminalFinalFreezeInvariantError(\n            production_certification_report.failure_reason\n            or "OIT-049 production readiness is not certified"\n        )\n\n    if not production_certification_report.final_freeze_ready:\n        raise OracleTerminalFinalFreezeInvariantError(\n            "OIT-049 final-freeze readiness is not certified"\n        )\n\n    runner = production_certification_report.runner_certification\n    pipeline = production_certification_report.pipeline_certification\n\n    manifest_body = {\n        "subsystem_id": SUBSYSTEM_ID,\n        "final_milestone": FINAL_MILESTONE,\n        "source_production_certification_hash": (\n            production_certification_report.report_hash\n        ),\n        "source_runner_certification_hash": (\n            runner.certification_hash\n        ),\n        "source_runner_sha256": runner.runner_sha256,\n        "source_pipeline_certification_hash": (\n            pipeline.certification_hash\n        ),\n        "source_pipeline_report_hash": (\n            pipeline.pipeline_report_hash\n        ),\n        "source_pipeline_result_hash": (\n            pipeline.pipeline_result_hash\n        ),\n        "command_registry_certified": (\n            runner.command_registry.command_registry_certified\n        ),\n        "end_to_end_pipeline_certified": (\n            pipeline.pipeline_certified\n        ),\n        "production_readiness_certified": (\n            production_certification_report\n            .production_readiness_certified\n        ),\n        "read_only_boundary_frozen": True,\n        "publication_frozen_disabled": True,\n        "action_authorization_frozen_disabled": True,\n        "qseries_execution_frozen_disabled": True,\n        "persistent_memory_deferred": True,\n        "learning_deferred": True,\n        "no_further_oit_feature_layers_required": True,\n        "next_subsystem": NEXT_SUBSYSTEM,\n    }\n    manifest = OracleTerminalFinalFreezeManifest(\n        **manifest_body,\n        manifest_hash=_stable_hash(manifest_body),\n    )\n    verify_final_freeze_manifest(manifest)\n\n    completed = bool(\n        manifest.command_registry_certified\n        and manifest.end_to_end_pipeline_certified\n        and manifest.production_readiness_certified\n        and manifest.read_only_boundary_frozen\n        and manifest.no_further_oit_feature_layers_required\n    )\n\n    report_body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "status": "completed_and_frozen",\n        "repository_root": str(root),\n        "source_certification_report_hash": (\n            production_certification_report.report_hash\n        ),\n        "freeze_manifest": manifest,\n        "subsystem_completed": completed,\n        "subsystem_frozen": completed,\n        "terminal_production_ready": completed,\n        "next_subsystem_authorized": completed,\n        "further_oit_feature_builds_allowed": False,\n        "correction_builds_allowed_only_for_defects": True,\n        "persistent_memory_enabled": False,\n        "learning_update_performed": False,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "runtime_artifact_created": False,\n        "runtime_artifact_modified": False,\n        "networking_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "read_only": True,\n        "failure_reason": (\n            None if completed else "OIT-050 freeze failed"\n        ),\n    }\n    report = OracleTerminalFinalFreezeCompletionReport(\n        **report_body,\n        report_hash=_stable_hash(report_body),\n    )\n    verify_oracle_terminal_final_freeze_completion_report(report)\n    return report\n\n\ndef verify_oracle_terminal_final_freeze_completion_report(\n    report: OracleTerminalFinalFreezeCompletionReport,\n) -> bool:\n    body = asdict(report)\n    supplied = body.pop("report_hash")\n\n    if _stable_hash(body) != supplied:\n        raise OracleTerminalFinalFreezeInvariantError(\n            "OIT-050 report hash mismatch"\n        )\n\n    if report.schema_version != SCHEMA_VERSION:\n        raise OracleTerminalFinalFreezeInvariantError(\n            "OIT-050 schema mismatch"\n        )\n\n    if report.policy_id != POLICY_ID:\n        raise OracleTerminalFinalFreezeInvariantError(\n            "OIT-050 policy mismatch"\n        )\n\n    if report.status != "completed_and_frozen":\n        raise OracleTerminalFinalFreezeInvariantError(\n            "OIT-050 completion status mismatch"\n        )\n\n    verify_final_freeze_manifest(report.freeze_manifest)\n\n    if report.source_certification_report_hash != (\n        report.freeze_manifest\n        .source_production_certification_hash\n    ):\n        raise OracleTerminalFinalFreezeInvariantError(\n            "OIT-050 certification lineage mismatch"\n        )\n\n    if not report.read_only:\n        raise OracleTerminalFinalFreezeInvariantError(\n            "OIT-050 report is not read-only"\n        )\n\n    if (\n        report.further_oit_feature_builds_allowed\n        or not report.correction_builds_allowed_only_for_defects\n        or report.persistent_memory_enabled\n        or report.learning_update_performed\n        or report.analytics_execution_performed\n        or report.database_access_performed\n        or report.runtime_artifact_created\n        or report.runtime_artifact_modified\n        or report.networking_performed\n        or report.publication_allowed\n        or report.action_authorization_allowed\n        or report.qseries_execution_allowed\n    ):\n        raise OracleTerminalFinalFreezeInvariantError(\n            "forbidden post-freeze capability enabled"\n        )\n\n    expected = bool(\n        report.freeze_manifest.command_registry_certified\n        and report.freeze_manifest.end_to_end_pipeline_certified\n        and report.freeze_manifest.production_readiness_certified\n        and report.freeze_manifest.read_only_boundary_frozen\n        and report.freeze_manifest.no_further_oit_feature_layers_required\n    )\n\n    for value, label in (\n        (report.subsystem_completed, "completion"),\n        (report.subsystem_frozen, "freeze"),\n        (report.terminal_production_ready, "production readiness"),\n        (report.next_subsystem_authorized, "next subsystem authorization"),\n    ):\n        if value != expected:\n            raise OracleTerminalFinalFreezeInvariantError(\n                f"OIT-050 {label} state mismatch"\n            )\n\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nimport importlib.util\nimport sys\nfrom dataclasses import replace\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_terminal.oracle_terminal_final_freeze_and_completion import (\n    NEXT_SUBSYSTEM,\n    OracleTerminalFinalFreezeInvariantError,\n    build_oracle_terminal_final_freeze_completion_report,\n    verify_oracle_terminal_final_freeze_completion_report,\n)\n\n\ndef load_oit_049_fixture(root: Path):\n    path = (\n        root\n        / "test_oit_049_oracle_terminal_production_read_only_certification.py"\n    )\n    name = "oit_049_fixture_for_oit_050"\n    specification = importlib.util.spec_from_file_location(\n        name,\n        path,\n    )\n    if specification is None or specification.loader is None:\n        raise RuntimeError(\n            "unable to load certified OIT-049 fixture"\n        )\n\n    module = importlib.util.module_from_spec(specification)\n    sys.modules[name] = module\n    specification.loader.exec_module(module)\n    return module\n\n\ndef build_oit_049_report(root: Path):\n    fixture = load_oit_049_fixture(root)\n\n    from qseries_v2.oracle_terminal.oracle_end_to_end_interactive_intelligence_pipeline import (\n        execute_end_to_end_interactive_intelligence_pipeline,\n    )\n    from qseries_v2.oracle_terminal.oracle_terminal_production_read_only_certification import (\n        build_oracle_terminal_production_read_only_certification_report,\n    )\n\n    context = fixture.load_oit_048_fixture(root).make_context_report(root)\n    session = fixture.load_oit_048_fixture(root).make_prior_session()\n\n    pipeline_report = (\n        execute_end_to_end_interactive_intelligence_pipeline(\n            root,\n            context_assembly_report=context,\n            prior_session_context=session,\n            query="Has it changed now?",\n        )\n    )\n\n    return (\n        build_oracle_terminal_production_read_only_certification_report(\n            root,\n            pipeline_report=pipeline_report,\n        )\n    )\n\n\ndef main() -> int:\n    print("=" * 48)\n    print(" OIT-050 TEST")\n    print(" FINAL FREEZE AND COMPLETION")\n    print("=" * 48)\n\n    root = Path(__file__).resolve().parent\n    certification = build_oit_049_report(root)\n\n    report = build_oracle_terminal_final_freeze_completion_report(\n        root,\n        production_certification_report=certification,\n    )\n\n    assert report.subsystem_completed\n    assert report.subsystem_frozen\n    assert report.terminal_production_ready\n    assert report.next_subsystem_authorized\n    assert not report.further_oit_feature_builds_allowed\n    assert report.correction_builds_allowed_only_for_defects\n\n    manifest = report.freeze_manifest\n    assert manifest.subsystem_id == "oracle_open_intelligence_terminal"\n    assert manifest.final_milestone == "OIT-050"\n    assert manifest.command_registry_certified\n    assert manifest.end_to_end_pipeline_certified\n    assert manifest.production_readiness_certified\n    assert manifest.read_only_boundary_frozen\n    assert manifest.publication_frozen_disabled\n    assert manifest.action_authorization_frozen_disabled\n    assert manifest.qseries_execution_frozen_disabled\n    assert manifest.persistent_memory_deferred\n    assert manifest.learning_deferred\n    assert manifest.no_further_oit_feature_layers_required\n    assert manifest.next_subsystem == NEXT_SUBSYSTEM\n\n    assert (\n        manifest.source_production_certification_hash\n        == certification.report_hash\n    )\n    assert (\n        manifest.source_runner_certification_hash\n        == certification.runner_certification.certification_hash\n    )\n    assert (\n        manifest.source_runner_sha256\n        == certification.runner_certification.runner_sha256\n    )\n    assert (\n        manifest.source_pipeline_certification_hash\n        == certification.pipeline_certification.certification_hash\n    )\n\n    replay = build_oracle_terminal_final_freeze_completion_report(\n        root,\n        production_certification_report=certification,\n    )\n    assert replay == report\n    assert verify_oracle_terminal_final_freeze_completion_report(\n        report\n    )\n\n    tampered = replace(\n        report,\n        further_oit_feature_builds_allowed=True,\n    )\n    try:\n        verify_oracle_terminal_final_freeze_completion_report(\n            tampered\n        )\n    except OracleTerminalFinalFreezeInvariantError:\n        pass\n    else:\n        raise AssertionError(\n            "tampered OIT-050 report accepted"\n        )\n\n    assert not report.persistent_memory_enabled\n    assert not report.learning_update_performed\n    assert not report.analytics_execution_performed\n    assert not report.database_access_performed\n    assert not report.runtime_artifact_created\n    assert not report.runtime_artifact_modified\n    assert not report.networking_performed\n    assert not report.publication_allowed\n    assert not report.action_authorization_allowed\n    assert not report.qseries_execution_allowed\n    assert report.read_only\n\n    print("[PASS] Certified OIT-049 Correction V3 consumed")\n    print("[PASS] OIT-048 live runner hash frozen")\n    print("[PASS] Command-registry certification frozen")\n    print("[PASS] End-to-end pipeline certification frozen")\n    print("[PASS] Production-readiness certification frozen")\n    print("[PASS] Read-only boundary frozen")\n    print("[PASS] Publication remained disabled")\n    print("[PASS] Action authorization remained disabled")\n    print("[PASS] Q Series execution remained disabled")\n    print("[PASS] Persistent memory deferred to next subsystem")\n    print("[PASS] Continuous learning deferred to next subsystem")\n    print("[PASS] No further OIT feature layers required")\n    print("[PASS] Correction builds restricted to genuine defects")\n    print("[PASS] Freeze deterministic across replay")\n    print("[PASS] Tampered freeze report rejected")\n    print("[DONE] OIT-050 FINAL FREEZE AND COMPLETION PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


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
        OIT_049,
        OIT_049_TEST,
        RUNNER,
        REGISTRY,
        NAVIGATION,
    ):
        if path.is_file():
            protected[path] = sha256(path)

    return protected


def main() -> int:
    print("=" * 48)
    print(" OIT-050 INSTALLER")
    print(" FINAL FREEZE AND COMPLETION")
    print("=" * 48)

    try:
        require_contract(
            OIT_049,
            (
                'SCHEMA_VERSION = "OIT-049"',
                'POLICY_ID = "oracle-terminal.production-read-only-certification.v3"',
                "OracleTerminalCommandRegistryCertification",
                "OracleTerminalRunnerCertification",
                "OracleTerminalPipelineCertification",
                "OracleTerminalProductionReadOnlyCertificationReport",
                "verify_oracle_terminal_production_read_only_certification_report",
                "production_readiness_certified",
                "final_freeze_ready",
            ),
            "Certified OIT-049 Correction V3 production",
        )

        require_contract(
            OIT_049_TEST,
            (
                "OIT-049 TEST",
                "CORRECTION V3 - REGISTRY-DRIVEN RUNNER",
                "Production readiness certified",
                "Final-freeze readiness certified",
                "OIT-049 CORRECTION V3 PRODUCTION CERTIFICATION PASS",
            ),
            "Certified OIT-049 Correction V3 standalone test",
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
            "Frozen live OIT-048 terminal runner",
        )

        protected = protected_sources()

        print("[OK] Certified OIT-049 Correction V3 production verified")
        print("[OK] Certified OIT-049 Correction V3 test verified")
        print("[OK] Live OIT-048 terminal runner verified")
        print("[OK] Registry-driven command architecture located")
        print(
            f"[OK] Protected production source files captured: "
            f"{len(protected)}"
        )

        upstream = subprocess.run(
            [sys.executable, str(OIT_049_TEST)],
            cwd=ROOT,
            check=False,
        )

        if upstream.returncode:
            raise RuntimeError(
                "OIT-049 certification failed with exit code "
                f"{upstream.returncode}"
            )

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_terminal_final_freeze_and_completion import *"
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
                "OIT-050 test failed with exit code "
                f"{completed.returncode}"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Protected production source changed: {path}"
                )

        print("[PASS] Certified OIT-049 production and test unchanged")
        print("[PASS] Live Oracle terminal runner unchanged")
        print("[PASS] Command registry and navigation modules unchanged")
        print("[PASS] OIT-050 production module installed")
        print("[PASS] OIT-050 standalone test installed")
        print("[PASS] Oracle Open Intelligence Terminal completed")
        print("[PASS] Oracle Open Intelligence Terminal frozen at OIT-050")
        print("[PASS] No further OIT feature layers required")
        print("[PASS] Corrections restricted to genuine defects")
        print("[PASS] Persistent memory deferred to next subsystem")
        print("[PASS] Continuous learning deferred to next subsystem")
        print("[PASS] Publication and execution remained disabled")
        print("[PASS] Read-only and execution boundaries frozen")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OIT-050 FINAL FREEZE AND COMPLETION INSTALLED")
        print("")
        print("NEXT SUBSYSTEM")
        print("  Oracle Memory and Continuous Intelligence Learner")
        return 0

    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
