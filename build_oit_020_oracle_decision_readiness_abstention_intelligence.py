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
            candidate
            / "qseries_v2"
            / "oracle_terminal"
            / "oracle_bull_bear_neutral_debate_synthesis.py"
        )
        if required.is_file():
            return candidate
    raise SystemExit("[ERROR] Could not locate current Q Series repository.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"
OIT_019 = PACKAGE / "oracle_bull_bear_neutral_debate_synthesis.py"
OIT_019_TEST = ROOT / "test_oit_019_oracle_bull_bear_neutral_debate_synthesis.py"
PRODUCTION = PACKAGE / "oracle_decision_readiness_abstention_intelligence.py"
TEST = ROOT / "test_oit_020_oracle_decision_readiness_abstention_intelligence.py"
INIT = PACKAGE / "__init__.py"
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass\nfrom pathlib import Path\nfrom typing import Any, Mapping\n\nfrom .oracle_bull_bear_neutral_debate_synthesis import (\n    OracleDebateFinding,\n    OracleDebateSynthesisInvariantError,\n    OracleDebateSynthesisReport,\n    build_debate_synthesis_report,\n    verify_debate_synthesis_report,\n)\n\nSCHEMA_VERSION = "OIT-020"\nENGINE_ID = "OIT-020"\nPOLICY_ID = "oracle.decision-readiness-abstention-intelligence.v1"\n\n\nclass OracleDecisionReadinessInvariantError(\n    OracleDebateSynthesisInvariantError\n):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleDecisionReadinessFinding:\n    finding_index: int\n    cause_record_id: str\n    effect_record_id: str\n    source_debate_hash: str\n    leading_position: str\n    debate_margin: float\n    debate_conflict: float\n    adjudicated_confidence: float\n    requires_human_review: bool\n    readiness_score: float\n    abstention_pressure: float\n    readiness_state: str\n    directional_interpretation: str\n    minimum_confirmation_count: int\n    required_confirmations: tuple[str, ...]\n    disqualifying_conditions: tuple[str, ...]\n    rationale: tuple[str, ...]\n    read_only: bool\n    finding_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleDecisionReadinessReport:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    status: str\n    repository_root: str\n    query: str\n    debate_report_hash: str\n    findings: tuple[OracleDecisionReadinessFinding, ...]\n    finding_count: int\n    ready_count: int\n    observe_count: int\n    abstain_count: int\n    human_review_count: int\n    aggregate_state: str\n    aggregate_direction: str\n    aggregate_readiness: float\n    aggregate_abstention_pressure: float\n    readiness_summary: str\n    read_only: bool\n    analytics_execution_performed: bool\n    database_access_performed: bool\n    publication_allowed: bool\n    qseries_execution_allowed: bool\n    action_authorization_allowed: bool\n    failure_reason: str | None\n    report_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if isinstance(value, Path):\n        return value.as_posix()\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    return repr(value)\n\n\ndef _stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=True,\n    ).encode("utf-8")\n    return hashlib.sha256(payload).hexdigest()\n\n\ndef _bounded(value: float) -> float:\n    return round(max(0.0, min(1.0, value)), 6)\n\n\ndef _classify(source: OracleDebateFinding) -> tuple[str, float, float]:\n    readiness = _bounded(\n        (0.45 * source.adjudicated_confidence)\n        + (0.35 * source.debate_margin)\n        + (0.20 * (1.0 - source.debate_conflict))\n    )\n    abstention = _bounded(\n        (0.45 * source.debate_conflict)\n        + (0.30 * (1.0 - source.debate_margin))\n        + (0.15 * (1.0 - source.adjudicated_confidence))\n        + (0.10 if source.requires_human_review else 0.0)\n    )\n\n    if (\n        source.requires_human_review\n        or source.adjudication_state in {"contested", "challenge_conflict"}\n        or abstention >= 0.68\n    ):\n        state = "abstain"\n    elif (\n        readiness >= 0.58\n        and source.debate_margin >= 0.12\n        and source.adjudicated_confidence >= 0.45\n        and abstention < 0.60\n    ):\n        state = "ready"\n    else:\n        state = "observe"\n    return state, readiness, abstention\n\n\ndef _build_finding(\n    source: OracleDebateFinding,\n    index: int,\n) -> OracleDecisionReadinessFinding:\n    state, readiness, abstention = _classify(source)\n\n    if state == "ready":\n        minimum_confirmations = 1\n    elif state == "observe":\n        minimum_confirmations = 2\n    else:\n        minimum_confirmations = 3\n\n    confirmations = (\n        f"confirm the {source.leading_position} lead persists on refresh",\n        "confirm debate margin does not contract materially",\n        "confirm no new contradiction raises human-review pressure",\n    )\n    disqualifiers = (\n        "leading position changes after certified evidence refresh",\n        "debate conflict rises above the bounded readiness threshold",\n        "human review becomes required",\n        "source lineage or report hash fails verification",\n    )\n    interpretation = (\n        source.leading_position\n        if state == "ready"\n        else "non_actionable_" + source.leading_position\n    )\n    rationale = (\n        f"readiness score: {readiness:.6f}",\n        f"abstention pressure: {abstention:.6f}",\n        f"debate margin: {source.debate_margin:.6f}",\n        f"debate conflict: {source.debate_conflict:.6f}",\n        f"adjudicated confidence: {source.adjudicated_confidence:.6f}",\n        f"readiness state: {state}",\n        "classification is intelligence-only and cannot authorize action",\n    )\n\n    body = {\n        "finding_index": index,\n        "cause_record_id": source.cause_record_id,\n        "effect_record_id": source.effect_record_id,\n        "source_debate_hash": source.finding_hash,\n        "leading_position": source.leading_position,\n        "debate_margin": source.debate_margin,\n        "debate_conflict": source.debate_conflict,\n        "adjudicated_confidence": source.adjudicated_confidence,\n        "requires_human_review": source.requires_human_review,\n        "readiness_score": readiness,\n        "abstention_pressure": abstention,\n        "readiness_state": state,\n        "directional_interpretation": interpretation,\n        "minimum_confirmation_count": minimum_confirmations,\n        "required_confirmations": confirmations,\n        "disqualifying_conditions": disqualifiers,\n        "rationale": rationale,\n        "read_only": True,\n    }\n    return OracleDecisionReadinessFinding(\n        **body,\n        finding_hash=_stable_hash(body),\n    )\n\n\ndef verify_decision_readiness_finding(\n    finding: OracleDecisionReadinessFinding,\n) -> bool:\n    body = asdict(finding)\n    supplied = body.pop("finding_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleDecisionReadinessInvariantError(\n            "decision-readiness finding hash mismatch"\n        )\n    if not finding.read_only:\n        raise OracleDecisionReadinessInvariantError(\n            "decision-readiness finding is not read-only"\n        )\n    if finding.readiness_state not in {"ready", "observe", "abstain"}:\n        raise OracleDecisionReadinessInvariantError(\n            "unsupported readiness state"\n        )\n    if finding.leading_position not in {"bull", "bear", "neutral"}:\n        raise OracleDecisionReadinessInvariantError(\n            "unsupported directional position"\n        )\n    for value in (\n        finding.debate_margin,\n        finding.debate_conflict,\n        finding.adjudicated_confidence,\n        finding.readiness_score,\n        finding.abstention_pressure,\n    ):\n        if not 0.0 <= value <= 1.0:\n            raise OracleDecisionReadinessInvariantError(\n                "readiness metric outside bounded range"\n            )\n    if finding.minimum_confirmation_count < 1:\n        raise OracleDecisionReadinessInvariantError(\n            "minimum confirmation count invalid"\n        )\n    if not finding.required_confirmations:\n        raise OracleDecisionReadinessInvariantError(\n            "required confirmations missing"\n        )\n    if not finding.disqualifying_conditions:\n        raise OracleDecisionReadinessInvariantError(\n            "disqualifying conditions missing"\n        )\n    if not finding.source_debate_hash:\n        raise OracleDecisionReadinessInvariantError(\n            "debate lineage missing"\n        )\n    return True\n\n\ndef _aggregate(\n    findings: tuple[OracleDecisionReadinessFinding, ...],\n) -> tuple[str, str, float, float, str]:\n    if not findings:\n        return (\n            "abstain",\n            "neutral",\n            0.0,\n            1.0,\n            "No certified debate findings were available; abstention required.",\n        )\n\n    ready = sum(item.readiness_state == "ready" for item in findings)\n    observe = sum(item.readiness_state == "observe" for item in findings)\n    abstain = sum(item.readiness_state == "abstain" for item in findings)\n\n    if abstain:\n        state = "abstain"\n    elif ready == len(findings):\n        state = "ready"\n    else:\n        state = "observe"\n\n    directional_scores = {"bull": 0.0, "bear": 0.0, "neutral": 0.0}\n    for item in findings:\n        multiplier = (\n            1.0 if item.readiness_state == "ready"\n            else 0.5 if item.readiness_state == "observe"\n            else 0.0\n        )\n        directional_scores[item.leading_position] += (\n            item.readiness_score * multiplier\n        )\n    direction = sorted(\n        directional_scores.items(),\n        key=lambda pair: (-pair[1], pair[0]),\n    )[0][0]\n\n    aggregate_readiness = _bounded(\n        sum(item.readiness_score for item in findings) / len(findings)\n    )\n    aggregate_abstention = _bounded(\n        sum(item.abstention_pressure for item in findings) / len(findings)\n    )\n    summary = (\n        f"{len(findings)} findings classified: {ready} ready, "\n        f"{observe} observe, {abstain} abstain; aggregate state {state}; "\n        f"non-authorizing direction {direction}."\n    )\n    return (\n        state,\n        direction,\n        aggregate_readiness,\n        aggregate_abstention,\n        summary,\n    )\n\n\ndef build_decision_readiness_report(\n    repository_root: str | Path,\n    query: str,\n    *,\n    debate_report: OracleDebateSynthesisReport | None = None,\n) -> OracleDecisionReadinessReport:\n    root = Path(repository_root).resolve()\n    source = debate_report\n    if source is None:\n        source = build_debate_synthesis_report(root, query)\n    verify_debate_synthesis_report(source)\n\n    findings = tuple(\n        _build_finding(item, index)\n        for index, item in enumerate(source.findings, start=1)\n    )\n    for finding in findings:\n        verify_decision_readiness_finding(finding)\n\n    state, direction, readiness, abstention, summary = _aggregate(findings)\n    body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root),\n        "query": str(query),\n        "debate_report_hash": source.report_hash,\n        "findings": findings,\n        "finding_count": len(findings),\n        "ready_count": sum(\n            item.readiness_state == "ready" for item in findings\n        ),\n        "observe_count": sum(\n            item.readiness_state == "observe" for item in findings\n        ),\n        "abstain_count": sum(\n            item.readiness_state == "abstain" for item in findings\n        ),\n        "human_review_count": sum(\n            item.requires_human_review for item in findings\n        ),\n        "aggregate_state": state,\n        "aggregate_direction": direction,\n        "aggregate_readiness": readiness,\n        "aggregate_abstention_pressure": abstention,\n        "readiness_summary": summary,\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "publication_allowed": False,\n        "qseries_execution_allowed": False,\n        "action_authorization_allowed": False,\n        "failure_reason": None,\n    }\n    report = OracleDecisionReadinessReport(\n        **body,\n        report_hash=_stable_hash(body),\n    )\n    verify_decision_readiness_report(report)\n    return report\n\n\ndef verify_decision_readiness_report(\n    report: OracleDecisionReadinessReport,\n) -> bool:\n    body = asdict(report)\n    supplied = body.pop("report_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleDecisionReadinessInvariantError(\n            "decision-readiness report hash mismatch"\n        )\n    if report.schema_version != SCHEMA_VERSION:\n        raise OracleDecisionReadinessInvariantError("schema mismatch")\n    if report.policy_id != POLICY_ID:\n        raise OracleDecisionReadinessInvariantError("policy mismatch")\n    if not report.read_only:\n        raise OracleDecisionReadinessInvariantError(\n            "decision-readiness report is not read-only"\n        )\n    if (\n        report.analytics_execution_performed\n        or report.database_access_performed\n        or report.publication_allowed\n        or report.qseries_execution_allowed\n        or report.action_authorization_allowed\n    ):\n        raise OracleDecisionReadinessInvariantError(\n            "forbidden capability enabled"\n        )\n    if report.finding_count != len(report.findings):\n        raise OracleDecisionReadinessInvariantError(\n            "decision-readiness finding count mismatch"\n        )\n    counts = {\n        "ready": report.ready_count,\n        "observe": report.observe_count,\n        "abstain": report.abstain_count,\n    }\n    for state, expected in counts.items():\n        actual = sum(\n            item.readiness_state == state for item in report.findings\n        )\n        if actual != expected:\n            raise OracleDecisionReadinessInvariantError(\n                f"{state} readiness count mismatch"\n            )\n    if sum(counts.values()) != report.finding_count:\n        raise OracleDecisionReadinessInvariantError(\n            "classified readiness count mismatch"\n        )\n    actual_review = sum(\n        item.requires_human_review for item in report.findings\n    )\n    if actual_review != report.human_review_count:\n        raise OracleDecisionReadinessInvariantError(\n            "human review count mismatch"\n        )\n    if report.aggregate_state not in {"ready", "observe", "abstain"}:\n        raise OracleDecisionReadinessInvariantError(\n            "invalid aggregate readiness state"\n        )\n    if report.aggregate_direction not in {"bull", "bear", "neutral"}:\n        raise OracleDecisionReadinessInvariantError(\n            "invalid aggregate direction"\n        )\n    for value in (\n        report.aggregate_readiness,\n        report.aggregate_abstention_pressure,\n    ):\n        if not 0.0 <= value <= 1.0:\n            raise OracleDecisionReadinessInvariantError(\n                "aggregate readiness metric outside bounded range"\n            )\n    for finding in report.findings:\n        verify_decision_readiness_finding(finding)\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import replace\nfrom pathlib import Path\nfrom tempfile import TemporaryDirectory\n\nfrom qseries_v2.oracle_terminal.oracle_bull_bear_neutral_debate_synthesis import (\n    ENGINE_ID as OIT_019_ENGINE_ID,\n    POLICY_ID as OIT_019_POLICY_ID,\n    SCHEMA_VERSION as OIT_019_SCHEMA_VERSION,\n    OracleDebateFinding,\n    OracleDebatePosition,\n    OracleDebateSynthesisReport,\n    _stable_hash as oit_019_hash,\n    verify_debate_synthesis_report,\n)\nfrom qseries_v2.oracle_terminal.oracle_decision_readiness_abstention_intelligence import (\n    OracleDecisionReadinessInvariantError,\n    build_decision_readiness_report,\n    verify_decision_readiness_report,\n)\n\n\ndef position(name: str, score: float):\n    body = {\n        "position": name,\n        "score": score,\n        "confidence": round(0.50 + abs(score - 0.50), 6),\n        "supporting_points": (f"{name} support",),\n        "opposing_points": (f"{name} opposition",),\n        "required_confirmation": (f"{name} confirmation",),\n    }\n    return OracleDebatePosition(\n        **body,\n        position_hash=oit_019_hash(body),\n    )\n\n\ndef finding(\n    index: int,\n    *,\n    leader: str,\n    margin: float,\n    conflict: float,\n    confidence: float,\n    state: str,\n    review: bool,\n):\n    positions = {\n        "bull": position("bull", 0.82 if leader == "bull" else 0.22),\n        "bear": position("bear", 0.82 if leader == "bear" else 0.22),\n        "neutral": position("neutral", 0.82 if leader == "neutral" else 0.22),\n    }\n    body = {\n        "finding_index": index,\n        "cause_record_id": f"CAUSE-{index}",\n        "effect_record_id": f"EFFECT-{index}",\n        "source_challenge_hash": f"challenge-{index}",\n        "original_narrative_state": "certified",\n        "bull": positions["bull"],\n        "bear": positions["bear"],\n        "neutral": positions["neutral"],\n        "leading_position": leader,\n        "debate_margin": margin,\n        "debate_conflict": conflict,\n        "adjudicated_confidence": confidence,\n        "adjudication_state": state,\n        "requires_human_review": review,\n        "adjudication_rationale": ("certified debate rationale",),\n        "read_only": True,\n    }\n    return OracleDebateFinding(\n        **body,\n        finding_hash=oit_019_hash(body),\n    )\n\n\ndef make_report(root: Path):\n    findings = (\n        finding(\n            1,\n            leader="bull",\n            margin=0.48,\n            conflict=0.18,\n            confidence=0.78,\n            state="bull_leading",\n            review=False,\n        ),\n        finding(\n            2,\n            leader="bear",\n            margin=0.14,\n            conflict=0.54,\n            confidence=0.52,\n            state="bear_leading",\n            review=False,\n        ),\n        finding(\n            3,\n            leader="neutral",\n            margin=0.03,\n            conflict=0.88,\n            confidence=0.30,\n            state="contested",\n            review=True,\n        ),\n    )\n    body = {\n        "schema_version": OIT_019_SCHEMA_VERSION,\n        "engine_id": OIT_019_ENGINE_ID,\n        "policy_id": OIT_019_POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root.resolve()),\n        "query": "Assess decision readiness.",\n        "challenge_report_hash": "challenge-report-hash",\n        "findings": findings,\n        "finding_count": len(findings),\n        "bull_leading_count": 1,\n        "bear_leading_count": 1,\n        "neutral_leading_count": 1,\n        "contested_count": 1,\n        "human_review_count": 1,\n        "aggregate_leading_position": "bull",\n        "aggregate_confidence": 0.40,\n        "debate_state": "aggregate_debate_contested",\n        "debate_summary": "Synthetic certified debate.",\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "publication_allowed": False,\n        "qseries_execution_allowed": False,\n        "failure_reason": None,\n    }\n    report = OracleDebateSynthesisReport(\n        **body,\n        report_hash=oit_019_hash(body),\n    )\n    verify_debate_synthesis_report(report)\n    return report\n\n\ndef main() -> int:\n    print("=" * 40)\n    print(" OIT-020 TEST")\n    print(" DECISION READINESS AND ABSTENTION")\n    print("=" * 40)\n\n    with TemporaryDirectory() as temporary:\n        root = Path(temporary)\n        source = make_report(root)\n        report = build_decision_readiness_report(\n            root,\n            source.query,\n            debate_report=source,\n        )\n\n        assert report.debate_report_hash == source.report_hash\n        assert report.finding_count == 3\n        assert report.ready_count == 1\n        assert report.observe_count == 1\n        assert report.abstain_count == 1\n        assert report.human_review_count == 1\n\n        ready, observe, abstain = report.findings\n        assert ready.readiness_state == "ready"\n        assert ready.leading_position == "bull"\n        assert ready.readiness_score > ready.abstention_pressure\n\n        assert observe.readiness_state == "observe"\n        assert observe.leading_position == "bear"\n        assert observe.minimum_confirmation_count == 2\n\n        assert abstain.readiness_state == "abstain"\n        assert abstain.leading_position == "neutral"\n        assert abstain.requires_human_review\n        assert abstain.minimum_confirmation_count == 3\n        assert abstain.abstention_pressure > abstain.readiness_score\n\n        assert report.aggregate_state == "abstain"\n        assert report.aggregate_direction in {"bull", "bear", "neutral"}\n        assert 0.0 <= report.aggregate_readiness <= 1.0\n        assert 0.0 <= report.aggregate_abstention_pressure <= 1.0\n\n        replay = build_decision_readiness_report(\n            root,\n            source.query,\n            debate_report=source,\n        )\n        assert replay == report\n        assert verify_decision_readiness_report(report)\n\n        tampered = replace(\n            report,\n            readiness_summary=report.readiness_summary + " tampered",\n        )\n        try:\n            verify_decision_readiness_report(tampered)\n        except OracleDecisionReadinessInvariantError:\n            pass\n        else:\n            raise AssertionError("tampered readiness report accepted")\n\n        assert report.read_only\n        assert not report.analytics_execution_performed\n        assert not report.database_access_performed\n        assert not report.publication_allowed\n        assert not report.qseries_execution_allowed\n        assert not report.action_authorization_allowed\n\n    print("[PASS] Certified OIT-019 debate report consumed")\n    print("[PASS] Ready state classified from strong debate separation")\n    print("[PASS] Observe state classified from intermediate evidence")\n    print("[PASS] Abstain state enforced for contested human-review case")\n    print("[PASS] Readiness and abstention pressure quantified")\n    print("[PASS] Confirmation requirements materialized")\n    print("[PASS] Disqualifying conditions materialized")\n    print("[PASS] Aggregate abstention conservatively enforced")\n    print("[PASS] Complete OIT-019 lineage retained")\n    print("[PASS] Readiness report deterministic across replay")\n    print("[PASS] Tampered readiness report rejected")\n    print("[PASS] No analytics execution or database access performed")\n    print("[PASS] Publication, action authorization, and Q Series execution disabled")\n    print("[DONE] OIT-020 DECISION READINESS AND ABSTENTION PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


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
    for path in (OIT_019, OIT_019_TEST, RUNNER):
        if path.is_file():
            protected[path] = sha256(path)
    return protected


def main() -> int:
    print("=" * 48)
    print(" OIT-020 INSTALLER")
    print(" DECISION READINESS AND ABSTENTION INTELLIGENCE")
    print("=" * 48)
    try:
        require_contract(
            OIT_019,
            (
                'SCHEMA_VERSION = "OIT-019"',
                'POLICY_ID = "oracle.bull-bear-neutral-debate-synthesis.v1"',
                "OracleDebateSynthesisReport",
                "OracleDebateFinding",
                "build_debate_synthesis_report",
                "verify_debate_synthesis_report",
                "debate_margin",
                "debate_conflict",
                "adjudicated_confidence",
                "requires_human_review",
                "publication_allowed",
                "qseries_execution_allowed",
            ),
            "Certified OIT-019 production",
        )
        require_contract(
            OIT_019_TEST,
            (
                "OIT-019 TEST",
                "BULL BEAR NEUTRAL DEBATE SYNTHESIS",
                "OIT-019 BULL BEAR NEUTRAL DEBATE SYNTHESIS PASS",
            ),
            "Certified OIT-019 standalone test",
        )

        protected = protected_sources()
        print("[OK] Certified OIT-019 production contract verified")
        print("[OK] Certified OIT-019 standalone test verified")
        print(f"[OK] Protected production source files captured: {len(protected)}")

        upstream = subprocess.run(
            [sys.executable, str(OIT_019_TEST)],
            cwd=ROOT,
            check=False,
        )
        if upstream.returncode:
            raise RuntimeError(
                f"OIT-019 certification failed with exit code {upstream.returncode}"
            )

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_decision_readiness_abstention_intelligence import *"
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
                f"OIT-020 test failed with exit code {completed.returncode}"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Protected production source changed: {path}"
                )

        print("[PASS] Certified OIT-019 production and test unchanged")
        print("[PASS] Oracle terminal runner unchanged")
        print("[PASS] OLA, OIA, INT-OII, ORR, OOR, and Q Series unchanged")
        print("[PASS] OIT-020 production module installed")
        print("[PASS] OIT-020 standalone test installed")
        print("[PASS] Ready, observe, and abstain states certified")
        print("[PASS] Human-review pressure conservatively enforced")
        print("[PASS] Action authorization remained disabled")
        print("[PASS] Read-only and execution boundaries preserved")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OIT-020 DECISION READINESS AND ABSTENTION INSTALLED")
        return 0
    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
