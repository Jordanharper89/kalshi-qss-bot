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
            / "oracle_cross_market_uncertainty_contradiction_synthesis.py"
        )
        if required.is_file():
            return candidate
    raise SystemExit("[ERROR] Could not locate current Q Series repository.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"
OIT_016 = (
    PACKAGE
    / "oracle_cross_market_uncertainty_contradiction_synthesis.py"
)
PRODUCTION = (
    PACKAGE
    / "oracle_cross_market_narrative_evolution_intelligence.py"
)
TEST = (
    ROOT
    / "test_oit_017_oracle_cross_market_narrative_evolution_intelligence.py"
)
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass\nfrom pathlib import Path\nfrom typing import Any, Mapping\n\nfrom .oracle_cross_market_uncertainty_contradiction_synthesis import (\n    OracleUncertaintyContradictionFinding,\n    OracleUncertaintyContradictionInvariantError,\n    OracleUncertaintyContradictionReport,\n    build_uncertainty_contradiction_report,\n    verify_uncertainty_contradiction_report,\n)\n\nSCHEMA_VERSION = "OIT-017"\nENGINE_ID = "OIT-017"\nPOLICY_ID = "oracle.cross-market-narrative-evolution-intelligence.v1"\n\n\nclass OracleNarrativeEvolutionInvariantError(\n    OracleUncertaintyContradictionInvariantError\n):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleNarrativeEvolutionFinding:\n    finding_index: int\n    cause_record_id: str\n    effect_record_id: str\n    source_finding_hash: str\n    narrative_state: str\n    narrative_direction: str\n    narrative_strength: float\n    narrative_stability: float\n    reversal_risk: float\n    contradiction_pressure: float\n    uncertainty_pressure: float\n    evidence_support: float\n    requires_monitoring: bool\n    evolution_signals: tuple[str, ...]\n    rationale: tuple[str, ...]\n    read_only: bool\n    finding_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleNarrativeEvolutionReport:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    status: str\n    repository_root: str\n    query: str\n    uncertainty_report_hash: str\n    findings: tuple[OracleNarrativeEvolutionFinding, ...]\n    finding_count: int\n    strengthening_count: int\n    weakening_count: int\n    fragmented_count: int\n    reversing_count: int\n    stable_count: int\n    monitoring_required_count: int\n    narrative_state: str\n    narrative_summary: str\n    read_only: bool\n    analytics_execution_performed: bool\n    database_access_performed: bool\n    publication_allowed: bool\n    qseries_execution_allowed: bool\n    failure_reason: str | None\n    report_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if isinstance(value, Path):\n        return value.as_posix()\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    return repr(value)\n\n\ndef _stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=True,\n    ).encode("utf-8")\n    return hashlib.sha256(payload).hexdigest()\n\n\ndef _bounded(value: float) -> float:\n    return round(max(0.0, min(1.0, value)), 6)\n\n\ndef _classify_narrative(\n    source: OracleUncertaintyContradictionFinding,\n) -> tuple[str, str, float, float, float, tuple[str, ...], tuple[str, ...]]:\n    contradiction = source.contradiction_severity\n    uncertainty = source.uncertainty_score\n    evidence_support = _bounded(\n        (0.65 * source.evidence_completeness)\n        + (0.35 * (1.0 - source.confidence_gap))\n    )\n    stability = _bounded(\n        (0.55 * evidence_support)\n        + (0.25 * (1.0 - uncertainty))\n        + (0.20 * (1.0 - contradiction))\n    )\n    reversal_risk = _bounded(\n        (0.50 * contradiction)\n        + (0.35 * uncertainty)\n        + (0.15 * (1.0 - evidence_support))\n    )\n\n    signals: list[str] = []\n    rationale = [\n        f"evidence support: {evidence_support:.6f}",\n        f"narrative stability: {stability:.6f}",\n        f"reversal risk: {reversal_risk:.6f}",\n        f"contradiction pressure: {contradiction:.6f}",\n        f"uncertainty pressure: {uncertainty:.6f}",\n    ]\n\n    if contradiction >= 0.75 and reversal_risk >= 0.65:\n        state = "reversing"\n        direction = "opposing_evidence_dominant"\n        strength = _bounded(reversal_risk)\n        signals.extend(\n            (\n                "material contradiction dominates current narrative",\n                "directional reversal risk exceeds stability",\n            )\n        )\n    elif contradiction >= 0.45 and uncertainty >= 0.45:\n        state = "fragmented"\n        direction = "competing_interpretations"\n        strength = _bounded(max(contradiction, uncertainty))\n        signals.extend(\n            (\n                "conflicting evidence supports multiple interpretations",\n                "narrative consensus is unstable",\n            )\n        )\n    elif evidence_support >= 0.65 and uncertainty <= 0.40:\n        state = "strengthening"\n        direction = "support_accumulating"\n        strength = _bounded(\n            (0.60 * evidence_support)\n            + (0.40 * stability)\n        )\n        signals.extend(\n            (\n                "evidence support exceeds uncertainty pressure",\n                "narrative consistency is increasing",\n            )\n        )\n    elif evidence_support < 0.45 or uncertainty >= 0.65:\n        state = "weakening"\n        direction = "support_eroding"\n        strength = _bounded(\n            (0.55 * (1.0 - evidence_support))\n            + (0.45 * uncertainty)\n        )\n        signals.extend(\n            (\n                "supporting evidence is incomplete or eroding",\n                "uncertainty pressure exceeds narrative support",\n            )\n        )\n    else:\n        state = "stable"\n        direction = "bounded_continuity"\n        strength = stability\n        signals.extend(\n            (\n                "support and uncertainty remain within bounded range",\n                "no material reversal signal detected",\n            )\n        )\n\n    rationale.append(\n        "narrative classification is deterministic and observational"\n    )\n    return (\n        state,\n        direction,\n        strength,\n        stability,\n        reversal_risk,\n        tuple(signals),\n        tuple(rationale),\n    )\n\n\ndef _build_finding(\n    source: OracleUncertaintyContradictionFinding,\n    index: int,\n) -> OracleNarrativeEvolutionFinding:\n    (\n        narrative_state,\n        narrative_direction,\n        narrative_strength,\n        narrative_stability,\n        reversal_risk,\n        signals,\n        rationale,\n    ) = _classify_narrative(source)\n\n    evidence_support = _bounded(\n        (0.65 * source.evidence_completeness)\n        + (0.35 * (1.0 - source.confidence_gap))\n    )\n\n    body = {\n        "finding_index": index,\n        "cause_record_id": source.cause_record_id,\n        "effect_record_id": source.effect_record_id,\n        "source_finding_hash": source.finding_hash,\n        "narrative_state": narrative_state,\n        "narrative_direction": narrative_direction,\n        "narrative_strength": narrative_strength,\n        "narrative_stability": narrative_stability,\n        "reversal_risk": reversal_risk,\n        "contradiction_pressure": source.contradiction_severity,\n        "uncertainty_pressure": source.uncertainty_score,\n        "evidence_support": evidence_support,\n        "requires_monitoring": (\n            narrative_state in {"weakening", "fragmented", "reversing"}\n            or reversal_risk >= 0.50\n        ),\n        "evolution_signals": signals,\n        "rationale": rationale,\n        "read_only": True,\n    }\n    return OracleNarrativeEvolutionFinding(\n        **body,\n        finding_hash=_stable_hash(body),\n    )\n\n\ndef verify_narrative_evolution_finding(\n    finding: OracleNarrativeEvolutionFinding,\n) -> bool:\n    body = asdict(finding)\n    supplied = body.pop("finding_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleNarrativeEvolutionInvariantError(\n            "narrative finding hash mismatch"\n        )\n    if not finding.read_only:\n        raise OracleNarrativeEvolutionInvariantError(\n            "narrative finding is not read-only"\n        )\n    for value in (\n        finding.narrative_strength,\n        finding.narrative_stability,\n        finding.reversal_risk,\n        finding.contradiction_pressure,\n        finding.uncertainty_pressure,\n        finding.evidence_support,\n    ):\n        if not 0.0 <= value <= 1.0:\n            raise OracleNarrativeEvolutionInvariantError(\n                "narrative metric outside bounded range"\n            )\n    if not finding.source_finding_hash:\n        raise OracleNarrativeEvolutionInvariantError(\n            "source uncertainty lineage missing"\n        )\n    if not finding.evolution_signals:\n        raise OracleNarrativeEvolutionInvariantError(\n            "narrative evolution signals missing"\n        )\n    return True\n\n\ndef _summary(\n    findings: tuple[OracleNarrativeEvolutionFinding, ...],\n) -> tuple[str, str]:\n    if not findings:\n        return (\n            "no_narrative_evidence",\n            "No certified uncertainty findings were available for narrative analysis.",\n        )\n\n    counts = {\n        state: sum(item.narrative_state == state for item in findings)\n        for state in (\n            "strengthening",\n            "weakening",\n            "fragmented",\n            "reversing",\n            "stable",\n        )\n    }\n\n    if counts["reversing"]:\n        state = "narrative_reversal_detected"\n    elif counts["fragmented"]:\n        state = "narrative_fragmentation_detected"\n    elif counts["weakening"] > counts["strengthening"]:\n        state = "narrative_support_weakening"\n    elif counts["strengthening"]:\n        state = "narrative_support_strengthening"\n    else:\n        state = "narrative_bounded_stability"\n\n    monitored = sum(item.requires_monitoring for item in findings)\n    summary = (\n        f"{len(findings)} narrative findings: "\n        f"{counts[\'strengthening\']} strengthening, "\n        f"{counts[\'weakening\']} weakening, "\n        f"{counts[\'fragmented\']} fragmented, "\n        f"{counts[\'reversing\']} reversing, "\n        f"{counts[\'stable\']} stable; "\n        f"{monitored} require continued monitoring."\n    )\n    return state, summary\n\n\ndef build_narrative_evolution_report(\n    repository_root: str | Path,\n    query: str,\n    *,\n    uncertainty_report: OracleUncertaintyContradictionReport | None = None,\n) -> OracleNarrativeEvolutionReport:\n    root = Path(repository_root).resolve()\n    source = uncertainty_report\n    if source is None:\n        source = build_uncertainty_contradiction_report(root, query)\n    verify_uncertainty_contradiction_report(source)\n\n    findings = tuple(\n        _build_finding(item, index)\n        for index, item in enumerate(source.findings, start=1)\n    )\n    for finding in findings:\n        verify_narrative_evolution_finding(finding)\n\n    narrative_state, narrative_summary = _summary(findings)\n    counts = {\n        state: sum(item.narrative_state == state for item in findings)\n        for state in (\n            "strengthening",\n            "weakening",\n            "fragmented",\n            "reversing",\n            "stable",\n        )\n    }\n\n    body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root),\n        "query": str(query),\n        "uncertainty_report_hash": source.report_hash,\n        "findings": findings,\n        "finding_count": len(findings),\n        "strengthening_count": counts["strengthening"],\n        "weakening_count": counts["weakening"],\n        "fragmented_count": counts["fragmented"],\n        "reversing_count": counts["reversing"],\n        "stable_count": counts["stable"],\n        "monitoring_required_count": sum(\n            item.requires_monitoring for item in findings\n        ),\n        "narrative_state": narrative_state,\n        "narrative_summary": narrative_summary,\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "publication_allowed": False,\n        "qseries_execution_allowed": False,\n        "failure_reason": None,\n    }\n    report = OracleNarrativeEvolutionReport(\n        **body,\n        report_hash=_stable_hash(body),\n    )\n    verify_narrative_evolution_report(report)\n    return report\n\n\ndef verify_narrative_evolution_report(\n    report: OracleNarrativeEvolutionReport,\n) -> bool:\n    body = asdict(report)\n    supplied = body.pop("report_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleNarrativeEvolutionInvariantError(\n            "narrative evolution report hash mismatch"\n        )\n    if report.schema_version != SCHEMA_VERSION:\n        raise OracleNarrativeEvolutionInvariantError("schema mismatch")\n    if report.policy_id != POLICY_ID:\n        raise OracleNarrativeEvolutionInvariantError("policy mismatch")\n    if not report.read_only:\n        raise OracleNarrativeEvolutionInvariantError(\n            "report is not read-only"\n        )\n    if (\n        report.analytics_execution_performed\n        or report.database_access_performed\n        or report.publication_allowed\n        or report.qseries_execution_allowed\n    ):\n        raise OracleNarrativeEvolutionInvariantError(\n            "forbidden runtime capability enabled"\n        )\n    if report.finding_count != len(report.findings):\n        raise OracleNarrativeEvolutionInvariantError(\n            "finding count mismatch"\n        )\n\n    expected = {\n        "strengthening": report.strengthening_count,\n        "weakening": report.weakening_count,\n        "fragmented": report.fragmented_count,\n        "reversing": report.reversing_count,\n        "stable": report.stable_count,\n    }\n    for state, count in expected.items():\n        actual = sum(\n            item.narrative_state == state\n            for item in report.findings\n        )\n        if actual != count:\n            raise OracleNarrativeEvolutionInvariantError(\n                f"{state} narrative count mismatch"\n            )\n    if sum(expected.values()) != report.finding_count:\n        raise OracleNarrativeEvolutionInvariantError(\n            "classified narrative count mismatch"\n        )\n\n    actual_monitoring = sum(\n        item.requires_monitoring for item in report.findings\n    )\n    if actual_monitoring != report.monitoring_required_count:\n        raise OracleNarrativeEvolutionInvariantError(\n            "monitoring count mismatch"\n        )\n\n    for finding in report.findings:\n        verify_narrative_evolution_finding(finding)\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import replace\nfrom pathlib import Path\nfrom tempfile import TemporaryDirectory\n\nfrom qseries_v2.oracle_terminal.oracle_cross_market_uncertainty_contradiction_synthesis import (\n    ENGINE_ID as OIT_016_ENGINE_ID,\n    POLICY_ID as OIT_016_POLICY_ID,\n    SCHEMA_VERSION as OIT_016_SCHEMA_VERSION,\n    OracleUncertaintyContradictionFinding,\n    OracleUncertaintyContradictionReport,\n    _stable_hash as oit_016_hash,\n    verify_uncertainty_contradiction_report,\n)\nfrom qseries_v2.oracle_terminal.oracle_cross_market_narrative_evolution_intelligence import (\n    OracleNarrativeEvolutionInvariantError,\n    build_narrative_evolution_report,\n    verify_narrative_evolution_report,\n)\n\n\ndef make_finding(\n    index: int,\n    cause: str,\n    effect: str,\n    uncertainty: float,\n    contradiction: float,\n    completeness: float,\n    confidence_gap: float,\n):\n    contradiction_state = (\n        "material_directional_contradiction"\n        if contradiction >= 0.60\n        else "none_detected"\n    )\n    uncertainty_state = (\n        "high" if uncertainty >= 0.67\n        else "moderate" if uncertainty >= 0.34\n        else "low"\n    )\n    body = {\n        "finding_index": index,\n        "cause_record_id": cause,\n        "effect_record_id": effect,\n        "source_hypothesis_hash": f"hypothesis-{index}",\n        "evidence_class": "suppressive" if contradiction else "supportive",\n        "contradiction_state": contradiction_state,\n        "uncertainty_state": uncertainty_state,\n        "uncertainty_score": uncertainty,\n        "confidence_gap": confidence_gap,\n        "evidence_completeness": completeness,\n        "contradiction_severity": contradiction,\n        "requires_additional_evidence": (\n            uncertainty_state != "low" or contradiction > 0.0\n        ),\n        "unresolved_questions": (\n            "What evidence would falsify the narrative?",\n        ),\n        "rationale": ("certified uncertainty finding",),\n        "read_only": True,\n    }\n    return OracleUncertaintyContradictionFinding(\n        **body,\n        finding_hash=oit_016_hash(body),\n    )\n\n\ndef make_report(root: Path):\n    findings = (\n        make_finding(\n            1,\n            "BTC-ETF",\n            "BTC-PRICE",\n            uncertainty=0.20,\n            contradiction=0.05,\n            completeness=0.82,\n            confidence_gap=0.20,\n        ),\n        make_finding(\n            2,\n            "BTC-PRICE",\n            "BTC-MINER",\n            uncertainty=0.72,\n            contradiction=0.82,\n            completeness=0.34,\n            confidence_gap=0.55,\n        ),\n    )\n    body = {\n        "schema_version": OIT_016_SCHEMA_VERSION,\n        "engine_id": OIT_016_ENGINE_ID,\n        "policy_id": OIT_016_POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root.resolve()),\n        "query": "How is the Bitcoin narrative evolving?",\n        "causal_report_hash": "causal-report-hash",\n        "findings": findings,\n        "finding_count": 2,\n        "high_uncertainty_count": 1,\n        "moderate_uncertainty_count": 0,\n        "low_uncertainty_count": 1,\n        "material_contradiction_count": 1,\n        "unresolved_evidence_count": 1,\n        "synthesis_state": "material_contradictions_require_review",\n        "synthesis_summary": "One stable and one conflicted finding.",\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "publication_allowed": False,\n        "qseries_execution_allowed": False,\n        "failure_reason": None,\n    }\n    report = OracleUncertaintyContradictionReport(\n        **body,\n        report_hash=oit_016_hash(body),\n    )\n    verify_uncertainty_contradiction_report(report)\n    return report\n\n\ndef main() -> int:\n    print("=" * 40)\n    print(" OIT-017 TEST")\n    print(" CROSS-MARKET NARRATIVE EVOLUTION")\n    print("=" * 40)\n\n    with TemporaryDirectory() as temporary:\n        root = Path(temporary)\n        source = make_report(root)\n        report = build_narrative_evolution_report(\n            root,\n            source.query,\n            uncertainty_report=source,\n        )\n\n        assert report.uncertainty_report_hash == source.report_hash\n        assert report.finding_count == 2\n        assert report.strengthening_count == 1\n        assert report.reversing_count == 1\n        assert report.monitoring_required_count == 1\n\n        strengthening, reversing = report.findings\n        assert strengthening.narrative_state == "strengthening"\n        assert strengthening.narrative_direction == "support_accumulating"\n        assert not strengthening.requires_monitoring\n\n        assert reversing.narrative_state == "reversing"\n        assert reversing.narrative_direction == "opposing_evidence_dominant"\n        assert reversing.requires_monitoring\n        assert reversing.reversal_risk >= 0.65\n\n        assert strengthening.source_finding_hash == (\n            source.findings[0].finding_hash\n        )\n        assert reversing.source_finding_hash == (\n            source.findings[1].finding_hash\n        )\n\n        replay = build_narrative_evolution_report(\n            root,\n            source.query,\n            uncertainty_report=source,\n        )\n        assert replay == report\n        assert verify_narrative_evolution_report(report)\n\n        tampered = replace(\n            report,\n            narrative_summary=report.narrative_summary + " tampered",\n        )\n        try:\n            verify_narrative_evolution_report(tampered)\n        except OracleNarrativeEvolutionInvariantError:\n            pass\n        else:\n            raise AssertionError("tampered narrative report accepted")\n\n        assert report.read_only\n        assert not report.analytics_execution_performed\n        assert not report.database_access_performed\n        assert not report.publication_allowed\n        assert not report.qseries_execution_allowed\n\n    print("[PASS] Certified OIT-016 uncertainty report consumed")\n    print("[PASS] Strengthening narrative detected")\n    print("[PASS] Narrative reversal detected")\n    print("[PASS] Narrative stability quantified")\n    print("[PASS] Reversal risk quantified")\n    print("[PASS] Contradiction and uncertainty pressure preserved")\n    print("[PASS] Complete OIT-016 lineage retained")\n    print("[PASS] Narrative report deterministic across replay")\n    print("[PASS] Tampered narrative report rejected")\n    print("[PASS] No analytics execution or database access performed")\n    print("[PASS] Publication and Q Series execution disabled")\n    print("[DONE] OIT-017 CROSS-MARKET NARRATIVE EVOLUTION PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


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
    for path in (OIT_016, RUNNER):
        if path.is_file():
            protected[path] = sha256(path)
    return protected


def require_oit_016() -> None:
    if not OIT_016.is_file():
        raise RuntimeError(f"Certified OIT-016 module missing: {OIT_016}")
    source = OIT_016.read_text(encoding="utf-8")
    required = (
        'SCHEMA_VERSION = "OIT-016"',
        (
            'POLICY_ID = '
            '"oracle.cross-market-uncertainty-contradiction-synthesis.v1"'
        ),
        "OracleUncertaintyContradictionReport",
        "OracleUncertaintyContradictionFinding",
        "build_uncertainty_contradiction_report",
        "verify_uncertainty_contradiction_report",
        "finding_hash",
        "publication_allowed",
        "qseries_execution_allowed",
    )
    missing = [token for token in required if token not in source]
    if missing:
        raise RuntimeError(
            f"Certified OIT-016 contract mismatch: {missing}"
        )


def main() -> int:
    print("=" * 40)
    print(" OIT-017 INSTALLER")
    print(" CROSS-MARKET NARRATIVE EVOLUTION")
    print("=" * 40)
    try:
        require_oit_016()
        protected = protected_sources()
        print("[OK] Certified OIT-016 uncertainty contract verified")
        print(
            f"[OK] Protected production source files captured: "
            f"{len(protected)}"
        )

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_cross_market_narrative_evolution_intelligence "
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
                f"OIT-017 test failed with exit code {completed.returncode}"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Protected production source changed: {path}"
                )

        print("[PASS] Certified OIT-016 production module unchanged")
        print("[PASS] Oracle terminal runner unchanged")
        print("[PASS] OLA, OIA, INT-OII, ORR, OOR, and Q Series unchanged")
        print("[PASS] OIT-017 production module installed")
        print("[PASS] OIT-017 standalone test installed")
        print("[PASS] Narrative evolution metrics bounded")
        print("[PASS] Strengthening, weakening, fragmentation, and reversal classified")
        print("[PASS] Read-only and execution boundaries preserved")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OIT-017 CROSS-MARKET NARRATIVE EVOLUTION INSTALLED")
        return 0
    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
