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
            / "oracle_decision_explanation_evidence_trace_intelligence.py"
        )
        if required.is_file():
            return candidate
    raise SystemExit("[ERROR] Could not locate current Q Series repository.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"
OIT_021 = PACKAGE / "oracle_decision_explanation_evidence_trace_intelligence.py"
OIT_021_TEST = ROOT / "test_oit_021_oracle_decision_explanation_evidence_trace_intelligence.py"
PRODUCTION = PACKAGE / "oracle_operator_decision_brief_assembly.py"
TEST = ROOT / "test_oit_022_oracle_operator_decision_brief_assembly.py"
INIT = PACKAGE / "__init__.py"
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass\nfrom pathlib import Path\nfrom typing import Any, Mapping\n\nfrom .oracle_decision_explanation_evidence_trace_intelligence import (\n    OracleDecisionExplanationFinding,\n    OracleDecisionExplanationInvariantError,\n    OracleDecisionExplanationReport,\n    build_decision_explanation_report,\n    verify_decision_explanation_report,\n)\n\nSCHEMA_VERSION = "OIT-022"\nENGINE_ID = "OIT-022"\nPOLICY_ID = "oracle.operator-decision-brief-assembly.v1"\n\n\nclass OracleOperatorDecisionBriefInvariantError(\n    OracleDecisionExplanationInvariantError\n):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleOperatorDecisionBriefItem:\n    item_index: int\n    cause_record_id: str\n    effect_record_id: str\n    source_explanation_hash: str\n    readiness_state: str\n    directional_interpretation: str\n    headline: str\n    explanation: str\n    evidence_points: tuple[str, ...]\n    confirmation_actions: tuple[str, ...]\n    blocking_conditions: tuple[str, ...]\n    operator_attention_required: bool\n    presentation_priority: int\n    read_only: bool\n    item_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleOperatorDecisionBrief:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    status: str\n    repository_root: str\n    query: str\n    explanation_report_hash: str\n    brief_items: tuple[OracleOperatorDecisionBriefItem, ...]\n    item_count: int\n    ready_item_count: int\n    observe_item_count: int\n    abstain_item_count: int\n    operator_attention_count: int\n    primary_state: str\n    primary_direction: str\n    brief_title: str\n    executive_summary: str\n    operator_next_steps: tuple[str, ...]\n    unresolved_blockers: tuple[str, ...]\n    terminal_consumption_ready: bool\n    read_only: bool\n    analytics_execution_performed: bool\n    database_access_performed: bool\n    publication_allowed: bool\n    qseries_execution_allowed: bool\n    action_authorization_allowed: bool\n    failure_reason: str | None\n    brief_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if isinstance(value, Path):\n        return value.as_posix()\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    return repr(value)\n\n\ndef _stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=True,\n    ).encode("utf-8")\n    return hashlib.sha256(payload).hexdigest()\n\n\ndef _headline(source: OracleDecisionExplanationFinding) -> str:\n    direction = source.directional_interpretation.replace("_", " ").title()\n    if source.readiness_state == "ready":\n        return f"READY — {direction}"\n    if source.readiness_state == "observe":\n        return f"OBSERVE — {direction}"\n    return f"ABSTAIN — {direction}"\n\n\ndef _priority(source: OracleDecisionExplanationFinding) -> int:\n    if source.readiness_state == "abstain":\n        return 1\n    if source.operator_attention_required:\n        return 2\n    if source.readiness_state == "observe":\n        return 3\n    return 4\n\n\ndef _build_item(\n    source: OracleDecisionExplanationFinding,\n    index: int,\n) -> OracleOperatorDecisionBriefItem:\n    evidence = tuple(\n        trace.evidence_statement for trace in source.evidence_trace\n    )\n    body = {\n        "item_index": index,\n        "cause_record_id": source.cause_record_id,\n        "effect_record_id": source.effect_record_id,\n        "source_explanation_hash": source.finding_hash,\n        "readiness_state": source.readiness_state,\n        "directional_interpretation": source.directional_interpretation,\n        "headline": _headline(source),\n        "explanation": source.concise_explanation,\n        "evidence_points": evidence,\n        "confirmation_actions": tuple(source.confirmation_plan),\n        "blocking_conditions": tuple(source.blocking_conditions),\n        "operator_attention_required": source.operator_attention_required,\n        "presentation_priority": _priority(source),\n        "read_only": True,\n    }\n    return OracleOperatorDecisionBriefItem(\n        **body,\n        item_hash=_stable_hash(body),\n    )\n\n\ndef verify_operator_decision_brief_item(\n    item: OracleOperatorDecisionBriefItem,\n) -> bool:\n    body = asdict(item)\n    supplied = body.pop("item_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleOperatorDecisionBriefInvariantError(\n            "operator decision brief item hash mismatch"\n        )\n    if not item.read_only:\n        raise OracleOperatorDecisionBriefInvariantError(\n            "operator decision brief item is not read-only"\n        )\n    if item.readiness_state not in {"ready", "observe", "abstain"}:\n        raise OracleOperatorDecisionBriefInvariantError(\n            "unsupported brief readiness state"\n        )\n    if not item.source_explanation_hash:\n        raise OracleOperatorDecisionBriefInvariantError(\n            "explanation lineage missing"\n        )\n    if not item.headline or not item.explanation:\n        raise OracleOperatorDecisionBriefInvariantError(\n            "brief presentation content missing"\n        )\n    if not item.evidence_points:\n        raise OracleOperatorDecisionBriefInvariantError(\n            "brief evidence points missing"\n        )\n    if not item.confirmation_actions:\n        raise OracleOperatorDecisionBriefInvariantError(\n            "brief confirmation actions missing"\n        )\n    if not item.blocking_conditions:\n        raise OracleOperatorDecisionBriefInvariantError(\n            "brief blocking conditions missing"\n        )\n    if item.presentation_priority < 1:\n        raise OracleOperatorDecisionBriefInvariantError(\n            "brief presentation priority invalid"\n        )\n    return True\n\n\ndef _aggregate_next_steps(\n    items: tuple[OracleOperatorDecisionBriefItem, ...],\n) -> tuple[str, ...]:\n    collected: list[str] = []\n    seen: set[str] = set()\n    for item in items:\n        for action in item.confirmation_actions:\n            if action not in seen:\n                seen.add(action)\n                collected.append(action)\n    return tuple(collected)\n\n\ndef _aggregate_blockers(\n    items: tuple[OracleOperatorDecisionBriefItem, ...],\n) -> tuple[str, ...]:\n    collected: list[str] = []\n    seen: set[str] = set()\n    for item in items:\n        if item.readiness_state == "ready":\n            continue\n        for blocker in item.blocking_conditions:\n            if blocker not in seen:\n                seen.add(blocker)\n                collected.append(blocker)\n    return tuple(collected)\n\n\ndef build_operator_decision_brief(\n    repository_root: str | Path,\n    query: str,\n    *,\n    explanation_report: OracleDecisionExplanationReport | None = None,\n) -> OracleOperatorDecisionBrief:\n    root = Path(repository_root).resolve()\n    source = explanation_report\n    if source is None:\n        source = build_decision_explanation_report(root, query)\n    verify_decision_explanation_report(source)\n\n    unsorted_items = tuple(\n        _build_item(item, index)\n        for index, item in enumerate(source.findings, start=1)\n    )\n    items = tuple(\n        sorted(\n            unsorted_items,\n            key=lambda item: (\n                item.presentation_priority,\n                item.item_index,\n                item.item_hash,\n            ),\n        )\n    )\n    for item in items:\n        verify_operator_decision_brief_item(item)\n\n    ready_count = sum(item.readiness_state == "ready" for item in items)\n    observe_count = sum(item.readiness_state == "observe" for item in items)\n    abstain_count = sum(item.readiness_state == "abstain" for item in items)\n    attention_count = sum(\n        item.operator_attention_required for item in items\n    )\n    next_steps = _aggregate_next_steps(items)\n    blockers = _aggregate_blockers(items)\n    terminal_ready = bool(\n        items\n        and all(item.evidence_points for item in items)\n        and all(item.source_explanation_hash for item in items)\n    )\n    title = (\n        f"Oracle Operator Decision Brief — "\n        f"{source.aggregate_state.upper()} / "\n        f"{source.aggregate_direction.upper()}"\n    )\n    summary = (\n        f"{len(items)} items assembled: {ready_count} ready, "\n        f"{observe_count} observe, {abstain_count} abstain; "\n        f"{attention_count} require operator attention. "\n        "This brief is explanatory only and cannot authorize action."\n    )\n\n    body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root),\n        "query": str(query),\n        "explanation_report_hash": source.report_hash,\n        "brief_items": items,\n        "item_count": len(items),\n        "ready_item_count": ready_count,\n        "observe_item_count": observe_count,\n        "abstain_item_count": abstain_count,\n        "operator_attention_count": attention_count,\n        "primary_state": source.aggregate_state,\n        "primary_direction": source.aggregate_direction,\n        "brief_title": title,\n        "executive_summary": summary,\n        "operator_next_steps": next_steps,\n        "unresolved_blockers": blockers,\n        "terminal_consumption_ready": terminal_ready,\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "publication_allowed": False,\n        "qseries_execution_allowed": False,\n        "action_authorization_allowed": False,\n        "failure_reason": None,\n    }\n    brief = OracleOperatorDecisionBrief(\n        **body,\n        brief_hash=_stable_hash(body),\n    )\n    verify_operator_decision_brief(brief)\n    return brief\n\n\ndef verify_operator_decision_brief(\n    brief: OracleOperatorDecisionBrief,\n) -> bool:\n    body = asdict(brief)\n    supplied = body.pop("brief_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleOperatorDecisionBriefInvariantError(\n            "operator decision brief hash mismatch"\n        )\n    if brief.schema_version != SCHEMA_VERSION:\n        raise OracleOperatorDecisionBriefInvariantError("schema mismatch")\n    if brief.policy_id != POLICY_ID:\n        raise OracleOperatorDecisionBriefInvariantError("policy mismatch")\n    if not brief.read_only:\n        raise OracleOperatorDecisionBriefInvariantError(\n            "operator decision brief is not read-only"\n        )\n    if (\n        brief.analytics_execution_performed\n        or brief.database_access_performed\n        or brief.publication_allowed\n        or brief.qseries_execution_allowed\n        or brief.action_authorization_allowed\n    ):\n        raise OracleOperatorDecisionBriefInvariantError(\n            "forbidden capability enabled"\n        )\n    if brief.item_count != len(brief.brief_items):\n        raise OracleOperatorDecisionBriefInvariantError(\n            "brief item count mismatch"\n        )\n    counts = {\n        "ready": brief.ready_item_count,\n        "observe": brief.observe_item_count,\n        "abstain": brief.abstain_item_count,\n    }\n    for state, expected in counts.items():\n        actual = sum(\n            item.readiness_state == state for item in brief.brief_items\n        )\n        if actual != expected:\n            raise OracleOperatorDecisionBriefInvariantError(\n                f"{state} brief count mismatch"\n            )\n    if sum(counts.values()) != brief.item_count:\n        raise OracleOperatorDecisionBriefInvariantError(\n            "classified brief count mismatch"\n        )\n    if brief.operator_attention_count != sum(\n        item.operator_attention_required for item in brief.brief_items\n    ):\n        raise OracleOperatorDecisionBriefInvariantError(\n            "operator attention count mismatch"\n        )\n    if brief.primary_state not in {"ready", "observe", "abstain"}:\n        raise OracleOperatorDecisionBriefInvariantError(\n            "invalid primary state"\n        )\n    if brief.primary_direction not in {"bull", "bear", "neutral"}:\n        raise OracleOperatorDecisionBriefInvariantError(\n            "invalid primary direction"\n        )\n    for item in brief.brief_items:\n        verify_operator_decision_brief_item(item)\n    expected_order = tuple(\n        sorted(\n            brief.brief_items,\n            key=lambda item: (\n                item.presentation_priority,\n                item.item_index,\n                item.item_hash,\n            ),\n        )\n    )\n    if brief.brief_items != expected_order:\n        raise OracleOperatorDecisionBriefInvariantError(\n            "brief item presentation order mismatch"\n        )\n    if brief.terminal_consumption_ready and not brief.brief_items:\n        raise OracleOperatorDecisionBriefInvariantError(\n            "empty brief marked terminal-ready"\n        )\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import replace\nfrom pathlib import Path\nfrom tempfile import TemporaryDirectory\n\nfrom qseries_v2.oracle_terminal.oracle_decision_explanation_evidence_trace_intelligence import (\n    ENGINE_ID as OIT_021_ENGINE_ID,\n    POLICY_ID as OIT_021_POLICY_ID,\n    SCHEMA_VERSION as OIT_021_SCHEMA_VERSION,\n    OracleDecisionEvidenceTrace,\n    OracleDecisionExplanationFinding,\n    OracleDecisionExplanationReport,\n    _stable_hash as oit_021_hash,\n    verify_decision_explanation_report,\n)\nfrom qseries_v2.oracle_terminal.oracle_operator_decision_brief_assembly import (\n    OracleOperatorDecisionBriefInvariantError,\n    build_operator_decision_brief,\n    verify_operator_decision_brief,\n)\n\n\ndef trace(index: int, finding_hash: str, state: str):\n    body = {\n        "trace_index": index,\n        "source_debate_hash": f"debate-{finding_hash}",\n        "readiness_finding_hash": finding_hash,\n        "evidence_role": "metric",\n        "evidence_statement": f"evidence statement {index}",\n        "supports_state": state,\n    }\n    return OracleDecisionEvidenceTrace(\n        **body,\n        trace_hash=oit_021_hash(body),\n    )\n\n\ndef explanation_finding(index: int, state: str, direction: str):\n    readiness_hash = f"readiness-{index}"\n    body = {\n        "finding_index": index,\n        "cause_record_id": f"CAUSE-{index}",\n        "effect_record_id": f"EFFECT-{index}",\n        "source_readiness_hash": readiness_hash,\n        "readiness_state": state,\n        "directional_interpretation": (\n            direction if state == "ready" else f"non_actionable_{direction}"\n        ),\n        "readiness_score": 0.80 if state == "ready" else 0.50 if state == "observe" else 0.20,\n        "abstention_pressure": 0.20 if state == "ready" else 0.50 if state == "observe" else 0.85,\n        "concise_explanation": f"{state} explanation for {direction}",\n        "evidence_trace": (\n            trace(1, readiness_hash, state),\n            trace(2, readiness_hash, state),\n        ),\n        "confirmation_plan": (\n            "confirm directional persistence",\n            "confirm evidence remains current",\n        ),\n        "blocking_conditions": (\n            "direction changes",\n            "lineage verification fails",\n        ),\n        "explanation_complete": True,\n        "operator_attention_required": state == "abstain",\n        "read_only": True,\n    }\n    return OracleDecisionExplanationFinding(\n        **body,\n        finding_hash=oit_021_hash(body),\n    )\n\n\ndef make_report(root: Path):\n    findings = (\n        explanation_finding(1, "ready", "bull"),\n        explanation_finding(2, "observe", "bear"),\n        explanation_finding(3, "abstain", "neutral"),\n    )\n    body = {\n        "schema_version": OIT_021_SCHEMA_VERSION,\n        "engine_id": OIT_021_ENGINE_ID,\n        "policy_id": OIT_021_POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root.resolve()),\n        "query": "Assemble an operator decision brief.",\n        "readiness_report_hash": "readiness-report-hash",\n        "findings": findings,\n        "finding_count": 3,\n        "explained_count": 3,\n        "ready_explained_count": 1,\n        "observe_explained_count": 1,\n        "abstain_explained_count": 1,\n        "operator_attention_count": 1,\n        "aggregate_state": "abstain",\n        "aggregate_direction": "bull",\n        "explanation_state": "complete",\n        "explanation_summary": "Synthetic explanation report.",\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "publication_allowed": False,\n        "qseries_execution_allowed": False,\n        "action_authorization_allowed": False,\n        "failure_reason": None,\n    }\n    report = OracleDecisionExplanationReport(\n        **body,\n        report_hash=oit_021_hash(body),\n    )\n    verify_decision_explanation_report(report)\n    return report\n\n\ndef main() -> int:\n    print("=" * 48)\n    print(" OIT-022 TEST")\n    print(" OPERATOR DECISION BRIEF ASSEMBLY")\n    print("=" * 48)\n\n    with TemporaryDirectory() as temporary:\n        root = Path(temporary)\n        source = make_report(root)\n        brief = build_operator_decision_brief(\n            root,\n            source.query,\n            explanation_report=source,\n        )\n\n        assert brief.explanation_report_hash == source.report_hash\n        assert brief.item_count == 3\n        assert brief.ready_item_count == 1\n        assert brief.observe_item_count == 1\n        assert brief.abstain_item_count == 1\n        assert brief.operator_attention_count == 1\n        assert brief.primary_state == "abstain"\n        assert brief.primary_direction == "bull"\n        assert brief.terminal_consumption_ready\n\n        assert brief.brief_items[0].readiness_state == "abstain"\n        assert brief.brief_items[1].readiness_state == "observe"\n        assert brief.brief_items[2].readiness_state == "ready"\n\n        for item in brief.brief_items:\n            assert item.headline\n            assert item.explanation\n            assert item.evidence_points\n            assert item.confirmation_actions\n            assert item.blocking_conditions\n            assert item.source_explanation_hash\n            assert item.read_only\n\n        assert brief.operator_next_steps\n        assert brief.unresolved_blockers\n        assert "cannot authorize action" in brief.executive_summary\n\n        replay = build_operator_decision_brief(\n            root,\n            source.query,\n            explanation_report=source,\n        )\n        assert replay == brief\n        assert verify_operator_decision_brief(brief)\n\n        tampered = replace(\n            brief,\n            executive_summary=brief.executive_summary + " tampered",\n        )\n        try:\n            verify_operator_decision_brief(tampered)\n        except OracleOperatorDecisionBriefInvariantError:\n            pass\n        else:\n            raise AssertionError("tampered operator brief accepted")\n\n        assert brief.read_only\n        assert not brief.analytics_execution_performed\n        assert not brief.database_access_performed\n        assert not brief.publication_allowed\n        assert not brief.qseries_execution_allowed\n        assert not brief.action_authorization_allowed\n\n    print("[PASS] Certified OIT-021 explanation report consumed")\n    print("[PASS] Ready, observe, and abstain items assembled")\n    print("[PASS] Operator attention items prioritized first")\n    print("[PASS] Evidence points materialized for terminal consumption")\n    print("[PASS] Confirmation actions consolidated")\n    print("[PASS] Unresolved blockers consolidated")\n    print("[PASS] Executive summary materialized")\n    print("[PASS] Terminal-consumption readiness certified")\n    print("[PASS] Complete OIT-021 lineage retained")\n    print("[PASS] Operator brief deterministic across replay")\n    print("[PASS] Tampered operator brief rejected")\n    print("[PASS] No analytics execution or database access performed")\n    print("[PASS] Publication, action authorization, and Q Series execution disabled")\n    print("[DONE] OIT-022 OPERATOR DECISION BRIEF ASSEMBLY PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


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
    for path in (OIT_021, OIT_021_TEST, RUNNER):
        if path.is_file():
            protected[path] = sha256(path)
    return protected


def main() -> int:
    print("=" * 48)
    print(" OIT-022 INSTALLER")
    print(" OPERATOR DECISION BRIEF ASSEMBLY")
    print("=" * 48)
    try:
        require_contract(
            OIT_021,
            (
                'SCHEMA_VERSION = "OIT-021"',
                'POLICY_ID = "oracle.decision-explanation-evidence-trace-intelligence.v1"',
                "OracleDecisionExplanationReport",
                "OracleDecisionExplanationFinding",
                "OracleDecisionEvidenceTrace",
                "build_decision_explanation_report",
                "verify_decision_explanation_report",
                "concise_explanation",
                "evidence_trace",
                "confirmation_plan",
                "blocking_conditions",
                "operator_attention_required",
                "action_authorization_allowed",
            ),
            "Certified OIT-021 production",
        )
        require_contract(
            OIT_021_TEST,
            (
                "OIT-021 TEST",
                "DECISION EXPLANATION AND EVIDENCE TRACE",
                "OIT-021 DECISION EXPLANATION AND EVIDENCE TRACE PASS",
            ),
            "Certified OIT-021 standalone test",
        )

        protected = protected_sources()
        print("[OK] Certified OIT-021 production contract verified")
        print("[OK] Certified OIT-021 standalone test verified")
        print(f"[OK] Protected production source files captured: {len(protected)}")

        upstream = subprocess.run(
            [sys.executable, str(OIT_021_TEST)],
            cwd=ROOT,
            check=False,
        )
        if upstream.returncode:
            raise RuntimeError(
                f"OIT-021 certification failed with exit code {upstream.returncode}"
            )

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = "from .oracle_operator_decision_brief_assembly import *"
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
                f"OIT-022 test failed with exit code {completed.returncode}"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Protected production source changed: {path}"
                )

        print("[PASS] Certified OIT-021 production and test unchanged")
        print("[PASS] Oracle terminal runner unchanged")
        print("[PASS] OLA, OIA, INT-OII, ORR, OOR, and Q Series unchanged")
        print("[PASS] OIT-022 production module installed")
        print("[PASS] OIT-022 standalone test installed")
        print("[PASS] Operator decision brief assembly certified")
        print("[PASS] Terminal-consumption boundary prepared")
        print("[PASS] Action authorization remained disabled")
        print("[PASS] Read-only and execution boundaries preserved")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OIT-022 OPERATOR DECISION BRIEF ASSEMBLY INSTALLED")
        return 0
    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
