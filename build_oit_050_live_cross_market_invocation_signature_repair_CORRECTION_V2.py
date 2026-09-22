from __future__ import annotations

import ast
import hashlib
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def locate_repository() -> Path:
    candidates: list[Path] = []
    for base in (Path.cwd().resolve(), SCRIPT_DIR):
        candidates.extend((base, base / "kalshi-qss-bot"))
        for parent in base.parents:
            candidates.extend((parent, parent / "kalshi-qss-bot"))

    seen: set[Path] = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)

        package = candidate / "qseries_v2" / "oracle_terminal"
        target = (
            package
            / "oracle_cross_market_causal_intelligence_analysis.py"
        )
        upstream = (
            package
            / "oracle_cross_market_intelligence_relationship_analysis.py"
        )
        freeze_test = (
            candidate
            / "test_oit_050_oracle_terminal_final_freeze_and_completion.py"
        )

        if target.is_file() and upstream.is_file() and freeze_test.is_file():
            return candidate

    raise SystemExit(
        "[ERROR] Could not locate current Q Series repository."
    )


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"

TARGET = (
    PACKAGE
    / "oracle_cross_market_causal_intelligence_analysis.py"
)
UPSTREAM = (
    PACKAGE
    / "oracle_cross_market_intelligence_relationship_analysis.py"
)
OIT_050 = (
    PACKAGE
    / "oracle_terminal_final_freeze_and_completion.py"
)
OIT_050_TEST = (
    ROOT
    / "test_oit_050_oracle_terminal_final_freeze_and_completion.py"
)
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"

TEST = (
    ROOT
    / "test_oit_050_live_cross_market_invocation_signature_repair.py"
)

