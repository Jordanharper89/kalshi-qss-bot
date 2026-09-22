from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from qseries_v2.oracle_terminal.oracle_bounded_multi_turn_intelligence_session_context import (
    OracleBoundedMultiTurnSessionContext,
    OracleIntelligenceConversationTurn,
    _stable_hash as oit_043_hash,
)
from qseries_v2.oracle_terminal.oracle_intelligence_session_context_assembly import (
    ENGINE_ID as OIT_040_ENGINE_ID,
    POLICY_ID as OIT_040_POLICY_ID,
    SCHEMA_VERSION as OIT_040_SCHEMA_VERSION,
    OracleIntelligenceContextField,
    OracleIntelligenceSessionContext,
    OracleIntelligenceSessionContextAssemblyReport,
    _stable_hash as oit_040_hash,
)
from qseries_v2.oracle_terminal.oracle_end_to_end_interactive_intelligence_pipeline import (
    OracleInteractiveIntelligencePipelineInvariantError,
    execute_end_to_end_interactive_intelligence_pipeline,
    verify_interactive_intelligence_pipeline_report,
)


def load_runner(root: Path):
    path = root / "run_oracle_open_intelligence_terminal.py"
    name = "oracle_open_intelligence_terminal_oit_048_test"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load live runner")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def context_field(key, path, field_type, value, text, ordinal):
    body = {
        "context_key": key,
        "source_field_path": path,
        "source_field_hash": f"source-field-{ordinal}",
        "field_type": field_type,
        "canonical_value": value,
        "searchable_text": text,
        "ordinal": ordinal,
    }
    return OracleIntelligenceContextField(
        **body,
        context_field_hash=oit_040_hash(body),
    )


def make_context_report(root: Path):
    fields = (
        context_field(
            "root",
            "$",
            "mapping",
            {"direction": "bull", "probability": 0.82},
            '{"direction":"bull","probability":0.82}',
            0,
        ),
        context_field(
            "direction",
            "$.direction",
            "string",
            "bull",
            "bull",
            1,
        ),
        context_field(
            "probability",
            "$.probability",
            "number",
            0.82,
            "0.82",
            2,
        ),
        context_field(
            "evidence.0.source_id",
            "$.evidence[0].source_id",
            "string",
            "SOURCE-048",
            "SOURCE-048",
            3,
        ),
        context_field(
            "evidence.0.confidence",
            "$.evidence[0].confidence",
            "number",
            0.88,
            "0.88",
            4,
        ),
    )
    context_body = {
        "context_id": "context-048",
        "source_normalization_report_hash": "normalization-048",
        "source_normalized_record_hash": "record-048",
        "source_envelope_hash": "envelope-048",
        "source_execution_report_hash": "execution-048",
        "source_validation_report_hash": "validation-048",
        "source_invocation_result_hash": "result-048",
        "context_fields": fields,
        "context_field_count": len(fields),
        "searchable_field_count": len(fields),
        "root_field_present": True,
        "deterministic_ordering_applied": True,
        "full_lineage_preserved": True,
        "bounded_context": True,
        "context_ready": True,
        "read_only": True,
    }
    context = OracleIntelligenceSessionContext(
        **context_body,
        context_hash=oit_040_hash(context_body),
    )
    report_body = {
        "schema_version": OIT_040_SCHEMA_VERSION,
        "engine_id": OIT_040_ENGINE_ID,
        "policy_id": OIT_040_POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root.resolve()),
        "normalization_report_hash": "normalization-048",
        "session_context": context,
        "context_assembled": True,
        "query_planning_ready": True,
        "multi_turn_memory_enabled": False,
        "persistent_memory_enabled": False,
        "learning_update_performed": False,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "runtime_artifact_created": False,
        "runtime_artifact_modified": False,
        "networking_performed": False,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
        "read_only": True,
        "failure_reason": None,
    }
    return OracleIntelligenceSessionContextAssemblyReport(
        **report_body,
        report_hash=oit_040_hash(report_body),
    )


