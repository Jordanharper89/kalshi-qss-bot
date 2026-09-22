from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from qseries_v2.oracle_terminal.oracle_terminal_decision_brief_presentation_view_model import (
    ENGINE_ID as OIT_024_ENGINE_ID,
    POLICY_ID as OIT_024_POLICY_ID,
    SCHEMA_VERSION as OIT_024_SCHEMA_VERSION,
    OracleTerminalPresentationPanel,
    OracleTerminalPresentationViewModel,
    _stable_hash as oit_024_hash,
    verify_terminal_presentation_view_model,
)
from qseries_v2.oracle_terminal.oracle_terminal_decision_brief_renderer_contract import (
    OracleTerminalRendererInvariantError,
    build_terminal_renderer_contract,
    verify_terminal_renderer_contract,
)


def panel(index: int, severity: str, attention: bool):
    body = {
        "panel_index": index,
        "panel_type": "attention" if attention else "decision_item",
        "panel_label": f"{severity.title()} Panel",
        "severity": severity,
        "content_lines": (f"{severity} content",),
        "source_section_hash": f"section-{index}",
        "operator_attention_required": attention,
        "display_order": 1 if severity == "critical" else 2 if severity == "warning" else 3,
        "read_only": True,
    }
    return OracleTerminalPresentationPanel(
        **body,
        panel_hash=oit_024_hash(body),
    )


def make_view_model(root: Path):
    panels = (
        panel(1, "critical", True),
        panel(2, "warning", False),
        panel(3, "informational", False),
    )
    body = {
        "schema_version": OIT_024_SCHEMA_VERSION,
        "engine_id": OIT_024_ENGINE_ID,
        "policy_id": OIT_024_POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root.resolve()),
        "query": "Render the terminal decision brief.",
        "consumption_contract_hash": "consumption-contract-hash",
        "terminal_heading": "Oracle Operator Decision Brief",
        "terminal_subheading": "Synthetic presentation model.",
        "status_label": "ABSTAIN",
        "direction_label": "BULL",
        "panels": panels,
        "panel_count": 3,
        "critical_panel_count": 1,
        "warning_panel_count": 1,
        "informational_panel_count": 1,
        "operator_attention_count": 1,
        "rendering_ready": True,
        "keyboard_navigation_ready": True,
        "expandable_evidence_ready": True,
        "read_only": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "publication_allowed": False,
        "qseries_execution_allowed": False,
        "action_authorization_allowed": False,
        "failure_reason": None,
    }
    view_model = OracleTerminalPresentationViewModel(
        **body,
        view_model_hash=oit_024_hash(body),
    )
    verify_terminal_presentation_view_model(view_model)
    return view_model


def main() -> int:
    print("=" * 48)
    print(" OIT-025 TEST")
    print(" TERMINAL DECISION BRIEF RENDERER CONTRACT")
    print("=" * 48)

    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        source = make_view_model(root)
        contract = build_terminal_renderer_contract(
            root,
            source.query,
            presentation_view_model=source,
        )

        assert contract.presentation_view_model_hash == source.view_model_hash
        assert contract.block_count == 3
        assert contract.critical_block_count == 1
        assert contract.warning_block_count == 1
        assert contract.informational_block_count == 1
        assert contract.operator_attention_count == 1
        assert contract.renderer_ready
        assert contract.banner_lines
        assert contract.terminal_output_lines
        assert "STATUS: ABSTAIN | DIRECTION: BULL" in contract.banner_lines

        assert contract.rendered_blocks[0].rendered_lines[0].startswith("[!]")
        assert contract.rendered_blocks[1].rendered_lines[0].startswith("[~]")
        assert contract.rendered_blocks[2].rendered_lines[0].startswith("[i]")

        for block in contract.rendered_blocks:
            assert block.heading
            assert block.rendered_lines
            assert block.source_panel_hash
            assert block.read_only

        replay = build_terminal_renderer_contract(
            root,
            source.query,
            presentation_view_model=source,
        )
        assert replay == contract
        assert verify_terminal_renderer_contract(contract)

        tampered = replace(
            contract,
            terminal_output_lines=contract.terminal_output_lines + ("tampered",),
        )
        try:
            verify_terminal_renderer_contract(tampered)
        except OracleTerminalRendererInvariantError:
            pass
        else:
            raise AssertionError("tampered renderer contract accepted")

        assert contract.read_only
        assert not contract.analytics_execution_performed
        assert not contract.database_access_performed
        assert not contract.publication_allowed
        assert not contract.qseries_execution_allowed
        assert not contract.action_authorization_allowed

    print("[PASS] Certified OIT-024 presentation view model consumed")
    print("[PASS] Terminal banner materialized")
    print("[PASS] Critical rendering marker materialized")
    print("[PASS] Warning rendering marker materialized")
    print("[PASS] Informational rendering marker materialized")
    print("[PASS] Terminal output flattened deterministically")
    print("[PASS] Operator-attention rendering preserved")
    print("[PASS] Renderer readiness certified")
    print("[PASS] Complete OIT-024 lineage retained")
    print("[PASS] Renderer contract deterministic across replay")
    print("[PASS] Tampered renderer contract rejected")
    print("[PASS] No analytics execution or database access performed")
    print("[PASS] Publication, action authorization, and Q Series execution disabled")
    print("[DONE] OIT-025 TERMINAL DECISION BRIEF RENDERER CONTRACT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
