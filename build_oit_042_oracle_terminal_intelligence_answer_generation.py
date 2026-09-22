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
            / "oracle_natural_language_intelligence_response_projection.py"
        )
        test = (
            candidate
            / "test_oit_041_oracle_natural_language_intelligence_response_projection.py"
        )
        if production.is_file() and test.is_file():
            return candidate

    raise SystemExit("[ERROR] Could not locate current Q Series repository.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"
OIT_041 = (
    PACKAGE
    / "oracle_natural_language_intelligence_response_projection.py"
)
OIT_041_TEST = (
    ROOT
    / "test_oit_041_oracle_natural_language_intelligence_response_projection.py"
)
PRODUCTION = (
    PACKAGE
    / "oracle_terminal_intelligence_answer_generation.py"
)
TEST = (
    ROOT
    / "test_oit_042_oracle_terminal_intelligence_answer_generation.py"
)
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass\nfrom pathlib import Path\nfrom typing import Any, Mapping\n\nfrom .oracle_natural_language_intelligence_response_projection import (\n    OracleNaturalLanguageIntelligenceProjectionReport,\n    OracleProjectedIntelligenceField,\n    OracleIntelligenceResponseProjectionInvariantError,\n    verify_natural_language_intelligence_projection_report,\n)\n\nSCHEMA_VERSION = "OIT-042"\nENGINE_ID = "OIT-042"\nPOLICY_ID = "oracle.terminal-intelligence-answer-generation.v1"\n\nMAX_ANSWER_LINES = 128\n\n\nclass OracleTerminalIntelligenceAnswerInvariantError(\n    OracleIntelligenceResponseProjectionInvariantError\n):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleTerminalIntelligenceAnswerLine:\n    line_index: int\n    line_type: str\n    text: str\n    source_field_paths: tuple[str, ...]\n    source_field_hashes: tuple[str, ...]\n    evidence_linked: bool\n    line_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleTerminalIntelligenceAnswer:\n    answer_id: str\n    source_projection_hash: str\n    source_projection_report_hash: str\n    query: str\n    answer_lines: tuple[OracleTerminalIntelligenceAnswerLine, ...]\n    answer_line_count: int\n    evidence_line_count: int\n    summary_line_count: int\n    uncertainty_line_count: int\n    all_claims_evidence_linked: bool\n    deterministic_ordering_applied: bool\n    bounded_answer: bool\n    answer_ready: bool\n    read_only: bool\n    answer_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleTerminalIntelligenceAnswerGenerationReport:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    status: str\n    repository_root: str\n    projection_report_hash: str\n    answer: OracleTerminalIntelligenceAnswer\n    answer_generated: bool\n    answer_render_ready: bool\n    unsupported_claims_generated: bool\n    free_form_generation_used: bool\n    multi_turn_memory_enabled: bool\n    persistent_memory_enabled: bool\n    learning_update_performed: bool\n    analytics_execution_performed: bool\n    database_access_performed: bool\n    runtime_artifact_created: bool\n    runtime_artifact_modified: bool\n    networking_performed: bool\n    publication_allowed: bool\n    action_authorization_allowed: bool\n    qseries_execution_allowed: bool\n    read_only: bool\n    failure_reason: str | None\n    report_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    raise OracleTerminalIntelligenceAnswerInvariantError(\n        f"unsupported answer value type: "\n        f"{type(value).__module__}.{type(value).__qualname__}"\n    )\n\n\ndef _stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=True,\n        allow_nan=False,\n    ).encode("utf-8")\n    return hashlib.sha256(payload).hexdigest()\n\n\ndef _format_value(value: Any) -> str:\n    if value is None:\n        return "null"\n    if isinstance(value, bool):\n        return "true" if value else "false"\n    if isinstance(value, float):\n        return format(value, ".12g")\n    if isinstance(value, (str, int)):\n        return str(value)\n    return json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=True,\n        allow_nan=False,\n    )\n\n\ndef _answer_line(\n    *,\n    index: int,\n    line_type: str,\n    text: str,\n    fields: tuple[OracleProjectedIntelligenceField, ...],\n) -> OracleTerminalIntelligenceAnswerLine:\n    body = {\n        "line_index": index,\n        "line_type": line_type,\n        "text": text,\n        "source_field_paths": tuple(\n            field.source_field_path for field in fields\n        ),\n        "source_field_hashes": tuple(\n            field.projected_field_hash for field in fields\n        ),\n        "evidence_linked": bool(fields),\n    }\n    line = OracleTerminalIntelligenceAnswerLine(\n        **body,\n        line_hash=_stable_hash(body),\n    )\n    verify_answer_line(line)\n    return line\n\n\ndef _classify_field(field: OracleProjectedIntelligenceField) -> str:\n    lowered = (\n        field.context_key.lower()\n        + " "\n        + field.source_field_path.lower()\n    )\n    if any(token in lowered for token in ("evidence", "source", "confidence")):\n        return "evidence"\n    if any(token in lowered for token in ("uncertainty", "risk", "contradiction")):\n        return "uncertainty"\n    return "fact"\n\n\ndef _build_lines(\n    report: OracleNaturalLanguageIntelligenceProjectionReport,\n) -> tuple[OracleTerminalIntelligenceAnswerLine, ...]:\n    projection = report.projection\n    fields = projection.projected_fields\n    lines: list[OracleTerminalIntelligenceAnswerLine] = []\n\n    summary_text = (\n        f"Oracle found {len(fields)} certified context field"\n        f"{\'\' if len(fields) == 1 else \'s\'} relevant to the query."\n    )\n    lines.append(\n        _answer_line(\n            index=0,\n            line_type="summary",\n            text=summary_text,\n            fields=tuple(fields),\n        )\n    )\n\n    ordered = sorted(\n        fields,\n        key=lambda field: (\n            -field.match_score,\n            field.source_field_path,\n            field.projected_field_hash,\n        ),\n    )\n\n    for field in ordered:\n        line_type = _classify_field(field)\n        text = (\n            f"{field.context_key}: "\n            f"{_format_value(field.canonical_value)}"\n        )\n        lines.append(\n            _answer_line(\n                index=len(lines),\n                line_type=line_type,\n                text=text,\n                fields=(field,),\n            )\n        )\n\n    if not any(line.line_type == "uncertainty" for line in lines):\n        uncertainty_fields = tuple(\n            field\n            for field in ordered\n            if any(\n                token in (\n                    field.context_key.lower()\n                    + " "\n                    + field.source_field_path.lower()\n                )\n                for token in (\n                    "confidence",\n                    "probability",\n                    "risk",\n                    "uncertainty",\n                )\n            )\n        )\n        if uncertainty_fields:\n            lines.append(\n                _answer_line(\n                    index=len(lines),\n                    line_type="uncertainty",\n                    text=(\n                        "Uncertainty remains bounded by the certified "\n                        "probability and confidence fields shown above."\n                    ),\n                    fields=uncertainty_fields,\n                )\n            )\n\n    if len(lines) > MAX_ANSWER_LINES:\n        raise OracleTerminalIntelligenceAnswerInvariantError(\n            "answer line limit exceeded"\n        )\n\n    return tuple(lines)\n\n\ndef verify_answer_line(\n    line: OracleTerminalIntelligenceAnswerLine,\n) -> bool:\n    body = asdict(line)\n    supplied = body.pop("line_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleTerminalIntelligenceAnswerInvariantError(\n            "answer line hash mismatch"\n        )\n    if line.line_index < 0:\n        raise OracleTerminalIntelligenceAnswerInvariantError(\n            "answer line index invalid"\n        )\n    if line.line_type not in {\n        "summary",\n        "fact",\n        "evidence",\n        "uncertainty",\n    }:\n        raise OracleTerminalIntelligenceAnswerInvariantError(\n            "answer line type invalid"\n        )\n    if not line.text:\n        raise OracleTerminalIntelligenceAnswerInvariantError(\n            "answer line text missing"\n        )\n    if len(line.source_field_paths) != len(line.source_field_hashes):\n        raise OracleTerminalIntelligenceAnswerInvariantError(\n            "answer line lineage count mismatch"\n        )\n    if line.evidence_linked != bool(line.source_field_paths):\n        raise OracleTerminalIntelligenceAnswerInvariantError(\n            "answer line evidence state mismatch"\n        )\n    return True\n\n\ndef verify_terminal_intelligence_answer(\n    answer: OracleTerminalIntelligenceAnswer,\n) -> bool:\n    body = asdict(answer)\n    supplied = body.pop("answer_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleTerminalIntelligenceAnswerInvariantError(\n            "answer hash mismatch"\n        )\n    if answer.answer_line_count != len(answer.answer_lines):\n        raise OracleTerminalIntelligenceAnswerInvariantError(\n            "answer line count mismatch"\n        )\n    for index, line in enumerate(answer.answer_lines):\n        verify_answer_line(line)\n        if line.line_index != index:\n            raise OracleTerminalIntelligenceAnswerInvariantError(\n                "answer line ordering mismatch"\n            )\n    if answer.evidence_line_count != sum(\n        line.line_type == "evidence"\n        for line in answer.answer_lines\n    ):\n        raise OracleTerminalIntelligenceAnswerInvariantError(\n            "evidence line count mismatch"\n        )\n    if answer.summary_line_count != sum(\n        line.line_type == "summary"\n        for line in answer.answer_lines\n    ):\n        raise OracleTerminalIntelligenceAnswerInvariantError(\n            "summary line count mismatch"\n        )\n    if answer.uncertainty_line_count != sum(\n        line.line_type == "uncertainty"\n        for line in answer.answer_lines\n    ):\n        raise OracleTerminalIntelligenceAnswerInvariantError(\n            "uncertainty line count mismatch"\n        )\n    if answer.all_claims_evidence_linked != all(\n        line.evidence_linked\n        for line in answer.answer_lines\n    ):\n        raise OracleTerminalIntelligenceAnswerInvariantError(\n            "answer evidence-link state mismatch"\n        )\n    if answer.bounded_answer != (\n        answer.answer_line_count <= MAX_ANSWER_LINES\n    ):\n        raise OracleTerminalIntelligenceAnswerInvariantError(\n            "bounded answer state mismatch"\n        )\n    expected_ready = bool(\n        answer.answer_lines\n        and answer.all_claims_evidence_linked\n        and answer.deterministic_ordering_applied\n        and answer.bounded_answer\n        and answer.read_only\n    )\n    if answer.answer_ready != expected_ready:\n        raise OracleTerminalIntelligenceAnswerInvariantError(\n            "answer readiness mismatch"\n        )\n    return True\n\n\ndef build_terminal_intelligence_answer_generation_report(\n    repository_root: str | Path,\n    *,\n    projection_report: OracleNaturalLanguageIntelligenceProjectionReport,\n) -> OracleTerminalIntelligenceAnswerGenerationReport:\n    root = Path(repository_root).resolve()\n    verify_natural_language_intelligence_projection_report(\n        projection_report\n    )\n\n    if not projection_report.answer_generation_ready:\n        raise OracleTerminalIntelligenceAnswerInvariantError(\n            projection_report.failure_reason\n            or "projection is not answer-generation ready"\n        )\n\n    projection = projection_report.projection\n    lines = _build_lines(projection_report)\n\n    answer_body = {\n        "answer_id": _stable_hash(\n            {\n                "projection_hash": projection.projection_hash,\n                "answer_lines": lines,\n            }\n        )[:24],\n        "source_projection_hash": projection.projection_hash,\n        "source_projection_report_hash": projection_report.report_hash,\n        "query": projection.query_intent.normalized_query,\n        "answer_lines": lines,\n        "answer_line_count": len(lines),\n        "evidence_line_count": sum(\n            line.line_type == "evidence"\n            for line in lines\n        ),\n        "summary_line_count": sum(\n            line.line_type == "summary"\n            for line in lines\n        ),\n        "uncertainty_line_count": sum(\n            line.line_type == "uncertainty"\n            for line in lines\n        ),\n        "all_claims_evidence_linked": all(\n            line.evidence_linked for line in lines\n        ),\n        "deterministic_ordering_applied": True,\n        "bounded_answer": len(lines) <= MAX_ANSWER_LINES,\n        "answer_ready": bool(\n            lines\n            and all(line.evidence_linked for line in lines)\n            and len(lines) <= MAX_ANSWER_LINES\n        ),\n        "read_only": True,\n    }\n    answer = OracleTerminalIntelligenceAnswer(\n        **answer_body,\n        answer_hash=_stable_hash(answer_body),\n    )\n    verify_terminal_intelligence_answer(answer)\n\n    report_body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root),\n        "projection_report_hash": projection_report.report_hash,\n        "answer": answer,\n        "answer_generated": answer.answer_ready,\n        "answer_render_ready": answer.answer_ready,\n        "unsupported_claims_generated": False,\n        "free_form_generation_used": False,\n        "multi_turn_memory_enabled": False,\n        "persistent_memory_enabled": False,\n        "learning_update_performed": False,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "runtime_artifact_created": False,\n        "runtime_artifact_modified": False,\n        "networking_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "read_only": True,\n        "failure_reason": (\n            None if answer.answer_ready\n            else "answer_generation_failed"\n        ),\n    }\n    report = OracleTerminalIntelligenceAnswerGenerationReport(\n        **report_body,\n        report_hash=_stable_hash(report_body),\n    )\n    verify_terminal_intelligence_answer_generation_report(\n        report\n    )\n    return report\n\n\ndef verify_terminal_intelligence_answer_generation_report(\n    report: OracleTerminalIntelligenceAnswerGenerationReport,\n) -> bool:\n    body = asdict(report)\n    supplied = body.pop("report_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleTerminalIntelligenceAnswerInvariantError(\n            "answer generation report hash mismatch"\n        )\n    if report.schema_version != SCHEMA_VERSION:\n        raise OracleTerminalIntelligenceAnswerInvariantError(\n            "answer schema mismatch"\n        )\n    if report.policy_id != POLICY_ID:\n        raise OracleTerminalIntelligenceAnswerInvariantError(\n            "answer policy mismatch"\n        )\n\n    verify_terminal_intelligence_answer(report.answer)\n\n    if not report.read_only:\n        raise OracleTerminalIntelligenceAnswerInvariantError(\n            "answer generation report is not read-only"\n        )\n\n    if (\n        report.unsupported_claims_generated\n        or report.free_form_generation_used\n        or report.multi_turn_memory_enabled\n        or report.persistent_memory_enabled\n        or report.learning_update_performed\n        or report.analytics_execution_performed\n        or report.database_access_performed\n        or report.runtime_artifact_created\n        or report.runtime_artifact_modified\n        or report.networking_performed\n        or report.publication_allowed\n        or report.action_authorization_allowed\n        or report.qseries_execution_allowed\n    ):\n        raise OracleTerminalIntelligenceAnswerInvariantError(\n            "forbidden answer capability enabled"\n        )\n\n    expected = bool(\n        report.answer.answer_ready\n        and report.answer.all_claims_evidence_linked\n        and report.answer.bounded_answer\n    )\n    if report.answer_generated != expected:\n        raise OracleTerminalIntelligenceAnswerInvariantError(\n            "answer generated state mismatch"\n        )\n    if report.answer_render_ready != expected:\n        raise OracleTerminalIntelligenceAnswerInvariantError(\n            "answer render readiness mismatch"\n        )\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import replace\nfrom pathlib import Path\nfrom tempfile import TemporaryDirectory\n\nfrom qseries_v2.oracle_terminal.oracle_natural_language_intelligence_response_projection import (\n    ENGINE_ID as OIT_041_ENGINE_ID,\n    POLICY_ID as OIT_041_POLICY_ID,\n    SCHEMA_VERSION as OIT_041_SCHEMA_VERSION,\n    OracleIntelligenceQueryIntent,\n    OracleNaturalLanguageIntelligenceProjection,\n    OracleNaturalLanguageIntelligenceProjectionReport,\n    OracleProjectedIntelligenceField,\n    _stable_hash as oit_041_hash,\n    verify_natural_language_intelligence_projection_report,\n)\nfrom qseries_v2.oracle_terminal.oracle_terminal_intelligence_answer_generation import (\n    OracleTerminalIntelligenceAnswerInvariantError,\n    build_terminal_intelligence_answer_generation_report,\n    verify_terminal_intelligence_answer_generation_report,\n)\n\n\ndef projected_field(\n    key: str,\n    path: str,\n    field_type: str,\n    value,\n    text: str,\n    terms: tuple[str, ...],\n    score: int,\n    reason: str,\n    ordinal: int,\n):\n    body = {\n        "context_key": key,\n        "source_field_path": path,\n        "source_context_field_hash": f"context-field-{ordinal}",\n        "field_type": field_type,\n        "canonical_value": value,\n        "searchable_text": text,\n        "match_terms": terms,\n        "match_score": score,\n        "selection_reason": reason,\n        "projection_ordinal": ordinal,\n    }\n    return OracleProjectedIntelligenceField(\n        **body,\n        projected_field_hash=oit_041_hash(body),\n    )\n\n\ndef make_projection_report(root: Path):\n    intent_body = {\n        "raw_query": "What evidence supports the bull direction?",\n        "normalized_query": "What evidence supports the bull direction?",\n        "query_terms": (\n            "what",\n            "evidence",\n            "supports",\n            "the",\n            "bull",\n            "direction",\n        ),\n        "distinctive_terms": (\n            "evidence",\n            "supports",\n            "bull",\n            "direction",\n        ),\n        "requested_field_names": ("direction",),\n        "broad_context_requested": False,\n        "evidence_requested": True,\n        "query_valid": True,\n    }\n    intent = OracleIntelligenceQueryIntent(\n        **intent_body,\n        intent_hash=oit_041_hash(intent_body),\n    )\n\n    fields = (\n        projected_field(\n            "direction",\n            "$.direction",\n            "string",\n            "bull",\n            "bull",\n            ("bull", "direction"),\n            120,\n            "exact_field_request",\n            0,\n        ),\n        projected_field(\n            "evidence.0.source_id",\n            "$.evidence[0].source_id",\n            "string",\n            "SOURCE-ALPHA",\n            "SOURCE-ALPHA",\n            ("evidence",),\n            35,\n            "distinctive_term_match+evidence_request",\n            1,\n        ),\n        projected_field(\n            "evidence.0.confidence",\n            "$.evidence[0].confidence",\n            "number",\n            0.84,\n            "0.84",\n            ("evidence",),\n            35,\n            "distinctive_term_match+evidence_request",\n            2,\n        ),\n        projected_field(\n            "probability",\n            "$.probability",\n            "number",\n            0.78,\n            "0.78",\n            (),\n            1,\n            "root_context",\n            3,\n        ),\n    )\n\n    projection_body = {\n        "projection_id": "projection-042",\n        "source_context_hash": "context-hash",\n        "source_context_report_hash": "context-report-hash",\n        "query_intent": intent,\n        "projected_fields": fields,\n        "projected_field_count": len(fields),\n        "evidence_field_count": 2,\n        "exact_field_match_count": 1,\n        "term_match_count": 3,\n        "bounded_projection": True,\n        "source_lineage_preserved": True,\n        "deterministic_ordering_applied": True,\n        "projection_ready": True,\n        "read_only": True,\n    }\n    projection = OracleNaturalLanguageIntelligenceProjection(\n        **projection_body,\n        projection_hash=oit_041_hash(projection_body),\n    )\n\n    report_body = {\n        "schema_version": OIT_041_SCHEMA_VERSION,\n        "engine_id": OIT_041_ENGINE_ID,\n        "policy_id": OIT_041_POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root.resolve()),\n        "context_assembly_report_hash": "context-report-hash",\n        "projection": projection,\n        "query_accepted": True,\n        "relevant_context_found": True,\n        "answer_generation_ready": True,\n        "free_form_answer_generated": False,\n        "multi_turn_memory_enabled": False,\n        "persistent_memory_enabled": False,\n        "learning_update_performed": False,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "runtime_artifact_created": False,\n        "runtime_artifact_modified": False,\n        "networking_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "read_only": True,\n        "failure_reason": None,\n    }\n    report = OracleNaturalLanguageIntelligenceProjectionReport(\n        **report_body,\n        report_hash=oit_041_hash(report_body),\n    )\n    verify_natural_language_intelligence_projection_report(report)\n    return report\n\n\ndef main() -> int:\n    print("=" * 48)\n    print(" OIT-042 TEST")\n    print(" TERMINAL INTELLIGENCE ANSWER GENERATION")\n    print("=" * 48)\n\n    with TemporaryDirectory() as temporary:\n        root = Path(temporary)\n        projection = make_projection_report(root)\n\n        report = build_terminal_intelligence_answer_generation_report(\n            root,\n            projection_report=projection,\n        )\n\n        assert report.answer_generated\n        assert report.answer_render_ready\n        assert not report.unsupported_claims_generated\n        assert not report.free_form_generation_used\n\n        answer = report.answer\n        assert answer.answer_ready\n        assert answer.bounded_answer\n        assert answer.all_claims_evidence_linked\n        assert answer.summary_line_count == 1\n        assert answer.evidence_line_count == 2\n        assert answer.uncertainty_line_count == 1\n        assert answer.answer_line_count == 6\n\n        texts = tuple(line.text for line in answer.answer_lines)\n        assert texts[0] == (\n            "Oracle found 4 certified context fields relevant to the query."\n        )\n        assert "direction: bull" in texts\n        assert "evidence.0.source_id: SOURCE-ALPHA" in texts\n        assert "evidence.0.confidence: 0.84" in texts\n        assert "probability: 0.78" in texts\n        assert texts[-1].startswith(\n            "Uncertainty remains bounded"\n        )\n\n        for line in answer.answer_lines:\n            assert line.evidence_linked\n            assert line.source_field_paths\n            assert line.source_field_hashes\n\n        replay = build_terminal_intelligence_answer_generation_report(\n            root,\n            projection_report=projection,\n        )\n        assert replay == report\n        assert verify_terminal_intelligence_answer_generation_report(\n            report\n        )\n\n        tampered = replace(\n            report,\n            unsupported_claims_generated=True,\n        )\n        try:\n            verify_terminal_intelligence_answer_generation_report(\n                tampered\n            )\n        except OracleTerminalIntelligenceAnswerInvariantError:\n            pass\n        else:\n            raise AssertionError(\n                "tampered answer generation report accepted"\n            )\n\n        assert not report.multi_turn_memory_enabled\n        assert not report.persistent_memory_enabled\n        assert not report.learning_update_performed\n        assert not report.analytics_execution_performed\n        assert not report.database_access_performed\n        assert not report.runtime_artifact_created\n        assert not report.runtime_artifact_modified\n        assert not report.networking_performed\n        assert not report.publication_allowed\n        assert not report.action_authorization_allowed\n        assert not report.qseries_execution_allowed\n        assert report.read_only\n\n    print("[PASS] Certified OIT-041 projection consumed")\n    print("[PASS] Deterministic answer summary generated")\n    print("[PASS] Projected facts rendered")\n    print("[PASS] Evidence fields rendered")\n    print("[PASS] Probability and confidence uncertainty surfaced")\n    print("[PASS] Every answer line bound to source fields")\n    print("[PASS] Unsupported claims remained forbidden")\n    print("[PASS] Free-form generation remained disabled")\n    print("[PASS] Bounded answer line limit enforced")\n    print("[PASS] Answer deterministic across replay")\n    print("[PASS] Tampered answer report rejected")\n    print("[PASS] Multi-turn memory and learning remained disabled")\n    print("[PASS] No analytics execution or runtime mutation performed")\n    print("[PASS] Publication, action authorization, and Q Series execution disabled")\n    print("[DONE] OIT-042 TERMINAL INTELLIGENCE ANSWER GENERATION PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


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

    for path in (OIT_041, OIT_041_TEST, RUNNER):
        if path.is_file():
            protected[path] = sha256(path)

    return protected


