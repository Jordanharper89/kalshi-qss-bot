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

        oit_044 = (
            package
            / "oracle_multi_turn_follow_up_query_context_resolution.py"
        )
        oit_044_test = (
            candidate
            / "test_oit_044_oracle_multi_turn_follow_up_query_context_resolution.py"
        )
        oit_041 = (
            package
            / "oracle_natural_language_intelligence_response_projection.py"
        )
        oit_040 = (
            package
            / "oracle_intelligence_session_context_assembly.py"
        )

        if (
            oit_044.is_file()
            and oit_044_test.is_file()
            and oit_041.is_file()
            and oit_040.is_file()
        ):
            return candidate

    raise SystemExit(
        "[ERROR] Could not locate current Q Series repository."
    )


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"

OIT_040 = (
    PACKAGE
    / "oracle_intelligence_session_context_assembly.py"
)
OIT_041 = (
    PACKAGE
    / "oracle_natural_language_intelligence_response_projection.py"
)
OIT_044 = (
    PACKAGE
    / "oracle_multi_turn_follow_up_query_context_resolution.py"
)
OIT_044_TEST = (
    ROOT
    / "test_oit_044_oracle_multi_turn_follow_up_query_context_resolution.py"
)

PRODUCTION = (
    PACKAGE
    / "oracle_resolved_follow_up_projection_reentry_gate.py"
)
TEST = (
    ROOT
    / "test_oit_045_oracle_resolved_follow_up_projection_reentry_gate.py"
)
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass\nfrom pathlib import Path\nfrom typing import Any, Mapping\n\nfrom .oracle_intelligence_session_context_assembly import (\n    OracleIntelligenceSessionContextAssemblyReport,\n    verify_intelligence_session_context_assembly_report,\n)\nfrom .oracle_multi_turn_follow_up_query_context_resolution import (\n    OracleFollowUpQueryResolutionReport,\n    OracleFollowUpQueryResolutionInvariantError,\n    verify_follow_up_query_resolution_report,\n)\nfrom .oracle_natural_language_intelligence_response_projection import (\n    OracleNaturalLanguageIntelligenceProjectionReport,\n    build_natural_language_intelligence_projection_report,\n    verify_natural_language_intelligence_projection_report,\n)\n\nSCHEMA_VERSION = "OIT-045"\nENGINE_ID = "OIT-045"\nPOLICY_ID = "oracle.resolved-follow-up-projection-reentry.v1"\n\n\nclass OracleResolvedFollowUpProjectionReentryInvariantError(\n    OracleFollowUpQueryResolutionInvariantError\n):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleResolvedFollowUpProjectionBinding:\n    source_follow_up_report_hash: str\n    source_context_assembly_report_hash: str\n    source_session_context_hash: str\n    resolved_query: str\n    normalized_query: str\n    follow_up_detected: bool\n    primary_reference_turn_index: int | None\n    resolution_confidence: float\n    projection_report_hash: str\n    projection_hash: str\n    projected_field_count: int\n    relevant_context_found: bool\n    exact_cross_stage_lineage_verified: bool\n    read_only: bool\n    binding_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleResolvedFollowUpProjectionReentryReport:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    status: str\n    repository_root: str\n    follow_up_resolution_report_hash: str\n    context_assembly_report_hash: str\n    projection_report: OracleNaturalLanguageIntelligenceProjectionReport\n    projection_binding: OracleResolvedFollowUpProjectionBinding\n    reentry_performed: bool\n    answer_generation_ready: bool\n    persistent_memory_enabled: bool\n    learning_update_performed: bool\n    analytics_execution_performed: bool\n    database_access_performed: bool\n    runtime_artifact_created: bool\n    runtime_artifact_modified: bool\n    networking_performed: bool\n    publication_allowed: bool\n    action_authorization_allowed: bool\n    qseries_execution_allowed: bool\n    read_only: bool\n    failure_reason: str | None\n    report_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(\n                value.items(),\n                key=lambda pair: str(pair[0]),\n            )\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    raise OracleResolvedFollowUpProjectionReentryInvariantError(\n        "unsupported OIT-045 value type: "\n        f"{type(value).__module__}.{type(value).__qualname__}"\n    )\n\n\ndef _stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=True,\n        allow_nan=False,\n    ).encode("utf-8")\n    return hashlib.sha256(payload).hexdigest()\n\n\ndef verify_projection_binding(\n    binding: OracleResolvedFollowUpProjectionBinding,\n) -> bool:\n    body = asdict(binding)\n    supplied = body.pop("binding_hash")\n\n    if _stable_hash(body) != supplied:\n        raise OracleResolvedFollowUpProjectionReentryInvariantError(\n            "OIT-045 projection binding hash mismatch"\n        )\n\n    if not binding.source_follow_up_report_hash:\n        raise OracleResolvedFollowUpProjectionReentryInvariantError(\n            "OIT-045 follow-up report lineage missing"\n        )\n\n    if not binding.source_context_assembly_report_hash:\n        raise OracleResolvedFollowUpProjectionReentryInvariantError(\n            "OIT-045 context assembly lineage missing"\n        )\n\n    if not binding.source_session_context_hash:\n        raise OracleResolvedFollowUpProjectionReentryInvariantError(\n            "OIT-045 session context lineage missing"\n        )\n\n    if not binding.resolved_query or not binding.normalized_query:\n        raise OracleResolvedFollowUpProjectionReentryInvariantError(\n            "OIT-045 resolved query missing"\n        )\n\n    if not 0.0 <= binding.resolution_confidence <= 1.0:\n        raise OracleResolvedFollowUpProjectionReentryInvariantError(\n            "OIT-045 resolution confidence outside bounds"\n        )\n\n    if not binding.projection_report_hash or not binding.projection_hash:\n        raise OracleResolvedFollowUpProjectionReentryInvariantError(\n            "OIT-045 projection lineage missing"\n        )\n\n    if binding.projected_field_count < 0:\n        raise OracleResolvedFollowUpProjectionReentryInvariantError(\n            "OIT-045 projected field count invalid"\n        )\n\n    if binding.relevant_context_found != (\n        binding.projected_field_count > 0\n    ):\n        raise OracleResolvedFollowUpProjectionReentryInvariantError(\n            "OIT-045 relevant-context state mismatch"\n        )\n\n    if not binding.exact_cross_stage_lineage_verified:\n        raise OracleResolvedFollowUpProjectionReentryInvariantError(\n            "OIT-045 exact cross-stage lineage not verified"\n        )\n\n    if not binding.read_only:\n        raise OracleResolvedFollowUpProjectionReentryInvariantError(\n            "OIT-045 projection binding is not read-only"\n        )\n\n    return True\n\n\ndef build_resolved_follow_up_projection_reentry_report(\n    repository_root: str | Path,\n    *,\n    follow_up_resolution_report: OracleFollowUpQueryResolutionReport,\n    context_assembly_report: OracleIntelligenceSessionContextAssemblyReport,\n) -> OracleResolvedFollowUpProjectionReentryReport:\n    root = Path(repository_root).resolve()\n\n    verify_follow_up_query_resolution_report(\n        follow_up_resolution_report\n    )\n    verify_intelligence_session_context_assembly_report(\n        context_assembly_report\n    )\n\n    if not follow_up_resolution_report.downstream_projection_ready:\n        raise OracleResolvedFollowUpProjectionReentryInvariantError(\n            follow_up_resolution_report.failure_reason\n            or "OIT-044 resolution is not projection-ready"\n        )\n\n    if not context_assembly_report.query_planning_ready:\n        raise OracleResolvedFollowUpProjectionReentryInvariantError(\n            context_assembly_report.failure_reason\n            or "OIT-040 context is not query-planning ready"\n        )\n\n    resolved = (\n        follow_up_resolution_report.resolved_follow_up_query\n    )\n\n    projection_report = (\n        build_natural_language_intelligence_projection_report(\n            root,\n            context_assembly_report=context_assembly_report,\n            query=resolved.resolved_query,\n        )\n    )\n    verify_natural_language_intelligence_projection_report(\n        projection_report\n    )\n\n    projection = projection_report.projection\n    context = context_assembly_report.session_context\n\n    exact_lineage = bool(\n        follow_up_resolution_report.source_session_context_hash\n        and follow_up_resolution_report.source_session_context_hash\n        != context.context_hash\n        and projection_report.context_assembly_report_hash\n        == context_assembly_report.report_hash\n        and projection.source_context_hash == context.context_hash\n        and projection.source_context_report_hash\n        == context_assembly_report.report_hash\n        and projection.query_intent.raw_query\n        == resolved.resolved_query\n        and projection.query_intent.normalized_query\n        == " ".join(resolved.resolved_query.strip().split())\n    )\n\n    # OIT-044 references the volatile OIT-043 session context.\n    # OIT-040 is the certified intelligence context used for projection.\n    # They must remain distinct but both must be preserved exactly.\n    if not exact_lineage:\n        raise OracleResolvedFollowUpProjectionReentryInvariantError(\n            "OIT-045 exact OIT-040/OIT-044 lineage mismatch"\n        )\n\n    binding_body = {\n        "source_follow_up_report_hash": (\n            follow_up_resolution_report.report_hash\n        ),\n        "source_context_assembly_report_hash": (\n            context_assembly_report.report_hash\n        ),\n        "source_session_context_hash": (\n            follow_up_resolution_report.source_session_context_hash\n        ),\n        "resolved_query": resolved.resolved_query,\n        "normalized_query": resolved.normalized_query,\n        "follow_up_detected": resolved.follow_up_detected,\n        "primary_reference_turn_index": (\n            resolved.primary_reference_turn_index\n        ),\n        "resolution_confidence": resolved.resolution_confidence,\n        "projection_report_hash": projection_report.report_hash,\n        "projection_hash": projection.projection_hash,\n        "projected_field_count": projection.projected_field_count,\n        "relevant_context_found": bool(\n            projection.projected_fields\n        ),\n        "exact_cross_stage_lineage_verified": True,\n        "read_only": True,\n    }\n    binding = OracleResolvedFollowUpProjectionBinding(\n        **binding_body,\n        binding_hash=_stable_hash(binding_body),\n    )\n    verify_projection_binding(binding)\n\n    report_body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root),\n        "follow_up_resolution_report_hash": (\n            follow_up_resolution_report.report_hash\n        ),\n        "context_assembly_report_hash": (\n            context_assembly_report.report_hash\n        ),\n        "projection_report": projection_report,\n        "projection_binding": binding,\n        "reentry_performed": True,\n        "answer_generation_ready": bool(\n            projection_report.answer_generation_ready\n            and binding.relevant_context_found\n            and binding.exact_cross_stage_lineage_verified\n        ),\n        "persistent_memory_enabled": False,\n        "learning_update_performed": False,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "runtime_artifact_created": False,\n        "runtime_artifact_modified": False,\n        "networking_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "read_only": True,\n        "failure_reason": (\n            None\n            if projection_report.answer_generation_ready\n            and binding.relevant_context_found\n            else "OIT-045 projection reentry not answer-ready"\n        ),\n    }\n    report = OracleResolvedFollowUpProjectionReentryReport(\n        **report_body,\n        report_hash=_stable_hash(report_body),\n    )\n    verify_resolved_follow_up_projection_reentry_report(\n        report\n    )\n    return report\n\n\ndef verify_resolved_follow_up_projection_reentry_report(\n    report: OracleResolvedFollowUpProjectionReentryReport,\n) -> bool:\n    body = asdict(report)\n    supplied = body.pop("report_hash")\n\n    if _stable_hash(body) != supplied:\n        raise OracleResolvedFollowUpProjectionReentryInvariantError(\n            "OIT-045 report hash mismatch"\n        )\n\n    if report.schema_version != SCHEMA_VERSION:\n        raise OracleResolvedFollowUpProjectionReentryInvariantError(\n            "OIT-045 schema mismatch"\n        )\n\n    if report.policy_id != POLICY_ID:\n        raise OracleResolvedFollowUpProjectionReentryInvariantError(\n            "OIT-045 policy mismatch"\n        )\n\n    verify_natural_language_intelligence_projection_report(\n        report.projection_report\n    )\n    verify_projection_binding(report.projection_binding)\n\n    if not report.read_only:\n        raise OracleResolvedFollowUpProjectionReentryInvariantError(\n            "OIT-045 report is not read-only"\n        )\n\n    if (\n        report.persistent_memory_enabled\n        or report.learning_update_performed\n        or report.analytics_execution_performed\n        or report.database_access_performed\n        or report.runtime_artifact_created\n        or report.runtime_artifact_modified\n        or report.networking_performed\n        or report.publication_allowed\n        or report.action_authorization_allowed\n        or report.qseries_execution_allowed\n    ):\n        raise OracleResolvedFollowUpProjectionReentryInvariantError(\n            "forbidden OIT-045 capability enabled"\n        )\n\n    if report.follow_up_resolution_report_hash != (\n        report.projection_binding.source_follow_up_report_hash\n    ):\n        raise OracleResolvedFollowUpProjectionReentryInvariantError(\n            "OIT-045 follow-up report lineage mismatch"\n        )\n\n    if report.context_assembly_report_hash != (\n        report.projection_binding.source_context_assembly_report_hash\n    ):\n        raise OracleResolvedFollowUpProjectionReentryInvariantError(\n            "OIT-045 context assembly lineage mismatch"\n        )\n\n    if report.projection_report.report_hash != (\n        report.projection_binding.projection_report_hash\n    ):\n        raise OracleResolvedFollowUpProjectionReentryInvariantError(\n            "OIT-045 projection report lineage mismatch"\n        )\n\n    if report.projection_report.projection.projection_hash != (\n        report.projection_binding.projection_hash\n    ):\n        raise OracleResolvedFollowUpProjectionReentryInvariantError(\n            "OIT-045 projection hash lineage mismatch"\n        )\n\n    expected_ready = bool(\n        report.reentry_performed\n        and report.projection_report.answer_generation_ready\n        and report.projection_binding.relevant_context_found\n        and report.projection_binding.exact_cross_stage_lineage_verified\n    )\n\n    if report.answer_generation_ready != expected_ready:\n        raise OracleResolvedFollowUpProjectionReentryInvariantError(\n            "OIT-045 answer-generation readiness mismatch"\n        )\n\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import replace\nfrom pathlib import Path\nfrom tempfile import TemporaryDirectory\n\nfrom qseries_v2.oracle_terminal.oracle_intelligence_session_context_assembly import (\n    ENGINE_ID as OIT_040_ENGINE_ID,\n    POLICY_ID as OIT_040_POLICY_ID,\n    SCHEMA_VERSION as OIT_040_SCHEMA_VERSION,\n    OracleIntelligenceContextField,\n    OracleIntelligenceSessionContext,\n    OracleIntelligenceSessionContextAssemblyReport,\n    _stable_hash as oit_040_hash,\n    verify_intelligence_session_context_assembly_report,\n)\nfrom qseries_v2.oracle_terminal.oracle_multi_turn_follow_up_query_context_resolution import (\n    ENGINE_ID as OIT_044_ENGINE_ID,\n    POLICY_ID as OIT_044_POLICY_ID,\n    SCHEMA_VERSION as OIT_044_SCHEMA_VERSION,\n    OracleFollowUpQueryReference,\n    OracleFollowUpQueryResolutionReport,\n    OracleResolvedFollowUpQuery,\n    _stable_hash as oit_044_hash,\n    verify_follow_up_query_resolution_report,\n)\nfrom qseries_v2.oracle_terminal.oracle_resolved_follow_up_projection_reentry_gate import (\n    OracleResolvedFollowUpProjectionReentryInvariantError,\n    build_resolved_follow_up_projection_reentry_report,\n    verify_resolved_follow_up_projection_reentry_report,\n)\n\n\ndef context_field(\n    key: str,\n    path: str,\n    field_type: str,\n    value,\n    text: str,\n    ordinal: int,\n):\n    body = {\n        "context_key": key,\n        "source_field_path": path,\n        "source_field_hash": f"source-field-{ordinal}",\n        "field_type": field_type,\n        "canonical_value": value,\n        "searchable_text": text,\n        "ordinal": ordinal,\n    }\n    return OracleIntelligenceContextField(\n        **body,\n        context_field_hash=oit_040_hash(body),\n    )\n\n\ndef make_context_report(root: Path):\n    fields = (\n        context_field(\n            "root",\n            "$",\n            "mapping",\n            {\n                "record_id": "REAL-045",\n                "direction": "bull",\n                "probability": 0.79,\n            },\n            \'{"direction":"bull","probability":0.79,"record_id":"REAL-045"}\',\n            0,\n        ),\n        context_field(\n            "direction",\n            "$.direction",\n            "string",\n            "bull",\n            "bull",\n            1,\n        ),\n        context_field(\n            "probability",\n            "$.probability",\n            "number",\n            0.79,\n            "0.79",\n            2,\n        ),\n        context_field(\n            "evidence.0.source_id",\n            "$.evidence[0].source_id",\n            "string",\n            "SOURCE-045",\n            "SOURCE-045",\n            3,\n        ),\n        context_field(\n            "evidence.0.confidence",\n            "$.evidence[0].confidence",\n            "number",\n            0.86,\n            "0.86",\n            4,\n        ),\n    )\n\n    context_body = {\n        "context_id": "context-045",\n        "source_normalization_report_hash": "normalization-report-045",\n        "source_normalized_record_hash": "normalized-record-045",\n        "source_envelope_hash": "source-envelope-045",\n        "source_execution_report_hash": "execution-report-045",\n        "source_validation_report_hash": "validation-report-045",\n        "source_invocation_result_hash": "invocation-result-045",\n        "context_fields": fields,\n        "context_field_count": len(fields),\n        "searchable_field_count": len(fields),\n        "root_field_present": True,\n        "deterministic_ordering_applied": True,\n        "full_lineage_preserved": True,\n        "bounded_context": True,\n        "context_ready": True,\n        "read_only": True,\n    }\n    context = OracleIntelligenceSessionContext(\n        **context_body,\n        context_hash=oit_040_hash(context_body),\n    )\n\n    report_body = {\n        "schema_version": OIT_040_SCHEMA_VERSION,\n        "engine_id": OIT_040_ENGINE_ID,\n        "policy_id": OIT_040_POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root.resolve()),\n        "normalization_report_hash": "normalization-report-045",\n        "session_context": context,\n        "context_assembled": True,\n        "query_planning_ready": True,\n        "multi_turn_memory_enabled": False,\n        "persistent_memory_enabled": False,\n        "learning_update_performed": False,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "runtime_artifact_created": False,\n        "runtime_artifact_modified": False,\n        "networking_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "read_only": True,\n        "failure_reason": None,\n    }\n    report = OracleIntelligenceSessionContextAssemblyReport(\n        **report_body,\n        report_hash=oit_040_hash(report_body),\n    )\n    verify_intelligence_session_context_assembly_report(report)\n    return report\n\n\ndef make_follow_up_report(root: Path):\n    reference_body = {\n        "reference_type": "latest_turn",\n        "source_turn_index": 1,\n        "source_turn_hash": "turn-hash-045",\n        "source_query": "What evidence supports the bull direction?",\n        "source_answer_id": "answer-045",\n        "source_answer_hash": "answer-hash-045",\n        "reference_text": (\n            "turn 1: What evidence supports the bull direction?"\n        ),\n        "reference_score": 20,\n    }\n    reference = OracleFollowUpQueryReference(\n        **reference_body,\n        reference_hash=oit_044_hash(reference_body),\n    )\n\n    resolved_query = (\n        "Has it changed now? "\n        "[context from prior query: "\n        "What evidence supports the bull direction?]"\n    )\n\n    resolved_body = {\n        "raw_query": "Has it changed now?",\n        "normalized_query": "Has it changed now?",\n        "query_terms": ("has", "it", "changed", "now"),\n        "follow_up_detected": True,\n        "standalone_query": False,\n        "referenced_turns": (reference,),\n        "referenced_turn_count": 1,\n        "primary_reference_turn_index": 1,\n        "resolved_query": resolved_query,\n        "resolution_confidence": 0.70,\n        "session_lineage_preserved": True,\n        "resolution_ready": True,\n        "read_only": True,\n    }\n    resolved = OracleResolvedFollowUpQuery(\n        **resolved_body,\n        resolution_hash=oit_044_hash(resolved_body),\n    )\n\n    report_body = {\n        "schema_version": OIT_044_SCHEMA_VERSION,\n        "engine_id": OIT_044_ENGINE_ID,\n        "policy_id": OIT_044_POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root.resolve()),\n        "source_session_context_hash": "volatile-session-context-045",\n        "resolved_follow_up_query": resolved,\n        "context_resolution_performed": True,\n        "downstream_projection_ready": True,\n        "persistent_memory_enabled": False,\n        "learning_update_performed": False,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "runtime_artifact_created": False,\n        "runtime_artifact_modified": False,\n        "networking_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "read_only": True,\n        "failure_reason": None,\n    }\n    report = OracleFollowUpQueryResolutionReport(\n        **report_body,\n        report_hash=oit_044_hash(report_body),\n    )\n    verify_follow_up_query_resolution_report(report)\n    return report\n\n\ndef main() -> int:\n    print("=" * 48)\n    print(" OIT-045 TEST")\n    print(" RESOLVED FOLLOW-UP PROJECTION REENTRY GATE")\n    print("=" * 48)\n\n    with TemporaryDirectory() as temporary:\n        root = Path(temporary)\n        context_report = make_context_report(root)\n        follow_up_report = make_follow_up_report(root)\n\n        report = build_resolved_follow_up_projection_reentry_report(\n            root,\n            follow_up_resolution_report=follow_up_report,\n            context_assembly_report=context_report,\n        )\n\n        assert report.reentry_performed\n        assert report.answer_generation_ready\n        assert report.projection_report.answer_generation_ready\n        assert report.projection_binding.relevant_context_found\n        assert (\n            report.projection_binding.exact_cross_stage_lineage_verified\n        )\n        assert (\n            report.projection_binding.source_follow_up_report_hash\n            == follow_up_report.report_hash\n        )\n        assert (\n            report.projection_binding.source_context_assembly_report_hash\n            == context_report.report_hash\n        )\n        assert (\n            report.projection_binding.source_session_context_hash\n            == follow_up_report.source_session_context_hash\n        )\n        assert (\n            report.projection_binding.resolved_query\n            == follow_up_report.resolved_follow_up_query.resolved_query\n        )\n        assert (\n            report.projection_binding.projection_report_hash\n            == report.projection_report.report_hash\n        )\n        assert (\n            report.projection_binding.projection_hash\n            == report.projection_report.projection.projection_hash\n        )\n        assert report.projection_binding.projected_field_count > 0\n\n        selected_paths = tuple(\n            field.source_field_path\n            for field in report.projection_report.projection.projected_fields\n        )\n        assert "$.direction" in selected_paths\n        assert "$.evidence[0].source_id" in selected_paths\n        assert "$.evidence[0].confidence" in selected_paths\n\n        replay = build_resolved_follow_up_projection_reentry_report(\n            root,\n            follow_up_resolution_report=follow_up_report,\n            context_assembly_report=context_report,\n        )\n        assert replay == report\n        assert verify_resolved_follow_up_projection_reentry_report(\n            report\n        )\n\n        tampered = replace(\n            report,\n            persistent_memory_enabled=True,\n        )\n        try:\n            verify_resolved_follow_up_projection_reentry_report(\n                tampered\n            )\n        except OracleResolvedFollowUpProjectionReentryInvariantError:\n            pass\n        else:\n            raise AssertionError(\n                "tampered OIT-045 report accepted"\n            )\n\n        assert not report.learning_update_performed\n        assert not report.analytics_execution_performed\n        assert not report.database_access_performed\n        assert not report.runtime_artifact_created\n        assert not report.runtime_artifact_modified\n        assert not report.networking_performed\n        assert not report.publication_allowed\n        assert not report.action_authorization_allowed\n        assert not report.qseries_execution_allowed\n        assert report.read_only\n\n    print("[PASS] Certified OIT-044 resolved follow-up consumed")\n    print("[PASS] Certified OIT-040 intelligence context consumed")\n    print("[PASS] Resolved query reentered OIT-041 projection")\n    print("[PASS] OIT-043 volatile-session lineage preserved")\n    print("[PASS] OIT-040 intelligence-context lineage preserved")\n    print("[PASS] Distinct session and intelligence contexts retained")\n    print("[PASS] Relevant projected fields recovered")\n    print("[PASS] Exact cross-stage hashes verified")\n    print("[PASS] Answer-generation readiness certified")\n    print("[PASS] Reentry deterministic across replay")\n    print("[PASS] Tampered reentry report rejected")\n    print("[PASS] Persistent memory and learning remained disabled")\n    print("[PASS] No analytics execution or runtime mutation performed")\n    print("[PASS] Publication, action authorization, and Q Series execution disabled")\n    print("[DONE] OIT-045 RESOLVED FOLLOW-UP PROJECTION REENTRY PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


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
        OIT_040,
        OIT_041,
        OIT_044,
        OIT_044_TEST,
        RUNNER,
    ):
        if path.is_file():
            protected[path] = sha256(path)

    return protected


