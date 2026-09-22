from __future__ import annotations

import ast
import hashlib
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def locate_repository() -> Path:
    candidates: list[Path] = []
    for base in (Path.cwd().resolve(), SCRIPT_DIR):
        candidates.extend((base, base / "kalshi-qss-bot"))
        for parent in base.parents:
            candidates.extend((parent, parent / "kalshi-qss-bot"))

    seen: set[Path] = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)

        package = candidate / "qseries_v2" / "oracle_terminal"
        target = (
            package
            / "oracle_terminal_decision_brief_consumption_contract.py"
        )
        freeze = (
            package
            / "oracle_terminal_final_freeze_and_completion.py"
        )
        freeze_test = (
            candidate
            / "test_oit_050_oracle_terminal_final_freeze_and_completion.py"
        )

        if target.is_file() and freeze.is_file() and freeze_test.is_file():
            return candidate

    raise SystemExit(
        "[ERROR] Could not locate current Q Series repository."
    )


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"

TARGET = (
    PACKAGE
    / "oracle_terminal_decision_brief_consumption_contract.py"
)
OIT_022 = (
    PACKAGE
    / "oracle_operator_decision_brief_assembly.py"
)
OIT_024 = (
    PACKAGE
    / "oracle_terminal_decision_brief_presentation_view_model.py"
)
OIT_025 = (
    PACKAGE
    / "oracle_terminal_decision_brief_renderer_contract.py"
)
OIT_026 = (
    PACKAGE
    / "oracle_terminal_renderer_invocation_output_activation_gate.py"
)
OIT_027 = (
    PACKAGE
    / "oracle_terminal_activated_output_display_session_gate.py"
)
OIT_050 = (
    PACKAGE
    / "oracle_terminal_final_freeze_and_completion.py"
)
OIT_050_TEST = (
    ROOT
    / "test_oit_050_oracle_terminal_final_freeze_and_completion.py"
)
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"

TEST = (
    ROOT
    / "test_oit_050_bounded_abstention_display_readiness_repair.py"
)

