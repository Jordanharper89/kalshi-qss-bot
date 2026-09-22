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
            / "oracle_narrative_challenge_self_critique_intelligence.py"
        )
        if required.is_file():
            return candidate
    raise SystemExit("[ERROR] Could not locate current Q Series repository.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"
OIT_017 = (
    PACKAGE
    / "oracle_cross_market_narrative_evolution_intelligence.py"
)
OIT_017_TEST = (
    ROOT
    / "test_oit_017_oracle_cross_market_narrative_evolution_intelligence.py"
)
OIT_018 = (
    PACKAGE
    / "oracle_narrative_challenge_self_critique_intelligence.py"
)
OIT_018_TEST = (
    ROOT
    / "test_oit_018_oracle_narrative_challenge_self_critique_intelligence.py"
)
PRODUCTION = (
    PACKAGE
    / "oracle_bull_bear_neutral_debate_synthesis.py"
)
TEST = (
    ROOT
    / "test_oit_019_oracle_bull_bear_neutral_debate_synthesis.py"
)
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass\nfrom pathlib import Path\nfrom typing import Any, Mapping\n\nfrom .oracle_narrative_challenge_self_critique_intelligence import (\n    OracleNarrativeChallengeFinding,\n    OracleNarrativeChallengeInvariantError,\n    OracleNarrativeChallengeReport,\n    build_narrative_challenge_report,\n    verify_narrative_challenge_report,\n)\n\nSCHEMA_VERSION = "OIT-019"\nENGINE_ID = "OIT-019"\nPOLICY_ID = "oracle.bull-bear-neutral-debate-synthesis.v1"\n\n\nclass OracleDebateSynthesisInvariantError(\n    OracleNarrativeChallengeInvariantError\n):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleDebatePosition:\n    position: str\n    score: float\n    confidence: float\n    supporting_points: tuple[str, ...]\n    opposing_points: tuple[str, ...]\n    required_confirmation: tuple[str, ...]\n    position_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleDebateFinding:\n    finding_index: int\n    cause_record_id: str\n    effect_record_id: str\n    source_challenge_hash: str\n    original_narrative_state: str\n    bull: OracleDebatePosition\n    bear: OracleDebatePosition\n    neutral: OracleDebatePosition\n    leading_position: str\n    debate_margin: float\n    debate_conflict: float\n    adjudicated_confidence: float\n    adjudication_state: str\n    requires_human_review: bool\n    adjudication_rationale: tuple[str, ...]\n    read_only: bool\n    finding_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleDebateSynthesisReport:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    status: str\n    repository_root: str\n    query: str\n    challenge_report_hash: str\n    findings: tuple[OracleDebateFinding, ...]\n    finding_count: int\n    bull_leading_count: int\n    bear_leading_count: int\n    neutral_leading_count: int\n    contested_count: int\n    human_review_count: int\n    aggregate_leading_position: str\n    aggregate_confidence: float\n    debate_state: str\n    debate_summary: str\n    read_only: bool\n    analytics_execution_performed: bool\n    database_access_performed: bool\n    publication_allowed: bool\n    qseries_execution_allowed: bool\n    failure_reason: str | None\n    report_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if isinstance(value, Path):\n        return value.as_posix()\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    return repr(value)\n\n\ndef _stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=True,\n    ).encode("utf-8")\n    return hashlib.sha256(payload).hexdigest()\n\n\ndef _bounded(value: float) -> float:\n    return round(max(0.0, min(1.0, value)), 6)\n\n\ndef _position(\n    position: str,\n    score: float,\n    supporting_points: tuple[str, ...],\n    opposing_points: tuple[str, ...],\n    required_confirmation: tuple[str, ...],\n) -> OracleDebatePosition:\n    bounded_score = _bounded(score)\n    confidence = _bounded(0.50 + abs(bounded_score - 0.50))\n    body = {\n        "position": position,\n        "score": bounded_score,\n        "confidence": confidence,\n        "supporting_points": supporting_points,\n        "opposing_points": opposing_points,\n        "required_confirmation": required_confirmation,\n    }\n    return OracleDebatePosition(\n        **body,\n        position_hash=_stable_hash(body),\n    )\n\n\ndef _derive_positions(\n    source: OracleNarrativeChallengeFinding,\n) -> tuple[OracleDebatePosition, OracleDebatePosition, OracleDebatePosition]:\n    survival = source.surviving_confidence\n    fragility = source.fragility_score\n    counter = source.counter_evidence_pressure\n    assumption = source.assumption_risk\n    falsifiability = source.falsifiability_score\n\n    bull_score = _bounded(\n        (0.55 * survival)\n        + (0.20 * (1.0 - fragility))\n        + (0.15 * falsifiability)\n        + (0.10 * (1.0 - counter))\n    )\n    bear_score = _bounded(\n        (0.45 * counter)\n        + (0.30 * fragility)\n        + (0.15 * assumption)\n        + (0.10 * (1.0 - survival))\n    )\n    neutral_score = _bounded(\n        (0.40 * (1.0 - abs(bull_score - bear_score)))\n        + (0.30 * assumption)\n        + (0.20 * (1.0 - falsifiability))\n        + (0.10 * min(bull_score, bear_score))\n    )\n\n    bull = _position(\n        "bull",\n        bull_score,\n        (\n            f"surviving narrative confidence is {survival:.6f}",\n            f"challenge fragility is bounded at {fragility:.6f}",\n            "certified narrative support survived adversarial review",\n        ),\n        tuple(source.counter_arguments),\n        (\n            "confirm support persists across the next certified update",\n            "confirm evidence remains independent across venues",\n        ),\n    )\n    bear = _position(\n        "bear",\n        bear_score,\n        (\n            f"counter-evidence pressure is {counter:.6f}",\n            f"assumption risk is {assumption:.6f}",\n            *tuple(source.counter_arguments),\n        ),\n        (\n            "surviving confidence may still reflect durable support",\n            "apparent reversal pressure may be temporary",\n        ),\n        (\n            "confirm contradiction persists after temporal refresh",\n            "confirm fragile assumptions fail under new evidence",\n        ),\n    )\n    neutral = _position(\n        "neutral",\n        neutral_score,\n        (\n            f"falsifiability is bounded at {falsifiability:.6f}",\n            "bull and bear interpretations remain explicitly testable",\n            "insufficient separation supports temporary non-directionality",\n        ),\n        (\n            "a meaningful score margin may justify directional preference",\n            "new evidence may resolve the current ambiguity",\n        ),\n        tuple(source.falsification_tests),\n    )\n    return bull, bear, neutral\n\n\ndef _build_finding(\n    source: OracleNarrativeChallengeFinding,\n    index: int,\n) -> OracleDebateFinding:\n    bull, bear, neutral = _derive_positions(source)\n    scores = {\n        "bull": bull.score,\n        "bear": bear.score,\n        "neutral": neutral.score,\n    }\n    ordered = sorted(\n        scores.items(),\n        key=lambda item: (-item[1], item[0]),\n    )\n    leader, leading_score = ordered[0]\n    runner_up_score = ordered[1][1]\n    margin = _bounded(leading_score - runner_up_score)\n    conflict = _bounded(\n        1.0 - (max(scores.values()) - min(scores.values()))\n    )\n\n    if margin < 0.08:\n        adjudication_state = "contested"\n        requires_review = True\n    elif source.challenge_state == "failed" and leader != "bear":\n        adjudication_state = "challenge_conflict"\n        requires_review = True\n    elif source.challenge_state == "passed" and leader == "bear":\n        adjudication_state = "challenge_conflict"\n        requires_review = True\n    else:\n        adjudication_state = f"{leader}_leading"\n        requires_review = False\n\n    adjudicated_confidence = _bounded(\n        (0.55 * leading_score)\n        + (0.25 * margin)\n        + (0.20 * (1.0 - conflict))\n    )\n\n    rationale = (\n        f"bull score: {bull.score:.6f}",\n        f"bear score: {bear.score:.6f}",\n        f"neutral score: {neutral.score:.6f}",\n        f"leading position: {leader}",\n        f"debate margin: {margin:.6f}",\n        f"debate conflict: {conflict:.6f}",\n        f"adjudicated confidence: {adjudicated_confidence:.6f}",\n        "adjudication is observational and cannot authorize action",\n    )\n\n    body = {\n        "finding_index": index,\n        "cause_record_id": source.cause_record_id,\n        "effect_record_id": source.effect_record_id,\n        "source_challenge_hash": source.finding_hash,\n        "original_narrative_state": source.original_narrative_state,\n        "bull": bull,\n        "bear": bear,\n        "neutral": neutral,\n        "leading_position": leader,\n        "debate_margin": margin,\n        "debate_conflict": conflict,\n        "adjudicated_confidence": adjudicated_confidence,\n        "adjudication_state": adjudication_state,\n        "requires_human_review": requires_review,\n        "adjudication_rationale": rationale,\n        "read_only": True,\n    }\n    return OracleDebateFinding(\n        **body,\n        finding_hash=_stable_hash(body),\n    )\n\n\ndef verify_debate_position(position: OracleDebatePosition) -> bool:\n    body = asdict(position)\n    supplied = body.pop("position_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleDebateSynthesisInvariantError(\n            "debate position hash mismatch"\n        )\n    if position.position not in {"bull", "bear", "neutral"}:\n        raise OracleDebateSynthesisInvariantError(\n            "unsupported debate position"\n        )\n    for value in (position.score, position.confidence):\n        if not 0.0 <= value <= 1.0:\n            raise OracleDebateSynthesisInvariantError(\n                "debate position metric outside bounded range"\n            )\n    if not position.supporting_points:\n        raise OracleDebateSynthesisInvariantError(\n            "debate supporting points missing"\n        )\n    if not position.opposing_points:\n        raise OracleDebateSynthesisInvariantError(\n            "debate opposing points missing"\n        )\n    if not position.required_confirmation:\n        raise OracleDebateSynthesisInvariantError(\n            "debate confirmation requirements missing"\n        )\n    return True\n\n\ndef verify_debate_finding(finding: OracleDebateFinding) -> bool:\n    body = asdict(finding)\n    supplied = body.pop("finding_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleDebateSynthesisInvariantError(\n            "debate finding hash mismatch"\n        )\n    if not finding.read_only:\n        raise OracleDebateSynthesisInvariantError(\n            "debate finding is not read-only"\n        )\n    for position in (finding.bull, finding.bear, finding.neutral):\n        verify_debate_position(position)\n    if finding.leading_position not in {"bull", "bear", "neutral"}:\n        raise OracleDebateSynthesisInvariantError(\n            "invalid leading debate position"\n        )\n    for value in (\n        finding.debate_margin,\n        finding.debate_conflict,\n        finding.adjudicated_confidence,\n    ):\n        if not 0.0 <= value <= 1.0:\n            raise OracleDebateSynthesisInvariantError(\n                "debate metric outside bounded range"\n            )\n    scores = {\n        "bull": finding.bull.score,\n        "bear": finding.bear.score,\n        "neutral": finding.neutral.score,\n    }\n    expected_leader = sorted(\n        scores.items(),\n        key=lambda item: (-item[1], item[0]),\n    )[0][0]\n    if finding.leading_position != expected_leader:\n        raise OracleDebateSynthesisInvariantError(\n            "leading debate position mismatch"\n        )\n    if not finding.source_challenge_hash:\n        raise OracleDebateSynthesisInvariantError(\n            "challenge lineage missing"\n        )\n    return True\n\n\ndef _aggregate(\n    findings: tuple[OracleDebateFinding, ...],\n) -> tuple[str, float, str, str]:\n    if not findings:\n        return (\n            "neutral",\n            0.0,\n            "no_debate_evidence",\n            "No certified challenge findings were available for debate.",\n        )\n\n    totals = {\n        position: sum(\n            getattr(item, position).score for item in findings\n        )\n        for position in ("bull", "bear", "neutral")\n    }\n    ordered = sorted(\n        totals.items(),\n        key=lambda item: (-item[1], item[0]),\n    )\n    leader = ordered[0][0]\n    total_score = sum(totals.values())\n    confidence = _bounded(\n        ordered[0][1] / total_score if total_score else 0.0\n    )\n    contested = sum(\n        item.adjudication_state in {"contested", "challenge_conflict"}\n        for item in findings\n    )\n    state = (\n        "aggregate_debate_contested"\n        if contested\n        else f"aggregate_{leader}_leading"\n    )\n    summary = (\n        f"{len(findings)} debate findings; aggregate {leader} position "\n        f"leads with normalized confidence {confidence:.6f}; "\n        f"{contested} findings remain contested."\n    )\n    return leader, confidence, state, summary\n\n\ndef build_debate_synthesis_report(\n    repository_root: str | Path,\n    query: str,\n    *,\n    challenge_report: OracleNarrativeChallengeReport | None = None,\n) -> OracleDebateSynthesisReport:\n    root = Path(repository_root).resolve()\n    source = challenge_report\n    if source is None:\n        source = build_narrative_challenge_report(root, query)\n    verify_narrative_challenge_report(source)\n\n    findings = tuple(\n        _build_finding(item, index)\n        for index, item in enumerate(source.findings, start=1)\n    )\n    for finding in findings:\n        verify_debate_finding(finding)\n\n    leader, confidence, state, summary = _aggregate(findings)\n    bull_count = sum(item.leading_position == "bull" for item in findings)\n    bear_count = sum(item.leading_position == "bear" for item in findings)\n    neutral_count = sum(item.leading_position == "neutral" for item in findings)\n    contested_count = sum(\n        item.adjudication_state in {"contested", "challenge_conflict"}\n        for item in findings\n    )\n    human_review_count = sum(item.requires_human_review for item in findings)\n\n    body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root),\n        "query": str(query),\n        "challenge_report_hash": source.report_hash,\n        "findings": findings,\n        "finding_count": len(findings),\n        "bull_leading_count": bull_count,\n        "bear_leading_count": bear_count,\n        "neutral_leading_count": neutral_count,\n        "contested_count": contested_count,\n        "human_review_count": human_review_count,\n        "aggregate_leading_position": leader,\n        "aggregate_confidence": confidence,\n        "debate_state": state,\n        "debate_summary": summary,\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "publication_allowed": False,\n        "qseries_execution_allowed": False,\n        "failure_reason": None,\n    }\n    report = OracleDebateSynthesisReport(\n        **body,\n        report_hash=_stable_hash(body),\n    )\n    verify_debate_synthesis_report(report)\n    return report\n\n\ndef verify_debate_synthesis_report(\n    report: OracleDebateSynthesisReport,\n) -> bool:\n    body = asdict(report)\n    supplied = body.pop("report_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleDebateSynthesisInvariantError(\n            "debate synthesis report hash mismatch"\n        )\n    if report.schema_version != SCHEMA_VERSION:\n        raise OracleDebateSynthesisInvariantError("schema mismatch")\n    if report.policy_id != POLICY_ID:\n        raise OracleDebateSynthesisInvariantError("policy mismatch")\n    if not report.read_only:\n        raise OracleDebateSynthesisInvariantError(\n            "debate report is not read-only"\n        )\n    if (\n        report.analytics_execution_performed\n        or report.database_access_performed\n        or report.publication_allowed\n        or report.qseries_execution_allowed\n    ):\n        raise OracleDebateSynthesisInvariantError(\n            "forbidden runtime capability enabled"\n        )\n    if report.finding_count != len(report.findings):\n        raise OracleDebateSynthesisInvariantError(\n            "debate finding count mismatch"\n        )\n    expected = {\n        "bull": report.bull_leading_count,\n        "bear": report.bear_leading_count,\n        "neutral": report.neutral_leading_count,\n    }\n    for position, count in expected.items():\n        actual = sum(\n            item.leading_position == position\n            for item in report.findings\n        )\n        if actual != count:\n            raise OracleDebateSynthesisInvariantError(\n                f"{position} leading count mismatch"\n            )\n    if sum(expected.values()) != report.finding_count:\n        raise OracleDebateSynthesisInvariantError(\n            "classified debate count mismatch"\n        )\n    actual_contested = sum(\n        item.adjudication_state in {"contested", "challenge_conflict"}\n        for item in report.findings\n    )\n    if actual_contested != report.contested_count:\n        raise OracleDebateSynthesisInvariantError(\n            "contested debate count mismatch"\n        )\n    actual_review = sum(\n        item.requires_human_review for item in report.findings\n    )\n    if actual_review != report.human_review_count:\n        raise OracleDebateSynthesisInvariantError(\n            "human review count mismatch"\n        )\n    if report.aggregate_leading_position not in {\n        "bull", "bear", "neutral"\n    }:\n        raise OracleDebateSynthesisInvariantError(\n            "invalid aggregate debate position"\n        )\n    if not 0.0 <= report.aggregate_confidence <= 1.0:\n        raise OracleDebateSynthesisInvariantError(\n            "aggregate confidence outside bounded range"\n        )\n    for finding in report.findings:\n        verify_debate_finding(finding)\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import replace\nfrom pathlib import Path\nfrom tempfile import TemporaryDirectory\n\nfrom qseries_v2.oracle_terminal.oracle_narrative_challenge_self_critique_intelligence import (\n    ENGINE_ID as OIT_018_ENGINE_ID,\n    POLICY_ID as OIT_018_POLICY_ID,\n    SCHEMA_VERSION as OIT_018_SCHEMA_VERSION,\n    OracleNarrativeChallengeFinding,\n    OracleNarrativeChallengeReport,\n    _stable_hash as oit_018_hash,\n    verify_narrative_challenge_report,\n)\nfrom qseries_v2.oracle_terminal.oracle_bull_bear_neutral_debate_synthesis import (\n    OracleDebateSynthesisInvariantError,\n    build_debate_synthesis_report,\n    verify_debate_synthesis_report,\n)\n\n\ndef make_challenge(\n    index: int,\n    cause: str,\n    effect: str,\n    *,\n    narrative_state: str,\n    challenge_state: str,\n    fragility: float,\n    counter: float,\n    assumption: float,\n    falsifiability: float,\n    survival: float,\n):\n    body = {\n        "finding_index": index,\n        "cause_record_id": cause,\n        "effect_record_id": effect,\n        "source_narrative_hash": f"narrative-{index}",\n        "original_narrative_state": narrative_state,\n        "challenge_state": challenge_state,\n        "fragility_score": fragility,\n        "counter_evidence_pressure": counter,\n        "assumption_risk": assumption,\n        "falsifiability_score": falsifiability,\n        "surviving_confidence": survival,\n        "challenge_passed": challenge_state == "passed",\n        "fragile_assumptions": (\n            "the observed relationship persists out of sample",\n        ),\n        "counter_arguments": (\n            "an alternative interpretation remains possible",\n        ),\n        "falsification_tests": (\n            "recalculate after the next certified temporal update",\n        ),\n        "critique_rationale": (\n            "certified challenge finding",\n        ),\n        "read_only": True,\n    }\n    return OracleNarrativeChallengeFinding(\n        **body,\n        finding_hash=oit_018_hash(body),\n    )\n\n\ndef make_report(root: Path):\n    findings = (\n        make_challenge(\n            1,\n            "ETF-FLOW",\n            "BTC-PRICE",\n            narrative_state="strengthening",\n            challenge_state="passed",\n            fragility=0.18,\n            counter=0.12,\n            assumption=0.20,\n            falsifiability=0.80,\n            survival=0.82,\n        ),\n        make_challenge(\n            2,\n            "MINER-STRESS",\n            "BTC-PRICE",\n            narrative_state="reversing",\n            challenge_state="failed",\n            fragility=0.82,\n            counter=0.88,\n            assumption=0.76,\n            falsifiability=0.70,\n            survival=0.18,\n        ),\n        make_challenge(\n            3,\n            "MACRO-LIQUIDITY",\n            "BTC-PRICE",\n            narrative_state="fragmented",\n            challenge_state="weakened",\n            fragility=0.50,\n            counter=0.48,\n            assumption=0.62,\n            falsifiability=0.55,\n            survival=0.48,\n        ),\n    )\n    body = {\n        "schema_version": OIT_018_SCHEMA_VERSION,\n        "engine_id": OIT_018_ENGINE_ID,\n        "policy_id": OIT_018_POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root.resolve()),\n        "query": "Debate the Bitcoin market direction.",\n        "narrative_report_hash": "narrative-report-hash",\n        "findings": findings,\n        "finding_count": len(findings),\n        "passed_count": sum(\n            item.challenge_state == "passed" for item in findings\n        ),\n        "weakened_count": sum(\n            item.challenge_state == "weakened" for item in findings\n        ),\n        "failed_count": sum(\n            item.challenge_state == "failed" for item in findings\n        ),\n        "fragile_count": sum(\n            item.fragility_score >= 0.45 for item in findings\n        ),\n        "monitoring_required_count": sum(\n            item.challenge_state != "passed"\n            or item.fragility_score >= 0.45\n            for item in findings\n        ),\n        "challenge_state": "one_or_more_narratives_failed_challenge",\n        "challenge_summary": "Passed, failed, and weakened narratives present.",\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "publication_allowed": False,\n        "qseries_execution_allowed": False,\n        "failure_reason": None,\n    }\n    report = OracleNarrativeChallengeReport(\n        **body,\n        report_hash=oit_018_hash(body),\n    )\n    verify_narrative_challenge_report(report)\n    return report\n\n\ndef main() -> int:\n    print("=" * 40)\n    print(" OIT-019 TEST")\n    print(" BULL BEAR NEUTRAL DEBATE SYNTHESIS")\n    print("=" * 40)\n\n    with TemporaryDirectory() as temporary:\n        root = Path(temporary)\n        source = make_report(root)\n        report = build_debate_synthesis_report(\n            root,\n            source.query,\n            challenge_report=source,\n        )\n\n        assert report.challenge_report_hash == source.report_hash\n        assert report.finding_count == 3\n        assert report.bull_leading_count >= 1\n        assert report.bear_leading_count >= 1\n        assert (\n            report.bull_leading_count\n            + report.bear_leading_count\n            + report.neutral_leading_count\n            == report.finding_count\n        )\n\n        first, second, third = report.findings\n        assert first.leading_position == "bull"\n        assert second.leading_position == "bear"\n        assert first.bull.score > first.bear.score\n        assert second.bear.score > second.bull.score\n\n        for finding in report.findings:\n            assert finding.bull.position == "bull"\n            assert finding.bear.position == "bear"\n            assert finding.neutral.position == "neutral"\n            assert finding.source_challenge_hash\n            assert finding.adjudication_rationale\n            assert 0.0 <= finding.debate_margin <= 1.0\n            assert 0.0 <= finding.debate_conflict <= 1.0\n            assert 0.0 <= finding.adjudicated_confidence <= 1.0\n\n        assert third.original_narrative_state == "fragmented"\n        assert report.aggregate_leading_position in {\n            "bull", "bear", "neutral"\n        }\n        assert 0.0 <= report.aggregate_confidence <= 1.0\n\n        replay = build_debate_synthesis_report(\n            root,\n            source.query,\n            challenge_report=source,\n        )\n        assert replay == report\n        assert verify_debate_synthesis_report(report)\n\n        tampered = replace(\n            report,\n            debate_summary=report.debate_summary + " tampered",\n        )\n        try:\n            verify_debate_synthesis_report(tampered)\n        except OracleDebateSynthesisInvariantError:\n            pass\n        else:\n            raise AssertionError("tampered debate report accepted")\n\n        assert report.read_only\n        assert not report.analytics_execution_performed\n        assert not report.database_access_performed\n        assert not report.publication_allowed\n        assert not report.qseries_execution_allowed\n\n    print("[PASS] Certified OIT-018 challenge report consumed")\n    print("[PASS] Bull case constructed and scored")\n    print("[PASS] Bear case constructed and scored")\n    print("[PASS] Neutral case constructed and scored")\n    print("[PASS] Strong surviving narrative produces bull lead")\n    print("[PASS] Failed fragile narrative produces bear lead")\n    print("[PASS] Debate margin and conflict quantified")\n    print("[PASS] Aggregate position adjudicated deterministically")\n    print("[PASS] Complete OIT-018 lineage retained")\n    print("[PASS] Debate report deterministic across replay")\n    print("[PASS] Tampered debate report rejected")\n    print("[PASS] No analytics execution or database access performed")\n    print("[PASS] Publication and Q Series execution disabled")\n    print("[DONE] OIT-019 BULL BEAR NEUTRAL DEBATE SYNTHESIS PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_complete(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def require_contract(path: Path, tokens: tuple[str, ...], name: str) -> None:
    if not path.is_file():
        raise RuntimeError(f"{name} missing: {path}")
    source = path.read_text(encoding="utf-8")
    missing = [token for token in tokens if token not in source]
    if missing:
        raise RuntimeError(f"{name} contract mismatch: {missing}")


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
    for path in (
        OIT_017,
        OIT_017_TEST,
        OIT_018,
        OIT_018_TEST,
        RUNNER,
    ):
        if path.is_file():
            protected[path] = sha256(path)
    return protected


def main() -> int:
    print("=" * 40)
    print(" OIT-019 INSTALLER")
    print(" BULL BEAR NEUTRAL DEBATE SYNTHESIS")
    print("=" * 40)
    try:
        require_contract(
            OIT_017,
            (
                'SCHEMA_VERSION = "OIT-017"',
                (
                    'POLICY_ID = '
                    '"oracle.cross-market-narrative-evolution-intelligence.v1"'
                ),
                "OracleNarrativeEvolutionReport",
                "verify_narrative_evolution_report",
            ),
            "Certified OIT-017 production",
        )
        require_contract(
            OIT_017_TEST,
            (
                "OIT-017 CORRECTION V2 TEST",
                "OIT-017 CORRECTION V2 NARRATIVE EVOLUTION PASS",
            ),
            "Corrected OIT-017 standalone test",
        )
        require_contract(
            OIT_018,
            (
                'SCHEMA_VERSION = "OIT-018"',
                (
                    'POLICY_ID = '
                    '"oracle.narrative-challenge-self-critique-intelligence.v1"'
                ),
                "OracleNarrativeChallengeReport",
                "OracleNarrativeChallengeFinding",
                "build_narrative_challenge_report",
                "verify_narrative_challenge_report",
                "surviving_confidence",
                "fragility_score",
                "counter_arguments",
                "falsification_tests",
                "publication_allowed",
                "qseries_execution_allowed",
            ),
            "Certified OIT-018 production",
        )
        require_contract(
            OIT_018_TEST,
            (
                "OIT-018 CORRECTION V2 TEST",
                "Corrected certified OIT-017 narrative report consumed",
                "OIT-018 CORRECTION V2 SELF-CRITIQUE PASS",
            ),
            "Corrected OIT-018 standalone test",
        )

        protected = protected_sources()
        print("[OK] Corrected OIT-017 certification chain verified")
        print("[OK] Certified OIT-018 challenge contract verified")
        print("[OK] OIT-018 Correction V2 standalone test verified")
        print(
            f"[OK] Protected production source files captured: "
            f"{len(protected)}"
        )

        upstream_017 = subprocess.run(
            [sys.executable, str(OIT_017_TEST)],
            cwd=ROOT,
            check=False,
        )
        if upstream_017.returncode:
            raise RuntimeError(
                f"OIT-017 certification failed with exit code "
                f"{upstream_017.returncode}"
            )

        upstream_018 = subprocess.run(
            [sys.executable, str(OIT_018_TEST)],
            cwd=ROOT,
            check=False,
        )
        if upstream_018.returncode:
            raise RuntimeError(
                f"OIT-018 certification failed with exit code "
                f"{upstream_018.returncode}"
            )

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_bull_bear_neutral_debate_synthesis import *"
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
                f"OIT-019 test failed with exit code "
                f"{completed.returncode}"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Protected production source changed: {path}"
                )

        print("[PASS] Corrected OIT-017 production and test unchanged")
        print("[PASS] Certified OIT-018 production and test unchanged")
        print("[PASS] Oracle terminal runner unchanged")
        print("[PASS] OLA, OIA, INT-OII, ORR, OOR, and Q Series unchanged")
        print("[PASS] OIT-019 production module installed")
        print("[PASS] OIT-019 standalone test installed")
        print("[PASS] Bull, bear, and neutral positions synthesized")
        print("[PASS] Debate adjudication and conflict metrics bounded")
        print("[PASS] Read-only and execution boundaries preserved")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OIT-019 BULL BEAR NEUTRAL DEBATE SYNTHESIS INSTALLED")
        return 0
    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
