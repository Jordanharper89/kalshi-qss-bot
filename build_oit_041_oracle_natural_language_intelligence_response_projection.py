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
            / "oracle_intelligence_session_context_assembly.py"
        )
        test = (
            candidate
            / "test_oit_040_oracle_intelligence_session_context_assembly.py"
        )
        if production.is_file() and test.is_file():
            return candidate

    raise SystemExit("[ERROR] Could not locate current Q Series repository.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"
OIT_040 = (
    PACKAGE
    / "oracle_intelligence_session_context_assembly.py"
)
OIT_040_TEST = (
    ROOT
    / "test_oit_040_oracle_intelligence_session_context_assembly.py"
)
PRODUCTION = (
    PACKAGE
    / "oracle_natural_language_intelligence_response_projection.py"
)
TEST = (
    ROOT
    / "test_oit_041_oracle_natural_language_intelligence_response_projection.py"
)
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport json\nimport re\nfrom dataclasses import asdict, dataclass\nfrom pathlib import Path\nfrom typing import Any, Mapping, Sequence\n\nfrom .oracle_intelligence_session_context_assembly import (\n    OracleIntelligenceContextField,\n    OracleIntelligenceSessionContext,\n    OracleIntelligenceSessionContextAssemblyReport,\n    OracleIntelligenceSessionContextInvariantError,\n    verify_context_field,\n    verify_intelligence_session_context_assembly_report,\n    verify_session_context,\n)\n\nSCHEMA_VERSION = "OIT-041"\nENGINE_ID = "OIT-041"\nPOLICY_ID = "oracle.natural-language-intelligence-response-projection.v1"\n\nMAX_QUERY_LENGTH = 2000\nMAX_SELECTED_FIELDS = 64\n\nGENERIC_TERMS = frozenset(\n    {\n        "a",\n        "an",\n        "and",\n        "are",\n        "as",\n        "at",\n        "be",\n        "by",\n        "do",\n        "does",\n        "for",\n        "from",\n        "give",\n        "how",\n        "i",\n        "in",\n        "intelligence",\n        "is",\n        "it",\n        "market",\n        "me",\n        "of",\n        "on",\n        "or",\n        "show",\n        "tell",\n        "that",\n        "the",\n        "this",\n        "to",\n        "what",\n        "which",\n        "with",\n    }\n)\n\n\nclass OracleIntelligenceResponseProjectionInvariantError(\n    OracleIntelligenceSessionContextInvariantError\n):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleIntelligenceQueryIntent:\n    raw_query: str\n    normalized_query: str\n    query_terms: tuple[str, ...]\n    distinctive_terms: tuple[str, ...]\n    requested_field_names: tuple[str, ...]\n    broad_context_requested: bool\n    evidence_requested: bool\n    query_valid: bool\n    intent_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleProjectedIntelligenceField:\n    context_key: str\n    source_field_path: str\n    source_context_field_hash: str\n    field_type: str\n    canonical_value: Any\n    searchable_text: str\n    match_terms: tuple[str, ...]\n    match_score: int\n    selection_reason: str\n    projection_ordinal: int\n    projected_field_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleNaturalLanguageIntelligenceProjection:\n    projection_id: str\n    source_context_hash: str\n    source_context_report_hash: str\n    query_intent: OracleIntelligenceQueryIntent\n    projected_fields: tuple[OracleProjectedIntelligenceField, ...]\n    projected_field_count: int\n    evidence_field_count: int\n    exact_field_match_count: int\n    term_match_count: int\n    bounded_projection: bool\n    source_lineage_preserved: bool\n    deterministic_ordering_applied: bool\n    projection_ready: bool\n    read_only: bool\n    projection_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleNaturalLanguageIntelligenceProjectionReport:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    status: str\n    repository_root: str\n    context_assembly_report_hash: str\n    projection: OracleNaturalLanguageIntelligenceProjection\n    query_accepted: bool\n    relevant_context_found: bool\n    answer_generation_ready: bool\n    free_form_answer_generated: bool\n    multi_turn_memory_enabled: bool\n    persistent_memory_enabled: bool\n    learning_update_performed: bool\n    analytics_execution_performed: bool\n    database_access_performed: bool\n    runtime_artifact_created: bool\n    runtime_artifact_modified: bool\n    networking_performed: bool\n    publication_allowed: bool\n    action_authorization_allowed: bool\n    qseries_execution_allowed: bool\n    read_only: bool\n    failure_reason: str | None\n    report_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    raise OracleIntelligenceResponseProjectionInvariantError(\n        f"unsupported projection value type: "\n        f"{type(value).__module__}.{type(value).__qualname__}"\n    )\n\n\ndef _stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=True,\n        allow_nan=False,\n    ).encode("utf-8")\n    return hashlib.sha256(payload).hexdigest()\n\n\ndef _terms(value: str) -> tuple[str, ...]:\n    return tuple(\n        re.findall(r"[a-z0-9]+", str(value).lower())\n    )\n\n\ndef _normalize_query(query: str) -> str:\n    return " ".join(str(query).strip().split())\n\n\ndef _build_query_intent(\n    query: str,\n    context: OracleIntelligenceSessionContext,\n) -> OracleIntelligenceQueryIntent:\n    normalized = _normalize_query(query)\n    query_terms = _terms(normalized)\n    distinctive = tuple(\n        term\n        for term in query_terms\n        if term not in GENERIC_TERMS and len(term) > 1\n    )\n\n    context_names = {\n        field.context_key.lower()\n        for field in context.context_fields\n    }\n    requested = tuple(\n        sorted(\n            name\n            for name in context_names\n            if any(\n                part in query_terms\n                for part in _terms(name)\n            )\n        )\n    )\n\n    broad = bool(\n        not distinctive\n        or any(\n            phrase in normalized.lower()\n            for phrase in (\n                "show everything",\n                "full context",\n                "all fields",\n                "complete intelligence",\n                "overview",\n                "summary",\n            )\n        )\n    )\n    evidence_requested = any(\n        term in query_terms\n        for term in (\n            "evidence",\n            "source",\n            "sources",\n            "support",\n            "proof",\n            "confidence",\n        )\n    )\n    valid = bool(\n        normalized\n        and len(normalized) <= MAX_QUERY_LENGTH\n        and query_terms\n    )\n\n    body = {\n        "raw_query": str(query),\n        "normalized_query": normalized,\n        "query_terms": query_terms,\n        "distinctive_terms": distinctive,\n        "requested_field_names": requested,\n        "broad_context_requested": broad,\n        "evidence_requested": evidence_requested,\n        "query_valid": valid,\n    }\n    intent = OracleIntelligenceQueryIntent(\n        **body,\n        intent_hash=_stable_hash(body),\n    )\n    verify_query_intent(intent)\n    return intent\n\n\ndef verify_query_intent(\n    intent: OracleIntelligenceQueryIntent,\n) -> bool:\n    body = asdict(intent)\n    supplied = body.pop("intent_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleIntelligenceResponseProjectionInvariantError(\n            "query intent hash mismatch"\n        )\n    expected_valid = bool(\n        intent.normalized_query\n        and len(intent.normalized_query) <= MAX_QUERY_LENGTH\n        and intent.query_terms\n    )\n    if intent.query_valid != expected_valid:\n        raise OracleIntelligenceResponseProjectionInvariantError(\n            "query validity mismatch"\n        )\n    if tuple(_terms(intent.normalized_query)) != intent.query_terms:\n        raise OracleIntelligenceResponseProjectionInvariantError(\n            "query term normalization mismatch"\n        )\n    return True\n\n\ndef _score_context_field(\n    field: OracleIntelligenceContextField,\n    intent: OracleIntelligenceQueryIntent,\n) -> tuple[int, tuple[str, ...], str]:\n    key_terms = set(_terms(field.context_key))\n    path_terms = set(_terms(field.source_field_path))\n    text_terms = set(_terms(field.searchable_text))\n    distinctive = set(intent.distinctive_terms)\n\n    exact_key = field.context_key.lower() in {\n        name.lower()\n        for name in intent.requested_field_names\n    }\n    matched = tuple(\n        sorted(\n            distinctive.intersection(\n                key_terms | path_terms | text_terms\n            )\n        )\n    )\n\n    score = 0\n    reason = "no_match"\n\n    if exact_key:\n        score += 100\n        reason = "exact_field_request"\n\n    if matched:\n        score += len(matched) * 10\n        if reason == "no_match":\n            reason = "distinctive_term_match"\n\n    if intent.evidence_requested and any(\n        token in field.context_key.lower()\n        or token in field.source_field_path.lower()\n        for token in ("evidence", "source", "confidence")\n    ):\n        score += 25\n        reason = (\n            "evidence_request"\n            if reason == "no_match"\n            else reason + "+evidence_request"\n        )\n\n    if intent.broad_context_requested:\n        score += 1\n        if reason == "no_match":\n            reason = "broad_context"\n\n    if field.source_field_path == "$":\n        score += 1\n        if reason == "no_match":\n            reason = "root_context"\n\n    return score, matched, reason\n\n\ndef _project_field(\n    field: OracleIntelligenceContextField,\n    *,\n    match_terms: tuple[str, ...],\n    score: int,\n    reason: str,\n    ordinal: int,\n) -> OracleProjectedIntelligenceField:\n    verify_context_field(field)\n    body = {\n        "context_key": field.context_key,\n        "source_field_path": field.source_field_path,\n        "source_context_field_hash": (\n            field.context_field_hash\n        ),\n        "field_type": field.field_type,\n        "canonical_value": field.canonical_value,\n        "searchable_text": field.searchable_text,\n        "match_terms": match_terms,\n        "match_score": score,\n        "selection_reason": reason,\n        "projection_ordinal": ordinal,\n    }\n    projected = OracleProjectedIntelligenceField(\n        **body,\n        projected_field_hash=_stable_hash(body),\n    )\n    verify_projected_field(projected)\n    return projected\n\n\ndef verify_projected_field(\n    field: OracleProjectedIntelligenceField,\n) -> bool:\n    body = asdict(field)\n    supplied = body.pop("projected_field_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleIntelligenceResponseProjectionInvariantError(\n            "projected field hash mismatch"\n        )\n    if not field.context_key:\n        raise OracleIntelligenceResponseProjectionInvariantError(\n            "projected context key missing"\n        )\n    if not field.source_field_path:\n        raise OracleIntelligenceResponseProjectionInvariantError(\n            "projected source path missing"\n        )\n    if not field.source_context_field_hash:\n        raise OracleIntelligenceResponseProjectionInvariantError(\n            "projected field lineage missing"\n        )\n    if field.match_score < 0:\n        raise OracleIntelligenceResponseProjectionInvariantError(\n            "projected field score invalid"\n        )\n    if field.projection_ordinal < 0:\n        raise OracleIntelligenceResponseProjectionInvariantError(\n            "projected field ordinal invalid"\n        )\n    return True\n\n\ndef verify_projection(\n    projection: OracleNaturalLanguageIntelligenceProjection,\n) -> bool:\n    body = asdict(projection)\n    supplied = body.pop("projection_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleIntelligenceResponseProjectionInvariantError(\n            "projection hash mismatch"\n        )\n\n    verify_query_intent(projection.query_intent)\n    for index, field in enumerate(projection.projected_fields):\n        verify_projected_field(field)\n        if field.projection_ordinal != index:\n            raise OracleIntelligenceResponseProjectionInvariantError(\n                "projection field ordering mismatch"\n            )\n\n    if projection.projected_field_count != len(\n        projection.projected_fields\n    ):\n        raise OracleIntelligenceResponseProjectionInvariantError(\n            "projected field count mismatch"\n        )\n\n    if projection.evidence_field_count != sum(\n        any(\n            token in field.context_key.lower()\n            or token in field.source_field_path.lower()\n            for token in ("evidence", "source", "confidence")\n        )\n        for field in projection.projected_fields\n    ):\n        raise OracleIntelligenceResponseProjectionInvariantError(\n            "evidence field count mismatch"\n        )\n\n    if projection.exact_field_match_count != sum(\n        "exact_field_request" in field.selection_reason\n        for field in projection.projected_fields\n    ):\n        raise OracleIntelligenceResponseProjectionInvariantError(\n            "exact field match count mismatch"\n        )\n\n    if projection.term_match_count != sum(\n        bool(field.match_terms)\n        for field in projection.projected_fields\n    ):\n        raise OracleIntelligenceResponseProjectionInvariantError(\n            "term match count mismatch"\n        )\n\n    if projection.bounded_projection != (\n        projection.projected_field_count <= MAX_SELECTED_FIELDS\n    ):\n        raise OracleIntelligenceResponseProjectionInvariantError(\n            "bounded projection state mismatch"\n        )\n\n    if not projection.source_lineage_preserved:\n        raise OracleIntelligenceResponseProjectionInvariantError(\n            "projection source lineage incomplete"\n        )\n\n    if not projection.deterministic_ordering_applied:\n        raise OracleIntelligenceResponseProjectionInvariantError(\n            "projection ordering not deterministic"\n        )\n\n    expected_ready = bool(\n        projection.query_intent.query_valid\n        and projection.projected_fields\n        and projection.bounded_projection\n        and projection.source_lineage_preserved\n        and projection.deterministic_ordering_applied\n        and projection.read_only\n    )\n    if projection.projection_ready != expected_ready:\n        raise OracleIntelligenceResponseProjectionInvariantError(\n            "projection readiness mismatch"\n        )\n    return True\n\n\ndef build_natural_language_intelligence_projection_report(\n    repository_root: str | Path,\n    *,\n    context_assembly_report: OracleIntelligenceSessionContextAssemblyReport,\n    query: str,\n) -> OracleNaturalLanguageIntelligenceProjectionReport:\n    root = Path(repository_root).resolve()\n    verify_intelligence_session_context_assembly_report(\n        context_assembly_report\n    )\n\n    if not context_assembly_report.query_planning_ready:\n        raise OracleIntelligenceResponseProjectionInvariantError(\n            context_assembly_report.failure_reason\n            or "session context is not query-planning ready"\n        )\n\n    context = context_assembly_report.session_context\n    verify_session_context(context)\n    intent = _build_query_intent(query, context)\n\n    if not intent.query_valid:\n        raise OracleIntelligenceResponseProjectionInvariantError(\n            "natural-language query is invalid"\n        )\n\n    scored = []\n    for field in context.context_fields:\n        score, matched, reason = _score_context_field(\n            field,\n            intent,\n        )\n        if score > 0:\n            scored.append(\n                (score, field.source_field_path, field, matched, reason)\n            )\n\n    scored.sort(\n        key=lambda item: (\n            -item[0],\n            item[1],\n            item[2].context_field_hash,\n        )\n    )\n    selected = scored[:MAX_SELECTED_FIELDS]\n\n    projected_fields = tuple(\n        _project_field(\n            field,\n            match_terms=matched,\n            score=score,\n            reason=reason,\n            ordinal=index,\n        )\n        for index, (\n            score,\n            _,\n            field,\n            matched,\n            reason,\n        ) in enumerate(selected)\n    )\n\n    lineage_preserved = all(\n        any(\n            projected.source_context_field_hash\n            == source.context_field_hash\n            and projected.source_field_path\n            == source.source_field_path\n            for source in context.context_fields\n        )\n        for projected in projected_fields\n    )\n\n    projection_body = {\n        "projection_id": _stable_hash(\n            {\n                "context_hash": context.context_hash,\n                "query_intent_hash": intent.intent_hash,\n                "projected_fields": projected_fields,\n            }\n        )[:24],\n        "source_context_hash": context.context_hash,\n        "source_context_report_hash": (\n            context_assembly_report.report_hash\n        ),\n        "query_intent": intent,\n        "projected_fields": projected_fields,\n        "projected_field_count": len(projected_fields),\n        "evidence_field_count": sum(\n            any(\n                token in field.context_key.lower()\n                or token in field.source_field_path.lower()\n                for token in (\n                    "evidence",\n                    "source",\n                    "confidence",\n                )\n            )\n            for field in projected_fields\n        ),\n        "exact_field_match_count": sum(\n            "exact_field_request" in field.selection_reason\n            for field in projected_fields\n        ),\n        "term_match_count": sum(\n            bool(field.match_terms)\n            for field in projected_fields\n        ),\n        "bounded_projection": (\n            len(projected_fields) <= MAX_SELECTED_FIELDS\n        ),\n        "source_lineage_preserved": lineage_preserved,\n        "deterministic_ordering_applied": True,\n        "projection_ready": bool(\n            intent.query_valid\n            and projected_fields\n            and lineage_preserved\n            and len(projected_fields) <= MAX_SELECTED_FIELDS\n        ),\n        "read_only": True,\n    }\n    projection = OracleNaturalLanguageIntelligenceProjection(\n        **projection_body,\n        projection_hash=_stable_hash(projection_body),\n    )\n    verify_projection(projection)\n\n    report_body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root),\n        "context_assembly_report_hash": (\n            context_assembly_report.report_hash\n        ),\n        "projection": projection,\n        "query_accepted": intent.query_valid,\n        "relevant_context_found": bool(projected_fields),\n        "answer_generation_ready": projection.projection_ready,\n        "free_form_answer_generated": False,\n        "multi_turn_memory_enabled": False,\n        "persistent_memory_enabled": False,\n        "learning_update_performed": False,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "runtime_artifact_created": False,\n        "runtime_artifact_modified": False,\n        "networking_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "read_only": True,\n        "failure_reason": (\n            None\n            if projection.projection_ready\n            else "relevant_context_not_found"\n        ),\n    }\n    report = OracleNaturalLanguageIntelligenceProjectionReport(\n        **report_body,\n        report_hash=_stable_hash(report_body),\n    )\n    verify_natural_language_intelligence_projection_report(\n        report\n    )\n    return report\n\n\ndef verify_natural_language_intelligence_projection_report(\n    report: OracleNaturalLanguageIntelligenceProjectionReport,\n) -> bool:\n    body = asdict(report)\n    supplied = body.pop("report_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleIntelligenceResponseProjectionInvariantError(\n            "projection report hash mismatch"\n        )\n    if report.schema_version != SCHEMA_VERSION:\n        raise OracleIntelligenceResponseProjectionInvariantError(\n            "projection schema mismatch"\n        )\n    if report.policy_id != POLICY_ID:\n        raise OracleIntelligenceResponseProjectionInvariantError(\n            "projection policy mismatch"\n        )\n\n    verify_projection(report.projection)\n\n    if not report.read_only:\n        raise OracleIntelligenceResponseProjectionInvariantError(\n            "projection report is not read-only"\n        )\n\n    if (\n        report.free_form_answer_generated\n        or report.multi_turn_memory_enabled\n        or report.persistent_memory_enabled\n        or report.learning_update_performed\n        or report.analytics_execution_performed\n        or report.database_access_performed\n        or report.runtime_artifact_created\n        or report.runtime_artifact_modified\n        or report.networking_performed\n        or report.publication_allowed\n        or report.action_authorization_allowed\n        or report.qseries_execution_allowed\n    ):\n        raise OracleIntelligenceResponseProjectionInvariantError(\n            "forbidden projection capability enabled"\n        )\n\n    if report.query_accepted != (\n        report.projection.query_intent.query_valid\n    ):\n        raise OracleIntelligenceResponseProjectionInvariantError(\n            "query acceptance mismatch"\n        )\n\n    if report.relevant_context_found != bool(\n        report.projection.projected_fields\n    ):\n        raise OracleIntelligenceResponseProjectionInvariantError(\n            "relevant context state mismatch"\n        )\n\n    expected = bool(\n        report.query_accepted\n        and report.relevant_context_found\n        and report.projection.projection_ready\n    )\n    if report.answer_generation_ready != expected:\n        raise OracleIntelligenceResponseProjectionInvariantError(\n            "answer generation readiness mismatch"\n        )\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import replace\nfrom pathlib import Path\nfrom tempfile import TemporaryDirectory\n\nfrom qseries_v2.oracle_terminal.oracle_intelligence_session_context_assembly import (\n    ENGINE_ID as OIT_040_ENGINE_ID,\n    POLICY_ID as OIT_040_POLICY_ID,\n    SCHEMA_VERSION as OIT_040_SCHEMA_VERSION,\n    OracleIntelligenceContextField,\n    OracleIntelligenceSessionContext,\n    OracleIntelligenceSessionContextAssemblyReport,\n    _stable_hash as oit_040_hash,\n    verify_intelligence_session_context_assembly_report,\n)\nfrom qseries_v2.oracle_terminal.oracle_natural_language_intelligence_response_projection import (\n    OracleIntelligenceResponseProjectionInvariantError,\n    build_natural_language_intelligence_projection_report,\n    verify_natural_language_intelligence_projection_report,\n)\n\n\ndef context_field(\n    key: str,\n    path: str,\n    field_type: str,\n    value,\n    text: str,\n    ordinal: int,\n):\n    body = {\n        "context_key": key,\n        "source_field_path": path,\n        "source_field_hash": f"source-field-{ordinal}",\n        "field_type": field_type,\n        "canonical_value": value,\n        "searchable_text": text,\n        "ordinal": ordinal,\n    }\n    return OracleIntelligenceContextField(\n        **body,\n        context_field_hash=oit_040_hash(body),\n    )\n\n\ndef make_context_report(root: Path):\n    fields = (\n        context_field(\n            "root",\n            "$",\n            "mapping",\n            {\n                "record_id": "REAL-041",\n                "probability": 0.78,\n                "direction": "bull",\n            },\n            \'{"direction":"bull","probability":0.78,"record_id":"REAL-041"}\',\n            0,\n        ),\n        context_field(\n            "direction",\n            "$.direction",\n            "string",\n            "bull",\n            "bull",\n            1,\n        ),\n        context_field(\n            "evidence.0.source_id",\n            "$.evidence[0].source_id",\n            "string",\n            "SOURCE-ALPHA",\n            "SOURCE-ALPHA",\n            2,\n        ),\n        context_field(\n            "evidence.0.confidence",\n            "$.evidence[0].confidence",\n            "number",\n            0.84,\n            "0.84",\n            3,\n        ),\n        context_field(\n            "probability",\n            "$.probability",\n            "number",\n            0.78,\n            "0.78",\n            4,\n        ),\n        context_field(\n            "record_id",\n            "$.record_id",\n            "string",\n            "REAL-041",\n            "REAL-041",\n            5,\n        ),\n    )\n\n    context_body = {\n        "context_id": "context-041",\n        "source_normalization_report_hash": "normalization-report-hash",\n        "source_normalized_record_hash": "normalized-record-hash",\n        "source_envelope_hash": "source-envelope-hash",\n        "source_execution_report_hash": "execution-report-hash",\n        "source_validation_report_hash": "validation-report-hash",\n        "source_invocation_result_hash": "invocation-result-hash",\n        "context_fields": fields,\n        "context_field_count": len(fields),\n        "searchable_field_count": len(fields),\n        "root_field_present": True,\n        "deterministic_ordering_applied": True,\n        "full_lineage_preserved": True,\n        "bounded_context": True,\n        "context_ready": True,\n        "read_only": True,\n    }\n    context = OracleIntelligenceSessionContext(\n        **context_body,\n        context_hash=oit_040_hash(context_body),\n    )\n\n    report_body = {\n        "schema_version": OIT_040_SCHEMA_VERSION,\n        "engine_id": OIT_040_ENGINE_ID,\n        "policy_id": OIT_040_POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root.resolve()),\n        "normalization_report_hash": "normalization-report-hash",\n        "session_context": context,\n        "context_assembled": True,\n        "query_planning_ready": True,\n        "multi_turn_memory_enabled": False,\n        "persistent_memory_enabled": False,\n        "learning_update_performed": False,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "runtime_artifact_created": False,\n        "runtime_artifact_modified": False,\n        "networking_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "read_only": True,\n        "failure_reason": None,\n    }\n    report = OracleIntelligenceSessionContextAssemblyReport(\n        **report_body,\n        report_hash=oit_040_hash(report_body),\n    )\n    verify_intelligence_session_context_assembly_report(report)\n    return report\n\n\ndef main() -> int:\n    print("=" * 48)\n    print(" OIT-041 TEST")\n    print(" NATURAL-LANGUAGE INTELLIGENCE RESPONSE PROJECTION")\n    print("=" * 48)\n\n    with TemporaryDirectory() as temporary:\n        root = Path(temporary)\n        context_report = make_context_report(root)\n\n        report = build_natural_language_intelligence_projection_report(\n            root,\n            context_assembly_report=context_report,\n            query="What evidence supports the bull direction?",\n        )\n\n        assert report.query_accepted\n        assert report.relevant_context_found\n        assert report.answer_generation_ready\n        assert not report.free_form_answer_generated\n\n        projection = report.projection\n        assert projection.projection_ready\n        assert projection.bounded_projection\n        assert projection.source_lineage_preserved\n        assert projection.deterministic_ordering_applied\n        assert projection.projected_field_count > 0\n        assert projection.evidence_field_count >= 2\n        assert projection.term_match_count >= 1\n\n        selected_paths = tuple(\n            field.source_field_path\n            for field in projection.projected_fields\n        )\n        assert "$.direction" in selected_paths\n        assert "$.evidence[0].source_id" in selected_paths\n        assert "$.evidence[0].confidence" in selected_paths\n\n        first = projection.projected_fields[0]\n        assert first.match_score >= (\n            projection.projected_fields[-1].match_score\n        )\n\n        exact_report = build_natural_language_intelligence_projection_report(\n            root,\n            context_assembly_report=context_report,\n            query="Show probability",\n        )\n        assert exact_report.projection.exact_field_match_count == 1\n        assert exact_report.projection.projected_fields[0].context_key == (\n            "probability"\n        )\n\n        broad_report = build_natural_language_intelligence_projection_report(\n            root,\n            context_assembly_report=context_report,\n            query="Give me an overview",\n        )\n        assert broad_report.projection.projected_field_count == 6\n\n        replay = build_natural_language_intelligence_projection_report(\n            root,\n            context_assembly_report=context_report,\n            query="What evidence supports the bull direction?",\n        )\n        assert replay == report\n        assert verify_natural_language_intelligence_projection_report(\n            report\n        )\n\n        tampered = replace(\n            report,\n            free_form_answer_generated=True,\n        )\n        try:\n            verify_natural_language_intelligence_projection_report(\n                tampered\n            )\n        except OracleIntelligenceResponseProjectionInvariantError:\n            pass\n        else:\n            raise AssertionError(\n                "tampered projection report accepted"\n            )\n\n        assert not report.multi_turn_memory_enabled\n        assert not report.persistent_memory_enabled\n        assert not report.learning_update_performed\n        assert not report.analytics_execution_performed\n        assert not report.database_access_performed\n        assert not report.runtime_artifact_created\n        assert not report.runtime_artifact_modified\n        assert not report.networking_performed\n        assert not report.publication_allowed\n        assert not report.action_authorization_allowed\n        assert not report.qseries_execution_allowed\n        assert report.read_only\n\n    print("[PASS] Certified OIT-040 session context consumed")\n    print("[PASS] Natural-language query normalized")\n    print("[PASS] Distinctive query terms extracted")\n    print("[PASS] Exact field requests detected")\n    print("[PASS] Evidence-related context prioritized")\n    print("[PASS] Broad overview projection supported")\n    print("[PASS] Deterministic field scoring and ordering certified")\n    print("[PASS] Full source context lineage retained")\n    print("[PASS] Bounded projection enforced")\n    print("[PASS] Answer-generation readiness certified")\n    print("[PASS] Free-form answer generation remained disabled")\n    print("[PASS] Multi-turn memory and learning remained disabled")\n    print("[PASS] Projection deterministic across replay")\n    print("[PASS] Tampered projection report rejected")\n    print("[PASS] No analytics execution or runtime mutation performed")\n    print("[PASS] Publication, action authorization, and Q Series execution disabled")\n    print("[DONE] OIT-041 NATURAL-LANGUAGE RESPONSE PROJECTION PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


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

    for path in (OIT_040, OIT_040_TEST, RUNNER):
        if path.is_file():
            protected[path] = sha256(path)

    return protected


def main() -> int:
    print("=" * 48)
    print(" OIT-041 INSTALLER")
    print(" NATURAL-LANGUAGE INTELLIGENCE RESPONSE PROJECTION")
    print("=" * 48)

    try:
        require_contract(
            OIT_040,
            (
                'SCHEMA_VERSION = "OIT-040"',
                'POLICY_ID = "oracle.intelligence-session-context-assembly.v1"',
                "OracleIntelligenceContextField",
                "OracleIntelligenceSessionContext",
                "OracleIntelligenceSessionContextAssemblyReport",
                "verify_context_field",
                "verify_session_context",
                "verify_intelligence_session_context_assembly_report",
                "query_planning_ready",
                "multi_turn_memory_enabled",
                "persistent_memory_enabled",
            ),
            "Certified OIT-040 production",
        )
        require_contract(
            OIT_040_TEST,
            (
                "OIT-040 TEST",
                "INTELLIGENCE SESSION CONTEXT ASSEMBLY",
                "OIT-040 INTELLIGENCE SESSION CONTEXT ASSEMBLY PASS",
            ),
            "Certified OIT-040 standalone test",
        )

        protected = protected_sources()

        print("[OK] Certified OIT-040 production contract verified")
        print("[OK] Certified OIT-040 standalone test verified")
        print(f"[OK] Protected production source files captured: {len(protected)}")

        upstream = subprocess.run(
            [sys.executable, str(OIT_040_TEST)],
            cwd=ROOT,
            check=False,
        )
        if upstream.returncode:
            raise RuntimeError(
                f"OIT-040 certification failed with exit code {upstream.returncode}"
            )

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_natural_language_intelligence_response_projection import *"
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
                f"OIT-041 test failed with exit code {completed.returncode}"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Protected production source changed: {path}"
                )

        print("[PASS] Certified OIT-040 production and test unchanged")
        print("[PASS] Oracle terminal runner unchanged")
        print("[PASS] OIT-041 production module installed")
        print("[PASS] OIT-041 standalone test installed")
        print("[PASS] Natural-language intent extraction certified")
        print("[PASS] Evidence-linked context projection certified")
        print("[PASS] Exact-field and broad-context selection certified")
        print("[PASS] Deterministic bounded projection certified")
        print("[PASS] Free-form answer generation remained disabled")
        print("[PASS] Memory and learning remained disabled")
        print("[PASS] No analytics execution or runtime mutation performed")
        print("[PASS] OLA, OIA, INT-OII, ORR, OOR, and Q Series unchanged")
        print("[PASS] Publication and execution remained disabled")
        print("[PASS] Read-only and execution boundaries preserved")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OIT-041 NATURAL-LANGUAGE RESPONSE PROJECTION INSTALLED")
        return 0

    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
