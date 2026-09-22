from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from qseries_v2.oracle_terminal.oracle_terminal_live_runner_binding_readiness_gate import (
    ENGINE_ID as OIT_028_ENGINE_ID,
    POLICY_ID as OIT_028_POLICY_ID,
    SCHEMA_VERSION as OIT_028_SCHEMA_VERSION,
    OracleTerminalRunnerBindingContract,
    OracleTerminalRunnerBindingReadinessGateReport,
    OracleTerminalRunnerInspection,
    _stable_hash as oit_028_hash,
    verify_terminal_runner_binding_readiness_gate_report,
)
from qseries_v2.oracle_terminal.oracle_terminal_live_runner_binding_authorization_gate import (
    OracleTerminalRunnerBindingAuthorizationInvariantError,
    build_terminal_runner_binding_authorization_gate_report,
    verify_terminal_runner_binding_authorization_gate_report,
)


def make_readiness_report(root: Path):
    inspection_body = {
        "runner_path": str(
            root / "run_oracle_open_intelligence_terminal.py"
        ),
        "runner_name": "run_oracle_open_intelligence_terminal.py",
        "runner_exists": True,
        "runner_sha256": "runner-sha256",
        "syntax_valid": True,
        "top_level_imports": ("pathlib",),
        "top_level_functions": ("main",),
        "main_entrypoint_present": True,
        "direct_execution_guard_present": True,
        "forbidden_imports": (),
        "forbidden_call_sites": (),
        "import_side_effect_risk_detected": False,
    }
    inspection = OracleTerminalRunnerInspection(
        **inspection_body,
        inspection_hash=oit_028_hash(inspection_body),
    )
    binding_body = {
        "binding_id": "binding-001",
        "runner_sha256": "runner-sha256",
        "source_display_session_gate_hash": "display-session-gate-hash",
        "required_callable_module": (
            "qseries_v2.oracle_terminal."
            "oracle_terminal_activated_output_display_session_gate"
        ),
        "required_callable_name": (
            "build_terminal_display_session_gate_report"
        ),
        "required_callable_signature": ("repository_root", "query"),
        "runner_entrypoint_name": "main",
        "import_safe": True,
        "callable_resolution_ready": True,
        "signature_compatible": True,
        "read_only_dependency_path": True,
        "publication_exposure_detected": False,
        "execution_exposure_detected": False,
        "database_write_exposure_detected": False,
        "networking_side_effect_exposure_detected": False,
        "binding_ready": True,
    }
    binding = OracleTerminalRunnerBindingContract(
        **binding_body,
        binding_hash=oit_028_hash(binding_body),
    )
    report_body = {
        "schema_version": OIT_028_SCHEMA_VERSION,
        "engine_id": OIT_028_ENGINE_ID,
        "policy_id": OIT_028_POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root.resolve()),
        "runner_inspection": inspection,
        "binding_contract": binding,
        "runner_identity_verified": True,
        "syntax_verified": True,
        "import_safety_verified": True,
        "callable_resolution_verified": True,
        "signature_compatibility_verified": True,
        "read_only_dependency_verified": True,
        "live_runner_binding_ready": True,
        "runner_modified": False,
        "read_only": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
        "failure_reason": None,
    }
    report = OracleTerminalRunnerBindingReadinessGateReport(
        **report_body,
        report_hash=oit_028_hash(report_body),
    )
    verify_terminal_runner_binding_readiness_gate_report(report)
    return report


def main() -> int:
    print("=" * 48)
    print(" OIT-029 TEST")
    print(" LIVE RUNNER BINDING AUTHORIZATION GATE")
    print("=" * 48)

    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        source = make_readiness_report(root)
        report = build_terminal_runner_binding_authorization_gate_report(
            root,
            "Authorize the terminal runner binding.",
            readiness_report=source,
        )

        authorization = report.callable_authorization
        assert report.readiness_report_hash == source.report_hash
        assert report.runner_sha256 == source.runner_inspection.runner_sha256
        assert authorization.authorization_granted
        assert authorization.display_only
        assert authorization.read_only
        assert not authorization.analytics_access_allowed
        assert not authorization.database_access_allowed
        assert not authorization.networking_allowed
        assert not authorization.publication_allowed
        assert not authorization.action_authorization_allowed
        assert not authorization.qseries_execution_allowed
        assert report.denied_capability_count == 7
        assert all(
            denial.denial_enforced
            for denial in report.denied_capabilities
        )
        assert report.runner_identity_authorized
        assert report.callable_identity_authorized
        assert report.signature_authorized
        assert report.display_only_authorized
        assert report.read_only_boundary_authorized
        assert report.live_runner_binding_authorized
        assert not report.runner_modified

        replay = build_terminal_runner_binding_authorization_gate_report(
            root,
            "Authorize the terminal runner binding.",
            readiness_report=source,
        )
        assert replay == report
        assert verify_terminal_runner_binding_authorization_gate_report(
            report
        )

        tampered = replace(
            report,
            runner_modified=True,
        )
        try:
            verify_terminal_runner_binding_authorization_gate_report(
                tampered
            )
        except OracleTerminalRunnerBindingAuthorizationInvariantError:
            pass
        else:
            raise AssertionError(
                "tampered runner authorization report accepted"
            )

        assert report.read_only
        assert not report.analytics_execution_performed
        assert not report.database_access_performed
        assert not report.publication_allowed
        assert not report.action_authorization_allowed
        assert not report.qseries_execution_allowed

    print("[PASS] Certified OIT-028 runner readiness consumed")
    print("[PASS] Exact runner identity authorized")
    print("[PASS] Exact OIT-027 display-session callable authorized")
    print("[PASS] Callable signature authorized")
    print("[PASS] Display-session-only invocation authorized")
    print("[PASS] Direct analytics access denied")
    print("[PASS] Database and networking access denied")
    print("[PASS] Publication and action authorization denied")
    print("[PASS] Q Series execution denied")
    print("[PASS] Lower-level terminal bypass denied")
    print("[PASS] No runner modification performed")
    print("[PASS] Authorization report deterministic across replay")
    print("[PASS] Tampered authorization report rejected")
    print("[DONE] OIT-029 LIVE RUNNER BINDING AUTHORIZATION GATE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