def make_prior_session():
    turn_body = {
        "turn_index": 0,
        "query": "What evidence supports the bull direction?",
        "answer_id": "answer-048-0",
        "answer_hash": "answer-hash-048-0",
        "answer_line_count": 2,
        "source_answer_report_hash": "answer-report-048-0",
        "source_projection_report_hash": "projection-report-048-0",
        "evidence_linked": True,
        "read_only": True,
    }
    turn = OracleIntelligenceConversationTurn(
        **turn_body,
        turn_hash=oit_043_hash(turn_body),
    )
    body = {
        "session_id": "session-048",
        "turns": (turn,),
        "turn_count": 1,
        "total_answer_line_count": 2,
        "latest_turn_index": 0,
        "bounded_turn_count": True,
        "bounded_line_count": True,
        "deterministic_ordering_applied": True,
        "complete_lineage_preserved": True,
        "volatile_memory_only": True,
        "persistent_memory_enabled": False,
        "learning_enabled": False,
        "session_active": True,
        "read_only": True,
    }
    return OracleBoundedMultiTurnSessionContext(
        **body,
        context_hash=oit_043_hash(body),
    )


def main() -> int:
    print("=" * 48)
    print(" OIT-048 TEST")
    print(" END-TO-END INTERACTIVE INTELLIGENCE PIPELINE")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    with TemporaryDirectory() as temporary:
        fixture_root = Path(temporary)
        context = make_context_report(fixture_root)
        session = make_prior_session()

        report = execute_end_to_end_interactive_intelligence_pipeline(
            fixture_root,
            context_assembly_report=context,
            prior_session_context=session,
            query="Has it changed now?",
        )

        assert report.end_to_end_pipeline_certified
        assert report.live_runner_binding_ready

        result = report.pipeline_result
        assert result.pipeline_completed
        assert result.terminal_display_ready
        assert result.session_continuation_ready
        assert result.rendered_line_count > 0
        assert result.session_turn_count == 2
        assert result.lineage.exact_stage_order_verified
        assert result.lineage.exact_cross_stage_lineage_verified
        assert (
            result.follow_up_resolution_report
            .resolved_follow_up_query.follow_up_detected
        )
        assert result.projection_reentry_report.answer_generation_ready
        assert result.final_answer_assembly_report.final_answer_assembled
        assert result.conversation_rendering_report.rendering_completed
        assert result.session_update_report.turn_appended

        replay = execute_end_to_end_interactive_intelligence_pipeline(
            fixture_root,
            context_assembly_report=context,
            prior_session_context=session,
            query="Has it changed now?",
        )
        assert replay == report
        assert verify_interactive_intelligence_pipeline_report(report)

        tampered = replace(
            report,
            persistent_memory_enabled=True,
        )
        try:
            verify_interactive_intelligence_pipeline_report(tampered)
        except OracleInteractiveIntelligencePipelineInvariantError:
            pass
        else:
            raise AssertionError("tampered OIT-048 report accepted")

    runner = load_runner(root)
    assert runner.OIT_048_PIPELINE_BOUND
    assert runner.OIT_048_PIPELINE_VERSION == "OIT-048"
    assert callable(runner.execute_oit_048_interactive_pipeline)
    assert callable(runner.render_oit_048_interactive_pipeline)

    print("[PASS] Certified OIT-040 context consumed")
    print("[PASS] Certified OIT-043 volatile session consumed")
    print("[PASS] OIT-044 follow-up resolution executed")
    print("[PASS] OIT-045 projection reentry executed")
    print("[PASS] OIT-046 final answer assembly executed")
    print("[PASS] OIT-047 conversation rendering executed")
    print("[PASS] Updated OIT-043 session context produced")
    print("[PASS] Exact stage order and hashes verified")
    print("[PASS] End-to-end replay deterministic")
    print("[PASS] Live terminal runner binding imported")
    print("[PASS] Runner execute and render callables available")
    print("[PASS] Tampered pipeline report rejected")
    print("[PASS] Persistent memory and learning remained disabled")
    print("[PASS] No analytics execution or runtime mutation performed")
    print("[PASS] Publication, action authorization, and Q Series execution disabled")
    print("[DONE] OIT-048 END-TO-END INTERACTIVE PIPELINE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
