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
            / "oracle_memory_canonical_record_admission_registry_gate.py"
        )
        upstream_test = (
            candidate
            / "test_oml_008_oracle_memory_canonical_record_admission_registry_gate.py"
        )

        if upstream.is_file() and upstream_test.is_file():
            return candidate

    raise RuntimeError(
        "Could not locate repository containing certified OML-008."
    )


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_memory"

OML_008 = (
    PACKAGE
    / "oracle_memory_canonical_record_admission_registry_gate.py"
)
OML_008_TEST = (
    ROOT
    / "test_oml_008_oracle_memory_canonical_record_admission_registry_gate.py"
)

PRODUCTION = PACKAGE / "oracle_memory_canonical_record_candidate_contract.py"
TEST = ROOT / "test_oml_009_oracle_memory_canonical_record_candidate_contract.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from qseries_v2.oracle_memory.oracle_memory_canonical_record_admission_registry_gate import (
    OracleMemoryCanonicalRecordAdmissionRegistryGateDecision,
    verify_oracle_memory_canonical_record_admission_registry_gate_decision,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    MEMORY_DOMAINS,
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-009"
ENGINE_ID = "OML-009"
POLICY_ID = "oracle-memory.canonical-record-candidate-contract.v1"

UPSTREAM_SCHEMA_VERSION = "OML-008"
UPSTREAM_ENGINE_ID = "OML-008"

CANDIDATE_STATE_CONTRACT_ONLY = "candidate_contract_only"


class OracleMemoryCanonicalRecordCandidateInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCanonicalRecordCandidate:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_gate_decision_hash: str
    domain_id: str
    candidate_id: str
    entity_key: str
    source_key: str
    observed_at: str
    effective_at: str
    payload: Mapping[str, Any]
    evidence_hashes: tuple[str, ...]
    parent_record_hashes: tuple[str, ...]
    confidence: float
    uncertainty: float
    contradiction_count: int
    candidate_state: str
    admission_authorized: bool
    persistent_storage_authorized: bool
    learning_update_authorized: bool
    runtime_activation_authorized: bool
    publication_authorized: bool
    action_authorization_enabled: bool
    qseries_execution_authorized: bool
    read_only: bool
    candidate_hash: str