PRODUCTION_SOURCE = 'from __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass\nfrom pathlib import Path\nfrom typing import Any, Mapping\n\nfrom .oracle_cross_market_intelligence_relationship_analysis import (\n    OracleCrossMarketIntelligenceReport,\n    OracleCrossMarketRelationship,\n    OracleCrossMarketRelationshipInvariantError,\n    build_cross_market_intelligence_report,\n    verify_cross_market_intelligence_report,\n)\n\nSCHEMA_VERSION = "OIT-015"\nENGINE_ID = "OIT-015"\nPOLICY_ID = "oracle.cross-market-causal-intelligence-analysis.v1"\nMAX_CAUSAL_CONFIDENCE = 0.85\n\n\nclass OracleCausalIntelligenceInvariantError(\n    OracleCrossMarketRelationshipInvariantError\n):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleCausalHypothesis:\n    hypothesis_index: int\n    cause_record_id: str\n    effect_record_id: str\n    shared_entities: tuple[str, ...]\n    temporal_order: str\n    causal_direction: str\n    causal_type: str\n    evidence_class: str\n    probability_distance: float | None\n    relationship_score: float\n    causal_confidence: float\n    supports_causation: bool\n    contradicts_causation: bool\n    limitations: tuple[str, ...]\n    rationale: tuple[str, ...]\n    source_relationship_hash: str\n    read_only: bool\n    hypothesis_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleCausalIntelligenceReport:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    status: str\n    repository_root: str\n    query: str\n    cross_market_report_hash: str\n    hypotheses: tuple[OracleCausalHypothesis, ...]\n    hypothesis_count: int\n    supportive_hypothesis_count: int\n    suppressive_hypothesis_count: int\n    associative_hypothesis_count: int\n    insufficient_hypothesis_count: int\n    causal_state: str\n    causal_summary: str\n    read_only: bool\n    analytics_execution_performed: bool\n    database_access_performed: bool\n    publication_allowed: bool\n    qseries_execution_allowed: bool\n    failure_reason: str | None\n    report_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if isinstance(value, (list, tuple)):\n        return [_canonical(item) for item in value]\n    if isinstance(value, Path):\n        return value.as_posix()\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    return repr(value)\n\n\ndef _stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=True,\n    ).encode("utf-8")\n    return hashlib.sha256(payload).hexdigest()\n\n\ndef _bounded(value: float) -> float:\n    return round(max(0.0, min(MAX_CAUSAL_CONFIDENCE, value)), 6)\n\n\ndef _temporal_order(\n    relationship: OracleCrossMarketRelationship,\n) -> tuple[str, str, str]:\n    temporal = relationship.temporal_relationship.strip().lower()\n    if temporal == "left_leads_right":\n        return (\n            relationship.left_record_id,\n            relationship.right_record_id,\n            "left_precedes_right",\n        )\n    if temporal == "right_leads_left":\n        return (\n            relationship.right_record_id,\n            relationship.left_record_id,\n            "right_precedes_left",\n        )\n    return (\n        relationship.left_record_id,\n        relationship.right_record_id,\n        temporal or "undetermined",\n    )\n\n\ndef _classify(\n    relationship: OracleCrossMarketRelationship,\n) -> tuple[str, str, bool, bool, float, tuple[str, ...], tuple[str, ...]]:\n    shared = relationship.shared_entity_count > 0\n    temporal = relationship.temporal_relationship.strip().lower()\n    directional = relationship.directional_relationship.strip().lower()\n    has_order = temporal in {"left_leads_right", "right_leads_left"}\n    strong_enough = relationship.relationship_score >= 0.50\n\n    limitations = [\n        "observational evidence cannot establish causation by itself",\n        "unobserved confounders may explain the relationship",\n    ]\n    rationale = [\n        f"shared semantic entities: {relationship.shared_entity_count}",\n        f"temporal relationship: {relationship.temporal_relationship}",\n        f"directional relationship: {relationship.directional_relationship}",\n        f"relationship score: {relationship.relationship_score:.6f}",\n    ]\n\n    base = relationship.relationship_score * 0.55\n    if shared:\n        base += 0.10\n    if has_order:\n        base += 0.10\n    if relationship.probability_distance is not None:\n        base += max(0.0, 0.10 * (1.0 - relationship.probability_distance))\n\n    if shared and has_order and directional == "aligned" and strong_enough:\n        rationale.append("ordered and aligned evidence supports a causal hypothesis")\n        limitations.append("mechanism has not yet been independently verified")\n        return (\n            "supportive",\n            "candidate_influence",\n            True,\n            False,\n            _bounded(base),\n            tuple(limitations),\n            tuple(rationale),\n        )\n\n    if shared and has_order and directional == "contradictory":\n        rationale.append(\n            "ordered contradictory movement supports a suppressive hypothesis"\n        )\n        limitations.append(\n            "inverse movement may reflect hedging, substitution, or a confounder"\n        )\n        return (\n            "suppressive",\n            "candidate_inhibitory_influence",\n            True,\n            True,\n            _bounded(base - 0.05),\n            tuple(limitations),\n            tuple(rationale),\n        )\n\n    if shared and not has_order:\n        rationale.append("semantic relationship exists without stable lead-lag order")\n        limitations.append("temporal precedence is not established")\n        return (\n            "associative",\n            "non_directional_association",\n            False,\n            False,\n            _bounded(base - 0.15),\n            tuple(limitations),\n            tuple(rationale),\n        )\n\n    rationale.append("available relationship evidence is insufficient for causation")\n    limitations.append("minimum semantic and temporal conditions are unmet")\n    return (\n        "insufficient",\n        "no_causal_classification",\n        False,\n        False,\n        _bounded(base - 0.25),\n        tuple(limitations),\n        tuple(rationale),\n    )\n\n\ndef _build_hypothesis(\n    relationship: OracleCrossMarketRelationship,\n    index: int,\n) -> OracleCausalHypothesis:\n    cause, effect, temporal_order = _temporal_order(relationship)\n    (\n        evidence_class,\n        causal_type,\n        supports,\n        contradicts,\n        confidence,\n        limitations,\n        rationale,\n    ) = _classify(relationship)\n\n    body = {\n        "hypothesis_index": index,\n        "cause_record_id": cause,\n        "effect_record_id": effect,\n        "shared_entities": tuple(relationship.shared_entities),\n        "temporal_order": temporal_order,\n        "causal_direction": f"{cause}->{effect}",\n        "causal_type": causal_type,\n        "evidence_class": evidence_class,\n        "probability_distance": relationship.probability_distance,\n        "relationship_score": relationship.relationship_score,\n        "causal_confidence": confidence,\n        "supports_causation": supports,\n        "contradicts_causation": contradicts,\n        "limitations": limitations,\n        "rationale": rationale,\n        "source_relationship_hash": relationship.relationship_hash,\n        "read_only": True,\n    }\n    return OracleCausalHypothesis(\n        **body,\n        hypothesis_hash=_stable_hash(body),\n    )\n\n\ndef verify_causal_hypothesis(hypothesis: OracleCausalHypothesis) -> bool:\n    body = asdict(hypothesis)\n    supplied = body.pop("hypothesis_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleCausalIntelligenceInvariantError(\n            "causal hypothesis hash mismatch"\n        )\n    if not hypothesis.read_only:\n        raise OracleCausalIntelligenceInvariantError(\n            "causal hypothesis is not read-only"\n        )\n    if not (0.0 <= hypothesis.causal_confidence <= MAX_CAUSAL_CONFIDENCE):\n        raise OracleCausalIntelligenceInvariantError(\n            "causal confidence exceeds bounded policy"\n        )\n    if not hypothesis.source_relationship_hash:\n        raise OracleCausalIntelligenceInvariantError(\n            "source relationship lineage missing"\n        )\n    if hypothesis.cause_record_id == hypothesis.effect_record_id:\n        raise OracleCausalIntelligenceInvariantError(\n            "self-causation hypothesis forbidden"\n        )\n    return True\n\n\ndef _summary(hypotheses: tuple[OracleCausalHypothesis, ...]) -> tuple[str, str]:\n    if not hypotheses:\n        return (\n            "no_causal_evidence",\n            "No certified cross-market relationships were available for causal inspection.",\n        )\n    supportive = sum(item.evidence_class == "supportive" for item in hypotheses)\n    suppressive = sum(item.evidence_class == "suppressive" for item in hypotheses)\n    associative = sum(item.evidence_class == "associative" for item in hypotheses)\n    insufficient = sum(item.evidence_class == "insufficient" for item in hypotheses)\n    if supportive or suppressive:\n        state = "bounded_causal_hypotheses_present"\n    elif associative:\n        state = "associations_without_causal_order"\n    else:\n        state = "insufficient_causal_evidence"\n    return (\n        state,\n        (\n            f"{len(hypotheses)} bounded causal inspections: "\n            f"{supportive} supportive, {suppressive} suppressive, "\n            f"{associative} associative, {insufficient} insufficient. "\n            "No hypothesis is treated as proof of causation."\n        ),\n    )\n\n\ndef build_causal_intelligence_report(\n    repository_root: str | Path,\n    query: str,\n    *,\n    cross_market_report: OracleCrossMarketIntelligenceReport | None = None,\n) -> OracleCausalIntelligenceReport:\n    root = Path(repository_root).resolve()\n    source = cross_market_report\n    if source is None:\n        source = build_cross_market_intelligence_report(\n            repository_root=root,\n            query=query,\n        )\n    verify_cross_market_intelligence_report(source)\n\n    hypotheses = tuple(\n        _build_hypothesis(relationship, index)\n        for index, relationship in enumerate(source.relationships, start=1)\n    )\n    for hypothesis in hypotheses:\n        verify_causal_hypothesis(hypothesis)\n\n    causal_state, causal_summary = _summary(hypotheses)\n    supportive = sum(item.evidence_class == "supportive" for item in hypotheses)\n    suppressive = sum(item.evidence_class == "suppressive" for item in hypotheses)\n    associative = sum(item.evidence_class == "associative" for item in hypotheses)\n    insufficient = sum(item.evidence_class == "insufficient" for item in hypotheses)\n\n    body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root),\n        "query": str(query),\n        "cross_market_report_hash": source.report_hash,\n        "hypotheses": hypotheses,\n        "hypothesis_count": len(hypotheses),\n        "supportive_hypothesis_count": supportive,\n        "suppressive_hypothesis_count": suppressive,\n        "associative_hypothesis_count": associative,\n        "insufficient_hypothesis_count": insufficient,\n        "causal_state": causal_state,\n        "causal_summary": causal_summary,\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "publication_allowed": False,\n        "qseries_execution_allowed": False,\n        "failure_reason": None,\n    }\n    report = OracleCausalIntelligenceReport(\n        **body,\n        report_hash=_stable_hash(body),\n    )\n    verify_causal_intelligence_report(report)\n    return report\n\n\ndef verify_causal_intelligence_report(\n    report: OracleCausalIntelligenceReport,\n) -> bool:\n    body = asdict(report)\n    supplied = body.pop("report_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleCausalIntelligenceInvariantError(\n            "causal intelligence report hash mismatch"\n        )\n    if report.schema_version != SCHEMA_VERSION:\n        raise OracleCausalIntelligenceInvariantError("schema mismatch")\n    if report.policy_id != POLICY_ID:\n        raise OracleCausalIntelligenceInvariantError("policy mismatch")\n    if not report.read_only:\n        raise OracleCausalIntelligenceInvariantError("report is not read-only")\n    if (\n        report.analytics_execution_performed\n        or report.database_access_performed\n        or report.publication_allowed\n        or report.qseries_execution_allowed\n    ):\n        raise OracleCausalIntelligenceInvariantError(\n            "forbidden runtime capability enabled"\n        )\n    if report.hypothesis_count != len(report.hypotheses):\n        raise OracleCausalIntelligenceInvariantError(\n            "hypothesis count mismatch"\n        )\n    counts = {\n        "supportive": report.supportive_hypothesis_count,\n        "suppressive": report.suppressive_hypothesis_count,\n        "associative": report.associative_hypothesis_count,\n        "insufficient": report.insufficient_hypothesis_count,\n    }\n    for evidence_class, expected in counts.items():\n        actual = sum(\n            item.evidence_class == evidence_class\n            for item in report.hypotheses\n        )\n        if actual != expected:\n            raise OracleCausalIntelligenceInvariantError(\n                f"{evidence_class} count mismatch"\n            )\n    if sum(counts.values()) != report.hypothesis_count:\n        raise OracleCausalIntelligenceInvariantError(\n            "classified hypothesis count mismatch"\n        )\n    for hypothesis in report.hypotheses:\n        verify_causal_hypothesis(hypothesis)\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nimport inspect\nfrom pathlib import Path\nfrom types import SimpleNamespace\n\nfrom qseries_v2.oracle_terminal import (\n    oracle_cross_market_causal_intelligence_analysis as causal_module,\n)\nfrom qseries_v2.oracle_terminal.oracle_cross_market_causal_intelligence_analysis import (\n    build_causal_intelligence_report,\n    verify_causal_intelligence_report,\n)\nfrom qseries_v2.oracle_terminal.oracle_cross_market_intelligence_relationship_analysis import (\n    build_cross_market_intelligence_report,\n)\n\n\ndef main() -> int:\n    print("=" * 56)\n    print(" OIT-050 DEFECT CORRECTION TEST")\n    print(" LIVE CROSS-MARKET INVOCATION SIGNATURE REPAIR")\n    print("=" * 56)\n\n    signature = inspect.signature(\n        build_cross_market_intelligence_report\n    )\n    repository_parameter = signature.parameters["repository_root"]\n    query_parameter = signature.parameters["query"]\n\n    assert repository_parameter.kind is inspect.Parameter.KEYWORD_ONLY\n    assert query_parameter.kind is inspect.Parameter.KEYWORD_ONLY\n\n    production_path = Path(causal_module.__file__).resolve()\n    production_source = production_path.read_text(encoding="utf-8")\n\n    assert (\n        "build_cross_market_intelligence_report(root, query)"\n        not in production_source\n    )\n    assert (\n        "build_cross_market_intelligence_report("\n        in production_source\n    )\n    assert "repository_root=root" in production_source\n    assert "query=query" in production_source\n\n    calls: list[dict[str, object]] = []\n\n    def keyword_only_cross_market_builder(\n        *,\n        repository_root: Path,\n        query: str,\n        result_limit: int = 10,\n    ):\n        calls.append(\n            {\n                "repository_root": repository_root,\n                "query": query,\n                "result_limit": result_limit,\n            }\n        )\n        return SimpleNamespace(\n            relationships=(),\n            report_hash="cross-market-report-hash-defect-test",\n        )\n\n    original_builder = (\n        causal_module.build_cross_market_intelligence_report\n    )\n    original_verifier = (\n        causal_module.verify_cross_market_intelligence_report\n    )\n\n    try:\n        causal_module.build_cross_market_intelligence_report = (\n            keyword_only_cross_market_builder\n        )\n        causal_module.verify_cross_market_intelligence_report = (\n            lambda report: True\n        )\n\n        repository_root = Path.cwd().resolve()\n        query = (\n            "what is the current direction of solana, "\n            "what evidence supports it"\n        )\n\n        report = build_causal_intelligence_report(\n            repository_root,\n            query,\n        )\n    finally:\n        causal_module.build_cross_market_intelligence_report = (\n            original_builder\n        )\n        causal_module.verify_cross_market_intelligence_report = (\n            original_verifier\n        )\n\n    assert len(calls) == 1\n    assert calls[0]["repository_root"] == repository_root\n    assert calls[0]["query"] == query\n    assert calls[0]["result_limit"] == 10\n\n    assert report.query == query\n    assert report.cross_market_report_hash == (\n        "cross-market-report-hash-defect-test"\n    )\n    assert report.hypothesis_count == 0\n    assert report.causal_state == "no_causal_evidence"\n    assert report.read_only\n    assert not report.analytics_execution_performed\n    assert not report.database_access_performed\n    assert not report.publication_allowed\n    assert not report.qseries_execution_allowed\n    assert verify_causal_intelligence_report(report)\n\n    replay_calls: list[dict[str, object]] = []\n\n    def replay_builder(\n        *,\n        repository_root: Path,\n        query: str,\n        result_limit: int = 10,\n    ):\n        replay_calls.append(\n            {\n                "repository_root": repository_root,\n                "query": query,\n                "result_limit": result_limit,\n            }\n        )\n        return SimpleNamespace(\n            relationships=(),\n            report_hash="cross-market-report-hash-defect-test",\n        )\n\n    try:\n        causal_module.build_cross_market_intelligence_report = (\n            replay_builder\n        )\n        causal_module.verify_cross_market_intelligence_report = (\n            lambda report: True\n        )\n        replay = build_causal_intelligence_report(\n            repository_root,\n            query,\n        )\n    finally:\n        causal_module.build_cross_market_intelligence_report = (\n            original_builder\n        )\n        causal_module.verify_cross_market_intelligence_report = (\n            original_verifier\n        )\n\n    assert replay == report\n    assert replay_calls == calls\n\n    print("[PASS] Actual OIT-014 callable signature inspected")\n    print("[PASS] repository_root is keyword-only")\n    print("[PASS] query is keyword-only")\n    print("[PASS] Defective positional invocation removed")\n    print("[PASS] Correct repository_root keyword binding verified")\n    print("[PASS] Correct query keyword binding verified")\n    print("[PASS] Exact Solana terminal question accepted")\n    print("[PASS] Causal fallback completed without TypeError")\n    print("[PASS] Empty bounded cross-market result handled safely")\n    print("[PASS] Causal report deterministic across replay")\n    print("[PASS] Read-only boundary preserved")\n    print("[PASS] Analytics and database execution remained disabled")\n    print("[PASS] Publication and Q Series execution remained disabled")\n    print("[DONE] OIT-050 CROSS-MARKET SIGNATURE REPAIR PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'

