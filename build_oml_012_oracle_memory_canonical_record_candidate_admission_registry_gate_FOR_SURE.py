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
            / "oracle_memory_canonical_record_candidate_admission_registry.py"
        )
        upstream_test = (
            candidate
            / "test_oml_011_oracle_memory_canonical_record_candidate_admission_registry.py"
        )

        if upstream.is_file() and upstream_test.is_file():
            return candidate

    raise RuntimeError(
        "Could not locate repository containing certified OML-011."
    )


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_memory"

OML_011 = (
    PACKAGE
    / "oracle_memory_canonical_record_candidate_admission_registry.py"
)
OML_011_TEST = (
    ROOT
    / "test_oml_011_oracle_memory_canonical_record_candidate_admission_registry.py"
)

PRODUCTION = (
    PACKAGE
    / "oracle_memory_canonical_record_candidate_admission_registry_gate.py"
)
TEST = (
    ROOT
    / "test_oml_012_oracle_memory_canonical_record_candidate_admission_registry_gate.py"
)
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from qseries_v2.oracle_memory.oracle_memory_canonical_record_candidate_admission_registry import (
    ENGINE_ID as OML_011_ENGINE_ID,
    POLICY_ID as OML_011_POLICY_ID,
    REGISTRY_STATUS_CERTIFIED,
    SCHEMA_VERSION as OML_011_SCHEMA_VERSION,
    OracleMemoryCanonicalRecordCandidateAdmissionRegistry,
    verify_oracle_memory_canonical_record_candidate_admission_registry,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    MEMORY_DOMAINS,
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-012"
ENGINE_ID = "OML-012"
POLICY_ID = (
    "oracle-memory.canonical-record-candidate-admission-registry-gate.v1"
)

UPSTREAM_SCHEMA_VERSION = "OML-011"
UPSTREAM_ENGINE_ID = "OML-011"
UPSTREAM_POLICY_ID = (
    "oracle-memory.canonical-record-candidate-admission-registry.v1"
)

GATE_STATUS_ADMITTED = "admitted"


class OracleMemoryCanonicalRecordCandidateAdmissionRegistryGateInvariantError(
    RuntimeError
):
    pass


@dataclass(frozen=True)
class OracleMemoryCanonicalRecordCandidateAdmissionRegistryGateDecision:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_policy_id: str
    upstream_registry_hash: str
    upstream_decision_hash: str
    upstream_certification_hash: str
    upstream_gate_decision_hash: str
    upstream_domain_registry_hash: str
    admitted_domain_ids: tuple[str, ...]
    admitted_entry_hashes: tuple[str, ...]
    admitted_entry_count: int
    registry_verified: bool
    registry_status_verified: bool
    upstream_identity_verified: bool
    upstream_lineage_verified: bool
    domain_count_verified: bool
    domain_order_verified: bool
    domain_uniqueness_verified: bool
    entry_hashes_verified: bool
    candidate_contracts_admitted_verified: bool
    candidate_admissions_disabled_verified: bool
    entries_inactive_verified: bool
    entries_non_writing_verified: bool
    entries_read_only_verified: bool
    persistent_storage_disabled_verified: bool
    learning_updates_disabled_verified: bool
    runtime_activation_disabled_verified: bool
    publication_disabled_verified: bool
    action_authorization_disabled_verified: bool
    qseries_execution_disabled_verified: bool
    upstream_continuation_authorized: bool
    gate_status: str
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

    raise OracleMemoryCanonicalRecordCandidateAdmissionRegistryGateInvariantError(
        "unsupported OML-012 value type: "
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
    raise OracleMemoryCanonicalRecordCandidateAdmissionRegistryGateInvariantError(
        reason
    )


def build_oracle_memory_canonical_record_candidate_admission_registry_gate_decision(
    *,
    registry: OracleMemoryCanonicalRecordCandidateAdmissionRegistry,
) -> OracleMemoryCanonicalRecordCandidateAdmissionRegistryGateDecision:
    verify_oracle_memory_canonical_record_candidate_admission_registry(
        registry
    )

    if OML_011_SCHEMA_VERSION != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-012 upstream schema constant mismatch")

    if OML_011_ENGINE_ID != UPSTREAM_ENGINE_ID:
        _reject("OML-012 upstream engine constant mismatch")

    if OML_011_POLICY_ID != UPSTREAM_POLICY_ID:
        _reject("OML-012 upstream policy constant mismatch")

    if registry.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-012 upstream registry schema mismatch")

    if registry.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-012 upstream registry engine mismatch")

    if registry.policy_id != UPSTREAM_POLICY_ID:
        _reject("OML-012 upstream registry policy mismatch")

    domain_ids = tuple(entry.domain_id for entry in registry.entries)
    entry_hashes = tuple(entry.entry_hash for entry in registry.entries)

    checks = {
        "registry_verified": True,
        "registry_status_verified": (
            registry.registry_status == REGISTRY_STATUS_CERTIFIED
        ),
        "upstream_identity_verified": (
            registry.subsystem_id == SUBSYSTEM_ID
        ),
        "upstream_lineage_verified": all(
            len(value) == 64
            for value in (
                registry.registry_hash,
                registry.upstream_decision_hash,
                registry.upstream_certification_hash,
                registry.upstream_gate_decision_hash,
                registry.upstream_registry_hash,
            )
        ),
        "domain_count_verified": (
            registry.entry_count == len(MEMORY_DOMAINS)
            and len(registry.entries) == len(MEMORY_DOMAINS)
        ),
        "domain_order_verified": domain_ids == MEMORY_DOMAINS,
        "domain_uniqueness_verified": (
            len(set(domain_ids)) == len(domain_ids)
        ),
        "entry_hashes_verified": (
            len(entry_hashes) == len(MEMORY_DOMAINS)
            and len(set(entry_hashes)) == len(entry_hashes)
            and all(len(value) == 64 for value in entry_hashes)
        ),
        "candidate_contracts_admitted_verified": (
            registry.all_contracts_admitted
            and all(
                entry.canonical_candidate_contract_admitted
                for entry in registry.entries
            )
        ),
        "candidate_admissions_disabled_verified": (
            registry.all_candidate_admissions_disabled
            and all(
                not entry.candidate_admission_authorized
                for entry in registry.entries
            )
        ),
        "entries_inactive_verified": (
            registry.all_entries_inactive
            and all(
                not entry.runtime_activation_authorized
                for entry in registry.entries
            )
        ),
        "entries_non_writing_verified": (
            registry.all_entries_non_writing
            and all(
                not entry.persistent_storage_authorized
                and not entry.learning_update_authorized
                for entry in registry.entries
            )
        ),
        "entries_read_only_verified": (
            registry.all_entries_read_only
            and all(entry.read_only for entry in registry.entries)
        ),
        "persistent_storage_disabled_verified": all(
            not entry.persistent_storage_authorized
            for entry in registry.entries
        ),
        "learning_updates_disabled_verified": all(
            not entry.learning_update_authorized
            for entry in registry.entries
        ),
        "runtime_activation_disabled_verified": all(
            not entry.runtime_activation_authorized
            for entry in registry.entries
        ),
        "publication_disabled_verified": (
            registry.publication_disabled
            and all(
                not entry.publication_authorized
                for entry in registry.entries
            )
        ),
        "action_authorization_disabled_verified": (
            registry.action_authorization_disabled
            and all(
                not entry.action_authorization_enabled
                for entry in registry.entries
            )
        ),
        "qseries_execution_disabled_verified": (
            registry.qseries_execution_disabled
            and all(
                not entry.qseries_execution_authorized
                for entry in registry.entries
            )
        ),
        "upstream_continuation_authorized": (
            registry.next_certification_authorized
        ),
    }

    failed = [name for name, passed in checks.items() if not passed]

    if failed:
        _reject(
            "OML-012 candidate admission registry gate failed: "
            + ", ".join(failed)
        )

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": registry.schema_version,
        "upstream_engine_id": registry.engine_id,
        "upstream_policy_id": registry.policy_id,
        "upstream_registry_hash": registry.registry_hash,
        "upstream_decision_hash": registry.upstream_decision_hash,
        "upstream_certification_hash": (
            registry.upstream_certification_hash
        ),
        "upstream_gate_decision_hash": (
            registry.upstream_gate_decision_hash
        ),
        "upstream_domain_registry_hash": (
            registry.upstream_registry_hash
        ),
        "admitted_domain_ids": domain_ids,
        "admitted_entry_hashes": entry_hashes,
        "admitted_entry_count": len(registry.entries),
        **checks,
        "gate_status": GATE_STATUS_ADMITTED,
        "admitted": True,
        "next_certification_authorized": True,
        "read_only": True,
        "failure_reason": None,
    }

    decision = (
        OracleMemoryCanonicalRecordCandidateAdmissionRegistryGateDecision(
            **body,
            decision_hash=_stable_hash(body),
        )
    )

    verify_oracle_memory_canonical_record_candidate_admission_registry_gate_decision(
        decision
    )
    return decision


def verify_oracle_memory_canonical_record_candidate_admission_registry_gate_decision(
    decision: OracleMemoryCanonicalRecordCandidateAdmissionRegistryGateDecision,
) -> bool:
    body = asdict(decision)
    supplied = body.pop("decision_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-012 decision hash mismatch")

    if decision.schema_version != SCHEMA_VERSION:
        _reject("OML-012 schema mismatch")

    if decision.engine_id != ENGINE_ID:
        _reject("OML-012 engine mismatch")

    if decision.policy_id != POLICY_ID:
        _reject("OML-012 policy mismatch")

    if decision.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-012 subsystem mismatch")

    if decision.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-012 admitted upstream schema mismatch")

    if decision.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-012 admitted upstream engine mismatch")

    if decision.upstream_policy_id != UPSTREAM_POLICY_ID:
        _reject("OML-012 admitted upstream policy mismatch")

    hashes = (
        decision.upstream_registry_hash,
        decision.upstream_decision_hash,
        decision.upstream_certification_hash,
        decision.upstream_gate_decision_hash,
        decision.upstream_domain_registry_hash,
        decision.decision_hash,
    )

    if any(len(value) != 64 for value in hashes):
        _reject("OML-012 lineage hash length invalid")

    if decision.admitted_domain_ids != MEMORY_DOMAINS:
        _reject("OML-012 admitted domain identity mismatch")

    if decision.admitted_entry_count != len(MEMORY_DOMAINS):
        _reject("OML-012 admitted entry count mismatch")

    if len(decision.admitted_entry_hashes) != len(MEMORY_DOMAINS):
        _reject("OML-012 admitted entry hash count mismatch")

    if len(set(decision.admitted_entry_hashes)) != len(
        decision.admitted_entry_hashes
    ):
        _reject("OML-012 admitted entry hashes not unique")

    if any(len(value) != 64 for value in decision.admitted_entry_hashes):
        _reject("OML-012 admitted entry hash length invalid")

    required_true = (
        decision.registry_verified,
        decision.registry_status_verified,
        decision.upstream_identity_verified,
        decision.upstream_lineage_verified,
        decision.domain_count_verified,
        decision.domain_order_verified,
        decision.domain_uniqueness_verified,
        decision.entry_hashes_verified,
        decision.candidate_contracts_admitted_verified,
        decision.candidate_admissions_disabled_verified,
        decision.entries_inactive_verified,
        decision.entries_non_writing_verified,
        decision.entries_read_only_verified,
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
        _reject("OML-012 admitted decision missing required guarantee")

    if decision.gate_status != GATE_STATUS_ADMITTED:
        _reject("OML-012 gate status mismatch")

    if decision.failure_reason is not None:
        _reject("OML-012 admitted decision contains failure reason")

    return True
"""

TEST_SOURCE = r"""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_canonical_record_admission_registry import (
    build_oracle_memory_canonical_record_admission_registry,
)
from qseries_v2.oracle_memory.oracle_memory_canonical_record_admission_registry_gate import (
    build_oracle_memory_canonical_record_admission_registry_gate_decision,
)
from qseries_v2.oracle_memory.oracle_memory_canonical_record_candidate_admission_registry import (
    build_oracle_memory_canonical_record_candidate_admission_registry,
)
from qseries_v2.oracle_memory.oracle_memory_canonical_record_candidate_admission_registry_gate import (
    GATE_STATUS_ADMITTED,
    OracleMemoryCanonicalRecordCandidateAdmissionRegistryGateInvariantError,
    build_oracle_memory_canonical_record_candidate_admission_registry_gate_decision,
    verify_oracle_memory_canonical_record_candidate_admission_registry_gate_decision,
)
from qseries_v2.oracle_memory.oracle_memory_canonical_record_candidate_contract import (
    build_oracle_memory_canonical_record_candidate_contract_certification,
)
from qseries_v2.oracle_memory.oracle_memory_canonical_record_candidate_contract_admission_gate import (
    build_oracle_memory_canonical_record_candidate_contract_admission_decision,
)
from qseries_v2.oracle_memory.oracle_memory_canonical_record_contract import (
    build_oracle_memory_canonical_record_contract_certification,
)
from qseries_v2.oracle_memory.oracle_memory_canonical_record_contract_admission_gate import (
    build_oracle_memory_canonical_record_contract_admission_decision,
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


def build_oml_011_registry(root: Path):
    fixture = load_module(
        root
        / "test_oit_050_oracle_terminal_final_freeze_and_completion.py",
        "oit_050_fixture_for_oml_012",
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
    oml_005 = build_oracle_memory_canonical_record_contract_certification(
        admission_decision=oml_004,
    )
    oml_006 = build_oracle_memory_canonical_record_contract_admission_decision(
        certification=oml_005,
    )
    oml_007 = build_oracle_memory_canonical_record_admission_registry(
        admission_decision=oml_006,
    )
    oml_008 = build_oracle_memory_canonical_record_admission_registry_gate_decision(
        registry=oml_007,
    )
    oml_009 = (
        build_oracle_memory_canonical_record_candidate_contract_certification(
            gate_decision=oml_008,
        )
    )
    oml_010 = (
        build_oracle_memory_canonical_record_candidate_contract_admission_decision(
            certification=oml_009,
        )
    )

    return (
        build_oracle_memory_canonical_record_candidate_admission_registry(
            admission_decision=oml_010,
        )
    )


def expect_rejection(callable_object, label: str) -> None:
    try:
        callable_object()
    except OracleMemoryCanonicalRecordCandidateAdmissionRegistryGateInvariantError:
        return

    raise AssertionError(f"tampered OML-012 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-012 TEST")
    print(" CANDIDATE ADMISSION REGISTRY GATE")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    registry = build_oml_011_registry(root)

    decision = (
        build_oracle_memory_canonical_record_candidate_admission_registry_gate_decision(
            registry=registry,
        )
    )

    assert decision.schema_version == "OML-012"
    assert decision.engine_id == "OML-012"
    assert decision.upstream_schema_version == "OML-011"
    assert decision.upstream_engine_id == "OML-011"
    assert decision.upstream_registry_hash == registry.registry_hash
    assert decision.admitted_domain_ids == MEMORY_DOMAINS
    assert decision.admitted_entry_count == 8
    assert decision.admitted_entry_hashes == tuple(
        entry.entry_hash for entry in registry.entries
    )

    assert decision.registry_verified
    assert decision.registry_status_verified
    assert decision.upstream_identity_verified
    assert decision.upstream_lineage_verified
    assert decision.domain_count_verified
    assert decision.domain_order_verified
    assert decision.domain_uniqueness_verified
    assert decision.entry_hashes_verified
    assert decision.candidate_contracts_admitted_verified
    assert decision.candidate_admissions_disabled_verified
    assert decision.entries_inactive_verified
    assert decision.entries_non_writing_verified
    assert decision.entries_read_only_verified
    assert decision.persistent_storage_disabled_verified
    assert decision.learning_updates_disabled_verified
    assert decision.runtime_activation_disabled_verified
    assert decision.publication_disabled_verified
    assert decision.action_authorization_disabled_verified
    assert decision.qseries_execution_disabled_verified
    assert decision.upstream_continuation_authorized
    assert decision.gate_status == GATE_STATUS_ADMITTED
    assert decision.admitted
    assert decision.next_certification_authorized
    assert decision.read_only
    assert decision.failure_reason is None

    replay = (
        build_oracle_memory_canonical_record_candidate_admission_registry_gate_decision(
            registry=registry,
        )
    )

    assert replay == decision
    assert (
        verify_oracle_memory_canonical_record_candidate_admission_registry_gate_decision(
            decision
        )
    )

    expect_rejection(
        lambda: verify_oracle_memory_canonical_record_candidate_admission_registry_gate_decision(
            replace(decision, admitted_entry_count=7)
        ),
        "entry count",
    )

    expect_rejection(
        lambda: verify_oracle_memory_canonical_record_candidate_admission_registry_gate_decision(
            replace(
                decision,
                candidate_admissions_disabled_verified=False,
            )
        ),
        "candidate admission boundary",
    )

    expect_rejection(
        lambda: verify_oracle_memory_canonical_record_candidate_admission_registry_gate_decision(
            replace(decision, entries_non_writing_verified=False)
        ),
        "non-writing guarantee",
    )

    expect_rejection(
        lambda: verify_oracle_memory_canonical_record_candidate_admission_registry_gate_decision(
            replace(decision, qseries_execution_disabled_verified=False)
        ),
        "Q Series execution boundary",
    )

    print("[PASS] Certified OML-011 registry consumed")
    print("[PASS] OML-011 through OIT-050 lineage retained")
    print("[PASS] Eight candidate-admission entries admitted")
    print("[PASS] Domain order and entry hashes admitted")
    print("[PASS] Every candidate contract remained admitted")
    print("[PASS] Candidate admission remained disabled")
    print("[PASS] Every registry entry remained inactive")
    print("[PASS] Persistent storage remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Gate deterministic across replay")
    print("[PASS] Tampered gate decisions rejected")
    print("[DONE] OML-012 CANDIDATE ADMISSION REGISTRY GATE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def write_complete(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def validate_actual_oml_011() -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_canonical_record_candidate_admission_registry"
    )

    expected = {
        "SCHEMA_VERSION": "OML-011",
        "ENGINE_ID": "OML-011",
        "POLICY_ID": (
            "oracle-memory.canonical-record-candidate-admission-registry.v1"
        ),
        "UPSTREAM_SCHEMA_VERSION": "OML-010",
        "UPSTREAM_ENGINE_ID": "OML-010",
        "REGISTRY_STATUS_CERTIFIED": "certified_inactive",
    }

    for name, value in expected.items():
        actual = getattr(module, name, None)

        if actual != value:
            raise RuntimeError(
                f"Certified OML-011 {name} mismatch: "
                f"expected {value!r}, got {actual!r}"
            )

    required = (
        "OracleMemoryCanonicalRecordCandidateAdmissionEntry",
        "OracleMemoryCanonicalRecordCandidateAdmissionRegistry",
        "build_oracle_memory_canonical_record_candidate_admission_registry",
        "verify_oracle_memory_canonical_record_candidate_admission_entry",
        "verify_oracle_memory_canonical_record_candidate_admission_registry",
    )

    missing = [name for name in required if not hasattr(module, name)]

    if missing:
        raise RuntimeError(
            "Certified OML-011 missing required symbols: "
            + ", ".join(missing)
        )


def main() -> int:
    print("=" * 48)
    print(" OML-012 FOR-SURE INSTALLER")
    print(" CANDIDATE ADMISSION REGISTRY GATE")
    print("=" * 48)
    print("[BOOT] Revision: IMPORT_ALIGNED_FULL_REPLACEMENT")

    try:
        validate_actual_oml_011()
        print("[OK] Actual OML-011 imported and structurally verified")

        upstream = subprocess.run(
            [sys.executable, str(OML_011_TEST)],
            cwd=ROOT,
            check=False,
        )

        if upstream.returncode:
            raise RuntimeError(
                "OML-011 certification failed with exit code "
                f"{upstream.returncode}"
            )

        production_before = OML_011.read_bytes()
        test_before = OML_011_TEST.read_bytes()

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_memory_canonical_record_candidate_admission_registry_gate "
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
                "OML-012 test failed with exit code "
                f"{completed.returncode}"
            )

        if OML_011.read_bytes() != production_before:
            raise RuntimeError("Certified OML-011 production changed")

        if OML_011_TEST.read_bytes() != test_before:
            raise RuntimeError("Certified OML-011 standalone test changed")

        print("[PASS] Certified OML-011 production unchanged")
        print("[PASS] Certified OML-011 standalone test unchanged")
        print("[PASS] OML-012 production registry gate installed")
        print("[PASS] OML-012 standalone deterministic test installed")
        print("[PASS] Eight candidate-admission entries admitted")
        print("[PASS] Candidate admission remained disabled")
        print("[PASS] All entries remained inactive and non-writing")
        print("[PASS] Persistent memory remained disabled")
        print("[PASS] Continuous learning remained disabled")
        print("[PASS] Publication remained disabled")
        print("[PASS] Action authorization remained disabled")
        print("[PASS] Q Series execution remained disabled")
        print(f"[PASS] Repository located: {ROOT}")
        print(
            "[DONE] OML-012 CANDIDATE ADMISSION "
            "REGISTRY GATE INSTALLED"
        )
        return 0

    except (RuntimeError, SyntaxError, ImportError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
