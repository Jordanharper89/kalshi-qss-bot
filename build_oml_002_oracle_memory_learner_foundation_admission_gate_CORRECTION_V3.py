from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
INSTALLER_REVISION = "CORRECTION_V3_UNIQUE_FILENAME_FULL_REPLACEMENT"

print("=" * 48)
print(" OML-002 CORRECTION V3 INSTALLER")
print(" FOUNDATION ADMISSION GATE")
print("=" * 48)
print(f"[BOOT] Revision: {INSTALLER_REVISION}")


def locate_repository() -> Path:
    candidates: list[Path] = []
    for base in (Path.cwd().resolve(), SCRIPT_DIR):
        candidates.extend((base, base / "kalshi-qss-bot"))
        for parent in base.parents:
            candidates.extend((parent, parent / "kalshi-qss-bot"))
    seen: set[Path] = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        module = candidate / "qseries_v2" / "oracle_memory" / "oracle_memory_continuous_intelligence_learner_foundation.py"
        test = candidate / "test_oml_001_oracle_memory_and_continuous_intelligence_learner_foundation.py"
        if module.is_file() and test.is_file():
            return candidate
    raise SystemExit("[ERROR] Could not locate repository with certified OML-001.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_memory"
OML_001 = PACKAGE / "oracle_memory_continuous_intelligence_learner_foundation.py"
OML_001_TEST = ROOT / "test_oml_001_oracle_memory_and_continuous_intelligence_learner_foundation.py"
PRODUCTION = PACKAGE / "oracle_memory_learner_foundation_admission_gate.py"
TEST = ROOT / "test_oml_002_oracle_memory_learner_foundation_admission_gate.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = r'''
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    ENGINE_ID as OML_001_ENGINE_ID,
    MEMORY_DOMAINS,
    POLICY_ID as OML_001_POLICY_ID,
    SCHEMA_VERSION as OML_001_SCHEMA_VERSION,
    SUBSYSTEM_ID,
    OracleMemoryLearnerFoundationReport,
    verify_oracle_memory_learner_foundation_report,
)

SCHEMA_VERSION = "OML-002"
ENGINE_ID = "OML-002"
POLICY_ID = "oracle-memory-learner.foundation-admission-gate.v1"
UPSTREAM_SCHEMA_VERSION = "OML-001"
UPSTREAM_ENGINE_ID = "OML-001"
UPSTREAM_POLICY_ID = "oracle-memory-continuous-intelligence-learner.foundation.v1"
ADMISSION_STATUS_ADMITTED = "admitted"


class OracleMemoryLearnerFoundationAdmissionInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryLearnerFoundationAdmissionDecision:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    repository_root: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_policy_id: str
    upstream_report_hash: str
    upstream_certification_hash: str
    upstream_oit_report_hash: str
    upstream_oit_runner_sha256: str
    configured_memory_domains: tuple[str, ...]
    foundation_verified: bool
    subsystem_identity_verified: bool
    package_separation_verified: bool
    certified_read_only_consumption_verified: bool
    deterministic_contract_verified: bool
    replay_contract_verified: bool
    immutable_lineage_verified: bool
    auditability_verified: bool
    memory_domains_verified: bool
    no_persistent_memory_verified: bool
    no_learning_update_verified: bool
    no_learner_execution_verified: bool
    no_memory_write_verified: bool
    no_database_access_verified: bool
    no_networking_verified: bool
    no_runtime_mutation_verified: bool
    publication_disabled_verified: bool
    action_authorization_disabled_verified: bool
    qseries_execution_disabled_verified: bool
    foundation_ready_verified: bool
    upstream_continuation_authorized: bool
    admission_status: str
    admitted: bool
    next_certification_authorized: bool
    read_only: bool
    failure_reason: str | None
    decision_hash: str


