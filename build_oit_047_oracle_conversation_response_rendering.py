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

        production = (
            package
            / "oracle_final_intelligence_answer_assembly.py"
        )
        test = (
            candidate
            / "test_oit_046_oracle_final_intelligence_answer_assembly.py"
        )

        if production.is_file() and test.is_file():
            return candidate

    raise SystemExit(
        "[ERROR] Could not locate current Q Series repository."
    )


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"

OIT_046 = (
    PACKAGE
    / "oracle_final_intelligence_answer_assembly.py"
)
OIT_046_TEST = (
    ROOT
    / "test_oit_046_oracle_final_intelligence_answer_assembly.py"
)

PRODUCTION = (
    PACKAGE
    / "oracle_conversation_response_rendering.py"
)
TEST = (
    ROOT
    / "test_oit_047_oracle_conversation_response_rendering.py"
)
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass\nfrom pathlib import Path\nfrom typing import Any, Mapping\n\nfrom .oracle_final_intelligence_answer_assembly import (\n    OracleFinalIntelligenceAnswerAssemblyInvariantError,\n    OracleFinalIntelligenceAnswerAssemblyReport,\n    OracleFinalIntelligenceAnswerPackage,\n    verify_final_answer_package,\n    verify_final_intelligence_answer_assembly_report,\n)\n\nSCHEMA_VERSION = "OIT-047"\nENGINE_ID = "OIT-047"\nPOLICY_ID = "oracle.conversation-response-rendering.v1"\n\nMAX_RENDERED_LINES = 256\n\n\nclass OracleConversationResponseRenderingInvariantError(\n    OracleFinalIntelligenceAnswerAssemblyInvariantError\n):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleConversationRenderLine:\n    render_index: int\n    render_type: str\n    text: str\n    source_answer_line_hashes: tuple[str, ...]\n    source_field_paths: tuple[str, ...]\n    evidence_linked: bool\n    render_line_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleConversationResponseFrame:\n    frame_id: str\n    frame_type: str\n    title: str\n    subtitle: str\n    lines: tuple[OracleConversationRenderLine, ...]\n    line_count: int\n    source_package_hash: str\n    source_answer_hash: str\n    source_lineage_hash: str\n    deterministic_ordering_applied: bool\n    bounded_frame: bool\n    terminal_display_ready: bool\n    read_only: bool\n    frame_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleConversationResponseRenderingReport:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    status: str\n    repository_root: str\n    final_answer_assembly_report_hash: str\n    response_frame: OracleConversationResponseFrame\n    rendering_completed: bool\n    interactive_pipeline_ready: bool\n    exact_answer_text_preserved: bool\n    unsupported_content_generated: bool\n    persistent_memory_enabled: bool\n    learning_update_performed: bool\n    analytics_execution_performed: bool\n    database_access_performed: bool\n    runtime_artifact_created: bool\n    runtime_artifact_modified: bool\n    networking_performed: bool\n    publication_allowed: bool\n    action_authorization_allowed: bool\n    qseries_execution_allowed: bool\n    read_only: bool\n    failure_reason: str | None\n    report_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(\n                value.items(),\n                key=lambda pair: str(pair[0]),\n            )\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    raise OracleConversationResponseRenderingInvariantError(\n        "unsupported OIT-047 value type: "\n        f"{type(value).__module__}.{type(value).__qualname__}"\n    )\n\n\ndef _stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=True,\n        allow_nan=False,\n    ).encode("utf-8")\n    return hashlib.sha256(payload).hexdigest()\n\n\ndef _render_type(answer_line_type: str) -> str:\n    mapping = {\n        "summary": "summary",\n        "fact": "fact",\n        "evidence": "evidence",\n        "uncertainty": "uncertainty",\n    }\n    if answer_line_type not in mapping:\n        raise OracleConversationResponseRenderingInvariantError(\n            "unsupported answer line type"\n        )\n    return mapping[answer_line_type]\n\n\ndef _render_line(\n    *,\n    index: int,\n    answer_line,\n) -> OracleConversationRenderLine:\n    body = {\n        "render_index": index,\n        "render_type": _render_type(answer_line.line_type),\n        "text": answer_line.text,\n        "source_answer_line_hashes": (\n            answer_line.line_hash,\n        ),\n        "source_field_paths": (\n            answer_line.source_field_paths\n        ),\n        "evidence_linked": answer_line.evidence_linked,\n    }\n    line = OracleConversationRenderLine(\n        **body,\n        render_line_hash=_stable_hash(body),\n    )\n    verify_conversation_render_line(line)\n    return line\n\n\ndef verify_conversation_render_line(\n    line: OracleConversationRenderLine,\n) -> bool:\n    body = asdict(line)\n    supplied = body.pop("render_line_hash")\n\n    if _stable_hash(body) != supplied:\n        raise OracleConversationResponseRenderingInvariantError(\n            "OIT-047 render line hash mismatch"\n        )\n\n    if line.render_index < 0:\n        raise OracleConversationResponseRenderingInvariantError(\n            "OIT-047 render line index invalid"\n        )\n\n    if line.render_type not in {\n        "summary",\n        "fact",\n        "evidence",\n        "uncertainty",\n    }:\n        raise OracleConversationResponseRenderingInvariantError(\n            "OIT-047 render line type invalid"\n        )\n\n    if not line.text:\n        raise OracleConversationResponseRenderingInvariantError(\n            "OIT-047 render line text missing"\n        )\n\n    if not line.source_answer_line_hashes:\n        raise OracleConversationResponseRenderingInvariantError(\n            "OIT-047 answer-line lineage missing"\n        )\n\n    if not line.source_field_paths:\n        raise OracleConversationResponseRenderingInvariantError(\n            "OIT-047 field lineage missing"\n        )\n\n    if not line.evidence_linked:\n        raise OracleConversationResponseRenderingInvariantError(\n            "OIT-047 render line is not evidence-linked"\n        )\n\n    return True\n\n\ndef verify_conversation_response_frame(\n    frame: OracleConversationResponseFrame,\n) -> bool:\n    body = asdict(frame)\n    supplied = body.pop("frame_hash")\n\n    if _stable_hash(body) != supplied:\n        raise OracleConversationResponseRenderingInvariantError(\n            "OIT-047 response frame hash mismatch"\n        )\n\n    if not frame.frame_id:\n        raise OracleConversationResponseRenderingInvariantError(\n            "OIT-047 frame ID missing"\n        )\n\n    if frame.frame_type != "oracle_conversation_response":\n        raise OracleConversationResponseRenderingInvariantError(\n            "OIT-047 frame type invalid"\n        )\n\n    if not frame.title or not frame.subtitle:\n        raise OracleConversationResponseRenderingInvariantError(\n            "OIT-047 frame heading missing"\n        )\n\n    if frame.line_count != len(frame.lines):\n        raise OracleConversationResponseRenderingInvariantError(\n            "OIT-047 frame line count mismatch"\n        )\n\n    for index, line in enumerate(frame.lines):\n        verify_conversation_render_line(line)\n        if line.render_index != index:\n            raise OracleConversationResponseRenderingInvariantError(\n                "OIT-047 render ordering mismatch"\n            )\n\n    if not frame.source_package_hash:\n        raise OracleConversationResponseRenderingInvariantError(\n            "OIT-047 package lineage missing"\n        )\n\n    if not frame.source_answer_hash:\n        raise OracleConversationResponseRenderingInvariantError(\n            "OIT-047 answer lineage missing"\n        )\n\n    if not frame.source_lineage_hash:\n        raise OracleConversationResponseRenderingInvariantError(\n            "OIT-047 final lineage missing"\n        )\n\n    if frame.bounded_frame != (\n        frame.line_count <= MAX_RENDERED_LINES\n    ):\n        raise OracleConversationResponseRenderingInvariantError(\n            "OIT-047 bounded-frame state mismatch"\n        )\n\n    expected_ready = bool(\n        frame.lines\n        and frame.deterministic_ordering_applied\n        and frame.bounded_frame\n        and frame.read_only\n        and all(line.evidence_linked for line in frame.lines)\n    )\n\n    if frame.terminal_display_ready != expected_ready:\n        raise OracleConversationResponseRenderingInvariantError(\n            "OIT-047 terminal display readiness mismatch"\n        )\n\n    return True\n\n\ndef build_conversation_response_rendering_report(\n    repository_root: str | Path,\n    *,\n    final_answer_assembly_report: OracleFinalIntelligenceAnswerAssemblyReport,\n) -> OracleConversationResponseRenderingReport:\n    root = Path(repository_root).resolve()\n\n    verify_final_intelligence_answer_assembly_report(\n        final_answer_assembly_report\n    )\n\n    if not final_answer_assembly_report.conversation_rendering_ready:\n        raise OracleConversationResponseRenderingInvariantError(\n            final_answer_assembly_report.failure_reason\n            or "OIT-046 report is not conversation-rendering ready"\n        )\n\n    package: OracleFinalIntelligenceAnswerPackage = (\n        final_answer_assembly_report.final_answer_package\n    )\n    verify_final_answer_package(package)\n\n    lines = tuple(\n        _render_line(\n            index=index,\n            answer_line=answer_line,\n        )\n        for index, answer_line in enumerate(\n            package.answer.answer_lines\n        )\n    )\n\n    if len(lines) > MAX_RENDERED_LINES:\n        raise OracleConversationResponseRenderingInvariantError(\n            "OIT-047 rendered line limit exceeded"\n        )\n\n    preserved = tuple(\n        line.text for line in lines\n    ) == tuple(\n        line.text for line in package.answer.answer_lines\n    )\n\n    frame_body = {\n        "frame_id": _stable_hash(\n            {\n                "package_hash": package.package_hash,\n                "answer_hash": package.answer.answer_hash,\n                "render_lines": lines,\n            }\n        )[:24],\n        "frame_type": "oracle_conversation_response",\n        "title": "Oracle Intelligence Response",\n        "subtitle": (\n            "Read-only evidence-linked answer"\n            + (\n                " | follow-up context resolved"\n                if package.follow_up_detected\n                else ""\n            )\n        ),\n        "lines": lines,\n        "line_count": len(lines),\n        "source_package_hash": package.package_hash,\n        "source_answer_hash": package.answer.answer_hash,\n        "source_lineage_hash": package.lineage.lineage_hash,\n        "deterministic_ordering_applied": True,\n        "bounded_frame": len(lines) <= MAX_RENDERED_LINES,\n        "terminal_display_ready": bool(\n            lines\n            and preserved\n            and all(line.evidence_linked for line in lines)\n            and len(lines) <= MAX_RENDERED_LINES\n        ),\n        "read_only": True,\n    }\n    frame = OracleConversationResponseFrame(\n        **frame_body,\n        frame_hash=_stable_hash(frame_body),\n    )\n    verify_conversation_response_frame(frame)\n\n    report_body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root),\n        "final_answer_assembly_report_hash": (\n            final_answer_assembly_report.report_hash\n        ),\n        "response_frame": frame,\n        "rendering_completed": frame.terminal_display_ready,\n        "interactive_pipeline_ready": frame.terminal_display_ready,\n        "exact_answer_text_preserved": preserved,\n        "unsupported_content_generated": False,\n        "persistent_memory_enabled": False,\n        "learning_update_performed": False,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "runtime_artifact_created": False,\n        "runtime_artifact_modified": False,\n        "networking_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "read_only": True,\n        "failure_reason": (\n            None\n            if frame.terminal_display_ready and preserved\n            else "OIT-047 conversation rendering failed"\n        ),\n    }\n    report = OracleConversationResponseRenderingReport(\n        **report_body,\n        report_hash=_stable_hash(report_body),\n    )\n    verify_conversation_response_rendering_report(report)\n    return report\n\n\ndef verify_conversation_response_rendering_report(\n    report: OracleConversationResponseRenderingReport,\n) -> bool:\n    body = asdict(report)\n    supplied = body.pop("report_hash")\n\n    if _stable_hash(body) != supplied:\n        raise OracleConversationResponseRenderingInvariantError(\n            "OIT-047 rendering report hash mismatch"\n        )\n\n    if report.schema_version != SCHEMA_VERSION:\n        raise OracleConversationResponseRenderingInvariantError(\n            "OIT-047 schema mismatch"\n        )\n\n    if report.policy_id != POLICY_ID:\n        raise OracleConversationResponseRenderingInvariantError(\n            "OIT-047 policy mismatch"\n        )\n\n    verify_conversation_response_frame(\n        report.response_frame\n    )\n\n    if not report.read_only:\n        raise OracleConversationResponseRenderingInvariantError(\n            "OIT-047 report is not read-only"\n        )\n\n    if (\n        report.unsupported_content_generated\n        or report.persistent_memory_enabled\n        or report.learning_update_performed\n        or report.analytics_execution_performed\n        or report.database_access_performed\n        or report.runtime_artifact_created\n        or report.runtime_artifact_modified\n        or report.networking_performed\n        or report.publication_allowed\n        or report.action_authorization_allowed\n        or report.qseries_execution_allowed\n    ):\n        raise OracleConversationResponseRenderingInvariantError(\n            "forbidden OIT-047 capability enabled"\n        )\n\n    expected = bool(\n        report.response_frame.terminal_display_ready\n        and report.exact_answer_text_preserved\n        and report.response_frame.read_only\n    )\n\n    if report.rendering_completed != expected:\n        raise OracleConversationResponseRenderingInvariantError(\n            "OIT-047 rendering-completed state mismatch"\n        )\n\n    if report.interactive_pipeline_ready != expected:\n        raise OracleConversationResponseRenderingInvariantError(\n            "OIT-047 pipeline readiness mismatch"\n        )\n\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import replace\nfrom pathlib import Path\nfrom tempfile import TemporaryDirectory\n\nfrom qseries_v2.oracle_terminal.oracle_terminal_intelligence_answer_generation import (\n    OracleTerminalIntelligenceAnswer,\n    OracleTerminalIntelligenceAnswerLine,\n    _stable_hash as oit_042_hash,\n)\nfrom qseries_v2.oracle_terminal.oracle_final_intelligence_answer_assembly import (\n    ENGINE_ID as OIT_046_ENGINE_ID,\n    POLICY_ID as OIT_046_POLICY_ID,\n    SCHEMA_VERSION as OIT_046_SCHEMA_VERSION,\n    OracleFinalIntelligenceAnswerAssemblyReport,\n    OracleFinalIntelligenceAnswerLineage,\n    OracleFinalIntelligenceAnswerPackage,\n    _stable_hash as oit_046_hash,\n    verify_final_intelligence_answer_assembly_report,\n)\nfrom qseries_v2.oracle_terminal.oracle_terminal_intelligence_answer_generation import (\n    ENGINE_ID as OIT_042_ENGINE_ID,\n    POLICY_ID as OIT_042_POLICY_ID,\n    SCHEMA_VERSION as OIT_042_SCHEMA_VERSION,\n    OracleTerminalIntelligenceAnswerGenerationReport,\n)\nfrom qseries_v2.oracle_terminal.oracle_conversation_response_rendering import (\n    OracleConversationResponseRenderingInvariantError,\n    build_conversation_response_rendering_report,\n    verify_conversation_response_rendering_report,\n)\n\n\ndef answer_line(\n    index: int,\n    line_type: str,\n    text: str,\n    source_path: str,\n):\n    body = {\n        "line_index": index,\n        "line_type": line_type,\n        "text": text,\n        "source_field_paths": (source_path,),\n        "source_field_hashes": (f"field-hash-{index}",),\n        "evidence_linked": True,\n    }\n    return OracleTerminalIntelligenceAnswerLine(\n        **body,\n        line_hash=oit_042_hash(body),\n    )\n\n\ndef make_assembly_report(root: Path):\n    lines = (\n        answer_line(\n            0,\n            "summary",\n            "Oracle found 3 certified context fields relevant to the query.",\n            "$.direction",\n        ),\n        answer_line(\n            1,\n            "fact",\n            "direction: bull",\n            "$.direction",\n        ),\n        answer_line(\n            2,\n            "evidence",\n            "evidence.0.source_id: SOURCE-047",\n            "$.evidence[0].source_id",\n        ),\n        answer_line(\n            3,\n            "uncertainty",\n            "Uncertainty remains bounded by probability 0.81.",\n            "$.probability",\n        ),\n    )\n\n    answer_body = {\n        "answer_id": "answer-047",\n        "source_projection_hash": "projection-hash-047",\n        "source_projection_report_hash": "projection-report-hash-047",\n        "query": "Has it changed now?",\n        "answer_lines": lines,\n        "answer_line_count": len(lines),\n        "evidence_line_count": 1,\n        "summary_line_count": 1,\n        "uncertainty_line_count": 1,\n        "all_claims_evidence_linked": True,\n        "deterministic_ordering_applied": True,\n        "bounded_answer": True,\n        "answer_ready": True,\n        "read_only": True,\n    }\n    answer = OracleTerminalIntelligenceAnswer(\n        **answer_body,\n        answer_hash=oit_042_hash(answer_body),\n    )\n\n    answer_report_body = {\n        "schema_version": OIT_042_SCHEMA_VERSION,\n        "engine_id": OIT_042_ENGINE_ID,\n        "policy_id": OIT_042_POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root.resolve()),\n        "projection_report_hash": "projection-report-hash-047",\n        "answer": answer,\n        "answer_generated": True,\n        "answer_render_ready": True,\n        "unsupported_claims_generated": False,\n        "free_form_generation_used": False,\n        "multi_turn_memory_enabled": False,\n        "persistent_memory_enabled": False,\n        "learning_update_performed": False,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "runtime_artifact_created": False,\n        "runtime_artifact_modified": False,\n        "networking_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "read_only": True,\n        "failure_reason": None,\n    }\n    answer_report = OracleTerminalIntelligenceAnswerGenerationReport(\n        **answer_report_body,\n        report_hash=oit_042_hash(answer_report_body),\n    )\n\n    lineage_body = {\n        "source_reentry_report_hash": "reentry-report-hash-047",\n        "source_follow_up_resolution_report_hash": "follow-up-report-hash-047",\n        "source_context_assembly_report_hash": "context-report-hash-047",\n        "source_projection_report_hash": "projection-report-hash-047",\n        "source_projection_hash": "projection-hash-047",\n        "source_answer_generation_report_hash": answer_report.report_hash,\n        "source_answer_hash": answer.answer_hash,\n        "source_session_context_hash": "session-context-hash-047",\n        "primary_reference_turn_index": 1,\n        "exact_lineage_verified": True,\n    }\n    lineage = OracleFinalIntelligenceAnswerLineage(\n        **lineage_body,\n        lineage_hash=oit_046_hash(lineage_body),\n    )\n\n    package_body = {\n        "package_id": "package-047",\n        "query": "Has it changed now?",\n        "resolved_query": (\n            "Has it changed now? [context from prior query: "\n            "What evidence supports the bull direction?]"\n        ),\n        "follow_up_detected": True,\n        "resolution_confidence": 0.70,\n        "answer": answer,\n        "lineage": lineage,\n        "answer_line_count": len(lines),\n        "all_claims_evidence_linked": True,\n        "deterministic_assembly": True,\n        "bounded_answer": True,\n        "terminal_render_ready": True,\n        "read_only": True,\n    }\n    package = OracleFinalIntelligenceAnswerPackage(\n        **package_body,\n        package_hash=oit_046_hash(package_body),\n    )\n\n    report_body = {\n        "schema_version": OIT_046_SCHEMA_VERSION,\n        "engine_id": OIT_046_ENGINE_ID,\n        "policy_id": OIT_046_POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root.resolve()),\n        "reentry_report_hash": "reentry-report-hash-047",\n        "answer_generation_report": answer_report,\n        "final_answer_package": package,\n        "final_answer_assembled": True,\n        "conversation_rendering_ready": True,\n        "unsupported_claims_generated": False,\n        "persistent_memory_enabled": False,\n        "learning_update_performed": False,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "runtime_artifact_created": False,\n        "runtime_artifact_modified": False,\n        "networking_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "read_only": True,\n        "failure_reason": None,\n    }\n    report = OracleFinalIntelligenceAnswerAssemblyReport(\n        **report_body,\n        report_hash=oit_046_hash(report_body),\n    )\n    verify_final_intelligence_answer_assembly_report(report)\n    return report\n\n\ndef main() -> int:\n    print("=" * 48)\n    print(" OIT-047 TEST")\n    print(" CONVERSATION RESPONSE RENDERING")\n    print("=" * 48)\n\n    with TemporaryDirectory() as temporary:\n        root = Path(temporary)\n        assembly = make_assembly_report(root)\n\n        report = build_conversation_response_rendering_report(\n            root,\n            final_answer_assembly_report=assembly,\n        )\n\n        assert report.rendering_completed\n        assert report.interactive_pipeline_ready\n        assert report.exact_answer_text_preserved\n        assert not report.unsupported_content_generated\n\n        frame = report.response_frame\n        assert frame.terminal_display_ready\n        assert frame.frame_type == "oracle_conversation_response"\n        assert frame.title == "Oracle Intelligence Response"\n        assert "follow-up context resolved" in frame.subtitle\n        assert frame.line_count == 4\n        assert frame.bounded_frame\n        assert frame.deterministic_ordering_applied\n        assert frame.source_package_hash == (\n            assembly.final_answer_package.package_hash\n        )\n        assert frame.source_answer_hash == (\n            assembly.final_answer_package.answer.answer_hash\n        )\n        assert frame.source_lineage_hash == (\n            assembly.final_answer_package.lineage.lineage_hash\n        )\n\n        original_text = tuple(\n            line.text\n            for line in assembly.final_answer_package.answer.answer_lines\n        )\n        rendered_text = tuple(\n            line.text for line in frame.lines\n        )\n        assert rendered_text == original_text\n\n        assert tuple(\n            line.render_type for line in frame.lines\n        ) == (\n            "summary",\n            "fact",\n            "evidence",\n            "uncertainty",\n        )\n\n        assert all(line.evidence_linked for line in frame.lines)\n        assert all(\n            line.source_answer_line_hashes\n            for line in frame.lines\n        )\n        assert all(\n            line.source_field_paths\n            for line in frame.lines\n        )\n\n        replay = build_conversation_response_rendering_report(\n            root,\n            final_answer_assembly_report=assembly,\n        )\n        assert replay == report\n        assert verify_conversation_response_rendering_report(\n            report\n        )\n\n        tampered = replace(\n            report,\n            unsupported_content_generated=True,\n        )\n        try:\n            verify_conversation_response_rendering_report(\n                tampered\n            )\n        except OracleConversationResponseRenderingInvariantError:\n            pass\n        else:\n            raise AssertionError(\n                "tampered OIT-047 report accepted"\n            )\n\n        assert not report.persistent_memory_enabled\n        assert not report.learning_update_performed\n        assert not report.analytics_execution_performed\n        assert not report.database_access_performed\n        assert not report.runtime_artifact_created\n        assert not report.runtime_artifact_modified\n        assert not report.networking_performed\n        assert not report.publication_allowed\n        assert not report.action_authorization_allowed\n        assert not report.qseries_execution_allowed\n        assert report.read_only\n\n    print("[PASS] Certified OIT-046 final answer consumed")\n    print("[PASS] Conversation response frame materialized")\n    print("[PASS] Exact answer text preserved")\n    print("[PASS] Summary, fact, evidence, and uncertainty lines rendered")\n    print("[PASS] Answer-line hashes retained")\n    print("[PASS] Source field paths retained")\n    print("[PASS] Final package and lineage hashes retained")\n    print("[PASS] Follow-up context surfaced in frame subtitle")\n    print("[PASS] Deterministic render ordering certified")\n    print("[PASS] Bounded frame limit enforced")\n    print("[PASS] Interactive pipeline readiness certified")\n    print("[PASS] Rendering deterministic across replay")\n    print("[PASS] Tampered rendering report rejected")\n    print("[PASS] Persistent memory and learning remained disabled")\n    print("[PASS] No analytics execution or runtime mutation performed")\n    print("[PASS] Publication, action authorization, and Q Series execution disabled")\n    print("[DONE] OIT-047 CONVERSATION RESPONSE RENDERING PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


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
        OIT_046,
        OIT_046_TEST,
        RUNNER,
    ):
        if path.is_file():
            protected[path] = sha256(path)

    return protected


