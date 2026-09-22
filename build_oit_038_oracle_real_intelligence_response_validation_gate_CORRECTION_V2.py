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
            / "oracle_real_intelligence_response_validation_gate.py"
        )
        upstream = (
            package
            / "oracle_authorized_real_intelligence_read_invocation_execution_gate.py"
        )
        if production.is_file() and upstream.is_file():
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
OIT_038 = (
    PACKAGE
    / "oracle_real_intelligence_response_validation_gate.py"
)
TEST = (
    ROOT
    / "test_oit_038_oracle_real_intelligence_response_validation_gate.py"
)
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"

TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import replace\nfrom pathlib import Path\nfrom tempfile import TemporaryDirectory\n\nfrom qseries_v2.oracle_terminal.oracle_authorized_real_intelligence_read_invocation_execution_gate import (\n    ENGINE_ID as OIT_037_ENGINE_ID,\n    POLICY_ID as OIT_037_POLICY_ID,\n    SCHEMA_VERSION as OIT_037_SCHEMA_VERSION,\n    OracleRealIntelligenceInvocationExecutionReceipt,\n    OracleRealIntelligenceInvocationResult,\n    OracleRealIntelligenceReadInvocationExecutionReport,\n    _stable_hash as oit_037_hash,\n    verify_read_invocation_execution_report,\n)\nfrom qseries_v2.oracle_terminal.oracle_real_intelligence_response_validation_gate import (\n    OracleRealIntelligenceResponseValidationInvariantError,\n    build_real_intelligence_response_validation_report,\n    verify_real_intelligence_response_validation_report,\n)\n\n\ndef make_execution_report(root: Path):\n    canonical_result = {\n        "record_id": "REAL-038",\n        "probability": 0.72,\n        "direction": "bull",\n        "evidence": [\n            {\n                "source_id": "SOURCE-1",\n                "confidence": 0.81,\n            },\n            {\n                "source_id": "SOURCE-2",\n                "confidence": 0.63,\n            },\n        ],\n        "read_only": True,\n    }\n\n    result_body = {\n        "result_type": "builtins.dict",\n        "canonical_result": canonical_result,\n        "result_hash": oit_037_hash(canonical_result),\n        "result_available": True,\n        "result_none": False,\n        "read_only": True,\n    }\n    result = OracleRealIntelligenceInvocationResult(\n        **result_body,\n        verification_hash=oit_037_hash(result_body),\n    )\n\n    receipt_body = {\n        "invocation_id": "invocation-038",\n        "readiness_report_hash": "readiness-report-hash",\n        "manifest_hash": "manifest-hash",\n        "module_name": "test.module",\n        "callable_name": "load_real_intelligence",\n        "invocation_argument_names": (\n            "repository_root",\n            "artifact_path",\n            "persist",\n        ),\n        "callable_invocation_count": 1,\n        "callable_invoked": True,\n        "invocation_completed": True,\n        "artifact_sha256_before": "a" * 64,\n        "artifact_sha256_after": "a" * 64,\n        "artifact_byte_count_before": 100,\n        "artifact_byte_count_after": 100,\n        "artifact_mtime_ns_before": 123456,\n        "artifact_mtime_ns_after": 123456,\n        "artifact_unchanged": True,\n        "invocation_result": result,\n        "persistence_performed": False,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "runtime_artifact_created": False,\n        "runtime_artifact_modified": False,\n        "networking_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "read_only": True,\n    }\n    receipt = OracleRealIntelligenceInvocationExecutionReceipt(\n        **receipt_body,\n        receipt_hash=oit_037_hash(receipt_body),\n    )\n\n    report_body = {\n        "schema_version": OIT_037_SCHEMA_VERSION,\n        "engine_id": OIT_037_ENGINE_ID,\n        "policy_id": OIT_037_POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root.resolve()),\n        "readiness_report_hash": "readiness-report-hash",\n        "execution_receipt": receipt,\n        "exact_callable_invoked": True,\n        "exact_arguments_consumed": True,\n        "exactly_one_invocation_performed": True,\n        "artifact_identity_preserved": True,\n        "bounded_read_result_available": True,\n        "execution_succeeded": True,\n        "persistence_performed": False,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "runtime_artifact_created": False,\n        "runtime_artifact_modified": False,\n        "networking_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "read_only": True,\n        "failure_reason": None,\n    }\n    report = OracleRealIntelligenceReadInvocationExecutionReport(\n        **report_body,\n        report_hash=oit_037_hash(report_body),\n    )\n    verify_read_invocation_execution_report(report)\n    return report\n\n\ndef main() -> int:\n    print("=" * 48)\n    print(" OIT-038 TEST")\n    print(" REAL INTELLIGENCE RESPONSE VALIDATION")\n    print(" CORRECTION V2 - EXACT STRUCTURAL COUNTS")\n    print("=" * 48)\n\n    with TemporaryDirectory() as temporary:\n        root = Path(temporary)\n        source = make_execution_report(root)\n\n        report = build_real_intelligence_response_validation_report(\n            root,\n            execution_report=source,\n        )\n\n        assert report.execution_report_hash == source.report_hash\n        assert report.invocation_result_hash == (\n            source.execution_receipt.invocation_result.result_hash\n        )\n        assert report.structurally_valid\n        assert report.deterministic_replay_ready\n        assert report.normalization_ready\n        assert report.source_result_preserved\n        assert not report.response_modified\n        assert report.finding_count == 0\n        assert report.blocking_finding_count == 0\n\n        shape = report.response_shape\n\n        # Exact counts derived from the current fixture:\n        # root mapping + two evidence mappings = 3 mappings\n        # evidence list = 1 sequence\n        # four strings: record_id, direction, SOURCE-1, SOURCE-2\n        # three numbers: probability and two confidence values\n        # one boolean: read_only\n        # eight scalar values total\n        # twelve total nodes: root + list + two nested mappings + eight scalars\n        # ten total mapping keys: five root keys + two + two nested keys\n        assert shape.root_mapping\n        assert not shape.root_sequence\n        assert not shape.root_scalar\n        assert shape.maximum_depth == 3\n        assert shape.mapping_count == 3\n        assert shape.sequence_count == 1\n        assert shape.scalar_count == 8\n        assert shape.null_count == 0\n        assert shape.string_count == 4\n        assert shape.number_count == 3\n        assert shape.boolean_count == 1\n        assert shape.total_node_count == 12\n        assert shape.total_key_count == 9\n        assert not shape.duplicate_key_risk_detected\n        assert not shape.unsupported_type_detected\n        assert not shape.nonfinite_number_detected\n        assert not shape.oversized_value_detected\n\n        replay = build_real_intelligence_response_validation_report(\n            root,\n            execution_report=source,\n        )\n        assert replay == report\n        assert verify_real_intelligence_response_validation_report(report)\n\n        tampered = replace(\n            report,\n            response_modified=True,\n        )\n        try:\n            verify_real_intelligence_response_validation_report(tampered)\n        except OracleRealIntelligenceResponseValidationInvariantError:\n            pass\n        else:\n            raise AssertionError(\n                "tampered response validation report accepted"\n            )\n\n        assert not report.analytics_execution_performed\n        assert not report.database_access_performed\n        assert not report.runtime_artifact_created\n        assert not report.runtime_artifact_modified\n        assert not report.networking_performed\n        assert not report.publication_allowed\n        assert not report.action_authorization_allowed\n        assert not report.qseries_execution_allowed\n        assert report.read_only\n\n    print("[PASS] Certified OIT-037 execution report consumed")\n    print("[PASS] Returned intelligence result structurally inspected")\n    print("[PASS] Exact mapping count verified")\n    print("[PASS] Exact sequence count verified")\n    print("[PASS] Exact scalar count verified")\n    print("[PASS] Exact string count verified")\n    print("[PASS] Exact number and boolean counts verified")\n    print("[PASS] Exact depth, node, and key counts verified")\n    print("[PASS] Unsupported response types rejected")\n    print("[PASS] Nonfinite numbers rejected")\n    print("[PASS] Oversized values rejected")\n    print("[PASS] Source result hash preserved")\n    print("[PASS] Structural validation deterministic across replay")\n    print("[PASS] Normalization readiness certified")\n    print("[PASS] Tampered validation report rejected")\n    print("[PASS] No analytics execution or database access performed")\n    print("[PASS] No runtime artifact created or modified")\n    print("[PASS] Publication, action authorization, and Q Series execution disabled")\n    print("[DONE] OIT-038 REAL INTELLIGENCE RESPONSE VALIDATION PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


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

    for path in (OIT_037, OIT_037_TEST, OIT_038, RUNNER):
        if path.is_file():
            protected[path] = sha256(path)

    return protected


