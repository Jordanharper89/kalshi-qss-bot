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
            / "oracle_cross_market_narrative_evolution_intelligence.py"
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
PRODUCTION = (
    PACKAGE
    / "oracle_narrative_challenge_self_critique_intelligence.py"
)
TEST = (
    ROOT
    / "test_oit_018_oracle_narrative_challenge_self_critique_intelligence.py"
)
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass\nfrom pathlib import Path\nfrom typing import Any, Mapping\n\nfrom .oracle_cross_market_narrative_evolution_intelligence import (\n    OracleNarrativeEvolutionFinding,\n    OracleNarrativeEvolutionInvariantError,\n    OracleNarrativeEvolutionReport,\n    build_narrative_evolution_report,\n    verify_narrative_evolution_report,\n)\n\nSCHEMA_VERSION = "OIT-018"\nENGINE_ID = "OIT-018"\nPOLICY_ID = "oracle.narrative-challenge-self-critique-intelligence.v1"\n\n\nclass OracleNarrativeChallengeInvariantError(\n    OracleNarrativeEvolutionInvariantError\n):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleNarrativeChallengeFinding:\n    finding_index: int\n    cause_record_id: str\n    effect_record_id: str\n    source_narrative_hash: str\n    original_narrative_state: str\n    challenge_state: str\n    fragility_score: float\n    counter_evidence_pressure: float\n    assumption_risk: float\n    falsifiability_score: float\n    surviving_confidence: float\n    challenge_passed: bool\n    fragile_assumptions: tuple[str, ...]\n    counter_arguments: tuple[str, ...]\n    falsification_tests: tuple[str, ...]\n    critique_rationale: tuple[str, ...]\n    read_only: bool\n    finding_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleNarrativeChallengeReport:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    status: str\n    repository_root: str\n    query: str\n    narrative_report_hash: str\n    findings: tuple[OracleNarrativeChallengeFinding, ...]\n    finding_count: int\n    passed_count: int\n    weakened_count: int\n    failed_count: int\n    fragile_count: int\n    monitoring_required_count: int\n    challenge_state: str\n    challenge_summary: str\n    read_only: bool\n    analytics_execution_performed: bool\n    database_access_performed: bool\n    publication_allowed: bool\n    qseries_execution_allowed: bool\n    failure_reason: str | None\n    report_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if isinstance(value, Path):\n        return value.as_posix()\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    return repr(value)\n\n\ndef _stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=True,\n    ).encode("utf-8")\n    return hashlib.sha256(payload).hexdigest()\n\n\ndef _bounded(value: float) -> float:\n    return round(max(0.0, min(1.0, value)), 6)\n\n\ndef _challenge(\n    source: OracleNarrativeEvolutionFinding,\n) -> tuple[\n    str,\n    float,\n    float,\n    float,\n    float,\n    float,\n    bool,\n    tuple[str, ...],\n    tuple[str, ...],\n    tuple[str, ...],\n    tuple[str, ...],\n]:\n    contradiction = source.contradiction_pressure\n    uncertainty = source.uncertainty_pressure\n    reversal = source.reversal_risk\n    support_gap = 1.0 - source.evidence_support\n    instability = 1.0 - source.narrative_stability\n\n    counter_pressure = _bounded(\n        (0.45 * contradiction)\n        + (0.30 * reversal)\n        + (0.25 * uncertainty)\n    )\n    assumption_risk = _bounded(\n        (0.35 * uncertainty)\n        + (0.35 * instability)\n        + (0.30 * support_gap)\n    )\n    fragility = _bounded(\n        (0.40 * counter_pressure)\n        + (0.35 * assumption_risk)\n        + (0.25 * instability)\n    )\n    falsifiability = _bounded(\n        0.55\n        + (0.15 if source.evolution_signals else 0.0)\n        + (0.15 if source.requires_monitoring else 0.0)\n        - (0.20 * uncertainty)\n    )\n    surviving_confidence = _bounded(\n        source.narrative_strength\n        * (1.0 - (0.55 * fragility))\n        * (1.0 - (0.25 * counter_pressure))\n    )\n\n    if fragility >= 0.70 or surviving_confidence < 0.25:\n        challenge_state = "failed"\n        challenge_passed = False\n    elif fragility >= 0.45 or surviving_confidence < 0.50:\n        challenge_state = "weakened"\n        challenge_passed = False\n    else:\n        challenge_state = "passed"\n        challenge_passed = True\n\n    assumptions: list[str] = []\n    if source.evidence_support < 0.60:\n        assumptions.append("supporting evidence is representative and sufficiently complete")\n    if source.narrative_stability < 0.60:\n        assumptions.append("the observed narrative relationship remains stable")\n    if source.reversal_risk >= 0.50:\n        assumptions.append("opposing evidence will not dominate the narrative")\n    if source.uncertainty_pressure >= 0.50:\n        assumptions.append("unresolved uncertainty does not conceal a confounder")\n    if not assumptions:\n        assumptions.append("the observed cross-market relationship persists out of sample")\n\n    counter_arguments: list[str] = []\n    if contradiction >= 0.40:\n        counter_arguments.append("directional contradiction may invalidate the dominant interpretation")\n    if reversal >= 0.50:\n        counter_arguments.append("current evidence may represent an early narrative reversal")\n    if uncertainty >= 0.50:\n        counter_arguments.append("missing evidence may support a materially different explanation")\n    if source.narrative_state == "strengthening":\n        counter_arguments.append("recent support may be temporary momentum rather than durable structure")\n    elif source.narrative_state == "reversing":\n        counter_arguments.append("the apparent reversal may be transient hedging or substitution")\n    else:\n        counter_arguments.append("the narrative may be associative rather than causally durable")\n\n    falsification_tests = (\n        "observe whether the proposed effect persists after the cause weakens",\n        "seek independent evidence from a separate source and venue",\n        "test whether the relationship survives contradictory observations",\n        "recalculate after the next certified temporal update",\n    )\n\n    rationale = (\n        f"counter-evidence pressure: {counter_pressure:.6f}",\n        f"assumption risk: {assumption_risk:.6f}",\n        f"fragility score: {fragility:.6f}",\n        f"falsifiability score: {falsifiability:.6f}",\n        f"surviving confidence: {surviving_confidence:.6f}",\n        "self-critique cannot modify certified source evidence",\n    )\n\n    return (\n        challenge_state,\n        fragility,\n        counter_pressure,\n        assumption_risk,\n        falsifiability,\n        surviving_confidence,\n        challenge_passed,\n        tuple(assumptions),\n        tuple(counter_arguments),\n        falsification_tests,\n        rationale,\n    )\n\n\ndef _build_finding(\n    source: OracleNarrativeEvolutionFinding,\n    index: int,\n) -> OracleNarrativeChallengeFinding:\n    (\n        challenge_state,\n        fragility,\n        counter_pressure,\n        assumption_risk,\n        falsifiability,\n        surviving_confidence,\n        challenge_passed,\n        assumptions,\n        counter_arguments,\n        falsification_tests,\n        rationale,\n    ) = _challenge(source)\n\n    body = {\n        "finding_index": index,\n        "cause_record_id": source.cause_record_id,\n        "effect_record_id": source.effect_record_id,\n        "source_narrative_hash": source.finding_hash,\n        "original_narrative_state": source.narrative_state,\n        "challenge_state": challenge_state,\n        "fragility_score": fragility,\n        "counter_evidence_pressure": counter_pressure,\n        "assumption_risk": assumption_risk,\n        "falsifiability_score": falsifiability,\n        "surviving_confidence": surviving_confidence,\n        "challenge_passed": challenge_passed,\n        "fragile_assumptions": assumptions,\n        "counter_arguments": counter_arguments,\n        "falsification_tests": falsification_tests,\n        "critique_rationale": rationale,\n        "read_only": True,\n    }\n    return OracleNarrativeChallengeFinding(\n        **body,\n        finding_hash=_stable_hash(body),\n    )\n\n\ndef verify_narrative_challenge_finding(\n    finding: OracleNarrativeChallengeFinding,\n) -> bool:\n    body = asdict(finding)\n    supplied = body.pop("finding_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleNarrativeChallengeInvariantError(\n            "narrative challenge finding hash mismatch"\n        )\n    if not finding.read_only:\n        raise OracleNarrativeChallengeInvariantError(\n            "narrative challenge finding is not read-only"\n        )\n    for value in (\n        finding.fragility_score,\n        finding.counter_evidence_pressure,\n        finding.assumption_risk,\n        finding.falsifiability_score,\n        finding.surviving_confidence,\n    ):\n        if not 0.0 <= value <= 1.0:\n            raise OracleNarrativeChallengeInvariantError(\n                "challenge metric outside bounded range"\n            )\n    if finding.challenge_passed != (finding.challenge_state == "passed"):\n        raise OracleNarrativeChallengeInvariantError(\n            "challenge pass state mismatch"\n        )\n    if not finding.source_narrative_hash:\n        raise OracleNarrativeChallengeInvariantError(\n            "source narrative lineage missing"\n        )\n    if not finding.fragile_assumptions:\n        raise OracleNarrativeChallengeInvariantError(\n            "fragile assumptions missing"\n        )\n    if not finding.counter_arguments:\n        raise OracleNarrativeChallengeInvariantError(\n            "counter arguments missing"\n        )\n    if not finding.falsification_tests:\n        raise OracleNarrativeChallengeInvariantError(\n            "falsification tests missing"\n        )\n    return True\n\n\ndef _summary(\n    findings: tuple[OracleNarrativeChallengeFinding, ...],\n) -> tuple[str, str]:\n    if not findings:\n        return (\n            "no_narratives_to_challenge",\n            "No certified narrative findings were available for self-critique.",\n        )\n\n    passed = sum(item.challenge_state == "passed" for item in findings)\n    weakened = sum(item.challenge_state == "weakened" for item in findings)\n    failed = sum(item.challenge_state == "failed" for item in findings)\n    fragile = sum(item.fragility_score >= 0.45 for item in findings)\n    monitoring = sum(\n        item.challenge_state != "passed"\n        or item.fragility_score >= 0.45\n        for item in findings\n    )\n\n    if failed:\n        state = "one_or_more_narratives_failed_challenge"\n    elif weakened:\n        state = "one_or_more_narratives_weakened"\n    else:\n        state = "all_narratives_survived_bounded_challenge"\n\n    return (\n        state,\n        (\n            f"{len(findings)} challenged narratives: "\n            f"{passed} passed, {weakened} weakened, {failed} failed; "\n            f"{fragile} fragile and {monitoring} require monitoring."\n        ),\n    )\n\n\ndef build_narrative_challenge_report(\n    repository_root: str | Path,\n    query: str,\n    *,\n    narrative_report: OracleNarrativeEvolutionReport | None = None,\n) -> OracleNarrativeChallengeReport:\n    root = Path(repository_root).resolve()\n    source = narrative_report\n    if source is None:\n        source = build_narrative_evolution_report(root, query)\n    verify_narrative_evolution_report(source)\n\n    findings = tuple(\n        _build_finding(item, index)\n        for index, item in enumerate(source.findings, start=1)\n    )\n    for finding in findings:\n        verify_narrative_challenge_finding(finding)\n\n    challenge_state, challenge_summary = _summary(findings)\n    passed = sum(item.challenge_state == "passed" for item in findings)\n    weakened = sum(item.challenge_state == "weakened" for item in findings)\n    failed = sum(item.challenge_state == "failed" for item in findings)\n    fragile = sum(item.fragility_score >= 0.45 for item in findings)\n    monitoring = sum(\n        item.challenge_state != "passed"\n        or item.fragility_score >= 0.45\n        for item in findings\n    )\n\n    body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root),\n        "query": str(query),\n        "narrative_report_hash": source.report_hash,\n        "findings": findings,\n        "finding_count": len(findings),\n        "passed_count": passed,\n        "weakened_count": weakened,\n        "failed_count": failed,\n        "fragile_count": fragile,\n        "monitoring_required_count": monitoring,\n        "challenge_state": challenge_state,\n        "challenge_summary": challenge_summary,\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "publication_allowed": False,\n        "qseries_execution_allowed": False,\n        "failure_reason": None,\n    }\n    report = OracleNarrativeChallengeReport(\n        **body,\n        report_hash=_stable_hash(body),\n    )\n    verify_narrative_challenge_report(report)\n    return report\n\n\ndef verify_narrative_challenge_report(\n    report: OracleNarrativeChallengeReport,\n) -> bool:\n    body = asdict(report)\n    supplied = body.pop("report_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleNarrativeChallengeInvariantError(\n            "narrative challenge report hash mismatch"\n        )\n    if report.schema_version != SCHEMA_VERSION:\n        raise OracleNarrativeChallengeInvariantError("schema mismatch")\n    if report.policy_id != POLICY_ID:\n        raise OracleNarrativeChallengeInvariantError("policy mismatch")\n    if not report.read_only:\n        raise OracleNarrativeChallengeInvariantError(\n            "report is not read-only"\n        )\n    if (\n        report.analytics_execution_performed\n        or report.database_access_performed\n        or report.publication_allowed\n        or report.qseries_execution_allowed\n    ):\n        raise OracleNarrativeChallengeInvariantError(\n            "forbidden runtime capability enabled"\n        )\n    if report.finding_count != len(report.findings):\n        raise OracleNarrativeChallengeInvariantError(\n            "finding count mismatch"\n        )\n\n    expected = {\n        "passed": report.passed_count,\n        "weakened": report.weakened_count,\n        "failed": report.failed_count,\n    }\n    for state, count in expected.items():\n        actual = sum(\n            item.challenge_state == state\n            for item in report.findings\n        )\n        if actual != count:\n            raise OracleNarrativeChallengeInvariantError(\n                f"{state} challenge count mismatch"\n            )\n    if sum(expected.values()) != report.finding_count:\n        raise OracleNarrativeChallengeInvariantError(\n            "classified challenge count mismatch"\n        )\n\n    actual_fragile = sum(\n        item.fragility_score >= 0.45 for item in report.findings\n    )\n    if actual_fragile != report.fragile_count:\n        raise OracleNarrativeChallengeInvariantError(\n            "fragile finding count mismatch"\n        )\n    actual_monitoring = sum(\n        item.challenge_state != "passed"\n        or item.fragility_score >= 0.45\n        for item in report.findings\n    )\n    if actual_monitoring != report.monitoring_required_count:\n        raise OracleNarrativeChallengeInvariantError(\n            "monitoring count mismatch"\n        )\n\n    for finding in report.findings:\n        verify_narrative_challenge_finding(finding)\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import replace\nfrom pathlib import Path\nfrom tempfile import TemporaryDirectory\n\nfrom qseries_v2.oracle_terminal.oracle_cross_market_narrative_evolution_intelligence import (\n    ENGINE_ID as OIT_017_ENGINE_ID,\n    POLICY_ID as OIT_017_POLICY_ID,\n    SCHEMA_VERSION as OIT_017_SCHEMA_VERSION,\n    OracleNarrativeEvolutionFinding,\n    OracleNarrativeEvolutionReport,\n    _stable_hash as oit_017_hash,\n    verify_narrative_evolution_report,\n)\nfrom qseries_v2.oracle_terminal.oracle_narrative_challenge_self_critique_intelligence import (\n    OracleNarrativeChallengeInvariantError,\n    build_narrative_challenge_report,\n    verify_narrative_challenge_report,\n)\n\n\ndef make_narrative(\n    index: int,\n    cause: str,\n    effect: str,\n    *,\n    state: str,\n    strength: float,\n    stability: float,\n    reversal: float,\n    contradiction: float,\n    uncertainty: float,\n    support: float,\n    monitoring: bool,\n):\n    body = {\n        "finding_index": index,\n        "cause_record_id": cause,\n        "effect_record_id": effect,\n        "source_finding_hash": f"uncertainty-{index}",\n        "narrative_state": state,\n        "narrative_direction": (\n            "support_accumulating"\n            if state == "strengthening"\n            else "opposing_evidence_dominant"\n        ),\n        "narrative_strength": strength,\n        "narrative_stability": stability,\n        "reversal_risk": reversal,\n        "contradiction_pressure": contradiction,\n        "uncertainty_pressure": uncertainty,\n        "evidence_support": support,\n        "requires_monitoring": monitoring,\n        "evolution_signals": ("certified narrative signal",),\n        "rationale": ("certified narrative rationale",),\n        "read_only": True,\n    }\n    return OracleNarrativeEvolutionFinding(\n        **body,\n        finding_hash=oit_017_hash(body),\n    )\n\n\ndef make_report(root: Path):\n    findings = (\n        make_narrative(\n            1,\n            "BTC-ETF",\n            "BTC-PRICE",\n            state="strengthening",\n            strength=0.82,\n            stability=0.80,\n            reversal=0.15,\n            contradiction=0.05,\n            uncertainty=0.20,\n            support=0.86,\n            monitoring=False,\n        ),\n        make_narrative(\n            2,\n            "BTC-PRICE",\n            "BTC-MINER",\n            state="reversing",\n            strength=0.78,\n            stability=0.22,\n            reversal=0.84,\n            contradiction=0.82,\n            uncertainty=0.72,\n            support=0.30,\n            monitoring=True,\n        ),\n    )\n    body = {\n        "schema_version": OIT_017_SCHEMA_VERSION,\n        "engine_id": OIT_017_ENGINE_ID,\n        "policy_id": OIT_017_POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root.resolve()),\n        "query": "Challenge the current Bitcoin narratives.",\n        "uncertainty_report_hash": "uncertainty-report-hash",\n        "findings": findings,\n        "finding_count": len(findings),\n        "strengthening_count": sum(\n            item.narrative_state == "strengthening" for item in findings\n        ),\n        "weakening_count": sum(\n            item.narrative_state == "weakening" for item in findings\n        ),\n        "fragmented_count": sum(\n            item.narrative_state == "fragmented" for item in findings\n        ),\n        "reversing_count": sum(\n            item.narrative_state == "reversing" for item in findings\n        ),\n        "stable_count": sum(\n            item.narrative_state == "stable" for item in findings\n        ),\n        "monitoring_required_count": sum(\n            item.requires_monitoring for item in findings\n        ),\n        "narrative_state": "narrative_reversal_detected",\n        "narrative_summary": "One strengthening and one reversing narrative.",\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "publication_allowed": False,\n        "qseries_execution_allowed": False,\n        "failure_reason": None,\n    }\n    report = OracleNarrativeEvolutionReport(\n        **body,\n        report_hash=oit_017_hash(body),\n    )\n    verify_narrative_evolution_report(report)\n    return report\n\n\ndef main() -> int:\n    print("=" * 40)\n    print(" OIT-018 CORRECTION V2 TEST")\n    print(" NARRATIVE CHALLENGE AND SELF-CRITIQUE")\n    print("=" * 40)\n\n    with TemporaryDirectory() as temporary:\n        root = Path(temporary)\n        source = make_report(root)\n\n        assert source.finding_count == 2\n        assert source.strengthening_count == 1\n        assert source.reversing_count == 1\n        assert source.monitoring_required_count == 1\n\n        report = build_narrative_challenge_report(\n            root,\n            source.query,\n            narrative_report=source,\n        )\n\n        assert report.narrative_report_hash == source.report_hash\n        assert report.finding_count == 2\n        assert report.passed_count == 1\n        assert report.failed_count == 1\n        assert report.fragile_count == 1\n        assert report.monitoring_required_count == 1\n\n        passed, failed = report.findings\n        assert passed.challenge_state == "passed"\n        assert passed.challenge_passed\n        assert passed.surviving_confidence >= 0.50\n\n        assert failed.challenge_state == "failed"\n        assert not failed.challenge_passed\n        assert failed.fragility_score >= 0.70\n        assert failed.counter_evidence_pressure > (\n            passed.counter_evidence_pressure\n        )\n\n        assert passed.source_narrative_hash == (\n            source.findings[0].finding_hash\n        )\n        assert failed.source_narrative_hash == (\n            source.findings[1].finding_hash\n        )\n\n        assert all(item.fragile_assumptions for item in report.findings)\n        assert all(item.counter_arguments for item in report.findings)\n        assert all(item.falsification_tests for item in report.findings)\n\n        replay = build_narrative_challenge_report(\n            root,\n            source.query,\n            narrative_report=source,\n        )\n        assert replay == report\n        assert verify_narrative_challenge_report(report)\n\n        tampered = replace(\n            report,\n            challenge_summary=report.challenge_summary + " tampered",\n        )\n        try:\n            verify_narrative_challenge_report(tampered)\n        except OracleNarrativeChallengeInvariantError:\n            pass\n        else:\n            raise AssertionError("tampered challenge report accepted")\n\n        assert report.read_only\n        assert not report.analytics_execution_performed\n        assert not report.database_access_performed\n        assert not report.publication_allowed\n        assert not report.qseries_execution_allowed\n\n    print("[PASS] Corrected certified OIT-017 narrative report consumed")\n    print("[PASS] OIT-017 fixture counts derived from narrative findings")\n    print("[PASS] Strong narrative survived bounded challenge")\n    print("[PASS] Fragile narrative failed bounded challenge")\n    print("[PASS] Counter-evidence pressure quantified")\n    print("[PASS] Fragile assumptions surfaced")\n    print("[PASS] Counter-arguments generated")\n    print("[PASS] Falsification tests generated")\n    print("[PASS] Complete corrected OIT-017 lineage retained")\n    print("[PASS] Challenge report deterministic across replay")\n    print("[PASS] Tampered challenge report rejected")\n    print("[PASS] No analytics execution or database access performed")\n    print("[PASS] Publication and Q Series execution disabled")\n    print("[DONE] OIT-018 CORRECTION V2 SELF-CRITIQUE PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


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
    for path in (OIT_017, OIT_017_TEST, RUNNER):
        if path.is_file():
            protected[path] = sha256(path)
    return protected


def main() -> int:
    print("=" * 40)
    print(" OIT-018 CORRECTION V3 INSTALLER")
    print(" FULL INSTALLATION AND CHAIN CERTIFICATION")
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
                "OracleNarrativeEvolutionFinding",
                "build_narrative_evolution_report",
                "verify_narrative_evolution_report",
                "publication_allowed",
                "qseries_execution_allowed",
            ),
            "Certified OIT-017 production",
        )
        require_contract(
            OIT_017_TEST,
            (
                "OIT-017 CORRECTION V2 TEST",
                "Fixture unresolved-evidence count derived from findings",
                "Both evidence-requiring findings counted exactly",
                "OIT-017 CORRECTION V2 NARRATIVE EVOLUTION PASS",
            ),
            "Corrected OIT-017 standalone test",
        )

        protected = protected_sources()
        print("[OK] Corrected OIT-017 production contract verified")
        print("[OK] OIT-017 Correction V2 standalone test verified")
        print(
            f"[OK] Protected production source files captured: "
            f"{len(protected)}"
        )

        upstream = subprocess.run(
            [sys.executable, str(OIT_017_TEST)],
            cwd=ROOT,
            check=False,
        )
        if upstream.returncode:
            raise RuntimeError(
                f"Corrected OIT-017 certification failed with exit code "
                f"{upstream.returncode}"
            )

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_narrative_challenge_self_critique_intelligence "
            "import *"
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
                f"OIT-018 Correction V3 test failed with exit code "
                f"{completed.returncode}"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Protected production source changed: {path}"
                )

        print("[PASS] Corrected OIT-017 production and test unchanged")
        print("[PASS] Oracle terminal runner unchanged")
        print("[PASS] OLA, OIA, INT-OII, ORR, OOR, and Q Series unchanged")
        print("[PASS] OIT-018 production module installed from scratch")
        print("[PASS] OIT-018 corrected standalone test installed")
        print("[PASS] Corrected OIT-017 chain certified before OIT-018")
        print("[PASS] Narrative challenge and self-critique certified")
        print("[PASS] Read-only and execution boundaries preserved")
        print(f"[PASS] Repository located: {ROOT}")
        print(
            "[DONE] OIT-018 CORRECTION V3 FULL INSTALLATION "
            "AND CHAIN CERTIFICATION INSTALLED"
        )
        return 0
    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