def _canonical(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _canonical(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleMemoryLearnerFoundationAdmissionInvariantError(
        "unsupported OML-002 value type: "
        f"{type(value).__module__}.{type(value).__qualname__}"
    )


def _stable_hash(value: Any) -> str:
    payload = json.dumps(
        _canonical(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _reject(reason: str) -> None:
    raise OracleMemoryLearnerFoundationAdmissionInvariantError(reason)


def build_oracle_memory_learner_foundation_admission_decision(
    repository_root: str | Path,
    *,
    foundation_report: OracleMemoryLearnerFoundationReport,
) -> OracleMemoryLearnerFoundationAdmissionDecision:
    root = Path(repository_root).resolve()
    verify_oracle_memory_learner_foundation_report(foundation_report)

    if OML_001_SCHEMA_VERSION != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-002 upstream schema constant mismatch")
    if OML_001_ENGINE_ID != UPSTREAM_ENGINE_ID:
        _reject("OML-002 upstream engine constant mismatch")
    if OML_001_POLICY_ID != UPSTREAM_POLICY_ID:
        _reject("OML-002 upstream policy constant mismatch")

    upstream = foundation_report.upstream_certification
    checks = {
        "foundation_verified": True,
        "subsystem_identity_verified": foundation_report.subsystem_id == SUBSYSTEM_ID,
        "package_separation_verified": foundation_report.package_separate_from_oracle_terminal,
        "certified_read_only_consumption_verified": foundation_report.certified_read_only_upstream_consumption_only,
        "deterministic_contract_verified": foundation_report.deterministic_contract_enabled,
        "replay_contract_verified": foundation_report.replay_verification_enabled,
        "immutable_lineage_verified": foundation_report.immutable_lineage_required,
        "auditability_verified": foundation_report.auditability_required,
        "memory_domains_verified": tuple(foundation_report.configured_memory_domains) == MEMORY_DOMAINS,
        "no_persistent_memory_verified": not foundation_report.persistent_memory_enabled,
        "no_learning_update_verified": not foundation_report.learning_update_enabled,
        "no_learner_execution_verified": not foundation_report.learner_execution_performed,
        "no_memory_write_verified": not foundation_report.memory_write_performed,
        "no_database_access_verified": not foundation_report.database_access_performed,
        "no_networking_verified": not foundation_report.networking_performed,
        "no_runtime_mutation_verified": not foundation_report.runtime_artifact_created and not foundation_report.runtime_artifact_modified,
        "publication_disabled_verified": not foundation_report.publication_allowed,
        "action_authorization_disabled_verified": not foundation_report.action_authorization_allowed,
        "qseries_execution_disabled_verified": not foundation_report.qseries_execution_allowed,
        "foundation_ready_verified": foundation_report.foundation_ready,
        "upstream_continuation_authorized": foundation_report.next_certification_authorized,
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        _reject("OML-002 foundation admission failed: " + ", ".join(failed))

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "repository_root": str(root),
        "upstream_schema_version": foundation_report.schema_version,
        "upstream_engine_id": foundation_report.engine_id,
        "upstream_policy_id": foundation_report.policy_id,
        "upstream_report_hash": foundation_report.report_hash,
        "upstream_certification_hash": upstream.certification_hash,
        "upstream_oit_report_hash": upstream.upstream_report_hash,
        "upstream_oit_runner_sha256": upstream.upstream_runner_sha256,
        "configured_memory_domains": MEMORY_DOMAINS,
        **checks,
        "admission_status": ADMISSION_STATUS_ADMITTED,
        "admitted": True,
        "next_certification_authorized": True,
        "read_only": True,
        "failure_reason": None,
    }
    decision = OracleMemoryLearnerFoundationAdmissionDecision(
        **body,
        decision_hash=_stable_hash(body),
    )
    verify_oracle_memory_learner_foundation_admission_decision(decision)
    return decision


def verify_oracle_memory_learner_foundation_admission_decision(
    decision: OracleMemoryLearnerFoundationAdmissionDecision,
) -> bool:
    body = asdict(decision)
    supplied = body.pop("decision_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-002 admission decision hash mismatch")
    if decision.schema_version != SCHEMA_VERSION:
        _reject("OML-002 schema mismatch")
    if decision.engine_id != ENGINE_ID:
        _reject("OML-002 engine mismatch")
    if decision.policy_id != POLICY_ID:
        _reject("OML-002 policy mismatch")
    if decision.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-002 subsystem mismatch")
    if decision.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-002 admitted upstream schema mismatch")
    if decision.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-002 admitted upstream engine mismatch")
    if decision.upstream_policy_id != UPSTREAM_POLICY_ID:
        _reject("OML-002 admitted upstream policy mismatch")

    hashes = (
        decision.upstream_report_hash,
        decision.upstream_certification_hash,
        decision.upstream_oit_report_hash,
        decision.upstream_oit_runner_sha256,
        decision.decision_hash,
    )
    if any(len(value) != 64 for value in hashes):
        _reject("OML-002 lineage hash length invalid")
    if tuple(decision.configured_memory_domains) != MEMORY_DOMAINS:
        _reject("OML-002 memory-domain lineage mismatch")

    required_true = (
        decision.foundation_verified,
        decision.subsystem_identity_verified,
        decision.package_separation_verified,
        decision.certified_read_only_consumption_verified,
        decision.deterministic_contract_verified,
        decision.replay_contract_verified,
        decision.immutable_lineage_verified,
        decision.auditability_verified,
        decision.memory_domains_verified,
        decision.no_persistent_memory_verified,
        decision.no_learning_update_verified,
        decision.no_learner_execution_verified,
        decision.no_memory_write_verified,
        decision.no_database_access_verified,
        decision.no_networking_verified,
        decision.no_runtime_mutation_verified,
        decision.publication_disabled_verified,
        decision.action_authorization_disabled_verified,
        decision.qseries_execution_disabled_verified,
        decision.foundation_ready_verified,
        decision.upstream_continuation_authorized,
        decision.admitted,
        decision.next_certification_authorized,
        decision.read_only,
    )
    if not all(required_true):
        _reject("OML-002 admitted decision missing required guarantee")
    if decision.admission_status != ADMISSION_STATUS_ADMITTED:
        _reject("OML-002 admission status mismatch")
    if decision.failure_reason is not None:
        _reject("OML-002 admitted decision contains failure reason")
    return True
'''

TEST_SOURCE = r'''
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


def load_oit_050_fixture(root: Path):
    path = root / "test_oit_050_oracle_terminal_final_freeze_and_completion.py"
    name = "oit_050_fixture_for_oml_002"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load certified OIT-050 fixture")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def build_oml_001_report(root: Path):
    fixture = load_oit_050_fixture(root)
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
    decision = build_oracle_memory_learner_foundation_admission_decision(
        root,
        foundation_report=foundation,
    )

    assert decision.schema_version == "OML-002"
    assert decision.engine_id == "OML-002"
    assert decision.upstream_schema_version == "OML-001"
    assert decision.upstream_engine_id == "OML-001"
    assert decision.upstream_report_hash == foundation.report_hash
    assert decision.upstream_certification_hash == foundation.upstream_certification.certification_hash
    assert decision.upstream_oit_report_hash == foundation.upstream_certification.upstream_report_hash
    assert decision.upstream_oit_runner_sha256 == foundation.upstream_certification.upstream_runner_sha256

    required = (
        decision.foundation_verified,
        decision.subsystem_identity_verified,
        decision.package_separation_verified,
        decision.certified_read_only_consumption_verified,
        decision.deterministic_contract_verified,
        decision.replay_contract_verified,
        decision.immutable_lineage_verified,
        decision.auditability_verified,
        decision.memory_domains_verified,
        decision.no_persistent_memory_verified,
        decision.no_learning_update_verified,
        decision.no_learner_execution_verified,
        decision.no_memory_write_verified,
        decision.no_database_access_verified,
        decision.no_networking_verified,
        decision.no_runtime_mutation_verified,
        decision.publication_disabled_verified,
        decision.action_authorization_disabled_verified,
        decision.qseries_execution_disabled_verified,
        decision.foundation_ready_verified,
        decision.upstream_continuation_authorized,
        decision.admitted,
        decision.next_certification_authorized,
        decision.read_only,
    )
    assert all(required)
    assert decision.admission_status == ADMISSION_STATUS_ADMITTED
    assert decision.failure_reason is None

    replay = build_oracle_memory_learner_foundation_admission_decision(
        root,
        foundation_report=foundation,
    )
    assert replay == decision
    assert verify_oracle_memory_learner_foundation_admission_decision(decision)

    expect_rejection(
        lambda: verify_oracle_memory_learner_foundation_admission_decision(
            replace(decision, upstream_report_hash="0" * 64)
        ),
        "upstream report lineage",
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
'''


def require_contract(path: Path, tokens: tuple[str, ...], label: str) -> None:
    if not path.is_file():
        raise RuntimeError(f"{label} missing: {path}")
    text = path.read_text(encoding="utf-8")
    missing = [token for token in tokens if token not in text]
    if missing:
        raise RuntimeError(f"{label} contract mismatch: {missing}")
    ast.parse(text, filename=str(path))


def write_complete(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def main() -> int:
    print("[BOOT] Repository discovery complete")
    try:
        installer_path = Path(__file__).resolve()
        installer_text = installer_path.read_text(encoding="utf-8")
        ast.parse(installer_text, filename=str(installer_path))
        required_self_tokens = (
            "PRODUCTION_SOURCE",
            "TEST_SOURCE",
            "write_complete(PRODUCTION, PRODUCTION_SOURCE)",
            "write_complete(TEST, TEST_SOURCE)",
            "OML-002 FOUNDATION ADMISSION GATE INSTALLED",
        )
        missing_self_tokens = [
            token for token in required_self_tokens if token not in installer_text
        ]
        if missing_self_tokens:
            raise RuntimeError(
                "OML-002 installer incomplete: " + ", ".join(missing_self_tokens)
            )
        print("[OK] Installer source self-validation passed")
        require_contract(
            OML_001,
            (
                'SCHEMA_VERSION = "OML-001"',
                'ENGINE_ID = "OML-001"',
                'POLICY_ID = "oracle-memory-continuous-intelligence-learner.foundation.v1"',
                'SUBSYSTEM_ID = "oracle_memory_and_continuous_intelligence_learner"',
                "MEMORY_DOMAINS",
                "OracleMemoryLearnerUpstreamCertification",
                "OracleMemoryLearnerFoundationReport",
                "build_oracle_memory_learner_foundation_report",
                "verify_oracle_memory_learner_foundation_report",
                "package_separate_from_oracle_terminal",
                "certified_read_only_upstream_consumption_only",
                "deterministic_contract_enabled",
                "replay_verification_enabled",
                "immutable_lineage_required",
                "auditability_required",
                "persistent_memory_enabled",
                "learning_update_enabled",
                "memory_write_performed",
                "database_access_performed",
                "networking_performed",
                "publication_allowed",
                "action_authorization_allowed",
                "qseries_execution_allowed",
                "foundation_ready",
                "next_certification_authorized",
            ),
            "Certified OML-001 production",
        )
        require_contract(
            OML_001_TEST,
            (
                "OML-001 TEST",
                "MEMORY AND CONTINUOUS LEARNER FOUNDATION",
                "Certified OIT-050 final freeze consumed",
                "Replay equality verified",
                "Tampered reports rejected",
                "OML-001 MEMORY AND CONTINUOUS LEARNER FOUNDATION PASS",
            ),
            "Certified OML-001 standalone test",
        )

        print("[OK] Certified OML-001 production contract verified")
        print("[OK] Certified OML-001 standalone test verified")
        upstream = subprocess.run([sys.executable, str(OML_001_TEST)], cwd=ROOT, check=False)
        if upstream.returncode:
            raise RuntimeError(f"OML-001 certification failed with exit code {upstream.returncode}")

        oml_001_before = OML_001.read_bytes()
        oml_001_test_before = OML_001_TEST.read_bytes()

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = "from .oracle_memory_learner_foundation_admission_gate import *"
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

        completed = subprocess.run([sys.executable, str(TEST)], cwd=ROOT, check=False)
        if completed.returncode:
            raise RuntimeError(f"OML-002 test failed with exit code {completed.returncode}")
        if OML_001.read_bytes() != oml_001_before:
            raise RuntimeError("Certified OML-001 production module changed")
        if OML_001_TEST.read_bytes() != oml_001_test_before:
            raise RuntimeError("Certified OML-001 standalone test changed")

        print("[PASS] Certified OML-001 production unchanged")
        print("[PASS] Certified OML-001 standalone test unchanged")
        print("[PASS] OML-002 production admission gate installed")
        print("[PASS] OML-002 standalone deterministic test installed")
        print("[PASS] OML-001 identity and policy enforced")
        print("[PASS] OIT-050 lineage retained through OML-001")
        print("[PASS] Read-only foundation guarantees admitted")
        print("[PASS] Memory and learner capability locks admitted")
        print("[PASS] Publication remained disabled")
        print("[PASS] Action authorization remained disabled")
        print("[PASS] Q Series execution remained disabled")
        print("[PASS] No database, network, or runtime mutation performed")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OML-002 FOUNDATION ADMISSION GATE INSTALLED")
        return 0
    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