PRODUCTION_SOURCE = 'from __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass\nfrom pathlib import Path\nfrom typing import Any, Mapping\n\nfrom .oracle_operator_decision_brief_assembly import (\n    OracleOperatorDecisionBrief,\n    OracleOperatorDecisionBriefInvariantError,\n    OracleOperatorDecisionBriefItem,\n    build_operator_decision_brief,\n    verify_operator_decision_brief,\n)\n\nSCHEMA_VERSION = "OIT-023"\nENGINE_ID = "OIT-023"\nPOLICY_ID = "oracle.terminal-decision-brief-consumption-contract.v1"\n\n\nclass OracleTerminalBriefConsumptionInvariantError(\n    OracleOperatorDecisionBriefInvariantError\n):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleTerminalBriefSection:\n    section_index: int\n    section_type: str\n    title: str\n    content_lines: tuple[str, ...]\n    source_item_hashes: tuple[str, ...]\n    attention_required: bool\n    display_priority: int\n    section_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleTerminalBriefConsumptionContract:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    status: str\n    repository_root: str\n    query: str\n    operator_brief_hash: str\n    terminal_title: str\n    terminal_summary: str\n    sections: tuple[OracleTerminalBriefSection, ...]\n    section_count: int\n    attention_section_count: int\n    source_item_count: int\n    primary_state: str\n    primary_direction: str\n    consumption_ready: bool\n    rendering_allowed: bool\n    interactive_query_allowed: bool\n    read_only: bool\n    analytics_execution_performed: bool\n    database_access_performed: bool\n    publication_allowed: bool\n    qseries_execution_allowed: bool\n    action_authorization_allowed: bool\n    failure_reason: str | None\n    contract_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if isinstance(value, Path):\n        return value.as_posix()\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    return repr(value)\n\n\ndef _stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=True,\n    ).encode("utf-8")\n    return hashlib.sha256(payload).hexdigest()\n\n\ndef _section(\n    index: int,\n    section_type: str,\n    title: str,\n    lines: tuple[str, ...],\n    hashes: tuple[str, ...],\n    attention: bool,\n    priority: int,\n) -> OracleTerminalBriefSection:\n    body = {\n        "section_index": index,\n        "section_type": section_type,\n        "title": title,\n        "content_lines": lines,\n        "source_item_hashes": hashes,\n        "attention_required": attention,\n        "display_priority": priority,\n    }\n    return OracleTerminalBriefSection(\n        **body,\n        section_hash=_stable_hash(body),\n    )\n\n\ndef _item_lines(item: OracleOperatorDecisionBriefItem) -> tuple[str, ...]:\n    return (\n        item.headline,\n        item.explanation,\n        *(f"EVIDENCE: {line}" for line in item.evidence_points),\n        *(f"CONFIRM: {line}" for line in item.confirmation_actions),\n        *(f"BLOCKER: {line}" for line in item.blocking_conditions),\n    )\n\n\ndef verify_terminal_brief_section(\n    section: OracleTerminalBriefSection,\n) -> bool:\n    body = asdict(section)\n    supplied = body.pop("section_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleTerminalBriefConsumptionInvariantError(\n            "terminal section hash mismatch"\n        )\n    if section.section_type not in {\n        "executive_summary",\n        "attention",\n        "decision_item",\n        "next_steps",\n        "blockers",\n    }:\n        raise OracleTerminalBriefConsumptionInvariantError(\n            "unsupported terminal section type"\n        )\n    if not section.title or not section.content_lines:\n        raise OracleTerminalBriefConsumptionInvariantError(\n            "terminal section content missing"\n        )\n    if section.display_priority < 1:\n        raise OracleTerminalBriefConsumptionInvariantError(\n            "terminal section priority invalid"\n        )\n    return True\n\n\ndef build_terminal_brief_consumption_contract(\n    repository_root: str | Path,\n    query: str,\n    *,\n    operator_brief: OracleOperatorDecisionBrief | None = None,\n) -> OracleTerminalBriefConsumptionContract:\n    root = Path(repository_root).resolve()\n    source = operator_brief\n    if source is None:\n        source = build_operator_decision_brief(root, query)\n    verify_operator_decision_brief(source)\n\n    sections: list[OracleTerminalBriefSection] = []\n    sections.append(\n        _section(\n            1,\n            "executive_summary",\n            source.brief_title,\n            (source.executive_summary,),\n            tuple(item.item_hash for item in source.brief_items),\n            source.operator_attention_count > 0,\n            1,\n        )\n    )\n\n    next_index = 2\n    for item in source.brief_items:\n        section_type = (\n            "attention"\n            if item.operator_attention_required\n            else "decision_item"\n        )\n        sections.append(\n            _section(\n                next_index,\n                section_type,\n                item.headline,\n                _item_lines(item),\n                (item.item_hash,),\n                item.operator_attention_required,\n                2 if item.operator_attention_required else 3,\n            )\n        )\n        next_index += 1\n\n    if source.operator_next_steps:\n        sections.append(\n            _section(\n                next_index,\n                "next_steps",\n                "Operator Next Steps",\n                tuple(source.operator_next_steps),\n                tuple(item.item_hash for item in source.brief_items),\n                False,\n                4,\n            )\n        )\n        next_index += 1\n\n    if source.unresolved_blockers:\n        sections.append(\n            _section(\n                next_index,\n                "blockers",\n                "Unresolved Blockers",\n                tuple(source.unresolved_blockers),\n                tuple(item.item_hash for item in source.brief_items),\n                True,\n                2,\n            )\n        )\n\n    ordered = tuple(\n        sorted(\n            sections,\n            key=lambda section: (\n                section.display_priority,\n                section.section_index,\n                section.section_hash,\n            ),\n        )\n    )\n    for section in ordered:\n        verify_terminal_brief_section(section)\n\n    body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root),\n        "query": str(query),\n        "operator_brief_hash": source.brief_hash,\n        "terminal_title": source.brief_title,\n        "terminal_summary": source.executive_summary,\n        "sections": ordered,\n        "section_count": len(ordered),\n        "attention_section_count": sum(\n            section.attention_required for section in ordered\n        ),\n        "source_item_count": source.item_count,\n        "primary_state": source.primary_state,\n        "primary_direction": source.primary_direction,\n        "consumption_ready": bool(\n            ordered\n            and (\n                source.terminal_consumption_ready\n                or (\n                    source.item_count == 0\n                    and source.primary_state == "abstain"\n                    and source.primary_direction == "neutral"\n                    and ordered[0].section_type == "executive_summary"\n                    and bool(source.executive_summary)\n                )\n            )\n        ),\n        "rendering_allowed": True,\n        "interactive_query_allowed": True,\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "publication_allowed": False,\n        "qseries_execution_allowed": False,\n        "action_authorization_allowed": False,\n        "failure_reason": None,\n    }\n    contract = OracleTerminalBriefConsumptionContract(\n        **body,\n        contract_hash=_stable_hash(body),\n    )\n    verify_terminal_brief_consumption_contract(contract)\n    return contract\n\n\ndef verify_terminal_brief_consumption_contract(\n    contract: OracleTerminalBriefConsumptionContract,\n) -> bool:\n    body = asdict(contract)\n    supplied = body.pop("contract_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleTerminalBriefConsumptionInvariantError(\n            "terminal consumption contract hash mismatch"\n        )\n    if contract.schema_version != SCHEMA_VERSION:\n        raise OracleTerminalBriefConsumptionInvariantError(\n            "schema mismatch"\n        )\n    if contract.policy_id != POLICY_ID:\n        raise OracleTerminalBriefConsumptionInvariantError(\n            "policy mismatch"\n        )\n    if not contract.read_only:\n        raise OracleTerminalBriefConsumptionInvariantError(\n            "terminal consumption contract is not read-only"\n        )\n    if (\n        contract.analytics_execution_performed\n        or contract.database_access_performed\n        or contract.publication_allowed\n        or contract.qseries_execution_allowed\n        or contract.action_authorization_allowed\n    ):\n        raise OracleTerminalBriefConsumptionInvariantError(\n            "forbidden capability enabled"\n        )\n    if not contract.rendering_allowed:\n        raise OracleTerminalBriefConsumptionInvariantError(\n            "terminal rendering must remain available"\n        )\n    if not contract.interactive_query_allowed:\n        raise OracleTerminalBriefConsumptionInvariantError(\n            "interactive read-only query must remain available"\n        )\n    if contract.section_count != len(contract.sections):\n        raise OracleTerminalBriefConsumptionInvariantError(\n            "terminal section count mismatch"\n        )\n    if contract.attention_section_count != sum(\n        section.attention_required for section in contract.sections\n    ):\n        raise OracleTerminalBriefConsumptionInvariantError(\n            "attention section count mismatch"\n        )\n    if contract.primary_state not in {"ready", "observe", "abstain"}:\n        raise OracleTerminalBriefConsumptionInvariantError(\n            "invalid primary state"\n        )\n    if contract.primary_direction not in {"bull", "bear", "neutral"}:\n        raise OracleTerminalBriefConsumptionInvariantError(\n            "invalid primary direction"\n        )\n    for section in contract.sections:\n        verify_terminal_brief_section(section)\n    expected = tuple(\n        sorted(\n            contract.sections,\n            key=lambda section: (\n                section.display_priority,\n                section.section_index,\n                section.section_hash,\n            ),\n        )\n    )\n    if contract.sections != expected:\n        raise OracleTerminalBriefConsumptionInvariantError(\n            "terminal section ordering mismatch"\n        )\n    if contract.consumption_ready and not contract.sections:\n        raise OracleTerminalBriefConsumptionInvariantError(\n            "empty contract marked consumption-ready"\n        )\n\n    bounded_zero_item_abstention = bool(\n        contract.source_item_count == 0\n        and contract.primary_state == "abstain"\n        and contract.primary_direction == "neutral"\n        and contract.sections\n        and contract.sections[0].section_type == "executive_summary"\n        and bool(contract.terminal_summary)\n    )\n\n    if (\n        contract.consumption_ready\n        and contract.source_item_count == 0\n        and not bounded_zero_item_abstention\n    ):\n        raise OracleTerminalBriefConsumptionInvariantError(\n            "unsupported zero-item contract marked consumption-ready"\n        )\n\n    if bounded_zero_item_abstention and not contract.consumption_ready:\n        raise OracleTerminalBriefConsumptionInvariantError(\n            "bounded abstention contract must remain displayable"\n        )\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom pathlib import Path\nfrom tempfile import TemporaryDirectory\n\nfrom qseries_v2.oracle_terminal.oracle_operator_decision_brief_assembly import (\n    ENGINE_ID as OIT_022_ENGINE_ID,\n    POLICY_ID as OIT_022_POLICY_ID,\n    SCHEMA_VERSION as OIT_022_SCHEMA_VERSION,\n    OracleOperatorDecisionBrief,\n    _stable_hash as oit_022_hash,\n    verify_operator_decision_brief,\n)\nfrom qseries_v2.oracle_terminal.oracle_terminal_decision_brief_consumption_contract import (\n    build_terminal_brief_consumption_contract,\n    verify_terminal_brief_consumption_contract,\n)\nfrom qseries_v2.oracle_terminal.oracle_terminal_decision_brief_presentation_view_model import (\n    build_terminal_presentation_view_model,\n    verify_terminal_presentation_view_model,\n)\nfrom qseries_v2.oracle_terminal.oracle_terminal_decision_brief_renderer_contract import (\n    build_terminal_renderer_contract,\n    verify_terminal_renderer_contract,\n)\nfrom qseries_v2.oracle_terminal.oracle_terminal_renderer_invocation_output_activation_gate import (\n    build_terminal_renderer_activation_gate_report,\n    verify_terminal_renderer_activation_gate_report,\n)\nfrom qseries_v2.oracle_terminal.oracle_terminal_activated_output_display_session_gate import (\n    build_terminal_display_session_gate_report,\n    verify_terminal_display_session_gate_report,\n)\n\n\nQUERY = (\n    "what is the current direction of solana, "\n    "what evidence supports it"\n)\n\n\ndef make_zero_item_brief(\n    root: Path,\n    *,\n    state: str = "abstain",\n    direction: str = "neutral",\n) -> OracleOperatorDecisionBrief:\n    summary = (\n        "0 items assembled: 0 ready, 0 observe, 0 abstain; "\n        "0 require operator attention. "\n        "This brief is explanatory only and cannot authorize action."\n    )\n    body = {\n        "schema_version": OIT_022_SCHEMA_VERSION,\n        "engine_id": OIT_022_ENGINE_ID,\n        "policy_id": OIT_022_POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root.resolve()),\n        "query": QUERY,\n        "explanation_report_hash": "explanation-report-abstention-v3",\n        "brief_items": (),\n        "item_count": 0,\n        "ready_item_count": 0,\n        "observe_item_count": 0,\n        "abstain_item_count": 0,\n        "operator_attention_count": 0,\n        "primary_state": state,\n        "primary_direction": direction,\n        "brief_title": (\n            f"Oracle Operator Decision Brief — "\n            f"{state.upper()} / {direction.upper()}"\n        ),\n        "executive_summary": summary,\n        "operator_next_steps": (),\n        "unresolved_blockers": (),\n        "terminal_consumption_ready": False,\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "publication_allowed": False,\n        "qseries_execution_allowed": False,\n        "action_authorization_allowed": False,\n        "failure_reason": None,\n    }\n    brief = OracleOperatorDecisionBrief(\n        **body,\n        brief_hash=oit_022_hash(body),\n    )\n    verify_operator_decision_brief(brief)\n    return brief\n\n\ndef main() -> int:\n    print("=" * 60)\n    print(" OIT-050 DEFECT CORRECTION TEST")\n    print(" BOUNDED ABSTENTION DISPLAY READINESS REPAIR")\n    print("=" * 60)\n\n    with TemporaryDirectory() as temporary:\n        root = Path(temporary)\n\n        brief = make_zero_item_brief(root)\n\n        contract = build_terminal_brief_consumption_contract(\n            root,\n            QUERY,\n            operator_brief=brief,\n        )\n        assert contract.source_item_count == 0\n        assert contract.primary_state == "abstain"\n        assert contract.primary_direction == "neutral"\n        assert contract.section_count == 1\n        assert contract.sections[0].section_type == "executive_summary"\n        assert contract.consumption_ready\n        assert contract.rendering_allowed\n        assert contract.interactive_query_allowed\n        assert verify_terminal_brief_consumption_contract(contract)\n\n        view_model = build_terminal_presentation_view_model(\n            root,\n            QUERY,\n            consumption_contract=contract,\n        )\n        assert view_model.panel_count == 1\n        assert view_model.informational_panel_count == 1\n        assert view_model.status_label == "ABSTAIN"\n        assert view_model.direction_label == "NEUTRAL"\n        assert view_model.rendering_ready\n        assert view_model.keyboard_navigation_ready\n        assert view_model.expandable_evidence_ready\n        assert verify_terminal_presentation_view_model(view_model)\n\n        renderer = build_terminal_renderer_contract(\n            root,\n            QUERY,\n            presentation_view_model=view_model,\n        )\n        assert renderer.block_count == 1\n        assert renderer.informational_block_count == 1\n        assert renderer.renderer_ready\n        assert renderer.terminal_output_lines\n        assert any(\n            "STATUS: ABSTAIN | DIRECTION: NEUTRAL" in line\n            for line in renderer.terminal_output_lines\n        )\n        assert any(\n            "0 items assembled" in line\n            for line in renderer.terminal_output_lines\n        )\n        assert verify_terminal_renderer_contract(renderer)\n\n        activation = build_terminal_renderer_activation_gate_report(\n            root,\n            QUERY,\n            renderer_contract=renderer,\n        )\n        assert activation.invocation_authorized\n        assert activation.output_activated\n        assert activation.display_ready\n        assert activation.renderer_activation_ready\n        assert verify_terminal_renderer_activation_gate_report(\n            activation\n        )\n\n        display = build_terminal_display_session_gate_report(\n            root,\n            QUERY,\n            activation_report=activation,\n        )\n        assert display.session_open\n        assert display.display_ready\n        assert display.output_preserved_exactly\n        assert display.display_session_ready\n        assert verify_terminal_display_session_gate_report(display)\n\n        replay_contract = build_terminal_brief_consumption_contract(\n            root,\n            QUERY,\n            operator_brief=brief,\n        )\n        replay_view = build_terminal_presentation_view_model(\n            root,\n            QUERY,\n            consumption_contract=replay_contract,\n        )\n        replay_renderer = build_terminal_renderer_contract(\n            root,\n            QUERY,\n            presentation_view_model=replay_view,\n        )\n        replay_activation = build_terminal_renderer_activation_gate_report(\n            root,\n            QUERY,\n            renderer_contract=replay_renderer,\n        )\n        replay_display = build_terminal_display_session_gate_report(\n            root,\n            QUERY,\n            activation_report=replay_activation,\n        )\n\n        assert replay_contract == contract\n        assert replay_view == view_model\n        assert replay_renderer == renderer\n        assert replay_activation == activation\n        assert replay_display == display\n\n        unsafe_brief = make_zero_item_brief(\n            root,\n            state="abstain",\n            direction="bull",\n        )\n        unsafe_contract = build_terminal_brief_consumption_contract(\n            root,\n            QUERY,\n            operator_brief=unsafe_brief,\n        )\n        assert not unsafe_contract.consumption_ready\n\n    print("[PASS] Valid zero-item ABSTAIN / NEUTRAL brief consumed")\n    print("[PASS] Executive-summary section retained")\n    print("[PASS] OIT-023 consumption readiness repaired")\n    print("[PASS] OIT-024 informational panel rendering ready")\n    print("[PASS] OIT-025 renderer ready")\n    print("[PASS] OIT-026 output activation ready")\n    print("[PASS] OIT-027 display session ready")\n    print("[PASS] Exact terminal output preserved")\n    print("[PASS] Zero-item non-neutral case remained blocked")\n    print("[PASS] Full readiness chain deterministic across replay")\n    print("[PASS] Read-only and interactive boundaries preserved")\n    print("[PASS] Publication and Q Series execution remained disabled")\n    print("[DONE] OIT-050 BOUNDED ABSTENTION DISPLAY REPAIR PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'

