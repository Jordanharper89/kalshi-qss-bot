from __future__ import annotations

import ast
import importlib
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "oracle_memory"

UPSTREAM = PACKAGE / "oracle_memory_cross_market_dependency_memory.py"
UPSTREAM_TEST = ROOT / "test_oml_026_oracle_memory_cross_market_dependency_memory.py"

PRODUCTION = PACKAGE / "oracle_memory_certified_observation_intake_contract.py"
TEST = ROOT / "test_oml_027_oracle_memory_certified_observation_intake_contract.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    MEMORY_DOMAINS,
    SUBSYSTEM_ID,
)
from qseries_v2.oracle_memory.oracle_memory_cross_market_dependency_memory import (
    OracleMemoryCrossMarketDependencyMemory,
    verify_oracle_memory_cross_market_dependency_memory,
)

SCHEMA_VERSION = "OML-027"
ENGINE_ID = "OML-027"
POLICY_ID = "oracle-memory.certified-observation-intake-contract.v1"

UPSTREAM_SCHEMA_VERSION = "OML-026"
UPSTREAM_ENGINE_ID = "OML-026"

OBSERVATION_STATE_CERTIFIED_INTAKE_ONLY = "certified_intake_only"
BATCH_STATE_CONTRACT_ONLY = "contract_only"

OBSERVATION_KIND_REAL_WORLD = "real_world"
OBSERVATION_KIND_MARKET = "market"
OBSERVATION_KIND_SOURCE = "source"
OBSERVATION_KIND_EVENT = "event"

ALLOWED_OBSERVATION_KINDS = (
    OBSERVATION_KIND_REAL_WORLD,
    OBSERVATION_KIND_MARKET,
    OBSERVATION_KIND_SOURCE,
    OBSERVATION_KIND_EVENT,
)


class OracleMemoryObservationIntakeInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCertifiedObservation:
    observation_id: str
    observation_kind: str
    domain_id: str
    entity_key: str
    source_key: str
    observed_at: str
    effective_at: str
    payload: Mapping[str, Any]
    evidence_hashes: tuple[str, ...]
    parent_observation_hashes: tuple[str, ...]
    confidence: float
    uncertainty: float
    contradiction_count: int
    source_certification_hash: str
    observation_state: str
    deterministic_identity_verified: bool
    canonical_payload_verified: bool
    evidence_lineage_verified: bool
    parent_lineage_verified: bool
    persistence_authorized: bool
    learning_update_authorized: bool
    runtime_activation_authorized: bool
    publication_authorized: bool
    action_authorization_enabled: bool
    qseries_execution_authorized: bool
    read_only: bool
    observation_hash: str


@dataclass(frozen=True)
class OracleMemoryObservationIntakeBatch:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_memory_hash: str
    observations: tuple[OracleMemoryCertifiedObservation, ...]
    observation_count: int
    unique_observation_count: int
    duplicate_observation_count: int
    batch_state: str
    canonical_order_verified: bool
    deterministic_hashing_verified: bool
    duplicate_detection_verified: bool
    evidence_lineage_verified: bool
    source_certification_verified: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    intake_ready: bool
    candidate_materialization_authorized: bool
    read_only: bool
    batch_hash: str


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
            raise OracleMemoryObservationIntakeInvariantError(
                "OML-027 non-finite number forbidden"
            )
        return value

    raise OracleMemoryObservationIntakeInvariantError(
        "unsupported OML-027 value type: "
        f"{type(value).__module__}.{type(value).__qualname__}"
    )