DEFECTIVE_CALL = (
    "source = build_cross_market_intelligence_report(root, query)"
)
CORRECT_KEYWORD_ROOT = "repository_root=root"
CORRECT_KEYWORD_QUERY = "query=query"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_contract(
    path: Path,
    tokens: tuple[str, ...],
    label: str,
) -> None:
    if not path.is_file():
        raise RuntimeError(f"{label} missing: {path}")

    source = path.read_text(encoding="utf-8")
    missing = [token for token in tokens if token not in source]
    if missing:
        raise RuntimeError(
            f"{label} contract mismatch: {missing}"
        )


def write_complete(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        source.lstrip(),
        encoding="utf-8",
        newline="\n",
    )
    ast.parse(
        path.read_text(encoding="utf-8"),
        filename=str(path),
    )
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def capture_protected_sources() -> dict[Path, str]:
    protected: dict[Path, str] = {}

    for path in (ROOT / "qseries_v2").rglob("*.py"):
        if path.is_file() and path.resolve() != TARGET.resolve():
            protected[path.resolve()] = sha256(path)

    for path in (
        RUNNER,
        OIT_050_TEST,
    ):
        if path.is_file():
            protected[path.resolve()] = sha256(path)

    return protected


def main() -> int:
    print("=" * 56)
    print(" OIT-050 CORRECTION V2 INSTALLER")
    print(" LIVE CROSS-MARKET INVOCATION SIGNATURE REPAIR")
    print("=" * 56)

    try:
        require_contract(
            UPSTREAM,
            (
                'SCHEMA_VERSION = "OIT-014"',
                'POLICY_ID = "oracle.cross-market-intelligence-relationship-analysis.v2"',
                "def build_cross_market_intelligence_report(*,",
                "repository_root:",
                "query:",
                "verify_cross_market_intelligence_report",
            ),
            "Actual OIT-014 keyword-only cross-market contract",
        )

        require_contract(
            TARGET,
            (
                "def build_causal_intelligence_report(",
                "build_cross_market_intelligence_report",
                DEFECTIVE_CALL,
                "verify_cross_market_intelligence_report",
                "publication_allowed",
                "qseries_execution_allowed",
            ),
            "Defective installed causal intelligence module",
        )

        require_contract(
            OIT_050,
            (
                'SCHEMA_VERSION = "OIT-050"',
                'POLICY_ID = "oracle-terminal.final-freeze-and-completion.v1"',
                "correction_builds_allowed_only_for_defects",
                "no_further_oit_feature_layers_required",
            ),
            "Certified OIT-050 final freeze contract",
        )

        require_contract(
            OIT_050_TEST,
            (
                "OIT-050 TEST",
                "FINAL FREEZE AND COMPLETION",
                "Correction builds restricted to genuine defects",
                "OIT-050 FINAL FREEZE AND COMPLETION PASS",
            ),
            "Certified OIT-050 final freeze test",
        )

        protected = capture_protected_sources()
        target_before = sha256(TARGET)

        print("[OK] Actual OIT-014 keyword-only callable verified")
        print("[OK] Exact positional invocation defect located")
        print("[OK] Certified OIT-050 defect-correction permission verified")
        print("[OK] Current frozen repository state accepted")
        print(
            f"[OK] Protected source files captured: "
            f"{len(protected)}"
        )

        pre_freeze = subprocess.run(
            [sys.executable, str(OIT_050_TEST)],
            cwd=ROOT,
            check=False,
        )
        if pre_freeze.returncode:
            raise RuntimeError(
                "Pre-repair OIT-050 certification failed with exit code "
                f"{pre_freeze.returncode}"
            )

        write_complete(TARGET, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        installed = TARGET.read_text(encoding="utf-8")
        if DEFECTIVE_CALL in installed:
            raise RuntimeError(
                "Defective positional invocation remains installed"
            )
        if CORRECT_KEYWORD_ROOT not in installed:
            raise RuntimeError(
                "Correct repository_root keyword binding missing"
            )
        if CORRECT_KEYWORD_QUERY not in installed:
            raise RuntimeError(
                "Correct query keyword binding missing"
            )

        repaired = subprocess.run(
            [sys.executable, str(TEST)],
            cwd=ROOT,
            check=False,
        )
        if repaired.returncode:
            raise RuntimeError(
                "Signature-repair regression test failed with exit code "
                f"{repaired.returncode}"
            )

        post_freeze = subprocess.run(
            [sys.executable, str(OIT_050_TEST)],
            cwd=ROOT,
            check=False,
        )
        if post_freeze.returncode:
            raise RuntimeError(
                "Post-repair OIT-050 certification failed with exit code "
                f"{post_freeze.returncode}"
            )

        if sha256(TARGET) == target_before:
            raise RuntimeError(
                "Target causal module was not replaced"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Protected source changed: {path}"
                )

        print("[PASS] Entire causal intelligence module replaced")
        print("[PASS] Defective positional invocation eliminated")
        print("[PASS] OIT-014 keyword-only signature honored")
        print("[PASS] Exact Solana /ask regression certified")
        print("[PASS] Frozen OIT-050 test passed before repair")
        print("[PASS] Frozen OIT-050 test passed after repair")
        print("[PASS] Live terminal runner unchanged")
        print("[PASS] All non-defect Q Series sources unchanged")
        print("[PASS] Read-only boundary preserved")
        print("[PASS] Publication and Q Series execution remained disabled")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OIT-050 CORRECTION V2 SIGNATURE REPAIR INSTALLED")
        return 0

    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
