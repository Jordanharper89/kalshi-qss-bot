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

        upstream = (
            candidate
            / "qseries_v2"
            / "oracle_memory"
            / "oracle_memory_canonical_record_contract.py"
        )
        upstream_test = (
            candidate
            / "test_oml_005_oracle_memory_canonical_record_contract.py"
        )

        if upstream.is_file() and upstream_test.is_file():
            return candidate

    raise RuntimeError(
        "Could not locate repository containing certified OML-005."
    )


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_memory"

OML_005 = PACKAGE / "oracle_memory_canonical_record_contract.py"
OML_005_TEST = (
    ROOT
    / "test_oml_005_oracle_memory_canonical_record_contract.py"
)

PRODUCTION = (
    PACKAGE
    / "oracle_memory_canonical_record_contract_admission_gate.py"
)
TEST = (
    ROOT
    / "test_oml_006_oracle_memory_canonical_record_contract_admission_gate.py"
)
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from qseries_v2.oracle_memory.oracle_memory_canonical_record_contract import (
    ENGINE_ID as OML_005_ENGINE_ID,
    POLICY_ID as OML_005_POLICY_ID,
    SCHEMA_VERSION as OML_005_SCHEMA_VERSION,
    OracleMemoryCanonicalRecordContractCertification,
    verify_oracle_memory_canonical_record_contract_certification,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    MEMORY_DOMAINS,
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-006"
ENGINE_ID = "OML-006"
POLICY_ID = "oracle-memory.canonical-record-contract-admission-gate.v1"

UPSTREAM_SCHEMA_VERSION = "OML-005"
UPSTREAM_ENGINE_ID = "OML-005"
UPSTREAM_POLICY_ID = "oracle-memory.canonical-record-contract.v1"

ADMISSION_STATUS_ADMITTED = "admitted"


class OracleMemoryCanonicalRecordContractAdmissionInvariantError(
    RuntimeError
):
    pass


@dataclass(frozen=True)
class OracleMemoryCanonicalRecordContractAdmissionDecision:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_policy_id: str
    upstream_certification_hash: str
    upstream_admission_hash: str
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
        return {
            str(key): _canonical(item)
            for key, item in sorted(
                value.items(),
                key=lambda pair: str(pair[0]),
            )
        }

    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]

    if value is None or isinstance(
        value,
        (str, int, float, bool),
    ):
        return value

    raise OracleMemoryCanonicalRecordContractAdmissionInvariantError(
        "unsupported OML-006 value type: "
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
    raise OracleMemoryCanonicalRecordContractAdmissionInvariantError(
        reason
    )


def build_oracle_memory_canonical_record_contract_admission_decision(
    *,
    certification: OracleMemoryCanonicalRecordContractCertification,
) -> OracleMemoryCanonicalRecordContractAdmissionDecision:
    verify_oracle_memory_canonical_record_contract_certification(
        certification
    )

    if OML_005_SCHEMA_VERSION != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-006 upstream schema constant mismatch")

    if OML_005_ENGINE_ID != UPSTREAM_ENGINE_ID:
        _reject("OML-006 upstream engine constant mismatch")

    if OML_005_POLICY_ID != UPSTREAM_POLICY_ID:
        _reject("OML-006 upstream policy constant mismatch")

    if certification.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-006 upstream certification schema mismatch")

    if certification.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-006 upstream certification engine mismatch")

    if certification.policy_id != UPSTREAM_POLICY_ID:
        _reject("OML-006 upstream certification policy mismatch")

    checks = {
        "contract_verified": True,
        "upstream_identity_verified": (
            certification.subsystem_id == SUBSYSTEM_ID
        ),
        "upstream_lineage_verified": all(
            len(value) == 64
            for value in (
                certification.certification_hash,
                certification.upstream_admission_hash,
                certification.upstream_registry_hash,
            )
        ),
        "canonical_serialization_verified": (
            certification.canonical_serialization_required
        ),
        "deterministic_hashing_verified": (
            certification.deterministic_record_hashing_required
        ),
        "immutable_identity_verified": (
            certification.immutable_record_identity_required
        ),
        "evidence_lineage_verified": (
            certification.evidence_lineage_required
        ),
        "parent_lineage_verified": (
            certification.parent_lineage_supported
        ),
        "confidence_bounds_verified": certification.confidence_bounded,
        "uncertainty_bounds_verified": certification.uncertainty_bounded,
        "duplicate_evidence_rejection_verified": (
            certification.duplicate_evidence_hashes_forbidden
        ),
        "duplicate_parent_rejection_verified": (
            certification.duplicate_parent_hashes_forbidden
        ),
        "persistent_storage_disabled_verified": (
            not certification.persistent_storage_enabled
        ),
        "learning_updates_disabled_verified": (
            not certification.learning_updates_enabled
        ),
        "runtime_activation_disabled_verified": (
            not certification.runtime_activation_enabled
        ),
        "publication_disabled_verified": (
            not certification.publication_enabled
        ),
        "action_authorization_disabled_verified": (
            not certification.action_authorization_enabled
        ),
        "qseries_execution_disabled_verified": (
            not certification.qseries_execution_enabled
        ),
        "upstream_continuation_authorized": (
            certification.next_certification_authorized
        ),
    }

    failed = [name for name, passed in checks.items() if not passed]

    if certification.certified_domain_ids != MEMORY_DOMAINS:
        failed.append("certified_domain_ids")

    if not certification.contract_ready:
        failed.append("contract_ready")

    if not certification.read_only:
        failed.append("read_only")

    if failed:
        _reject(
            "OML-006 record contract admission failed: "
            + ", ".join(failed)
        )

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": certification.schema_version,
        "upstream_engine_id": certification.engine_id,
        "upstream_policy_id": certification.policy_id,
        "upstream_certification_hash": certification.certification_hash,
        "upstream_admission_hash": certification.upstream_admission_hash,
        "upstream_registry_hash": certification.upstream_registry_hash,
        "certified_domain_ids": certification.certified_domain_ids,
        **checks,
        "admission_status": ADMISSION_STATUS_ADMITTED,
        "admitted": True,
        "next_certification_authorized": True,
        "read_only": True,
        "failure_reason": None,
    }

    decision = OracleMemoryCanonicalRecordContractAdmissionDecision(
        **body,
        decision_hash=_stable_hash(body),
    )

    verify_oracle_memory_canonical_record_contract_admission_decision(
        decision
    )
    return decision


