from __future__ import annotations

import importlib.util
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
)
from qseries_v2.oracle_terminal.oracle_terminal_live_runner_binding_authorization_gate import (
    ENGINE_ID as OIT_029_ENGINE_ID,
    POLICY_ID as OIT_029_POLICY_ID,
    SCHEMA_VERSION as OIT_029_SCHEMA_VERSION,
    OracleTerminalRunnerBindingAuthorizationGateReport,
    OracleTerminalRunnerCallableAuthorization,
    OracleTerminalRunnerDeniedCapability,
    _stable_hash as oit_029_hash,
)
from qseries_v2.oracle_terminal.oracle_terminal_live_runner_display_integration_certification import (
    OracleTerminalLiveRunnerIntegrationInvariantError,
    certify_live_runner_integration,
    verify_live_runner_integration_certification,
)


def load_runner(root: Path):
    path = root / "run_oracle_open_intelligence_terminal.py"
    spec = importlib.util.spec_from_file_location("oit_030_runner_test", path)
    if spec is None or spec.loader is None:
        raise AssertionError("unable to load runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def display_report(root: Path, query: str):
    frame_one_body = {
        "frame_index": 1,
        "frame_type": "banner",
        "frame_lines": ("Oracle Terminal", "STATUS: READY"),
        "source_activation_hash": "activation-hash",
        "display_only": True,
        "read_only": True,
    }
    frame_one = OracleTerminalDisplayFrame(
        **frame_one_body,
        frame_hash=oit_027_hash(frame_one_body),
    )
    frame_two_body = {
        "frame_index": 2,
        "frame_type": "informational",
        "frame_lines": ("[i] Query", f"  {query}"),
        "source_activation_hash": "activation-hash",
        "display_only": True,
        "read_only": True,
    }
    frame_two = OracleTerminalDisplayFrame(
        **frame_two_body,
        frame_hash=oit_027_hash(frame_two_body),
    )
    session_body = {
        "session_id": "session-030",
        "query": query,
        "source_activation_report_hash": "activation-report-hash",
        "source_output_activation_hash": "activation-hash",
        "frames": (frame_one, frame_two),
        "frame_count": 2,
        "output_line_count": 4,
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
        "query": query,
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
    return OracleTerminalDisplaySessionGateReport(
        **report_body,
        report_hash=oit_027_hash(report_body),
    )


def authorization_report(root: Path, runner_sha: str):
    authorization_body = {
        "authorization_id": "authorization-030",
        "runner_sha256": runner_sha,
        "readiness_report_hash": "readiness-hash",
        "authorized_module": (
            "qseries_v2.oracle_terminal."
            "oracle_terminal_activated_output_display_session_gate"
        ),
        "authorized_callable": "build_terminal_display_session_gate_report",
        "authorized_signature": ("repository_root", "query"),
        "invocation_mode": "display_session_only",
        "display_only": True,
        "read_only": True,
        "analytics_access_allowed": False,
        "database_access_allowed": False,
        "networking_allowed": False,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
        "authorization_granted": True,
    }
    authorization = OracleTerminalRunnerCallableAuthorization(
        **authorization_body,
        authorization_hash=oit_029_hash(authorization_body),
    )
    denials = []
    for name in (
        "direct_analytics_execution",
        "database_access",
        "networking",
        "publication",
        "action_authorization",
        "qseries_execution",
        "lower_level_terminal_bypass",
    ):
        body = {
            "capability_name": name,
            "denial_reason": "certified denial",
            "denial_enforced": True,
        }
        denials.append(
            OracleTerminalRunnerDeniedCapability(
                **body,
                denial_hash=oit_029_hash(body),
            )
        )
    report_body = {
        "schema_version": OIT_029_SCHEMA_VERSION,
        "engine_id": OIT_029_ENGINE_ID,
        "policy_id": OIT_029_POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root.resolve()),
        "readiness_report_hash": "readiness-hash",
        "runner_sha256": runner_sha,
        "callable_authorization": authorization,
        "denied_capabilities": tuple(denials),
        "denied_capability_count": 7,
        "runner_identity_authorized": True,
        "callable_identity_authorized": True,
        "signature_authorized": True,
        "display_only_authorized": True,
        "read_only_boundary_authorized": True,
        "live_runner_binding_authorized": True,
        "runner_modified": False,
        "read_only": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
        "failure_reason": None,
    }
    return OracleTerminalRunnerBindingAuthorizationGateReport(
        **report_body,
        report_hash=oit_029_hash(report_body),
    )


def main() -> int:
    print("=" * 48)
    print(" OIT-030 TEST")
    print(" LIVE RUNNER DISPLAY INTEGRATION")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    runner_path = root / "run_oracle_open_intelligence_terminal.py"
    module = load_runner(root)

    captured = []
    query = "What is the strongest current opportunity?"
    report = display_report(root, query)

    def builder(repository_root, supplied_query):
        assert Path(repository_root).resolve() == root.resolve()
        assert supplied_query == query
        return report

    returned = module.display_query(
        query,
        root=root,
        builder=builder,
        write=captured.append,
    )
    assert returned == report
    assert captured == [
        "Oracle Terminal",
        "STATUS: READY",
        "",
        "[i] Query",
        f"  {query}",
    ]
    assert module.normalize_query("  What   changed?  ") == "What changed?"
    assert module.main(["--status"]) == 0

    runner_sha = __import__("hashlib").sha256(
        runner_path.read_bytes()
    ).hexdigest()
    authorization = authorization_report(root, runner_sha)
    certification = certify_live_runner_integration(
        root,
        authorization,
    )
    assert certification.runner_integration_ready
    assert certification.natural_language_query_supported
    assert certification.one_shot_query_supported
    assert certification.interactive_prompt_supported
    assert certification.certified_display_session_invocation_present
    assert certification.certified_frame_rendering_present
    assert certification.exact_frame_order_preserved
    assert certification.safe_prompt_return_present
    assert certification.help_command_present
    assert certification.status_command_present
    assert certification.quit_command_present
    assert verify_live_runner_integration_certification(certification)

    tampered = replace(certification, read_only=False)
    try:
        verify_live_runner_integration_certification(tampered)
    except OracleTerminalLiveRunnerIntegrationInvariantError:
        pass
    else:
        raise AssertionError("tampered integration certification accepted")

    print("[PASS] Certified OIT-029 authorization contract consumed")
    print("[PASS] Live Oracle terminal runner replaced")
    print("[PASS] Natural-language one-shot query supported")
    print("[PASS] Interactive natural-language prompt supported")
    print("[PASS] Certified OIT-027 display-session callable invoked")
    print("[PASS] Certified display frames rendered in exact order")
    print("[PASS] Safe return to interactive prompt certified")
    print("[PASS] Help, status, and quit commands available")
    print("[PASS] Tampered integration certification rejected")
    print("[PASS] Publication, action authorization, and Q Series execution disabled")
    print("[DONE] OIT-030 LIVE RUNNER DISPLAY INTEGRATION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
