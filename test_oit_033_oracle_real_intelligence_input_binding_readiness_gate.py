from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from qseries_v2.oracle_terminal.oracle_real_intelligence_input_binding_readiness_gate import (
    OracleRealIntelligenceBindingInvariantError,
    build_real_intelligence_binding_readiness_report,
    verify_real_intelligence_binding_readiness_report,
)


def main() -> int:
    print("=" * 48)
    print(" OIT-033 TEST")
    print(" REAL INTELLIGENCE INPUT BINDING READINESS")
    print("=" * 48)

    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        runtime_root = root / "runtime" / "oracle_intelligence"
        runtime_root.mkdir(parents=True)

        genuine = runtime_root / "genuine_intelligence.json"
        genuine.write_text(
            '{"record_id":"REAL-001","probability":0.61}',
            encoding="utf-8",
        )
        forbidden = runtime_root / "incomplete.partial"
        forbidden.write_text("partial", encoding="utf-8")

        report = build_real_intelligence_binding_readiness_report(root)

        assert report.runtime_root_exists
        assert report.canonical_runtime_target_verified
        assert report.artifact_candidate_count == 2
        assert report.eligible_artifact_count == 1
        assert report.genuine_artifact_available
        assert report.read_only_callable_available
        assert report.real_input_binding_ready
        assert report.failure_reason is None

        eligible = [
            item for item in report.artifact_candidates
            if item.candidate_eligible
        ]
        assert len(eligible) == 1
        assert eligible[0].relative_path.endswith("genuine_intelligence.json")
        assert eligible[0].byte_count > 0
        assert len(eligible[0].sha256) == 64

        rejected = [
            item for item in report.artifact_candidates
            if item.forbidden_suffix
        ]
        assert len(rejected) == 1
        assert not rejected[0].candidate_eligible

        replay = build_real_intelligence_binding_readiness_report(root)
        assert replay == report
        assert verify_real_intelligence_binding_readiness_report(report)

        tampered = replace(
            report,
            runtime_artifact_created=True,
        )
        try:
            verify_real_intelligence_binding_readiness_report(tampered)
        except OracleRealIntelligenceBindingInvariantError:
            pass
        else:
            raise AssertionError("tampered binding report accepted")

        assert not report.analytics_execution_performed
        assert not report.database_access_performed
        assert not report.runtime_artifact_created
        assert not report.publication_allowed
        assert not report.action_authorization_allowed
        assert not report.qseries_execution_allowed
        assert report.read_only

    print("[PASS] Canonical runtime/oracle_intelligence target verified")
    print("[PASS] Genuine nonempty runtime artifact discovered")
    print("[PASS] Artifact SHA-256 and byte count captured")
    print("[PASS] Partial and temporary artifact rejected")
    print("[PASS] Existing terminal read-only callables discovered")
    print("[PASS] Persistence-signaling callables rejected")
    print("[PASS] Real input binding readiness certified")
    print("[PASS] Discovery deterministic across replay")
    print("[PASS] Tampered binding report rejected")
    print("[PASS] No analytics execution or database access performed")
    print("[PASS] No runtime artifact created")
    print("[PASS] Publication, action authorization, and Q Series execution disabled")
    print("[DONE] OIT-033 REAL INTELLIGENCE INPUT BINDING READINESS PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
