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
        normalization = (
            package
            / "oracle_certified_real_intelligence_normalization.py"
        )
        envelope = (
            package
            / "oracle_certified_real_intelligence_source_envelope.py"
        )
        test = (
            candidate
            / "test_oit_039_oracle_certified_real_intelligence_normalization.py"
        )
        if normalization.is_file() and envelope.is_file() and test.is_file():
            return candidate

    raise SystemExit("[ERROR] Could not locate current Q Series repository.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"
OIT_039_ENVELOPE = (
    PACKAGE
    / "oracle_certified_real_intelligence_source_envelope.py"
)
OIT_039_NORMALIZATION = (
    PACKAGE
    / "oracle_certified_real_intelligence_normalization.py"
)
OIT_039_TEST = (
    ROOT
    / "test_oit_039_oracle_certified_real_intelligence_normalization.py"
)
PRODUCTION = (
    PACKAGE
    / "oracle_intelligence_session_context_assembly.py"
)
TEST = (
    ROOT
    / "test_oit_040_oracle_intelligence_session_context_assembly.py"
)
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass\nfrom pathlib import Path\nfrom typing import Any, Mapping\n\nfrom .oracle_certified_real_intelligence_source_envelope import (\n    OracleRealIntelligenceSourceEnvelope,\n    verify_real_intelligence_source_envelope,\n)\nfrom .oracle_certified_real_intelligence_normalization import (\n    OracleNormalizedIntelligenceField,\n    OracleNormalizedIntelligenceRecord,\n    OracleRealIntelligenceNormalizationInvariantError,\n    OracleRealIntelligenceNormalizationReport,\n    verify_normalized_field,\n    verify_normalized_record,\n    verify_real_intelligence_normalization_report,\n)\n\nSCHEMA_VERSION = "OIT-040"\nENGINE_ID = "OIT-040"\nPOLICY_ID = "oracle.intelligence-session-context-assembly.v1"\n\nCONTEXT_FIELD_LIMIT = 4096\n\n\nclass OracleIntelligenceSessionContextInvariantError(\n    OracleRealIntelligenceNormalizationInvariantError\n):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleIntelligenceContextField:\n    context_key: str\n    source_field_path: str\n    source_field_hash: str\n    field_type: str\n    canonical_value: Any\n    searchable_text: str\n    ordinal: int\n    context_field_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleIntelligenceSessionContext:\n    context_id: str\n    source_normalization_report_hash: str\n    source_normalized_record_hash: str\n    source_envelope_hash: str\n    source_execution_report_hash: str\n    source_validation_report_hash: str\n    source_invocation_result_hash: str\n    context_fields: tuple[OracleIntelligenceContextField, ...]\n    context_field_count: int\n    searchable_field_count: int\n    root_field_present: bool\n    deterministic_ordering_applied: bool\n    full_lineage_preserved: bool\n    bounded_context: bool\n    context_ready: bool\n    read_only: bool\n    context_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleIntelligenceSessionContextAssemblyReport:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    status: str\n    repository_root: str\n    normalization_report_hash: str\n    session_context: OracleIntelligenceSessionContext\n    context_assembled: bool\n    query_planning_ready: bool\n    multi_turn_memory_enabled: bool\n    persistent_memory_enabled: bool\n    learning_update_performed: bool\n    analytics_execution_performed: bool\n    database_access_performed: bool\n    runtime_artifact_created: bool\n    runtime_artifact_modified: bool\n    networking_performed: bool\n    publication_allowed: bool\n    action_authorization_allowed: bool\n    qseries_execution_allowed: bool\n    read_only: bool\n    failure_reason: str | None\n    report_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    raise OracleIntelligenceSessionContextInvariantError(\n        f"unsupported context value type: "\n        f"{type(value).__module__}.{type(value).__qualname__}"\n    )\n\n\ndef _stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=True,\n        allow_nan=False,\n    ).encode("utf-8")\n    return hashlib.sha256(payload).hexdigest()\n\n\ndef _searchable_text(value: Any) -> str:\n    if value is None:\n        return ""\n    if isinstance(value, bool):\n        return "true" if value else "false"\n    if isinstance(value, (str, int, float)):\n        return str(value)\n    return json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=True,\n        allow_nan=False,\n    )\n\n\ndef _context_key(field_path: str) -> str:\n    if field_path == "$":\n        return "root"\n    value = field_path[2:] if field_path.startswith("$.") else field_path\n    value = value.replace("[", ".").replace("]", "")\n    pieces = [\n        piece.strip().lower()\n        for piece in value.split(".")\n        if piece.strip()\n    ]\n    return ".".join(pieces)\n\n\ndef _assemble_context_field(\n    field: OracleNormalizedIntelligenceField,\n    ordinal: int,\n) -> OracleIntelligenceContextField:\n    verify_normalized_field(field)\n    body = {\n        "context_key": _context_key(field.field_path),\n        "source_field_path": field.field_path,\n        "source_field_hash": field.field_hash,\n        "field_type": field.field_type,\n        "canonical_value": field.canonical_value,\n        "searchable_text": _searchable_text(field.canonical_value),\n        "ordinal": ordinal,\n    }\n    context_field = OracleIntelligenceContextField(\n        **body,\n        context_field_hash=_stable_hash(body),\n    )\n    verify_context_field(context_field)\n    return context_field\n\n\ndef verify_context_field(\n    field: OracleIntelligenceContextField,\n) -> bool:\n    body = asdict(field)\n    supplied = body.pop("context_field_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleIntelligenceSessionContextInvariantError(\n            "context field hash mismatch"\n        )\n    if not field.context_key:\n        raise OracleIntelligenceSessionContextInvariantError(\n            "context field key missing"\n        )\n    if not field.source_field_path or not field.source_field_hash:\n        raise OracleIntelligenceSessionContextInvariantError(\n            "context field lineage missing"\n        )\n    if field.ordinal < 0:\n        raise OracleIntelligenceSessionContextInvariantError(\n            "context field ordinal invalid"\n        )\n    return True\n\n\ndef verify_session_context(\n    context: OracleIntelligenceSessionContext,\n) -> bool:\n    body = asdict(context)\n    supplied = body.pop("context_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleIntelligenceSessionContextInvariantError(\n            "session context hash mismatch"\n        )\n    if not context.context_id:\n        raise OracleIntelligenceSessionContextInvariantError(\n            "session context ID missing"\n        )\n    if context.context_field_count != len(context.context_fields):\n        raise OracleIntelligenceSessionContextInvariantError(\n            "session context field count mismatch"\n        )\n    for index, field in enumerate(context.context_fields):\n        verify_context_field(field)\n        if field.ordinal != index:\n            raise OracleIntelligenceSessionContextInvariantError(\n                "session context field ordering mismatch"\n            )\n    if context.searchable_field_count != sum(\n        bool(field.searchable_text)\n        for field in context.context_fields\n    ):\n        raise OracleIntelligenceSessionContextInvariantError(\n            "searchable field count mismatch"\n        )\n    if context.root_field_present != any(\n        field.source_field_path == "$"\n        for field in context.context_fields\n    ):\n        raise OracleIntelligenceSessionContextInvariantError(\n            "root field presence mismatch"\n        )\n    if not context.deterministic_ordering_applied:\n        raise OracleIntelligenceSessionContextInvariantError(\n            "deterministic context ordering not applied"\n        )\n    if not context.full_lineage_preserved:\n        raise OracleIntelligenceSessionContextInvariantError(\n            "session context lineage incomplete"\n        )\n    if context.bounded_context != (\n        context.context_field_count <= CONTEXT_FIELD_LIMIT\n    ):\n        raise OracleIntelligenceSessionContextInvariantError(\n            "bounded context state mismatch"\n        )\n    expected_ready = bool(\n        context.context_fields\n        and context.root_field_present\n        and context.deterministic_ordering_applied\n        and context.full_lineage_preserved\n        and context.bounded_context\n        and context.read_only\n    )\n    if context.context_ready != expected_ready:\n        raise OracleIntelligenceSessionContextInvariantError(\n            "session context readiness mismatch"\n        )\n    return True\n\n\ndef build_intelligence_session_context_assembly_report(\n    repository_root: str | Path,\n    *,\n    normalization_report: OracleRealIntelligenceNormalizationReport,\n) -> OracleIntelligenceSessionContextAssemblyReport:\n    root = Path(repository_root).resolve()\n    verify_real_intelligence_normalization_report(\n        normalization_report\n    )\n\n    if not normalization_report.normalized_record_available:\n        raise OracleIntelligenceSessionContextInvariantError(\n            normalization_report.failure_reason\n            or "normalized record unavailable"\n        )\n\n    record: OracleNormalizedIntelligenceRecord = (\n        normalization_report.normalized_record\n    )\n    verify_normalized_record(record)\n\n    ordered_fields = tuple(\n        sorted(\n            record.normalized_fields,\n            key=lambda field: (\n                field.field_path,\n                field.field_hash,\n            ),\n        )\n    )\n    context_fields = tuple(\n        _assemble_context_field(field, index)\n        for index, field in enumerate(ordered_fields)\n    )\n\n    lineage_preserved = bool(\n        record.source_envelope_hash\n        == normalization_report.source_envelope_hash\n        and all(\n            field.source_envelope_hash\n            == record.source_envelope_hash\n            for field in record.normalized_fields\n        )\n        and all(\n            context_field.source_field_hash\n            == normalized_field.field_hash\n            for context_field, normalized_field in zip(\n                context_fields,\n                ordered_fields,\n            )\n        )\n    )\n\n    context_body = {\n        "context_id": _stable_hash(\n            {\n                "normalization_report_hash": (\n                    normalization_report.report_hash\n                ),\n                "normalized_record_hash": record.record_hash,\n                "context_fields": context_fields,\n            }\n        )[:24],\n        "source_normalization_report_hash": (\n            normalization_report.report_hash\n        ),\n        "source_normalized_record_hash": record.record_hash,\n        "source_envelope_hash": record.source_envelope_hash,\n        "source_execution_report_hash": (\n            record.source_execution_report_hash\n        ),\n        "source_validation_report_hash": (\n            record.source_validation_report_hash\n        ),\n        "source_invocation_result_hash": (\n            record.source_invocation_result_hash\n        ),\n        "context_fields": context_fields,\n        "context_field_count": len(context_fields),\n        "searchable_field_count": sum(\n            bool(field.searchable_text)\n            for field in context_fields\n        ),\n        "root_field_present": any(\n            field.source_field_path == "$"\n            for field in context_fields\n        ),\n        "deterministic_ordering_applied": True,\n        "full_lineage_preserved": lineage_preserved,\n        "bounded_context": len(context_fields) <= CONTEXT_FIELD_LIMIT,\n        "context_ready": bool(\n            context_fields\n            and lineage_preserved\n            and len(context_fields) <= CONTEXT_FIELD_LIMIT\n            and any(\n                field.source_field_path == "$"\n                for field in context_fields\n            )\n        ),\n        "read_only": True,\n    }\n    context = OracleIntelligenceSessionContext(\n        **context_body,\n        context_hash=_stable_hash(context_body),\n    )\n    verify_session_context(context)\n\n    report_body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root),\n        "normalization_report_hash": (\n            normalization_report.report_hash\n        ),\n        "session_context": context,\n        "context_assembled": context.context_ready,\n        "query_planning_ready": context.context_ready,\n        "multi_turn_memory_enabled": False,\n        "persistent_memory_enabled": False,\n        "learning_update_performed": False,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "runtime_artifact_created": False,\n        "runtime_artifact_modified": False,\n        "networking_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "read_only": True,\n        "failure_reason": (\n            None if context.context_ready\n            else "session_context_not_ready"\n        ),\n    }\n    report = OracleIntelligenceSessionContextAssemblyReport(\n        **report_body,\n        report_hash=_stable_hash(report_body),\n    )\n    verify_intelligence_session_context_assembly_report(report)\n    return report\n\n\ndef verify_intelligence_session_context_assembly_report(\n    report: OracleIntelligenceSessionContextAssemblyReport,\n) -> bool:\n    body = asdict(report)\n    supplied = body.pop("report_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleIntelligenceSessionContextInvariantError(\n            "session context assembly report hash mismatch"\n        )\n    if report.schema_version != SCHEMA_VERSION:\n        raise OracleIntelligenceSessionContextInvariantError(\n            "session context schema mismatch"\n        )\n    if report.policy_id != POLICY_ID:\n        raise OracleIntelligenceSessionContextInvariantError(\n            "session context policy mismatch"\n        )\n    verify_session_context(report.session_context)\n    if not report.read_only:\n        raise OracleIntelligenceSessionContextInvariantError(\n            "session context report is not read-only"\n        )\n    if (\n        report.multi_turn_memory_enabled\n        or report.persistent_memory_enabled\n        or report.learning_update_performed\n        or report.analytics_execution_performed\n        or report.database_access_performed\n        or report.runtime_artifact_created\n        or report.runtime_artifact_modified\n        or report.networking_performed\n        or report.publication_allowed\n        or report.action_authorization_allowed\n        or report.qseries_execution_allowed\n    ):\n        raise OracleIntelligenceSessionContextInvariantError(\n            "forbidden context capability enabled"\n        )\n    expected = bool(\n        report.session_context.context_ready\n        and report.session_context.full_lineage_preserved\n        and report.session_context.bounded_context\n    )\n    if report.context_assembled != expected:\n        raise OracleIntelligenceSessionContextInvariantError(\n            "context assembly state mismatch"\n        )\n    if report.query_planning_ready != expected:\n        raise OracleIntelligenceSessionContextInvariantError(\n            "query planning readiness mismatch"\n        )\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import replace\nfrom pathlib import Path\nfrom tempfile import TemporaryDirectory\n\nfrom qseries_v2.oracle_terminal.oracle_certified_real_intelligence_source_envelope import (\n    ENGINE_ID as ENVELOPE_ENGINE_ID,\n    POLICY_ID as ENVELOPE_POLICY_ID,\n    SCHEMA_VERSION as ENVELOPE_SCHEMA_VERSION,\n    OracleRealIntelligenceSourceEnvelope,\n    _stable_hash as envelope_hash,\n)\nfrom qseries_v2.oracle_terminal.oracle_certified_real_intelligence_normalization import (\n    ENGINE_ID as NORMALIZATION_ENGINE_ID,\n    POLICY_ID as NORMALIZATION_POLICY_ID,\n    SCHEMA_VERSION as NORMALIZATION_SCHEMA_VERSION,\n    OracleNormalizedIntelligenceField,\n    OracleNormalizedIntelligenceRecord,\n    OracleRealIntelligenceNormalizationReport,\n    _stable_hash as normalization_hash,\n    verify_real_intelligence_normalization_report,\n)\nfrom qseries_v2.oracle_terminal.oracle_intelligence_session_context_assembly import (\n    OracleIntelligenceSessionContextInvariantError,\n    build_intelligence_session_context_assembly_report,\n    verify_intelligence_session_context_assembly_report,\n)\n\n\ndef normalized_field(\n    path: str,\n    name: str,\n    field_type: str,\n    value,\n    source_result_hash: str,\n    source_envelope_hash: str,\n):\n    body = {\n        "field_path": path,\n        "field_name": name,\n        "field_type": field_type,\n        "canonical_value": value,\n        "source_result_hash": source_result_hash,\n        "source_envelope_hash": source_envelope_hash,\n    }\n    return OracleNormalizedIntelligenceField(\n        **body,\n        field_hash=normalization_hash(body),\n    )\n\n\ndef make_normalization_report(root: Path):\n    canonical_result = {\n        "record_id": "REAL-040",\n        "probability": 0.76,\n        "direction": "bull",\n        "read_only": True,\n    }\n    invocation_result_hash = envelope_hash(canonical_result)\n\n    envelope_body = {\n        "schema_version": ENVELOPE_SCHEMA_VERSION,\n        "engine_id": ENVELOPE_ENGINE_ID,\n        "policy_id": ENVELOPE_POLICY_ID,\n        "execution_report_hash": "execution-report-hash",\n        "validation_report_hash": "validation-report-hash",\n        "invocation_result_hash": invocation_result_hash,\n        "canonical_result": canonical_result,\n        "canonical_result_hash": invocation_result_hash,\n        "execution_validation_lineage_verified": True,\n        "source_result_preserved": True,\n        "read_only": True,\n    }\n    envelope = OracleRealIntelligenceSourceEnvelope(\n        **envelope_body,\n        envelope_hash=envelope_hash(envelope_body),\n    )\n\n    fields = (\n        normalized_field(\n            "$",\n            "$",\n            "mapping",\n            canonical_result,\n            invocation_result_hash,\n            envelope.envelope_hash,\n        ),\n        normalized_field(\n            "$.direction",\n            "direction",\n            "string",\n            "bull",\n            invocation_result_hash,\n            envelope.envelope_hash,\n        ),\n        normalized_field(\n            "$.probability",\n            "probability",\n            "number",\n            0.76,\n            invocation_result_hash,\n            envelope.envelope_hash,\n        ),\n        normalized_field(\n            "$.read_only",\n            "read_only",\n            "boolean",\n            True,\n            invocation_result_hash,\n            envelope.envelope_hash,\n        ),\n        normalized_field(\n            "$.record_id",\n            "record_id",\n            "string",\n            "REAL-040",\n            invocation_result_hash,\n            envelope.envelope_hash,\n        ),\n    )\n\n    record_body = {\n        "record_id": "normalized-record-040",\n        "source_execution_report_hash": (\n            envelope.execution_report_hash\n        ),\n        "source_validation_report_hash": (\n            envelope.validation_report_hash\n        ),\n        "source_envelope_hash": envelope.envelope_hash,\n        "source_invocation_result_hash": invocation_result_hash,\n        "normalized_fields": fields,\n        "normalized_field_count": len(fields),\n        "root_type": "builtins.dict",\n        "lossy_coercion_performed": False,\n        "source_structure_preserved": True,\n        "deterministic_ordering_applied": True,\n        "normalization_complete": True,\n    }\n    record = OracleNormalizedIntelligenceRecord(\n        **record_body,\n        record_hash=normalization_hash(record_body),\n    )\n\n    report_body = {\n        "schema_version": NORMALIZATION_SCHEMA_VERSION,\n        "engine_id": NORMALIZATION_ENGINE_ID,\n        "policy_id": NORMALIZATION_POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root.resolve()),\n        "source_envelope_hash": envelope.envelope_hash,\n        "normalized_record": record,\n        "normalized_record_available": True,\n        "source_result_preserved": True,\n        "source_response_modified": False,\n        "lossy_coercion_performed": False,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "runtime_artifact_created": False,\n        "runtime_artifact_modified": False,\n        "networking_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "read_only": True,\n        "failure_reason": None,\n    }\n    report = OracleRealIntelligenceNormalizationReport(\n        **report_body,\n        report_hash=normalization_hash(report_body),\n    )\n    verify_real_intelligence_normalization_report(report)\n    return report\n\n\ndef main() -> int:\n    print("=" * 48)\n    print(" OIT-040 TEST")\n    print(" INTELLIGENCE SESSION CONTEXT ASSEMBLY")\n    print("=" * 48)\n\n    with TemporaryDirectory() as temporary:\n        root = Path(temporary)\n        normalization = make_normalization_report(root)\n\n        report = build_intelligence_session_context_assembly_report(\n            root,\n            normalization_report=normalization,\n        )\n\n        assert report.context_assembled\n        assert report.query_planning_ready\n        assert not report.multi_turn_memory_enabled\n        assert not report.persistent_memory_enabled\n        assert not report.learning_update_performed\n\n        context = report.session_context\n        assert context.context_ready\n        assert context.bounded_context\n        assert context.full_lineage_preserved\n        assert context.root_field_present\n        assert context.deterministic_ordering_applied\n        assert context.context_field_count == 5\n        assert context.searchable_field_count == 5\n\n        paths = tuple(\n            field.source_field_path\n            for field in context.context_fields\n        )\n        assert paths == (\n            "$",\n            "$.direction",\n            "$.probability",\n            "$.read_only",\n            "$.record_id",\n        )\n\n        keys = tuple(\n            field.context_key\n            for field in context.context_fields\n        )\n        assert keys == (\n            "root",\n            "direction",\n            "probability",\n            "read_only",\n            "record_id",\n        )\n\n        values = {\n            field.context_key: field.searchable_text\n            for field in context.context_fields\n        }\n        assert values["direction"] == "bull"\n        assert values["probability"] == "0.76"\n        assert values["read_only"] == "true"\n        assert values["record_id"] == "REAL-040"\n\n        replay = build_intelligence_session_context_assembly_report(\n            root,\n            normalization_report=normalization,\n        )\n        assert replay == report\n        assert verify_intelligence_session_context_assembly_report(\n            report\n        )\n\n        tampered = replace(\n            report,\n            persistent_memory_enabled=True,\n        )\n        try:\n            verify_intelligence_session_context_assembly_report(\n                tampered\n            )\n        except OracleIntelligenceSessionContextInvariantError:\n            pass\n        else:\n            raise AssertionError(\n                "tampered context assembly report accepted"\n            )\n\n        assert not report.analytics_execution_performed\n        assert not report.database_access_performed\n        assert not report.runtime_artifact_created\n        assert not report.runtime_artifact_modified\n        assert not report.networking_performed\n        assert not report.publication_allowed\n        assert not report.action_authorization_allowed\n        assert not report.qseries_execution_allowed\n        assert report.read_only\n\n    print("[PASS] Certified OIT-039 normalization report consumed")\n    print("[PASS] Deterministic session context assembled")\n    print("[PASS] Exact normalized-field ordering retained")\n    print("[PASS] Searchable context text materialized")\n    print("[PASS] Root context field preserved")\n    print("[PASS] Full OIT-037 through OIT-039 lineage retained")\n    print("[PASS] Bounded context limit enforced")\n    print("[PASS] Query-planning readiness certified")\n    print("[PASS] Multi-turn and persistent memory remained disabled")\n    print("[PASS] Learning updates remained disabled")\n    print("[PASS] Context deterministic across replay")\n    print("[PASS] Tampered context report rejected")\n    print("[PASS] No analytics execution or database access performed")\n    print("[PASS] No runtime artifact created or modified")\n    print("[PASS] Publication, action authorization, and Q Series execution disabled")\n    print("[DONE] OIT-040 INTELLIGENCE SESSION CONTEXT ASSEMBLY PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


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

    for path in (
        OIT_039_ENVELOPE,
        OIT_039_NORMALIZATION,
        OIT_039_TEST,
        RUNNER,
    ):
        if path.is_file():
            protected[path] = sha256(path)

    return protected


