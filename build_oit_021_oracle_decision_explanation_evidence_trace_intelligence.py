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
            / "oracle_decision_readiness_abstention_intelligence.py"
        )
        if required.is_file():
            return candidate
    raise SystemExit("[ERROR] Could not locate current Q Series repository.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"
OIT_020 = PACKAGE / "oracle_decision_readiness_abstention_intelligence.py"
OIT_020_TEST = ROOT / "test_oit_020_oracle_decision_readiness_abstention_intelligence.py"
PRODUCTION = PACKAGE / "oracle_decision_explanation_evidence_trace_intelligence.py"
TEST = ROOT / "test_oit_021_oracle_decision_explanation_evidence_trace_intelligence.py"
INIT = PACKAGE / "__init__.py"
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass\nfrom pathlib import Path\nfrom typing import Any, Mapping\n\nfrom .oracle_decision_readiness_abstention_intelligence import (\n    OracleDecisionReadinessFinding,\n    OracleDecisionReadinessInvariantError,\n    OracleDecisionReadinessReport,\n    build_decision_readiness_report,\n    verify_decision_readiness_report,\n)\n\nSCHEMA_VERSION = "OIT-021"\nENGINE_ID = "OIT-021"\nPOLICY_ID = "oracle.decision-explanation-evidence-trace-intelligence.v1"\n\n\nclass OracleDecisionExplanationInvariantError(\n    OracleDecisionReadinessInvariantError\n):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleDecisionEvidenceTrace:\n    trace_index: int\n    source_debate_hash: str\n    readiness_finding_hash: str\n    evidence_role: str\n    evidence_statement: str\n    supports_state: str\n    trace_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleDecisionExplanationFinding:\n    finding_index: int\n    cause_record_id: str\n    effect_record_id: str\n    source_readiness_hash: str\n    readiness_state: str\n    directional_interpretation: str\n    readiness_score: float\n    abstention_pressure: float\n    concise_explanation: str\n    evidence_trace: tuple[OracleDecisionEvidenceTrace, ...]\n    confirmation_plan: tuple[str, ...]\n    blocking_conditions: tuple[str, ...]\n    explanation_complete: bool\n    operator_attention_required: bool\n    read_only: bool\n    finding_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleDecisionExplanationReport:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    status: str\n    repository_root: str\n    query: str\n    readiness_report_hash: str\n    findings: tuple[OracleDecisionExplanationFinding, ...]\n    finding_count: int\n    explained_count: int\n    ready_explained_count: int\n    observe_explained_count: int\n    abstain_explained_count: int\n    operator_attention_count: int\n    aggregate_state: str\n    aggregate_direction: str\n    explanation_state: str\n    explanation_summary: str\n    read_only: bool\n    analytics_execution_performed: bool\n    database_access_performed: bool\n    publication_allowed: bool\n    qseries_execution_allowed: bool\n    action_authorization_allowed: bool\n    failure_reason: str | None\n    report_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if isinstance(value, Path):\n        return value.as_posix()\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    return repr(value)\n\n\ndef _stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=True,\n    ).encode("utf-8")\n    return hashlib.sha256(payload).hexdigest()\n\n\ndef _trace(\n    index: int,\n    source: OracleDecisionReadinessFinding,\n    role: str,\n    statement: str,\n) -> OracleDecisionEvidenceTrace:\n    body = {\n        "trace_index": index,\n        "source_debate_hash": source.source_debate_hash,\n        "readiness_finding_hash": source.finding_hash,\n        "evidence_role": role,\n        "evidence_statement": statement,\n        "supports_state": source.readiness_state,\n    }\n    return OracleDecisionEvidenceTrace(\n        **body,\n        trace_hash=_stable_hash(body),\n    )\n\n\ndef _explain(source: OracleDecisionReadinessFinding) -> str:\n    if source.readiness_state == "ready":\n        return (\n            f"{source.directional_interpretation} interpretation is ready for "\n            f"operator consideration because readiness {source.readiness_score:.6f} "\n            f"exceeds abstention pressure {source.abstention_pressure:.6f}, "\n            f"with debate margin {source.debate_margin:.6f}."\n        )\n    if source.readiness_state == "observe":\n        return (\n            f"{source.directional_interpretation} remains observational because "\n            f"readiness {source.readiness_score:.6f} is not yet sufficient to "\n            f"clear confirmation requirements while abstention pressure remains "\n            f"{source.abstention_pressure:.6f}."\n        )\n    return (\n        f"{source.directional_interpretation} is blocked by abstention because "\n        f"abstention pressure is {source.abstention_pressure:.6f}, debate conflict "\n        f"is {source.debate_conflict:.6f}, and human review is "\n        f"{\'required\' if source.requires_human_review else \'not required\'}."\n    )\n\n\ndef _build_finding(\n    source: OracleDecisionReadinessFinding,\n    index: int,\n) -> OracleDecisionExplanationFinding:\n    statements = (\n        ("readiness", f"readiness score = {source.readiness_score:.6f}"),\n        ("abstention", f"abstention pressure = {source.abstention_pressure:.6f}"),\n        ("margin", f"debate margin = {source.debate_margin:.6f}"),\n        ("conflict", f"debate conflict = {source.debate_conflict:.6f}"),\n        (\n            "confidence",\n            f"adjudicated confidence = {source.adjudicated_confidence:.6f}",\n        ),\n        (\n            "review",\n            f"human review required = {source.requires_human_review}",\n        ),\n    )\n    traces = tuple(\n        _trace(i, source, role, statement)\n        for i, (role, statement) in enumerate(statements, start=1)\n    )\n    complete = bool(\n        traces\n        and source.required_confirmations\n        and source.disqualifying_conditions\n        and source.source_debate_hash\n    )\n    attention = (\n        source.requires_human_review\n        or source.readiness_state == "abstain"\n        or not complete\n    )\n    body = {\n        "finding_index": index,\n        "cause_record_id": source.cause_record_id,\n        "effect_record_id": source.effect_record_id,\n        "source_readiness_hash": source.finding_hash,\n        "readiness_state": source.readiness_state,\n        "directional_interpretation": source.directional_interpretation,\n        "readiness_score": source.readiness_score,\n        "abstention_pressure": source.abstention_pressure,\n        "concise_explanation": _explain(source),\n        "evidence_trace": traces,\n        "confirmation_plan": tuple(source.required_confirmations),\n        "blocking_conditions": tuple(source.disqualifying_conditions),\n        "explanation_complete": complete,\n        "operator_attention_required": attention,\n        "read_only": True,\n    }\n    return OracleDecisionExplanationFinding(\n        **body,\n        finding_hash=_stable_hash(body),\n    )\n\n\ndef verify_decision_evidence_trace(trace: OracleDecisionEvidenceTrace) -> bool:\n    body = asdict(trace)\n    supplied = body.pop("trace_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleDecisionExplanationInvariantError(\n            "decision evidence trace hash mismatch"\n        )\n    if trace.supports_state not in {"ready", "observe", "abstain"}:\n        raise OracleDecisionExplanationInvariantError(\n            "unsupported trace readiness state"\n        )\n    if not trace.source_debate_hash or not trace.readiness_finding_hash:\n        raise OracleDecisionExplanationInvariantError(\n            "decision evidence lineage missing"\n        )\n    if not trace.evidence_statement:\n        raise OracleDecisionExplanationInvariantError(\n            "decision evidence statement missing"\n        )\n    return True\n\n\ndef verify_decision_explanation_finding(\n    finding: OracleDecisionExplanationFinding,\n) -> bool:\n    body = asdict(finding)\n    supplied = body.pop("finding_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleDecisionExplanationInvariantError(\n            "decision explanation finding hash mismatch"\n        )\n    if not finding.read_only:\n        raise OracleDecisionExplanationInvariantError(\n            "decision explanation finding is not read-only"\n        )\n    if finding.readiness_state not in {"ready", "observe", "abstain"}:\n        raise OracleDecisionExplanationInvariantError(\n            "unsupported explanation readiness state"\n        )\n    if not finding.source_readiness_hash:\n        raise OracleDecisionExplanationInvariantError(\n            "readiness lineage missing"\n        )\n    if not finding.concise_explanation:\n        raise OracleDecisionExplanationInvariantError(\n            "concise explanation missing"\n        )\n    if not finding.evidence_trace:\n        raise OracleDecisionExplanationInvariantError(\n            "evidence trace missing"\n        )\n    for trace in finding.evidence_trace:\n        verify_decision_evidence_trace(trace)\n        if trace.readiness_finding_hash != finding.source_readiness_hash:\n            raise OracleDecisionExplanationInvariantError(\n                "evidence trace readiness lineage mismatch"\n            )\n    if finding.explanation_complete and (\n        not finding.confirmation_plan or not finding.blocking_conditions\n    ):\n        raise OracleDecisionExplanationInvariantError(\n            "complete explanation missing controls"\n        )\n    return True\n\n\ndef build_decision_explanation_report(\n    repository_root: str | Path,\n    query: str,\n    *,\n    readiness_report: OracleDecisionReadinessReport | None = None,\n) -> OracleDecisionExplanationReport:\n    root = Path(repository_root).resolve()\n    source = readiness_report\n    if source is None:\n        source = build_decision_readiness_report(root, query)\n    verify_decision_readiness_report(source)\n\n    findings = tuple(\n        _build_finding(item, index)\n        for index, item in enumerate(source.findings, start=1)\n    )\n    for finding in findings:\n        verify_decision_explanation_finding(finding)\n\n    explained_count = sum(item.explanation_complete for item in findings)\n    attention_count = sum(\n        item.operator_attention_required for item in findings\n    )\n    explanation_state = (\n        "complete"\n        if explained_count == len(findings)\n        else "incomplete"\n    )\n    summary = (\n        f"{len(findings)} readiness findings explained; "\n        f"{explained_count} complete; {attention_count} require operator attention; "\n        f"aggregate state {source.aggregate_state}."\n    )\n\n    body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root),\n        "query": str(query),\n        "readiness_report_hash": source.report_hash,\n        "findings": findings,\n        "finding_count": len(findings),\n        "explained_count": explained_count,\n        "ready_explained_count": sum(\n            item.readiness_state == "ready" for item in findings\n        ),\n        "observe_explained_count": sum(\n            item.readiness_state == "observe" for item in findings\n        ),\n        "abstain_explained_count": sum(\n            item.readiness_state == "abstain" for item in findings\n        ),\n        "operator_attention_count": attention_count,\n        "aggregate_state": source.aggregate_state,\n        "aggregate_direction": source.aggregate_direction,\n        "explanation_state": explanation_state,\n        "explanation_summary": summary,\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "publication_allowed": False,\n        "qseries_execution_allowed": False,\n        "action_authorization_allowed": False,\n        "failure_reason": None,\n    }\n    report = OracleDecisionExplanationReport(\n        **body,\n        report_hash=_stable_hash(body),\n    )\n    verify_decision_explanation_report(report)\n    return report\n\n\ndef verify_decision_explanation_report(\n    report: OracleDecisionExplanationReport,\n) -> bool:\n    body = asdict(report)\n    supplied = body.pop("report_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleDecisionExplanationInvariantError(\n            "decision explanation report hash mismatch"\n        )\n    if report.schema_version != SCHEMA_VERSION:\n        raise OracleDecisionExplanationInvariantError("schema mismatch")\n    if report.policy_id != POLICY_ID:\n        raise OracleDecisionExplanationInvariantError("policy mismatch")\n    if not report.read_only:\n        raise OracleDecisionExplanationInvariantError(\n            "decision explanation report is not read-only"\n        )\n    if (\n        report.analytics_execution_performed\n        or report.database_access_performed\n        or report.publication_allowed\n        or report.qseries_execution_allowed\n        or report.action_authorization_allowed\n    ):\n        raise OracleDecisionExplanationInvariantError(\n            "forbidden capability enabled"\n        )\n    if report.finding_count != len(report.findings):\n        raise OracleDecisionExplanationInvariantError(\n            "decision explanation finding count mismatch"\n        )\n    if report.explained_count != sum(\n        item.explanation_complete for item in report.findings\n    ):\n        raise OracleDecisionExplanationInvariantError(\n            "explained count mismatch"\n        )\n    if report.operator_attention_count != sum(\n        item.operator_attention_required for item in report.findings\n    ):\n        raise OracleDecisionExplanationInvariantError(\n            "operator attention count mismatch"\n        )\n    counts = {\n        "ready": report.ready_explained_count,\n        "observe": report.observe_explained_count,\n        "abstain": report.abstain_explained_count,\n    }\n    for state, expected in counts.items():\n        actual = sum(\n            item.readiness_state == state for item in report.findings\n        )\n        if actual != expected:\n            raise OracleDecisionExplanationInvariantError(\n                f"{state} explanation count mismatch"\n            )\n    if sum(counts.values()) != report.finding_count:\n        raise OracleDecisionExplanationInvariantError(\n            "classified explanation count mismatch"\n        )\n    if report.aggregate_state not in {"ready", "observe", "abstain"}:\n        raise OracleDecisionExplanationInvariantError(\n            "invalid aggregate state"\n        )\n    if report.aggregate_direction not in {"bull", "bear", "neutral"}:\n        raise OracleDecisionExplanationInvariantError(\n            "invalid aggregate direction"\n        )\n    if report.explanation_state not in {"complete", "incomplete"}:\n        raise OracleDecisionExplanationInvariantError(\n            "invalid explanation state"\n        )\n    for finding in report.findings:\n        verify_decision_explanation_finding(finding)\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import replace\nfrom pathlib import Path\nfrom tempfile import TemporaryDirectory\n\nfrom qseries_v2.oracle_terminal.oracle_decision_readiness_abstention_intelligence import (\n    ENGINE_ID as OIT_020_ENGINE_ID,\n    POLICY_ID as OIT_020_POLICY_ID,\n    SCHEMA_VERSION as OIT_020_SCHEMA_VERSION,\n    OracleDecisionReadinessFinding,\n    OracleDecisionReadinessReport,\n    _stable_hash as oit_020_hash,\n    verify_decision_readiness_report,\n)\nfrom qseries_v2.oracle_terminal.oracle_decision_explanation_evidence_trace_intelligence import (\n    OracleDecisionExplanationInvariantError,\n    build_decision_explanation_report,\n    verify_decision_explanation_report,\n)\n\n\ndef readiness_finding(index: int, state: str, direction: str):\n    values = {\n        "ready": (0.78, 0.24, False, 1),\n        "observe": (0.48, 0.52, False, 2),\n        "abstain": (0.20, 0.82, True, 3),\n    }\n    readiness, abstention, review, minimum = values[state]\n    body = {\n        "finding_index": index,\n        "cause_record_id": f"CAUSE-{index}",\n        "effect_record_id": f"EFFECT-{index}",\n        "source_debate_hash": f"debate-{index}",\n        "leading_position": direction,\n        "debate_margin": 0.40 if state == "ready" else 0.12 if state == "observe" else 0.03,\n        "debate_conflict": 0.20 if state == "ready" else 0.55 if state == "observe" else 0.90,\n        "adjudicated_confidence": 0.80 if state == "ready" else 0.50 if state == "observe" else 0.25,\n        "requires_human_review": review,\n        "readiness_score": readiness,\n        "abstention_pressure": abstention,\n        "readiness_state": state,\n        "directional_interpretation": direction if state == "ready" else f"non_actionable_{direction}",\n        "minimum_confirmation_count": minimum,\n        "required_confirmations": (\n            "confirm directional persistence",\n            "confirm margin stability",\n        ),\n        "disqualifying_conditions": (\n            "direction changes",\n            "lineage verification fails",\n        ),\n        "rationale": ("certified readiness rationale",),\n        "read_only": True,\n    }\n    return OracleDecisionReadinessFinding(\n        **body,\n        finding_hash=oit_020_hash(body),\n    )\n\n\ndef make_report(root: Path):\n    findings = (\n        readiness_finding(1, "ready", "bull"),\n        readiness_finding(2, "observe", "bear"),\n        readiness_finding(3, "abstain", "neutral"),\n    )\n    body = {\n        "schema_version": OIT_020_SCHEMA_VERSION,\n        "engine_id": OIT_020_ENGINE_ID,\n        "policy_id": OIT_020_POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root.resolve()),\n        "query": "Explain decision readiness.",\n        "debate_report_hash": "debate-report-hash",\n        "findings": findings,\n        "finding_count": 3,\n        "ready_count": 1,\n        "observe_count": 1,\n        "abstain_count": 1,\n        "human_review_count": 1,\n        "aggregate_state": "abstain",\n        "aggregate_direction": "bull",\n        "aggregate_readiness": 0.486667,\n        "aggregate_abstention_pressure": 0.526667,\n        "readiness_summary": "Synthetic readiness report.",\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "publication_allowed": False,\n        "qseries_execution_allowed": False,\n        "action_authorization_allowed": False,\n        "failure_reason": None,\n    }\n    report = OracleDecisionReadinessReport(\n        **body,\n        report_hash=oit_020_hash(body),\n    )\n    verify_decision_readiness_report(report)\n    return report\n\n\ndef main() -> int:\n    print("=" * 48)\n    print(" OIT-021 TEST")\n    print(" DECISION EXPLANATION AND EVIDENCE TRACE")\n    print("=" * 48)\n\n    with TemporaryDirectory() as temporary:\n        root = Path(temporary)\n        source = make_report(root)\n        report = build_decision_explanation_report(\n            root,\n            source.query,\n            readiness_report=source,\n        )\n\n        assert report.readiness_report_hash == source.report_hash\n        assert report.finding_count == 3\n        assert report.explained_count == 3\n        assert report.ready_explained_count == 1\n        assert report.observe_explained_count == 1\n        assert report.abstain_explained_count == 1\n        assert report.operator_attention_count == 1\n        assert report.explanation_state == "complete"\n\n        ready, observe, abstain = report.findings\n        assert "ready for operator consideration" in ready.concise_explanation\n        assert "remains observational" in observe.concise_explanation\n        assert "blocked by abstention" in abstain.concise_explanation\n        assert not ready.operator_attention_required\n        assert abstain.operator_attention_required\n\n        for finding in report.findings:\n            assert finding.explanation_complete\n            assert len(finding.evidence_trace) == 6\n            assert finding.confirmation_plan\n            assert finding.blocking_conditions\n            assert finding.source_readiness_hash\n            for trace in finding.evidence_trace:\n                assert trace.readiness_finding_hash == finding.source_readiness_hash\n\n        replay = build_decision_explanation_report(\n            root,\n            source.query,\n            readiness_report=source,\n        )\n        assert replay == report\n        assert verify_decision_explanation_report(report)\n\n        tampered = replace(\n            report,\n            explanation_summary=report.explanation_summary + " tampered",\n        )\n        try:\n            verify_decision_explanation_report(tampered)\n        except OracleDecisionExplanationInvariantError:\n            pass\n        else:\n            raise AssertionError("tampered explanation report accepted")\n\n        assert report.read_only\n        assert not report.analytics_execution_performed\n        assert not report.database_access_performed\n        assert not report.publication_allowed\n        assert not report.qseries_execution_allowed\n        assert not report.action_authorization_allowed\n\n    print("[PASS] Certified OIT-020 readiness report consumed")\n    print("[PASS] Ready-state explanation materialized")\n    print("[PASS] Observe-state explanation materialized")\n    print("[PASS] Abstain-state explanation materialized")\n    print("[PASS] Evidence trace bound to readiness and debate lineage")\n    print("[PASS] Confirmation plan preserved")\n    print("[PASS] Blocking conditions preserved")\n    print("[PASS] Operator-attention requirement surfaced")\n    print("[PASS] Complete OIT-020 lineage retained")\n    print("[PASS] Explanation report deterministic across replay")\n    print("[PASS] Tampered explanation report rejected")\n    print("[PASS] No analytics execution or database access performed")\n    print("[PASS] Publication, action authorization, and Q Series execution disabled")\n    print("[DONE] OIT-021 DECISION EXPLANATION AND EVIDENCE TRACE PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


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
    for path in (OIT_020, OIT_020_TEST, RUNNER):
        if path.is_file():
            protected[path] = sha256(path)
    return protected


def main() -> int:
    print("=" * 48)
    print(" OIT-021 INSTALLER")
    print(" DECISION EXPLANATION AND EVIDENCE TRACE")
    print("=" * 48)
    try:
        require_contract(
            OIT_020,
            (
                'SCHEMA_VERSION = "OIT-020"',
                'POLICY_ID = "oracle.decision-readiness-abstention-intelligence.v1"',
                "OracleDecisionReadinessReport",
                "OracleDecisionReadinessFinding",
                "build_decision_readiness_report",
                "verify_decision_readiness_report",
                "readiness_state",
                "readiness_score",
                "abstention_pressure",
                "required_confirmations",
                "disqualifying_conditions",
                "action_authorization_allowed",
            ),
            "Certified OIT-020 production",
        )
        require_contract(
            OIT_020_TEST,
            (
                "OIT-020 TEST",
                "DECISION READINESS AND ABSTENTION",
                "OIT-020 DECISION READINESS AND ABSTENTION PASS",
            ),
            "Certified OIT-020 standalone test",
        )

        protected = protected_sources()
        print("[OK] Certified OIT-020 production contract verified")
        print("[OK] Certified OIT-020 standalone test verified")
        print(f"[OK] Protected production source files captured: {len(protected)}")

        upstream = subprocess.run(
            [sys.executable, str(OIT_020_TEST)],
            cwd=ROOT,
            check=False,
        )
        if upstream.returncode:
            raise RuntimeError(
                f"OIT-020 certification failed with exit code {upstream.returncode}"
            )

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_decision_explanation_evidence_trace_intelligence import *"
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
                f"OIT-021 test failed with exit code {completed.returncode}"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Protected production source changed: {path}"
                )

        print("[PASS] Certified OIT-020 production and test unchanged")
        print("[PASS] Oracle terminal runner unchanged")
        print("[PASS] OLA, OIA, INT-OII, ORR, OOR, and Q Series unchanged")
        print("[PASS] OIT-021 production module installed")
        print("[PASS] OIT-021 standalone test installed")
        print("[PASS] Decision explanations and evidence traces certified")
        print("[PASS] Confirmation and blocking controls preserved")
        print("[PASS] Action authorization remained disabled")
        print("[PASS] Read-only and execution boundaries preserved")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OIT-021 DECISION EXPLANATION AND EVIDENCE TRACE INSTALLED")
        return 0
    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
