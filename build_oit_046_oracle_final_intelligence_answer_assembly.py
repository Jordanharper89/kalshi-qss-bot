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

        package = candidate / "qseries_v2" / "oracle_terminal"

        oit_045 = (
            package
            / "oracle_resolved_follow_up_projection_reentry_gate.py"
        )
        oit_045_test = (
            candidate
            / "test_oit_045_oracle_resolved_follow_up_projection_reentry_gate.py"
        )
        oit_042 = (
            package
            / "oracle_terminal_intelligence_answer_generation.py"
        )

        if (
            oit_045.is_file()
            and oit_045_test.is_file()
            and oit_042.is_file()
        ):
            return candidate

    raise SystemExit(
        "[ERROR] Could not locate current Q Series repository."
    )


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"

OIT_042 = (
    PACKAGE
    / "oracle_terminal_intelligence_answer_generation.py"
)
OIT_045 = (
    PACKAGE
    / "oracle_resolved_follow_up_projection_reentry_gate.py"
)
OIT_045_TEST = (
    ROOT
    / "test_oit_045_oracle_resolved_follow_up_projection_reentry_gate.py"
)

PRODUCTION = (
    PACKAGE
    / "oracle_final_intelligence_answer_assembly.py"
)
TEST = (
    ROOT
    / "test_oit_046_oracle_final_intelligence_answer_assembly.py"
)
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass\nfrom pathlib import Path\nfrom typing import Any, Mapping\n\nfrom .oracle_resolved_follow_up_projection_reentry_gate import (\n    OracleResolvedFollowUpProjectionReentryInvariantError,\n    OracleResolvedFollowUpProjectionReentryReport,\n    verify_resolved_follow_up_projection_reentry_report,\n)\nfrom .oracle_terminal_intelligence_answer_generation import (\n    OracleTerminalIntelligenceAnswer,\n    OracleTerminalIntelligenceAnswerGenerationReport,\n    build_terminal_intelligence_answer_generation_report,\n    verify_terminal_intelligence_answer,\n    verify_terminal_intelligence_answer_generation_report,\n)\n\nSCHEMA_VERSION = "OIT-046"\nENGINE_ID = "OIT-046"\nPOLICY_ID = "oracle.final-intelligence-answer-assembly.v1"\n\n\nclass OracleFinalIntelligenceAnswerAssemblyInvariantError(\n    OracleResolvedFollowUpProjectionReentryInvariantError\n):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleFinalIntelligenceAnswerLineage:\n    source_reentry_report_hash: str\n    source_follow_up_resolution_report_hash: str\n    source_context_assembly_report_hash: str\n    source_projection_report_hash: str\n    source_projection_hash: str\n    source_answer_generation_report_hash: str\n    source_answer_hash: str\n    source_session_context_hash: str\n    primary_reference_turn_index: int | None\n    exact_lineage_verified: bool\n    lineage_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleFinalIntelligenceAnswerPackage:\n    package_id: str\n    query: str\n    resolved_query: str\n    follow_up_detected: bool\n    resolution_confidence: float\n    answer: OracleTerminalIntelligenceAnswer\n    lineage: OracleFinalIntelligenceAnswerLineage\n    answer_line_count: int\n    all_claims_evidence_linked: bool\n    deterministic_assembly: bool\n    bounded_answer: bool\n    terminal_render_ready: bool\n    read_only: bool\n    package_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleFinalIntelligenceAnswerAssemblyReport:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    status: str\n    repository_root: str\n    reentry_report_hash: str\n    answer_generation_report: OracleTerminalIntelligenceAnswerGenerationReport\n    final_answer_package: OracleFinalIntelligenceAnswerPackage\n    final_answer_assembled: bool\n    conversation_rendering_ready: bool\n    unsupported_claims_generated: bool\n    persistent_memory_enabled: bool\n    learning_update_performed: bool\n    analytics_execution_performed: bool\n    database_access_performed: bool\n    runtime_artifact_created: bool\n    runtime_artifact_modified: bool\n    networking_performed: bool\n    publication_allowed: bool\n    action_authorization_allowed: bool\n    qseries_execution_allowed: bool\n    read_only: bool\n    failure_reason: str | None\n    report_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(\n                value.items(),\n                key=lambda pair: str(pair[0]),\n            )\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    raise OracleFinalIntelligenceAnswerAssemblyInvariantError(\n        "unsupported OIT-046 value type: "\n        f"{type(value).__module__}.{type(value).__qualname__}"\n    )\n\n\ndef _stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=True,\n        allow_nan=False,\n    ).encode("utf-8")\n    return hashlib.sha256(payload).hexdigest()\n\n\ndef verify_final_answer_lineage(\n    lineage: OracleFinalIntelligenceAnswerLineage,\n) -> bool:\n    body = asdict(lineage)\n    supplied = body.pop("lineage_hash")\n\n    if _stable_hash(body) != supplied:\n        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(\n            "OIT-046 lineage hash mismatch"\n        )\n\n    required = (\n        lineage.source_reentry_report_hash,\n        lineage.source_follow_up_resolution_report_hash,\n        lineage.source_context_assembly_report_hash,\n        lineage.source_projection_report_hash,\n        lineage.source_projection_hash,\n        lineage.source_answer_generation_report_hash,\n        lineage.source_answer_hash,\n        lineage.source_session_context_hash,\n    )\n    if not all(required):\n        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(\n            "OIT-046 lineage is incomplete"\n        )\n\n    if (\n        lineage.primary_reference_turn_index is not None\n        and lineage.primary_reference_turn_index < 0\n    ):\n        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(\n            "OIT-046 primary turn index invalid"\n        )\n\n    if not lineage.exact_lineage_verified:\n        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(\n            "OIT-046 exact lineage not verified"\n        )\n\n    return True\n\n\ndef verify_final_answer_package(\n    package: OracleFinalIntelligenceAnswerPackage,\n) -> bool:\n    body = asdict(package)\n    supplied = body.pop("package_hash")\n\n    if _stable_hash(body) != supplied:\n        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(\n            "OIT-046 final answer package hash mismatch"\n        )\n\n    if not package.package_id:\n        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(\n            "OIT-046 package ID missing"\n        )\n\n    if not package.query or not package.resolved_query:\n        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(\n            "OIT-046 query identity missing"\n        )\n\n    if not 0.0 <= package.resolution_confidence <= 1.0:\n        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(\n            "OIT-046 resolution confidence outside bounds"\n        )\n\n    verify_terminal_intelligence_answer(package.answer)\n    verify_final_answer_lineage(package.lineage)\n\n    if package.answer_line_count != package.answer.answer_line_count:\n        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(\n            "OIT-046 answer line count mismatch"\n        )\n\n    if package.all_claims_evidence_linked != (\n        package.answer.all_claims_evidence_linked\n    ):\n        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(\n            "OIT-046 evidence-link state mismatch"\n        )\n\n    if package.bounded_answer != package.answer.bounded_answer:\n        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(\n            "OIT-046 bounded-answer state mismatch"\n        )\n\n    expected_ready = bool(\n        package.answer.answer_ready\n        and package.all_claims_evidence_linked\n        and package.deterministic_assembly\n        and package.bounded_answer\n        and package.lineage.exact_lineage_verified\n        and package.read_only\n    )\n\n    if package.terminal_render_ready != expected_ready:\n        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(\n            "OIT-046 terminal-render readiness mismatch"\n        )\n\n    return True\n\n\ndef build_final_intelligence_answer_assembly_report(\n    repository_root: str | Path,\n    *,\n    reentry_report: OracleResolvedFollowUpProjectionReentryReport,\n) -> OracleFinalIntelligenceAnswerAssemblyReport:\n    root = Path(repository_root).resolve()\n\n    verify_resolved_follow_up_projection_reentry_report(\n        reentry_report\n    )\n\n    if not reentry_report.answer_generation_ready:\n        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(\n            reentry_report.failure_reason\n            or "OIT-045 reentry is not answer-generation ready"\n        )\n\n    answer_report = build_terminal_intelligence_answer_generation_report(\n        root,\n        projection_report=reentry_report.projection_report,\n    )\n    verify_terminal_intelligence_answer_generation_report(\n        answer_report\n    )\n\n    if not answer_report.answer_generated:\n        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(\n            answer_report.failure_reason\n            or "OIT-042 answer generation failed"\n        )\n\n    binding = reentry_report.projection_binding\n    projection = reentry_report.projection_report.projection\n    answer = answer_report.answer\n\n    exact_lineage = bool(\n        reentry_report.report_hash\n        and reentry_report.follow_up_resolution_report_hash\n        == binding.source_follow_up_report_hash\n        and reentry_report.context_assembly_report_hash\n        == binding.source_context_assembly_report_hash\n        and reentry_report.projection_report.report_hash\n        == binding.projection_report_hash\n        and projection.projection_hash\n        == binding.projection_hash\n        and answer_report.projection_report_hash\n        == reentry_report.projection_report.report_hash\n        and answer.source_projection_report_hash\n        == reentry_report.projection_report.report_hash\n        and answer.source_projection_hash\n        == projection.projection_hash\n        and answer.query\n        == projection.query_intent.normalized_query\n        and binding.exact_cross_stage_lineage_verified\n    )\n\n    if not exact_lineage:\n        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(\n            "OIT-046 cross-stage lineage mismatch"\n        )\n\n    lineage_body = {\n        "source_reentry_report_hash": reentry_report.report_hash,\n        "source_follow_up_resolution_report_hash": (\n            binding.source_follow_up_report_hash\n        ),\n        "source_context_assembly_report_hash": (\n            binding.source_context_assembly_report_hash\n        ),\n        "source_projection_report_hash": (\n            reentry_report.projection_report.report_hash\n        ),\n        "source_projection_hash": projection.projection_hash,\n        "source_answer_generation_report_hash": (\n            answer_report.report_hash\n        ),\n        "source_answer_hash": answer.answer_hash,\n        "source_session_context_hash": (\n            binding.source_session_context_hash\n        ),\n        "primary_reference_turn_index": (\n            binding.primary_reference_turn_index\n        ),\n        "exact_lineage_verified": True,\n    }\n    lineage = OracleFinalIntelligenceAnswerLineage(\n        **lineage_body,\n        lineage_hash=_stable_hash(lineage_body),\n    )\n    verify_final_answer_lineage(lineage)\n\n    query = reentry_report.projection_report.projection.query_intent.raw_query\n\n    package_body = {\n        "package_id": _stable_hash(\n            {\n                "reentry_report_hash": reentry_report.report_hash,\n                "answer_report_hash": answer_report.report_hash,\n                "answer_hash": answer.answer_hash,\n            }\n        )[:24],\n        "query": query,\n        "resolved_query": binding.resolved_query,\n        "follow_up_detected": binding.follow_up_detected,\n        "resolution_confidence": binding.resolution_confidence,\n        "answer": answer,\n        "lineage": lineage,\n        "answer_line_count": answer.answer_line_count,\n        "all_claims_evidence_linked": (\n            answer.all_claims_evidence_linked\n        ),\n        "deterministic_assembly": True,\n        "bounded_answer": answer.bounded_answer,\n        "terminal_render_ready": bool(\n            answer.answer_ready\n            and answer.all_claims_evidence_linked\n            and answer.bounded_answer\n            and exact_lineage\n        ),\n        "read_only": True,\n    }\n    package = OracleFinalIntelligenceAnswerPackage(\n        **package_body,\n        package_hash=_stable_hash(package_body),\n    )\n    verify_final_answer_package(package)\n\n    report_body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root),\n        "reentry_report_hash": reentry_report.report_hash,\n        "answer_generation_report": answer_report,\n        "final_answer_package": package,\n        "final_answer_assembled": package.terminal_render_ready,\n        "conversation_rendering_ready": package.terminal_render_ready,\n        "unsupported_claims_generated": False,\n        "persistent_memory_enabled": False,\n        "learning_update_performed": False,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "runtime_artifact_created": False,\n        "runtime_artifact_modified": False,\n        "networking_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "read_only": True,\n        "failure_reason": (\n            None\n            if package.terminal_render_ready\n            else "OIT-046 final answer assembly failed"\n        ),\n    }\n    report = OracleFinalIntelligenceAnswerAssemblyReport(\n        **report_body,\n        report_hash=_stable_hash(report_body),\n    )\n    verify_final_intelligence_answer_assembly_report(report)\n    return report\n\n\ndef verify_final_intelligence_answer_assembly_report(\n    report: OracleFinalIntelligenceAnswerAssemblyReport,\n) -> bool:\n    body = asdict(report)\n    supplied = body.pop("report_hash")\n\n    if _stable_hash(body) != supplied:\n        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(\n            "OIT-046 report hash mismatch"\n        )\n\n    if report.schema_version != SCHEMA_VERSION:\n        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(\n            "OIT-046 schema mismatch"\n        )\n\n    if report.policy_id != POLICY_ID:\n        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(\n            "OIT-046 policy mismatch"\n        )\n\n    verify_terminal_intelligence_answer_generation_report(\n        report.answer_generation_report\n    )\n    verify_final_answer_package(\n        report.final_answer_package\n    )\n\n    if not report.read_only:\n        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(\n            "OIT-046 report is not read-only"\n        )\n\n    if (\n        report.unsupported_claims_generated\n        or report.persistent_memory_enabled\n        or report.learning_update_performed\n        or report.analytics_execution_performed\n        or report.database_access_performed\n        or report.runtime_artifact_created\n        or report.runtime_artifact_modified\n        or report.networking_performed\n        or report.publication_allowed\n        or report.action_authorization_allowed\n        or report.qseries_execution_allowed\n    ):\n        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(\n            "forbidden OIT-046 capability enabled"\n        )\n\n    if report.reentry_report_hash != (\n        report.final_answer_package.lineage.source_reentry_report_hash\n    ):\n        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(\n            "OIT-046 reentry lineage mismatch"\n        )\n\n    if report.answer_generation_report.report_hash != (\n        report.final_answer_package.lineage\n        .source_answer_generation_report_hash\n    ):\n        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(\n            "OIT-046 answer-generation lineage mismatch"\n        )\n\n    if report.answer_generation_report.answer.answer_hash != (\n        report.final_answer_package.answer.answer_hash\n    ):\n        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(\n            "OIT-046 answer identity mismatch"\n        )\n\n    expected = bool(\n        report.final_answer_package.terminal_render_ready\n        and report.final_answer_package.lineage.exact_lineage_verified\n        and report.final_answer_package.answer.answer_ready\n    )\n\n    if report.final_answer_assembled != expected:\n        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(\n            "OIT-046 final-answer state mismatch"\n        )\n\n    if report.conversation_rendering_ready != expected:\n        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(\n            "OIT-046 rendering readiness mismatch"\n        )\n\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import replace\nfrom pathlib import Path\nfrom tempfile import TemporaryDirectory\n\nfrom qseries_v2.oracle_terminal.oracle_natural_language_intelligence_response_projection import (\n    ENGINE_ID as OIT_041_ENGINE_ID,\n    POLICY_ID as OIT_041_POLICY_ID,\n    SCHEMA_VERSION as OIT_041_SCHEMA_VERSION,\n    OracleIntelligenceQueryIntent,\n    OracleNaturalLanguageIntelligenceProjection,\n    OracleNaturalLanguageIntelligenceProjectionReport,\n    OracleProjectedIntelligenceField,\n    _stable_hash as oit_041_hash,\n)\nfrom qseries_v2.oracle_terminal.oracle_resolved_follow_up_projection_reentry_gate import (\n    ENGINE_ID as OIT_045_ENGINE_ID,\n    POLICY_ID as OIT_045_POLICY_ID,\n    SCHEMA_VERSION as OIT_045_SCHEMA_VERSION,\n    OracleResolvedFollowUpProjectionBinding,\n    OracleResolvedFollowUpProjectionReentryReport,\n    _stable_hash as oit_045_hash,\n    verify_resolved_follow_up_projection_reentry_report,\n)\nfrom qseries_v2.oracle_terminal.oracle_final_intelligence_answer_assembly import (\n    OracleFinalIntelligenceAnswerAssemblyInvariantError,\n    build_final_intelligence_answer_assembly_report,\n    verify_final_intelligence_answer_assembly_report,\n)\n\n\ndef projected_field(\n    key: str,\n    path: str,\n    field_type: str,\n    value,\n    text: str,\n    terms: tuple[str, ...],\n    score: int,\n    reason: str,\n    ordinal: int,\n):\n    body = {\n        "context_key": key,\n        "source_field_path": path,\n        "source_context_field_hash": f"context-field-{ordinal}",\n        "field_type": field_type,\n        "canonical_value": value,\n        "searchable_text": text,\n        "match_terms": terms,\n        "match_score": score,\n        "selection_reason": reason,\n        "projection_ordinal": ordinal,\n    }\n    return OracleProjectedIntelligenceField(\n        **body,\n        projected_field_hash=oit_041_hash(body),\n    )\n\n\ndef make_reentry_report(root: Path):\n    resolved_query = (\n        "Has it changed now? "\n        "[context from prior query: "\n        "What evidence supports the bull direction?]"\n    )\n\n    intent_body = {\n        "raw_query": resolved_query,\n        "normalized_query": resolved_query,\n        "query_terms": (\n            "has",\n            "it",\n            "changed",\n            "now",\n            "context",\n            "from",\n            "prior",\n            "query",\n            "what",\n            "evidence",\n            "supports",\n            "the",\n            "bull",\n            "direction",\n        ),\n        "distinctive_terms": (\n            "has",\n            "changed",\n            "now",\n            "context",\n            "prior",\n            "query",\n            "evidence",\n            "supports",\n            "bull",\n            "direction",\n        ),\n        "requested_field_names": ("direction",),\n        "broad_context_requested": False,\n        "evidence_requested": True,\n        "query_valid": True,\n    }\n    intent = OracleIntelligenceQueryIntent(\n        **intent_body,\n        intent_hash=oit_041_hash(intent_body),\n    )\n\n    fields = (\n        projected_field(\n            "direction",\n            "$.direction",\n            "string",\n            "bull",\n            "bull",\n            ("bull", "direction"),\n            120,\n            "exact_field_request",\n            0,\n        ),\n        projected_field(\n            "evidence.0.source_id",\n            "$.evidence[0].source_id",\n            "string",\n            "SOURCE-046",\n            "SOURCE-046",\n            ("evidence",),\n            35,\n            "distinctive_term_match+evidence_request",\n            1,\n        ),\n        projected_field(\n            "evidence.0.confidence",\n            "$.evidence[0].confidence",\n            "number",\n            0.87,\n            "0.87",\n            ("evidence",),\n            35,\n            "distinctive_term_match+evidence_request",\n            2,\n        ),\n        projected_field(\n            "probability",\n            "$.probability",\n            "number",\n            0.80,\n            "0.80",\n            (),\n            1,\n            "root_context",\n            3,\n        ),\n    )\n\n    projection_body = {\n        "projection_id": "projection-046",\n        "source_context_hash": "intelligence-context-046",\n        "source_context_report_hash": "context-report-046",\n        "query_intent": intent,\n        "projected_fields": fields,\n        "projected_field_count": len(fields),\n        "evidence_field_count": 2,\n        "exact_field_match_count": 1,\n        "term_match_count": 3,\n        "bounded_projection": True,\n        "source_lineage_preserved": True,\n        "deterministic_ordering_applied": True,\n        "projection_ready": True,\n        "read_only": True,\n    }\n    projection = OracleNaturalLanguageIntelligenceProjection(\n        **projection_body,\n        projection_hash=oit_041_hash(projection_body),\n    )\n\n    projection_report_body = {\n        "schema_version": OIT_041_SCHEMA_VERSION,\n        "engine_id": OIT_041_ENGINE_ID,\n        "policy_id": OIT_041_POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root.resolve()),\n        "context_assembly_report_hash": "context-report-046",\n        "projection": projection,\n        "query_accepted": True,\n        "relevant_context_found": True,\n        "answer_generation_ready": True,\n        "free_form_answer_generated": False,\n        "multi_turn_memory_enabled": False,\n        "persistent_memory_enabled": False,\n        "learning_update_performed": False,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "runtime_artifact_created": False,\n        "runtime_artifact_modified": False,\n        "networking_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "read_only": True,\n        "failure_reason": None,\n    }\n    projection_report = OracleNaturalLanguageIntelligenceProjectionReport(\n        **projection_report_body,\n        report_hash=oit_041_hash(projection_report_body),\n    )\n\n    binding_body = {\n        "source_follow_up_report_hash": "follow-up-report-046",\n        "source_context_assembly_report_hash": "context-report-046",\n        "source_session_context_hash": "volatile-session-context-046",\n        "resolved_query": resolved_query,\n        "normalized_query": "Has it changed now?",\n        "follow_up_detected": True,\n        "primary_reference_turn_index": 1,\n        "resolution_confidence": 0.70,\n        "projection_report_hash": projection_report.report_hash,\n        "projection_hash": projection.projection_hash,\n        "projected_field_count": len(fields),\n        "relevant_context_found": True,\n        "exact_cross_stage_lineage_verified": True,\n        "read_only": True,\n    }\n    binding = OracleResolvedFollowUpProjectionBinding(\n        **binding_body,\n        binding_hash=oit_045_hash(binding_body),\n    )\n\n    reentry_body = {\n        "schema_version": OIT_045_SCHEMA_VERSION,\n        "engine_id": OIT_045_ENGINE_ID,\n        "policy_id": OIT_045_POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root.resolve()),\n        "follow_up_resolution_report_hash": "follow-up-report-046",\n        "context_assembly_report_hash": "context-report-046",\n        "projection_report": projection_report,\n        "projection_binding": binding,\n        "reentry_performed": True,\n        "answer_generation_ready": True,\n        "persistent_memory_enabled": False,\n        "learning_update_performed": False,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "runtime_artifact_created": False,\n        "runtime_artifact_modified": False,\n        "networking_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "read_only": True,\n        "failure_reason": None,\n    }\n    reentry = OracleResolvedFollowUpProjectionReentryReport(\n        **reentry_body,\n        report_hash=oit_045_hash(reentry_body),\n    )\n    verify_resolved_follow_up_projection_reentry_report(reentry)\n    return reentry\n\n\ndef main() -> int:\n    print("=" * 48)\n    print(" OIT-046 TEST")\n    print(" FINAL INTELLIGENCE ANSWER ASSEMBLY")\n    print("=" * 48)\n\n    with TemporaryDirectory() as temporary:\n        root = Path(temporary)\n        reentry = make_reentry_report(root)\n\n        report = build_final_intelligence_answer_assembly_report(\n            root,\n            reentry_report=reentry,\n        )\n\n        assert report.final_answer_assembled\n        assert report.conversation_rendering_ready\n        assert not report.unsupported_claims_generated\n\n        package = report.final_answer_package\n        assert package.terminal_render_ready\n        assert package.deterministic_assembly\n        assert package.bounded_answer\n        assert package.all_claims_evidence_linked\n        assert package.follow_up_detected\n        assert package.resolution_confidence == 0.70\n        assert package.lineage.exact_lineage_verified\n        assert (\n            package.lineage.source_reentry_report_hash\n            == reentry.report_hash\n        )\n        assert (\n            package.lineage.source_follow_up_resolution_report_hash\n            == reentry.follow_up_resolution_report_hash\n        )\n        assert (\n            package.lineage.source_context_assembly_report_hash\n            == reentry.context_assembly_report_hash\n        )\n        assert (\n            package.lineage.source_projection_report_hash\n            == reentry.projection_report.report_hash\n        )\n        assert (\n            package.lineage.source_projection_hash\n            == reentry.projection_report.projection.projection_hash\n        )\n        assert (\n            package.lineage.source_answer_generation_report_hash\n            == report.answer_generation_report.report_hash\n        )\n        assert (\n            package.lineage.source_answer_hash\n            == package.answer.answer_hash\n        )\n        assert (\n            package.lineage.source_session_context_hash\n            == reentry.projection_binding.source_session_context_hash\n        )\n        assert package.lineage.primary_reference_turn_index == 1\n\n        assert package.answer_line_count == (\n            package.answer.answer_line_count\n        )\n        assert package.answer_line_count == 6\n        assert package.answer.summary_line_count == 1\n        assert package.answer.evidence_line_count == 2\n        assert package.answer.uncertainty_line_count == 1\n\n        replay = build_final_intelligence_answer_assembly_report(\n            root,\n            reentry_report=reentry,\n        )\n        assert replay == report\n        assert verify_final_intelligence_answer_assembly_report(\n            report\n        )\n\n        tampered = replace(\n            report,\n            persistent_memory_enabled=True,\n        )\n        try:\n            verify_final_intelligence_answer_assembly_report(\n                tampered\n            )\n        except OracleFinalIntelligenceAnswerAssemblyInvariantError:\n            pass\n        else:\n            raise AssertionError(\n                "tampered OIT-046 report accepted"\n            )\n\n        assert not report.learning_update_performed\n        assert not report.analytics_execution_performed\n        assert not report.database_access_performed\n        assert not report.runtime_artifact_created\n        assert not report.runtime_artifact_modified\n        assert not report.networking_performed\n        assert not report.publication_allowed\n        assert not report.action_authorization_allowed\n        assert not report.qseries_execution_allowed\n        assert report.read_only\n\n    print("[PASS] Certified OIT-045 reentry report consumed")\n    print("[PASS] Certified OIT-042 answer generator invoked")\n    print("[PASS] Final evidence-linked answer assembled")\n    print("[PASS] Follow-up and resolution metadata preserved")\n    print("[PASS] OIT-043 volatile-session lineage preserved")\n    print("[PASS] OIT-040 intelligence-context lineage preserved")\n    print("[PASS] OIT-041 projection lineage preserved")\n    print("[PASS] OIT-042 answer lineage preserved")\n    print("[PASS] Exact cross-stage hashes verified")\n    print("[PASS] Conversation-rendering readiness certified")\n    print("[PASS] Assembly deterministic across replay")\n    print("[PASS] Tampered assembly report rejected")\n    print("[PASS] Persistent memory and learning remained disabled")\n    print("[PASS] No analytics execution or runtime mutation performed")\n    print("[PASS] Publication, action authorization, and Q Series execution disabled")\n    print("[DONE] OIT-046 FINAL INTELLIGENCE ANSWER ASSEMBLY PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


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
    missing = [
        token
        for token in tokens
        if token not in source
    ]

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
        OIT_042,
        OIT_045,
        OIT_045_TEST,
        RUNNER,
    ):
        if path.is_file():
            protected[path] = sha256(path)

    return protected