def main() -> int:
    print("=" * 48)
    print(" OIT-047 INSTALLER")
    print(" CONVERSATION RESPONSE RENDERING")
    print("=" * 48)

    try:
        require_contract(
            OIT_046,
            (
                'SCHEMA_VERSION = "OIT-046"',
                'POLICY_ID = "oracle.final-intelligence-answer-assembly.v1"',
                "OracleFinalIntelligenceAnswerLineage",
                "OracleFinalIntelligenceAnswerPackage",
                "OracleFinalIntelligenceAnswerAssemblyReport",
                "verify_final_answer_package",
                "verify_final_intelligence_answer_assembly_report",
                "conversation_rendering_ready",
                "terminal_render_ready",
            ),
            "Certified OIT-046 production",
        )

        require_contract(
            OIT_046_TEST,
            (
                "OIT-046 TEST",
                "FINAL INTELLIGENCE ANSWER ASSEMBLY",
                "Conversation-rendering readiness certified",
                "OIT-046 FINAL INTELLIGENCE ANSWER ASSEMBLY PASS",
            ),
            "Certified OIT-046 standalone test",
        )

        protected = protected_sources()

        print("[OK] Certified OIT-046 production contract verified")
        print("[OK] Certified OIT-046 standalone test verified")
        print(
            f"[OK] Protected production source files captured: "
            f"{len(protected)}"
        )

        upstream = subprocess.run(
            [sys.executable, str(OIT_046_TEST)],
            cwd=ROOT,
            check=False,
        )

        if upstream.returncode:
            raise RuntimeError(
                "OIT-046 certification failed with exit code "
                f"{upstream.returncode}"
            )

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_conversation_response_rendering import *"
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
                "OIT-047 test failed with exit code "
                f"{completed.returncode}"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Protected production source changed: {path}"
                )

        print("[PASS] Certified OIT-046 production and test unchanged")
        print("[PASS] Oracle terminal runner unchanged")
        print("[PASS] OIT-047 production module installed")
        print("[PASS] OIT-047 standalone test installed")
        print("[PASS] Conversation response rendering certified")
        print("[PASS] Exact answer text and line hashes retained")
        print("[PASS] Final package and lineage hashes retained")
        print("[PASS] Interactive pipeline readiness certified")
        print("[PASS] Persistent memory and learning remained disabled")
        print("[PASS] No analytics execution or runtime mutation performed")
        print("[PASS] OLA, OIA, INT-OII, ORR, OOR, and Q Series unchanged")
        print("[PASS] Publication and execution remained disabled")
        print("[PASS] Read-only and execution boundaries preserved")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OIT-047 CONVERSATION RESPONSE RENDERING INSTALLED")
        return 0

    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