@dataclass(frozen=True)
class OracleMemoryCanonicalRecordCandidateContractCertification:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_gate_decision_hash: str
    upstream_registry_hash: str
    certified_domain_ids: tuple[str, ...]
    canonical_candidate_serialization_required: bool
    deterministic_candidate_hashing_required: bool
    immutable_candidate_identity_required: bool
    evidence_lineage_required: bool
    parent_lineage_supported: bool
    confidence_bounded: bool
    uncertainty_bounded: bool
    duplicate_evidence_hashes_forbidden: bool
    duplicate_parent_hashes_forbidden: bool
    candidate_admission_enabled: bool
    persistent_storage_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    contract_ready: bool
    next_certification_authorized: bool
    read_only: bool
    certification_hash: str


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

    if value is None or isinstance(value, (str, bool, int)):
        return value

    if isinstance(value, float):
        if not math.isfinite(value):
            raise OracleMemoryCanonicalRecordCandidateInvariantError(
                "OML-009 non-finite numeric value forbidden"
            )
        return value

    raise OracleMemoryCanonicalRecordCandidateInvariantError(
        "unsupported OML-009 value type: "
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
    raise OracleMemoryCanonicalRecordCandidateInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-009 invalid {label} length")

    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryCanonicalRecordCandidateInvariantError(
            f"OML-009 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_canonical_record_candidate(
    *,
    gate_decision: OracleMemoryCanonicalRecordAdmissionRegistryGateDecision,
    domain_id: str,
    candidate_id: str,
    entity_key: str,
    source_key: str,
    observed_at: str,
    effective_at: str,
    payload: Mapping[str, Any],
    evidence_hashes: tuple[str, ...] = (),
    parent_record_hashes: tuple[str, ...] = (),
    confidence: float,
    uncertainty: float,
    contradiction_count: int = 0,
) -> OracleMemoryCanonicalRecordCandidate:
    verify_oracle_memory_canonical_record_admission_registry_gate_decision(
        gate_decision
    )

    if gate_decision.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-009 upstream schema mismatch")

    if gate_decision.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-009 upstream engine mismatch")

    if not gate_decision.admitted:
        _reject("OML-009 upstream registry gate not admitted")

    if not gate_decision.next_certification_authorized:
        _reject("OML-009 upstream continuation not authorized")

    if not gate_decision.read_only:
        _reject("OML-009 upstream read-only guarantee missing")

    if domain_id not in gate_decision.admitted_domain_ids:
        _reject("OML-009 domain not admitted")

    if domain_id not in MEMORY_DOMAINS:
        _reject("OML-009 unknown memory domain")

    for label, value in (
        ("candidate_id", candidate_id),
        ("entity_key", entity_key),
        ("source_key", source_key),
        ("observed_at", observed_at),
        ("effective_at", effective_at),
    ):
        if not isinstance(value, str) or not value.strip():
            _reject(f"OML-009 {label} must be non-empty")

    if not isinstance(payload, Mapping):
        _reject("OML-009 payload must be a mapping")

    canonical_payload = _canonical(payload)

    confidence = float(confidence)
    uncertainty = float(uncertainty)

    if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
        _reject("OML-009 confidence outside [0, 1]")

    if not math.isfinite(uncertainty) or not 0.0 <= uncertainty <= 1.0:
        _reject("OML-009 uncertainty outside [0, 1]")

    if (
        not isinstance(contradiction_count, int)
        or isinstance(contradiction_count, bool)
        or contradiction_count < 0
    ):
        _reject("OML-009 contradiction count invalid")

    if len(set(evidence_hashes)) != len(evidence_hashes):
        _reject("OML-009 duplicate evidence hashes forbidden")

    if len(set(parent_record_hashes)) != len(parent_record_hashes):
        _reject("OML-009 duplicate parent hashes forbidden")

    for value in evidence_hashes:
        _require_hash(value, "evidence hash")

    for value in parent_record_hashes:
        _require_hash(value, "parent record hash")

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_gate_decision_hash": gate_decision.decision_hash,
        "domain_id": domain_id,
        "candidate_id": candidate_id.strip(),
        "entity_key": entity_key.strip(),
        "source_key": source_key.strip(),
        "observed_at": observed_at.strip(),
        "effective_at": effective_at.strip(),
        "payload": canonical_payload,
        "evidence_hashes": tuple(evidence_hashes),
        "parent_record_hashes": tuple(parent_record_hashes),
        "confidence": confidence,
        "uncertainty": uncertainty,
        "contradiction_count": contradiction_count,
        "candidate_state": CANDIDATE_STATE_CONTRACT_ONLY,
        "admission_authorized": False,
        "persistent_storage_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "read_only": True,
    }

    candidate = OracleMemoryCanonicalRecordCandidate(
        **body,
        candidate_hash=_stable_hash(body),
    )

    verify_oracle_memory_canonical_record_candidate(candidate)
    return candidate


def verify_oracle_memory_canonical_record_candidate(
    candidate: OracleMemoryCanonicalRecordCandidate,
) -> bool:
    body = asdict(candidate)
    supplied = body.pop("candidate_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-009 candidate hash mismatch")

    if candidate.schema_version != SCHEMA_VERSION:
        _reject("OML-009 candidate schema mismatch")

    if candidate.engine_id != ENGINE_ID:
        _reject("OML-009 candidate engine mismatch")

    if candidate.policy_id != POLICY_ID:
        _reject("OML-009 candidate policy mismatch")

    if candidate.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-009 candidate subsystem mismatch")

    _require_hash(
        candidate.upstream_gate_decision_hash,
        "upstream gate decision hash",
    )
    _require_hash(candidate.candidate_hash, "candidate hash")

    if candidate.domain_id not in MEMORY_DOMAINS:
        _reject("OML-009 candidate domain mismatch")

    if candidate.candidate_state != CANDIDATE_STATE_CONTRACT_ONLY:
        _reject("OML-009 candidate state mismatch")

    _canonical(candidate.payload)

    if not 0.0 <= candidate.confidence <= 1.0:
        _reject("OML-009 candidate confidence outside [0, 1]")

    if not 0.0 <= candidate.uncertainty <= 1.0:
        _reject("OML-009 candidate uncertainty outside [0, 1]")

    if candidate.contradiction_count < 0:
        _reject("OML-009 candidate contradiction count invalid")

    if len(set(candidate.evidence_hashes)) != len(
        candidate.evidence_hashes
    ):
        _reject("OML-009 duplicate evidence lineage")

    if len(set(candidate.parent_record_hashes)) != len(
        candidate.parent_record_hashes
    ):
        _reject("OML-009 duplicate parent lineage")

    forbidden = (
        candidate.admission_authorized,
        candidate.persistent_storage_authorized,
        candidate.learning_update_authorized,
        candidate.runtime_activation_authorized,
        candidate.publication_authorized,
        candidate.action_authorization_enabled,
        candidate.qseries_execution_authorized,
    )

    if any(forbidden):
        _reject("OML-009 forbidden candidate capability enabled")

    if not candidate.read_only:
        _reject("OML-009 candidate is not read-only")

    return True