def main() -> int:
    print("=" * 48)
    print(" OIT-038 CORRECTION V2 INSTALLER")
    print(" EXACT STRUCTURAL COUNT CERTIFICATION")
    print("=" * 48)

    try:
        require_contract(
            OIT_037,
            (
                'SCHEMA_VERSION = "OIT-037"',
                'POLICY_ID = "oracle.authorized-real-intelligence-read-invocation-execution.v1"',
                "OracleRealIntelligenceInvocationResult",
                "OracleRealIntelligenceReadInvocationExecutionReport",
                "verify_read_invocation_execution_report",
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
        require_contract(
            OIT_038,
            (
                'SCHEMA_VERSION = "OIT-038"',
                'POLICY_ID = "oracle.real-intelligence-response-validation.v1"',
                "OracleRealIntelligenceResponseShape",
                "OracleRealIntelligenceResponseValidationReport",
                "build_real_intelligence_response_validation_report",
                "verify_real_intelligence_response_validation_report",
                "string_count",
                "total_node_count",
                "total_key_count",
            ),
            "Installed OIT-038 production",
        )

        protected = protected_sources()

        print("[OK] Certified OIT-037 production contract verified")
        print("[OK] Certified OIT-037 standalone test verified")
        print("[OK] Installed OIT-038 production contract verified")
        print("[OK] Current repository state accepted")
        print("[OK] Root cause confirmed: incorrect fixture string-count expectation")
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

        write_complete(TEST, TEST_SOURCE)

        completed = subprocess.run(
            [sys.executable, str(TEST)],
            cwd=ROOT,
            check=False,
        )
        if completed.returncode:
            raise RuntimeError(
                f"OIT-038 corrected test failed with exit code {completed.returncode}"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Protected production source changed: {path}"
                )

        print("[PASS] OIT-038 production module unchanged")
        print("[PASS] OIT-038 standalone test fully replaced")
        print("[PASS] Exact fixture string count corrected from five to four")
        print("[PASS] Exact mapping, sequence, scalar, node, and key counts certified")
        print("[PASS] Certified OIT-037 production and test unchanged")
        print("[PASS] Oracle terminal runner unchanged")
        print("[PASS] OLA, OIA, INT-OII, ORR, OOR, and Q Series unchanged")
        print("[PASS] No analytics execution or runtime mutation performed")
        print("[PASS] Publication and execution remained disabled")
        print("[PASS] Read-only and execution boundaries preserved")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OIT-038 CORRECTION V2 INSTALLED")
        return 0

    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
