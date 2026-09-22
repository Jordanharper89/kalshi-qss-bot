from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_terminal.oracle_terminal_final_freeze_and_completion import (
    NEXT_SUBSYSTEM,
    OracleTerminalFinalFreezeInvariantError,
    build_oracle_terminal_final_freeze_completion_report,
    verify_oracle_terminal_final_freeze_completion_report,
)


def load_oit_049_fixture(root: Path):
    path = (
        root
        / "test_oit_049_oracle_terminal_production_read_only_certification.py"
    )
    name = "oit_049_fixture_for_oit_050"
    specification = importlib.util.spec_from_file_location(
        name,
        path,
    )
    if specification is None or specification.loader is None:
        raise RuntimeError(
            "unable to load certified OIT-049 fixture"
        )

    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def build_oit_049_report(root: Path):
    fixture = load_oit_049_fixture(root)

    from qseries_v2.oracle_terminal.oracle_end_to_end_interactive_intelligence_pipeline import (
        execute_end_to_end_interactive_intelligence_pipeline,
    )
    from qseries_v2.oracle_terminal.oracle_terminal_production_read_only_certification import (
        build_oracle_terminal_production_read_only_certification_report,
    )

    context = fixture.load_oit_048_fixture(root).make_context_report(root)
    session = fixture.load_oit_048_fixture(root).make_prior_session()

    pipeline_report = (
        execute_end_to_end_interactive_intelligence_pipeline(
            root,
            context_assembly_report=context,
            prior_session_context=session,
            query="Has it changed now?",
        )
    )

    return (
        build_oracle_terminal_production_read_only_certification_report(
            root,
            pipeline_report=pipeline_report,
        )
    )


def main() -> int:
    print("=" * 48)
    print(" OIT-050 TEST")
    print(" FINAL FREEZE AND COMPLETION")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    certification = build_oit_049_report(root)

    report = build_oracle_terminal_final_freeze_completion_report(
        root,
        production_certification_report=certification,
    )

    assert report.subsystem_completed
    assert report.subsystem_frozen
    assert report.terminal_production_ready
    assert report.next_subsystem_authorized
    assert not report.further_oit_feature_builds_allowed
    assert report.correction_builds_allowed_only_for_defects

    manifest = report.freeze_manifest
    assert manifest.subsystem_id == "oracle_open_intelligence_terminal"
    assert manifest.final_milestone == "OIT-050"
    assert manifest.command_registry_certified
    assert manifest.end_to_end_pipeline_certified
    assert manifest.production_readiness_certified
    assert manifest.read_only_boundary_frozen
    assert manifest.publication_frozen_disabled
    assert manifest.action_authorization_frozen_disabled
    assert manifest.qseries_execution_frozen_disabled
    assert manifest.persistent_memory_deferred
    assert manifest.learning_deferred
    assert manifest.no_further_oit_feature_layers_required
    assert manifest.next_subsystem == NEXT_SUBSYSTEM

    assert (
        manifest.source_production_certification_hash
        == certification.report_hash
    )
    assert (
        manifest.source_runner_certification_hash
        == certification.runner_certification.certification_hash
    )
    assert (
        manifest.source_runner_sha256
        == certification.runner_certification.runner_sha256
    )
    assert (
        manifest.source_pipeline_certification_hash
        == certification.pipeline_certification.certification_hash
    )

    replay = build_oracle_terminal_final_freeze_completion_report(
        root,
        production_certification_report=certification,
    )
    assert replay == report
    assert verify_oracle_terminal_final_freeze_completion_report(
        report
    )

    tampered = replace(
        report,
        further_oit_feature_builds_allowed=True,
    )
    try:
        verify_oracle_terminal_final_freeze_completion_report(
            tampered
        )
    except OracleTerminalFinalFreezeInvariantError:
        pass
    else:
        raise AssertionError(
            "tampered OIT-050 report accepted"
        )

    assert not report.persistent_memory_enabled
    assert not report.learning_update_performed
    assert not report.analytics_execution_performed
    assert not report.database_access_performed
    assert not report.runtime_artifact_created
    assert not report.runtime_artifact_modified
    assert not report.networking_performed
    assert not report.publication_allowed
    assert not report.action_authorization_allowed
    assert not report.qseries_execution_allowed
    assert report.read_only

    print("[PASS] Certified OIT-049 Correction V3 consumed")
    print("[PASS] OIT-048 live runner hash frozen")
    print("[PASS] Command-registry certification frozen")
    print("[PASS] End-to-end pipeline certification frozen")
    print("[PASS] Production-readiness certification frozen")
    print("[PASS] Read-only boundary frozen")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Persistent memory deferred to next subsystem")
    print("[PASS] Continuous learning deferred to next subsystem")
    print("[PASS] No further OIT feature layers required")
    print("[PASS] Correction builds restricted to genuine defects")
    print("[PASS] Freeze deterministic across replay")
    print("[PASS] Tampered freeze report rejected")
    print("[DONE] OIT-050 FINAL FREEZE AND COMPLETION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
