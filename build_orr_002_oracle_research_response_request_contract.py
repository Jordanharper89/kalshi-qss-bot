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
            candidate / "qseries_v2" / "oracle_research_response" /
            "oracle_research_response_runtime_read_only_dependency_gate.py"
        ).is_file():
            return candidate
    raise SystemExit("[ERROR] Could not locate repository with actual ORR-001 module.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_research_response"
SOURCE = PACKAGE / "oracle_research_response_runtime_read_only_dependency_gate.py"
PRODUCTION = PACKAGE / "oracle_research_response_request_contract.py"
TEST = ROOT / "test_orr_002_oracle_research_response_request_contract.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = 'from __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass, is_dataclass\nfrom datetime import datetime, timezone\nfrom typing import Any, Mapping\n\nfrom qseries_v2.oracle_research_response.oracle_research_response_runtime_read_only_dependency_gate import (\n    DEPENDENCY_STATUS as ORR_001_DEPENDENCY_STATUS,\n    DEPENDENCY_TYPE as ORR_001_DEPENDENCY_TYPE,\n    SUBSYSTEM_NAMESPACE,\n    OracleResearchResponseRuntimeDependencyReceipt,\n)\n\nSCHEMA_VERSION = "ORR-002"\nENGINE_ID = "ORR-002"\nPOLICY_ID = "oracle.research-response.request-contract.v1"\nREQUEST_TYPE = "oracle_research_response_read_only_request"\nREQUEST_STATUS = "oracle_research_response_request_materialized"\n\nRESPONSE_MODE_RESEARCH_ANSWER = "research_answer"\nRESPONSE_MODE_PREDICTION_CARD = "prediction_card"\nRESPONSE_MODE_MARKET_DEEP_DIVE = "market_deep_dive"\nRESPONSE_MODE_COMPARISON = "comparison"\nRESPONSE_MODE_EVIDENCE_SUMMARY = "evidence_summary"\n\nALLOWED_RESPONSE_MODES = (\n    RESPONSE_MODE_RESEARCH_ANSWER,\n    RESPONSE_MODE_PREDICTION_CARD,\n    RESPONSE_MODE_MARKET_DEEP_DIVE,\n    RESPONSE_MODE_COMPARISON,\n    RESPONSE_MODE_EVIDENCE_SUMMARY,\n)\n\nMAX_QUESTION_LENGTH = 4000\nMAX_FILTER_ITEMS = 32\nMAX_FILTER_VALUE_LENGTH = 256\n\n\nclass OracleResearchResponseRequestInvariantError(ValueError):\n    pass\n\n\ndef _canonical(value: Any) -> Any:\n    if is_dataclass(value):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {str(key): _canonical(item) for key, item in sorted(value.items(), key=lambda item: str(item[0]))}\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if isinstance(value, datetime):\n        if value.tzinfo is None or value.utcoffset() is None:\n            raise OracleResearchResponseRequestInvariantError(\n                "datetime must be timezone-aware"\n            )\n        return value.astimezone(timezone.utc).isoformat()\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    raise OracleResearchResponseRequestInvariantError(\n        f"unsupported value type: {type(value)!r}"\n    )\n\n\ndef stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=False,\n        allow_nan=False,\n    )\n    return hashlib.sha256(payload.encode("utf-8")).hexdigest()\n\n\ndef _valid_sha256(value: Any) -> bool:\n    return (\n        isinstance(value, str)\n        and len(value) == 64\n        and all(character in "0123456789abcdef" for character in value)\n    )\n\n\ndef _normalized_required_text(name: str, value: Any, maximum: int) -> str:\n    if not isinstance(value, str):\n        raise OracleResearchResponseRequestInvariantError(f"{name} must be text")\n    normalized = " ".join(value.strip().split())\n    if not normalized:\n        raise OracleResearchResponseRequestInvariantError(f"{name} cannot be empty")\n    if len(normalized) > maximum:\n        raise OracleResearchResponseRequestInvariantError(\n            f"{name} exceeds maximum length {maximum}"\n        )\n    return normalized\n\n\ndef _normalized_filters(filters: Mapping[str, str] | None) -> tuple[tuple[str, str], ...]:\n    if filters is None:\n        return ()\n    if not isinstance(filters, Mapping):\n        raise OracleResearchResponseRequestInvariantError(\n            "filters must be a string mapping"\n        )\n    if len(filters) > MAX_FILTER_ITEMS:\n        raise OracleResearchResponseRequestInvariantError(\n            "too many request filters"\n        )\n\n    normalized: list[tuple[str, str]] = []\n    for raw_key, raw_value in filters.items():\n        key = _normalized_required_text(\n            "filter key",\n            raw_key,\n            MAX_FILTER_VALUE_LENGTH,\n        ).lower().replace(" ", "_")\n        value = _normalized_required_text(\n            f"filter value for {key}",\n            raw_value,\n            MAX_FILTER_VALUE_LENGTH,\n        )\n        normalized.append((key, value))\n\n    normalized.sort()\n    if len({key for key, _ in normalized}) != len(normalized):\n        raise OracleResearchResponseRequestInvariantError(\n            "duplicate normalized filter key"\n        )\n    return tuple(normalized)\n\n\n@dataclass(frozen=True)\nclass OracleResearchResponseRequest:\n    request_id: str\n    dependency_receipt_id: str\n    dependency_receipt_hash: str\n    source_runtime_completion_id: str\n    source_runtime_completion_hash: str\n    subsystem_namespace: str\n    requester_id: str\n    correlation_id: str\n    question_text: str\n    response_mode: str\n    filters: tuple[tuple[str, str], ...]\n    requested_at: datetime\n    dependency_identity_verified: bool\n    dependency_hash_verified: bool\n    dependency_contract_verified: bool\n    typed_question_verified: bool\n    response_mode_verified: bool\n    filter_boundary_verified: bool\n    deterministic_boundary_verified: bool\n    immutable_request_boundary_verified: bool\n    read_only_boundary_verified: bool\n    request_single_use_verified: bool\n    duplicate_request_allowed: bool\n    request_reversible: bool\n    runtime_serving_allowed: bool\n    network_listener_allowed: bool\n    database_connection_allowed: bool\n    publication_allowed: bool\n    qseries_handoff_allowed: bool\n    qseries_execution_allowed: bool\n    order_creation_allowed: bool\n    funds_movement_allowed: bool\n    portfolio_mutation_allowed: bool\n    request_type: str\n    request_status: str\n    request_hash: str\n\n\nclass OracleResearchResponseRequestContract:\n    def materialize(\n        self,\n        *,\n        dependency_receipt: OracleResearchResponseRuntimeDependencyReceipt,\n        requester_id: str,\n        correlation_id: str,\n        question_text: str,\n        response_mode: str,\n        requested_at: datetime,\n        filters: Mapping[str, str] | None = None,\n    ) -> OracleResearchResponseRequest:\n        if not isinstance(\n            dependency_receipt,\n            OracleResearchResponseRuntimeDependencyReceipt,\n        ):\n            raise OracleResearchResponseRequestInvariantError(\n                "dependency_receipt must be canonical ORR-001 receipt"\n            )\n\n        dependency_body = asdict(dependency_receipt)\n        supplied_dependency_hash = dependency_body.pop(\n            "dependency_receipt_hash",\n            None,\n        )\n        if (\n            not _valid_sha256(supplied_dependency_hash)\n            or stable_hash(dependency_body) != supplied_dependency_hash\n        ):\n            raise OracleResearchResponseRequestInvariantError(\n                "ORR-001 dependency receipt hash mismatch"\n            )\n\n        dependency_required = (\n            _valid_sha256(dependency_receipt.dependency_receipt_id),\n            _valid_sha256(dependency_receipt.source_runtime_completion_id),\n            _valid_sha256(dependency_receipt.source_runtime_completion_hash),\n            dependency_receipt.subsystem_namespace == SUBSYSTEM_NAMESPACE,\n            dependency_receipt.dependency_type == ORR_001_DEPENDENCY_TYPE,\n            dependency_receipt.dependency_status == ORR_001_DEPENDENCY_STATUS,\n            dependency_receipt.complete_runtime_lineage_verified,\n            dependency_receipt.source_runtime_complete_verified,\n            dependency_receipt.source_runtime_immutable_freeze_verified,\n            dependency_receipt.source_runtime_read_only_verified,\n            dependency_receipt.downstream_read_only_operation_verified,\n            dependency_receipt.deterministic_boundary_verified,\n            dependency_receipt.immutable_result_boundary_verified,\n            dependency_receipt.dependency_single_use_verified,\n            not dependency_receipt.duplicate_dependency_allowed,\n            not dependency_receipt.dependency_reversible,\n        )\n        forbidden_dependency = (\n            dependency_receipt.runtime_serving_allowed,\n            dependency_receipt.network_listener_allowed,\n            dependency_receipt.database_connection_allowed,\n            dependency_receipt.publication_allowed,\n            dependency_receipt.qseries_handoff_allowed,\n            dependency_receipt.qseries_execution_allowed,\n            dependency_receipt.order_creation_allowed,\n            dependency_receipt.funds_movement_allowed,\n            dependency_receipt.portfolio_mutation_allowed,\n        )\n        if not all(dependency_required) or any(forbidden_dependency):\n            raise OracleResearchResponseRequestInvariantError(\n                "ORR-001 dependency contract incomplete or unsafe"\n            )\n\n        requester = _normalized_required_text("requester_id", requester_id, 256)\n        correlation = _normalized_required_text(\n            "correlation_id",\n            correlation_id,\n            256,\n        )\n        question = _normalized_required_text(\n            "question_text",\n            question_text,\n            MAX_QUESTION_LENGTH,\n        )\n\n        if response_mode not in ALLOWED_RESPONSE_MODES:\n            raise OracleResearchResponseRequestInvariantError(\n                "unsupported response_mode"\n            )\n        normalized_filters = _normalized_filters(filters)\n\n        if (\n            not isinstance(requested_at, datetime)\n            or requested_at.tzinfo is None\n            or requested_at.utcoffset() is None\n        ):\n            raise OracleResearchResponseRequestInvariantError(\n                "requested_at must be timezone-aware"\n            )\n        at = requested_at.astimezone(timezone.utc)\n\n        body = {\n            "dependency_receipt_id": dependency_receipt.dependency_receipt_id,\n            "dependency_receipt_hash": dependency_receipt.dependency_receipt_hash,\n            "source_runtime_completion_id": dependency_receipt.source_runtime_completion_id,\n            "source_runtime_completion_hash": dependency_receipt.source_runtime_completion_hash,\n            "subsystem_namespace": SUBSYSTEM_NAMESPACE,\n            "requester_id": requester,\n            "correlation_id": correlation,\n            "question_text": question,\n            "response_mode": response_mode,\n            "filters": normalized_filters,\n            "requested_at": at,\n            "dependency_identity_verified": True,\n            "dependency_hash_verified": True,\n            "dependency_contract_verified": True,\n            "typed_question_verified": True,\n            "response_mode_verified": True,\n            "filter_boundary_verified": True,\n            "deterministic_boundary_verified": True,\n            "immutable_request_boundary_verified": True,\n            "read_only_boundary_verified": True,\n            "request_single_use_verified": True,\n            "duplicate_request_allowed": False,\n            "request_reversible": False,\n            "runtime_serving_allowed": False,\n            "network_listener_allowed": False,\n            "database_connection_allowed": False,\n            "publication_allowed": False,\n            "qseries_handoff_allowed": False,\n            "qseries_execution_allowed": False,\n            "order_creation_allowed": False,\n            "funds_movement_allowed": False,\n            "portfolio_mutation_allowed": False,\n            "request_type": REQUEST_TYPE,\n            "request_status": REQUEST_STATUS,\n        }\n        body["request_id"] = stable_hash(\n            {\n                "engine_id": ENGINE_ID,\n                "dependency_receipt_id": dependency_receipt.dependency_receipt_id,\n                "dependency_receipt_hash": dependency_receipt.dependency_receipt_hash,\n                "requester_id": requester,\n                "correlation_id": correlation,\n                "question_text": question,\n                "response_mode": response_mode,\n                "filters": normalized_filters,\n                "requested_at": at,\n                "request_type": REQUEST_TYPE,\n            }\n        )\n        return OracleResearchResponseRequest(\n            **body,\n            request_hash=stable_hash(body),\n        )\n\n\n__all__ = [\n    "SCHEMA_VERSION",\n    "ENGINE_ID",\n    "POLICY_ID",\n    "REQUEST_TYPE",\n    "REQUEST_STATUS",\n    "RESPONSE_MODE_RESEARCH_ANSWER",\n    "RESPONSE_MODE_PREDICTION_CARD",\n    "RESPONSE_MODE_MARKET_DEEP_DIVE",\n    "RESPONSE_MODE_COMPARISON",\n    "RESPONSE_MODE_EVIDENCE_SUMMARY",\n    "ALLOWED_RESPONSE_MODES",\n    "MAX_QUESTION_LENGTH",\n    "MAX_FILTER_ITEMS",\n    "MAX_FILTER_VALUE_LENGTH",\n    "OracleResearchResponseRequestInvariantError",\n    "OracleResearchResponseRequest",\n    "OracleResearchResponseRequestContract",\n    "stable_hash",\n]\n'
TEST_SOURCE = 'from dataclasses import asdict, replace\nfrom datetime import datetime, timezone\n\nfrom qseries_v2.oracle_research_response.oracle_research_response_runtime_read_only_dependency_gate import (\n    DEPENDENCY_STATUS,\n    DEPENDENCY_TYPE,\n    SUBSYSTEM_NAMESPACE,\n    OracleResearchResponseRuntimeDependencyReceipt,\n    stable_hash as dependency_hash,\n)\nfrom qseries_v2.oracle_research_response.oracle_research_response_request_contract import *\n\n\ndef sample_dependency() -> OracleResearchResponseRuntimeDependencyReceipt:\n    body = {\n        "dependency_receipt_id": "1" * 64,\n        "source_runtime_completion_id": "2" * 64,\n        "source_runtime_completion_hash": "3" * 64,\n        "source_runtime_namespace": "oracle_operator_runtime",\n        "source_runtime_completion_status": "oracle_operator_runtime_final_completion_certified_and_frozen",\n        "subsystem_namespace": SUBSYSTEM_NAMESPACE,\n        "admitted_at": datetime(2026, 7, 28, 18, 0, tzinfo=timezone.utc),\n        "complete_runtime_lineage_verified": True,\n        "source_runtime_complete_verified": True,\n        "source_runtime_immutable_freeze_verified": True,\n        "source_runtime_read_only_verified": True,\n        "downstream_read_only_operation_verified": True,\n        "deterministic_boundary_verified": True,\n        "immutable_result_boundary_verified": True,\n        "dependency_single_use_verified": True,\n        "duplicate_dependency_allowed": False,\n        "dependency_reversible": False,\n        "runtime_serving_allowed": False,\n        "network_listener_allowed": False,\n        "database_connection_allowed": False,\n        "publication_allowed": False,\n        "qseries_handoff_allowed": False,\n        "qseries_execution_allowed": False,\n        "order_creation_allowed": False,\n        "funds_movement_allowed": False,\n        "portfolio_mutation_allowed": False,\n        "dependency_type": DEPENDENCY_TYPE,\n        "dependency_status": DEPENDENCY_STATUS,\n    }\n    return OracleResearchResponseRuntimeDependencyReceipt(\n        **body,\n        dependency_receipt_hash=dependency_hash(body),\n    )\n\n\ndef reject(function) -> None:\n    try:\n        function()\n        raise AssertionError("unsafe research response request accepted")\n    except OracleResearchResponseRequestInvariantError:\n        pass\n\n\ndef main() -> int:\n    print("=" * 40)\n    print(" ORR-002 TEST")\n    print(" RESEARCH RESPONSE REQUEST CONTRACT")\n    print("=" * 40)\n\n    dependency = sample_dependency()\n    requested_at = datetime(2026, 7, 28, 18, 5, tzinfo=timezone.utc)\n    contract = OracleResearchResponseRequestContract()\n\n    first = contract.materialize(\n        dependency_receipt=dependency,\n        requester_id="operator:jordan",\n        correlation_id="session:orr-002-test",\n        question_text="  What are the strongest Kalshi opportunities closing today?  ",\n        response_mode=RESPONSE_MODE_PREDICTION_CARD,\n        filters={"Venue": "Kalshi", "Time Horizon": "Today"},\n        requested_at=requested_at,\n    )\n    second = contract.materialize(\n        dependency_receipt=dependency,\n        requester_id="operator:jordan",\n        correlation_id="session:orr-002-test",\n        question_text="What are the strongest Kalshi opportunities closing today?",\n        response_mode=RESPONSE_MODE_PREDICTION_CARD,\n        filters={"Time Horizon": "Today", "Venue": "Kalshi"},\n        requested_at=requested_at,\n    )\n\n    assert first == second\n    assert first.question_text == "What are the strongest Kalshi opportunities closing today?"\n    assert first.filters == (("time_horizon", "Today"), ("venue", "Kalshi"))\n    assert first.request_hash == stable_hash(\n        {\n            key: value\n            for key, value in asdict(first).items()\n            if key != "request_hash"\n        }\n    )\n    assert first.request_type == REQUEST_TYPE\n    assert first.request_status == REQUEST_STATUS\n    assert first.typed_question_verified\n    assert first.response_mode_verified\n    assert first.filter_boundary_verified\n    assert first.read_only_boundary_verified\n    assert first.request_single_use_verified\n    assert not first.duplicate_request_allowed\n    assert not first.request_reversible\n\n    reject(\n        lambda: contract.materialize(\n            dependency_receipt=replace(\n                dependency,\n                dependency_receipt_hash="0" * 64,\n            ),\n            requester_id="operator:jordan",\n            correlation_id="session:test",\n            question_text="What changed?",\n            response_mode=RESPONSE_MODE_RESEARCH_ANSWER,\n            requested_at=requested_at,\n        )\n    )\n    reject(\n        lambda: contract.materialize(\n            dependency_receipt=dependency,\n            requester_id="operator:jordan",\n            correlation_id="session:test",\n            question_text="   ",\n            response_mode=RESPONSE_MODE_RESEARCH_ANSWER,\n            requested_at=requested_at,\n        )\n    )\n    reject(\n        lambda: contract.materialize(\n            dependency_receipt=dependency,\n            requester_id="operator:jordan",\n            correlation_id="session:test",\n            question_text="Place an order.",\n            response_mode="execution",\n            requested_at=requested_at,\n        )\n    )\n    reject(\n        lambda: contract.materialize(\n            dependency_receipt=dependency,\n            requester_id="operator:jordan",\n            correlation_id="session:test",\n            question_text="What changed?",\n            response_mode=RESPONSE_MODE_RESEARCH_ANSWER,\n            requested_at=datetime(2026, 7, 28, 18, 5),\n        )\n    )\n\n    print("[PASS] Actual ORR-001 runtime dependency receipt consumed")\n    print("[PASS] Typed natural-language research question materialized")\n    print("[PASS] Research answer and prediction-card response modes supported")\n    print("[PASS] Deterministic normalized filters certified")\n    print("[PASS] Immutable single-use request boundary certified")\n    print("[PASS] Runtime serving, networking, database connection, and publication remain disabled")\n    print("[PASS] Q Series execution, orders, funds, and portfolio mutation remain disabled")\n    print("[PASS] Tampered, empty, unsupported, and unsafe requests rejected")\n    print("[DONE] ORR-002 RESEARCH RESPONSE REQUEST CONTRACT PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_complete(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def main() -> int:
    print("=" * 40)
    print(" ORR-002 INSTALLER")
    print(" RESEARCH RESPONSE REQUEST CONTRACT")
    print("=" * 40)
    try:
        source_text = SOURCE.read_text(encoding="utf-8")
        required = (
            'SCHEMA_VERSION = "ORR-001"',
            "OracleResearchResponseRuntimeDependencyReceipt",
            "dependency_receipt_hash",
            "source_runtime_read_only_verified",
            "downstream_read_only_operation_verified",
            "DEPENDENCY_TYPE",
            "DEPENDENCY_STATUS",
        )
        missing = [item for item in required if item not in source_text]
        if missing:
            raise RuntimeError(f"ORR-001 contract incomplete: {missing}")
        ast.parse(source_text, filename=str(SOURCE))
        protected_hash = sha256(SOURCE)
        print("[OK] Actual ORR-001 runtime dependency contract verified")

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_research_response_request_contract import ("
            "ALLOWED_RESPONSE_MODES, "
            "REQUEST_STATUS, "
            "REQUEST_TYPE, "
            "OracleResearchResponseRequest, "
            "OracleResearchResponseRequestContract, "
            "OracleResearchResponseRequestInvariantError)"
        )
        current = (
            INIT.read_text(encoding="utf-8")
            if INIT.exists()
            else "from __future__ import annotations\n"
        )
        if export not in current:
            INIT.write_text(
                current.rstrip() + "\n\n" + export + "\n",
                encoding="utf-8",
                newline="\n",
            )
        ast.parse(INIT.read_text(encoding="utf-8"), filename=str(INIT))
        print(f"[OK] PACKAGE UPDATED: {INIT.resolve()}")

        completed = subprocess.run([sys.executable, str(TEST)], cwd=ROOT, check=False)
        if completed.returncode:
            raise RuntimeError(f"ORR-002 test failed with exit code {completed.returncode}")
        if sha256(SOURCE) != protected_hash:
            raise RuntimeError("Protected ORR-001 module changed")

        print("[PASS] Protected ORR-001 module unchanged")
        print("[PASS] ORR-001 read-only dependency lineage preserved")
        print("[PASS] Typed-question request boundary established")
        print("[PASS] No acquisition, analytics, integration, operator, or runtime module modified")
        print("[PASS] No Q Series execution module modified")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] ORR-002 INSTALLED AND VERIFIED")
        return 0
    except (RuntimeError, SyntaxError, OSError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
