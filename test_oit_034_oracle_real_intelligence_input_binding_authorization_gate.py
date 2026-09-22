from __future__ import annotations
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from qseries_v2.oracle_terminal.oracle_real_intelligence_input_binding_readiness_gate import (
    ENGINE_ID as E33, POLICY_ID as P33, SCHEMA_VERSION as S33,
    OracleRealIntelligenceArtifactCandidate,
    OracleRealIntelligenceCallableCandidate,
    OracleRealIntelligenceBindingReadinessReport,
    _stable_hash as h33,
    verify_real_intelligence_binding_readiness_report,
)
from qseries_v2.oracle_terminal.oracle_real_intelligence_input_binding_authorization_gate import (
    OracleRealIntelligenceAuthorizationInvariantError,
    build_real_intelligence_binding_authorization_report,
    verify_real_intelligence_binding_authorization_report,
)

def make_source(root):
    ab = {
        "relative_path": "runtime/oracle_intelligence/genuine.json",
        "byte_count": 42,
        "sha256": "a" * 64,
        "suffix": ".json",
        "hidden": False,
        "forbidden_suffix": False,
        "readable": True,
        "candidate_eligible": True,
    }
    artifact = OracleRealIntelligenceArtifactCandidate(**ab, candidate_hash=h33(ab))
    cb = {
        "module_name": "qseries_v2.oracle_terminal.oracle_genuine_intelligence_artifact_admission",
        "callable_name": "load_genuine_intelligence_artifact",
        "signature": ("repository_root", "artifact_path"),
        "importable": True,
        "callable_resolved": True,
        "read_only_name_signal": True,
        "persistence_name_signal": False,
        "candidate_eligible": True,
    }
    callable_item = OracleRealIntelligenceCallableCandidate(**cb, candidate_hash=h33(cb))
    body = {
        "schema_version": S33,
        "engine_id": E33,
        "policy_id": P33,
        "status": "certified_read_only",
        "repository_root": str(root.resolve()),
        "runtime_root": str((root / "runtime" / "oracle_intelligence").resolve()),
        "runtime_root_exists": True,
        "artifact_candidates": (artifact,),
        "artifact_candidate_count": 1,
        "eligible_artifact_count": 1,
        "callable_candidates": (callable_item,),
        "callable_candidate_count": 1,
        "eligible_callable_count": 1,
        "canonical_runtime_target_verified": True,
        "genuine_artifact_available": True,
        "read_only_callable_available": True,
        "real_input_binding_ready": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "runtime_artifact_created": False,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
        "read_only": True,
        "failure_reason": None,
    }
    report = OracleRealIntelligenceBindingReadinessReport(**body, report_hash=h33(body))
    verify_real_intelligence_binding_readiness_report(report)
    return report

def main():
    print("=" * 48)
    print(" OIT-034 TEST")
    print(" REAL INTELLIGENCE INPUT BINDING AUTHORIZATION")
    print("=" * 48)
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        source = make_source(root)
        report = build_real_intelligence_binding_authorization_report(root, readiness_report=source)
        assert report.real_input_binding_authorized
        assert report.authorized_artifact.sha256 == "a" * 64
        assert report.authorized_artifact.byte_count == 42
        assert report.authorized_callable.callable_name == "load_genuine_intelligence_artifact"
        assert report.exact_artifact_hash_required
        assert report.exact_artifact_byte_count_required
        assert report.read_only_invocation_required
        assert not report.persistence_allowed
        assert not report.analytics_execution_allowed
        assert not report.database_access_allowed
        assert not report.networking_allowed
        assert not report.publication_allowed
        assert not report.action_authorization_allowed
        assert not report.qseries_execution_allowed
        assert verify_real_intelligence_binding_authorization_report(report)
        assert build_real_intelligence_binding_authorization_report(root, readiness_report=source) == report
        try:
            verify_real_intelligence_binding_authorization_report(replace(report, persistence_allowed=True))
        except OracleRealIntelligenceAuthorizationInvariantError:
            pass
        else:
            raise AssertionError("tampered authorization accepted")
    print("[PASS] Certified OIT-033 readiness consumed")
    print("[PASS] Exact artifact path, SHA-256, and byte count authorized")
    print("[PASS] Exact read-only callable authorized")
    print("[PASS] Lower-level bypass and persistence denied")
    print("[PASS] Database, networking, analytics, publication, action, and Q Series execution denied")
    print("[PASS] Authorization deterministic across replay")
    print("[PASS] Tampered authorization rejected")
    print("[DONE] OIT-034 REAL INTELLIGENCE INPUT BINDING AUTHORIZATION PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
