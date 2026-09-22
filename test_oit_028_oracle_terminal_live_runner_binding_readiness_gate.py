from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from qseries_v2.oracle_terminal.oracle_terminal_activated_output_display_session_gate import (
    ENGINE_ID as OIT_027_ENGINE_ID,
    POLICY_ID as OIT_027_POLICY_ID,
    SCHEMA_VERSION as OIT_027_SCHEMA_VERSION,
    OracleTerminalDisplayFrame,
    OracleTerminalDisplaySession,
    OracleTerminalDisplaySessionGateReport,
    _stable_hash as oit_027_hash,
    verify_terminal_display_session_gate_report,
)
from qseries_v2.oracle_terminal.oracle_terminal_live_runner_binding_readiness_gate import (
    OracleTerminalRunnerBindingReadinessInvariantError,
    build_terminal_runner_binding_readiness_gate_report,
    verify_terminal_runner_binding_readiness_gate_report,
)


def make_display_report(root: Path):
    frame_body = {
        "frame_index": 1,
        "frame_type": "banner",
        "frame_lines": ("Oracle Terminal", "STATUS: READY"),
        "source_activation_hash": "activation-hash",
        "display_only": True,
        "read_only": True,
    }
    frame = OracleTerminalDisplayFrame(
        **frame_body,
        frame_hash=oit_027_hash(frame_body),
    )
    session_body = {
        "session_id": "session-001",
        "query": "Inspect runner binding readiness.",
        "source_activation_report_hash": "activation-report-hash",
        "source_output_activation_hash": "activation-hash",
        "frames": (frame,),
        "frame_count": 1,
        "output_line_count": 2,
        "session_open": True,
        "display_ready": True,
        "interactive_read_only": True,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
        "read_only": True,
    }
    session = OracleTerminalDisplaySession(
        **session_body,
        session_hash=oit_027_hash(session_body),
    )
    report_body = {
        "schema_version": OIT_027_SCHEMA_VERSION,
        "engine_id": OIT_027_ENGINE_ID,
        "policy_id": OIT_027_POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root.resolve()),
        "query": "Inspect runner binding readiness.",
        "activation_report_hash": "activation-report-hash",
        "display_session": session,
        "session_open": True,
        "display_ready": True,
        "output_preserved_exactly": True,
        "display_session_ready": True,
        "read_only": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
        "failure_reason": None,
    }
    report = OracleTerminalDisplaySessionGateReport(
        **report_body,
        report_hash=oit_027_hash(report_body),
    )
    verify_terminal_display_session_gate_report(report)
    return report


def main() -> int:
    print("=" * 48)
    print(" OIT-028 TEST")
    print(" LIVE RUNNER BINDING READINESS GATE")
    print("=" * 48)

    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        runner = root / "run_oracle_open_intelligence_terminal.py"
        runner.write_text(
            "from __future__ import annotations\n\n"
            "def main() -> int:\n"
            "    return 0\n\n"
            "if __name__ == \"__main__\":\n"
            "    raise SystemExit(main())\n",
            encoding="utf-8",
        )
        source = make_display_report(root)
        report = build_terminal_runner_binding_readiness_gate_report(
            root,
            source.query,
            display_session_gate_report=source,
        )

        assert report.runner_identity_verified
        assert report.syntax_verified
        assert report.import_safety_verified
        assert report.callable_resolution_verified
        assert report.signature_compatibility_verified
        assert report.read_only_dependency_verified
        assert report.live_runner_binding_ready
        assert not report.runner_modified
        assert report.runner_inspection.main_entrypoint_present
        assert report.runner_inspection.direct_execution_guard_present
        assert not report.runner_inspection.forbidden_imports
        assert not report.runner_inspection.forbidden_call_sites

        replay = build_terminal_runner_binding_readiness_gate_report(
            root,
            source.query,
            display_session_gate_report=source,
        )
        assert replay == report
        assert verify_terminal_runner_binding_readiness_gate_report(report)

        tampered = replace(
            report,
            runner_modified=True,
        )
        try:
            verify_terminal_runner_binding_readiness_gate_report(tampered)
        except OracleTerminalRunnerBindingReadinessInvariantError:
            pass
        else:
            raise AssertionError("tampered runner readiness report accepted")

        assert report.read_only
        assert not report.analytics_execution_performed
        assert not report.database_access_performed
        assert not report.publication_allowed
        assert not report.action_authorization_allowed
        assert not report.qseries_execution_allowed

    print("[PASS] Certified OIT-027 display-session gate consumed")
    print("[PASS] Oracle terminal runner identity verified")
    print("[PASS] Runner syntax verified")
    print("[PASS] Main entrypoint detected")
    print("[PASS] Direct-execution guard detected")
    print("[PASS] Import-side-effect risk rejected")
    print("[PASS] Certified display-session callable resolved")
    print("[PASS] Callable signature compatibility certified")
    print("[PASS] Read-only dependency path certified")
    print("[PASS] No runner modification performed")
    print("[PASS] Runner-binding report deterministic across replay")
    print("[PASS] Tampered runner-binding report rejected")
    print("[PASS] Publication, action authorization, and Q Series execution disabled")
    print("[DONE] OIT-028 LIVE RUNNER BINDING READINESS GATE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
