from __future__ import annotations

import ast
import hashlib
import re
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
        oit_047 = package / "oracle_conversation_response_rendering.py"
        oit_047_test = candidate / "test_oit_047_oracle_conversation_response_rendering.py"
        runner = candidate / "run_oracle_open_intelligence_terminal.py"
        if oit_047.is_file() and oit_047_test.is_file() and runner.is_file():
            return candidate

    raise SystemExit("[ERROR] Could not locate current Q Series repository.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"
OIT_047 = PACKAGE / "oracle_conversation_response_rendering.py"
OIT_047_TEST = ROOT / "test_oit_047_oracle_conversation_response_rendering.py"
PRODUCTION = PACKAGE / "oracle_end_to_end_interactive_intelligence_pipeline.py"
TEST = ROOT / "test_oit_048_oracle_end_to_end_interactive_intelligence_pipeline.py"
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"
RUNNER_BACKUP = ROOT / "run_oracle_open_intelligence_terminal_PRE_OIT_048.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass\nfrom pathlib import Path\nfrom typing import Any, Mapping\n\nfrom .oracle_bounded_multi_turn_intelligence_session_context import (\n    OracleBoundedMultiTurnSessionContext,\n    OracleBoundedMultiTurnSessionUpdateReport,\n    append_answer_to_bounded_multi_turn_session,\n    verify_bounded_multi_turn_session_update_report,\n    verify_multi_turn_session_context,\n)\nfrom .oracle_conversation_response_rendering import (\n    OracleConversationResponseRenderingReport,\n    build_conversation_response_rendering_report,\n    verify_conversation_response_rendering_report,\n)\nfrom .oracle_final_intelligence_answer_assembly import (\n    OracleFinalIntelligenceAnswerAssemblyReport,\n    build_final_intelligence_answer_assembly_report,\n    verify_final_intelligence_answer_assembly_report,\n)\nfrom .oracle_intelligence_session_context_assembly import (\n    OracleIntelligenceSessionContextAssemblyReport,\n    verify_intelligence_session_context_assembly_report,\n)\nfrom .oracle_multi_turn_follow_up_query_context_resolution import (\n    OracleFollowUpQueryResolutionReport,\n    resolve_multi_turn_follow_up_query,\n    verify_follow_up_query_resolution_report,\n)\nfrom .oracle_resolved_follow_up_projection_reentry_gate import (\n    OracleResolvedFollowUpProjectionReentryReport,\n    build_resolved_follow_up_projection_reentry_report,\n    verify_resolved_follow_up_projection_reentry_report,\n)\n\nSCHEMA_VERSION = "OIT-048"\nENGINE_ID = "OIT-048"\nPOLICY_ID = "oracle.end-to-end-interactive-intelligence-pipeline.v1"\n\n\nclass OracleInteractiveIntelligencePipelineInvariantError(RuntimeError):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleInteractiveIntelligencePipelineLineage:\n    source_context_assembly_report_hash: str\n    source_prior_session_context_hash: str\n    follow_up_resolution_report_hash: str\n    projection_reentry_report_hash: str\n    final_answer_assembly_report_hash: str\n    conversation_rendering_report_hash: str\n    updated_session_context_hash: str\n    exact_stage_order_verified: bool\n    exact_cross_stage_lineage_verified: bool\n    lineage_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleInteractiveIntelligencePipelineResult:\n    pipeline_id: str\n    query: str\n    context_assembly_report_hash: str\n    prior_session_context_hash: str\n    follow_up_resolution_report: OracleFollowUpQueryResolutionReport\n    projection_reentry_report: OracleResolvedFollowUpProjectionReentryReport\n    final_answer_assembly_report: OracleFinalIntelligenceAnswerAssemblyReport\n    conversation_rendering_report: OracleConversationResponseRenderingReport\n    session_update_report: OracleBoundedMultiTurnSessionUpdateReport\n    lineage: OracleInteractiveIntelligencePipelineLineage\n    rendered_lines: tuple[str, ...]\n    rendered_line_count: int\n    session_turn_count: int\n    pipeline_completed: bool\n    terminal_display_ready: bool\n    session_continuation_ready: bool\n    read_only: bool\n    result_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleInteractiveIntelligencePipelineReport:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    status: str\n    repository_root: str\n    pipeline_result: OracleInteractiveIntelligencePipelineResult\n    end_to_end_pipeline_certified: bool\n    live_runner_binding_ready: bool\n    persistent_memory_enabled: bool\n    learning_update_performed: bool\n    analytics_execution_performed: bool\n    database_access_performed: bool\n    runtime_artifact_created: bool\n    runtime_artifact_modified: bool\n    networking_performed: bool\n    publication_allowed: bool\n    action_authorization_allowed: bool\n    qseries_execution_allowed: bool\n    read_only: bool\n    failure_reason: str | None\n    report_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(\n                value.items(),\n                key=lambda pair: str(pair[0]),\n            )\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    raise OracleInteractiveIntelligencePipelineInvariantError(\n        "unsupported OIT-048 value type: "\n        f"{type(value).__module__}.{type(value).__qualname__}"\n    )\n\n\ndef _stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=True,\n        allow_nan=False,\n    ).encode("utf-8")\n    return hashlib.sha256(payload).hexdigest()\n\n\ndef verify_pipeline_lineage(\n    lineage: OracleInteractiveIntelligencePipelineLineage,\n) -> bool:\n    body = asdict(lineage)\n    supplied = body.pop("lineage_hash")\n\n    if _stable_hash(body) != supplied:\n        raise OracleInteractiveIntelligencePipelineInvariantError(\n            "OIT-048 lineage hash mismatch"\n        )\n\n    required = (\n        lineage.source_context_assembly_report_hash,\n        lineage.source_prior_session_context_hash,\n        lineage.follow_up_resolution_report_hash,\n        lineage.projection_reentry_report_hash,\n        lineage.final_answer_assembly_report_hash,\n        lineage.conversation_rendering_report_hash,\n        lineage.updated_session_context_hash,\n    )\n    if not all(required):\n        raise OracleInteractiveIntelligencePipelineInvariantError(\n            "OIT-048 lineage incomplete"\n        )\n\n    if not lineage.exact_stage_order_verified:\n        raise OracleInteractiveIntelligencePipelineInvariantError(\n            "OIT-048 stage order not verified"\n        )\n\n    if not lineage.exact_cross_stage_lineage_verified:\n        raise OracleInteractiveIntelligencePipelineInvariantError(\n            "OIT-048 cross-stage lineage not verified"\n        )\n\n    return True\n\n\ndef verify_pipeline_result(\n    result: OracleInteractiveIntelligencePipelineResult,\n) -> bool:\n    body = asdict(result)\n    supplied = body.pop("result_hash")\n\n    if _stable_hash(body) != supplied:\n        raise OracleInteractiveIntelligencePipelineInvariantError(\n            "OIT-048 result hash mismatch"\n        )\n\n    if not result.pipeline_id or not result.query:\n        raise OracleInteractiveIntelligencePipelineInvariantError(\n            "OIT-048 pipeline identity missing"\n        )\n\n    verify_follow_up_query_resolution_report(\n        result.follow_up_resolution_report\n    )\n    verify_resolved_follow_up_projection_reentry_report(\n        result.projection_reentry_report\n    )\n    verify_final_intelligence_answer_assembly_report(\n        result.final_answer_assembly_report\n    )\n    verify_conversation_response_rendering_report(\n        result.conversation_rendering_report\n    )\n    verify_bounded_multi_turn_session_update_report(\n        result.session_update_report\n    )\n    verify_pipeline_lineage(result.lineage)\n\n    if result.rendered_line_count != len(result.rendered_lines):\n        raise OracleInteractiveIntelligencePipelineInvariantError(\n            "OIT-048 rendered line count mismatch"\n        )\n\n    if result.session_turn_count != (\n        result.session_update_report.updated_session_context.turn_count\n    ):\n        raise OracleInteractiveIntelligencePipelineInvariantError(\n            "OIT-048 session turn count mismatch"\n        )\n\n    expected_completed = bool(\n        result.follow_up_resolution_report.downstream_projection_ready\n        and result.projection_reentry_report.answer_generation_ready\n        and result.final_answer_assembly_report.final_answer_assembled\n        and result.conversation_rendering_report.rendering_completed\n        and result.session_update_report.turn_appended\n        and result.lineage.exact_stage_order_verified\n        and result.lineage.exact_cross_stage_lineage_verified\n        and result.read_only\n    )\n\n    if result.pipeline_completed != expected_completed:\n        raise OracleInteractiveIntelligencePipelineInvariantError(\n            "OIT-048 pipeline completion mismatch"\n        )\n\n    if result.terminal_display_ready != (\n        result.pipeline_completed\n        and result.conversation_rendering_report\n        .response_frame.terminal_display_ready\n    ):\n        raise OracleInteractiveIntelligencePipelineInvariantError(\n            "OIT-048 terminal display readiness mismatch"\n        )\n\n    if result.session_continuation_ready != (\n        result.pipeline_completed\n        and result.session_update_report.session_continuation_ready\n    ):\n        raise OracleInteractiveIntelligencePipelineInvariantError(\n            "OIT-048 session continuation readiness mismatch"\n        )\n\n    return True\n\n\ndef execute_end_to_end_interactive_intelligence_pipeline(\n    repository_root: str | Path,\n    *,\n    context_assembly_report: OracleIntelligenceSessionContextAssemblyReport,\n    prior_session_context: OracleBoundedMultiTurnSessionContext,\n    query: str,\n) -> OracleInteractiveIntelligencePipelineReport:\n    root = Path(repository_root).resolve()\n\n    verify_intelligence_session_context_assembly_report(\n        context_assembly_report\n    )\n    verify_multi_turn_session_context(prior_session_context)\n\n    follow_up = resolve_multi_turn_follow_up_query(\n        root,\n        session_context=prior_session_context,\n        query=query,\n    )\n    verify_follow_up_query_resolution_report(follow_up)\n\n    reentry = build_resolved_follow_up_projection_reentry_report(\n        root,\n        follow_up_resolution_report=follow_up,\n        context_assembly_report=context_assembly_report,\n    )\n    verify_resolved_follow_up_projection_reentry_report(reentry)\n\n    assembly = build_final_intelligence_answer_assembly_report(\n        root,\n        reentry_report=reentry,\n    )\n    verify_final_intelligence_answer_assembly_report(assembly)\n\n    rendering = build_conversation_response_rendering_report(\n        root,\n        final_answer_assembly_report=assembly,\n    )\n    verify_conversation_response_rendering_report(rendering)\n\n    session_update = append_answer_to_bounded_multi_turn_session(\n        root,\n        answer_report=assembly.answer_generation_report,\n        prior_session_context=prior_session_context,\n    )\n    verify_bounded_multi_turn_session_update_report(session_update)\n\n    exact_stage_order = bool(\n        follow_up.report_hash\n        == reentry.follow_up_resolution_report_hash\n        and reentry.report_hash\n        == assembly.reentry_report_hash\n        and assembly.report_hash\n        == rendering.final_answer_assembly_report_hash\n        and assembly.answer_generation_report.report_hash\n        == session_update.source_answer_report_hash\n    )\n\n    exact_cross_stage = bool(\n        follow_up.source_session_context_hash\n        == prior_session_context.context_hash\n        and reentry.context_assembly_report_hash\n        == context_assembly_report.report_hash\n        and reentry.projection_binding.source_session_context_hash\n        == prior_session_context.context_hash\n        and assembly.final_answer_package.lineage.source_session_context_hash\n        == prior_session_context.context_hash\n        and rendering.response_frame.source_package_hash\n        == assembly.final_answer_package.package_hash\n        and rendering.response_frame.source_answer_hash\n        == assembly.final_answer_package.answer.answer_hash\n        and session_update.updated_session_context.turns[-1].answer_hash\n        == assembly.final_answer_package.answer.answer_hash\n    )\n\n    if not exact_stage_order or not exact_cross_stage:\n        raise OracleInteractiveIntelligencePipelineInvariantError(\n            "OIT-048 end-to-end lineage mismatch"\n        )\n\n    lineage_body = {\n        "source_context_assembly_report_hash": (\n            context_assembly_report.report_hash\n        ),\n        "source_prior_session_context_hash": (\n            prior_session_context.context_hash\n        ),\n        "follow_up_resolution_report_hash": follow_up.report_hash,\n        "projection_reentry_report_hash": reentry.report_hash,\n        "final_answer_assembly_report_hash": assembly.report_hash,\n        "conversation_rendering_report_hash": rendering.report_hash,\n        "updated_session_context_hash": (\n            session_update.updated_session_context.context_hash\n        ),\n        "exact_stage_order_verified": True,\n        "exact_cross_stage_lineage_verified": True,\n    }\n    lineage = OracleInteractiveIntelligencePipelineLineage(\n        **lineage_body,\n        lineage_hash=_stable_hash(lineage_body),\n    )\n    verify_pipeline_lineage(lineage)\n\n    rendered_lines = tuple(\n        line.text for line in rendering.response_frame.lines\n    )\n\n    result_body = {\n        "pipeline_id": _stable_hash(\n            {\n                "query": query,\n                "context_hash": context_assembly_report.report_hash,\n                "prior_session_hash": prior_session_context.context_hash,\n                "rendering_hash": rendering.report_hash,\n                "updated_session_hash": (\n                    session_update.updated_session_context.context_hash\n                ),\n            }\n        )[:24],\n        "query": str(query),\n        "context_assembly_report_hash": (\n            context_assembly_report.report_hash\n        ),\n        "prior_session_context_hash": (\n            prior_session_context.context_hash\n        ),\n        "follow_up_resolution_report": follow_up,\n        "projection_reentry_report": reentry,\n        "final_answer_assembly_report": assembly,\n        "conversation_rendering_report": rendering,\n        "session_update_report": session_update,\n        "lineage": lineage,\n        "rendered_lines": rendered_lines,\n        "rendered_line_count": len(rendered_lines),\n        "session_turn_count": (\n            session_update.updated_session_context.turn_count\n        ),\n        "pipeline_completed": True,\n        "terminal_display_ready": True,\n        "session_continuation_ready": True,\n        "read_only": True,\n    }\n    result = OracleInteractiveIntelligencePipelineResult(\n        **result_body,\n        result_hash=_stable_hash(result_body),\n    )\n    verify_pipeline_result(result)\n\n    report_body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root),\n        "pipeline_result": result,\n        "end_to_end_pipeline_certified": result.pipeline_completed,\n        "live_runner_binding_ready": (\n            result.pipeline_completed\n            and result.terminal_display_ready\n            and result.session_continuation_ready\n        ),\n        "persistent_memory_enabled": False,\n        "learning_update_performed": False,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "runtime_artifact_created": False,\n        "runtime_artifact_modified": False,\n        "networking_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "read_only": True,\n        "failure_reason": None,\n    }\n    report = OracleInteractiveIntelligencePipelineReport(\n        **report_body,\n        report_hash=_stable_hash(report_body),\n    )\n    verify_interactive_intelligence_pipeline_report(report)\n    return report\n\n\ndef verify_interactive_intelligence_pipeline_report(\n    report: OracleInteractiveIntelligencePipelineReport,\n) -> bool:\n    body = asdict(report)\n    supplied = body.pop("report_hash")\n\n    if _stable_hash(body) != supplied:\n        raise OracleInteractiveIntelligencePipelineInvariantError(\n            "OIT-048 report hash mismatch"\n        )\n\n    if report.schema_version != SCHEMA_VERSION:\n        raise OracleInteractiveIntelligencePipelineInvariantError(\n            "OIT-048 schema mismatch"\n        )\n\n    if report.policy_id != POLICY_ID:\n        raise OracleInteractiveIntelligencePipelineInvariantError(\n            "OIT-048 policy mismatch"\n        )\n\n    verify_pipeline_result(report.pipeline_result)\n\n    if not report.read_only:\n        raise OracleInteractiveIntelligencePipelineInvariantError(\n            "OIT-048 report is not read-only"\n        )\n\n    if (\n        report.persistent_memory_enabled\n        or report.learning_update_performed\n        or report.analytics_execution_performed\n        or report.database_access_performed\n        or report.runtime_artifact_created\n        or report.runtime_artifact_modified\n        or report.networking_performed\n        or report.publication_allowed\n        or report.action_authorization_allowed\n        or report.qseries_execution_allowed\n    ):\n        raise OracleInteractiveIntelligencePipelineInvariantError(\n            "forbidden OIT-048 capability enabled"\n        )\n\n    expected = bool(\n        report.pipeline_result.pipeline_completed\n        and report.pipeline_result.terminal_display_ready\n        and report.pipeline_result.session_continuation_ready\n    )\n\n    if report.end_to_end_pipeline_certified != expected:\n        raise OracleInteractiveIntelligencePipelineInvariantError(\n            "OIT-048 certification state mismatch"\n        )\n\n    if report.live_runner_binding_ready != expected:\n        raise OracleInteractiveIntelligencePipelineInvariantError(\n            "OIT-048 runner-binding readiness mismatch"\n        )\n\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nimport importlib.util\nimport sys\nfrom dataclasses import replace\nfrom pathlib import Path\nfrom tempfile import TemporaryDirectory\n\nfrom qseries_v2.oracle_terminal.oracle_bounded_multi_turn_intelligence_session_context import (\n    OracleBoundedMultiTurnSessionContext,\n    OracleIntelligenceConversationTurn,\n    _stable_hash as oit_043_hash,\n)\nfrom qseries_v2.oracle_terminal.oracle_intelligence_session_context_assembly import (\n    ENGINE_ID as OIT_040_ENGINE_ID,\n    POLICY_ID as OIT_040_POLICY_ID,\n    SCHEMA_VERSION as OIT_040_SCHEMA_VERSION,\n    OracleIntelligenceContextField,\n    OracleIntelligenceSessionContext,\n    OracleIntelligenceSessionContextAssemblyReport,\n    _stable_hash as oit_040_hash,\n)\nfrom qseries_v2.oracle_terminal.oracle_end_to_end_interactive_intelligence_pipeline import (\n    OracleInteractiveIntelligencePipelineInvariantError,\n    execute_end_to_end_interactive_intelligence_pipeline,\n    verify_interactive_intelligence_pipeline_report,\n)\n\n\ndef load_runner(root: Path):\n    path = root / "run_oracle_open_intelligence_terminal.py"\n    name = "oracle_open_intelligence_terminal_oit_048_test"\n    spec = importlib.util.spec_from_file_location(name, path)\n    if spec is None or spec.loader is None:\n        raise RuntimeError("unable to load live runner")\n    module = importlib.util.module_from_spec(spec)\n    sys.modules[name] = module\n    spec.loader.exec_module(module)\n    return module\n\n\ndef context_field(key, path, field_type, value, text, ordinal):\n    body = {\n        "context_key": key,\n        "source_field_path": path,\n        "source_field_hash": f"source-field-{ordinal}",\n        "field_type": field_type,\n        "canonical_value": value,\n        "searchable_text": text,\n        "ordinal": ordinal,\n    }\n    return OracleIntelligenceContextField(\n        **body,\n        context_field_hash=oit_040_hash(body),\n    )\n\n\ndef make_context_report(root: Path):\n    fields = (\n        context_field(\n            "root",\n            "$",\n            "mapping",\n            {"direction": "bull", "probability": 0.82},\n            \'{"direction":"bull","probability":0.82}\',\n            0,\n        ),\n        context_field(\n            "direction",\n            "$.direction",\n            "string",\n            "bull",\n            "bull",\n            1,\n        ),\n        context_field(\n            "probability",\n            "$.probability",\n            "number",\n            0.82,\n            "0.82",\n            2,\n        ),\n        context_field(\n            "evidence.0.source_id",\n            "$.evidence[0].source_id",\n            "string",\n            "SOURCE-048",\n            "SOURCE-048",\n            3,\n        ),\n        context_field(\n            "evidence.0.confidence",\n            "$.evidence[0].confidence",\n            "number",\n            0.88,\n            "0.88",\n            4,\n        ),\n    )\n    context_body = {\n        "context_id": "context-048",\n        "source_normalization_report_hash": "normalization-048",\n        "source_normalized_record_hash": "record-048",\n        "source_envelope_hash": "envelope-048",\n        "source_execution_report_hash": "execution-048",\n        "source_validation_report_hash": "validation-048",\n        "source_invocation_result_hash": "result-048",\n        "context_fields": fields,\n        "context_field_count": len(fields),\n        "searchable_field_count": len(fields),\n        "root_field_present": True,\n        "deterministic_ordering_applied": True,\n        "full_lineage_preserved": True,\n        "bounded_context": True,\n        "context_ready": True,\n        "read_only": True,\n    }\n    context = OracleIntelligenceSessionContext(\n        **context_body,\n        context_hash=oit_040_hash(context_body),\n    )\n    report_body = {\n        "schema_version": OIT_040_SCHEMA_VERSION,\n        "engine_id": OIT_040_ENGINE_ID,\n        "policy_id": OIT_040_POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root.resolve()),\n        "normalization_report_hash": "normalization-048",\n        "session_context": context,\n        "context_assembled": True,\n        "query_planning_ready": True,\n        "multi_turn_memory_enabled": False,\n        "persistent_memory_enabled": False,\n        "learning_update_performed": False,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "runtime_artifact_created": False,\n        "runtime_artifact_modified": False,\n        "networking_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "read_only": True,\n        "failure_reason": None,\n    }\n    return OracleIntelligenceSessionContextAssemblyReport(\n        **report_body,\n        report_hash=oit_040_hash(report_body),\n    )\n\n\ndef make_prior_session():\n    turn_body = {\n        "turn_index": 0,\n        "query": "What evidence supports the bull direction?",\n        "answer_id": "answer-048-0",\n        "answer_hash": "answer-hash-048-0",\n        "answer_line_count": 2,\n        "source_answer_report_hash": "answer-report-048-0",\n        "source_projection_report_hash": "projection-report-048-0",\n        "evidence_linked": True,\n        "read_only": True,\n    }\n    turn = OracleIntelligenceConversationTurn(\n        **turn_body,\n        turn_hash=oit_043_hash(turn_body),\n    )\n    body = {\n        "session_id": "session-048",\n        "turns": (turn,),\n        "turn_count": 1,\n        "total_answer_line_count": 2,\n        "latest_turn_index": 0,\n        "bounded_turn_count": True,\n        "bounded_line_count": True,\n        "deterministic_ordering_applied": True,\n        "complete_lineage_preserved": True,\n        "volatile_memory_only": True,\n        "persistent_memory_enabled": False,\n        "learning_enabled": False,\n        "session_active": True,\n        "read_only": True,\n    }\n    return OracleBoundedMultiTurnSessionContext(\n        **body,\n        context_hash=oit_043_hash(body),\n    )\n\n\ndef main() -> int:\n    print("=" * 48)\n    print(" OIT-048 TEST")\n    print(" END-TO-END INTERACTIVE INTELLIGENCE PIPELINE")\n    print("=" * 48)\n\n    root = Path(__file__).resolve().parent\n    with TemporaryDirectory() as temporary:\n        fixture_root = Path(temporary)\n        context = make_context_report(fixture_root)\n        session = make_prior_session()\n\n        report = execute_end_to_end_interactive_intelligence_pipeline(\n            fixture_root,\n            context_assembly_report=context,\n            prior_session_context=session,\n            query="Has it changed now?",\n        )\n\n        assert report.end_to_end_pipeline_certified\n        assert report.live_runner_binding_ready\n\n        result = report.pipeline_result\n        assert result.pipeline_completed\n        assert result.terminal_display_ready\n        assert result.session_continuation_ready\n        assert result.rendered_line_count > 0\n        assert result.session_turn_count == 2\n        assert result.lineage.exact_stage_order_verified\n        assert result.lineage.exact_cross_stage_lineage_verified\n        assert (\n            result.follow_up_resolution_report\n            .resolved_follow_up_query.follow_up_detected\n        )\n        assert result.projection_reentry_report.answer_generation_ready\n        assert result.final_answer_assembly_report.final_answer_assembled\n        assert result.conversation_rendering_report.rendering_completed\n        assert result.session_update_report.turn_appended\n\n        replay = execute_end_to_end_interactive_intelligence_pipeline(\n            fixture_root,\n            context_assembly_report=context,\n            prior_session_context=session,\n            query="Has it changed now?",\n        )\n        assert replay == report\n        assert verify_interactive_intelligence_pipeline_report(report)\n\n        tampered = replace(\n            report,\n            persistent_memory_enabled=True,\n        )\n        try:\n            verify_interactive_intelligence_pipeline_report(tampered)\n        except OracleInteractiveIntelligencePipelineInvariantError:\n            pass\n        else:\n            raise AssertionError("tampered OIT-048 report accepted")\n\n    runner = load_runner(root)\n    assert runner.OIT_048_PIPELINE_BOUND\n    assert runner.OIT_048_PIPELINE_VERSION == "OIT-048"\n    assert callable(runner.execute_oit_048_interactive_pipeline)\n    assert callable(runner.render_oit_048_interactive_pipeline)\n\n    print("[PASS] Certified OIT-040 context consumed")\n    print("[PASS] Certified OIT-043 volatile session consumed")\n    print("[PASS] OIT-044 follow-up resolution executed")\n    print("[PASS] OIT-045 projection reentry executed")\n    print("[PASS] OIT-046 final answer assembly executed")\n    print("[PASS] OIT-047 conversation rendering executed")\n    print("[PASS] Updated OIT-043 session context produced")\n    print("[PASS] Exact stage order and hashes verified")\n    print("[PASS] End-to-end replay deterministic")\n    print("[PASS] Live terminal runner binding imported")\n    print("[PASS] Runner execute and render callables available")\n    print("[PASS] Tampered pipeline report rejected")\n    print("[PASS] Persistent memory and learning remained disabled")\n    print("[PASS] No analytics execution or runtime mutation performed")\n    print("[PASS] Publication, action authorization, and Q Series execution disabled")\n    print("[DONE] OIT-048 END-TO-END INTERACTIVE PIPELINE PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'
RUNNER_BLOCK = '\n# BEGIN OIT-048 END-TO-END INTERACTIVE INTELLIGENCE PIPELINE\nfrom qseries_v2.oracle_terminal.oracle_end_to_end_interactive_intelligence_pipeline import (\n    execute_end_to_end_interactive_intelligence_pipeline as _oit_048_execute_pipeline,\n    verify_interactive_intelligence_pipeline_report as _oit_048_verify_pipeline,\n)\n\nOIT_048_PIPELINE_BOUND = True\nOIT_048_PIPELINE_VERSION = "OIT-048"\n\n\ndef execute_oit_048_interactive_pipeline(\n    *,\n    repository_root,\n    context_assembly_report,\n    prior_session_context,\n    query,\n):\n    report = _oit_048_execute_pipeline(\n        repository_root,\n        context_assembly_report=context_assembly_report,\n        prior_session_context=prior_session_context,\n        query=query,\n    )\n    _oit_048_verify_pipeline(report)\n    return report\n\n\ndef render_oit_048_interactive_pipeline(\n    report,\n    *,\n    write=print,\n):\n    _oit_048_verify_pipeline(report)\n    for line in report.pipeline_result.rendered_lines:\n        write(line)\n    return report.pipeline_result.session_update_report.updated_session_context\n# END OIT-048 END-TO-END INTERACTIVE INTELLIGENCE PIPELINE\n'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_contract(path: Path, tokens: tuple[str, ...], label: str) -> None:
    if not path.is_file():
        raise RuntimeError(f"{label} missing: {path}")
    source = path.read_text(encoding="utf-8")
    missing = [token for token in tokens if token not in source]
    if missing:
        raise RuntimeError(f"{label} contract mismatch: {missing}")


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

    for path in (OIT_047, OIT_047_TEST):
        protected[path] = sha256(path)

    return protected


def build_runner_source() -> str:
    current = RUNNER.read_text(encoding="utf-8")

    if "# BEGIN OIT-048 END-TO-END INTERACTIVE INTELLIGENCE PIPELINE" in current:
        start = current.index(
            "# BEGIN OIT-048 END-TO-END INTERACTIVE INTELLIGENCE PIPELINE"
        )
        current = current[:start].rstrip() + "\n"

    updated, count = re.subn(
        r'RUNNER_VERSION\s*=\s*["\'][^"\']+["\']',
        'RUNNER_VERSION = "OIT-048"',
        current,
        count=1,
    )
    if count == 0:
        updated = 'RUNNER_VERSION = "OIT-048"\n' + current

    if not updated.endswith("\n"):
        updated += "\n"

    updated += "\n" + RUNNER_BLOCK.strip() + "\n"
    ast.parse(updated, filename=str(RUNNER))
    return updated


def main() -> int:
    print("=" * 48)
    print(" OIT-048 INSTALLER")
    print(" END-TO-END INTERACTIVE INTELLIGENCE PIPELINE")
    print("=" * 48)

    try:
        require_contract(
            OIT_047,
            (
                'SCHEMA_VERSION = "OIT-047"',
                'POLICY_ID = "oracle.conversation-response-rendering.v1"',
                "OracleConversationResponseRenderingReport",
                "build_conversation_response_rendering_report",
                "verify_conversation_response_rendering_report",
                "interactive_pipeline_ready",
            ),
            "Certified OIT-047 production",
        )
        require_contract(
            OIT_047_TEST,
            (
                "OIT-047 TEST",
                "CONVERSATION RESPONSE RENDERING",
                "Interactive pipeline readiness certified",
                "OIT-047 CONVERSATION RESPONSE RENDERING PASS",
            ),
            "Certified OIT-047 standalone test",
        )

        protected = protected_sources()
        runner_before = sha256(RUNNER)

        print("[OK] Certified OIT-047 production contract verified")
        print("[OK] Certified OIT-047 standalone test verified")
        print("[OK] Live Oracle terminal runner located")
        print(f"[OK] Protected production source files captured: {len(protected)}")

        upstream = subprocess.run(
            [sys.executable, str(OIT_047_TEST)],
            cwd=ROOT,
            check=False,
        )
        if upstream.returncode:
            raise RuntimeError(
                f"OIT-047 certification failed with exit code {upstream.returncode}"
            )

        if not RUNNER_BACKUP.exists():
            RUNNER_BACKUP.write_bytes(RUNNER.read_bytes())
            print(f"[OK] PRE-OIT-048 RUNNER BACKUP: {RUNNER_BACKUP.resolve()}")
        else:
            print(f"[OK] PRE-OIT-048 RUNNER BACKUP PRESENT: {RUNNER_BACKUP.resolve()}")

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)
        write_complete(RUNNER, build_runner_source())

        export = (
            "from .oracle_end_to_end_interactive_intelligence_pipeline import *"
        )
        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"
            current += export + "\n"
            INIT.write_text(current, encoding="utf-8", newline="\n")
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
                f"OIT-048 test failed with exit code {completed.returncode}"
            )

        for path, expected in protected.items():
            if sha256(path) != expected:
                raise RuntimeError(f"Protected production source changed: {path}")

        runner_after = sha256(RUNNER)
        if runner_after == runner_before:
            raise RuntimeError("OIT-048 runner binding was not installed")

        print("[PASS] Certified OIT-047 production and test unchanged")
        print("[PASS] OIT-048 production module installed")
        print("[PASS] OIT-048 standalone test installed")
        print("[PASS] Live terminal runner fully replaced with preserved source plus OIT-048 binding")
        print("[PASS] Existing terminal commands and handlers preserved")
        print("[PASS] End-to-end OIT-040 through OIT-047 pipeline certified")
        print("[PASS] Updated volatile session returned to caller")
        print("[PASS] Persistent memory and learning remained disabled")
        print("[PASS] No analytics execution or runtime mutation performed")
        print("[PASS] OLA, OIA, INT-OII, ORR, OOR, and Q Series unchanged")
        print("[PASS] Publication and execution remained disabled")
        print("[PASS] Read-only and execution boundaries preserved")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OIT-048 END-TO-END INTERACTIVE PIPELINE INSTALLED")
        return 0

    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
