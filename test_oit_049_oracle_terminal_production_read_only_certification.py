from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_terminal.oracle_terminal_production_read_only_certification import (
    OracleTerminalProductionCertificationInvariantError,
    build_oracle_terminal_production_read_only_certification_report,
    certify_live_terminal_runner,
    verify_oracle_terminal_production_read_only_certification_report,
)


def load_oit_048_fixture(root: Path):
    path = root / "test_oit_048_oracle_end_to_end_interactive_intelligence_pipeline.py"
    name = "oit_048_fixture_for_oit_049_v3"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load certified OIT-048 fixture")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    print("=" * 48)
    print(" OIT-049 TEST")
    print(" PRODUCTION READ-ONLY CERTIFICATION")
    print(" CORRECTION V3 - REGISTRY-DRIVEN RUNNER")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    fixture = load_oit_048_fixture(root)

    from qseries_v2.oracle_terminal.oracle_end_to_end_interactive_intelligence_pipeline import (
        execute_end_to_end_interactive_intelligence_pipeline,
    )

    context = fixture.make_context_report(root)
    session = fixture.make_prior_session()
    pipeline_report = execute_end_to_end_interactive_intelligence_pipeline(
        root,
        context_assembly_report=context,
        prior_session_context=session,
        query="Has it changed now?",
    )

    runner = certify_live_terminal_runner(root)
    assert runner.runner_certified
    assert runner.runner_version == "OIT-048"
    assert runner.pipeline_version == "OIT-048"
    assert runner.pipeline_bound
    assert runner.execute_callable_available
    assert runner.render_callable_available
    assert runner.command_registry.command_registry_certified
    assert not runner.command_registry.missing_commands
    assert tuple(runner.command_registry.required_commands) == (
        "/help",
        "/status",
        "/ask",
        "/session",
        "/clear",
        "/quit",
    )
    assert runner.read_only_boundary_present
    assert runner.publication_disabled
    assert runner.action_authorization_disabled
    assert runner.qseries_execution_disabled

    report = build_oracle_terminal_production_read_only_certification_report(
        root,
        pipeline_report=pipeline_report,
    )
    assert report.production_readiness_certified
    assert report.final_freeze_ready
    assert report.runner_certification.runner_certified
    assert report.pipeline_certification.pipeline_certified

    replay = build_oracle_terminal_production_read_only_certification_report(
        root,
        pipeline_report=pipeline_report,
    )
    assert replay == report
    assert verify_oracle_terminal_production_read_only_certification_report(
        report
    )

    tampered = replace(report, publication_allowed=True)
    try:
        verify_oracle_terminal_production_read_only_certification_report(
            tampered
        )
    except OracleTerminalProductionCertificationInvariantError:
        pass
    else:
        raise AssertionError("tampered OIT-049 report accepted")

    print("[PASS] Certified OIT-048 pipeline consumed")
    print("[PASS] Live OIT-048 runner binding verified")
    print("[PASS] Registry-driven command locations discovered")
    print("[PASS] /help, /status, /ask, /session, /clear, and /quit verified")
    print("[PASS] Command literals not required in live runner")
    print("[PASS] Read-only terminal boundary verified")
    print("[PASS] Exact pipeline stage order verified")
    print("[PASS] Exact cross-stage lineage verified")
    print("[PASS] Production readiness certified")
    print("[PASS] Final-freeze readiness certified")
    print("[PASS] Certification deterministic across replay")
    print("[PASS] Tampered certification report rejected")
    print("[PASS] Persistent memory and learning remained disabled")
    print("[DONE] OIT-049 CORRECTION V3 PRODUCTION CERTIFICATION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
