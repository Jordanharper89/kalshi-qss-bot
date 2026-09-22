from __future__ import annotations

import ast
import hashlib
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def locate_repository() -> Path:
    candidates = []
    for base in (Path.cwd().resolve(), SCRIPT_DIR):
        candidates.extend((base, base / "kalshi-qss-bot"))
        for parent in base.parents:
            candidates.extend((parent, parent / "kalshi-qss-bot"))
    seen = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        required = (
            candidate / "qseries_v2" / "oracle_terminal"
            / "oracle_operator_decision_brief_assembly.py"
        )
        if required.is_file():
            return candidate
    raise SystemExit("[ERROR] Could not locate current Q Series repository.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"
OIT_022 = PACKAGE / "oracle_operator_decision_brief_assembly.py"
OIT_022_TEST = ROOT / "test_oit_022_oracle_operator_decision_brief_assembly.py"
PRODUCTION = PACKAGE / "oracle_terminal_decision_brief_consumption_contract.py"
TEST = ROOT / "test_oit_023_oracle_terminal_decision_brief_consumption_contract.py"
INIT = PACKAGE / "__init__.py"
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass\nfrom pathlib import Path\nfrom typing import Any, Mapping\n\nfrom .oracle_operator_decision_brief_assembly import (\n    OracleOperatorDecisionBrief,\n    OracleOperatorDecisionBriefInvariantError,\n    OracleOperatorDecisionBriefItem,\n    build_operator_decision_brief,\n    verify_operator_decision_brief,\n)\n\nSCHEMA_VERSION = "OIT-023"\nENGINE_ID = "OIT-023"\nPOLICY_ID = "oracle.terminal-decision-brief-consumption-contract.v1"\n\n\nclass OracleTerminalBriefConsumptionInvariantError(\n    OracleOperatorDecisionBriefInvariantError\n):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleTerminalBriefSection:\n    section_index: int\n    section_type: str\n    title: str\n    content_lines: tuple[str, ...]\n    source_item_hashes: tuple[str, ...]\n    attention_required: bool\n    display_priority: int\n    section_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleTerminalBriefConsumptionContract:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    status: str\n    repository_root: str\n    query: str\n    operator_brief_hash: str\n    terminal_title: str\n    terminal_summary: str\n    sections: tuple[OracleTerminalBriefSection, ...]\n    section_count: int\n    attention_section_count: int\n    source_item_count: int\n    primary_state: str\n    primary_direction: str\n    consumption_ready: bool\n    rendering_allowed: bool\n    interactive_query_allowed: bool\n    read_only: bool\n    analytics_execution_performed: bool\n    database_access_performed: bool\n    publication_allowed: bool\n    qseries_execution_allowed: bool\n    action_authorization_allowed: bool\n    failure_reason: str | None\n    contract_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if isinstance(value, Path):\n        return value.as_posix()\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    return repr(value)\n\n\ndef _stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=True,\n    ).encode("utf-8")\n    return hashlib.sha256(payload).hexdigest()\n\n\ndef _section(\n    index: int,\n    section_type: str,\n    title: str,\n    lines: tuple[str, ...],\n    hashes: tuple[str, ...],\n    attention: bool,\n    priority: int,\n) -> OracleTerminalBriefSection:\n    body = {\n        "section_index": index,\n        "section_type": section_type,\n        "title": title,\n        "content_lines": lines,\n        "source_item_hashes": hashes,\n        "attention_required": attention,\n        "display_priority": priority,\n    }\n    return OracleTerminalBriefSection(\n        **body,\n        section_hash=_stable_hash(body),\n    )\n\n\ndef _item_lines(item: OracleOperatorDecisionBriefItem) -> tuple[str, ...]:\n    return (\n        item.headline,\n        item.explanation,\n        *(f"EVIDENCE: {line}" for line in item.evidence_points),\n        *(f"CONFIRM: {line}" for line in item.confirmation_actions),\n        *(f"BLOCKER: {line}" for line in item.blocking_conditions),\n    )\n\n\ndef verify_terminal_brief_section(\n    section: OracleTerminalBriefSection,\n) -> bool:\n    body = asdict(section)\n    supplied = body.pop("section_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleTerminalBriefConsumptionInvariantError(\n            "terminal section hash mismatch"\n        )\n    if section.section_type not in {\n        "executive_summary",\n        "attention",\n        "decision_item",\n        "next_steps",\n        "blockers",\n    }:\n        raise OracleTerminalBriefConsumptionInvariantError(\n            "unsupported terminal section type"\n        )\n    if not section.title or not section.content_lines:\n        raise OracleTerminalBriefConsumptionInvariantError(\n            "terminal section content missing"\n        )\n    if section.display_priority < 1:\n        raise OracleTerminalBriefConsumptionInvariantError(\n            "terminal section priority invalid"\n        )\n    return True\n\n\ndef build_terminal_brief_consumption_contract(\n    repository_root: str | Path,\n    query: str,\n    *,\n    operator_brief: OracleOperatorDecisionBrief | None = None,\n) -> OracleTerminalBriefConsumptionContract:\n    root = Path(repository_root).resolve()\n    source = operator_brief\n    if source is None:\n        source = build_operator_decision_brief(root, query)\n    verify_operator_decision_brief(source)\n\n    sections: list[OracleTerminalBriefSection] = []\n    sections.append(\n        _section(\n            1,\n            "executive_summary",\n            source.brief_title,\n            (source.executive_summary,),\n            tuple(item.item_hash for item in source.brief_items),\n            source.operator_attention_count > 0,\n            1,\n        )\n    )\n\n    next_index = 2\n    for item in source.brief_items:\n        section_type = (\n            "attention"\n            if item.operator_attention_required\n            else "decision_item"\n        )\n        sections.append(\n            _section(\n                next_index,\n                section_type,\n                item.headline,\n                _item_lines(item),\n                (item.item_hash,),\n                item.operator_attention_required,\n                2 if item.operator_attention_required else 3,\n            )\n        )\n        next_index += 1\n\n    if source.operator_next_steps:\n        sections.append(\n            _section(\n                next_index,\n                "next_steps",\n                "Operator Next Steps",\n                tuple(source.operator_next_steps),\n                tuple(item.item_hash for item in source.brief_items),\n                False,\n                4,\n            )\n        )\n        next_index += 1\n\n    if source.unresolved_blockers:\n        sections.append(\n            _section(\n                next_index,\n                "blockers",\n                "Unresolved Blockers",\n                tuple(source.unresolved_blockers),\n                tuple(item.item_hash for item in source.brief_items),\n                True,\n                2,\n            )\n        )\n\n    ordered = tuple(\n        sorted(\n            sections,\n            key=lambda section: (\n                section.display_priority,\n                section.section_index,\n                section.section_hash,\n            ),\n        )\n    )\n    for section in ordered:\n        verify_terminal_brief_section(section)\n\n    body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root),\n        "query": str(query),\n        "operator_brief_hash": source.brief_hash,\n        "terminal_title": source.brief_title,\n        "terminal_summary": source.executive_summary,\n        "sections": ordered,\n        "section_count": len(ordered),\n        "attention_section_count": sum(\n            section.attention_required for section in ordered\n        ),\n        "source_item_count": source.item_count,\n        "primary_state": source.primary_state,\n        "primary_direction": source.primary_direction,\n        "consumption_ready": bool(\n            source.terminal_consumption_ready and ordered\n        ),\n        "rendering_allowed": True,\n        "interactive_query_allowed": True,\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "publication_allowed": False,\n        "qseries_execution_allowed": False,\n        "action_authorization_allowed": False,\n        "failure_reason": None,\n    }\n    contract = OracleTerminalBriefConsumptionContract(\n        **body,\n        contract_hash=_stable_hash(body),\n    )\n    verify_terminal_brief_consumption_contract(contract)\n    return contract\n\n\ndef verify_terminal_brief_consumption_contract(\n    contract: OracleTerminalBriefConsumptionContract,\n) -> bool:\n    body = asdict(contract)\n    supplied = body.pop("contract_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleTerminalBriefConsumptionInvariantError(\n            "terminal consumption contract hash mismatch"\n        )\n    if contract.schema_version != SCHEMA_VERSION:\n        raise OracleTerminalBriefConsumptionInvariantError(\n            "schema mismatch"\n        )\n    if contract.policy_id != POLICY_ID:\n        raise OracleTerminalBriefConsumptionInvariantError(\n            "policy mismatch"\n        )\n    if not contract.read_only:\n        raise OracleTerminalBriefConsumptionInvariantError(\n            "terminal consumption contract is not read-only"\n        )\n    if (\n        contract.analytics_execution_performed\n        or contract.database_access_performed\n        or contract.publication_allowed\n        or contract.qseries_execution_allowed\n        or contract.action_authorization_allowed\n    ):\n        raise OracleTerminalBriefConsumptionInvariantError(\n            "forbidden capability enabled"\n        )\n    if not contract.rendering_allowed:\n        raise OracleTerminalBriefConsumptionInvariantError(\n            "terminal rendering must remain available"\n        )\n    if not contract.interactive_query_allowed:\n        raise OracleTerminalBriefConsumptionInvariantError(\n            "interactive read-only query must remain available"\n        )\n    if contract.section_count != len(contract.sections):\n        raise OracleTerminalBriefConsumptionInvariantError(\n            "terminal section count mismatch"\n        )\n    if contract.attention_section_count != sum(\n        section.attention_required for section in contract.sections\n    ):\n        raise OracleTerminalBriefConsumptionInvariantError(\n            "attention section count mismatch"\n        )\n    if contract.primary_state not in {"ready", "observe", "abstain"}:\n        raise OracleTerminalBriefConsumptionInvariantError(\n            "invalid primary state"\n        )\n    if contract.primary_direction not in {"bull", "bear", "neutral"}:\n        raise OracleTerminalBriefConsumptionInvariantError(\n            "invalid primary direction"\n        )\n    for section in contract.sections:\n        verify_terminal_brief_section(section)\n    expected = tuple(\n        sorted(\n            contract.sections,\n            key=lambda section: (\n                section.display_priority,\n                section.section_index,\n                section.section_hash,\n            ),\n        )\n    )\n    if contract.sections != expected:\n        raise OracleTerminalBriefConsumptionInvariantError(\n            "terminal section ordering mismatch"\n        )\n    if contract.consumption_ready and not contract.sections:\n        raise OracleTerminalBriefConsumptionInvariantError(\n            "empty contract marked consumption-ready"\n        )\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import replace\nfrom pathlib import Path\nfrom tempfile import TemporaryDirectory\n\nfrom qseries_v2.oracle_terminal.oracle_operator_decision_brief_assembly import (\n    ENGINE_ID as OIT_022_ENGINE_ID,\n    POLICY_ID as OIT_022_POLICY_ID,\n    SCHEMA_VERSION as OIT_022_SCHEMA_VERSION,\n    OracleOperatorDecisionBrief,\n    OracleOperatorDecisionBriefItem,\n    _stable_hash as oit_022_hash,\n    verify_operator_decision_brief,\n)\nfrom qseries_v2.oracle_terminal.oracle_terminal_decision_brief_consumption_contract import (\n    OracleTerminalBriefConsumptionInvariantError,\n    build_terminal_brief_consumption_contract,\n    verify_terminal_brief_consumption_contract,\n)\n\n\ndef item(index: int, state: str, attention: bool):\n    body = {\n        "item_index": index,\n        "cause_record_id": f"CAUSE-{index}",\n        "effect_record_id": f"EFFECT-{index}",\n        "source_explanation_hash": f"explanation-{index}",\n        "readiness_state": state,\n        "directional_interpretation": "bull" if state == "ready" else "non_actionable_bear",\n        "headline": f"{state.upper()} ITEM",\n        "explanation": f"{state} explanation",\n        "evidence_points": ("evidence one", "evidence two"),\n        "confirmation_actions": ("confirm persistence",),\n        "blocking_conditions": ("lineage failure",),\n        "operator_attention_required": attention,\n        "presentation_priority": 1 if attention else 4,\n        "read_only": True,\n    }\n    return OracleOperatorDecisionBriefItem(\n        **body,\n        item_hash=oit_022_hash(body),\n    )\n\n\ndef make_brief(root: Path):\n    items = (\n        item(2, "abstain", True),\n        item(1, "ready", False),\n    )\n    body = {\n        "schema_version": OIT_022_SCHEMA_VERSION,\n        "engine_id": OIT_022_ENGINE_ID,\n        "policy_id": OIT_022_POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root.resolve()),\n        "query": "Render the operator brief.",\n        "explanation_report_hash": "explanation-report-hash",\n        "brief_items": items,\n        "item_count": 2,\n        "ready_item_count": 1,\n        "observe_item_count": 0,\n        "abstain_item_count": 1,\n        "operator_attention_count": 1,\n        "primary_state": "abstain",\n        "primary_direction": "bull",\n        "brief_title": "Oracle Operator Decision Brief",\n        "executive_summary": "One ready and one abstain item.",\n        "operator_next_steps": ("confirm persistence",),\n        "unresolved_blockers": ("lineage failure",),\n        "terminal_consumption_ready": True,\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "publication_allowed": False,\n        "qseries_execution_allowed": False,\n        "action_authorization_allowed": False,\n        "failure_reason": None,\n    }\n    brief = OracleOperatorDecisionBrief(\n        **body,\n        brief_hash=oit_022_hash(body),\n    )\n    verify_operator_decision_brief(brief)\n    return brief\n\n\ndef main() -> int:\n    print("=" * 48)\n    print(" OIT-023 TEST")\n    print(" TERMINAL DECISION BRIEF CONSUMPTION CONTRACT")\n    print("=" * 48)\n\n    with TemporaryDirectory() as temporary:\n        root = Path(temporary)\n        source = make_brief(root)\n        contract = build_terminal_brief_consumption_contract(\n            root,\n            source.query,\n            operator_brief=source,\n        )\n\n        assert contract.operator_brief_hash == source.brief_hash\n        assert contract.source_item_count == 2\n        assert contract.section_count == 5\n        assert contract.attention_section_count == 3\n        assert contract.primary_state == "abstain"\n        assert contract.primary_direction == "bull"\n        assert contract.consumption_ready\n        assert contract.rendering_allowed\n        assert contract.interactive_query_allowed\n\n        types = tuple(section.section_type for section in contract.sections)\n        assert types[0] == "executive_summary"\n        assert "attention" in types\n        assert "decision_item" in types\n        assert "next_steps" in types\n        assert "blockers" in types\n\n        for section in contract.sections:\n            assert section.title\n            assert section.content_lines\n            assert section.section_hash\n\n        replay = build_terminal_brief_consumption_contract(\n            root,\n            source.query,\n            operator_brief=source,\n        )\n        assert replay == contract\n        assert verify_terminal_brief_consumption_contract(contract)\n\n        tampered = replace(\n            contract,\n            terminal_summary=contract.terminal_summary + " tampered",\n        )\n        try:\n            verify_terminal_brief_consumption_contract(tampered)\n        except OracleTerminalBriefConsumptionInvariantError:\n            pass\n        else:\n            raise AssertionError("tampered terminal contract accepted")\n\n        assert contract.read_only\n        assert not contract.analytics_execution_performed\n        assert not contract.database_access_performed\n        assert not contract.publication_allowed\n        assert not contract.qseries_execution_allowed\n        assert not contract.action_authorization_allowed\n\n    print("[PASS] Certified OIT-022 operator brief consumed")\n    print("[PASS] Executive summary section materialized")\n    print("[PASS] Attention sections prioritized")\n    print("[PASS] Decision-item sections materialized")\n    print("[PASS] Next-step section materialized")\n    print("[PASS] Blocker section materialized")\n    print("[PASS] Terminal rendering allowed through read-only boundary")\n    print("[PASS] Interactive read-only query allowed")\n    print("[PASS] Complete OIT-022 lineage retained")\n    print("[PASS] Consumption contract deterministic across replay")\n    print("[PASS] Tampered consumption contract rejected")\n    print("[PASS] No analytics execution or database access performed")\n    print("[PASS] Publication, action authorization, and Q Series execution disabled")\n    print("[DONE] OIT-023 TERMINAL DECISION BRIEF CONSUMPTION CONTRACT PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_complete(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def require_contract(path: Path, tokens: tuple[str, ...], label: str) -> None:
    if not path.is_file():
        raise RuntimeError(f"{label} missing: {path}")
    source = path.read_text(encoding="utf-8")
    missing = [token for token in tokens if token not in source]
    if missing:
        raise RuntimeError(f"{label} contract mismatch: {missing}")


def protected_sources() -> dict[Path, str]:
    protected = {}
    roots = (
        ROOT / "qseries_v2" / "oracle_intelligence" / "live_acquisition",
        ROOT / "qseries_v2" / "oracle_intelligence" / "analytics",
        ROOT / "qseries_v2" / "oracle_intelligence_integration",
        ROOT / "qseries_v2" / "oracle_research_runtime",
        ROOT / "qseries_v2" / "oracle_operator_runtime",
        ROOT / "qseries_v2" / "qseries",
    )
    for base in roots:
        if base.exists():
            for path in base.rglob("*.py"):
                if path.is_file():
                    protected[path] = sha256(path)
    for path in (OIT_022, OIT_022_TEST, RUNNER):
        if path.is_file():
            protected[path] = sha256(path)
    return protected


def main() -> int:
    print("=" * 48)
    print(" OIT-023 INSTALLER")
    print(" TERMINAL DECISION BRIEF CONSUMPTION CONTRACT")
    print("=" * 48)
    try:
        require_contract(
            OIT_022,
            (
                'SCHEMA_VERSION = "OIT-022"',
                'POLICY_ID = "oracle.operator-decision-brief-assembly.v1"',
                "OracleOperatorDecisionBrief",
                "OracleOperatorDecisionBriefItem",
                "build_operator_decision_brief",
                "verify_operator_decision_brief",
                "terminal_consumption_ready",
                "operator_next_steps",
                "unresolved_blockers",
                "action_authorization_allowed",
            ),
            "Certified OIT-022 production",
        )
        require_contract(
            OIT_022_TEST,
            (
                "OIT-022 TEST",
                "OPERATOR DECISION BRIEF ASSEMBLY",
                "OIT-022 OPERATOR DECISION BRIEF ASSEMBLY PASS",
            ),
            "Certified OIT-022 standalone test",
        )

        protected = protected_sources()
        print("[OK] Certified OIT-022 production contract verified")
        print("[OK] Certified OIT-022 standalone test verified")
        print(f"[OK] Protected production source files captured: {len(protected)}")

        upstream = subprocess.run(
            [sys.executable, str(OIT_022_TEST)],
            cwd=ROOT,
            check=False,
        )
        if upstream.returncode:
            raise RuntimeError(
                f"OIT-022 certification failed with exit code {upstream.returncode}"
            )

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_terminal_decision_brief_consumption_contract import *"
        )
        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"
            INIT.write_text(
                current + export + "\n",
                encoding="utf-8",
                newline="\n",
            )
            print(f"[OK] PACKAGE UPDATED: {INIT.resolve()}")
        else:
            print(f"[OK] PACKAGE EXPORT PRESENT: {INIT.resolve()}")
        ast.parse(INIT.read_text(encoding="utf-8"), filename=str(INIT))

        completed = subprocess.run(
            [sys.executable, str(TEST)],
            cwd=ROOT,
            check=False,
        )
        if completed.returncode:
            raise RuntimeError(
                f"OIT-023 test failed with exit code {completed.returncode}"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Protected production source changed: {path}"
                )

        print("[PASS] Certified OIT-022 production and test unchanged")
        print("[PASS] Oracle terminal runner unchanged")
        print("[PASS] OLA, OIA, INT-OII, ORR, OOR, and Q Series unchanged")
        print("[PASS] OIT-023 production module installed")
        print("[PASS] OIT-023 standalone test installed")
        print("[PASS] Terminal brief consumption contract certified")
        print("[PASS] Read-only rendering and interaction boundary prepared")
        print("[PASS] Action authorization remained disabled")
        print("[PASS] Read-only and execution boundaries preserved")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OIT-023 TERMINAL DECISION BRIEF CONSUMPTION CONTRACT INSTALLED")
        return 0
    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