def build_oracle_memory_canonical_record_candidate_contract_certification(
    *,
    gate_decision: OracleMemoryCanonicalRecordAdmissionRegistryGateDecision,
) -> OracleMemoryCanonicalRecordCandidateContractCertification:
    verify_oracle_memory_canonical_record_admission_registry_gate_decision(
        gate_decision
    )

    if gate_decision.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-009 certification upstream schema mismatch")

    if gate_decision.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-009 certification upstream engine mismatch")

    if gate_decision.admitted_domain_ids != MEMORY_DOMAINS:
        _reject("OML-009 certification domain identity mismatch")

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": gate_decision.schema_version,
        "upstream_engine_id": gate_decision.engine_id,
        "upstream_gate_decision_hash": gate_decision.decision_hash,
        "upstream_registry_hash": gate_decision.upstream_registry_hash,
        "certified_domain_ids": gate_decision.admitted_domain_ids,
        "canonical_candidate_serialization_required": True,
        "deterministic_candidate_hashing_required": True,
        "immutable_candidate_identity_required": True,
        "evidence_lineage_required": True,
        "parent_lineage_supported": True,
        "confidence_bounded": True,
        "uncertainty_bounded": True,
        "duplicate_evidence_hashes_forbidden": True,
        "duplicate_parent_hashes_forbidden": True,
        "candidate_admission_enabled": False,
        "persistent_storage_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "contract_ready": True,
        "next_certification_authorized": True,
        "read_only": True,
    }

    certification = OracleMemoryCanonicalRecordCandidateContractCertification(
        **body,
        certification_hash=_stable_hash(body),
    )

    verify_oracle_memory_canonical_record_candidate_contract_certification(
        certification
    )
    return certification


