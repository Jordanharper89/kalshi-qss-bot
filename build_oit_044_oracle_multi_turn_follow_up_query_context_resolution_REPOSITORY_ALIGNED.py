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
            / "oracle_bounded_multi_turn_intelligence_session_context.py"
        )
        test = (
            candidate
            / "test_oit_043_oracle_bounded_multi_turn_intelligence_session_context.py"
        )
        if production.is_file() and test.is_file():
            return candidate

    raise SystemExit(
        "[ERROR] Could not locate current Q Series repository."
    )


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"

OIT_043 = (
    PACKAGE
    / "oracle_bounded_multi_turn_intelligence_session_context.py"
)
OIT_043_TEST = (
    ROOT
    / "test_oit_043_oracle_bounded_multi_turn_intelligence_session_context.py"
)
PRODUCTION = (
    PACKAGE
    / "oracle_multi_turn_follow_up_query_context_resolution.py"
)
TEST = (
    ROOT
    / "test_oit_044_oracle_multi_turn_follow_up_query_context_resolution.py"
)
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport json\nimport re\nfrom dataclasses import asdict, dataclass\nfrom pathlib import Path\nfrom typing import Any, Mapping\n\nfrom .oracle_bounded_multi_turn_intelligence_session_context import (\n    OracleBoundedMultiTurnSessionContext,\n    OracleBoundedMultiTurnSessionInvariantError,\n    OracleIntelligenceConversationTurn,\n    verify_conversation_turn,\n    verify_multi_turn_session_context,\n)\n\nSCHEMA_VERSION = "OIT-044"\nENGINE_ID = "OIT-044"\nPOLICY_ID = "oracle.multi-turn-follow-up-query-context-resolution.v1"\n\nMAX_FOLLOW_UP_LENGTH = 2000\n\nFOLLOW_UP_TERMS = frozenset(\n    {\n        "it",\n        "that",\n        "this",\n        "they",\n        "them",\n        "those",\n        "these",\n        "same",\n        "still",\n        "changed",\n        "change",\n        "now",\n        "before",\n        "again",\n        "more",\n        "less",\n        "why",\n        "how",\n        "what",\n        "which",\n        "and",\n        "but",\n    }\n)\n\n\nclass OracleFollowUpQueryResolutionInvariantError(\n    OracleBoundedMultiTurnSessionInvariantError\n):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleFollowUpQueryReference:\n    reference_type: str\n    source_turn_index: int\n    source_turn_hash: str\n    source_query: str\n    source_answer_id: str\n    source_answer_hash: str\n    reference_text: str\n    reference_score: int\n    reference_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleResolvedFollowUpQuery:\n    raw_query: str\n    normalized_query: str\n    query_terms: tuple[str, ...]\n    follow_up_detected: bool\n    standalone_query: bool\n    referenced_turns: tuple[OracleFollowUpQueryReference, ...]\n    referenced_turn_count: int\n    primary_reference_turn_index: int | None\n    resolved_query: str\n    resolution_confidence: float\n    session_lineage_preserved: bool\n    resolution_ready: bool\n    read_only: bool\n    resolution_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleFollowUpQueryResolutionReport:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    status: str\n    repository_root: str\n    source_session_context_hash: str\n    resolved_follow_up_query: OracleResolvedFollowUpQuery\n    context_resolution_performed: bool\n    downstream_projection_ready: bool\n    persistent_memory_enabled: bool\n    learning_update_performed: bool\n    analytics_execution_performed: bool\n    database_access_performed: bool\n    runtime_artifact_created: bool\n    runtime_artifact_modified: bool\n    networking_performed: bool\n    publication_allowed: bool\n    action_authorization_allowed: bool\n    qseries_execution_allowed: bool\n    read_only: bool\n    failure_reason: str | None\n    report_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(\n                value.items(),\n                key=lambda pair: str(pair[0]),\n            )\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if value is None or isinstance(\n        value,\n        (str, int, float, bool),\n    ):\n        return value\n    raise OracleFollowUpQueryResolutionInvariantError(\n        "unsupported follow-up resolution value type: "\n        f"{type(value).__module__}.{type(value).__qualname__}"\n    )\n\n\ndef _stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=True,\n        allow_nan=False,\n    ).encode("utf-8")\n    return hashlib.sha256(payload).hexdigest()\n\n\ndef _normalize_query(query: str) -> str:\n    return " ".join(str(query).strip().split())\n\n\ndef _terms(query: str) -> tuple[str, ...]:\n    return tuple(re.findall(r"[a-z0-9]+", query.lower()))\n\n\ndef _detect_follow_up(\n    normalized_query: str,\n    query_terms: tuple[str, ...],\n) -> bool:\n    if not normalized_query or not query_terms:\n        return False\n\n    if any(term in FOLLOW_UP_TERMS for term in query_terms):\n        return True\n\n    return len(query_terms) <= 4\n\n\ndef _reference_for_turn(\n    turn: OracleIntelligenceConversationTurn,\n    *,\n    current_terms: tuple[str, ...],\n    latest_turn_index: int,\n) -> OracleFollowUpQueryReference:\n    verify_conversation_turn(turn)\n\n    source_terms = set(_terms(turn.query))\n    overlap = len(source_terms.intersection(current_terms))\n\n    distance = latest_turn_index - turn.turn_index\n    recency_score = max(1, 20 - max(0, distance))\n    reference_score = (overlap * 10) + recency_score\n\n    body = {\n        "reference_type": (\n            "latest_turn"\n            if turn.turn_index == latest_turn_index\n            else "prior_turn"\n        ),\n        "source_turn_index": turn.turn_index,\n        "source_turn_hash": turn.turn_hash,\n        "source_query": turn.query,\n        "source_answer_id": turn.answer_id,\n        "source_answer_hash": turn.answer_hash,\n        "reference_text": (\n            f"turn {turn.turn_index}: {turn.query}"\n        ),\n        "reference_score": reference_score,\n    }\n    reference = OracleFollowUpQueryReference(\n        **body,\n        reference_hash=_stable_hash(body),\n    )\n    verify_follow_up_reference(reference)\n    return reference\n\n\ndef verify_follow_up_reference(\n    reference: OracleFollowUpQueryReference,\n) -> bool:\n    body = asdict(reference)\n    supplied = body.pop("reference_hash")\n\n    if _stable_hash(body) != supplied:\n        raise OracleFollowUpQueryResolutionInvariantError(\n            "follow-up reference hash mismatch"\n        )\n\n    if reference.reference_type not in {\n        "latest_turn",\n        "prior_turn",\n    }:\n        raise OracleFollowUpQueryResolutionInvariantError(\n            "follow-up reference type invalid"\n        )\n\n    if reference.source_turn_index < 0:\n        raise OracleFollowUpQueryResolutionInvariantError(\n            "follow-up source turn index invalid"\n        )\n\n    if not reference.source_turn_hash:\n        raise OracleFollowUpQueryResolutionInvariantError(\n            "follow-up source turn lineage missing"\n        )\n\n    if not reference.source_query:\n        raise OracleFollowUpQueryResolutionInvariantError(\n            "follow-up source query missing"\n        )\n\n    if (\n        not reference.source_answer_id\n        or not reference.source_answer_hash\n    ):\n        raise OracleFollowUpQueryResolutionInvariantError(\n            "follow-up source answer identity missing"\n        )\n\n    if reference.reference_score < 0:\n        raise OracleFollowUpQueryResolutionInvariantError(\n            "follow-up reference score invalid"\n        )\n\n    return True\n\n\ndef verify_resolved_follow_up_query(\n    resolved: OracleResolvedFollowUpQuery,\n) -> bool:\n    body = asdict(resolved)\n    supplied = body.pop("resolution_hash")\n\n    if _stable_hash(body) != supplied:\n        raise OracleFollowUpQueryResolutionInvariantError(\n            "resolved follow-up query hash mismatch"\n        )\n\n    if not resolved.normalized_query:\n        raise OracleFollowUpQueryResolutionInvariantError(\n            "normalized follow-up query missing"\n        )\n\n    if len(resolved.normalized_query) > MAX_FOLLOW_UP_LENGTH:\n        raise OracleFollowUpQueryResolutionInvariantError(\n            "follow-up query exceeds length limit"\n        )\n\n    if resolved.query_terms != _terms(\n        resolved.normalized_query\n    ):\n        raise OracleFollowUpQueryResolutionInvariantError(\n            "follow-up query term normalization mismatch"\n        )\n\n    if resolved.follow_up_detected == resolved.standalone_query:\n        raise OracleFollowUpQueryResolutionInvariantError(\n            "follow-up and standalone states conflict"\n        )\n\n    for reference in resolved.referenced_turns:\n        verify_follow_up_reference(reference)\n\n    if resolved.referenced_turn_count != len(\n        resolved.referenced_turns\n    ):\n        raise OracleFollowUpQueryResolutionInvariantError(\n            "follow-up reference count mismatch"\n        )\n\n    if resolved.primary_reference_turn_index is None:\n        if resolved.referenced_turns:\n            raise OracleFollowUpQueryResolutionInvariantError(\n                "follow-up primary reference missing"\n            )\n    elif not any(\n        reference.source_turn_index\n        == resolved.primary_reference_turn_index\n        for reference in resolved.referenced_turns\n    ):\n        raise OracleFollowUpQueryResolutionInvariantError(\n            "follow-up primary reference not present"\n        )\n\n    if not 0.0 <= resolved.resolution_confidence <= 1.0:\n        raise OracleFollowUpQueryResolutionInvariantError(\n            "follow-up resolution confidence outside bounds"\n        )\n\n    expected_ready = bool(\n        resolved.normalized_query\n        and resolved.session_lineage_preserved\n        and resolved.read_only\n        and (\n            resolved.standalone_query\n            or (\n                resolved.follow_up_detected\n                and resolved.referenced_turns\n                and resolved.primary_reference_turn_index\n                is not None\n            )\n        )\n    )\n\n    if resolved.resolution_ready != expected_ready:\n        raise OracleFollowUpQueryResolutionInvariantError(\n            "follow-up resolution readiness mismatch"\n        )\n\n    return True\n\n\ndef resolve_multi_turn_follow_up_query(\n    repository_root: str | Path,\n    *,\n    session_context: OracleBoundedMultiTurnSessionContext,\n    query: str,\n) -> OracleFollowUpQueryResolutionReport:\n    root = Path(repository_root).resolve()\n    verify_multi_turn_session_context(session_context)\n\n    normalized = _normalize_query(query)\n    query_terms = _terms(normalized)\n\n    if not normalized:\n        raise OracleFollowUpQueryResolutionInvariantError(\n            "follow-up query is empty"\n        )\n\n    if len(normalized) > MAX_FOLLOW_UP_LENGTH:\n        raise OracleFollowUpQueryResolutionInvariantError(\n            "follow-up query exceeds maximum length"\n        )\n\n    follow_up_detected = _detect_follow_up(\n        normalized,\n        query_terms,\n    )\n    standalone_query = not follow_up_detected\n\n    references: tuple[OracleFollowUpQueryReference, ...] = ()\n    primary_reference_turn_index: int | None = None\n    resolved_query = normalized\n    resolution_confidence = 1.0 if standalone_query else 0.0\n\n    if follow_up_detected:\n        latest_turn_index = session_context.latest_turn_index\n\n        candidates = tuple(\n            _reference_for_turn(\n                turn,\n                current_terms=query_terms,\n                latest_turn_index=latest_turn_index,\n            )\n            for turn in session_context.turns\n        )\n\n        references = tuple(\n            sorted(\n                candidates,\n                key=lambda reference: (\n                    -reference.reference_score,\n                    -reference.source_turn_index,\n                    reference.reference_hash,\n                ),\n            )[:3]\n        )\n\n        if references:\n            primary = references[0]\n            primary_reference_turn_index = (\n                primary.source_turn_index\n            )\n            resolved_query = (\n                normalized\n                + " [context from prior query: "\n                + primary.source_query\n                + "]"\n            )\n            resolution_confidence = min(\n                1.0,\n                0.5 + (primary.reference_score / 100.0),\n            )\n\n    lineage_preserved = all(\n        any(\n            turn.turn_hash == reference.source_turn_hash\n            and turn.answer_hash\n            == reference.source_answer_hash\n            and turn.answer_id\n            == reference.source_answer_id\n            for turn in session_context.turns\n        )\n        for reference in references\n    )\n\n    resolved_body = {\n        "raw_query": str(query),\n        "normalized_query": normalized,\n        "query_terms": query_terms,\n        "follow_up_detected": follow_up_detected,\n        "standalone_query": standalone_query,\n        "referenced_turns": references,\n        "referenced_turn_count": len(references),\n        "primary_reference_turn_index": (\n            primary_reference_turn_index\n        ),\n        "resolved_query": resolved_query,\n        "resolution_confidence": resolution_confidence,\n        "session_lineage_preserved": lineage_preserved,\n        "resolution_ready": bool(\n            normalized\n            and lineage_preserved\n            and (\n                standalone_query\n                or (\n                    follow_up_detected\n                    and references\n                    and primary_reference_turn_index\n                    is not None\n                )\n            )\n        ),\n        "read_only": True,\n    }\n    resolved = OracleResolvedFollowUpQuery(\n        **resolved_body,\n        resolution_hash=_stable_hash(resolved_body),\n    )\n    verify_resolved_follow_up_query(resolved)\n\n    report_body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root),\n        "source_session_context_hash": (\n            session_context.context_hash\n        ),\n        "resolved_follow_up_query": resolved,\n        "context_resolution_performed": follow_up_detected,\n        "downstream_projection_ready": (\n            resolved.resolution_ready\n        ),\n        "persistent_memory_enabled": False,\n        "learning_update_performed": False,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "runtime_artifact_created": False,\n        "runtime_artifact_modified": False,\n        "networking_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "read_only": True,\n        "failure_reason": (\n            None\n            if resolved.resolution_ready\n            else "follow_up_resolution_not_ready"\n        ),\n    }\n    report = OracleFollowUpQueryResolutionReport(\n        **report_body,\n        report_hash=_stable_hash(report_body),\n    )\n    verify_follow_up_query_resolution_report(report)\n    return report\n\n\ndef verify_follow_up_query_resolution_report(\n    report: OracleFollowUpQueryResolutionReport,\n) -> bool:\n    body = asdict(report)\n    supplied = body.pop("report_hash")\n\n    if _stable_hash(body) != supplied:\n        raise OracleFollowUpQueryResolutionInvariantError(\n            "follow-up query resolution report hash mismatch"\n        )\n\n    if report.schema_version != SCHEMA_VERSION:\n        raise OracleFollowUpQueryResolutionInvariantError(\n            "follow-up resolution schema mismatch"\n        )\n\n    if report.policy_id != POLICY_ID:\n        raise OracleFollowUpQueryResolutionInvariantError(\n            "follow-up resolution policy mismatch"\n        )\n\n    verify_resolved_follow_up_query(\n        report.resolved_follow_up_query\n    )\n\n    if not report.read_only:\n        raise OracleFollowUpQueryResolutionInvariantError(\n            "follow-up resolution report is not read-only"\n        )\n\n    if (\n        report.persistent_memory_enabled\n        or report.learning_update_performed\n        or report.analytics_execution_performed\n        or report.database_access_performed\n        or report.runtime_artifact_created\n        or report.runtime_artifact_modified\n        or report.networking_performed\n        or report.publication_allowed\n        or report.action_authorization_allowed\n        or report.qseries_execution_allowed\n    ):\n        raise OracleFollowUpQueryResolutionInvariantError(\n            "forbidden follow-up capability enabled"\n        )\n\n    if report.context_resolution_performed != (\n        report.resolved_follow_up_query.follow_up_detected\n    ):\n        raise OracleFollowUpQueryResolutionInvariantError(\n            "context resolution state mismatch"\n        )\n\n    if report.downstream_projection_ready != (\n        report.resolved_follow_up_query.resolution_ready\n    ):\n        raise OracleFollowUpQueryResolutionInvariantError(\n            "downstream projection readiness mismatch"\n        )\n\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import replace\nfrom pathlib import Path\nfrom tempfile import TemporaryDirectory\n\nfrom qseries_v2.oracle_terminal.oracle_bounded_multi_turn_intelligence_session_context import (\n    OracleBoundedMultiTurnSessionContext,\n    OracleIntelligenceConversationTurn,\n    _stable_hash as oit_043_hash,\n    verify_multi_turn_session_context,\n)\nfrom qseries_v2.oracle_terminal.oracle_multi_turn_follow_up_query_context_resolution import (\n    OracleFollowUpQueryResolutionInvariantError,\n    resolve_multi_turn_follow_up_query,\n    verify_follow_up_query_resolution_report,\n)\n\n\ndef make_turn(\n    index: int,\n    query: str,\n    answer_id: str,\n) -> OracleIntelligenceConversationTurn:\n    body = {\n        "turn_index": index,\n        "query": query,\n        "answer_id": answer_id,\n        "answer_hash": f"answer-hash-{index}",\n        "answer_line_count": 2,\n        "source_answer_report_hash": (\n            f"answer-report-hash-{index}"\n        ),\n        "source_projection_report_hash": (\n            f"projection-report-hash-{index}"\n        ),\n        "evidence_linked": True,\n        "read_only": True,\n    }\n    return OracleIntelligenceConversationTurn(\n        **body,\n        turn_hash=oit_043_hash(body),\n    )\n\n\ndef make_session() -> OracleBoundedMultiTurnSessionContext:\n    turns = (\n        make_turn(\n            0,\n            "What is the market direction?",\n            "answer-044-0",\n        ),\n        make_turn(\n            1,\n            "What evidence supports the bull direction?",\n            "answer-044-1",\n        ),\n    )\n\n    body = {\n        "session_id": "session-044",\n        "turns": turns,\n        "turn_count": len(turns),\n        "total_answer_line_count": 4,\n        "latest_turn_index": 1,\n        "bounded_turn_count": True,\n        "bounded_line_count": True,\n        "deterministic_ordering_applied": True,\n        "complete_lineage_preserved": True,\n        "volatile_memory_only": True,\n        "persistent_memory_enabled": False,\n        "learning_enabled": False,\n        "session_active": True,\n        "read_only": True,\n    }\n    context = OracleBoundedMultiTurnSessionContext(\n        **body,\n        context_hash=oit_043_hash(body),\n    )\n    verify_multi_turn_session_context(context)\n    return context\n\n\ndef main() -> int:\n    print("=" * 48)\n    print(" OIT-044 TEST")\n    print(" MULTI-TURN FOLLOW-UP QUERY CONTEXT RESOLUTION")\n    print(" OIT-043 CORRECTION V2 BASELINE")\n    print("=" * 48)\n\n    with TemporaryDirectory() as temporary:\n        root = Path(temporary)\n        session = make_session()\n\n        follow_up = resolve_multi_turn_follow_up_query(\n            root,\n            session_context=session,\n            query="Has it changed now?",\n        )\n\n        assert follow_up.context_resolution_performed\n        assert follow_up.downstream_projection_ready\n\n        resolved = follow_up.resolved_follow_up_query\n        assert resolved.follow_up_detected\n        assert not resolved.standalone_query\n        assert resolved.referenced_turn_count >= 1\n        assert resolved.primary_reference_turn_index == 1\n        assert (\n            "What evidence supports the bull direction?"\n            in resolved.resolved_query\n        )\n        assert 0.5 <= resolved.resolution_confidence <= 1.0\n        assert resolved.session_lineage_preserved\n        assert resolved.resolution_ready\n\n        standalone = resolve_multi_turn_follow_up_query(\n            root,\n            session_context=session,\n            query="Show probability for REAL-044",\n        )\n\n        standalone_resolved = (\n            standalone.resolved_follow_up_query\n        )\n        assert not standalone.context_resolution_performed\n        assert standalone.downstream_projection_ready\n        assert standalone_resolved.standalone_query\n        assert not standalone_resolved.follow_up_detected\n        assert standalone_resolved.referenced_turn_count == 0\n        assert standalone_resolved.resolved_query == (\n            "Show probability for REAL-044"\n        )\n        assert standalone_resolved.resolution_confidence == 1.0\n\n        replay = resolve_multi_turn_follow_up_query(\n            root,\n            session_context=session,\n            query="Has it changed now?",\n        )\n        assert replay == follow_up\n        assert verify_follow_up_query_resolution_report(\n            follow_up\n        )\n\n        tampered = replace(\n            follow_up,\n            persistent_memory_enabled=True,\n        )\n        try:\n            verify_follow_up_query_resolution_report(tampered)\n        except OracleFollowUpQueryResolutionInvariantError:\n            pass\n        else:\n            raise AssertionError(\n                "tampered follow-up resolution report accepted"\n            )\n\n        assert not follow_up.learning_update_performed\n        assert not follow_up.analytics_execution_performed\n        assert not follow_up.database_access_performed\n        assert not follow_up.runtime_artifact_created\n        assert not follow_up.runtime_artifact_modified\n        assert not follow_up.networking_performed\n        assert not follow_up.publication_allowed\n        assert not follow_up.action_authorization_allowed\n        assert not follow_up.qseries_execution_allowed\n        assert follow_up.read_only\n\n    print("[PASS] Certified OIT-043 Correction V2 session consumed")\n    print("[PASS] Short contextual follow-up detected")\n    print("[PASS] Latest relevant prior turn selected")\n    print("[PASS] Prior query context appended deterministically")\n    print("[PASS] Resolution confidence bounded")\n    print("[PASS] Standalone query preserved unchanged")\n    print("[PASS] Exact turn and answer lineage retained")\n    print("[PASS] Downstream projection readiness certified")\n    print("[PASS] Persistent memory remained disabled")\n    print("[PASS] Learning updates remained disabled")\n    print("[PASS] Resolution deterministic across replay")\n    print("[PASS] Tampered resolution report rejected")\n    print("[PASS] No analytics execution or runtime mutation performed")\n    print("[PASS] Publication, action authorization, and Q Series execution disabled")\n    print("[DONE] OIT-044 FOLLOW-UP QUERY CONTEXT RESOLUTION PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


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
        OIT_043,
        OIT_043_TEST,
        RUNNER,
    ):
        if path.is_file():
            protected[path] = sha256(path)

    return protected