def _stable_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            _canonical(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _reject(reason: str) -> None:
    raise OracleMemoryObservationIntakeInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-027 invalid {label} length")

    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryObservationIntakeInvariantError(
            f"OML-027 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_certified_observation(
    *,
    observation_kind: str,
    domain_id: str,
    entity_key: str,
    source_key: str,
    observed_at: str,
    effective_at: str,
    payload: Mapping[str, Any],
    evidence_hashes: Sequence[str],
    source_certification_hash: str,
    parent_observation_hashes: Sequence[str] = (),
    confidence: float,
    uncertainty: float,
    contradiction_count: int = 0,
) -> OracleMemoryCertifiedObservation:
    if observation_kind not in ALLOWED_OBSERVATION_KINDS:
        _reject("OML-027 observation kind not allowed")

    if domain_id not in MEMORY_DOMAINS:
        _reject("OML-027 unknown memory domain")

    for label, value in (
        ("entity_key", entity_key),
        ("source_key", source_key),
        ("observed_at", observed_at),
        ("effective_at", effective_at),
    ):
        if not isinstance(value, str) or not value.strip():
            _reject(f"OML-027 {label} must be non-empty")

    if not isinstance(payload, Mapping):
        _reject("OML-027 payload must be a mapping")

    canonical_payload = _canonical(payload)
    evidence = tuple(sorted(set(evidence_hashes)))
    parents = tuple(sorted(set(parent_observation_hashes)))

    if not evidence:
        _reject("OML-027 certified observation requires evidence")

    if len(evidence) != len(tuple(evidence_hashes)):
        _reject("OML-027 duplicate evidence hashes forbidden")

    if len(parents) != len(tuple(parent_observation_hashes)):
        _reject("OML-027 duplicate parent hashes forbidden")

    for value in evidence:
        _require_hash(value, "evidence hash")

    for value in parents:
        _require_hash(value, "parent observation hash")

    _require_hash(source_certification_hash, "source certification hash")

    confidence = float(confidence)
    uncertainty = float(uncertainty)

    if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
        _reject("OML-027 confidence outside [0, 1]")

    if not math.isfinite(uncertainty) or not 0.0 <= uncertainty <= 1.0:
        _reject("OML-027 uncertainty outside [0, 1]")

    if (
        not isinstance(contradiction_count, int)
        or isinstance(contradiction_count, bool)
        or contradiction_count < 0
    ):
        _reject("OML-027 contradiction count invalid")

    identity = {
        "observation_kind": observation_kind,
        "domain_id": domain_id,
        "entity_key": entity_key.strip(),
        "source_key": source_key.strip(),
        "observed_at": observed_at.strip(),
        "effective_at": effective_at.strip(),
        "payload": canonical_payload,
        "evidence_hashes": evidence,
        "parent_observation_hashes": parents,
        "source_certification_hash": source_certification_hash,
    }

    observation_id = _stable_hash(identity)

    body = {
        "observation_id": observation_id,
        "observation_kind": observation_kind,
        "domain_id": domain_id,
        "entity_key": entity_key.strip(),
        "source_key": source_key.strip(),
        "observed_at": observed_at.strip(),
        "effective_at": effective_at.strip(),
        "payload": canonical_payload,
        "evidence_hashes": evidence,
        "parent_observation_hashes": parents,
        "confidence": confidence,
        "uncertainty": uncertainty,
        "contradiction_count": contradiction_count,
        "source_certification_hash": source_certification_hash,
        "observation_state": OBSERVATION_STATE_CERTIFIED_INTAKE_ONLY,
        "deterministic_identity_verified": True,
        "canonical_payload_verified": True,
        "evidence_lineage_verified": True,
        "parent_lineage_verified": True,
        "persistence_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "read_only": True,
    }

    observation = OracleMemoryCertifiedObservation(
        **body,
        observation_hash=_stable_hash(body),
    )

    verify_oracle_memory_certified_observation(observation)
    return observation


def verify_oracle_memory_certified_observation(
    observation: OracleMemoryCertifiedObservation,
) -> bool:
    body = asdict(observation)
    supplied = body.pop("observation_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-027 observation hash mismatch")

    for value, label in (
        (observation.observation_id, "observation id"),
        (observation.source_certification_hash, "source certification hash"),
        (observation.observation_hash, "observation hash"),
    ):
        _require_hash(value, label)

    if observation.observation_kind not in ALLOWED_OBSERVATION_KINDS:
        _reject("OML-027 observation kind invalid")

    if observation.domain_id not in MEMORY_DOMAINS:
        _reject("OML-027 observation domain invalid")

    if observation.observation_state != (
        OBSERVATION_STATE_CERTIFIED_INTAKE_ONLY
    ):
        _reject("OML-027 observation state invalid")

    if not observation.evidence_hashes:
        _reject("OML-027 evidence lineage missing")

    for value in (
        *observation.evidence_hashes,
        *observation.parent_observation_hashes,
    ):
        _require_hash(value, "observation lineage hash")

    if not 0.0 <= observation.confidence <= 1.0:
        _reject("OML-027 observation confidence invalid")

    if not 0.0 <= observation.uncertainty <= 1.0:
        _reject("OML-027 observation uncertainty invalid")

    if observation.contradiction_count < 0:
        _reject("OML-027 observation contradiction count invalid")

    required_true = (
        observation.deterministic_identity_verified,
        observation.canonical_payload_verified,
        observation.evidence_lineage_verified,
        observation.parent_lineage_verified,
        observation.read_only,
    )

    if not all(required_true):
        _reject("OML-027 observation guarantee missing")

    forbidden = (
        observation.persistence_authorized,
        observation.learning_update_authorized,
        observation.runtime_activation_authorized,
        observation.publication_authorized,
        observation.action_authorization_enabled,
        observation.qseries_execution_authorized,
    )

    if any(forbidden):
        _reject("OML-027 forbidden observation capability enabled")

    return True


def build_oracle_memory_observation_intake_batch(
    *,
    cross_market_memory: OracleMemoryCrossMarketDependencyMemory,
    observations: Sequence[OracleMemoryCertifiedObservation],
) -> OracleMemoryObservationIntakeBatch:
    verify_oracle_memory_cross_market_dependency_memory(
        cross_market_memory
    )

    if cross_market_memory.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-027 upstream schema mismatch")

    if cross_market_memory.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-027 upstream engine mismatch")

    if not cross_market_memory.memory_ready:
        _reject("OML-027 upstream memory not ready")

    if not cross_market_memory.next_certification_authorized:
        _reject("OML-027 upstream continuation not authorized")

    if not cross_market_memory.read_only:
        _reject("OML-027 upstream memory not read-only")

    ordered = tuple(
        sorted(
            observations,
            key=lambda item: (
                MEMORY_DOMAINS.index(item.domain_id),
                item.observed_at,
                item.entity_key,
                item.observation_id,
            ),
        )
    )

    for observation in ordered:
        verify_oracle_memory_certified_observation(observation)

    seen: set[str] = set()
    duplicate_count = 0

    for observation in ordered:
        if observation.observation_hash in seen:
            duplicate_count += 1
        else:
            seen.add(observation.observation_hash)

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": cross_market_memory.schema_version,
        "upstream_engine_id": cross_market_memory.engine_id,
        "upstream_memory_hash": cross_market_memory.memory_hash,
        "observations": ordered,
        "observation_count": len(ordered),
        "unique_observation_count": len(seen),
        "duplicate_observation_count": duplicate_count,
        "batch_state": BATCH_STATE_CONTRACT_ONLY,
        "canonical_order_verified": True,
        "deterministic_hashing_verified": True,
        "duplicate_detection_verified": True,
        "evidence_lineage_verified": True,
        "source_certification_verified": True,
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "intake_ready": True,
        "candidate_materialization_authorized": False,
        "read_only": True,
    }

    batch = OracleMemoryObservationIntakeBatch(
        **body,
        batch_hash=_stable_hash(body),
    )

    verify_oracle_memory_observation_intake_batch(batch)
    return batch


