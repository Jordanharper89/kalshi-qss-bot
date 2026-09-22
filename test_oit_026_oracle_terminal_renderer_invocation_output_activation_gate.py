from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from qseries_v2.oracle_terminal.oracle_terminal_decision_brief_renderer_contract import (
    ENGINE_ID as OIT_025_ENGINE_ID,
    POLICY_ID as OIT_025_POLICY_ID,
    SCHEMA_VERSION as OIT_025_SCHEMA_VERSION,
    OracleTerminalRenderedBlock,
    OracleTerminalRendererContract,
    _stable_hash as oit_025_hash,
    verify_terminal_renderer_contract,
)
from qseries_v2.oracle_terminal.oracle_terminal_renderer_invocation_output_activation_gate import (
    OracleTerminalRendererActivationInvariantError,
    build_terminal_renderer_activation_gate_report,
    verify_terminal_renderer_activation_gate_report,
)


def rendered_block(index: int):
    body = {
        "block_index": index,
        "block_type": "decision_item",
        "severity": "warning",
        "heading": "Decision Item",
        "rendered_lines": ("[~] Decision Item", "  evidence"),
        "source_panel_hash": f"panel-{index}",
        "operator_attention_required": False,
        "read_only": True,
    }
    return OracleTerminalRenderedBlock(
        **body,
        block_hash=oit_025_hash(body),
    )


def make_contract(root: Path):
    blocks = (rendered_block(1),)
    banner = (
        "=" * 64,
        "Oracle Operator Decision Brief",
        "STATUS: OBSERVE | DIRECTION: BULL",
        "Synthetic renderer contract.",
        "=" * 64,
    )
    output = banner + ("",) + blocks[0].rendered_lines
    body = {
        "schema_version": OIT_025_SCHEMA_VERSION,
        "engine_id": OIT_025_ENGINE_ID,
        "policy_id": OIT_025_POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root.resolve()),
        "query": "Activate renderer output.",
        "presentation_view_model_hash": "presentation-view-model-hash",
        "banner_lines": banner,
        "rendered_blocks": blocks,
        "block_count": 1,
        "critical_block_count": 0,
        "warning_block_count": 1,
        "informational_block_count": 0,
        "operator_attention_count": 0,
        "renderer_ready": True,
        "terminal_output_lines": output,
        "read_only": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "publication_allowed": False,
        "qseries_execution_allowed": False,
        "action_authorization_allowed": False,
        "failure_reason": None,
    }
    contract = OracleTerminalRendererContract(
        **body,
        contract_hash=oit_025_hash(body),
    )
    verify_terminal_renderer_contract(contract)
    return contract


def main() -> int:
    print("=" * 48)
    print(" OIT-026 TEST")
    print(" TERMINAL RENDERER INVOCATION OUTPUT ACTIVATION GATE")
    print("=" * 48)

    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        source = make_contract(root)
        report = build_terminal_renderer_activation_gate_report(
            root,
            source.query,
            renderer_contract=source,
        )

        assert report.renderer_contract_hash == source.contract_hash
        assert report.invocation.invocation_authorized
        assert report.invocation.display_only
        assert report.invocation.read_only
        assert report.activation.output_activated
        assert report.activation.display_ready
        assert report.activation.terminal_output_lines == source.terminal_output_lines
        assert report.activation.output_line_count == len(source.terminal_output_lines)
        assert report.renderer_activation_ready

        replay = build_terminal_renderer_activation_gate_report(
            root,
            source.query,
            renderer_contract=source,
        )
        assert replay == report
        assert verify_terminal_renderer_activation_gate_report(report)

        tampered = replace(
            report,
            display_ready=False,
        )
        try:
            verify_terminal_renderer_activation_gate_report(tampered)
        except OracleTerminalRendererActivationInvariantError:
            pass
        else:
            raise AssertionError("tampered activation report accepted")

        assert report.read_only
        assert not report.analytics_execution_performed
        assert not report.database_access_performed
        assert not report.publication_allowed
        assert not report.action_authorization_allowed
        assert not report.qseries_execution_allowed

    print("[PASS] Certified OIT-025 renderer contract consumed")
    print("[PASS] Renderer invocation materialized")
    print("[PASS] Display-only invocation authorized")
    print("[PASS] Terminal output activation materialized")
    print("[PASS] Activated output matched certified renderer output")
    print("[PASS] Output line count certified")
    print("[PASS] Renderer activation readiness certified")
    print("[PASS] Complete OIT-025 lineage retained")
    print("[PASS] Activation report deterministic across replay")
    print("[PASS] Tampered activation report rejected")
    print("[PASS] No analytics execution or database access performed")
    print("[PASS] Publication, action authorization, and Q Series execution disabled")
    print("[DONE] OIT-026 TERMINAL RENDERER INVOCATION OUTPUT ACTIVATION GATE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