def main() -> int:
    print("=" * 48)
    print(" OIT-040 INSTALLER")
    print(" INTELLIGENCE SESSION CONTEXT ASSEMBLY")
    print("=" * 48)

    try:
        require_contract(
            OIT_039_ENVELOPE,
            (
                'SCHEMA_VERSION = "OIT-039"',
                'POLICY_ID = "oracle.certified-real-intelligence-source-envelope.v1"',
                "OracleRealIntelligenceSourceEnvelope",
                "verify_real_intelligence_source_envelope",
                "execution_validation_lineage_verified",
            ),
            "Certified OIT-039 source envelope",
        )
        require_contract(
            OIT_039_NORMALIZATION,
            (
                'SCHEMA_VERSION = "OIT-039"',
                'POLICY_ID = "oracle.certified-real-intelligence-normalization.v2"',
                "OracleNormalizedIntelligenceField",
                "OracleNormalizedIntelligenceRecord",
                "OracleRealIntelligenceNormalizationReport",
                "verify_normalized_field",
                "verify_normalized_record",
                "verify_real_intelligence_normalization_report",
                "normalized_record_available",
            ),
            "Certified OIT-039 normalization",
        )
        require_contract(
            OIT_039_TEST,
            (
                "OIT-039 TEST",
                "REPOSITORY-ALIGNED SOURCE ENVELOPE",
                "OIT-039 CERTIFIED REAL INTELLIGENCE NORMALIZATION PASS",
            ),
            "Certified OIT-039 standalone test",
        )

        protected = protected_sources()

        print("[OK] Certified OIT-039 source-envelope contract verified")
        print("[OK] Certified OIT-039 normalization contract verified")
        print("[OK] Certified OIT-039 standalone test verified")
        print(f"[OK] Protected production source files captured: {len(protected)}")

        upstream = subprocess.run(
            [sys.executable, str(OIT_039_TEST)],
            cwd=ROOT,
            check=False,
        )
        if upstream.returncode:
            raise RuntimeError(
                f"OIT-039 certification failed with exit code {upstream.returncode}"
            )

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_intelligence_session_context_assembly import *"
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
                f"OIT-040 test failed with exit code {completed.returncode}"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Protected production source changed: {path}"
                )

        print("[PASS] Certified OIT-039 production and test unchanged")
        print("[PASS] Oracle terminal runner unchanged")
        print("[PASS] OIT-040 production module installed")
        print("[PASS] OIT-040 standalone test installed")
        print("[PASS] Deterministic session-context assembly certified")
        print("[PASS] Full normalized-field lineage retained")
        print("[PASS] Searchable read-only context certified")
        print("[PASS] Multi-turn memory and persistent memory remained disabled")
        print("[PASS] Learning updates remained disabled")
        print("[PASS] No analytics execution or runtime mutation performed")
        print("[PASS] OLA, OIA, INT-OII, ORR, OOR, and Q Series unchanged")
        print("[PASS] Publication and execution remained disabled")
        print("[PASS] Read-only and execution boundaries preserved")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OIT-040 INTELLIGENCE SESSION CONTEXT ASSEMBLY INSTALLED")
        return 0

    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