def verify_oracle_memory_observation_intake_batch(
    batch: OracleMemoryObservationIntakeBatch,
) -> bool:
    body = asdict(batch)
    supplied = body.pop("batch_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-027 batch hash mismatch")

    if batch.schema_version != SCHEMA_VERSION:
        _reject("OML-027 schema mismatch")

    if batch.engine_id != ENGINE_ID:
        _reject("OML-027 engine mismatch")

    if batch.policy_id != POLICY_ID:
        _reject("OML-027 policy mismatch")

    if batch.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-027 subsystem mismatch")

    if batch.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-027 upstream schema lineage mismatch")

    if batch.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-027 upstream engine lineage mismatch")

    if batch.observation_count != len(batch.observations):
        _reject("OML-027 observation count mismatch")

    if (
        batch.unique_observation_count
        + batch.duplicate_observation_count
        != batch.observation_count
    ):
        _reject("OML-027 duplicate reconciliation mismatch")

    for observation in batch.observations:
        verify_oracle_memory_certified_observation(observation)

    if batch.batch_state != BATCH_STATE_CONTRACT_ONLY:
        _reject("OML-027 batch state invalid")

    required_true = (
        batch.canonical_order_verified,
        batch.deterministic_hashing_verified,
        batch.duplicate_detection_verified,
        batch.evidence_lineage_verified,
        batch.source_certification_verified,
        batch.intake_ready,
        batch.read_only,
    )

    if not all(required_true):
        _reject("OML-027 batch guarantee missing")

    forbidden = (
        batch.persistence_enabled,
        batch.learning_updates_enabled,
        batch.runtime_activation_enabled,
        batch.publication_enabled,
        batch.action_authorization_enabled,
        batch.qseries_execution_enabled,
        batch.candidate_materialization_authorized,
    )

    if any(forbidden):
        _reject("OML-027 forbidden batch capability enabled")

    return True
