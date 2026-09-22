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
    activate_authorized_real_intelligence_read_session,
)
from qseries_v2.oracle_terminal.oracle_authorized_real_intelligence_read_invocation_readiness_gate import (
    OracleRealIntelligenceReadInvocationReadinessInvariantError,
    build_authorized_read_invocation_readiness_report,
    verify_read_invocation_readiness_report,
)


def make_authorization(root: Path, module_name: str):
    artifact_path = (
        root
        / "runtime"
        / "oracle_intelligence"
        / "real_intelligence.json"
    )
    artifact_path.parent.mkdir(parents=True)
    content = b'{"record_id":"REAL-036","probability":0.67}'
    artifact_path.write_bytes(content)

    artifact_body = {
        "relative_path": (
            "runtime/oracle_intelligence/real_intelligence.json"
        ),
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
        "signature": (
            "repository_root",
            "artifact_path",
            "persist",
        ),
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
    return report


def main() -> int:
    print("=" * 48)
    print(" OIT-036 TEST")
    print(" AUTHORIZED REAL INTELLIGENCE READ INVOCATION READINESS")
    print("=" * 48)

    module_name = "oit_036_test_callable"
    module = types.ModuleType(module_name)

    def load_real_intelligence(
        repository_root,
        artifact_path,
        persist,
    ):
        raise AssertionError("OIT-036 must not invoke the callable")

    module.load_real_intelligence = load_real_intelligence
    sys.modules[module_name] = module

    try:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            authorization = make_authorization(root, module_name)
            session = activate_authorized_real_intelligence_read_session(
                root,
                authorization_report=authorization,
            )

            report = build_authorized_read_invocation_readiness_report(
                root,
                read_session_report=session,
            )

            manifest = report.invocation_manifest

            assert report.invocation_ready
            assert report.exact_callable_identity_verified
            assert report.exact_callable_signature_verified
            assert report.exact_argument_binding_verified
            assert report.persistence_disabled
            assert report.bounded_single_artifact_verified

            assert manifest.invocation_argument_count == 3
            assert manifest.callable_signature == (
                "repository_root",
                "artifact_path",
                "persist",
            )
            assert manifest.exact_signature_bound
            assert manifest.exact_artifact_path_bound
            assert manifest.repository_root_bound
            assert manifest.persist_argument_present
            assert manifest.persist_argument_value is False
            assert manifest.invocation_ready
            assert not manifest.callable_invoked

            arguments = {
                argument.argument_name: argument
                for argument in manifest.invocation_arguments
            }
            assert Path(
                arguments["repository_root"].canonical_value
            ).resolve() == root.resolve()
            assert Path(
                arguments["artifact_path"].canonical_value
            ).is_file()
            assert arguments["persist"].canonical_value == "false"

            assert not report.invocation_performed
            assert not report.analytics_execution_performed
            assert not report.database_access_performed
            assert not report.runtime_artifact_created
            assert not report.runtime_artifact_modified
            assert not report.networking_performed
            assert not report.publication_allowed
            assert not report.action_authorization_allowed
            assert not report.qseries_execution_allowed

            replay = build_authorized_read_invocation_readiness_report(
                root,
                read_session_report=session,
            )
            assert replay == report
            assert verify_read_invocation_readiness_report(report)

            tampered = replace(
                report,
                invocation_performed=True,
            )
            try:
                verify_read_invocation_readiness_report(tampered)
            except OracleRealIntelligenceReadInvocationReadinessInvariantError:
                pass
            else:
                raise AssertionError(
                    "tampered invocation-readiness report accepted"
                )

        print("[PASS] Certified OIT-035 read session consumed")
        print("[PASS] Exact callable identity bound")
        print("[PASS] Exact callable signature bound")
        print("[PASS] Repository-root argument bound")
        print("[PASS] Exact authorized artifact-path argument bound")
        print("[PASS] Persist argument bound to false")
        print("[PASS] Unsupported arguments rejected")
        print("[PASS] Bounded single-artifact invocation certified")
        print("[PASS] Invocation readiness deterministic across replay")
        print("[PASS] Callable remained uninvoked")
        print("[PASS] Tampered invocation-readiness report rejected")
        print("[PASS] No analytics execution or database access performed")
        print("[PASS] No runtime artifact created or modified")
        print("[PASS] Publication, action authorization, and Q Series execution disabled")
        print("[DONE] OIT-036 AUTHORIZED READ INVOCATION READINESS PASS")
        return 0
    finally:
        sys.modules.pop(module_name, None)


if __name__ == "__main__":
    raise SystemExit(main())
