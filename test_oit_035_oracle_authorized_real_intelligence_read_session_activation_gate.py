from __future__ import annotations

import hashlib
import sys
import types
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from qseries_v2.oracle_terminal.oracle_real_intelligence_input_binding_authorization_gate import (
    ENGINE_ID as OIT_034_ENGINE_ID,
    POLICY_ID as OIT_034_POLICY_ID,
    SCHEMA_VERSION as OIT_034_SCHEMA_VERSION,
    OracleAuthorizedArtifact,
    OracleAuthorizedCallable,
    OracleRealIntelligenceAuthorizationReport,
    _hash as oit_034_hash,
    verify_real_intelligence_binding_authorization_report,
)
from qseries_v2.oracle_terminal.oracle_authorized_real_intelligence_read_session_activation_gate import (
    OracleRealIntelligenceReadSessionInvariantError,
    activate_authorized_real_intelligence_read_session,
    verify_read_session_activation_report,
)


def make_authorization(root: Path, module_name: str):
    artifact_path = root / "runtime" / "oracle_intelligence" / "real.json"
    artifact_path.parent.mkdir(parents=True)
    content = b'{"record_id":"REAL-035","probability":0.64}'
    artifact_path.write_bytes(content)

    artifact_body = {
        "relative_path": "runtime/oracle_intelligence/real.json",
        "byte_count": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
        "source_candidate_hash": "artifact-candidate-hash",
        "authorization_granted": True,
    }
    artifact = OracleAuthorizedArtifact(
        **artifact_body,
        authorization_hash=oit_034_hash(artifact_body),
    )

    callable_body = {
        "module_name": module_name,
        "callable_name": "load_real_intelligence",
        "signature": ("repository_root", "artifact_path"),
        "source_candidate_hash": "callable-candidate-hash",
        "authorization_granted": True,
    }
    callable_item = OracleAuthorizedCallable(
        **callable_body,
        authorization_hash=oit_034_hash(callable_body),
    )

    report_body = {
        "schema_version": OIT_034_SCHEMA_VERSION,
        "engine_id": OIT_034_ENGINE_ID,
        "policy_id": OIT_034_POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root.resolve()),
        "readiness_report_hash": "readiness-report-hash",
        "authorized_artifact": artifact,
        "authorized_callable": callable_item,
        "exact_artifact_hash_required": True,
        "exact_artifact_byte_count_required": True,
        "read_only_invocation_required": True,
        "lower_level_bypass_allowed": False,
        "persistence_allowed": False,
        "analytics_execution_allowed": False,
        "database_access_allowed": False,
        "networking_allowed": False,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
        "real_input_binding_authorized": True,
        "read_only": True,
        "failure_reason": None,
    }
    report = OracleRealIntelligenceAuthorizationReport(
        **report_body,
        report_hash=oit_034_hash(report_body),
    )
    verify_real_intelligence_binding_authorization_report(report)
    return report, artifact_path


def main() -> int:
    print("=" * 48)
    print(" OIT-035 TEST")
    print(" AUTHORIZED REAL INTELLIGENCE READ SESSION")
    print("=" * 48)

    module_name = "oit_035_test_read_callable"
    module = types.ModuleType(module_name)

    def load_real_intelligence(repository_root, artifact_path):
        raise AssertionError("callable must not be invoked in OIT-035")

    module.load_real_intelligence = load_real_intelligence
    sys.modules[module_name] = module

    try:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            authorization, artifact_path = make_authorization(
                root,
                module_name,
            )
            before = artifact_path.read_bytes()
            before_mtime = artifact_path.stat().st_mtime_ns

            report = activate_authorized_real_intelligence_read_session(
                root,
                authorization_report=authorization,
            )

            assert report.artifact_identity_verified
            assert report.callable_identity_verified
            assert report.callable_signature_verified
            assert report.read_session_active
            assert report.consumption_invocation_ready
            assert report.read_session.bounded_single_artifact
            assert report.read_session.artifact_content_byte_count == len(before)
            assert report.read_session.artifact_content_sha256 == (
                hashlib.sha256(before).hexdigest()
            )
            assert report.read_session.artifact_read_receipt.opened_read_only
            assert not report.read_session.artifact_read_receipt.content_mutated
            assert not report.read_session.callable_resolution.callable_invoked

            assert artifact_path.read_bytes() == before
            assert artifact_path.stat().st_mtime_ns == before_mtime

            assert not report.analytics_execution_performed
            assert not report.callable_invocation_performed
            assert not report.database_access_performed
            assert not report.runtime_artifact_created
            assert not report.runtime_artifact_modified
            assert not report.networking_performed
            assert not report.publication_allowed
            assert not report.action_authorization_allowed
            assert not report.qseries_execution_allowed

            replay = activate_authorized_real_intelligence_read_session(
                root,
                authorization_report=authorization,
            )
            assert replay == report
            assert verify_read_session_activation_report(report)

            tampered = replace(
                report,
                callable_invocation_performed=True,
            )
            try:
                verify_read_session_activation_report(tampered)
            except OracleRealIntelligenceReadSessionInvariantError:
                pass
            else:
                raise AssertionError(
                    "tampered read-session report accepted"
                )

        print("[PASS] Certified OIT-034 authorization consumed")
        print("[PASS] Exact authorized artifact reopened read-only")
        print("[PASS] Artifact SHA-256 reverified")
        print("[PASS] Artifact byte count reverified")
        print("[PASS] Artifact bytes and modification time unchanged")
        print("[PASS] Exact authorized callable resolved")
        print("[PASS] Callable signature verified")
        print("[PASS] Callable remained uninvoked")
        print("[PASS] Bounded single-artifact read session activated")
        print("[PASS] Read session deterministic across replay")
        print("[PASS] Tampered read-session report rejected")
        print("[PASS] No analytics execution or database access performed")
        print("[PASS] No runtime artifact created or modified")
        print("[PASS] Publication, action authorization, and Q Series execution disabled")
        print("[DONE] OIT-035 AUTHORIZED REAL INTELLIGENCE READ SESSION PASS")
        return 0
    finally:
        sys.modules.pop(module_name, None)


if __name__ == "__main__":
    raise SystemExit(main())