def verify_oracle_memory_canonical_record_contract_admission_decision(
    decision: OracleMemoryCanonicalRecordContractAdmissionDecision,
) -> bool:
    body = asdict(decision)
    supplied = body.pop("decision_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-006 admission decision hash mismatch")

    if decision.schema_version != SCHEMA_VERSION:
        _reject("OML-006 schema mismatch")

    if decision.engine_id != ENGINE_ID:
        _reject("OML-006 engine mismatch")

    if decision.policy_id != POLICY_ID:
        _reject("OML-006 policy mismatch")

    if decision.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-006 subsystem mismatch")

    if decision.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-006 admitted upstream schema mismatch")

    if decision.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-006 admitted upstream engine mismatch")

    if decision.upstream_policy_id != UPSTREAM_POLICY_ID:
        _reject("OML-006 admitted upstream policy mismatch")

    hashes = (
        decision.upstream_certification_hash,
        decision.upstream_admission_hash,
        decision.upstream_registry_hash,
        decision.decision_hash,
    )

    if any(len(value) != 64 for value in hashes):
        _reject("OML-006 lineage hash length invalid")

    if decision.certified_domain_ids != MEMORY_DOMAINS:
        _reject("OML-006 admitted domain identity mismatch")

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
        _reject("OML-006 admitted decision missing required guarantee")

    if decision.admission_status != ADMISSION_STATUS_ADMITTED:
        _reject("OML-006 admission status mismatch")

    if decision.failure_reason is not None:
        _reject("OML-006 admitted decision contains failure reason")

    return True
"""

TEST_SOURCE = r"""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_canonical_record_contract import (
    build_oracle_memory_canonical_record_contract_certification,
)
from qseries_v2.oracle_memory.oracle_memory_canonical_record_contract_admission_gate import (
    ADMISSION_STATUS_ADMITTED,
    OracleMemoryCanonicalRecordContractAdmissionInvariantError,
    build_oracle_memory_canonical_record_contract_admission_decision,
    verify_oracle_memory_canonical_record_contract_admission_decision,
)
from qseries_v2.oracle_memory.oracle_memory_certified_domain_registry import (
    build_oracle_memory_certified_domain_registry,
)
from qseries_v2.oracle_memory.oracle_memory_certified_domain_registry_admission_gate import (
    build_oracle_memory_domain_registry_admission_decision,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    MEMORY_DOMAINS,
    build_oracle_memory_learner_foundation_report,
)
from qseries_v2.oracle_memory.oracle_memory_learner_foundation_admission_gate import (
    build_oracle_memory_learner_foundation_admission_decision,
)


