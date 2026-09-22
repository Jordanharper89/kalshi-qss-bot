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
            / "oracle_cross_market_intelligence_relationship_analysis.py"
        )
        if required.is_file():
            return candidate
    raise SystemExit("[ERROR] Could not locate current Q Series repository.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"
OIT_014 = PACKAGE / "oracle_cross_market_intelligence_relationship_analysis.py"
PRODUCTION = PACKAGE / "oracle_cross_market_causal_intelligence_analysis.py"
TEST = ROOT / "test_oit_015_oracle_cross_market_causal_intelligence_analysis.py"
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass\nfrom pathlib import Path\nfrom typing import Any, Mapping\n\nfrom .oracle_cross_market_intelligence_relationship_analysis import (\n    OracleCrossMarketIntelligenceReport,\n    OracleCrossMarketRelationship,\n    OracleCrossMarketRelationshipInvariantError,\n    build_cross_market_intelligence_report,\n    verify_cross_market_intelligence_report,\n)\n\nSCHEMA_VERSION = "OIT-015"\nENGINE_ID = "OIT-015"\nPOLICY_ID = "oracle.cross-market-causal-intelligence-analysis.v1"\nMAX_CAUSAL_CONFIDENCE = 0.85\n\n\nclass OracleCausalIntelligenceInvariantError(\n    OracleCrossMarketRelationshipInvariantError\n):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleCausalHypothesis:\n    hypothesis_index: int\n    cause_record_id: str\n    effect_record_id: str\n    shared_entities: tuple[str, ...]\n    temporal_order: str\n    causal_direction: str\n    causal_type: str\n    evidence_class: str\n    probability_distance: float | None\n    relationship_score: float\n    causal_confidence: float\n    supports_causation: bool\n    contradicts_causation: bool\n    limitations: tuple[str, ...]\n    rationale: tuple[str, ...]\n    source_relationship_hash: str\n    read_only: bool\n    hypothesis_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleCausalIntelligenceReport:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    status: str\n    repository_root: str\n    query: str\n    cross_market_report_hash: str\n    hypotheses: tuple[OracleCausalHypothesis, ...]\n    hypothesis_count: int\n    supportive_hypothesis_count: int\n    suppressive_hypothesis_count: int\n    associative_hypothesis_count: int\n    insufficient_hypothesis_count: int\n    causal_state: str\n    causal_summary: str\n    read_only: bool\n    analytics_execution_performed: bool\n    database_access_performed: bool\n    publication_allowed: bool\n    qseries_execution_allowed: bool\n    failure_reason: str | None\n    report_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if isinstance(value, (list, tuple)):\n        return [_canonical(item) for item in value]\n    if isinstance(value, Path):\n        return value.as_posix()\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    return repr(value)\n\n\ndef _stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=True,\n    ).encode("utf-8")\n    return hashlib.sha256(payload).hexdigest()\n\n\ndef _bounded(value: float) -> float:\n    return round(max(0.0, min(MAX_CAUSAL_CONFIDENCE, value)), 6)\n\n\ndef _temporal_order(\n    relationship: OracleCrossMarketRelationship,\n) -> tuple[str, str, str]:\n    temporal = relationship.temporal_relationship.strip().lower()\n    if temporal == "left_leads_right":\n        return (\n            relationship.left_record_id,\n            relationship.right_record_id,\n            "left_precedes_right",\n        )\n    if temporal == "right_leads_left":\n        return (\n            relationship.right_record_id,\n            relationship.left_record_id,\n            "right_precedes_left",\n        )\n    return (\n        relationship.left_record_id,\n        relationship.right_record_id,\n        temporal or "undetermined",\n    )\n\n\ndef _classify(\n    relationship: OracleCrossMarketRelationship,\n) -> tuple[str, str, bool, bool, float, tuple[str, ...], tuple[str, ...]]:\n    shared = relationship.shared_entity_count > 0\n    temporal = relationship.temporal_relationship.strip().lower()\n    directional = relationship.directional_relationship.strip().lower()\n    has_order = temporal in {"left_leads_right", "right_leads_left"}\n    strong_enough = relationship.relationship_score >= 0.50\n\n    limitations = [\n        "observational evidence cannot establish causation by itself",\n        "unobserved confounders may explain the relationship",\n    ]\n    rationale = [\n        f"shared semantic entities: {relationship.shared_entity_count}",\n        f"temporal relationship: {relationship.temporal_relationship}",\n        f"directional relationship: {relationship.directional_relationship}",\n        f"relationship score: {relationship.relationship_score:.6f}",\n    ]\n\n    base = relationship.relationship_score * 0.55\n    if shared:\n        base += 0.10\n    if has_order:\n        base += 0.10\n    if relationship.probability_distance is not None:\n        base += max(0.0, 0.10 * (1.0 - relationship.probability_distance))\n\n    if shared and has_order and directional == "aligned" and strong_enough:\n        rationale.append("ordered and aligned evidence supports a causal hypothesis")\n        limitations.append("mechanism has not yet been independently verified")\n        return (\n            "supportive",\n            "candidate_influence",\n            True,\n            False,\n            _bounded(base),\n            tuple(limitations),\n            tuple(rationale),\n        )\n\n    if shared and has_order and directional == "contradictory":\n        rationale.append(\n            "ordered contradictory movement supports a suppressive hypothesis"\n        )\n        limitations.append(\n            "inverse movement may reflect hedging, substitution, or a confounder"\n        )\n        return (\n            "suppressive",\n            "candidate_inhibitory_influence",\n            True,\n            True,\n            _bounded(base - 0.05),\n            tuple(limitations),\n            tuple(rationale),\n        )\n\n    if shared and not has_order:\n        rationale.append("semantic relationship exists without stable lead-lag order")\n        limitations.append("temporal precedence is not established")\n        return (\n            "associative",\n            "non_directional_association",\n            False,\n            False,\n            _bounded(base - 0.15),\n            tuple(limitations),\n            tuple(rationale),\n        )\n\n    rationale.append("available relationship evidence is insufficient for causation")\n    limitations.append("minimum semantic and temporal conditions are unmet")\n    return (\n        "insufficient",\n        "no_causal_classification",\n        False,\n        False,\n        _bounded(base - 0.25),\n        tuple(limitations),\n        tuple(rationale),\n    )\n\n\ndef _build_hypothesis(\n    relationship: OracleCrossMarketRelationship,\n    index: int,\n) -> OracleCausalHypothesis:\n    cause, effect, temporal_order = _temporal_order(relationship)\n    (\n        evidence_class,\n        causal_type,\n        supports,\n        contradicts,\n        confidence,\n        limitations,\n        rationale,\n    ) = _classify(relationship)\n\n    body = {\n        "hypothesis_index": index,\n        "cause_record_id": cause,\n        "effect_record_id": effect,\n        "shared_entities": tuple(relationship.shared_entities),\n        "temporal_order": temporal_order,\n        "causal_direction": f"{cause}->{effect}",\n        "causal_type": causal_type,\n        "evidence_class": evidence_class,\n        "probability_distance": relationship.probability_distance,\n        "relationship_score": relationship.relationship_score,\n        "causal_confidence": confidence,\n        "supports_causation": supports,\n        "contradicts_causation": contradicts,\n        "limitations": limitations,\n        "rationale": rationale,\n        "source_relationship_hash": relationship.relationship_hash,\n        "read_only": True,\n    }\n    return OracleCausalHypothesis(\n        **body,\n        hypothesis_hash=_stable_hash(body),\n    )\n\n\ndef verify_causal_hypothesis(hypothesis: OracleCausalHypothesis) -> bool:\n    body = asdict(hypothesis)\n    supplied = body.pop("hypothesis_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleCausalIntelligenceInvariantError(\n            "causal hypothesis hash mismatch"\n        )\n    if not hypothesis.read_only:\n        raise OracleCausalIntelligenceInvariantError(\n            "causal hypothesis is not read-only"\n        )\n    if not (0.0 <= hypothesis.causal_confidence <= MAX_CAUSAL_CONFIDENCE):\n        raise OracleCausalIntelligenceInvariantError(\n            "causal confidence exceeds bounded policy"\n        )\n    if not hypothesis.source_relationship_hash:\n        raise OracleCausalIntelligenceInvariantError(\n            "source relationship lineage missing"\n        )\n    if hypothesis.cause_record_id == hypothesis.effect_record_id:\n        raise OracleCausalIntelligenceInvariantError(\n            "self-causation hypothesis forbidden"\n        )\n    return True\n\n\ndef _summary(hypotheses: tuple[OracleCausalHypothesis, ...]) -> tuple[str, str]:\n    if not hypotheses:\n        return (\n            "no_causal_evidence",\n            "No certified cross-market relationships were available for causal inspection.",\n        )\n    supportive = sum(item.evidence_class == "supportive" for item in hypotheses)\n    suppressive = sum(item.evidence_class == "suppressive" for item in hypotheses)\n    associative = sum(item.evidence_class == "associative" for item in hypotheses)\n    insufficient = sum(item.evidence_class == "insufficient" for item in hypotheses)\n    if supportive or suppressive:\n        state = "bounded_causal_hypotheses_present"\n    elif associative:\n        state = "associations_without_causal_order"\n    else:\n        state = "insufficient_causal_evidence"\n    return (\n        state,\n        (\n            f"{len(hypotheses)} bounded causal inspections: "\n            f"{supportive} supportive, {suppressive} suppressive, "\n            f"{associative} associative, {insufficient} insufficient. "\n            "No hypothesis is treated as proof of causation."\n        ),\n    )\n\n\ndef build_causal_intelligence_report(\n    repository_root: str | Path,\n    query: str,\n    *,\n    cross_market_report: OracleCrossMarketIntelligenceReport | None = None,\n) -> OracleCausalIntelligenceReport:\n    root = Path(repository_root).resolve()\n    source = cross_market_report\n    if source is None:\n        source = build_cross_market_intelligence_report(root, query)\n    verify_cross_market_intelligence_report(source)\n\n    hypotheses = tuple(\n        _build_hypothesis(relationship, index)\n        for index, relationship in enumerate(source.relationships, start=1)\n    )\n    for hypothesis in hypotheses:\n        verify_causal_hypothesis(hypothesis)\n\n    causal_state, causal_summary = _summary(hypotheses)\n    supportive = sum(item.evidence_class == "supportive" for item in hypotheses)\n    suppressive = sum(item.evidence_class == "suppressive" for item in hypotheses)\n    associative = sum(item.evidence_class == "associative" for item in hypotheses)\n    insufficient = sum(item.evidence_class == "insufficient" for item in hypotheses)\n\n    body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root),\n        "query": str(query),\n        "cross_market_report_hash": source.report_hash,\n        "hypotheses": hypotheses,\n        "hypothesis_count": len(hypotheses),\n        "supportive_hypothesis_count": supportive,\n        "suppressive_hypothesis_count": suppressive,\n        "associative_hypothesis_count": associative,\n        "insufficient_hypothesis_count": insufficient,\n        "causal_state": causal_state,\n        "causal_summary": causal_summary,\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "publication_allowed": False,\n        "qseries_execution_allowed": False,\n        "failure_reason": None,\n    }\n    report = OracleCausalIntelligenceReport(\n        **body,\n        report_hash=_stable_hash(body),\n    )\n    verify_causal_intelligence_report(report)\n    return report\n\n\ndef verify_causal_intelligence_report(\n    report: OracleCausalIntelligenceReport,\n) -> bool:\n    body = asdict(report)\n    supplied = body.pop("report_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleCausalIntelligenceInvariantError(\n            "causal intelligence report hash mismatch"\n        )\n    if report.schema_version != SCHEMA_VERSION:\n        raise OracleCausalIntelligenceInvariantError("schema mismatch")\n    if report.policy_id != POLICY_ID:\n        raise OracleCausalIntelligenceInvariantError("policy mismatch")\n    if not report.read_only:\n        raise OracleCausalIntelligenceInvariantError("report is not read-only")\n    if (\n        report.analytics_execution_performed\n        or report.database_access_performed\n        or report.publication_allowed\n        or report.qseries_execution_allowed\n    ):\n        raise OracleCausalIntelligenceInvariantError(\n            "forbidden runtime capability enabled"\n        )\n    if report.hypothesis_count != len(report.hypotheses):\n        raise OracleCausalIntelligenceInvariantError(\n            "hypothesis count mismatch"\n        )\n    counts = {\n        "supportive": report.supportive_hypothesis_count,\n        "suppressive": report.suppressive_hypothesis_count,\n        "associative": report.associative_hypothesis_count,\n        "insufficient": report.insufficient_hypothesis_count,\n    }\n    for evidence_class, expected in counts.items():\n        actual = sum(\n            item.evidence_class == evidence_class\n            for item in report.hypotheses\n        )\n        if actual != expected:\n            raise OracleCausalIntelligenceInvariantError(\n                f"{evidence_class} count mismatch"\n            )\n    if sum(counts.values()) != report.hypothesis_count:\n        raise OracleCausalIntelligenceInvariantError(\n            "classified hypothesis count mismatch"\n        )\n    for hypothesis in report.hypotheses:\n        verify_causal_hypothesis(hypothesis)\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import replace\nfrom pathlib import Path\nfrom tempfile import TemporaryDirectory\n\nfrom qseries_v2.oracle_terminal.oracle_cross_market_intelligence_relationship_analysis import (\n    ENGINE_ID as OIT_014_ENGINE_ID,\n    POLICY_ID as OIT_014_POLICY_ID,\n    SCHEMA_VERSION as OIT_014_SCHEMA_VERSION,\n    OracleCrossMarketIntelligenceReport,\n    OracleCrossMarketRecordProfile,\n    OracleCrossMarketRelationship,\n    _stable_hash as oit_014_hash,\n    verify_cross_market_intelligence_report,\n)\nfrom qseries_v2.oracle_terminal.oracle_cross_market_causal_intelligence_analysis import (\n    MAX_CAUSAL_CONFIDENCE,\n    OracleCausalIntelligenceInvariantError,\n    build_causal_intelligence_report,\n    verify_causal_intelligence_report,\n)\n\n\ndef make_profile(index: int, record_id: str, entity: str):\n    body = {\n        "profile_index": index,\n        "evidence_index": index,\n        "record_id": record_id,\n        "title": record_id,\n        "entities": (entity,),\n        "venue": "Kalshi",\n        "category": "Crypto",\n        "probability": 0.60,\n        "direction": "positive",\n        "timestamp_utc": f"2026-07-30T0{index}:00:00Z",\n        "epoch_seconds": 1000 + index,\n        "artifact_relative_path": "runtime/certified.json",\n        "artifact_sha256": "a" * 64,\n        "record_hash": f"record-{index}",\n        "evidence_hash": f"evidence-{index}",\n        "inspection_hash": f"inspection-{index}",\n        "temporal_event_hash": f"temporal-{index}",\n        "source_record_locator": f"$.records[{index - 1}]",\n        "read_only": True,\n    }\n    return OracleCrossMarketRecordProfile(\n        **body,\n        profile_hash=oit_014_hash(body),\n    )\n\n\ndef make_relationship(\n    index: int,\n    left: str,\n    right: str,\n    temporal: str,\n    directional: str,\n    score: float,\n):\n    body = {\n        "relationship_index": index,\n        "left_profile_index": index,\n        "right_profile_index": index + 1,\n        "left_record_id": left,\n        "right_record_id": right,\n        "shared_entities": ("Bitcoin",),\n        "shared_entity_count": 1,\n        "elapsed_seconds": 3600,\n        "temporal_relationship": temporal,\n        "directional_relationship": directional,\n        "probability_distance": 0.10,\n        "evidence_dependence": "independent_evidence",\n        "relationship_score": score,\n        "relationship_strength": "strong" if score >= 0.70 else "moderate",\n        "rationale": ("certified relationship",),\n        "read_only": True,\n    }\n    return OracleCrossMarketRelationship(\n        **body,\n        relationship_hash=oit_014_hash(body),\n    )\n\n\ndef make_report(root: Path):\n    profiles = (\n        make_profile(1, "BTC-ETF", "Bitcoin"),\n        make_profile(2, "BTC-PRICE", "Bitcoin"),\n        make_profile(3, "BTC-MINER", "Bitcoin"),\n    )\n    relationships = (\n        make_relationship(\n            1,\n            "BTC-ETF",\n            "BTC-PRICE",\n            "left_leads_right",\n            "aligned",\n            0.80,\n        ),\n        make_relationship(\n            2,\n            "BTC-PRICE",\n            "BTC-MINER",\n            "left_leads_right",\n            "contradictory",\n            0.72,\n        ),\n    )\n    body = {\n        "schema_version": OIT_014_SCHEMA_VERSION,\n        "engine_id": OIT_014_ENGINE_ID,\n        "policy_id": OIT_014_POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root.resolve()),\n        "query": "What is causing the cross-market Bitcoin movement?",\n        "answer_hash": "answer-hash",\n        "query_plan_hash": "plan-hash",\n        "query_result_hash": "result-hash",\n        "temporal_report_hash": "temporal-report-hash",\n        "profiles": profiles,\n        "relationships": relationships,\n        "profile_count": 3,\n        "relationship_count": 2,\n        "connected_profile_count": 3,\n        "independent_profile_count": 0,\n        "strong_relationship_count": 2,\n        "moderate_relationship_count": 0,\n        "weak_relationship_count": 0,\n        "lead_lag_relationship_count": 2,\n        "contradictory_direction_count": 1,\n        "relationship_state": "connected_cross_market_evidence",\n        "relationship_summary": "Two certified relationships.",\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "publication_allowed": False,\n        "qseries_execution_allowed": False,\n        "failure_reason": None,\n    }\n    report = OracleCrossMarketIntelligenceReport(\n        **body,\n        report_hash=oit_014_hash(body),\n    )\n    verify_cross_market_intelligence_report(report)\n    return report\n\n\ndef main() -> int:\n    print("=" * 40)\n    print(" OIT-015 TEST")\n    print(" CROSS-MARKET CAUSAL INTELLIGENCE")\n    print("=" * 40)\n\n    with TemporaryDirectory() as temporary:\n        root = Path(temporary)\n        source = make_report(root)\n        report = build_causal_intelligence_report(\n            root,\n            source.query,\n            cross_market_report=source,\n        )\n\n        assert report.cross_market_report_hash == source.report_hash\n        assert report.hypothesis_count == 2\n        assert report.supportive_hypothesis_count == 1\n        assert report.suppressive_hypothesis_count == 1\n        assert report.associative_hypothesis_count == 0\n        assert report.insufficient_hypothesis_count == 0\n\n        supportive, suppressive = report.hypotheses\n        assert supportive.cause_record_id == "BTC-ETF"\n        assert supportive.effect_record_id == "BTC-PRICE"\n        assert supportive.evidence_class == "supportive"\n        assert supportive.supports_causation\n        assert not supportive.contradicts_causation\n\n        assert suppressive.cause_record_id == "BTC-PRICE"\n        assert suppressive.effect_record_id == "BTC-MINER"\n        assert suppressive.evidence_class == "suppressive"\n        assert suppressive.supports_causation\n        assert suppressive.contradicts_causation\n\n        assert all(\n            item.causal_confidence <= MAX_CAUSAL_CONFIDENCE\n            for item in report.hypotheses\n        )\n        assert all(\n            "observational evidence cannot establish causation by itself"\n            in item.limitations\n            for item in report.hypotheses\n        )\n\n        replay = build_causal_intelligence_report(\n            root,\n            source.query,\n            cross_market_report=source,\n        )\n        assert replay == report\n        assert verify_causal_intelligence_report(report)\n\n        tampered = replace(\n            report,\n            causal_summary=report.causal_summary + " tampered",\n        )\n        try:\n            verify_causal_intelligence_report(tampered)\n        except OracleCausalIntelligenceInvariantError:\n            pass\n        else:\n            raise AssertionError("tampered causal report was accepted")\n\n        assert report.read_only\n        assert not report.analytics_execution_performed\n        assert not report.database_access_performed\n        assert not report.publication_allowed\n        assert not report.qseries_execution_allowed\n\n    print("[PASS] Certified OIT-014 cross-market report consumed")\n    print("[PASS] Supportive causal hypothesis classified")\n    print("[PASS] Suppressive causal hypothesis classified")\n    print("[PASS] Temporal cause and effect ordering preserved")\n    print("[PASS] Causal confidence bounded below certainty")\n    print("[PASS] Correlation never represented as causal proof")\n    print("[PASS] Complete source relationship lineage retained")\n    print("[PASS] Causal report deterministic across replay")\n    print("[PASS] Tampered causal report rejected")\n    print("[PASS] No analytics execution or database access performed")\n    print("[PASS] Publication and Q Series execution disabled")\n    print("[DONE] OIT-015 CROSS-MARKET CAUSAL INTELLIGENCE PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


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
    for path in (OIT_014, RUNNER):
        if path.is_file():
            protected[path] = sha256(path)
    return protected


def require_oit_014() -> None:
    if not OIT_014.is_file():
        raise RuntimeError(f"Certified OIT-014 module missing: {OIT_014}")
    source = OIT_014.read_text(encoding="utf-8")
    required = (
        'SCHEMA_VERSION = "OIT-014"',
        'POLICY_ID = "oracle.cross-market-intelligence-relationship-analysis.v2"',
        "OracleCrossMarketIntelligenceReport",
        "OracleCrossMarketRelationship",
        "build_cross_market_intelligence_report",
        "verify_cross_market_intelligence_report",
        "relationship_hash",
        "publication_allowed",
        "qseries_execution_allowed",
    )
    missing = [token for token in required if token not in source]
    if missing:
        raise RuntimeError(
            f"Certified OIT-014 V2 contract mismatch: {missing}"
        )


def main() -> int:
    print("=" * 40)
    print(" OIT-015 INSTALLER")
    print(" CROSS-MARKET CAUSAL INTELLIGENCE")
    print("=" * 40)
    try:
        require_oit_014()
        protected = protected_sources()
        print("[OK] Certified OIT-014 V2 relationship contract verified")
        print(f"[OK] Protected production source files captured: {len(protected)}")

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_cross_market_causal_intelligence_analysis import *"
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
                f"OIT-015 test failed with exit code {completed.returncode}"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Protected production source changed: {path}"
                )

        print("[PASS] Certified OIT-014 production module unchanged")
        print("[PASS] Oracle terminal runner unchanged")
        print("[PASS] OLA, OIA, INT-OII, ORR, OOR, and Q Series unchanged")
        print("[PASS] OIT-015 production module installed")
        print("[PASS] OIT-015 standalone test installed")
        print("[PASS] Bounded causal hypotheses generated deterministically")
        print("[PASS] Correlation-to-causation overclaiming prohibited")
        print("[PASS] Read-only and execution boundaries preserved")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OIT-015 CROSS-MARKET CAUSAL INTELLIGENCE INSTALLED")
        return 0
    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
