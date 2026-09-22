from __future__ import annotations

import hashlib
import sys
import types
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from qseries_v2.oracle_terminal.oracle_authorized_real_intelligence_read_invocation_readiness_gate import (
    ENGINE_ID as OIT_036_ENGINE_ID,
    POLICY_ID as OIT_036_POLICY_ID,
    SCHEMA_VERSION as OIT_036_SCHEMA_VERSION,
    OracleRealIntelligenceInvocationArgument,
    OracleRealIntelligenceReadInvocationManifest,
    OracleRealIntelligenceReadInvocationReadinessReport,
    _stable_hash as oit_036_hash,
    verify_read_invocation_readiness_report,
)
from qseries_v2.oracle_terminal.oracle_authorized_real_intelligence_read_invocation_execution_gate import (
    OracleRealIntelligenceReadInvocationExecutionInvariantError,
    execute_authorized_real_intelligence_read_invocation,
    verify_read_invocation_execution_report,
)


def make_readiness(root: Path, module_name: str):
    artifact = (
        root
        / "runtime"
        / "oracle_intelligence"
        / "real_intelligence.json"
    )
    artifact.parent.mkdir(parents=True)
    artifact.write_bytes(
        b'{"record_id":"REAL-037","probability":0.71}'
    )

    arguments = []
    definitions = (
        (
            "repository_root",
            0,
            "repository_root",
            str(root.resolve()),
            "session-lineage",
        ),
        (
            "artifact_path",
            1,
            "authorized_artifact_path",
            str(artifact.resolve()),
            "artifact-lineage",
        ),
        (
            "persist",
            2,
            "boolean",
            "false",
            "session-lineage",
        ),
    )
    for name, position, kind, value, lineage in definitions:
        body = {
            "argument_name": name,
            "argument_position": position,
            "value_kind": kind,
            "canonical_value": value,
            "source_lineage_hash": lineage,
            "read_only": True,
        }
        arguments.append(
            OracleRealIntelligenceInvocationArgument(
                **body,
                argument_hash=oit_036_hash(body),
            )
        )

    manifest_body = {
        "invocation_id": "invocation-037",
        "session_hash": "session-hash",
        "module_name": module_name,
        "callable_name": "load_real_intelligence",
        "callable_signature": (
            "repository_root",
            "artifact_path",
            "persist",
        ),
        "invocation_arguments": tuple(arguments),
        "invocation_argument_count": 3,
        "exact_signature_bound": True,
        "exact_artifact_path_bound": True,
        "repository_root_bound": True,
        "persist_argument_present": True,
        "persist_argument_value": False,
        "invocation_ready": True,
        "callable_invoked": False,
        "read_only": True,
    }
    manifest = OracleRealIntelligenceReadInvocationManifest(
        **manifest_body,
        manifest_hash=oit_036_hash(manifest_body),
    )

    report_body = {
        "schema_version": OIT_036_SCHEMA_VERSION,
        "engine_id": OIT_036_ENGINE_ID,
        "policy_id": OIT_036_POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root.resolve()),
        "read_session_report_hash": "read-session-report-hash",
        "invocation_manifest": manifest,
        "exact_callable_identity_verified": True,
        "exact_callable_signature_verified": True,
        "exact_argument_binding_verified": True,
        "persistence_disabled": True,
        "bounded_single_artifact_verified": True,
        "invocation_ready": True,
        "invocation_performed": False,
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
    report = OracleRealIntelligenceReadInvocationReadinessReport(
        **report_body,
        report_hash=oit_036_hash(report_body),
    )
    verify_read_invocation_readiness_report(report)
    return report, artifact


def main() -> int:
    print("=" * 48)
    print(" OIT-037 TEST")
    print(" AUTHORIZED REAL INTELLIGENCE READ INVOCATION EXECUTION")
    print("=" * 48)

    module_name = "oit_037_test_callable"
    module = types.ModuleType(module_name)
    call_count = {"value": 0}

    def load_real_intelligence(
        repository_root,
        artifact_path,
        persist,
    ):
        call_count["value"] += 1
        assert isinstance(repository_root, Path)
        assert isinstance(artifact_path, Path)
        assert persist is False
        return {
            "record_id": "REAL-037",
            "source_sha256": hashlib.sha256(
                artifact_path.read_bytes()
            ).hexdigest(),
            "read_only": True,
        }

    module.load_real_intelligence = load_real_intelligence
    sys.modules[module_name] = module

    try:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            readiness, artifact = make_readiness(root, module_name)
            before = artifact.read_bytes()
            before_mtime = artifact.stat().st_mtime_ns

            report = execute_authorized_real_intelligence_read_invocation(
                root,
                readiness_report=readiness,
            )

            assert call_count["value"] == 1
            assert report.execution_succeeded
            assert report.exact_callable_invoked
            assert report.exact_arguments_consumed
            assert report.exactly_one_invocation_performed
            assert report.artifact_identity_preserved
            assert report.bounded_read_result_available

            receipt = report.execution_receipt
            assert receipt.callable_invocation_count == 1
            assert receipt.callable_invoked
            assert receipt.invocation_completed
            assert receipt.artifact_unchanged
            assert receipt.invocation_result.result_available
            assert not receipt.invocation_result.result_none
            assert receipt.invocation_result.canonical_result[
                "record_id"
            ] == "REAL-037"

            assert artifact.read_bytes() == before
            assert artifact.stat().st_mtime_ns == before_mtime

            assert not report.persistence_performed
            assert not report.analytics_execution_performed
            assert not report.database_access_performed
            assert not report.runtime_artifact_created
            assert not report.runtime_artifact_modified
            assert not report.networking_performed
            assert not report.publication_allowed
            assert not report.action_authorization_allowed
            assert not report.qseries_execution_allowed

            assert verify_read_invocation_execution_report(report)

            tampered = replace(
                report,
                runtime_artifact_modified=True,
            )
            try:
                verify_read_invocation_execution_report(tampered)
            except OracleRealIntelligenceReadInvocationExecutionInvariantError:
                pass
            else:
                raise AssertionError(
                    "tampered execution report accepted"
                )

        print("[PASS] Certified OIT-036 invocation readiness consumed")
        print("[PASS] Exact authorized callable invoked")
        print("[PASS] Exact bound arguments consumed")
        print("[PASS] Persist=false enforced")
        print("[PASS] Exactly one invocation performed")
        print("[PASS] Bounded read result captured")
        print("[PASS] Result canonicalized and hash verified")
        print("[PASS] Artifact SHA-256 preserved")
        print("[PASS] Artifact byte count and modification time preserved")
        print("[PASS] No persistence or analytics execution performed")
        print("[PASS] No database or networking access performed")
        print("[PASS] No runtime artifact created or modified")
        print("[PASS] Tampered execution report rejected")
        print("[PASS] Publication, action authorization, and Q Series execution disabled")
        print("[DONE] OIT-037 AUTHORIZED READ INVOCATION EXECUTION PASS")
        return 0
    finally:
        sys.modules.pop(module_name, None)


if __name__ == "__main__":
    raise SystemExit(main())