def load_module(path: Path, name: str):
    specification = importlib.util.spec_from_file_location(name, path)

    if specification is None or specification.loader is None:
        raise RuntimeError(f"unable to load fixture: {path}")

    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def build_oml_005_certification(root: Path):
    fixture = load_module(
        root
        / "test_oit_050_oracle_terminal_final_freeze_and_completion.py",
        "oit_050_fixture_for_oml_006",
    )

    from qseries_v2.oracle_terminal.oracle_terminal_final_freeze_and_completion import (
        build_oracle_terminal_final_freeze_completion_report,
    )

    oit_049 = fixture.build_oit_049_report(root)
    oit_050 = build_oracle_terminal_final_freeze_completion_report(
        root,
        production_certification_report=oit_049,
    )

    oml_001 = build_oracle_memory_learner_foundation_report(
        root,
        oit_final_freeze_report=oit_050,
    )

    oml_002 = build_oracle_memory_learner_foundation_admission_decision(
        root,
        foundation_report=oml_001,
    )

    oml_003 = build_oracle_memory_certified_domain_registry(
        admission_decision=oml_002,
    )

    oml_004 = build_oracle_memory_domain_registry_admission_decision(
        registry=oml_003,
    )

    return build_oracle_memory_canonical_record_contract_certification(
        admission_decision=oml_004,
    )


def expect_rejection(callable_object, label: str) -> None:
    try:
        callable_object()
    except OracleMemoryCanonicalRecordContractAdmissionInvariantError:
        return

    raise AssertionError(f"tampered OML-006 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-006 TEST")
    print(" CANONICAL RECORD CONTRACT ADMISSION GATE")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    certification = build_oml_005_certification(root)

    decision = (
        build_oracle_memory_canonical_record_contract_admission_decision(
            certification=certification,
        )
    )

    assert decision.schema_version == "OML-006"
    assert decision.engine_id == "OML-006"
    assert decision.upstream_schema_version == "OML-005"
    assert decision.upstream_engine_id == "OML-005"
    assert decision.upstream_certification_hash == (
        certification.certification_hash
    )
    assert decision.upstream_admission_hash == (
        certification.upstream_admission_hash
    )
    assert decision.upstream_registry_hash == (
        certification.upstream_registry_hash
    )
    assert decision.certified_domain_ids == MEMORY_DOMAINS

    assert decision.contract_verified
    assert decision.upstream_identity_verified
    assert decision.upstream_lineage_verified
    assert decision.canonical_serialization_verified
    assert decision.deterministic_hashing_verified
    assert decision.immutable_identity_verified
    assert decision.evidence_lineage_verified
    assert decision.parent_lineage_verified
    assert decision.confidence_bounds_verified
    assert decision.uncertainty_bounds_verified
    assert decision.duplicate_evidence_rejection_verified
    assert decision.duplicate_parent_rejection_verified
    assert decision.persistent_storage_disabled_verified
    assert decision.learning_updates_disabled_verified
    assert decision.runtime_activation_disabled_verified
    assert decision.publication_disabled_verified
    assert decision.action_authorization_disabled_verified
    assert decision.qseries_execution_disabled_verified
    assert decision.upstream_continuation_authorized
    assert decision.admission_status == ADMISSION_STATUS_ADMITTED
    assert decision.admitted
    assert decision.next_certification_authorized
    assert decision.read_only
    assert decision.failure_reason is None

    replay = (
        build_oracle_memory_canonical_record_contract_admission_decision(
            certification=certification,
        )
    )

    assert replay == decision
    assert (
        verify_oracle_memory_canonical_record_contract_admission_decision(
            decision
        )
    )

    expect_rejection(
        lambda: verify_oracle_memory_canonical_record_contract_admission_decision(
            replace(decision, canonical_serialization_verified=False)
        ),
        "canonical serialization guarantee",
    )

    expect_rejection(
        lambda: verify_oracle_memory_canonical_record_contract_admission_decision(
            replace(decision, persistent_storage_disabled_verified=False)
        ),
        "persistent storage boundary",
    )

    expect_rejection(
        lambda: verify_oracle_memory_canonical_record_contract_admission_decision(
            replace(decision, learning_updates_disabled_verified=False)
        ),
        "learning update boundary",
    )

    expect_rejection(
        lambda: verify_oracle_memory_canonical_record_contract_admission_decision(
            replace(decision, publication_disabled_verified=False)
        ),
        "publication boundary",
    )

    expect_rejection(
        lambda: verify_oracle_memory_canonical_record_contract_admission_decision(
            replace(decision, qseries_execution_disabled_verified=False)
        ),
        "Q Series execution boundary",
    )

    print("[PASS] Certified OML-005 contract consumed")
    print("[PASS] OML-005 identity and policy verified")
    print("[PASS] OML-004 through OIT-050 lineage retained")
    print("[PASS] Eight certified memory domains admitted")
    print("[PASS] Canonical serialization contract admitted")
    print("[PASS] Deterministic record hashing admitted")
    print("[PASS] Immutable record identity admitted")
    print("[PASS] Evidence and parent lineage admitted")
    print("[PASS] Confidence and uncertainty bounds admitted")
    print("[PASS] Duplicate lineage rejection admitted")
    print("[PASS] Persistent storage remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Admission deterministic across replay")
    print("[PASS] Tampered admission decisions rejected")
    print("[DONE] OML-006 CANONICAL RECORD CONTRACT ADMISSION GATE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def write_complete(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def validate_actual_oml_005() -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_canonical_record_contract"
    )

    expected = {
        "SCHEMA_VERSION": "OML-005",
        "ENGINE_ID": "OML-005",
        "POLICY_ID": "oracle-memory.canonical-record-contract.v1",
        "UPSTREAM_SCHEMA_VERSION": "OML-004",
        "UPSTREAM_ENGINE_ID": "OML-004",
        "RECORD_STATE_CONTRACT_ONLY": "contract_only",
    }

    for name, value in expected.items():
        actual = getattr(module, name, None)

        if actual != value:
            raise RuntimeError(
                f"Certified OML-005 {name} mismatch: "
                f"expected {value!r}, got {actual!r}"
            )

    required = (
        "OracleMemoryCanonicalRecord",
        "OracleMemoryCanonicalRecordContractCertification",
        "build_oracle_memory_canonical_record",
        "verify_oracle_memory_canonical_record",
        "build_oracle_memory_canonical_record_contract_certification",
        "verify_oracle_memory_canonical_record_contract_certification",
    )

    missing = [name for name in required if not hasattr(module, name)]

    if missing:
        raise RuntimeError(
            "Certified OML-005 missing required symbols: "
            + ", ".join(missing)
        )


