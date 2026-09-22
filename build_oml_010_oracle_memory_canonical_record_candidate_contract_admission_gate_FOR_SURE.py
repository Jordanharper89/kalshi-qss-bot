from __future__ import annotations

import ast
import importlib
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


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
        upstream = candidate / "qseries_v2" / "oracle_memory" / "oracle_memory_canonical_record_candidate_contract.py"
        upstream_test = candidate / "test_oml_009_oracle_memory_canonical_record_candidate_contract.py"
        if upstream.is_file() and upstream_test.is_file():
            return candidate
    raise RuntimeError("Could not locate repository containing certified OML-009.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_memory"
OML_009 = PACKAGE / "oracle_memory_canonical_record_candidate_contract.py"
OML_009_TEST = ROOT / "test_oml_009_oracle_memory_canonical_record_candidate_contract.py"
PRODUCTION = PACKAGE / "oracle_memory_canonical_record_candidate_contract_admission_gate.py"
TEST = ROOT / "test_oml_010_oracle_memory_canonical_record_candidate_contract_admission_gate.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = r'''
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from qseries_v2.oracle_memory.oracle_memory_canonical_record_candidate_contract import (
    ENGINE_ID as OML_009_ENGINE_ID,
    POLICY_ID as OML_009_POLICY_ID,
    SCHEMA_VERSION as OML_009_SCHEMA_VERSION,
    OracleMemoryCanonicalRecordCandidateContractCertification,
    verify_oracle_memory_canonical_record_candidate_contract_certification,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    MEMORY_DOMAINS,
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-010"
ENGINE_ID = "OML-010"
POLICY_ID = "oracle-memory.canonical-record-candidate-contract-admission-gate.v1"
UPSTREAM_SCHEMA_VERSION = "OML-009"
UPSTREAM_ENGINE_ID = "OML-009"
UPSTREAM_POLICY_ID = "oracle-memory.canonical-record-candidate-contract.v1"
ADMISSION_STATUS_ADMITTED = "admitted"


class OracleMemoryCanonicalRecordCandidateContractAdmissionInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCanonicalRecordCandidateContractAdmissionDecision:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_policy_id: str
    upstream_certification_hash: str
    upstream_gate_decision_hash: str
    upstream_registry_hash: str
    certified_domain_ids: tuple[str, ...]
    contract_verified: bool
    upstream_identity_verified: bool
    upstream_lineage_verified: bool
    canonical_serialization_verified: bool
    deterministic_hashing_verified: bool
    immutable_identity_verified: bool
    evidence_lineage_verified: bool
    parent_lineage_verified: bool
    confidence_bounds_verified: bool
    uncertainty_bounds_verified: bool
    duplicate_evidence_rejection_verified: bool
    duplicate_parent_rejection_verified: bool
    candidate_admission_disabled_verified: bool
    persistent_storage_disabled_verified: bool
    learning_updates_disabled_verified: bool
    runtime_activation_disabled_verified: bool
    publication_disabled_verified: bool
    action_authorization_disabled_verified: bool
    qseries_execution_disabled_verified: bool
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
        return {str(k): _canonical(v) for k, v in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleMemoryCanonicalRecordCandidateContractAdmissionInvariantError(
        "unsupported OML-010 value type: " + f"{type(value).__module__}.{type(value).__qualname__}"
    )


def _stable_hash(value: Any) -> str:
    payload = json.dumps(
        _canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _reject(reason: str) -> None:
    raise OracleMemoryCanonicalRecordCandidateContractAdmissionInvariantError(reason)


def build_oracle_memory_canonical_record_candidate_contract_admission_decision(
    *, certification: OracleMemoryCanonicalRecordCandidateContractCertification,
) -> OracleMemoryCanonicalRecordCandidateContractAdmissionDecision:
    verify_oracle_memory_canonical_record_candidate_contract_certification(certification)

    if OML_009_SCHEMA_VERSION != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-010 upstream schema constant mismatch")
    if OML_009_ENGINE_ID != UPSTREAM_ENGINE_ID:
        _reject("OML-010 upstream engine constant mismatch")
    if OML_009_POLICY_ID != UPSTREAM_POLICY_ID:
        _reject("OML-010 upstream policy constant mismatch")
    if certification.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-010 upstream certification schema mismatch")
    if certification.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-010 upstream certification engine mismatch")
    if certification.policy_id != UPSTREAM_POLICY_ID:
        _reject("OML-010 upstream certification policy mismatch")

    checks = {
        "contract_verified": True,
        "upstream_identity_verified": certification.subsystem_id == SUBSYSTEM_ID,
        "upstream_lineage_verified": all(len(value) == 64 for value in (
            certification.certification_hash,
            certification.upstream_gate_decision_hash,
            certification.upstream_registry_hash,
        )),
        "canonical_serialization_verified": certification.canonical_candidate_serialization_required,
        "deterministic_hashing_verified": certification.deterministic_candidate_hashing_required,
        "immutable_identity_verified": certification.immutable_candidate_identity_required,
        "evidence_lineage_verified": certification.evidence_lineage_required,
        "parent_lineage_verified": certification.parent_lineage_supported,
        "confidence_bounds_verified": certification.confidence_bounded,
        "uncertainty_bounds_verified": certification.uncertainty_bounded,
        "duplicate_evidence_rejection_verified": certification.duplicate_evidence_hashes_forbidden,
        "duplicate_parent_rejection_verified": certification.duplicate_parent_hashes_forbidden,
        "candidate_admission_disabled_verified": not certification.candidate_admission_enabled,
        "persistent_storage_disabled_verified": not certification.persistent_storage_enabled,
        "learning_updates_disabled_verified": not certification.learning_updates_enabled,
        "runtime_activation_disabled_verified": not certification.runtime_activation_enabled,
        "publication_disabled_verified": not certification.publication_enabled,
        "action_authorization_disabled_verified": not certification.action_authorization_enabled,
        "qseries_execution_disabled_verified": not certification.qseries_execution_enabled,
        "upstream_continuation_authorized": certification.next_certification_authorized,
    }

    failed = [name for name, passed in checks.items() if not passed]
    if certification.certified_domain_ids != MEMORY_DOMAINS:
        failed.append("certified_domain_ids")
    if not certification.contract_ready:
        failed.append("contract_ready")
    if not certification.read_only:
        failed.append("read_only")
    if failed:
        _reject("OML-010 candidate contract admission failed: " + ", ".join(failed))

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": certification.schema_version,
        "upstream_engine_id": certification.engine_id,
        "upstream_policy_id": certification.policy_id,
        "upstream_certification_hash": certification.certification_hash,
        "upstream_gate_decision_hash": certification.upstream_gate_decision_hash,
        "upstream_registry_hash": certification.upstream_registry_hash,
        "certified_domain_ids": certification.certified_domain_ids,
        **checks,
        "admission_status": ADMISSION_STATUS_ADMITTED,
        "admitted": True,
        "next_certification_authorized": True,
        "read_only": True,
        "failure_reason": None,
    }
    decision = OracleMemoryCanonicalRecordCandidateContractAdmissionDecision(
        **body, decision_hash=_stable_hash(body)
    )
    verify_oracle_memory_canonical_record_candidate_contract_admission_decision(decision)
    return decision


def verify_oracle_memory_canonical_record_candidate_contract_admission_decision(
    decision: OracleMemoryCanonicalRecordCandidateContractAdmissionDecision,
) -> bool:
    body = asdict(decision)
    supplied = body.pop("decision_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-010 admission decision hash mismatch")
    if decision.schema_version != SCHEMA_VERSION:
        _reject("OML-010 schema mismatch")
    if decision.engine_id != ENGINE_ID:
        _reject("OML-010 engine mismatch")
    if decision.policy_id != POLICY_ID:
        _reject("OML-010 policy mismatch")
    if decision.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-010 subsystem mismatch")
    if decision.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-010 admitted upstream schema mismatch")
    if decision.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-010 admitted upstream engine mismatch")
    if decision.upstream_policy_id != UPSTREAM_POLICY_ID:
        _reject("OML-010 admitted upstream policy mismatch")
    if any(len(value) != 64 for value in (
        decision.upstream_certification_hash,
        decision.upstream_gate_decision_hash,
        decision.upstream_registry_hash,
        decision.decision_hash,
    )):
        _reject("OML-010 lineage hash length invalid")
    if decision.certified_domain_ids != MEMORY_DOMAINS:
        _reject("OML-010 admitted domain identity mismatch")
    required_true = (
        decision.contract_verified,
        decision.upstream_identity_verified,
        decision.upstream_lineage_verified,
        decision.canonical_serialization_verified,
        decision.deterministic_hashing_verified,
        decision.immutable_identity_verified,
        decision.evidence_lineage_verified,
        decision.parent_lineage_verified,
        decision.confidence_bounds_verified,
        decision.uncertainty_bounds_verified,
        decision.duplicate_evidence_rejection_verified,
        decision.duplicate_parent_rejection_verified,
        decision.candidate_admission_disabled_verified,
        decision.persistent_storage_disabled_verified,
        decision.learning_updates_disabled_verified,
        decision.runtime_activation_disabled_verified,
        decision.publication_disabled_verified,
        decision.action_authorization_disabled_verified,
        decision.qseries_execution_disabled_verified,
        decision.upstream_continuation_authorized,
        decision.admitted,
        decision.next_certification_authorized,
        decision.read_only,
    )
    if not all(required_true):
        _reject("OML-010 admitted decision missing required guarantee")
    if decision.admission_status != ADMISSION_STATUS_ADMITTED:
        _reject("OML-010 admission status mismatch")
    if decision.failure_reason is not None:
        _reject("OML-010 admitted decision contains failure reason")
    return True
'''

TEST_SOURCE = r'''
from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_canonical_record_candidate_contract import (
    build_oracle_memory_canonical_record_candidate_contract_certification,
)
from qseries_v2.oracle_memory.oracle_memory_canonical_record_candidate_contract_admission_gate import (
    ADMISSION_STATUS_ADMITTED,
    OracleMemoryCanonicalRecordCandidateContractAdmissionInvariantError,
    build_oracle_memory_canonical_record_candidate_contract_admission_decision,
    verify_oracle_memory_canonical_record_candidate_contract_admission_decision,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import MEMORY_DOMAINS


def load_module(path: Path, name: str):
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"unable to load fixture: {path}")
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def build_oml_009_certification(root: Path):
    fixture = load_module(
        root / "test_oml_009_oracle_memory_canonical_record_candidate_contract.py",
        "oml_009_fixture_for_oml_010",
    )
    gate = fixture.build_oml_008_decision(root)
    return build_oracle_memory_canonical_record_candidate_contract_certification(
        gate_decision=gate,
    )


def expect_rejection(callable_object, label: str) -> None:
    try:
        callable_object()
    except OracleMemoryCanonicalRecordCandidateContractAdmissionInvariantError:
        return
    raise AssertionError(f"tampered OML-010 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-010 TEST")
    print(" CANDIDATE CONTRACT ADMISSION GATE")
    print("=" * 48)
    root = Path(__file__).resolve().parent
    certification = build_oml_009_certification(root)
    decision = build_oracle_memory_canonical_record_candidate_contract_admission_decision(
        certification=certification,
    )
    assert decision.schema_version == "OML-010"
    assert decision.engine_id == "OML-010"
    assert decision.upstream_schema_version == "OML-009"
    assert decision.upstream_engine_id == "OML-009"
    assert decision.upstream_certification_hash == certification.certification_hash
    assert decision.upstream_gate_decision_hash == certification.upstream_gate_decision_hash
    assert decision.upstream_registry_hash == certification.upstream_registry_hash
    assert decision.certified_domain_ids == MEMORY_DOMAINS
    assert decision.contract_verified
    assert decision.candidate_admission_disabled_verified
    assert decision.persistent_storage_disabled_verified
    assert decision.learning_updates_disabled_verified
    assert decision.runtime_activation_disabled_verified
    assert decision.publication_disabled_verified
    assert decision.action_authorization_disabled_verified
    assert decision.qseries_execution_disabled_verified
    assert decision.admission_status == ADMISSION_STATUS_ADMITTED
    assert decision.admitted
    assert decision.next_certification_authorized
    assert decision.read_only
    assert decision.failure_reason is None
    replay = build_oracle_memory_canonical_record_candidate_contract_admission_decision(
        certification=certification,
    )
    assert replay == decision
    assert verify_oracle_memory_canonical_record_candidate_contract_admission_decision(decision)
    expect_rejection(
        lambda: verify_oracle_memory_canonical_record_candidate_contract_admission_decision(
            replace(decision, candidate_admission_disabled_verified=False)
        ),
        "candidate admission boundary",
    )
    expect_rejection(
        lambda: verify_oracle_memory_canonical_record_candidate_contract_admission_decision(
            replace(decision, persistent_storage_disabled_verified=False)
        ),
        "persistent storage boundary",
    )
    expect_rejection(
        lambda: verify_oracle_memory_canonical_record_candidate_contract_admission_decision(
            replace(decision, qseries_execution_disabled_verified=False)
        ),
        "Q Series execution boundary",
    )
    print("[PASS] Certified OML-009 candidate contract consumed")
    print("[PASS] OML-009 identity and policy verified")
    print("[PASS] OML-008 through OIT-050 lineage retained")
    print("[PASS] Eight certified memory domains admitted")
    print("[PASS] Canonical candidate serialization admitted")
    print("[PASS] Deterministic candidate hashing admitted")
    print("[PASS] Immutable candidate identity admitted")
    print("[PASS] Evidence and parent lineage admitted")
    print("[PASS] Confidence and uncertainty bounds admitted")
    print("[PASS] Candidate admission remained disabled")
    print("[PASS] Persistent storage remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Admission deterministic across replay")
    print("[PASS] Tampered admission decisions rejected")
    print("[DONE] OML-010 CANDIDATE CONTRACT ADMISSION GATE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def write_complete(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def validate_actual_oml_009() -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    module = importlib.import_module(
        "qseries_v2.oracle_memory.oracle_memory_canonical_record_candidate_contract"
    )
    expected = {
        "SCHEMA_VERSION": "OML-009",
        "ENGINE_ID": "OML-009",
        "POLICY_ID": "oracle-memory.canonical-record-candidate-contract.v1",
        "UPSTREAM_SCHEMA_VERSION": "OML-008",
        "UPSTREAM_ENGINE_ID": "OML-008",
        "CANDIDATE_STATE_CONTRACT_ONLY": "candidate_contract_only",
    }
    for name, value in expected.items():
        actual = getattr(module, name, None)
        if actual != value:
            raise RuntimeError(
                f"Certified OML-009 {name} mismatch: expected {value!r}, got {actual!r}"
            )
    required = (
        "OracleMemoryCanonicalRecordCandidate",
        "OracleMemoryCanonicalRecordCandidateContractCertification",
        "build_oracle_memory_canonical_record_candidate",
        "verify_oracle_memory_canonical_record_candidate",
        "build_oracle_memory_canonical_record_candidate_contract_certification",
        "verify_oracle_memory_canonical_record_candidate_contract_certification",
    )
    missing = [name for name in required if not hasattr(module, name)]
    if missing:
        raise RuntimeError(
            "Certified OML-009 missing required symbols: " + ", ".join(missing)
        )


def main() -> int:
    print("=" * 48)
    print(" OML-010 FOR-SURE INSTALLER")
    print(" CANDIDATE CONTRACT ADMISSION GATE")
    print("=" * 48)
    print("[BOOT] Revision: ZIP_ALIGNED_IMPORT_VERIFIED_FULL_REPLACEMENT")
    try:
        validate_actual_oml_009()
        print("[OK] Actual OML-009 imported and structurally verified")
        upstream = subprocess.run(
            [sys.executable, str(OML_009_TEST)], cwd=ROOT, check=False
        )
        if upstream.returncode:
            raise RuntimeError(
                "OML-009 certification failed with exit code " + str(upstream.returncode)
            )
        production_before = OML_009.read_bytes()
        test_before = OML_009_TEST.read_bytes()
        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)
        export = (
            "from .oracle_memory_canonical_record_candidate_contract_admission_gate import *"
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
        completed = subprocess.run([sys.executable, str(TEST)], cwd=ROOT, check=False)
        if completed.returncode:
            raise RuntimeError(
                "OML-010 test failed with exit code " + str(completed.returncode)
            )
        if OML_009.read_bytes() != production_before:
            raise RuntimeError("Certified OML-009 production changed")
        if OML_009_TEST.read_bytes() != test_before:
            raise RuntimeError("Certified OML-009 standalone test changed")
        print("[PASS] Certified OML-009 production unchanged")
        print("[PASS] Certified OML-009 standalone test unchanged")
        print("[PASS] OML-010 production admission gate installed")
        print("[PASS] OML-010 standalone deterministic test installed")
        print("[PASS] Candidate contract admitted")
        print("[PASS] Candidate admission remained disabled")
        print("[PASS] Persistent memory remained disabled")
        print("[PASS] Continuous learning remained disabled")
        print("[PASS] Runtime activation remained disabled")
        print("[PASS] Publication remained disabled")
        print("[PASS] Action authorization remained disabled")
        print("[PASS] Q Series execution remained disabled")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OML-010 CANDIDATE CONTRACT ADMISSION GATE INSTALLED")
        return 0
    except (RuntimeError, SyntaxError, ImportError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
