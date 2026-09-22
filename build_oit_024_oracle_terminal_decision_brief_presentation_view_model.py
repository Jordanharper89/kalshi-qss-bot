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
            / "oracle_terminal_decision_brief_consumption_contract.py"
        )
        if required.is_file():
            return candidate
    raise SystemExit("[ERROR] Could not locate current Q Series repository.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"
OIT_023 = PACKAGE / "oracle_terminal_decision_brief_consumption_contract.py"
OIT_023_TEST = ROOT / "test_oit_023_oracle_terminal_decision_brief_consumption_contract.py"
PRODUCTION = PACKAGE / "oracle_terminal_decision_brief_presentation_view_model.py"
TEST = ROOT / "test_oit_024_oracle_terminal_decision_brief_presentation_view_model.py"
INIT = PACKAGE / "__init__.py"
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass\nfrom pathlib import Path\nfrom typing import Any, Mapping\n\nfrom .oracle_terminal_decision_brief_consumption_contract import (\n    OracleTerminalBriefConsumptionContract,\n    OracleTerminalBriefConsumptionInvariantError,\n    OracleTerminalBriefSection,\n    build_terminal_brief_consumption_contract,\n    verify_terminal_brief_consumption_contract,\n)\n\nSCHEMA_VERSION = "OIT-024"\nENGINE_ID = "OIT-024"\nPOLICY_ID = "oracle.terminal-decision-brief-presentation-view-model.v1"\n\n\nclass OracleTerminalPresentationInvariantError(\n    OracleTerminalBriefConsumptionInvariantError\n):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleTerminalPresentationPanel:\n    panel_index: int\n    panel_type: str\n    panel_label: str\n    severity: str\n    content_lines: tuple[str, ...]\n    source_section_hash: str\n    operator_attention_required: bool\n    display_order: int\n    read_only: bool\n    panel_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleTerminalPresentationViewModel:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    status: str\n    repository_root: str\n    query: str\n    consumption_contract_hash: str\n    terminal_heading: str\n    terminal_subheading: str\n    status_label: str\n    direction_label: str\n    panels: tuple[OracleTerminalPresentationPanel, ...]\n    panel_count: int\n    critical_panel_count: int\n    warning_panel_count: int\n    informational_panel_count: int\n    operator_attention_count: int\n    rendering_ready: bool\n    keyboard_navigation_ready: bool\n    expandable_evidence_ready: bool\n    read_only: bool\n    analytics_execution_performed: bool\n    database_access_performed: bool\n    publication_allowed: bool\n    qseries_execution_allowed: bool\n    action_authorization_allowed: bool\n    failure_reason: str | None\n    view_model_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if isinstance(value, Path):\n        return value.as_posix()\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    return repr(value)\n\n\ndef _stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=True,\n    ).encode("utf-8")\n    return hashlib.sha256(payload).hexdigest()\n\n\ndef _severity(section: OracleTerminalBriefSection) -> str:\n    if section.attention_required or section.section_type == "blockers":\n        return "critical"\n    if section.section_type in {"next_steps", "decision_item"}:\n        return "warning"\n    return "informational"\n\n\ndef _label(section: OracleTerminalBriefSection) -> str:\n    mapping = {\n        "executive_summary": "Executive Summary",\n        "attention": "Operator Attention",\n        "decision_item": "Decision Item",\n        "next_steps": "Next Steps",\n        "blockers": "Unresolved Blockers",\n    }\n    return mapping[section.section_type]\n\n\ndef _panel(\n    section: OracleTerminalBriefSection,\n    index: int,\n) -> OracleTerminalPresentationPanel:\n    severity = _severity(section)\n    priority_map = {\n        "critical": 1,\n        "warning": 2,\n        "informational": 3,\n    }\n    body = {\n        "panel_index": index,\n        "panel_type": section.section_type,\n        "panel_label": _label(section),\n        "severity": severity,\n        "content_lines": tuple(section.content_lines),\n        "source_section_hash": section.section_hash,\n        "operator_attention_required": section.attention_required,\n        "display_order": priority_map[severity],\n        "read_only": True,\n    }\n    return OracleTerminalPresentationPanel(\n        **body,\n        panel_hash=_stable_hash(body),\n    )\n\n\ndef verify_terminal_presentation_panel(\n    panel: OracleTerminalPresentationPanel,\n) -> bool:\n    body = asdict(panel)\n    supplied = body.pop("panel_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleTerminalPresentationInvariantError(\n            "terminal presentation panel hash mismatch"\n        )\n    if panel.severity not in {\n        "critical",\n        "warning",\n        "informational",\n    }:\n        raise OracleTerminalPresentationInvariantError(\n            "unsupported panel severity"\n        )\n    if not panel.panel_label or not panel.content_lines:\n        raise OracleTerminalPresentationInvariantError(\n            "panel presentation content missing"\n        )\n    if not panel.source_section_hash:\n        raise OracleTerminalPresentationInvariantError(\n            "panel source-section lineage missing"\n        )\n    if not panel.read_only:\n        raise OracleTerminalPresentationInvariantError(\n            "terminal presentation panel is not read-only"\n        )\n    if panel.display_order < 1:\n        raise OracleTerminalPresentationInvariantError(\n            "panel display order invalid"\n        )\n    return True\n\n\ndef build_terminal_presentation_view_model(\n    repository_root: str | Path,\n    query: str,\n    *,\n    consumption_contract: OracleTerminalBriefConsumptionContract | None = None,\n) -> OracleTerminalPresentationViewModel:\n    root = Path(repository_root).resolve()\n    source = consumption_contract\n    if source is None:\n        source = build_terminal_brief_consumption_contract(root, query)\n    verify_terminal_brief_consumption_contract(source)\n\n    generated = tuple(\n        _panel(section, index)\n        for index, section in enumerate(source.sections, start=1)\n    )\n    panels = tuple(\n        sorted(\n            generated,\n            key=lambda panel: (\n                panel.display_order,\n                panel.panel_index,\n                panel.panel_hash,\n            ),\n        )\n    )\n    for panel in panels:\n        verify_terminal_presentation_panel(panel)\n\n    critical = sum(panel.severity == "critical" for panel in panels)\n    warning = sum(panel.severity == "warning" for panel in panels)\n    informational = sum(\n        panel.severity == "informational" for panel in panels\n    )\n    attention = sum(\n        panel.operator_attention_required for panel in panels\n    )\n    rendering_ready = bool(\n        source.consumption_ready\n        and panels\n        and all(panel.source_section_hash for panel in panels)\n    )\n\n    body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root),\n        "query": str(query),\n        "consumption_contract_hash": source.contract_hash,\n        "terminal_heading": source.terminal_title,\n        "terminal_subheading": source.terminal_summary,\n        "status_label": source.primary_state.upper(),\n        "direction_label": source.primary_direction.upper(),\n        "panels": panels,\n        "panel_count": len(panels),\n        "critical_panel_count": critical,\n        "warning_panel_count": warning,\n        "informational_panel_count": informational,\n        "operator_attention_count": attention,\n        "rendering_ready": rendering_ready,\n        "keyboard_navigation_ready": rendering_ready,\n        "expandable_evidence_ready": rendering_ready,\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "publication_allowed": False,\n        "qseries_execution_allowed": False,\n        "action_authorization_allowed": False,\n        "failure_reason": None,\n    }\n    view_model = OracleTerminalPresentationViewModel(\n        **body,\n        view_model_hash=_stable_hash(body),\n    )\n    verify_terminal_presentation_view_model(view_model)\n    return view_model\n\n\ndef verify_terminal_presentation_view_model(\n    view_model: OracleTerminalPresentationViewModel,\n) -> bool:\n    body = asdict(view_model)\n    supplied = body.pop("view_model_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleTerminalPresentationInvariantError(\n            "terminal presentation view-model hash mismatch"\n        )\n    if view_model.schema_version != SCHEMA_VERSION:\n        raise OracleTerminalPresentationInvariantError("schema mismatch")\n    if view_model.policy_id != POLICY_ID:\n        raise OracleTerminalPresentationInvariantError("policy mismatch")\n    if not view_model.read_only:\n        raise OracleTerminalPresentationInvariantError(\n            "terminal presentation view-model is not read-only"\n        )\n    if (\n        view_model.analytics_execution_performed\n        or view_model.database_access_performed\n        or view_model.publication_allowed\n        or view_model.qseries_execution_allowed\n        or view_model.action_authorization_allowed\n    ):\n        raise OracleTerminalPresentationInvariantError(\n            "forbidden capability enabled"\n        )\n    if view_model.panel_count != len(view_model.panels):\n        raise OracleTerminalPresentationInvariantError(\n            "terminal presentation panel count mismatch"\n        )\n    counts = {\n        "critical": view_model.critical_panel_count,\n        "warning": view_model.warning_panel_count,\n        "informational": view_model.informational_panel_count,\n    }\n    for severity, expected in counts.items():\n        actual = sum(\n            panel.severity == severity for panel in view_model.panels\n        )\n        if actual != expected:\n            raise OracleTerminalPresentationInvariantError(\n                f"{severity} panel count mismatch"\n            )\n    if sum(counts.values()) != view_model.panel_count:\n        raise OracleTerminalPresentationInvariantError(\n            "classified panel count mismatch"\n        )\n    if view_model.operator_attention_count != sum(\n        panel.operator_attention_required for panel in view_model.panels\n    ):\n        raise OracleTerminalPresentationInvariantError(\n            "operator attention panel count mismatch"\n        )\n    for panel in view_model.panels:\n        verify_terminal_presentation_panel(panel)\n    expected = tuple(\n        sorted(\n            view_model.panels,\n            key=lambda panel: (\n                panel.display_order,\n                panel.panel_index,\n                panel.panel_hash,\n            ),\n        )\n    )\n    if view_model.panels != expected:\n        raise OracleTerminalPresentationInvariantError(\n            "terminal presentation panel ordering mismatch"\n        )\n    if (\n        view_model.rendering_ready\n        and (\n            not view_model.keyboard_navigation_ready\n            or not view_model.expandable_evidence_ready\n        )\n    ):\n        raise OracleTerminalPresentationInvariantError(\n            "rendering-ready view model missing interaction readiness"\n        )\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import replace\nfrom pathlib import Path\nfrom tempfile import TemporaryDirectory\n\nfrom qseries_v2.oracle_terminal.oracle_terminal_decision_brief_consumption_contract import (\n    ENGINE_ID as OIT_023_ENGINE_ID,\n    POLICY_ID as OIT_023_POLICY_ID,\n    SCHEMA_VERSION as OIT_023_SCHEMA_VERSION,\n    OracleTerminalBriefConsumptionContract,\n    OracleTerminalBriefSection,\n    _stable_hash as oit_023_hash,\n    verify_terminal_brief_consumption_contract,\n)\nfrom qseries_v2.oracle_terminal.oracle_terminal_decision_brief_presentation_view_model import (\n    OracleTerminalPresentationInvariantError,\n    build_terminal_presentation_view_model,\n    verify_terminal_presentation_view_model,\n)\n\n\ndef section(\n    index: int,\n    section_type: str,\n    attention: bool,\n    priority: int,\n):\n    body = {\n        "section_index": index,\n        "section_type": section_type,\n        "title": f"{section_type} title",\n        "content_lines": (f"{section_type} content",),\n        "source_item_hashes": (f"item-{index}",),\n        "attention_required": attention,\n        "display_priority": priority,\n    }\n    return OracleTerminalBriefSection(\n        **body,\n        section_hash=oit_023_hash(body),\n    )\n\n\ndef make_contract(root: Path):\n    sections = (\n        section(1, "executive_summary", True, 1),\n        section(2, "attention", True, 2),\n        section(5, "blockers", True, 2),\n        section(3, "decision_item", False, 3),\n        section(4, "next_steps", False, 4),\n    )\n    body = {\n        "schema_version": OIT_023_SCHEMA_VERSION,\n        "engine_id": OIT_023_ENGINE_ID,\n        "policy_id": OIT_023_POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root.resolve()),\n        "query": "Build the terminal presentation view model.",\n        "operator_brief_hash": "operator-brief-hash",\n        "terminal_title": "Oracle Operator Decision Brief",\n        "terminal_summary": "Synthetic terminal summary.",\n        "sections": sections,\n        "section_count": 5,\n        "attention_section_count": 3,\n        "source_item_count": 2,\n        "primary_state": "abstain",\n        "primary_direction": "bull",\n        "consumption_ready": True,\n        "rendering_allowed": True,\n        "interactive_query_allowed": True,\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "publication_allowed": False,\n        "qseries_execution_allowed": False,\n        "action_authorization_allowed": False,\n        "failure_reason": None,\n    }\n    contract = OracleTerminalBriefConsumptionContract(\n        **body,\n        contract_hash=oit_023_hash(body),\n    )\n    verify_terminal_brief_consumption_contract(contract)\n    return contract\n\n\ndef main() -> int:\n    print("=" * 48)\n    print(" OIT-024 TEST")\n    print(" TERMINAL DECISION BRIEF PRESENTATION VIEW MODEL")\n    print("=" * 48)\n\n    with TemporaryDirectory() as temporary:\n        root = Path(temporary)\n        source = make_contract(root)\n        view_model = build_terminal_presentation_view_model(\n            root,\n            source.query,\n            consumption_contract=source,\n        )\n\n        assert view_model.consumption_contract_hash == source.contract_hash\n        assert view_model.panel_count == 5\n        assert view_model.critical_panel_count == 3\n        assert view_model.warning_panel_count == 2\n        assert view_model.informational_panel_count == 0\n        assert view_model.operator_attention_count == 3\n        assert view_model.status_label == "ABSTAIN"\n        assert view_model.direction_label == "BULL"\n        assert view_model.rendering_ready\n        assert view_model.keyboard_navigation_ready\n        assert view_model.expandable_evidence_ready\n\n        severities = tuple(panel.severity for panel in view_model.panels)\n        assert severities[:3] == ("critical", "critical", "critical")\n        assert severities[3:] == ("warning", "warning")\n\n        for panel in view_model.panels:\n            assert panel.panel_label\n            assert panel.content_lines\n            assert panel.source_section_hash\n            assert panel.read_only\n\n        replay = build_terminal_presentation_view_model(\n            root,\n            source.query,\n            consumption_contract=source,\n        )\n        assert replay == view_model\n        assert verify_terminal_presentation_view_model(view_model)\n\n        tampered = replace(\n            view_model,\n            terminal_subheading=view_model.terminal_subheading + " tampered",\n        )\n        try:\n            verify_terminal_presentation_view_model(tampered)\n        except OracleTerminalPresentationInvariantError:\n            pass\n        else:\n            raise AssertionError("tampered terminal view model accepted")\n\n        assert view_model.read_only\n        assert not view_model.analytics_execution_performed\n        assert not view_model.database_access_performed\n        assert not view_model.publication_allowed\n        assert not view_model.qseries_execution_allowed\n        assert not view_model.action_authorization_allowed\n\n    print("[PASS] Certified OIT-023 consumption contract consumed")\n    print("[PASS] Terminal heading and subheading materialized")\n    print("[PASS] Status and direction labels materialized")\n    print("[PASS] Critical panels prioritized")\n    print("[PASS] Warning panels ordered deterministically")\n    print("[PASS] Operator-attention panels surfaced")\n    print("[PASS] Keyboard navigation readiness certified")\n    print("[PASS] Expandable evidence readiness certified")\n    print("[PASS] Complete OIT-023 lineage retained")\n    print("[PASS] Presentation view model deterministic across replay")\n    print("[PASS] Tampered presentation view model rejected")\n    print("[PASS] No analytics execution or database access performed")\n    print("[PASS] Publication, action authorization, and Q Series execution disabled")\n    print("[DONE] OIT-024 TERMINAL DECISION BRIEF PRESENTATION VIEW MODEL PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


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
    for path in (OIT_023, OIT_023_TEST, RUNNER):
        if path.is_file():
            protected[path] = sha256(path)
    return protected


def main() -> int:
    print("=" * 48)
    print(" OIT-024 INSTALLER")
    print(" TERMINAL DECISION BRIEF PRESENTATION VIEW MODEL")
    print("=" * 48)
    try:
        require_contract(
            OIT_023,
            (
                'SCHEMA_VERSION = "OIT-023"',
                'POLICY_ID = "oracle.terminal-decision-brief-consumption-contract.v1"',
                "OracleTerminalBriefConsumptionContract",
                "OracleTerminalBriefSection",
                "build_terminal_brief_consumption_contract",
                "verify_terminal_brief_consumption_contract",
                "consumption_ready",
                "rendering_allowed",
                "interactive_query_allowed",
                "action_authorization_allowed",
            ),
            "Certified OIT-023 production",
        )
        require_contract(
            OIT_023_TEST,
            (
                "OIT-023 TEST",
                "TERMINAL DECISION BRIEF CONSUMPTION CONTRACT",
                "OIT-023 TERMINAL DECISION BRIEF CONSUMPTION CONTRACT PASS",
            ),
            "Certified OIT-023 standalone test",
        )

        protected = protected_sources()
        print("[OK] Certified OIT-023 production contract verified")
        print("[OK] Certified OIT-023 standalone test verified")
        print(f"[OK] Protected production source files captured: {len(protected)}")

        upstream = subprocess.run(
            [sys.executable, str(OIT_023_TEST)],
            cwd=ROOT,
            check=False,
        )
        if upstream.returncode:
            raise RuntimeError(
                f"OIT-023 certification failed with exit code {upstream.returncode}"
            )

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_terminal_decision_brief_presentation_view_model import *"
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
                f"OIT-024 test failed with exit code {completed.returncode}"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Protected production source changed: {path}"
                )

        print("[PASS] Certified OIT-023 production and test unchanged")
        print("[PASS] Oracle terminal runner unchanged")
        print("[PASS] OLA, OIA, INT-OII, ORR, OOR, and Q Series unchanged")
        print("[PASS] OIT-024 production module installed")
        print("[PASS] OIT-024 standalone test installed")
        print("[PASS] Terminal presentation view model certified")
        print("[PASS] Attention-first panel ordering certified")
        print("[PASS] Read-only interaction readiness preserved")
        print("[PASS] Action authorization remained disabled")
        print("[PASS] Read-only and execution boundaries preserved")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OIT-024 TERMINAL DECISION BRIEF PRESENTATION VIEW MODEL INSTALLED")
        return 0
    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