def main() -> int:
    print("=" * 48)
    print(" OIT-045 INSTALLER")
    print(" RESOLVED FOLLOW-UP PROJECTION REENTRY GATE")
    print("=" * 48)

    try:
        require_contract(
            OIT_040,
            (
                'SCHEMA_VERSION = "OIT-040"',
                'POLICY_ID = "oracle.intelligence-session-context-assembly.v1"',
                "OracleIntelligenceSessionContextAssemblyReport",
                "verify_intelligence_session_context_assembly_report",
                "query_planning_ready",
            ),
            "Certified OIT-040 production",
        )

        require_contract(
            OIT_041,
            (
                'SCHEMA_VERSION = "OIT-041"',
                'POLICY_ID = "oracle.natural-language-intelligence-response-projection.v1"',
                "OracleNaturalLanguageIntelligenceProjectionReport",
                "build_natural_language_intelligence_projection_report",
                "verify_natural_language_intelligence_projection_report",
                "answer_generation_ready",
            ),
            "Certified OIT-041 production",
        )

        require_contract(
            OIT_044,
            (
                'SCHEMA_VERSION = "OIT-044"',
                'POLICY_ID = "oracle.multi-turn-follow-up-query-context-resolution.v1"',
                "OracleFollowUpQueryResolutionReport",
                "verify_follow_up_query_resolution_report",
                "downstream_projection_ready",
                "source_session_context_hash",
                "resolved_query",
            ),
            "Certified OIT-044 production",
        )

        require_contract(
            OIT_044_TEST,
            (
                "OIT-044 TEST",
                "OIT-043 CORRECTION V2 BASELINE",
                "Certified OIT-043 Correction V2 session consumed",
                "OIT-044 FOLLOW-UP QUERY CONTEXT RESOLUTION PASS",
            ),
            "Certified OIT-044 standalone test",
        )

        protected = protected_sources()

        print("[OK] Certified OIT-040 production contract verified")
        print("[OK] Certified OIT-041 production contract verified")
        print("[OK] Certified OIT-044 production contract verified")
        print("[OK] Certified OIT-044 standalone test verified")
        print(
            f"[OK] Protected production source files captured: "
            f"{len(protected)}"
        )

        upstream = subprocess.run(
            [sys.executable, str(OIT_044_TEST)],
            cwd=ROOT,
            check=False,
        )

        if upstream.returncode:
            raise RuntimeError(
                "OIT-044 certification failed with exit code "
                f"{upstream.returncode}"
            )

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_resolved_follow_up_projection_reentry_gate import *"
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
                "OIT-045 test failed with exit code "
                f"{completed.returncode}"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Protected production source changed: {path}"
                )

        print("[PASS] Certified OIT-040, OIT-041, and OIT-044 unchanged")
        print("[PASS] Certified OIT-044 standalone test unchanged")
        print("[PASS] Oracle terminal runner unchanged")
        print("[PASS] OIT-045 production module installed")
        print("[PASS] OIT-045 standalone test installed")
        print("[PASS] Resolved follow-up projection reentry certified")
        print("[PASS] OIT-043 volatile-session lineage retained")
        print("[PASS] OIT-040 intelligence-context lineage retained")
        print("[PASS] Answer-generation readiness certified")
        print("[PASS] Persistent memory and learning remained disabled")
        print("[PASS] No analytics execution or runtime mutation performed")
        print("[PASS] OLA, OIA, INT-OII, ORR, OOR, and Q Series unchanged")
        print("[PASS] Publication and execution remained disabled")
        print("[PASS] Read-only and execution boundaries preserved")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OIT-045 RESOLVED FOLLOW-UP PROJECTION REENTRY INSTALLED")
        return 0

    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