"""

TEST_SOURCE = r"""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_observation_intake_contract import (
    OBSERVATION_KIND_REAL_WORLD,
    OracleMemoryObservationIntakeInvariantError,
    build_oracle_memory_certified_observation,
    build_oracle_memory_observation_intake_batch,
    verify_oracle_memory_observation_intake_batch,
)
from qseries_v2.oracle_memory.oracle_memory_cross_market_dependency_memory import (
    build_oracle_memory_cross_market_dependency_memory,
)


def load_module(path: Path, name: str):
    specification = importlib.util.spec_from_file_location(name, path)

    if specification is None or specification.loader is None:
        raise RuntimeError(f"unable to load fixture: {path}")

    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def expect_rejection(callable_object, label: str) -> None:
    try:
        callable_object()
    except OracleMemoryObservationIntakeInvariantError:
        return

    raise AssertionError(f"tampered OML-027 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-027 TEST")
    print(" CERTIFIED OBSERVATION INTAKE CONTRACT")
    print("=" * 48)

    root = Path(__file__).resolve().parent

    fixture = load_module(
        root / "test_oml_026_oracle_memory_cross_market_dependency_memory.py",
        "oml_026_fixture_for_oml_027",
    )

    chain_memory, _ = fixture.build_chain_memory(root)

    cross_market_memory = build_oracle_memory_cross_market_dependency_memory(
        causal_chain_memory=chain_memory,
        dependencies=(),
    )

    observation = build_oracle_memory_certified_observation(
        observation_kind=OBSERVATION_KIND_REAL_WORLD,
        domain_id=(
            "market_behavior_memory"
            if "market_behavior_memory"
            in fixture.__dict__.get("MEMORY_DOMAINS", ())
            else __import__(
                "qseries_v2.oracle_memory."
                "oracle_memory_continuous_intelligence_learner_foundation",
                fromlist=["MEMORY_DOMAINS"],
            ).MEMORY_DOMAINS[0]
        ),
        entity_key="Bitcoin",
        source_key="oracle-live-shadow",
        observed_at="2026-08-02T15:00:00-05:00",
        effective_at="2026-08-02T15:00:00-05:00",
        payload={
            "observation": (
                "Real-world liquidity conditions changed before "
                "the financial-market reaction."
            ),
            "observation_type": "liquidity_shift",
            "market": "bitcoin",
        },
        evidence_hashes=("1" * 64, "2" * 64),
        source_certification_hash="3" * 64,
        confidence=0.81,
        uncertainty=0.19,
        contradiction_count=0,
    )

    batch = build_oracle_memory_observation_intake_batch(
        cross_market_memory=cross_market_memory,
        observations=(observation, observation),
    )

    assert batch.schema_version == "OML-027"
    assert batch.engine_id == "OML-027"
    assert batch.upstream_schema_version == "OML-026"
    assert batch.upstream_engine_id == "OML-026"
    assert batch.observation_count == 2
    assert batch.unique_observation_count == 1
    assert batch.duplicate_observation_count == 1
    assert batch.canonical_order_verified
    assert batch.deterministic_hashing_verified
    assert batch.duplicate_detection_verified
    assert batch.evidence_lineage_verified
    assert batch.source_certification_verified
    assert not batch.persistence_enabled
    assert not batch.learning_updates_enabled
    assert not batch.runtime_activation_enabled
    assert not batch.publication_enabled
    assert not batch.action_authorization_enabled
    assert not batch.qseries_execution_enabled
    assert batch.intake_ready
    assert not batch.candidate_materialization_authorized
    assert batch.read_only

    replay = build_oracle_memory_observation_intake_batch(
        cross_market_memory=cross_market_memory,
        observations=(observation, observation),
    )

    assert replay == batch
    assert verify_oracle_memory_observation_intake_batch(batch)

    expect_rejection(
        lambda: verify_oracle_memory_observation_intake_batch(
            replace(batch, observation_count=3)
        ),
        "observation count",
    )

    expect_rejection(
        lambda: verify_oracle_memory_observation_intake_batch(
            replace(batch, persistence_enabled=True)
        ),
        "persistence state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_observation_intake_batch(
            replace(batch, candidate_materialization_authorized=True)
        ),
        "candidate materialization boundary",
    )

    expect_rejection(
        lambda: verify_oracle_memory_observation_intake_batch(
            replace(batch, qseries_execution_enabled=True)
        ),
        "Q Series execution state",
    )

    print("[PASS] Certified OML-026 cross-market memory consumed")
    print("[PASS] Real-world observation intake contract created")
    print("[PASS] Observation payload canonicalized")
    print("[PASS] Evidence and source-certification lineage retained")
    print("[PASS] Deterministic observation identity generated")
    print("[PASS] Duplicate observation detected")
    print("[PASS] Candidate materialization remained unauthorized")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Intake batch deterministic across replay")
    print("[PASS] Tampered observation batches rejected")
    print("[DONE] OML-027 CERTIFIED OBSERVATION INTAKE CONTRACT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def write_complete(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def validate_upstream() -> None:
    if not UPSTREAM.is_file() or not UPSTREAM_TEST.is_file():
        raise RuntimeError(
            "Certified OML-026 production or standalone test missing"
        )

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_cross_market_dependency_memory"
    )

    expected = {
        "SCHEMA_VERSION": "OML-026",
        "ENGINE_ID": "OML-026",
        "POLICY_ID": "oracle-memory.cross-market-dependency-memory.v1",
        "UPSTREAM_SCHEMA_VERSION": "OML-025",
        "UPSTREAM_ENGINE_ID": "OML-025",
    }

    for name, value in expected.items():
        actual = getattr(module, name, None)

        if actual != value:
            raise RuntimeError(
                f"Certified OML-026 {name} mismatch: "
                f"expected {value!r}, got {actual!r}"
            )

    required = (
        "OracleMemoryCrossMarketDependencyMemory",
        "build_oracle_memory_cross_market_dependency_memory",
        "verify_oracle_memory_cross_market_dependency_memory",
    )

    missing = [name for name in required if not hasattr(module, name)]

    if missing:
        raise RuntimeError(
            "Certified OML-026 missing required symbols: "
            + ", ".join(missing)
        )


