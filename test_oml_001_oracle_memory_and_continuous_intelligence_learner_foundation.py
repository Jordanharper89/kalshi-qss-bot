from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    MEMORY_DOMAINS,
    OracleMemoryLearnerFoundationInvariantError,
    build_oracle_memory_learner_foundation_report,
    verify_oracle_memory_learner_foundation_report,
)


def load_oit_050_fixture(root: Path):
    path = (
        root
        / "test_oit_050_oracle_terminal_final_freeze_and_completion.py"
    )
    name = "oit_050_fixture_for_oml_001"

    specification = importlib.util.spec_from_file_location(
        name,
        path,
    )

    if specification is None or specification.loader is None:
        raise RuntimeError(
            "unable to load certified OIT-050 fixture"
        )

    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def build_oit_050_report(root: Path):
    fixture = load_oit_050_fixture(root)

    from qseries_v2.oracle_terminal.oracle_terminal_final_freeze_and_completion import (
        build_oracle_terminal_final_freeze_completion_report,
    )

    certification = fixture.build_oit_049_report(root)

    return build_oracle_terminal_final_freeze_completion_report(
        root,
        production_certification_report=certification,
    )


def expect_rejection(callable_object, label: str) -> None:
    try:
        callable_object()
    except OracleMemoryLearnerFoundationInvariantError:
        return

    raise AssertionError(
        f"tampered OML-001 {label} accepted"
    )


def main() -> int:
    print("=" * 48)
    print(" OML-001 TEST")
    print(" MEMORY AND CONTINUOUS LEARNER FOUNDATION")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    oit_report = build_oit_050_report(root)

    report = build_oracle_memory_learner_foundation_report(
        root,
        oit_final_freeze_report=oit_report,
    )

    assert report.schema_version == "OML-001"
    assert report.engine_id == "OML-001"
    assert (
        report.subsystem_id
        == "oracle_memory_and_continuous_intelligence_learner"
    )

    upstream = report.upstream_certification
    assert upstream.upstream_subsystem_id == (
        "oracle_open_intelligence_terminal"
    )
    assert upstream.upstream_final_milestone == "OIT-050"
    assert upstream.upstream_report_hash == oit_report.report_hash
    assert upstream.upstream_runner_sha256 == (
        oit_report.freeze_manifest.source_runner_sha256
    )
    assert upstream.upstream_completed
    assert upstream.upstream_frozen
    assert upstream.upstream_production_ready
    assert upstream.upstream_read_only_boundary_frozen
    assert upstream.upstream_publication_disabled
    assert upstream.upstream_action_authorization_disabled
    assert upstream.upstream_qseries_execution_disabled
    assert upstream.downstream_subsystem_authorized

    assert report.package_separate_from_oracle_terminal
    assert report.certified_read_only_upstream_consumption_only
    assert report.deterministic_contract_enabled
    assert report.replay_verification_enabled
    assert report.immutable_lineage_required
    assert report.auditability_required
    assert report.configured_memory_domains == MEMORY_DOMAINS
    assert report.foundation_ready
    assert report.next_certification_authorized
    assert report.read_only

    assert not report.persistent_memory_enabled
    assert not report.learning_update_enabled
    assert not report.learner_execution_performed
    assert not report.memory_write_performed
    assert not report.database_access_performed
    assert not report.networking_performed
    assert not report.runtime_artifact_created
    assert not report.runtime_artifact_modified
    assert not report.publication_allowed
    assert not report.action_authorization_allowed
    assert not report.qseries_execution_allowed

    replay = build_oracle_memory_learner_foundation_report(
        root,
        oit_final_freeze_report=oit_report,
    )

    assert replay == report
    assert verify_oracle_memory_learner_foundation_report(report)

    expect_rejection(
        lambda: verify_oracle_memory_learner_foundation_report(
            replace(
                report,
                memory_write_performed=True,
            )
        ),
        "memory-write state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_learner_foundation_report(
            replace(
                report,
                publication_allowed=True,
            )
        ),
        "publication state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_learner_foundation_report(
            replace(
                report,
                qseries_execution_allowed=True,
            )
        ),
        "Q Series execution state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_learner_foundation_report(
            replace(
                report,
                package_separate_from_oracle_terminal=False,
            )
        ),
        "package-separation state",
    )

    print("[PASS] Certified OIT-050 final freeze consumed")
    print("[PASS] OIT frozen subsystem identity verified")
    print("[PASS] OIT frozen runner hash lineage retained")
    print("[PASS] OML created as a separate production package")
    print("[PASS] Certified read-only upstream consumption enforced")
    print("[PASS] Eight memory and learner domains registered")
    print("[PASS] Deterministic hashing enabled")
    print("[PASS] Replay equality verified")
    print("[PASS] Immutable lineage and auditability required")
    print("[PASS] Persistent memory remained disabled")
    print("[PASS] Continuous learning remained disabled")
    print("[PASS] No memory write or learner execution performed")
    print("[PASS] No database, network, or runtime mutation performed")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered reports rejected")
    print("[DONE] OML-001 MEMORY AND CONTINUOUS LEARNER FOUNDATION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