def main() -> int:
    print("=" * 48)
    print(" OIT-046 INSTALLER")
    print(" FINAL INTELLIGENCE ANSWER ASSEMBLY")
    print("=" * 48)

    try:
        require_contract(
            OIT_042,
            (
                'SCHEMA_VERSION = "OIT-042"',
                'POLICY_ID = "oracle.terminal-intelligence-answer-generation.v1"',
                "OracleTerminalIntelligenceAnswer",
                "OracleTerminalIntelligenceAnswerGenerationReport",
                "build_terminal_intelligence_answer_generation_report",
                "verify_terminal_intelligence_answer",
                "verify_terminal_intelligence_answer_generation_report",
                "answer_generated",
                "unsupported_claims_generated",
            ),
            "Certified OIT-042 production",
        )

        require_contract(
            OIT_045,
            (
                'SCHEMA_VERSION = "OIT-045"',
                'POLICY_ID = "oracle.resolved-follow-up-projection-reentry.v1"',
                "OracleResolvedFollowUpProjectionBinding",
                "OracleResolvedFollowUpProjectionReentryReport",
                "verify_resolved_follow_up_projection_reentry_report",
                "answer_generation_ready",
                "source_session_context_hash",
                "exact_cross_stage_lineage_verified",
            ),
            "Certified OIT-045 production",
        )

        require_contract(
            OIT_045_TEST,
            (
                "OIT-045 TEST",
                "RESOLVED FOLLOW-UP PROJECTION REENTRY GATE",
                "Certified OIT-044 resolved follow-up consumed",
                "OIT-045 RESOLVED FOLLOW-UP PROJECTION REENTRY PASS",
            ),
            "Certified OIT-045 standalone test",
        )

        protected = protected_sources()

        print("[OK] Certified OIT-042 production contract verified")
        print("[OK] Certified OIT-045 production contract verified")
        print("[OK] Certified OIT-045 standalone test verified")
        print(
            f"[OK] Protected production source files captured: "
            f"{len(protected)}"
        )

        upstream = subprocess.run(
            [sys.executable, str(OIT_045_TEST)],
            cwd=ROOT,
            check=False,
        )

        if upstream.returncode:
            raise RuntimeError(
                "OIT-045 certification failed with exit code "
                f"{upstream.returncode}"
            )

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_final_intelligence_answer_assembly import *"
        )

        current = (
            INIT.read_text(encoding="utf-8")
            if INIT.exists()
            else ""
        )

        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"

            current += export + "\n"

            INIT.write_text(
                current,
                encoding="utf-8",
                newline="\n",
            )
            print(
                f"[OK] PACKAGE UPDATED: {INIT.resolve()}"
            )
        else:
            print(
                f"[OK] PACKAGE EXPORT PRESENT: {INIT.resolve()}"
            )

        ast.parse(
            INIT.read_text(encoding="utf-8"),
            filename=str(INIT),
        )

        completed = subprocess.run(
            [sys.executable, str(TEST)],
            cwd=ROOT,
            check=False,
        )

        if completed.returncode:
            raise RuntimeError(
                "OIT-046 test failed with exit code "
                f"{completed.returncode}"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Protected production source changed: {path}"
                )

        print("[PASS] Certified OIT-042 production unchanged")
        print("[PASS] Certified OIT-045 production and test unchanged")
        print("[PASS] Oracle terminal runner unchanged")
        print("[PASS] OIT-046 production module installed")
        print("[PASS] OIT-046 standalone test installed")
        print("[PASS] Final evidence-linked answer assembly certified")
        print("[PASS] Complete OIT-040 through OIT-045 lineage retained")
        print("[PASS] Conversation-rendering readiness certified")
        print("[PASS] Persistent memory and learning remained disabled")
        print("[PASS] No analytics execution or runtime mutation performed")
        print("[PASS] OLA, OIA, INT-OII, ORR, OOR, and Q Series unchanged")
        print("[PASS] Publication and execution remained disabled")
        print("[PASS] Read-only and execution boundaries preserved")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OIT-046 FINAL INTELLIGENCE ANSWER ASSEMBLY INSTALLED")
        return 0

    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
