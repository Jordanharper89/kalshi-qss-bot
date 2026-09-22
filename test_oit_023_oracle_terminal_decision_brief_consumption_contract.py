from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from qseries_v2.oracle_terminal.oracle_operator_decision_brief_assembly import (
    ENGINE_ID as OIT_022_ENGINE_ID,
    POLICY_ID as OIT_022_POLICY_ID,
    SCHEMA_VERSION as OIT_022_SCHEMA_VERSION,
    OracleOperatorDecisionBrief,
    OracleOperatorDecisionBriefItem,
    _stable_hash as oit_022_hash,
    verify_operator_decision_brief,
)
from qseries_v2.oracle_terminal.oracle_terminal_decision_brief_consumption_contract import (
    OracleTerminalBriefConsumptionInvariantError,
    build_terminal_brief_consumption_contract,
    verify_terminal_brief_consumption_contract,
)


def item(index: int, state: str, attention: bool):
    body = {
        "item_index": index,
        "cause_record_id": f"CAUSE-{index}",
        "effect_record_id": f"EFFECT-{index}",
        "source_explanation_hash": f"explanation-{index}",
        "readiness_state": state,
        "directional_interpretation": "bull" if state == "ready" else "non_actionable_bear",
        "headline": f"{state.upper()} ITEM",
        "explanation": f"{state} explanation",
        "evidence_points": ("evidence one", "evidence two"),
        "confirmation_actions": ("confirm persistence",),
        "blocking_conditions": ("lineage failure",),
        "operator_attention_required": attention,
        "presentation_priority": 1 if attention else 4,
        "read_only": True,
    }
    return OracleOperatorDecisionBriefItem(
        **body,
        item_hash=oit_022_hash(body),
    )


def make_brief(root: Path):
    items = (
        item(2, "abstain", True),
        item(1, "ready", False),
    )
    body = {
        "schema_version": OIT_022_SCHEMA_VERSION,
        "engine_id": OIT_022_ENGINE_ID,
        "policy_id": OIT_022_POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root.resolve()),
        "query": "Render the operator brief.",
        "explanation_report_hash": "explanation-report-hash",
        "brief_items": items,
        "item_count": 2,
        "ready_item_count": 1,
        "observe_item_count": 0,
        "abstain_item_count": 1,
        "operator_attention_count": 1,
        "primary_state": "abstain",
        "primary_direction": "bull",
        "brief_title": "Oracle Operator Decision Brief",
        "executive_summary": "One ready and one abstain item.",
        "operator_next_steps": ("confirm persistence",),
        "unresolved_blockers": ("lineage failure",),
        "terminal_consumption_ready": True,
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
    print("=" * 48)
    print(" OIT-023 TEST")
    print(" TERMINAL DECISION BRIEF CONSUMPTION CONTRACT")
    print("=" * 48)

    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        source = make_brief(root)
        contract = build_terminal_brief_consumption_contract(
            root,
            source.query,
            operator_brief=source,
        )

        assert contract.operator_brief_hash == source.brief_hash
        assert contract.source_item_count == 2
        assert contract.section_count == 5
        assert contract.attention_section_count == 3
        assert contract.primary_state == "abstain"
        assert contract.primary_direction == "bull"
        assert contract.consumption_ready
        assert contract.rendering_allowed
        assert contract.interactive_query_allowed

        types = tuple(section.section_type for section in contract.sections)
        assert types[0] == "executive_summary"
        assert "attention" in types
        assert "decision_item" in types
        assert "next_steps" in types
        assert "blockers" in types

        for section in contract.sections:
            assert section.title
            assert section.content_lines
            assert section.section_hash

        replay = build_terminal_brief_consumption_contract(
            root,
            source.query,
            operator_brief=source,
        )
        assert replay == contract
        assert verify_terminal_brief_consumption_contract(contract)

        tampered = replace(
            contract,
            terminal_summary=contract.terminal_summary + " tampered",
        )
        try:
            verify_terminal_brief_consumption_contract(tampered)
        except OracleTerminalBriefConsumptionInvariantError:
            pass
        else:
            raise AssertionError("tampered terminal contract accepted")

        assert contract.read_only
        assert not contract.analytics_execution_performed
        assert not contract.database_access_performed
        assert not contract.publication_allowed
        assert not contract.qseries_execution_allowed
        assert not contract.action_authorization_allowed

    print("[PASS] Certified OIT-022 operator brief consumed")
    print("[PASS] Executive summary section materialized")
    print("[PASS] Attention sections prioritized")
    print("[PASS] Decision-item sections materialized")
    print("[PASS] Next-step section materialized")
    print("[PASS] Blocker section materialized")
    print("[PASS] Terminal rendering allowed through read-only boundary")
    print("[PASS] Interactive read-only query allowed")
    print("[PASS] Complete OIT-022 lineage retained")
    print("[PASS] Consumption contract deterministic across replay")
    print("[PASS] Tampered consumption contract rejected")
    print("[PASS] No analytics execution or database access performed")
    print("[PASS] Publication, action authorization, and Q Series execution disabled")
    print("[DONE] OIT-023 TERMINAL DECISION BRIEF CONSUMPTION CONTRACT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