def main() -> int:
    print("=" * 48)
    print(" OIT-042 INSTALLER")
    print(" TERMINAL INTELLIGENCE ANSWER GENERATION")
    print("=" * 48)

    try:
        require_contract(
            OIT_041,
            (
                'SCHEMA_VERSION = "OIT-041"',
                'POLICY_ID = "oracle.natural-language-intelligence-response-projection.v1"',
                "OracleProjectedIntelligenceField",
                "OracleNaturalLanguageIntelligenceProjection",
                "OracleNaturalLanguageIntelligenceProjectionReport",
                "verify_natural_language_intelligence_projection_report",
                "answer_generation_ready",
                "free_form_answer_generated",
            ),
            "Certified OIT-041 production",
        )
        require_contract(
            OIT_041_TEST,
            (
                "OIT-041 TEST",
                "NATURAL-LANGUAGE INTELLIGENCE RESPONSE PROJECTION",
                "OIT-041 NATURAL-LANGUAGE RESPONSE PROJECTION PASS",
            ),
            "Certified OIT-041 standalone test",
        )

        protected = protected_sources()

        print("[OK] Certified OIT-041 production contract verified")
        print("[OK] Certified OIT-041 standalone test verified")
        print(f"[OK] Protected production source files captured: {len(protected)}")

        upstream = subprocess.run(
            [sys.executable, str(OIT_041_TEST)],
            cwd=ROOT,
            check=False,
        )
        if upstream.returncode:
            raise RuntimeError(
                f"OIT-041 certification failed with exit code {upstream.returncode}"
            )

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_terminal_intelligence_answer_generation import *"
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
                f"OIT-042 test failed with exit code {completed.returncode}"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Protected production source changed: {path}"
                )

        print("[PASS] Certified OIT-041 production and test unchanged")
        print("[PASS] Oracle terminal runner unchanged")
        print("[PASS] OIT-042 production module installed")
        print("[PASS] OIT-042 standalone test installed")
        print("[PASS] Deterministic evidence-linked answer generation certified")
        print("[PASS] Unsupported claim generation prohibited")
        print("[PASS] Free-form generation remained disabled")
        print("[PASS] Multi-turn memory and learning remained disabled")
        print("[PASS] No analytics execution or runtime mutation performed")
        print("[PASS] OLA, OIA, INT-OII, ORR, OOR, and Q Series unchanged")
        print("[PASS] Publication and execution remained disabled")
        print("[PASS] Read-only and execution boundaries preserved")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OIT-042 TERMINAL INTELLIGENCE ANSWER GENERATION INSTALLED")
        return 0

    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