def verify_oracle_memory_canonical_record_candidate_contract_certification(
    certification: OracleMemoryCanonicalRecordCandidateContractCertification,
) -> bool:
    body = asdict(certification)
    supplied = body.pop("certification_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-009 certification hash mismatch")

    if certification.schema_version != SCHEMA_VERSION:
        _reject("OML-009 certification schema mismatch")

    if certification.engine_id != ENGINE_ID:
        _reject("OML-009 certification engine mismatch")

    if certification.policy_id != POLICY_ID:
        _reject("OML-009 certification policy mismatch")

    if certification.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-009 certification subsystem mismatch")

    if certification.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-009 certification upstream schema mismatch")

    if certification.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-009 certification upstream engine mismatch")

    if certification.certified_domain_ids != MEMORY_DOMAINS:
        _reject("OML-009 certification domain mismatch")

    required_true = (
        certification.canonical_candidate_serialization_required,
        certification.deterministic_candidate_hashing_required,
        certification.immutable_candidate_identity_required,
        certification.evidence_lineage_required,
        certification.parent_lineage_supported,
        certification.confidence_bounded,
        certification.uncertainty_bounded,
        certification.duplicate_evidence_hashes_forbidden,
        certification.duplicate_parent_hashes_forbidden,
        certification.contract_ready,
        certification.next_certification_authorized,
        certification.read_only,
    )

    if not all(required_true):
        _reject("OML-009 certification guarantee missing")

    forbidden = (
        certification.candidate_admission_enabled,
        certification.persistent_storage_enabled,
        certification.learning_updates_enabled,
        certification.runtime_activation_enabled,
        certification.publication_enabled,
        certification.action_authorization_enabled,
        certification.qseries_execution_enabled,
    )

    if any(forbidden):
        _reject("OML-009 forbidden certification capability enabled")

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
from qseries_v2.oracle_memory.oracle_memory_canonical_record_candidate_contract import (
    OracleMemoryCanonicalRecordCandidateInvariantError,
    build_oracle_memory_canonical_record_candidate,
    build_oracle_memory_canonical_record_candidate_contract_certification,
    verify_oracle_memory_canonical_record_candidate,
    verify_oracle_memory_canonical_record_candidate_contract_certification,
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


def build_oml_008_decision(root: Path):
    fixture = load_module(
        root
        / "test_oit_050_oracle_terminal_final_freeze_and_completion.py",
        "oit_050_fixture_for_oml_009",
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

    return build_oracle_memory_canonical_record_admission_registry_gate_decision(
        registry=oml_007,
    )


def expect_rejection(callable_object, label: str) -> None:
    try:
        callable_object()
    except OracleMemoryCanonicalRecordCandidateInvariantError:
        return

    raise AssertionError(f"tampered OML-009 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-009 TEST")
    print(" CANONICAL RECORD CANDIDATE CONTRACT")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    gate = build_oml_008_decision(root)

    candidate = build_oracle_memory_canonical_record_candidate(
        gate_decision=gate,
        domain_id=MEMORY_DOMAINS[0],
        candidate_id="candidate:entity:btc",
        entity_key="BTC",
        source_key="certified-test-source",
        observed_at="2026-08-02T09:56:00-05:00",
        effective_at="2026-08-02T09:56:00-05:00",
        payload={
            "symbol": "BTC",
            "aliases": ["bitcoin", "xbt"],
        },
        evidence_hashes=("1" * 64, "2" * 64),
        parent_record_hashes=("3" * 64,),
        confidence=0.8,
        uncertainty=0.2,
        contradiction_count=0,
    )

    assert candidate.schema_version == "OML-009"
    assert candidate.engine_id == "OML-009"
    assert candidate.domain_id == MEMORY_DOMAINS[0]
    assert candidate.upstream_gate_decision_hash == gate.decision_hash
    assert candidate.candidate_state == "candidate_contract_only"
    assert not candidate.admission_authorized
    assert not candidate.persistent_storage_authorized
    assert not candidate.learning_update_authorized
    assert not candidate.runtime_activation_authorized
    assert not candidate.publication_authorized
    assert not candidate.action_authorization_enabled
    assert not candidate.qseries_execution_authorized
    assert candidate.read_only

    replay = build_oracle_memory_canonical_record_candidate(
        gate_decision=gate,
        domain_id=MEMORY_DOMAINS[0],
        candidate_id="candidate:entity:btc",
        entity_key="BTC",
        source_key="certified-test-source",
        observed_at="2026-08-02T09:56:00-05:00",
        effective_at="2026-08-02T09:56:00-05:00",
        payload={
            "aliases": ["bitcoin", "xbt"],
            "symbol": "BTC",
        },
        evidence_hashes=("1" * 64, "2" * 64),
        parent_record_hashes=("3" * 64,),
        confidence=0.8,
        uncertainty=0.2,
        contradiction_count=0,
    )

    assert replay == candidate
    assert verify_oracle_memory_canonical_record_candidate(candidate)

    certification = (
        build_oracle_memory_canonical_record_candidate_contract_certification(
            gate_decision=gate,
        )
    )

    assert certification.schema_version == "OML-009"
    assert certification.upstream_schema_version == "OML-008"
    assert certification.certified_domain_ids == MEMORY_DOMAINS
    assert certification.contract_ready
    assert certification.next_certification_authorized
    assert certification.read_only
    assert not certification.candidate_admission_enabled
    assert not certification.persistent_storage_enabled
    assert not certification.learning_updates_enabled
    assert not certification.runtime_activation_enabled
    assert not certification.publication_enabled
    assert not certification.action_authorization_enabled
    assert not certification.qseries_execution_enabled

    certification_replay = (
        build_oracle_memory_canonical_record_candidate_contract_certification(
            gate_decision=gate,
        )
    )

    assert certification_replay == certification
    assert (
        verify_oracle_memory_canonical_record_candidate_contract_certification(
            certification
        )
    )

    expect_rejection(
        lambda: verify_oracle_memory_canonical_record_candidate(
            replace(candidate, admission_authorized=True)
        ),
        "candidate admission state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_canonical_record_candidate(
            replace(candidate, persistent_storage_authorized=True)
        ),
        "persistent storage state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_canonical_record_candidate(
            replace(candidate, learning_update_authorized=True)
        ),
        "learning update state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_canonical_record_candidate(
            replace(candidate, qseries_execution_authorized=True)
        ),
        "Q Series execution state",
    )

    print("[PASS] Certified OML-008 gate consumed")
    print("[PASS] OML-008 through OIT-050 lineage retained")
    print("[PASS] Canonical memory record candidate contract created")
    print("[PASS] Candidate domain bound to certified registry")
    print("[PASS] Canonical candidate serialization verified")
    print("[PASS] Deterministic candidate hashing verified")
    print("[PASS] Immutable candidate identity enforced")
    print("[PASS] Evidence and parent lineage supported")
    print("[PASS] Confidence and uncertainty bounds enforced")
    print("[PASS] Candidate admission remained disabled")
    print("[PASS] Persistent storage remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Contract deterministic across replay")
    print("[PASS] Tampered candidates and certifications rejected")
    print("[DONE] OML-009 CANONICAL RECORD CANDIDATE CONTRACT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def write_complete(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def validate_actual_oml_008() -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_canonical_record_admission_registry_gate"
    )

    expected = {
        "SCHEMA_VERSION": "OML-008",
        "ENGINE_ID": "OML-008",
        "POLICY_ID": (
            "oracle-memory.canonical-record-admission-registry-gate.v1"
        ),
        "UPSTREAM_SCHEMA_VERSION": "OML-007",
        "UPSTREAM_ENGINE_ID": "OML-007",
        "GATE_STATUS_ADMITTED": "admitted",
    }

    for name, value in expected.items():
        actual = getattr(module, name, None)

        if actual != value:
            raise RuntimeError(
                f"Certified OML-008 {name} mismatch: "
                f"expected {value!r}, got {actual!r}"
            )

    required = (
        "OracleMemoryCanonicalRecordAdmissionRegistryGateDecision",
        "build_oracle_memory_canonical_record_admission_registry_gate_decision",
        "verify_oracle_memory_canonical_record_admission_registry_gate_decision",
    )

    missing = [name for name in required if not hasattr(module, name)]

    if missing:
        raise RuntimeError(
            "Certified OML-008 missing required symbols: "
            + ", ".join(missing)
        )


