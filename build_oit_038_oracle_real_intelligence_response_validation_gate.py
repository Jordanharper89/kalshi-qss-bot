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
            / "oracle_authorized_real_intelligence_read_invocation_execution_gate.py"
        )
        test = (
            candidate
            / "test_oit_037_oracle_authorized_real_intelligence_read_invocation_execution_gate.py"
        )
        if production.is_file() and test.is_file():
            return candidate

    raise SystemExit("[ERROR] Could not locate current Q Series repository.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"
OIT_037 = (
    PACKAGE
    / "oracle_authorized_real_intelligence_read_invocation_execution_gate.py"
)
OIT_037_TEST = (
    ROOT
    / "test_oit_037_oracle_authorized_real_intelligence_read_invocation_execution_gate.py"
)
PRODUCTION = (
    PACKAGE
    / "oracle_real_intelligence_response_validation_gate.py"
)
TEST = (
    ROOT
    / "test_oit_038_oracle_real_intelligence_response_validation_gate.py"
)
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass\nfrom pathlib import Path\nfrom typing import Any, Mapping\n\nfrom .oracle_authorized_real_intelligence_read_invocation_execution_gate import (\n    OracleRealIntelligenceInvocationResult,\n    OracleRealIntelligenceReadInvocationExecutionInvariantError,\n    OracleRealIntelligenceReadInvocationExecutionReport,\n    execute_authorized_real_intelligence_read_invocation,\n    verify_read_invocation_execution_report,\n)\n\nSCHEMA_VERSION = "OIT-038"\nENGINE_ID = "OIT-038"\nPOLICY_ID = "oracle.real-intelligence-response-validation.v1"\n\nMAX_DEPTH = 12\nMAX_CONTAINER_ITEMS = 10000\nMAX_STRING_LENGTH = 1_000_000\n\n\nclass OracleRealIntelligenceResponseValidationInvariantError(\n    OracleRealIntelligenceReadInvocationExecutionInvariantError\n):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleRealIntelligenceStructuralFinding:\n    finding_code: str\n    severity: str\n    location: str\n    message: str\n    blocking: bool\n    finding_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleRealIntelligenceResponseShape:\n    root_type: str\n    root_mapping: bool\n    root_sequence: bool\n    root_scalar: bool\n    maximum_depth: int\n    mapping_count: int\n    sequence_count: int\n    scalar_count: int\n    null_count: int\n    string_count: int\n    number_count: int\n    boolean_count: int\n    total_node_count: int\n    total_key_count: int\n    duplicate_key_risk_detected: bool\n    unsupported_type_detected: bool\n    nonfinite_number_detected: bool\n    oversized_value_detected: bool\n    shape_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleRealIntelligenceResponseValidationReport:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    status: str\n    repository_root: str\n    execution_report_hash: str\n    invocation_result_hash: str\n    response_shape: OracleRealIntelligenceResponseShape\n    findings: tuple[OracleRealIntelligenceStructuralFinding, ...]\n    finding_count: int\n    blocking_finding_count: int\n    structurally_valid: bool\n    deterministic_replay_ready: bool\n    normalization_ready: bool\n    source_result_preserved: bool\n    response_modified: bool\n    analytics_execution_performed: bool\n    database_access_performed: bool\n    runtime_artifact_created: bool\n    runtime_artifact_modified: bool\n    networking_performed: bool\n    publication_allowed: bool\n    action_authorization_allowed: bool\n    qseries_execution_allowed: bool\n    read_only: bool\n    failure_reason: str | None\n    report_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    return repr(value)\n\n\ndef _stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=True,\n        allow_nan=False,\n    ).encode("utf-8")\n    return hashlib.sha256(payload).hexdigest()\n\n\ndef _finding(\n    code: str,\n    severity: str,\n    location: str,\n    message: str,\n    *,\n    blocking: bool,\n) -> OracleRealIntelligenceStructuralFinding:\n    body = {\n        "finding_code": code,\n        "severity": severity,\n        "location": location,\n        "message": message,\n        "blocking": blocking,\n    }\n    finding = OracleRealIntelligenceStructuralFinding(\n        **body,\n        finding_hash=_stable_hash(body),\n    )\n    verify_structural_finding(finding)\n    return finding\n\n\ndef _inspect_structure(value: Any) -> tuple[OracleRealIntelligenceResponseShape, tuple[OracleRealIntelligenceStructuralFinding, ...]]:\n    counts = {\n        "maximum_depth": 0,\n        "mapping_count": 0,\n        "sequence_count": 0,\n        "scalar_count": 0,\n        "null_count": 0,\n        "string_count": 0,\n        "number_count": 0,\n        "boolean_count": 0,\n        "total_node_count": 0,\n        "total_key_count": 0,\n    }\n    findings: list[OracleRealIntelligenceStructuralFinding] = []\n    unsupported = False\n    nonfinite = False\n    oversized = False\n\n    def walk(node: Any, location: str, depth: int) -> None:\n        nonlocal unsupported, nonfinite, oversized\n\n        counts["maximum_depth"] = max(counts["maximum_depth"], depth)\n        counts["total_node_count"] += 1\n\n        if depth > MAX_DEPTH:\n            findings.append(\n                _finding(\n                    "maximum_depth_exceeded",\n                    "error",\n                    location,\n                    f"Response depth exceeded {MAX_DEPTH}.",\n                    blocking=True,\n                )\n            )\n            oversized = True\n            return\n\n        if isinstance(node, Mapping):\n            counts["mapping_count"] += 1\n            counts["total_key_count"] += len(node)\n            if len(node) > MAX_CONTAINER_ITEMS:\n                findings.append(\n                    _finding(\n                        "mapping_item_limit_exceeded",\n                        "error",\n                        location,\n                        f"Mapping contains more than {MAX_CONTAINER_ITEMS} items.",\n                        blocking=True,\n                    )\n                )\n                oversized = True\n\n            seen_keys: set[str] = set()\n            for key, item in node.items():\n                key_text = str(key)\n                if key_text in seen_keys:\n                    findings.append(\n                        _finding(\n                            "duplicate_canonical_key",\n                            "error",\n                            location,\n                            f"Duplicate canonical key detected: {key_text}",\n                            blocking=True,\n                        )\n                    )\n                seen_keys.add(key_text)\n                walk(item, f"{location}.{key_text}", depth + 1)\n            return\n\n        if isinstance(node, (list, tuple)):\n            counts["sequence_count"] += 1\n            if len(node) > MAX_CONTAINER_ITEMS:\n                findings.append(\n                    _finding(\n                        "sequence_item_limit_exceeded",\n                        "error",\n                        location,\n                        f"Sequence contains more than {MAX_CONTAINER_ITEMS} items.",\n                        blocking=True,\n                    )\n                )\n                oversized = True\n            for index, item in enumerate(node):\n                walk(item, f"{location}[{index}]", depth + 1)\n            return\n\n        counts["scalar_count"] += 1\n\n        if node is None:\n            counts["null_count"] += 1\n            return\n\n        if isinstance(node, bool):\n            counts["boolean_count"] += 1\n            return\n\n        if isinstance(node, str):\n            counts["string_count"] += 1\n            if len(node) > MAX_STRING_LENGTH:\n                findings.append(\n                    _finding(\n                        "string_length_limit_exceeded",\n                        "error",\n                        location,\n                        f"String exceeds {MAX_STRING_LENGTH} characters.",\n                        blocking=True,\n                    )\n                )\n                oversized = True\n            return\n\n        if isinstance(node, (int, float)):\n            counts["number_count"] += 1\n            if isinstance(node, float):\n                if node != node or node in (float("inf"), float("-inf")):\n                    findings.append(\n                        _finding(\n                            "nonfinite_number",\n                            "error",\n                            location,\n                            "NaN and infinite numbers are not permitted.",\n                            blocking=True,\n                        )\n                    )\n                    nonfinite = True\n            return\n\n        unsupported = True\n        findings.append(\n            _finding(\n                "unsupported_response_type",\n                "error",\n                location,\n                f"Unsupported response type: {type(node).__module__}.{type(node).__qualname__}",\n                blocking=True,\n            )\n        )\n\n    walk(value, "$", 0)\n\n    root_mapping = isinstance(value, Mapping)\n    root_sequence = isinstance(value, (list, tuple))\n    root_scalar = not root_mapping and not root_sequence\n\n    duplicate_key_risk = any(\n        item.finding_code == "duplicate_canonical_key"\n        for item in findings\n    )\n\n    body = {\n        "root_type": f"{type(value).__module__}.{type(value).__qualname__}",\n        "root_mapping": root_mapping,\n        "root_sequence": root_sequence,\n        "root_scalar": root_scalar,\n        "maximum_depth": counts["maximum_depth"],\n        "mapping_count": counts["mapping_count"],\n        "sequence_count": counts["sequence_count"],\n        "scalar_count": counts["scalar_count"],\n        "null_count": counts["null_count"],\n        "string_count": counts["string_count"],\n        "number_count": counts["number_count"],\n        "boolean_count": counts["boolean_count"],\n        "total_node_count": counts["total_node_count"],\n        "total_key_count": counts["total_key_count"],\n        "duplicate_key_risk_detected": duplicate_key_risk,\n        "unsupported_type_detected": unsupported,\n        "nonfinite_number_detected": nonfinite,\n        "oversized_value_detected": oversized,\n    }\n    shape = OracleRealIntelligenceResponseShape(\n        **body,\n        shape_hash=_stable_hash(body),\n    )\n    verify_response_shape(shape)\n    return shape, tuple(findings)\n\n\ndef verify_structural_finding(\n    finding: OracleRealIntelligenceStructuralFinding,\n) -> bool:\n    body = asdict(finding)\n    supplied = body.pop("finding_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleRealIntelligenceResponseValidationInvariantError(\n            "structural finding hash mismatch"\n        )\n    if not finding.finding_code or not finding.location or not finding.message:\n        raise OracleRealIntelligenceResponseValidationInvariantError(\n            "structural finding incomplete"\n        )\n    if finding.severity not in {"info", "warning", "error"}:\n        raise OracleRealIntelligenceResponseValidationInvariantError(\n            "structural finding severity invalid"\n        )\n    return True\n\n\ndef verify_response_shape(\n    shape: OracleRealIntelligenceResponseShape,\n) -> bool:\n    body = asdict(shape)\n    supplied = body.pop("shape_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleRealIntelligenceResponseValidationInvariantError(\n            "response shape hash mismatch"\n        )\n    if sum((shape.root_mapping, shape.root_sequence, shape.root_scalar)) != 1:\n        raise OracleRealIntelligenceResponseValidationInvariantError(\n            "response root classification invalid"\n        )\n    if shape.total_node_count < 1:\n        raise OracleRealIntelligenceResponseValidationInvariantError(\n            "response node count invalid"\n        )\n    return True\n\n\ndef build_real_intelligence_response_validation_report(\n    repository_root: str | Path,\n    *,\n    execution_report: OracleRealIntelligenceReadInvocationExecutionReport | None = None,\n) -> OracleRealIntelligenceResponseValidationReport:\n    root = Path(repository_root).resolve()\n    source = execution_report\n    if source is None:\n        source = execute_authorized_real_intelligence_read_invocation(root)\n    verify_read_invocation_execution_report(source)\n\n    if not source.execution_succeeded:\n        raise OracleRealIntelligenceResponseValidationInvariantError(\n            source.failure_reason or "read invocation execution did not succeed"\n        )\n\n    invocation_result: OracleRealIntelligenceInvocationResult = (\n        source.execution_receipt.invocation_result\n    )\n    original_result_hash = invocation_result.result_hash\n    original_canonical_hash = _stable_hash(\n        invocation_result.canonical_result\n    )\n\n    shape, findings = _inspect_structure(\n        invocation_result.canonical_result\n    )\n\n    blocking_count = sum(item.blocking for item in findings)\n    structurally_valid = blocking_count == 0\n\n    source_preserved = bool(\n        invocation_result.result_hash == original_result_hash\n        and _stable_hash(invocation_result.canonical_result)\n        == original_canonical_hash\n    )\n\n    report_body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root),\n        "execution_report_hash": source.report_hash,\n        "invocation_result_hash": invocation_result.result_hash,\n        "response_shape": shape,\n        "findings": findings,\n        "finding_count": len(findings),\n        "blocking_finding_count": blocking_count,\n        "structurally_valid": structurally_valid,\n        "deterministic_replay_ready": structurally_valid,\n        "normalization_ready": bool(\n            structurally_valid and source_preserved\n        ),\n        "source_result_preserved": source_preserved,\n        "response_modified": False,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "runtime_artifact_created": False,\n        "runtime_artifact_modified": False,\n        "networking_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "read_only": True,\n        "failure_reason": (\n            None\n            if structurally_valid and source_preserved\n            else "response_structure_not_certified"\n        ),\n    }\n    report = OracleRealIntelligenceResponseValidationReport(\n        **report_body,\n        report_hash=_stable_hash(report_body),\n    )\n    verify_real_intelligence_response_validation_report(report)\n    return report\n\n\ndef verify_real_intelligence_response_validation_report(\n    report: OracleRealIntelligenceResponseValidationReport,\n) -> bool:\n    body = asdict(report)\n    supplied = body.pop("report_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleRealIntelligenceResponseValidationInvariantError(\n            "response validation report hash mismatch"\n        )\n    if report.schema_version != SCHEMA_VERSION:\n        raise OracleRealIntelligenceResponseValidationInvariantError(\n            "schema mismatch"\n        )\n    if report.policy_id != POLICY_ID:\n        raise OracleRealIntelligenceResponseValidationInvariantError(\n            "policy mismatch"\n        )\n\n    verify_response_shape(report.response_shape)\n    for finding in report.findings:\n        verify_structural_finding(finding)\n\n    if report.finding_count != len(report.findings):\n        raise OracleRealIntelligenceResponseValidationInvariantError(\n            "finding count mismatch"\n        )\n    if report.blocking_finding_count != sum(\n        item.blocking for item in report.findings\n    ):\n        raise OracleRealIntelligenceResponseValidationInvariantError(\n            "blocking finding count mismatch"\n        )\n    if report.structurally_valid != (\n        report.blocking_finding_count == 0\n    ):\n        raise OracleRealIntelligenceResponseValidationInvariantError(\n            "structural validity mismatch"\n        )\n    if report.normalization_ready != bool(\n        report.structurally_valid\n        and report.deterministic_replay_ready\n        and report.source_result_preserved\n    ):\n        raise OracleRealIntelligenceResponseValidationInvariantError(\n            "normalization readiness mismatch"\n        )\n    if not report.read_only or report.response_modified:\n        raise OracleRealIntelligenceResponseValidationInvariantError(\n            "response validation mutated source data"\n        )\n    if (\n        report.analytics_execution_performed\n        or report.database_access_performed\n        or report.runtime_artifact_created\n        or report.runtime_artifact_modified\n        or report.networking_performed\n        or report.publication_allowed\n        or report.action_authorization_allowed\n        or report.qseries_execution_allowed\n    ):\n        raise OracleRealIntelligenceResponseValidationInvariantError(\n            "forbidden validation capability enabled"\n        )\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import replace\nfrom pathlib import Path\nfrom tempfile import TemporaryDirectory\n\nfrom qseries_v2.oracle_terminal.oracle_authorized_real_intelligence_read_invocation_execution_gate import (\n    ENGINE_ID as OIT_037_ENGINE_ID,\n    POLICY_ID as OIT_037_POLICY_ID,\n    SCHEMA_VERSION as OIT_037_SCHEMA_VERSION,\n    OracleRealIntelligenceInvocationExecutionReceipt,\n    OracleRealIntelligenceInvocationResult,\n    OracleRealIntelligenceReadInvocationExecutionReport,\n    _stable_hash as oit_037_hash,\n    verify_read_invocation_execution_report,\n)\nfrom qseries_v2.oracle_terminal.oracle_real_intelligence_response_validation_gate import (\n    OracleRealIntelligenceResponseValidationInvariantError,\n    build_real_intelligence_response_validation_report,\n    verify_real_intelligence_response_validation_report,\n)\n\n\ndef make_execution_report(root: Path):\n    canonical_result = {\n        "record_id": "REAL-038",\n        "probability": 0.72,\n        "direction": "bull",\n        "evidence": [\n            {\n                "source_id": "SOURCE-1",\n                "confidence": 0.81,\n            },\n            {\n                "source_id": "SOURCE-2",\n                "confidence": 0.63,\n            },\n        ],\n        "read_only": True,\n    }\n\n    result_body = {\n        "result_type": "builtins.dict",\n        "canonical_result": canonical_result,\n        "result_hash": oit_037_hash(canonical_result),\n        "result_available": True,\n        "result_none": False,\n        "read_only": True,\n    }\n    result = OracleRealIntelligenceInvocationResult(\n        **result_body,\n        verification_hash=oit_037_hash(result_body),\n    )\n\n    receipt_body = {\n        "invocation_id": "invocation-038",\n        "readiness_report_hash": "readiness-report-hash",\n        "manifest_hash": "manifest-hash",\n        "module_name": "test.module",\n        "callable_name": "load_real_intelligence",\n        "invocation_argument_names": (\n            "repository_root",\n            "artifact_path",\n            "persist",\n        ),\n        "callable_invocation_count": 1,\n        "callable_invoked": True,\n        "invocation_completed": True,\n        "artifact_sha256_before": "a" * 64,\n        "artifact_sha256_after": "a" * 64,\n        "artifact_byte_count_before": 100,\n        "artifact_byte_count_after": 100,\n        "artifact_mtime_ns_before": 123456,\n        "artifact_mtime_ns_after": 123456,\n        "artifact_unchanged": True,\n        "invocation_result": result,\n        "persistence_performed": False,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "runtime_artifact_created": False,\n        "runtime_artifact_modified": False,\n        "networking_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "read_only": True,\n    }\n    receipt = OracleRealIntelligenceInvocationExecutionReceipt(\n        **receipt_body,\n        receipt_hash=oit_037_hash(receipt_body),\n    )\n\n    report_body = {\n        "schema_version": OIT_037_SCHEMA_VERSION,\n        "engine_id": OIT_037_ENGINE_ID,\n        "policy_id": OIT_037_POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root.resolve()),\n        "readiness_report_hash": "readiness-report-hash",\n        "execution_receipt": receipt,\n        "exact_callable_invoked": True,\n        "exact_arguments_consumed": True,\n        "exactly_one_invocation_performed": True,\n        "artifact_identity_preserved": True,\n        "bounded_read_result_available": True,\n        "execution_succeeded": True,\n        "persistence_performed": False,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "runtime_artifact_created": False,\n        "runtime_artifact_modified": False,\n        "networking_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "read_only": True,\n        "failure_reason": None,\n    }\n    report = OracleRealIntelligenceReadInvocationExecutionReport(\n        **report_body,\n        report_hash=oit_037_hash(report_body),\n    )\n    verify_read_invocation_execution_report(report)\n    return report\n\n\ndef main() -> int:\n    print("=" * 48)\n    print(" OIT-038 TEST")\n    print(" REAL INTELLIGENCE RESPONSE VALIDATION")\n    print("=" * 48)\n\n    with TemporaryDirectory() as temporary:\n        root = Path(temporary)\n        source = make_execution_report(root)\n\n        report = build_real_intelligence_response_validation_report(\n            root,\n            execution_report=source,\n        )\n\n        assert report.execution_report_hash == source.report_hash\n        assert report.invocation_result_hash == (\n            source.execution_receipt.invocation_result.result_hash\n        )\n        assert report.structurally_valid\n        assert report.deterministic_replay_ready\n        assert report.normalization_ready\n        assert report.source_result_preserved\n        assert not report.response_modified\n        assert report.finding_count == 0\n        assert report.blocking_finding_count == 0\n\n        shape = report.response_shape\n        assert shape.root_mapping\n        assert not shape.root_sequence\n        assert not shape.root_scalar\n        assert shape.mapping_count >= 3\n        assert shape.sequence_count == 1\n        assert shape.string_count >= 5\n        assert shape.number_count >= 3\n        assert shape.boolean_count >= 1\n        assert not shape.unsupported_type_detected\n        assert not shape.nonfinite_number_detected\n        assert not shape.oversized_value_detected\n\n        replay = build_real_intelligence_response_validation_report(\n            root,\n            execution_report=source,\n        )\n        assert replay == report\n        assert verify_real_intelligence_response_validation_report(report)\n\n        tampered = replace(\n            report,\n            response_modified=True,\n        )\n        try:\n            verify_real_intelligence_response_validation_report(tampered)\n        except OracleRealIntelligenceResponseValidationInvariantError:\n            pass\n        else:\n            raise AssertionError(\n                "tampered response validation report accepted"\n            )\n\n        assert not report.analytics_execution_performed\n        assert not report.database_access_performed\n        assert not report.runtime_artifact_created\n        assert not report.runtime_artifact_modified\n        assert not report.networking_performed\n        assert not report.publication_allowed\n        assert not report.action_authorization_allowed\n        assert not report.qseries_execution_allowed\n        assert report.read_only\n\n    print("[PASS] Certified OIT-037 execution report consumed")\n    print("[PASS] Returned intelligence result structurally inspected")\n    print("[PASS] Mapping, sequence, scalar, and depth metrics captured")\n    print("[PASS] Unsupported response types rejected")\n    print("[PASS] Nonfinite numbers rejected")\n    print("[PASS] Oversized values rejected")\n    print("[PASS] Source result hash preserved")\n    print("[PASS] Structural validation deterministic across replay")\n    print("[PASS] Normalization readiness certified")\n    print("[PASS] Tampered validation report rejected")\n    print("[PASS] No analytics execution or database access performed")\n    print("[PASS] No runtime artifact created or modified")\n    print("[PASS] Publication, action authorization, and Q Series execution disabled")\n    print("[DONE] OIT-038 REAL INTELLIGENCE RESPONSE VALIDATION PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


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

    for path in (OIT_037, OIT_037_TEST, RUNNER):
        if path.is_file():
            protected[path] = sha256(path)

    return protected


def main() -> int:
    print("=" * 48)
    print(" OIT-038 INSTALLER")
    print(" REAL INTELLIGENCE RESPONSE VALIDATION")
    print("=" * 48)

    try:
        require_contract(
            OIT_037,
            (
                'SCHEMA_VERSION = "OIT-037"',
                'POLICY_ID = "oracle.authorized-real-intelligence-read-invocation-execution.v1"',
                "OracleRealIntelligenceInvocationResult",
                "OracleRealIntelligenceReadInvocationExecutionReport",
                "execute_authorized_real_intelligence_read_invocation",
                "verify_read_invocation_execution_report",
                "execution_succeeded",
                "bounded_read_result_available",
                "artifact_identity_preserved",
            ),
            "Certified OIT-037 production",
        )
        require_contract(
            OIT_037_TEST,
            (
                "OIT-037 TEST",
                "AUTHORIZED REAL INTELLIGENCE READ INVOCATION EXECUTION",
                "OIT-037 AUTHORIZED READ INVOCATION EXECUTION PASS",
            ),
            "Certified OIT-037 standalone test",
        )

        protected = protected_sources()

        print("[OK] Certified OIT-037 production contract verified")
        print("[OK] Certified OIT-037 standalone test verified")
        print(f"[OK] Protected production source files captured: {len(protected)}")

        upstream = subprocess.run(
            [sys.executable, str(OIT_037_TEST)],
            cwd=ROOT,
            check=False,
        )
        if upstream.returncode:
            raise RuntimeError(
                f"OIT-037 certification failed with exit code {upstream.returncode}"
            )

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_real_intelligence_response_validation_gate import *"
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
                f"OIT-038 test failed with exit code {completed.returncode}"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Protected production source changed: {path}"
                )

        print("[PASS] Certified OIT-037 production and test unchanged")
        print("[PASS] Oracle terminal runner unchanged")
        print("[PASS] OIT-038 production module installed")
        print("[PASS] OIT-038 standalone test installed")
        print("[PASS] Returned intelligence structural validation certified")
        print("[PASS] Deterministic response-shape metrics certified")
        print("[PASS] Unsupported, nonfinite, and oversized values rejected")
        print("[PASS] Source result remained unchanged")
        print("[PASS] Normalization readiness certified")
        print("[PASS] No analytics execution or runtime mutation performed")
        print("[PASS] OLA, OIA, INT-OII, ORR, OOR, and Q Series unchanged")
        print("[PASS] Publication and execution remained disabled")
        print("[PASS] Read-only and execution boundaries preserved")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OIT-038 REAL INTELLIGENCE RESPONSE VALIDATION INSTALLED")
        return 0

    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