def main() -> int:
    print("=" * 48)
    print(" OIT-044 INSTALLER")
    print(" FOLLOW-UP QUERY CONTEXT RESOLUTION")
    print(" OIT-043 CORRECTION V2 BASELINE")
    print("=" * 48)

    try:
        require_contract(
            OIT_043,
            (
                'SCHEMA_VERSION = "OIT-043"',
                'POLICY_ID = "oracle.bounded-multi-turn-intelligence-session-context.v1"',
                "OracleIntelligenceConversationTurn",
                "OracleBoundedMultiTurnSessionContext",
                "verify_conversation_turn",
                "verify_multi_turn_session_context",
                "volatile_memory_only",
                "persistent_memory_enabled",
                "learning_enabled",
            ),
            "Certified OIT-043 production",
        )

        require_contract(
            OIT_043_TEST,
            (
                "OIT-043 TEST",
                "CORRECTION V2 - REPOSITORY-ALIGNED HASH IMPORT",
                "OIT-042 hash helper imported explicitly",
                "OIT-043 CORRECTION V2 BOUNDED MULTI-TURN SESSION PASS",
            ),
            "Certified OIT-043 Correction V2 test",
        )

        protected = protected_sources()

        print("[OK] Certified OIT-043 production contract verified")
        print("[OK] Certified OIT-043 Correction V2 test verified")
        print("[OK] Corrected OIT-043 baseline accepted")
        print(
            f"[OK] Protected production source files captured: "
            f"{len(protected)}"
        )

        upstream = subprocess.run(
            [sys.executable, str(OIT_043_TEST)],
            cwd=ROOT,
            check=False,
        )
        if upstream.returncode:
            raise RuntimeError(
                f"OIT-043 Correction V2 certification failed "
                f"with exit code {upstream.returncode}"
            )

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_multi_turn_follow_up_query_context_resolution import *"
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
                f"OIT-044 test failed with exit code "
                f"{completed.returncode}"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Protected production source changed: {path}"
                )

        print("[PASS] Certified OIT-043 production unchanged")
        print("[PASS] Certified OIT-043 Correction V2 test unchanged")
        print("[PASS] Oracle terminal runner unchanged")
        print("[PASS] OIT-044 production module installed")
        print("[PASS] OIT-044 standalone test installed")
        print("[PASS] Follow-up detection and prior-turn resolution certified")
        print("[PASS] Standalone query preservation certified")
        print("[PASS] Exact volatile-session lineage retained")
        print("[PASS] Persistent memory remained disabled")
        print("[PASS] Learning updates remained disabled")
        print("[PASS] No analytics execution or runtime mutation performed")
        print("[PASS] OLA, OIA, INT-OII, ORR, OOR, and Q Series unchanged")
        print("[PASS] Publication and execution remained disabled")
        print("[PASS] Read-only and execution boundaries preserved")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OIT-044 FOLLOW-UP QUERY CONTEXT RESOLUTION INSTALLED")
        return 0

    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