def main() -> int:
    print("=" * 48)
    print(" OML-006 FOR-SURE INSTALLER")
    print(" CANONICAL RECORD CONTRACT ADMISSION GATE")
    print("=" * 48)
    print("[BOOT] Revision: IMPORT_ALIGNED_FULL_REPLACEMENT")

    try:
        validate_actual_oml_005()
        print("[OK] Actual OML-005 imported and structurally verified")

        upstream = subprocess.run(
            [sys.executable, str(OML_005_TEST)],
            cwd=ROOT,
            check=False,
        )

        if upstream.returncode:
            raise RuntimeError(
                "OML-005 certification failed with exit code "
                f"{upstream.returncode}"
            )

        production_before = OML_005.read_bytes()
        test_before = OML_005_TEST.read_bytes()

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_memory_canonical_record_contract_admission_gate "
            "import *"
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

        completed = subprocess.run(
            [sys.executable, str(TEST)],
            cwd=ROOT,
            check=False,
        )

        if completed.returncode:
            raise RuntimeError(
                "OML-006 test failed with exit code "
                f"{completed.returncode}"
            )

        if OML_005.read_bytes() != production_before:
            raise RuntimeError("Certified OML-005 production changed")

        if OML_005_TEST.read_bytes() != test_before:
            raise RuntimeError("Certified OML-005 standalone test changed")

        print("[PASS] Certified OML-005 production unchanged")
        print("[PASS] Certified OML-005 standalone test unchanged")
        print("[PASS] OML-006 production admission gate installed")
        print("[PASS] OML-006 standalone deterministic test installed")
        print("[PASS] Canonical record contract admitted")
        print("[PASS] Deterministic and immutable guarantees admitted")
        print("[PASS] Evidence and parent lineage admitted")
        print("[PASS] Persistent storage remained disabled")
        print("[PASS] Continuous learning remained disabled")
        print("[PASS] Runtime activation remained disabled")
        print("[PASS] Publication remained disabled")
        print("[PASS] Action authorization remained disabled")
        print("[PASS] Q Series execution remained disabled")
        print(f"[PASS] Repository located: {ROOT}")
        print(
            "[DONE] OML-006 CANONICAL RECORD CONTRACT "
            "ADMISSION GATE INSTALLED"
        )
        return 0

    except (RuntimeError, SyntaxError, ImportError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
