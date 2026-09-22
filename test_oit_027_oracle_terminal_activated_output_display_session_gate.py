from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from qseries_v2.oracle_terminal.oracle_terminal_renderer_invocation_output_activation_gate import (
    ENGINE_ID as OIT_026_ENGINE_ID,
    POLICY_ID as OIT_026_POLICY_ID,
    SCHEMA_VERSION as OIT_026_SCHEMA_VERSION,
    OracleTerminalRendererActivationGateReport,
    OracleTerminalRendererInvocation,
    OracleTerminalRendererOutputActivation,
    _stable_hash as oit_026_hash,
    verify_terminal_renderer_activation_gate_report,
)
from qseries_v2.oracle_terminal.oracle_terminal_activated_output_display_session_gate import (
    OracleTerminalDisplaySessionInvariantError,
    build_terminal_display_session_gate_report,
    verify_terminal_display_session_gate_report,
)


def make_activation_report(root: Path):
    output = (
        "=" * 64,
        "Oracle Operator Decision Brief",
        "STATUS: OBSERVE | DIRECTION: BULL",
        "Synthetic activated output.",
        "=" * 64,
        "",
        "[!] Operator Attention",
        "  review contested evidence",
        "",
        "[~] Next Steps",
        "  confirm persistence",
    )
    invocation_body = {
        "invocation_id": "invocation-001",
        "query": "Open the display session.",
        "source_renderer_contract_hash": "renderer-contract-hash",
        "requested_operation": "render_terminal_output",
        "output_mode": "display_only",
        "invocation_authorized": True,
        "display_only": True,
        "read_only": True,
    }
    invocation = OracleTerminalRendererInvocation(
        **invocation_body,
        invocation_hash=oit_026_hash(invocation_body),
    )
    activation_body = {
        "activation_id": "activation-001",
        "invocation_hash": invocation.invocation_hash,
        "source_renderer_contract_hash": "renderer-contract-hash",
        "terminal_output_lines": output,
        "output_line_count": len(output),
        "display_ready": True,
        "output_activated": True,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
        "read_only": True,
    }
    activation = OracleTerminalRendererOutputActivation(
        **activation_body,
        activation_hash=oit_026_hash(activation_body),
    )
    report_body = {
        "schema_version": OIT_026_SCHEMA_VERSION,
        "engine_id": OIT_026_ENGINE_ID,
        "policy_id": OIT_026_POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root.resolve()),
        "query": "Open the display session.",
        "renderer_contract_hash": "renderer-contract-hash",
        "invocation": invocation,
        "activation": activation,
        "invocation_authorized": True,
        "output_activated": True,
        "display_ready": True,
        "renderer_activation_ready": True,
        "read_only": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
        "failure_reason": None,
    }
    report = OracleTerminalRendererActivationGateReport(
        **report_body,
        report_hash=oit_026_hash(report_body),
    )
    verify_terminal_renderer_activation_gate_report(report)
    return report


def main() -> int:
    print("=" * 48)
    print(" OIT-027 TEST")
    print(" TERMINAL ACTIVATED OUTPUT DISPLAY SESSION GATE")
    print("=" * 48)

    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        source = make_activation_report(root)
        report = build_terminal_display_session_gate_report(
            root,
            source.query,
            activation_report=source,
        )

        assert report.activation_report_hash == source.report_hash
        assert report.session_open
        assert report.display_ready
        assert report.output_preserved_exactly
        assert report.display_session_ready
        assert report.display_session.frame_count == 3
        assert report.display_session.output_line_count == len(
            source.activation.terminal_output_lines
        )
        assert report.display_session.frames[0].frame_type == "banner"
        assert report.display_session.frames[1].frame_type == "critical"
        assert report.display_session.frames[2].frame_type == "warning"

        replay = build_terminal_display_session_gate_report(
            root,
            source.query,
            activation_report=source,
        )
        assert replay == report
        assert verify_terminal_display_session_gate_report(report)

        tampered = replace(
            report,
            output_preserved_exactly=False,
        )
        try:
            verify_terminal_display_session_gate_report(tampered)
        except OracleTerminalDisplaySessionInvariantError:
            pass
        else:
            raise AssertionError("tampered display session report accepted")

        assert report.read_only
        assert not report.analytics_execution_performed
        assert not report.database_access_performed
        assert not report.publication_allowed
        assert not report.action_authorization_allowed
        assert not report.qseries_execution_allowed

    print("[PASS] Certified OIT-026 activation report consumed")
    print("[PASS] Read-only display session materialized")
    print("[PASS] Banner frame materialized")
    print("[PASS] Critical frame materialized")
    print("[PASS] Warning frame materialized")
    print("[PASS] Activated output preserved exactly")
    print("[PASS] Interactive read-only session enabled")
    print("[PASS] Display-session readiness certified")
    print("[PASS] Complete OIT-026 lineage retained")
    print("[PASS] Display-session report deterministic across replay")
    print("[PASS] Tampered display-session report rejected")
    print("[PASS] No analytics execution or database access performed")
    print("[PASS] Publication, action authorization, and Q Series execution disabled")
    print("[DONE] OIT-027 TERMINAL ACTIVATED OUTPUT DISPLAY SESSION GATE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
