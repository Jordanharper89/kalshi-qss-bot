from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    build_oracle_memory_learner_foundation_report,
)
from qseries_v2.oracle_memory.oracle_memory_learner_foundation_admission_gate import (
    ADMISSION_STATUS_ADMITTED,
    OracleMemoryLearnerFoundationAdmissionInvariantError,
    build_oracle_memory_learner_foundation_admission_decision,
    verify_oracle_memory_learner_foundation_admission_decision,
)


def load_module(path: Path, name: str):
    specification = importlib.util.spec_from_file_location(name, path)

    if specification is None or specification.loader is None:
        raise RuntimeError(f"unable to load fixture: {path}")

    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def build_oml_001_report(root: Path):
    fixture = load_module(
        root
        / "test_oit_050_oracle_terminal_final_freeze_and_completion.py",
        "oit_050_fixture_for_oml_002",
    )

    from qseries_v2.oracle_terminal.oracle_terminal_final_freeze_and_completion import (
        build_oracle_terminal_final_freeze_completion_report,
    )

    oit_049 = fixture.build_oit_049_report(root)
    oit_050 = build_oracle_terminal_final_freeze_completion_report(
        root,
        production_certification_report=oit_049,
    )

    return build_oracle_memory_learner_foundation_report(
        root,
        oit_final_freeze_report=oit_050,
    )


def expect_rejection(callable_object, label: str) -> None:
    try:
        callable_object()
    except OracleMemoryLearnerFoundationAdmissionInvariantError:
        return

    raise AssertionError(f"tampered OML-002 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-002 TEST")
    print(" FOUNDATION ADMISSION GATE")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    foundation = build_oml_001_report(root)

    decision = (
        build_oracle_memory_learner_foundation_admission_decision(
            root,
            foundation_report=foundation,
        )
    )

    assert decision.schema_version == "OML-002"
    assert decision.engine_id == "OML-002"
    assert decision.upstream_schema_version == "OML-001"
    assert decision.upstream_engine_id == "OML-001"
    assert decision.upstream_report_hash == foundation.report_hash
    assert decision.upstream_certification_hash == (
        foundation.upstream_certification.certification_hash
    )
    assert decision.upstream_oit_report_hash == (
        foundation.upstream_certification.upstream_report_hash
    )
    assert decision.upstream_oit_runner_sha256 == (
        foundation.upstream_certification.upstream_runner_sha256
    )

    assert decision.foundation_verified
    assert decision.subsystem_identity_verified
    assert decision.package_separation_verified
    assert decision.certified_read_only_consumption_verified
    assert decision.deterministic_contract_verified
    assert decision.replay_contract_verified
    assert decision.immutable_lineage_verified
    assert decision.auditability_verified
    assert decision.memory_domains_verified
    assert decision.no_persistent_memory_verified
    assert decision.no_learning_update_verified
    assert decision.no_learner_execution_verified
    assert decision.no_memory_write_verified
    assert decision.no_database_access_verified
    assert decision.no_networking_verified
    assert decision.no_runtime_mutation_verified
    assert decision.publication_disabled_verified
    assert decision.action_authorization_disabled_verified
    assert decision.qseries_execution_disabled_verified
    assert decision.foundation_ready_verified
    assert decision.upstream_continuation_authorized
    assert decision.admission_status == ADMISSION_STATUS_ADMITTED
    assert decision.admitted
    assert decision.next_certification_authorized
    assert decision.read_only
    assert decision.failure_reason is None

    replay = (
        build_oracle_memory_learner_foundation_admission_decision(
            root,
            foundation_report=foundation,
        )
    )

    assert replay == decision
    assert verify_oracle_memory_learner_foundation_admission_decision(
        decision
    )

    expect_rejection(
        lambda: verify_oracle_memory_learner_foundation_admission_decision(
            replace(decision, no_memory_write_verified=False)
        ),
        "memory-write guarantee",
    )

    expect_rejection(
        lambda: verify_oracle_memory_learner_foundation_admission_decision(
            replace(decision, publication_disabled_verified=False)
        ),
        "publication boundary",
    )

    expect_rejection(
        lambda: verify_oracle_memory_learner_foundation_admission_decision(
            replace(decision, qseries_execution_disabled_verified=False)
        ),
        "Q Series execution boundary",
    )

    expect_rejection(
        lambda: verify_oracle_memory_learner_foundation_admission_decision(
            replace(decision, admitted=False)
        ),
        "admission state",
    )

    print("[PASS] Certified OML-001 foundation consumed")
    print("[PASS] OML-001 identity and policy verified")
    print("[PASS] OIT-050 report and runner lineage retained")
    print("[PASS] Oracle Memory package separation admitted")
    print("[PASS] Read-only upstream consumption admitted")
    print("[PASS] Deterministic and replay contracts admitted")
    print("[PASS] Immutable lineage and auditability admitted")
    print("[PASS] Eight memory-domain identities admitted")
    print("[PASS] Persistent memory remained disabled")
    print("[PASS] Continuous learning remained disabled")
    print("[PASS] Learner execution and memory writes remained absent")
    print("[PASS] Database, network, and runtime mutations remained absent")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Admission decision deterministic across replay")
    print("[PASS] Tampered admission decisions rejected")
    print("[DONE] OML-002 FOUNDATION ADMISSION GATE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
