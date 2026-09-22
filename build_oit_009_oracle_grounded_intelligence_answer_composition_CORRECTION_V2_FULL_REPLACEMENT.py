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
        if (
            candidate / "qseries_v2" / "oracle_terminal"
            / "oracle_natural_language_query_planning_and_execution.py"
        ).is_file():
            return candidate
    raise SystemExit("[ERROR] Could not locate repository containing OIT-008.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"
OIT_008 = PACKAGE / "oracle_natural_language_query_planning_and_execution.py"
PRODUCTION = PACKAGE / "oracle_grounded_intelligence_answer_composition.py"
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"
TEST = ROOT / "test_oit_009_oracle_grounded_intelligence_answer_composition.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass\nfrom pathlib import Path\nfrom typing import Any, Mapping\n\nfrom .oracle_natural_language_query_planning_and_execution import (\n    OracleNaturalLanguageQueryInvariantError,\n    OracleNaturalLanguageQueryMatch,\n    OracleNaturalLanguageQueryResult,\n    execute_natural_language_query,\n    verify_natural_language_query_match,\n    verify_natural_language_query_result,\n)\n\nSCHEMA_VERSION = "OIT-009"\nENGINE_ID = "OIT-009"\nPOLICY_ID = "oracle.grounded-intelligence-answer-composition.v2"\n\nMAX_EVIDENCE_ITEMS = 10\nSUMMARY_FIELD_PRIORITY = (\n    "title",\n    "question",\n    "market",\n    "market_id",\n    "prediction_id",\n    "record_id",\n    "ticker",\n    "symbol",\n    "stance",\n    "direction",\n    "signal",\n    "probability",\n    "confidence",\n    "score",\n    "price",\n    "venue",\n    "exchange",\n    "expires_at",\n    "date",\n    "status",\n)\n\n\nclass OracleGroundedAnswerInvariantError(\n    OracleNaturalLanguageQueryInvariantError\n):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleGroundedEvidenceItem:\n    evidence_index: int\n    record_id: str\n    artifact_relative_path: str\n    artifact_sha256: str\n    record_hash: str\n    query_plan_hash: str\n    matched_terms: tuple[str, ...]\n    matched_required_terms: tuple[str, ...]\n    matched_field_hints: tuple[str, ...]\n    score: int\n    selected_fields: tuple[tuple[str, Any], ...]\n    evidence_label: str\n    read_only: bool\n    evidence_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleGroundedIntelligenceAnswer:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    status: str\n    repository_root: str\n    query: str\n    answer_text: str\n    evidence: tuple[OracleGroundedEvidenceItem, ...]\n    evidence_count: int\n    answer_grounded: bool\n    uncertainty_statement: str\n    limitation_statement: str\n    query_plan_hash: str\n    query_result_hash: str\n    read_only: bool\n    analytics_execution_performed: bool\n    database_access_performed: bool\n    publication_allowed: bool\n    qseries_execution_allowed: bool\n    failure_reason: str | None\n    answer_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda item: str(item[0]))\n        }\n    if isinstance(value, (list, tuple)):\n        return [_canonical(item) for item in value]\n    if isinstance(value, Path):\n        return value.as_posix()\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    return repr(value)\n\n\ndef _stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=True,\n    ).encode("utf-8")\n    return hashlib.sha256(payload).hexdigest()\n\n\ndef _selected_fields(payload: Any) -> tuple[tuple[str, Any], ...]:\n    if not isinstance(payload, Mapping):\n        return (("value", _canonical(payload)),)\n\n    selected: list[tuple[str, Any]] = []\n    seen: set[str] = set()\n\n    for key in SUMMARY_FIELD_PRIORITY:\n        if key in payload and key not in seen:\n            selected.append((key, _canonical(payload[key])))\n            seen.add(key)\n\n    if not selected:\n        for key, value in sorted(payload.items(), key=lambda item: str(item[0])):\n            selected.append((str(key), _canonical(value)))\n            if len(selected) >= 8:\n                break\n\n    return tuple(selected)\n\n\ndef _display_value(value: Any) -> str:\n    if isinstance(value, float):\n        return f"{value:.6g}"\n    if isinstance(value, (dict, list, tuple)):\n        return json.dumps(\n            _canonical(value),\n            sort_keys=True,\n            ensure_ascii=False,\n            separators=(",", ":"),\n        )\n    return str(value)\n\n\ndef _build_evidence_item(\n    *,\n    index: int,\n    match: OracleNaturalLanguageQueryMatch,\n    query_plan_hash: str,\n) -> OracleGroundedEvidenceItem:\n    verify_natural_language_query_match(match)\n    selected = _selected_fields(match.payload)\n    label_parts = [\n        f"{key}={_display_value(value)}"\n        for key, value in selected[:6]\n    ]\n    label = "; ".join(label_parts) or f"record_id={match.record_id}"\n\n    body = {\n        "evidence_index": index,\n        "record_id": match.record_id,\n        "artifact_relative_path": match.artifact_relative_path,\n        "artifact_sha256": match.artifact_sha256,\n        "record_hash": match.record_hash,\n        "query_plan_hash": query_plan_hash,\n        "matched_terms": match.matched_terms,\n        "matched_required_terms": match.matched_required_terms,\n        "matched_field_hints": match.matched_field_hints,\n        "score": match.score,\n        "selected_fields": selected,\n        "evidence_label": label,\n        "read_only": True,\n    }\n    item = OracleGroundedEvidenceItem(\n        **body,\n        evidence_hash=_stable_hash(body),\n    )\n    verify_grounded_evidence_item(item)\n    return item\n\n\ndef verify_grounded_evidence_item(\n    item: OracleGroundedEvidenceItem,\n) -> bool:\n    body = asdict(item)\n    supplied = body.pop("evidence_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleGroundedAnswerInvariantError(\n            "OIT-009 evidence hash mismatch"\n        )\n    if not item.read_only:\n        raise OracleGroundedAnswerInvariantError(\n            "grounded evidence item is not read-only"\n        )\n    if item.evidence_index < 1:\n        raise OracleGroundedAnswerInvariantError(\n            "invalid evidence index"\n        )\n    if (\n        len(item.artifact_sha256) != 64\n        or not item.record_hash\n        or not item.query_plan_hash\n    ):\n        raise OracleGroundedAnswerInvariantError(\n            "evidence lineage is incomplete"\n        )\n    if item.matched_required_terms and not set(\n        item.matched_required_terms\n    ).issubset(set(item.matched_terms)):\n        raise OracleGroundedAnswerInvariantError(\n            "required evidence terms are not present in matched terms"\n        )\n    return True\n\n\ndef _compose_answer_text(\n    *,\n    query: str,\n    evidence: tuple[OracleGroundedEvidenceItem, ...],\n) -> str:\n    if not evidence:\n        return (\n            f\'No admitted Oracle intelligence record matched the question \'\n            f\'"{query}".\'\n        )\n    if len(evidence) == 1:\n        item = evidence[0]\n        return (\n            f\'Oracle found one grounded match for "{query}": \'\n            f\'{item.evidence_label}. Evidence [E1].\'\n        )\n    return (\n        f\'Oracle found {len(evidence)} grounded matches for "{query}". \'\n        + " ".join(\n            f"[E{item.evidence_index}] {item.evidence_label}"\n            for item in evidence\n        )\n    )\n\n\ndef _uncertainty_statement(\n    result: OracleNaturalLanguageQueryResult,\n) -> str:\n    if not result.query_ready:\n        return (\n            "The answer is unavailable because the admitted intelligence "\n            "read model is not query-ready."\n        )\n    if result.match_count == 0:\n        return (\n            "No matching admitted record was found; this does not prove that "\n            "the requested fact or opportunity does not exist."\n        )\n    if result.match_count == 1:\n        return (\n            "The answer is supported by one admitted record and should not be "\n            "treated as independently corroborated."\n        )\n    return (\n        f"The answer reflects {result.match_count} admitted matching records; "\n        "agreement, independence, and freshness are not inferred beyond the "\n        "fields shown."\n    )\n\n\ndef compose_grounded_intelligence_answer(\n    *,\n    repository_root: Path,\n    query: str,\n    result_limit: int = 10,\n) -> OracleGroundedIntelligenceAnswer:\n    root = repository_root.resolve()\n    result = execute_natural_language_query(\n        repository_root=root,\n        query=query,\n        result_limit=min(result_limit, MAX_EVIDENCE_ITEMS),\n    )\n    verify_natural_language_query_result(result)\n\n    evidence = tuple(\n        _build_evidence_item(\n            index=index,\n            match=match,\n            query_plan_hash=result.plan.plan_hash,\n        )\n        for index, match in enumerate(result.matches, start=1)\n    )\n    grounded = bool(result.query_ready and evidence)\n    failure = result.failure_reason\n    limitation = (\n        "This answer only summarizes immutable OIT-005-admitted artifacts "\n        "available through the certified OIT-006 to OIT-008 V3 read-only "\n        "chain. It does not execute analytics, access databases, publish, "\n        "trade, or create facts absent from matched records."\n    )\n\n    body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "status": (\n            "grounded_intelligence_answer_composed"\n            if result.query_ready\n            else "grounded_intelligence_answer_blocked"\n        ),\n        "repository_root": root.as_posix(),\n        "query": result.plan.normalized_query,\n        "answer_text": _compose_answer_text(\n            query=result.plan.normalized_query,\n            evidence=evidence,\n        ),\n        "evidence": evidence,\n        "evidence_count": len(evidence),\n        "answer_grounded": grounded,\n        "uncertainty_statement": _uncertainty_statement(result),\n        "limitation_statement": limitation,\n        "query_plan_hash": result.plan.plan_hash,\n        "query_result_hash": result.result_hash,\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "publication_allowed": False,\n        "qseries_execution_allowed": False,\n        "failure_reason": failure,\n    }\n    answer = OracleGroundedIntelligenceAnswer(\n        **body,\n        answer_hash=_stable_hash(body),\n    )\n    verify_grounded_intelligence_answer(answer)\n    return answer\n\n\ndef verify_grounded_intelligence_answer(\n    answer: OracleGroundedIntelligenceAnswer,\n) -> bool:\n    body = asdict(answer)\n    supplied = body.pop("answer_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleGroundedAnswerInvariantError(\n            "OIT-009 answer hash mismatch"\n        )\n    for item in answer.evidence:\n        verify_grounded_evidence_item(item)\n        if item.query_plan_hash != answer.query_plan_hash:\n            raise OracleGroundedAnswerInvariantError(\n                "evidence query-plan lineage mismatch"\n            )\n    if not answer.read_only:\n        raise OracleGroundedAnswerInvariantError(\n            "OIT-009 is not read-only"\n        )\n    if (\n        answer.analytics_execution_performed\n        or answer.database_access_performed\n        or answer.publication_allowed\n        or answer.qseries_execution_allowed\n    ):\n        raise OracleGroundedAnswerInvariantError(\n            "unsafe grounded answer boundary"\n        )\n    if answer.evidence_count != len(answer.evidence):\n        raise OracleGroundedAnswerInvariantError(\n            "evidence count mismatch"\n        )\n    if answer.answer_grounded and not answer.evidence:\n        raise OracleGroundedAnswerInvariantError(\n            "grounded answer has no evidence"\n        )\n    if not answer.query_plan_hash or not answer.query_result_hash:\n        raise OracleGroundedAnswerInvariantError(\n            "grounded answer lacks query lineage"\n        )\n    return True\n\n\ndef grounded_answer_lines(\n    answer: OracleGroundedIntelligenceAnswer,\n) -> tuple[str, ...]:\n    verify_grounded_intelligence_answer(answer)\n    lines = [\n        "ORACLE GROUNDED INTELLIGENCE ANSWER",\n        f"query: {answer.query}",\n        f"answer: {answer.answer_text}",\n        f"answer_grounded: {str(answer.answer_grounded).lower()}",\n        f"evidence_count: {answer.evidence_count}",\n        f"failure_reason: {answer.failure_reason or \'none\'}",\n        f"uncertainty: {answer.uncertainty_statement}",\n        f"limitations: {answer.limitation_statement}",\n    ]\n    if not answer.evidence:\n        lines.append("evidence: none")\n    else:\n        lines.append("evidence:")\n        for item in answer.evidence:\n            lines.extend((\n                f"  [E{item.evidence_index}] {item.record_id}",\n                f"      summary: {item.evidence_label}",\n                f"      score: {item.score}",\n                f"      matched_terms: {\', \'.join(item.matched_terms) or \'none\'}",\n                f"      matched_required_terms: {\', \'.join(item.matched_required_terms) or \'none\'}",\n                f"      matched_field_hints: {\', \'.join(item.matched_field_hints) or \'none\'}",\n                f"      artifact: {item.artifact_relative_path}",\n                f"      artifact_sha256: {item.artifact_sha256}",\n                f"      record_hash: {item.record_hash}",\n                f"      query_plan_hash: {item.query_plan_hash}",\n            ))\n    lines.extend((\n        f"query_plan_hash: {answer.query_plan_hash}",\n        f"query_result_hash: {answer.query_result_hash}",\n        f"answer_hash: {answer.answer_hash}",\n        "analytics_execution_performed: false",\n        "database_access_performed: false",\n        "publication_allowed: false",\n        "qseries_execution_allowed: false",\n        "read_only: true",\n    ))\n    return tuple(lines)\n'
TEST_SOURCE = '\nimport hashlib\nimport json\nimport os\nimport sys\nfrom pathlib import Path\nfrom tempfile import TemporaryDirectory\n\n\ndef stable_hash(value):\n    payload = json.dumps(\n        value,\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=True,\n    ).encode("utf-8")\n    return hashlib.sha256(payload).hexdigest()\n\n\ndef clear_modules():\n    for name in list(sys.modules):\n        if name == "qseries_v2" or name.startswith("qseries_v2."):\n            del sys.modules[name]\n\n\ndef main() -> int:\n    print("=" * 40)\n    print(" OIT-009 CORRECTION V2 TEST")\n    print(" OIT-008 V3 GROUNDED ANSWER BINDING")\n    print("=" * 40)\n\n    installed_root = Path(__file__).resolve().parent\n    installed_terminal = installed_root / "qseries_v2" / "oracle_terminal"\n\n    with TemporaryDirectory() as temporary:\n        root = Path(temporary)\n        qseries = root / "qseries_v2"\n        terminal = qseries / "oracle_terminal"\n        for directory in (qseries, terminal):\n            directory.mkdir(parents=True, exist_ok=True)\n            (directory / "__init__.py").write_text("", encoding="utf-8")\n\n        for source_name in (\n            "oracle_genuine_intelligence_artifact_admission.py",\n            "oracle_genuine_intelligence_read_only_consumption.py",\n            "oracle_queryable_intelligence_read_model.py",\n            "oracle_natural_language_query_planning_and_execution.py",\n            "oracle_grounded_intelligence_answer_composition.py",\n        ):\n            (terminal / source_name).write_text(\n                (installed_terminal / source_name).read_text(encoding="utf-8"),\n                encoding="utf-8",\n            )\n\n        intelligence = root / "runtime" / "oracle_intelligence" / "bounded_activation"\n        terminal_runtime = root / "runtime" / "oracle_terminal"\n        intelligence.mkdir(parents=True, exist_ok=True)\n        terminal_runtime.mkdir(parents=True, exist_ok=True)\n\n        artifact_path = intelligence / "first_genuine_intelligence.json"\n        artifact_payload = {\n            "schema_version": "TEST-INTELLIGENCE-1",\n            "records": [\n                {\n                    "market_id": "MARKET-001",\n                    "title": "Will Alpha happen?",\n                    "probability": 0.72,\n                    "stance": "bull",\n                    "venue": "Kalshi",\n                },\n                {\n                    "market_id": "MARKET-002",\n                    "title": "Will Beta happen?",\n                    "probability": 0.31,\n                    "stance": "bear",\n                    "venue": "Polymarket",\n                },\n            ],\n        }\n        artifact_path.write_text(\n            json.dumps(artifact_payload, sort_keys=True) + "\\n",\n            encoding="utf-8",\n        )\n        stat = artifact_path.stat()\n        relative = artifact_path.relative_to(root).as_posix()\n        artifact_state = {\n            "relative_path": relative,\n            "sha256": hashlib.sha256(artifact_path.read_bytes()).hexdigest(),\n            "byte_count": stat.st_size,\n            "modified_ns": stat.st_mtime_ns,\n        }\n\n        activation_body = {\n            "schema_version": "OIT-004",\n            "engine_id": "OIT-004",\n            "policy_id": "oracle.bounded-live-intelligence-activation.v1",\n            "status": "bounded_activation_completed",\n            "repository_root": root.as_posix(),\n            "analytics_entry_point": "test.module:Gate.execute",\n            "required_inputs": [\n                "certified_artifacts: Any",\n                "execution_context: Mapping[str, Any]",\n                "executed_at: datetime",\n                "persist: bool",\n            ],\n            "selected_input": {\n                "relative_path": "runtime/oracle_research/certified.json",\n                "sha256": "a" * 64,\n                "byte_count": 10,\n                "modified_ns": 1,\n                "payload_kind": "dict",\n                "record_count": 1,\n                "score": 100,\n                "score_reasons": ["test"],\n            },\n            "candidate_count": 1,\n            "persistence_target": "runtime/oracle_intelligence",\n            "activation_readiness": "activation_completed",\n            "activation_attempted": True,\n            "analytics_execution_performed": True,\n            "invocation_completed": True,\n            "persist_requested": True,\n            "new_intelligence_artifacts": [artifact_state],\n            "changed_intelligence_artifacts": [],\n            "protected_source_unchanged": True,\n            "outside_target_runtime_unchanged": True,\n            "database_write_requested": False,\n            "publication_allowed": False,\n            "qseries_execution_allowed": False,\n            "bounded_once": True,\n            "failure_reason": None,\n            "executed_at_utc": "2026-07-30T19:00:00+00:00",\n        }\n        activation_body["receipt_hash"] = stable_hash(activation_body)\n        (terminal_runtime / "oit_004_bounded_activation_receipt.json").write_text(\n            json.dumps(activation_body, indent=2, sort_keys=True) + "\\n",\n            encoding="utf-8",\n        )\n\n        before_hash = hashlib.sha256(artifact_path.read_bytes()).hexdigest()\n        before_mtime = artifact_path.stat().st_mtime_ns\n\n        old_path = list(sys.path)\n        old_cwd = Path.cwd()\n        try:\n            os.chdir(root)\n            sys.path.insert(0, str(root))\n            clear_modules()\n            module = __import__(\n                "qseries_v2.oracle_terminal."\n                "oracle_grounded_intelligence_answer_composition",\n                fromlist=["*"],\n            )\n\n            answer = module.compose_grounded_intelligence_answer(\n                repository_root=root,\n                query="Show me the bull Alpha market probability",\n                result_limit=5,\n            )\n            assert module.verify_grounded_intelligence_answer(answer)\n            assert answer.answer_grounded\n            assert answer.evidence_count == 1\n            assert answer.evidence[0].record_id == "MARKET-001"\n            assert answer.evidence[0].matched_required_terms == (\n                "bull",\n                "alpha",\n            )\n            assert answer.evidence[0].query_plan_hash == answer.query_plan_hash\n            assert "Evidence [E1]" in answer.answer_text\n\n            no_match = module.compose_grounded_intelligence_answer(\n                repository_root=root,\n                query="gamma market",\n            )\n            assert not no_match.answer_grounded\n            assert no_match.evidence_count == 0\n            assert "does not prove" in no_match.uncertainty_statement\n\n            bull = module.compose_grounded_intelligence_answer(\n                repository_root=root,\n                query="bull market probability",\n            )\n            assert bull.answer_grounded\n            assert bull.evidence_count == 1\n            assert bull.evidence[0].record_id == "MARKET-001"\n\n            schema_only = module.compose_grounded_intelligence_answer(\n                repository_root=root,\n                query="market probability",\n            )\n            assert schema_only.answer_grounded\n            assert schema_only.evidence_count == 2\n\n            rendered = "\\n".join(module.grounded_answer_lines(answer))\n            assert "matched_required_terms: bull, alpha" in rendered\n            assert "query_plan_hash:" in rendered\n            assert "query_result_hash:" in rendered\n            assert "read_only: true" in rendered\n\n            assert hashlib.sha256(\n                artifact_path.read_bytes()\n            ).hexdigest() == before_hash\n            assert artifact_path.stat().st_mtime_ns == before_mtime\n\n            artifact_path.write_text(\n                json.dumps({"mutated": True}) + "\\n",\n                encoding="utf-8",\n            )\n            blocked = module.compose_grounded_intelligence_answer(\n                repository_root=root,\n                query="alpha",\n            )\n            assert not blocked.answer_grounded\n            assert blocked.evidence_count == 0\n        finally:\n            os.chdir(old_cwd)\n            sys.path[:] = old_path\n            clear_modules()\n\n    print("[PASS] Certified OIT-008 CORRECTION V3 contract consumed")\n    print("[PASS] Required-content terms preserved in every evidence item")\n    print("[PASS] Query-plan, query-result, record, and artifact lineage preserved")\n    print("[PASS] gamma market produces safe no-match answer")\n    print("[PASS] bull market probability produces one grounded bull answer")\n    print("[PASS] schema-only market probability produces two grounded records")\n    print("[PASS] Source artifact bytes and modification time unchanged")\n    print("[PASS] Mutated source artifact blocks grounded answers")\n    print("[PASS] No analytics execution or database access performed")\n    print("[PASS] Publication and Q Series execution disabled")\n    print("[DONE] OIT-009 CORRECTION V2 FULL REPLACEMENT PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_complete(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def protected_sources() -> dict[Path, str]:
    result = {}
    prefixes = (
        ROOT / "qseries_v2" / "oracle_intelligence" / "live_acquisition",
        ROOT / "qseries_v2" / "oracle_intelligence" / "analytics",
        ROOT / "qseries_v2" / "oracle_intelligence_integration",
        ROOT / "qseries_v2" / "oracle_research_runtime",
        ROOT / "qseries_v2" / "oracle_operator_runtime",
        ROOT / "qseries_v2" / "qseries",
    )
    for base in prefixes:
        if base.exists():
            for path in base.rglob("*.py"):
                if path.is_file():
                    result[path] = sha256(path)
    for path in (OIT_008, RUNNER):
        if path.is_file():
            result[path] = sha256(path)
    return result


def main() -> int:
    print("=" * 40)
    print(" OIT-009 CORRECTION V2 INSTALLER")
    print(" OIT-008 V3 GROUNDED ANSWER BINDING")
    print("=" * 40)
    try:
        if not OIT_008.is_file():
            raise RuntimeError(f"Actual OIT-008 module missing: {OIT_008}")
        if not RUNNER.is_file():
            raise RuntimeError(f"Actual terminal runner missing: {RUNNER}")

        oit_008_text = OIT_008.read_text(encoding="utf-8")
        required = (
            'SCHEMA_VERSION = "OIT-008"',
            'POLICY_ID = "oracle.natural-language-query-planning-and-execution.v2"',
            "required_content_terms",
            "generic_schema_terms",
            "matched_required_terms",
            "deterministic_read_only_grounded_search",
        )
        missing = [item for item in required if item not in oit_008_text]
        if missing:
            raise RuntimeError(
                "Certified OIT-008 CORRECTION V3 contract not found: "
                f"{missing}"
            )

        protected = protected_sources()
        print("[OK] Certified OIT-008 CORRECTION V3 contract verified")
        print("[OK] Current terminal runner captured and preserved")
        print(f"[OK] Protected production source files captured: {len(protected)}")

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_grounded_intelligence_answer_composition import *"
        )
        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"
            INIT.write_text(
                current + export + "\n",
                encoding="utf-8",
                newline="\n",
            )
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
                f"OIT-009 CORRECTION V2 test failed with exit code "
                f"{completed.returncode}"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Protected production source changed: {path}"
                )

        print("[PASS] Certified OIT-008 production module unchanged")
        print("[PASS] Current terminal runner unchanged")
        print("[PASS] OLA, OIA, INT-OII, ORR, OOR, and Q Series unchanged")
        print("[PASS] Entire OIT-009 production module replaced")
        print("[PASS] Entire OIT-009 test replaced")
        print("[PASS] OIT-008 V3 required-term lineage certified")
        print("[PASS] Complete production test passed")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OIT-009 CORRECTION V2 FULL REPLACEMENT INSTALLED")
        return 0
    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