def main() -> int:
    print("=" * 48)
    print(" OML-027 FOR-SURE INSTALLER")
    print(" CERTIFIED OBSERVATION INTAKE CONTRACT")
    print("=" * 48)
    print("[BOOT] Revision: REPOSITORY_ALIGNED_OBSERVATION_BRIDGE")

    try:
        validate_upstream()
        print("[OK] Actual OML-026 imported and structurally verified")

        upstream_run = subprocess.run(
            [sys.executable, str(UPSTREAM_TEST)],
            cwd=ROOT,
            check=False,
        )

        if upstream_run.returncode:
            raise RuntimeError(
                "OML-026 certification failed with exit code "
                f"{upstream_run.returncode}"
            )

        production_before = UPSTREAM.read_bytes()
        test_before = UPSTREAM_TEST.read_bytes()

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_memory_certified_observation_intake_contract "
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
                "OML-027 test failed with exit code "
                f"{completed.returncode}"
            )

        if UPSTREAM.read_bytes() != production_before:
            raise RuntimeError("Certified OML-026 production changed")

        if UPSTREAM_TEST.read_bytes() != test_before:
            raise RuntimeError("Certified OML-026 standalone test changed")

        print("[PASS] Certified OML-026 production unchanged")
        print("[PASS] Certified OML-026 standalone test unchanged")
        print("[PASS] OML-027 observation intake contract installed")
        print("[PASS] OML-027 standalone deterministic test installed")
        print("[PASS] Real-world observation envelope installed")
        print("[PASS] Source-certification lineage installed")
        print("[PASS] Duplicate observation detection installed")
        print("[PASS] Candidate materialization remained disabled")
        print("[PASS] Persistence remained disabled")
        print("[PASS] Continuous learning remained disabled")
        print("[PASS] Publication remained disabled")
        print("[PASS] Action authorization remained disabled")
        print("[PASS] Q Series execution remained disabled")
        print(f"[PASS] Repository located: {ROOT}")
        print(
            "[DONE] OML-027 CERTIFIED OBSERVATION "
            "INTAKE CONTRACT INSTALLED"
        )
        return 0

    except (RuntimeError, SyntaxError, ImportError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
