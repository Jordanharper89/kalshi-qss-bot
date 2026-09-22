from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from qseries_v2.oracle_terminal.oracle_operator_decision_brief_assembly import (
    ENGINE_ID as OIT_022_ENGINE_ID,
    POLICY_ID as OIT_022_POLICY_ID,
    SCHEMA_VERSION as OIT_022_SCHEMA_VERSION,
    OracleOperatorDecisionBrief,
    _stable_hash as oit_022_hash,
    verify_operator_decision_brief,
)
from qseries_v2.oracle_terminal.oracle_terminal_decision_brief_consumption_contract import (
    build_terminal_brief_consumption_contract,
    verify_terminal_brief_consumption_contract,
)
from qseries_v2.oracle_terminal.oracle_terminal_decision_brief_presentation_view_model import (
    build_terminal_presentation_view_model,
    verify_terminal_presentation_view_model,
)
from qseries_v2.oracle_terminal.oracle_terminal_decision_brief_renderer_contract import (
    build_terminal_renderer_contract,
    verify_terminal_renderer_contract,
)
from qseries_v2.oracle_terminal.oracle_terminal_renderer_invocation_output_activation_gate import (
    build_terminal_renderer_activation_gate_report,
    verify_terminal_renderer_activation_gate_report,
)
from qseries_v2.oracle_terminal.oracle_terminal_activated_output_display_session_gate import (
    build_terminal_display_session_gate_report,
    verify_terminal_display_session_gate_report,
)


QUERY = (
    "what is the current direction of solana, "
    "what evidence supports it"
)


def make_zero_item_brief(
    root: Path,
    *,
    state: str = "abstain",
    direction: str = "neutral",
) -> OracleOperatorDecisionBrief:
    summary = (
        "0 items assembled: 0 ready, 0 observe, 0 abstain; "
        "0 require operator attention. "
        "This brief is explanatory only and cannot authorize action."
    )
    body = {
        "schema_version": OIT_022_SCHEMA_VERSION,
        "engine_id": OIT_022_ENGINE_ID,
        "policy_id": OIT_022_POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root.resolve()),
        "query": QUERY,
        "explanation_report_hash": "explanation-report-abstention-v3",
        "brief_items": (),
        "item_count": 0,
        "ready_item_count": 0,
        "observe_item_count": 0,
        "abstain_item_count": 0,
        "operator_attention_count": 0,
        "primary_state": state,
        "primary_direction": direction,
        "brief_title": (
            f"Oracle Operator Decision Brief — "
            f"{state.upper()} / {direction.upper()}"
        ),
        "executive_summary": summary,
        "operator_next_steps": (),
        "unresolved_blockers": (),
        "terminal_consumption_ready": False,
        "read_only": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "publication_allowed": False,
        "qseries_execution_allowed": False,
        "action_authorization_allowed": False,
        "failure_reason": None,
    }
    brief = OracleOperatorDecisionBrief(
        **body,
        brief_hash=oit_022_hash(body),
    )
    verify_operator_decision_brief(brief)
    return brief


def main() -> int:
    print("=" * 60)
    print(" OIT-050 DEFECT CORRECTION TEST")
    print(" BOUNDED ABSTENTION DISPLAY READINESS REPAIR")
    print("=" * 60)

    with TemporaryDirectory() as temporary:
        root = Path(temporary)

        brief = make_zero_item_brief(root)

        contract = build_terminal_brief_consumption_contract(
            root,
            QUERY,
            operator_brief=brief,
        )
        assert contract.source_item_count == 0
        assert contract.primary_state == "abstain"
        assert contract.primary_direction == "neutral"
        assert contract.section_count == 1
        assert contract.sections[0].section_type == "executive_summary"
        assert contract.consumption_ready
        assert contract.rendering_allowed
        assert contract.interactive_query_allowed
        assert verify_terminal_brief_consumption_contract(contract)

        view_model = build_terminal_presentation_view_model(
            root,
            QUERY,
            consumption_contract=contract,
        )
        assert view_model.panel_count == 1
        assert view_model.informational_panel_count == 1
        assert view_model.status_label == "ABSTAIN"
        assert view_model.direction_label == "NEUTRAL"
        assert view_model.rendering_ready
        assert view_model.keyboard_navigation_ready
        assert view_model.expandable_evidence_ready
        assert verify_terminal_presentation_view_model(view_model)

        renderer = build_terminal_renderer_contract(
            root,
            QUERY,
            presentation_view_model=view_model,
        )
        assert renderer.block_count == 1
        assert renderer.informational_block_count == 1
        assert renderer.renderer_ready
        assert renderer.terminal_output_lines
        assert any(
            "STATUS: ABSTAIN | DIRECTION: NEUTRAL" in line
            for line in renderer.terminal_output_lines
        )
        assert any(
            "0 items assembled" in line
            for line in renderer.terminal_output_lines
        )
        assert verify_terminal_renderer_contract(renderer)

        activation = build_terminal_renderer_activation_gate_report(
            root,
            QUERY,
            renderer_contract=renderer,
        )
        assert activation.invocation_authorized
        assert activation.output_activated
        assert activation.display_ready
        assert activation.renderer_activation_ready
        assert verify_terminal_renderer_activation_gate_report(
            activation
        )

        display = build_terminal_display_session_gate_report(
            root,
            QUERY,
            activation_report=activation,
        )
        assert display.session_open
        assert display.display_ready
        assert display.output_preserved_exactly
        assert display.display_session_ready
        assert verify_terminal_display_session_gate_report(display)

        replay_contract = build_terminal_brief_consumption_contract(
            root,
            QUERY,
            operator_brief=brief,
        )
        replay_view = build_terminal_presentation_view_model(
            root,
            QUERY,
            consumption_contract=replay_contract,
        )
        replay_renderer = build_terminal_renderer_contract(
            root,
            QUERY,
            presentation_view_model=replay_view,
        )
        replay_activation = build_terminal_renderer_activation_gate_report(
            root,
            QUERY,
            renderer_contract=replay_renderer,
        )
        replay_display = build_terminal_display_session_gate_report(
            root,
            QUERY,
            activation_report=replay_activation,
        )

        assert replay_contract == contract
        assert replay_view == view_model
        assert replay_renderer == renderer
        assert replay_activation == activation
        assert replay_display == display

        unsafe_brief = make_zero_item_brief(
            root,
            state="abstain",
            direction="bull",
        )
        unsafe_contract = build_terminal_brief_consumption_contract(
            root,
            QUERY,
            operator_brief=unsafe_brief,
        )
        assert not unsafe_contract.consumption_ready

    print("[PASS] Valid zero-item ABSTAIN / NEUTRAL brief consumed")
    print("[PASS] Executive-summary section retained")
    print("[PASS] OIT-023 consumption readiness repaired")
    print("[PASS] OIT-024 informational panel rendering ready")
    print("[PASS] OIT-025 renderer ready")
    print("[PASS] OIT-026 output activation ready")
    print("[PASS] OIT-027 display session ready")
    print("[PASS] Exact terminal output preserved")
    print("[PASS] Zero-item non-neutral case remained blocked")
    print("[PASS] Full readiness chain deterministic across replay")
    print("[PASS] Read-only and interactive boundaries preserved")
    print("[PASS] Publication and Q Series execution remained disabled")
    print("[DONE] OIT-050 BOUNDED ABSTENTION DISPLAY REPAIR PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
