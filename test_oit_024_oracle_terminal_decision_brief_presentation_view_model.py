from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from qseries_v2.oracle_terminal.oracle_terminal_decision_brief_consumption_contract import (
    ENGINE_ID as OIT_023_ENGINE_ID,
    POLICY_ID as OIT_023_POLICY_ID,
    SCHEMA_VERSION as OIT_023_SCHEMA_VERSION,
    OracleTerminalBriefConsumptionContract,
    OracleTerminalBriefSection,
    _stable_hash as oit_023_hash,
    verify_terminal_brief_consumption_contract,
)
from qseries_v2.oracle_terminal.oracle_terminal_decision_brief_presentation_view_model import (
    OracleTerminalPresentationInvariantError,
    build_terminal_presentation_view_model,
    verify_terminal_presentation_view_model,
)


def section(
    index: int,
    section_type: str,
    attention: bool,
    priority: int,
):
    body = {
        "section_index": index,
        "section_type": section_type,
        "title": f"{section_type} title",
        "content_lines": (f"{section_type} content",),
        "source_item_hashes": (f"item-{index}",),
        "attention_required": attention,
        "display_priority": priority,
    }
    return OracleTerminalBriefSection(
        **body,
        section_hash=oit_023_hash(body),
    )


def make_contract(root: Path):
    sections = (
        section(1, "executive_summary", True, 1),
        section(2, "attention", True, 2),
        section(5, "blockers", True, 2),
        section(3, "decision_item", False, 3),
        section(4, "next_steps", False, 4),
    )
    body = {
        "schema_version": OIT_023_SCHEMA_VERSION,
        "engine_id": OIT_023_ENGINE_ID,
        "policy_id": OIT_023_POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root.resolve()),
        "query": "Build the terminal presentation view model.",
        "operator_brief_hash": "operator-brief-hash",
        "terminal_title": "Oracle Operator Decision Brief",
        "terminal_summary": "Synthetic terminal summary.",
        "sections": sections,
        "section_count": 5,
        "attention_section_count": 3,
        "source_item_count": 2,
        "primary_state": "abstain",
        "primary_direction": "bull",
        "consumption_ready": True,
        "rendering_allowed": True,
        "interactive_query_allowed": True,
        "read_only": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "publication_allowed": False,
        "qseries_execution_allowed": False,
        "action_authorization_allowed": False,
        "failure_reason": None,
    }
    contract = OracleTerminalBriefConsumptionContract(
        **body,
        contract_hash=oit_023_hash(body),
    )
    verify_terminal_brief_consumption_contract(contract)
    return contract


def main() -> int:
    print("=" * 48)
    print(" OIT-024 TEST")
    print(" TERMINAL DECISION BRIEF PRESENTATION VIEW MODEL")
    print("=" * 48)

    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        source = make_contract(root)
        view_model = build_terminal_presentation_view_model(
            root,
            source.query,
            consumption_contract=source,
        )

        assert view_model.consumption_contract_hash == source.contract_hash
        assert view_model.panel_count == 5
        assert view_model.critical_panel_count == 3
        assert view_model.warning_panel_count == 2
        assert view_model.informational_panel_count == 0
        assert view_model.operator_attention_count == 3
        assert view_model.status_label == "ABSTAIN"
        assert view_model.direction_label == "BULL"
        assert view_model.rendering_ready
        assert view_model.keyboard_navigation_ready
        assert view_model.expandable_evidence_ready

        severities = tuple(panel.severity for panel in view_model.panels)
        assert severities[:3] == ("critical", "critical", "critical")
        assert severities[3:] == ("warning", "warning")

        for panel in view_model.panels:
            assert panel.panel_label
            assert panel.content_lines
            assert panel.source_section_hash
            assert panel.read_only

        replay = build_terminal_presentation_view_model(
            root,
            source.query,
            consumption_contract=source,
        )
        assert replay == view_model
        assert verify_terminal_presentation_view_model(view_model)

        tampered = replace(
            view_model,
            terminal_subheading=view_model.terminal_subheading + " tampered",
        )
        try:
            verify_terminal_presentation_view_model(tampered)
        except OracleTerminalPresentationInvariantError:
            pass
        else:
            raise AssertionError("tampered terminal view model accepted")

        assert view_model.read_only
        assert not view_model.analytics_execution_performed
        assert not view_model.database_access_performed
        assert not view_model.publication_allowed
        assert not view_model.qseries_execution_allowed
        assert not view_model.action_authorization_allowed

    print("[PASS] Certified OIT-023 consumption contract consumed")
    print("[PASS] Terminal heading and subheading materialized")
    print("[PASS] Status and direction labels materialized")
    print("[PASS] Critical panels prioritized")
    print("[PASS] Warning panels ordered deterministically")
    print("[PASS] Operator-attention panels surfaced")
    print("[PASS] Keyboard navigation readiness certified")
    print("[PASS] Expandable evidence readiness certified")
    print("[PASS] Complete OIT-023 lineage retained")
    print("[PASS] Presentation view model deterministic across replay")
    print("[PASS] Tampered presentation view model rejected")
    print("[PASS] No analytics execution or database access performed")
    print("[PASS] Publication, action authorization, and Q Series execution disabled")
    print("[DONE] OIT-024 TERMINAL DECISION BRIEF PRESENTATION VIEW MODEL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