OLD_READINESS = (
    "source.terminal_consumption_ready and ordered"
)
NEW_ABSTENTION_RULE = (
    'source.primary_state == "abstain"'
)
NEW_NEUTRAL_RULE = (
    'source.primary_direction == "neutral"'
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_contract(
    path: Path,
    tokens: tuple[str, ...],
    label: str,
) -> None:
    if not path.is_file():
        raise RuntimeError(f"{label} missing: {path}")

    source = path.read_text(encoding="utf-8")
    missing = [token for token in tokens if token not in source]
    if missing:
        raise RuntimeError(
            f"{label} contract mismatch: {missing}"
        )


def write_complete(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        source.lstrip(),
        encoding="utf-8",
        newline="\n",
    )
    ast.parse(
        path.read_text(encoding="utf-8"),
        filename=str(path),
    )
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def protected_sources() -> dict[Path, str]:
    protected: dict[Path, str] = {}

    for path in (ROOT / "qseries_v2").rglob("*.py"):
        if path.is_file() and path.resolve() != TARGET.resolve():
            protected[path.resolve()] = sha256(path)

    for path in (RUNNER, OIT_050_TEST):
        if path.is_file():
            protected[path.resolve()] = sha256(path)

    return protected


def main() -> int:
    print("=" * 60)
    print(" OIT-050 CORRECTION V3 INSTALLER")
    print(" BOUNDED ABSTENTION DISPLAY READINESS REPAIR")
    print("=" * 60)

    try:
        require_contract(
            TARGET,
            (
                'SCHEMA_VERSION = "OIT-023"',
                'POLICY_ID = "oracle.terminal-decision-brief-consumption-contract.v1"',
                OLD_READINESS,
                "empty contract marked consumption-ready",
                "rendering_allowed",
                "interactive_query_allowed",
            ),
            "Current OIT-023 consumption contract",
        )

        require_contract(
            OIT_022,
            (
                'SCHEMA_VERSION = "OIT-022"',
                "OracleOperatorDecisionBrief",
                "terminal_consumption_ready",
                "primary_state",
                "primary_direction",
            ),
            "Certified OIT-022 operator brief contract",
        )

        require_contract(
            OIT_024,
            (
                'SCHEMA_VERSION = "OIT-024"',
                "source.consumption_ready",
                "rendering_ready",
                "informational_panel_count",
            ),
            "Certified OIT-024 presentation contract",
        )

        require_contract(
            OIT_025,
            (
                'SCHEMA_VERSION = "OIT-025"',
                "source.rendering_ready",
                "renderer_ready",
                "terminal_output_lines",
            ),
            "Certified OIT-025 renderer contract",
        )

        require_contract(
            OIT_026,
            (
                'SCHEMA_VERSION = "OIT-026"',
                "renderer_activation_ready",
                "output_activated",
                "display_ready",
            ),
            "Certified OIT-026 activation contract",
        )

        require_contract(
            OIT_027,
            (
                'SCHEMA_VERSION = "OIT-027"',
                "display_session_ready",
                "output_preserved_exactly",
                "session_open",
            ),
            "Certified OIT-027 display-session contract",
        )

        require_contract(
            OIT_050,
            (
                'SCHEMA_VERSION = "OIT-050"',
                "correction_builds_allowed_only_for_defects",
                "no_further_oit_feature_layers_required",
            ),
            "Certified OIT-050 freeze contract",
        )

        protected = protected_sources()
        target_before = sha256(TARGET)

        print("[OK] Exact OIT-023 readiness defect located")
        print("[OK] OIT-024 through OIT-027 downstream contracts verified")
        print("[OK] Certified OIT-050 defect-correction permission verified")
        print("[OK] Current frozen repository state accepted")
        print(
            f"[OK] Protected source files captured: "
            f"{len(protected)}"
        )

        pre_freeze = subprocess.run(
            [sys.executable, str(OIT_050_TEST)],
            cwd=ROOT,
            check=False,
        )
        if pre_freeze.returncode:
            raise RuntimeError(
                "Pre-repair OIT-050 certification failed with exit code "
                f"{pre_freeze.returncode}"
            )

        write_complete(TARGET, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        installed = TARGET.read_text(encoding="utf-8")
        if OLD_READINESS in installed:
            raise RuntimeError(
                "Old strict readiness expression remains installed"
            )
        if NEW_ABSTENTION_RULE not in installed:
            raise RuntimeError(
                "Bounded abstention rule missing"
            )
        if NEW_NEUTRAL_RULE not in installed:
            raise RuntimeError(
                "Neutral-direction restriction missing"
            )

        regression = subprocess.run(
            [sys.executable, str(TEST)],
            cwd=ROOT,
            check=False,
        )
        if regression.returncode:
            raise RuntimeError(
                "Bounded-abstention regression test failed with exit code "
                f"{regression.returncode}"
            )

        post_freeze = subprocess.run(
            [sys.executable, str(OIT_050_TEST)],
            cwd=ROOT,
            check=False,
        )
        if post_freeze.returncode:
            raise RuntimeError(
                "Post-repair OIT-050 certification failed with exit code "
                f"{post_freeze.returncode}"
            )

        if sha256(TARGET) == target_before:
            raise RuntimeError(
                "OIT-023 target module was not replaced"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Protected source changed: {path}"
                )

        print("[PASS] Entire OIT-023 consumption module replaced")
        print("[PASS] Zero-item ABSTAIN / NEUTRAL display path certified")
        print("[PASS] Non-neutral zero-item output remains blocked")
        print("[PASS] OIT-024 through OIT-027 unchanged")
        print("[PASS] Frozen OIT-050 test passed before repair")
        print("[PASS] Frozen OIT-050 test passed after repair")
        print("[PASS] Live Oracle terminal runner unchanged")
        print("[PASS] All non-defect Q Series sources unchanged")
        print("[PASS] Read-only and interactive boundaries preserved")
        print("[PASS] Publication and Q Series execution remained disabled")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OIT-050 CORRECTION V3 DISPLAY REPAIR INSTALLED")
        return 0

    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