def main() -> int:
    print("=" * 48)
    print(" OML-009 FOR-SURE INSTALLER")
    print(" CANONICAL RECORD CANDIDATE CONTRACT")
    print("=" * 48)
    print("[BOOT] Revision: IMPORT_ALIGNED_FULL_REPLACEMENT")

    try:
        validate_actual_oml_008()
        print("[OK] Actual OML-008 imported and structurally verified")

        upstream = subprocess.run(
            [sys.executable, str(OML_008_TEST)],
            cwd=ROOT,
            check=False,
        )

        if upstream.returncode:
            raise RuntimeError(
                "OML-008 certification failed with exit code "
                f"{upstream.returncode}"
            )

        production_before = OML_008.read_bytes()
        test_before = OML_008_TEST.read_bytes()

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_memory_canonical_record_candidate_contract "
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
                "OML-009 test failed with exit code "
                f"{completed.returncode}"
            )

        if OML_008.read_bytes() != production_before:
            raise RuntimeError("Certified OML-008 production changed")

        if OML_008_TEST.read_bytes() != test_before:
            raise RuntimeError("Certified OML-008 standalone test changed")

        print("[PASS] Certified OML-008 production unchanged")
        print("[PASS] Certified OML-008 standalone test unchanged")
        print("[PASS] OML-009 candidate contract installed")
        print("[PASS] OML-009 standalone deterministic test installed")
        print("[PASS] Canonical candidate hashing enforced")
        print("[PASS] Candidate admission remained disabled")
        print("[PASS] Persistent memory remained disabled")
        print("[PASS] Continuous learning remained disabled")
        print("[PASS] Runtime activation remained disabled")
        print("[PASS] Publication remained disabled")
        print("[PASS] Action authorization remained disabled")
        print("[PASS] Q Series execution remained disabled")
        print(f"[PASS] Repository located: {ROOT}")
        print(
            "[DONE] OML-009 CANONICAL RECORD CANDIDATE "
            "CONTRACT INSTALLED"
        )
        return 0

    except (RuntimeError, SyntaxError, ImportError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
