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
            / "oracle_cross_market_causal_intelligence_analysis.py"
        )
        if required.is_file():
            return candidate
    raise SystemExit("[ERROR] Could not locate current Q Series repository.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"
OIT_015 = PACKAGE / "oracle_cross_market_causal_intelligence_analysis.py"
PRODUCTION = (
    PACKAGE
    / "oracle_cross_market_uncertainty_contradiction_synthesis.py"
)
TEST = (
    ROOT
    / "test_oit_016_oracle_cross_market_uncertainty_contradiction_synthesis.py"
)
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass\nfrom pathlib import Path\nfrom typing import Any, Mapping\n\nfrom .oracle_cross_market_causal_intelligence_analysis import (\n    MAX_CAUSAL_CONFIDENCE,\n    OracleCausalHypothesis,\n    OracleCausalIntelligenceInvariantError,\n    OracleCausalIntelligenceReport,\n    build_causal_intelligence_report,\n    verify_causal_intelligence_report,\n)\n\nSCHEMA_VERSION = "OIT-016"\nENGINE_ID = "OIT-016"\nPOLICY_ID = "oracle.cross-market-uncertainty-contradiction-synthesis.v1"\n\n\nclass OracleUncertaintyContradictionInvariantError(\n    OracleCausalIntelligenceInvariantError\n):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleUncertaintyContradictionFinding:\n    finding_index: int\n    cause_record_id: str\n    effect_record_id: str\n    source_hypothesis_hash: str\n    evidence_class: str\n    contradiction_state: str\n    uncertainty_state: str\n    uncertainty_score: float\n    confidence_gap: float\n    evidence_completeness: float\n    contradiction_severity: float\n    requires_additional_evidence: bool\n    unresolved_questions: tuple[str, ...]\n    rationale: tuple[str, ...]\n    read_only: bool\n    finding_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleUncertaintyContradictionReport:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    status: str\n    repository_root: str\n    query: str\n    causal_report_hash: str\n    findings: tuple[OracleUncertaintyContradictionFinding, ...]\n    finding_count: int\n    high_uncertainty_count: int\n    moderate_uncertainty_count: int\n    low_uncertainty_count: int\n    material_contradiction_count: int\n    unresolved_evidence_count: int\n    synthesis_state: str\n    synthesis_summary: str\n    read_only: bool\n    analytics_execution_performed: bool\n    database_access_performed: bool\n    publication_allowed: bool\n    qseries_execution_allowed: bool\n    failure_reason: str | None\n    report_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if isinstance(value, Path):\n        return value.as_posix()\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    return repr(value)\n\n\ndef _stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=True,\n    ).encode("utf-8")\n    return hashlib.sha256(payload).hexdigest()\n\n\ndef _bounded(value: float) -> float:\n    return round(max(0.0, min(1.0, value)), 6)\n\n\ndef _classify_uncertainty(score: float) -> str:\n    if score >= 0.67:\n        return "high"\n    if score >= 0.34:\n        return "moderate"\n    return "low"\n\n\ndef _finding(\n    hypothesis: OracleCausalHypothesis,\n    index: int,\n) -> OracleUncertaintyContradictionFinding:\n    confidence_gap = _bounded(1.0 - hypothesis.causal_confidence)\n\n    limitation_penalty = min(0.35, 0.07 * len(hypothesis.limitations))\n    evidence_completeness = _bounded(\n        hypothesis.causal_confidence\n        + (0.10 if hypothesis.supports_causation else 0.0)\n        - limitation_penalty\n    )\n\n    contradiction_severity = 0.0\n    contradiction_state = "none_detected"\n    if hypothesis.contradicts_causation:\n        contradiction_severity = _bounded(\n            0.45\n            + (0.30 * hypothesis.causal_confidence)\n            + (\n                0.15\n                if hypothesis.evidence_class == "suppressive"\n                else 0.0\n            )\n        )\n        contradiction_state = (\n            "material_directional_contradiction"\n            if contradiction_severity >= 0.60\n            else "bounded_directional_contradiction"\n        )\n    elif hypothesis.evidence_class == "associative":\n        contradiction_state = "not_a_contradiction_temporal_order_missing"\n    elif hypothesis.evidence_class == "insufficient":\n        contradiction_state = "not_a_contradiction_evidence_insufficient"\n\n    uncertainty_score = _bounded(\n        (0.60 * confidence_gap)\n        + (0.25 * (1.0 - evidence_completeness))\n        + (0.15 * contradiction_severity)\n    )\n    uncertainty_state = _classify_uncertainty(uncertainty_score)\n\n    unresolved = []\n    if hypothesis.causal_confidence < 0.50:\n        unresolved.append("What independent evidence would strengthen the hypothesis?")\n    if "mechanism has not yet been independently verified" in hypothesis.limitations:\n        unresolved.append("What mechanism links the proposed cause to the effect?")\n    if hypothesis.contradicts_causation:\n        unresolved.append("Is the inverse movement causal, hedging, substitution, or confounding?")\n    if hypothesis.evidence_class in {"associative", "insufficient"}:\n        unresolved.append("Can stable temporal precedence be established?")\n    if "unobserved confounders may explain the relationship" in hypothesis.limitations:\n        unresolved.append("Which confounders could explain both records?")\n    if not unresolved:\n        unresolved.append("What evidence would falsify the current causal interpretation?")\n\n    rationale = (\n        f"causal confidence: {hypothesis.causal_confidence:.6f}",\n        f"confidence gap: {confidence_gap:.6f}",\n        f"evidence completeness: {evidence_completeness:.6f}",\n        f"contradiction severity: {contradiction_severity:.6f}",\n        f"uncertainty score: {uncertainty_score:.6f}",\n        (\n            "uncertainty reflects incomplete or conflicting evidence, "\n            "not stochastic model training"\n        ),\n    )\n\n    body = {\n        "finding_index": index,\n        "cause_record_id": hypothesis.cause_record_id,\n        "effect_record_id": hypothesis.effect_record_id,\n        "source_hypothesis_hash": hypothesis.hypothesis_hash,\n        "evidence_class": hypothesis.evidence_class,\n        "contradiction_state": contradiction_state,\n        "uncertainty_state": uncertainty_state,\n        "uncertainty_score": uncertainty_score,\n        "confidence_gap": confidence_gap,\n        "evidence_completeness": evidence_completeness,\n        "contradiction_severity": contradiction_severity,\n        "requires_additional_evidence": uncertainty_state != "low"\n        or contradiction_severity > 0.0,\n        "unresolved_questions": tuple(unresolved),\n        "rationale": rationale,\n        "read_only": True,\n    }\n    return OracleUncertaintyContradictionFinding(\n        **body,\n        finding_hash=_stable_hash(body),\n    )\n\n\ndef verify_uncertainty_contradiction_finding(\n    finding: OracleUncertaintyContradictionFinding,\n) -> bool:\n    body = asdict(finding)\n    supplied = body.pop("finding_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleUncertaintyContradictionInvariantError(\n            "uncertainty finding hash mismatch"\n        )\n    if not finding.read_only:\n        raise OracleUncertaintyContradictionInvariantError(\n            "uncertainty finding is not read-only"\n        )\n    for value in (\n        finding.uncertainty_score,\n        finding.confidence_gap,\n        finding.evidence_completeness,\n        finding.contradiction_severity,\n    ):\n        if not 0.0 <= value <= 1.0:\n            raise OracleUncertaintyContradictionInvariantError(\n                "bounded uncertainty metric outside range"\n            )\n    if not finding.source_hypothesis_hash:\n        raise OracleUncertaintyContradictionInvariantError(\n            "source hypothesis lineage missing"\n        )\n    if not finding.unresolved_questions:\n        raise OracleUncertaintyContradictionInvariantError(\n            "uncertainty finding lacks unresolved questions"\n        )\n    return True\n\n\ndef _summary(\n    findings: tuple[OracleUncertaintyContradictionFinding, ...],\n) -> tuple[str, str]:\n    if not findings:\n        return (\n            "no_causal_hypotheses",\n            "No certified causal hypotheses were available for uncertainty synthesis.",\n        )\n    high = sum(item.uncertainty_state == "high" for item in findings)\n    moderate = sum(item.uncertainty_state == "moderate" for item in findings)\n    low = sum(item.uncertainty_state == "low" for item in findings)\n    contradictions = sum(\n        item.contradiction_severity >= 0.60 for item in findings\n    )\n    unresolved = sum(item.requires_additional_evidence for item in findings)\n\n    if contradictions:\n        state = "material_contradictions_require_review"\n    elif high:\n        state = "high_uncertainty_requires_more_evidence"\n    elif moderate:\n        state = "bounded_uncertainty_present"\n    else:\n        state = "low_uncertainty_bounded_evidence"\n\n    return (\n        state,\n        (\n            f"{len(findings)} findings: {high} high uncertainty, "\n            f"{moderate} moderate, {low} low; "\n            f"{contradictions} material contradictions and "\n            f"{unresolved} findings requiring additional evidence."\n        ),\n    )\n\n\ndef build_uncertainty_contradiction_report(\n    repository_root: str | Path,\n    query: str,\n    *,\n    causal_report: OracleCausalIntelligenceReport | None = None,\n) -> OracleUncertaintyContradictionReport:\n    root = Path(repository_root).resolve()\n    source = causal_report\n    if source is None:\n        source = build_causal_intelligence_report(root, query)\n    verify_causal_intelligence_report(source)\n\n    findings = tuple(\n        _finding(hypothesis, index)\n        for index, hypothesis in enumerate(source.hypotheses, start=1)\n    )\n    for finding in findings:\n        verify_uncertainty_contradiction_finding(finding)\n\n    synthesis_state, synthesis_summary = _summary(findings)\n    high = sum(item.uncertainty_state == "high" for item in findings)\n    moderate = sum(item.uncertainty_state == "moderate" for item in findings)\n    low = sum(item.uncertainty_state == "low" for item in findings)\n    material = sum(\n        item.contradiction_severity >= 0.60 for item in findings\n    )\n    unresolved = sum(item.requires_additional_evidence for item in findings)\n\n    body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root),\n        "query": str(query),\n        "causal_report_hash": source.report_hash,\n        "findings": findings,\n        "finding_count": len(findings),\n        "high_uncertainty_count": high,\n        "moderate_uncertainty_count": moderate,\n        "low_uncertainty_count": low,\n        "material_contradiction_count": material,\n        "unresolved_evidence_count": unresolved,\n        "synthesis_state": synthesis_state,\n        "synthesis_summary": synthesis_summary,\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "publication_allowed": False,\n        "qseries_execution_allowed": False,\n        "failure_reason": None,\n    }\n    report = OracleUncertaintyContradictionReport(\n        **body,\n        report_hash=_stable_hash(body),\n    )\n    verify_uncertainty_contradiction_report(report)\n    return report\n\n\ndef verify_uncertainty_contradiction_report(\n    report: OracleUncertaintyContradictionReport,\n) -> bool:\n    body = asdict(report)\n    supplied = body.pop("report_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleUncertaintyContradictionInvariantError(\n            "uncertainty contradiction report hash mismatch"\n        )\n    if report.schema_version != SCHEMA_VERSION:\n        raise OracleUncertaintyContradictionInvariantError("schema mismatch")\n    if report.policy_id != POLICY_ID:\n        raise OracleUncertaintyContradictionInvariantError("policy mismatch")\n    if not report.read_only:\n        raise OracleUncertaintyContradictionInvariantError(\n            "report is not read-only"\n        )\n    if (\n        report.analytics_execution_performed\n        or report.database_access_performed\n        or report.publication_allowed\n        or report.qseries_execution_allowed\n    ):\n        raise OracleUncertaintyContradictionInvariantError(\n            "forbidden runtime capability enabled"\n        )\n    if report.finding_count != len(report.findings):\n        raise OracleUncertaintyContradictionInvariantError(\n            "finding count mismatch"\n        )\n\n    expected = {\n        "high": report.high_uncertainty_count,\n        "moderate": report.moderate_uncertainty_count,\n        "low": report.low_uncertainty_count,\n    }\n    for state, count in expected.items():\n        actual = sum(\n            item.uncertainty_state == state\n            for item in report.findings\n        )\n        if actual != count:\n            raise OracleUncertaintyContradictionInvariantError(\n                f"{state} uncertainty count mismatch"\n            )\n    if sum(expected.values()) != report.finding_count:\n        raise OracleUncertaintyContradictionInvariantError(\n            "classified uncertainty count mismatch"\n        )\n\n    actual_material = sum(\n        item.contradiction_severity >= 0.60\n        for item in report.findings\n    )\n    if actual_material != report.material_contradiction_count:\n        raise OracleUncertaintyContradictionInvariantError(\n            "material contradiction count mismatch"\n        )\n    actual_unresolved = sum(\n        item.requires_additional_evidence\n        for item in report.findings\n    )\n    if actual_unresolved != report.unresolved_evidence_count:\n        raise OracleUncertaintyContradictionInvariantError(\n            "unresolved evidence count mismatch"\n        )\n    for finding in report.findings:\n        verify_uncertainty_contradiction_finding(finding)\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import replace\nfrom pathlib import Path\nfrom tempfile import TemporaryDirectory\n\nfrom qseries_v2.oracle_terminal.oracle_cross_market_causal_intelligence_analysis import (\n    ENGINE_ID as OIT_015_ENGINE_ID,\n    POLICY_ID as OIT_015_POLICY_ID,\n    SCHEMA_VERSION as OIT_015_SCHEMA_VERSION,\n    OracleCausalHypothesis,\n    OracleCausalIntelligenceReport,\n    _stable_hash as oit_015_hash,\n    verify_causal_intelligence_report,\n)\nfrom qseries_v2.oracle_terminal.oracle_cross_market_uncertainty_contradiction_synthesis import (\n    OracleUncertaintyContradictionInvariantError,\n    build_uncertainty_contradiction_report,\n    verify_uncertainty_contradiction_report,\n)\n\n\ndef make_hypothesis(\n    index: int,\n    cause: str,\n    effect: str,\n    evidence_class: str,\n    confidence: float,\n    *,\n    contradicts: bool,\n):\n    limitations = (\n        "observational evidence cannot establish causation by itself",\n        "unobserved confounders may explain the relationship",\n        "mechanism has not yet been independently verified",\n    )\n    body = {\n        "hypothesis_index": index,\n        "cause_record_id": cause,\n        "effect_record_id": effect,\n        "shared_entities": ("Bitcoin",),\n        "temporal_order": "left_precedes_right",\n        "causal_direction": f"{cause}->{effect}",\n        "causal_type": (\n            "candidate_inhibitory_influence"\n            if contradicts\n            else "candidate_influence"\n        ),\n        "evidence_class": evidence_class,\n        "probability_distance": 0.10,\n        "relationship_score": 0.80,\n        "causal_confidence": confidence,\n        "supports_causation": True,\n        "contradicts_causation": contradicts,\n        "limitations": limitations,\n        "rationale": ("certified causal hypothesis",),\n        "source_relationship_hash": f"relationship-{index}",\n        "read_only": True,\n    }\n    return OracleCausalHypothesis(\n        **body,\n        hypothesis_hash=oit_015_hash(body),\n    )\n\n\ndef make_report(root: Path):\n    hypotheses = (\n        make_hypothesis(\n            1,\n            "BTC-ETF",\n            "BTC-PRICE",\n            "supportive",\n            0.76,\n            contradicts=False,\n        ),\n        make_hypothesis(\n            2,\n            "BTC-PRICE",\n            "BTC-MINER",\n            "suppressive",\n            0.58,\n            contradicts=True,\n        ),\n    )\n    body = {\n        "schema_version": OIT_015_SCHEMA_VERSION,\n        "engine_id": OIT_015_ENGINE_ID,\n        "policy_id": OIT_015_POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root.resolve()),\n        "query": "Where are the uncertainty and contradictions?",\n        "cross_market_report_hash": "cross-market-report-hash",\n        "hypotheses": hypotheses,\n        "hypothesis_count": 2,\n        "supportive_hypothesis_count": 1,\n        "suppressive_hypothesis_count": 1,\n        "associative_hypothesis_count": 0,\n        "insufficient_hypothesis_count": 0,\n        "causal_state": "bounded_causal_hypotheses_present",\n        "causal_summary": "Two bounded hypotheses.",\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "publication_allowed": False,\n        "qseries_execution_allowed": False,\n        "failure_reason": None,\n    }\n    report = OracleCausalIntelligenceReport(\n        **body,\n        report_hash=oit_015_hash(body),\n    )\n    verify_causal_intelligence_report(report)\n    return report\n\n\ndef main() -> int:\n    print("=" * 40)\n    print(" OIT-016 TEST")\n    print(" UNCERTAINTY AND CONTRADICTION SYNTHESIS")\n    print("=" * 40)\n\n    with TemporaryDirectory() as temporary:\n        root = Path(temporary)\n        source = make_report(root)\n        report = build_uncertainty_contradiction_report(\n            root,\n            source.query,\n            causal_report=source,\n        )\n\n        assert report.causal_report_hash == source.report_hash\n        assert report.finding_count == 2\n        assert report.material_contradiction_count == 1\n        assert report.unresolved_evidence_count >= 1\n\n        supportive, suppressive = report.findings\n        assert supportive.contradiction_state == "none_detected"\n        assert suppressive.contradiction_state == (\n            "material_directional_contradiction"\n        )\n        assert suppressive.contradiction_severity >= 0.60\n        assert suppressive.requires_additional_evidence\n        assert supportive.source_hypothesis_hash == (\n            source.hypotheses[0].hypothesis_hash\n        )\n        assert suppressive.source_hypothesis_hash == (\n            source.hypotheses[1].hypothesis_hash\n        )\n\n        assert all(\n            0.0 <= item.uncertainty_score <= 1.0\n            for item in report.findings\n        )\n        assert all(item.unresolved_questions for item in report.findings)\n\n        replay = build_uncertainty_contradiction_report(\n            root,\n            source.query,\n            causal_report=source,\n        )\n        assert replay == report\n        assert verify_uncertainty_contradiction_report(report)\n\n        tampered = replace(\n            report,\n            synthesis_summary=report.synthesis_summary + " tampered",\n        )\n        try:\n            verify_uncertainty_contradiction_report(tampered)\n        except OracleUncertaintyContradictionInvariantError:\n            pass\n        else:\n            raise AssertionError("tampered uncertainty report accepted")\n\n        assert report.read_only\n        assert not report.analytics_execution_performed\n        assert not report.database_access_performed\n        assert not report.publication_allowed\n        assert not report.qseries_execution_allowed\n\n    print("[PASS] Certified OIT-015 causal report consumed")\n    print("[PASS] Confidence gaps quantified deterministically")\n    print("[PASS] Evidence completeness calculated")\n    print("[PASS] Material directional contradiction detected")\n    print("[PASS] Incomplete evidence separated from contradiction")\n    print("[PASS] Unresolved intelligence questions generated")\n    print("[PASS] Complete causal hypothesis lineage retained")\n    print("[PASS] Synthesis deterministic across replay")\n    print("[PASS] Tampered synthesis report rejected")\n    print("[PASS] No analytics execution or database access performed")\n    print("[PASS] Publication and Q Series execution disabled")\n    print("[DONE] OIT-016 UNCERTAINTY CONTRADICTION SYNTHESIS PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_complete(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


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
    for path in (OIT_015, RUNNER):
        if path.is_file():
            protected[path] = sha256(path)
    return protected


def require_oit_015() -> None:
    if not OIT_015.is_file():
        raise RuntimeError(f"Certified OIT-015 module missing: {OIT_015}")
    source = OIT_015.read_text(encoding="utf-8")
    required = (
        'SCHEMA_VERSION = "OIT-015"',
        'POLICY_ID = "oracle.cross-market-causal-intelligence-analysis.v1"',
        "OracleCausalIntelligenceReport",
        "OracleCausalHypothesis",
        "build_causal_intelligence_report",
        "verify_causal_intelligence_report",
        "hypothesis_hash",
        "publication_allowed",
        "qseries_execution_allowed",
    )
    missing = [token for token in required if token not in source]
    if missing:
        raise RuntimeError(
            f"Certified OIT-015 contract mismatch: {missing}"
        )


def main() -> int:
    print("=" * 40)
    print(" OIT-016 INSTALLER")
    print(" UNCERTAINTY AND CONTRADICTION SYNTHESIS")
    print("=" * 40)
    try:
        require_oit_015()
        protected = protected_sources()
        print("[OK] Certified OIT-015 causal contract verified")
        print(
            f"[OK] Protected production source files captured: "
            f"{len(protected)}"
        )

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_cross_market_uncertainty_contradiction_synthesis "
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
                f"OIT-016 test failed with exit code {completed.returncode}"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Protected production source changed: {path}"
                )

        print("[PASS] Certified OIT-015 production module unchanged")
        print("[PASS] Oracle terminal runner unchanged")
        print("[PASS] OLA, OIA, INT-OII, ORR, OOR, and Q Series unchanged")
        print("[PASS] OIT-016 production module installed")
        print("[PASS] OIT-016 standalone test installed")
        print("[PASS] Uncertainty and contradiction metrics bounded")
        print("[PASS] Read-only and execution boundaries preserved")
        print(f"[PASS] Repository located: {ROOT}")
        print(
            "[DONE] OIT-016 UNCERTAINTY AND CONTRADICTION "
            "SYNTHESIS INSTALLED"
        )
        return 0
    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
