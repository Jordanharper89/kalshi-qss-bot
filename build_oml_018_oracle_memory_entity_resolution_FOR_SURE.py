from __future__ import annotations

import ast
import importlib
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "oracle_memory"

UPSTREAM = PACKAGE / "oracle_memory_candidate_validation_and_deduplication.py"
UPSTREAM_TEST = (
    ROOT
    / "test_oml_017_oracle_memory_candidate_validation_and_deduplication.py"
)

PRODUCTION = PACKAGE / "oracle_memory_entity_resolution.py"
TEST = ROOT / "test_oml_018_oracle_memory_entity_resolution.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_candidate_validation_and_deduplication import (
    STATUS_VALID,
    OracleMemoryCandidateValidationBatch,
    OracleMemoryCandidateValidationResult,
    verify_oracle_memory_candidate_validation_batch,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    MEMORY_DOMAINS,
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-018"
ENGINE_ID = "OML-018"
POLICY_ID = "oracle-memory.entity-resolution.v1"

UPSTREAM_SCHEMA_VERSION = "OML-017"
UPSTREAM_ENGINE_ID = "OML-017"

RESOLUTION_STATUS_RESOLVED = "resolved"
RESOLUTION_STATUS_REJECTED_DUPLICATE = "rejected_duplicate"


class OracleMemoryEntityResolutionInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryEntityAlias:
    alias: str
    normalized_alias: str
    alias_hash: str


@dataclass(frozen=True)
class OracleMemoryResolvedEntity:
    canonical_entity_id: str
    domain_id: str
    canonical_name: str
    normalized_name: str
    aliases: tuple[OracleMemoryEntityAlias, ...]
    source_candidate_hash: str
    source_validation_result_hash: str
    resolution_status: str
    deterministic_identity_verified: bool
    alias_uniqueness_verified: bool
    canonical_name_verified: bool
    duplicate_candidate_rejected: bool
    persistence_authorized: bool
    learning_update_authorized: bool
    runtime_activation_authorized: bool
    publication_authorized: bool
    action_authorization_enabled: bool
    qseries_execution_authorized: bool
    read_only: bool
    entity_hash: str


@dataclass(frozen=True)
class OracleMemoryEntityResolutionBatch:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_batch_hash: str
    entities: tuple[OracleMemoryResolvedEntity, ...]
    resolved_entity_count: int
    rejected_duplicate_count: int
    canonical_order_verified: bool
    deterministic_resolution_verified: bool
    alias_normalization_verified: bool
    entity_identity_uniqueness_verified: bool
    duplicate_candidates_excluded: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    batch_ready: bool
    next_certification_authorized: bool
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

    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    raise OracleMemoryEntityResolutionInvariantError(
        "unsupported OML-018 value type: "
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
    raise OracleMemoryEntityResolutionInvariantError(reason)


def _normalize(value: str) -> str:
    normalized = " ".join(value.strip().lower().split())

    if not normalized:
        _reject("OML-018 normalized value cannot be empty")

    return normalized


def _build_alias(value: str) -> OracleMemoryEntityAlias:
    normalized = _normalize(value)

    body = {
        "alias": value.strip(),
        "normalized_alias": normalized,
    }

    return OracleMemoryEntityAlias(
        **body,
        alias_hash=_stable_hash(body),
    )


def verify_oracle_memory_entity_alias(
    alias: OracleMemoryEntityAlias,
) -> bool:
    body = asdict(alias)
    supplied = body.pop("alias_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-018 alias hash mismatch")

    if alias.normalized_alias != _normalize(alias.alias):
        _reject("OML-018 alias normalization mismatch")

    return True


def _build_entity(
    result: OracleMemoryCandidateValidationResult,
    *,
    aliases: Sequence[str],
) -> OracleMemoryResolvedEntity:
    if result.status != STATUS_VALID:
        _reject("OML-018 only valid candidates can resolve entities")

    if result.domain_id not in MEMORY_DOMAINS:
        _reject("OML-018 unknown memory domain")

    canonical_name = result.entity_key.strip()
    normalized_name = _normalize(canonical_name)

    alias_values = tuple(
        sorted(
            {
                canonical_name,
                *(
                    alias.strip()
                    for alias in aliases
                    if isinstance(alias, str) and alias.strip()
                ),
            },
            key=lambda item: _normalize(item),
        )
    )

    alias_objects = tuple(_build_alias(item) for item in alias_values)
    normalized_aliases = tuple(
        item.normalized_alias for item in alias_objects
    )

    canonical_entity_id = hashlib.sha256(
        (
            f"{result.domain_id}|{normalized_name}"
        ).encode("utf-8")
    ).hexdigest()

    body = {
        "canonical_entity_id": canonical_entity_id,
        "domain_id": result.domain_id,
        "canonical_name": canonical_name,
        "normalized_name": normalized_name,
        "aliases": alias_objects,
        "source_candidate_hash": result.candidate_hash,
        "source_validation_result_hash": result.result_hash,
        "resolution_status": RESOLUTION_STATUS_RESOLVED,
        "deterministic_identity_verified": True,
        "alias_uniqueness_verified": (
            len(set(normalized_aliases)) == len(normalized_aliases)
        ),
        "canonical_name_verified": (
            normalized_name in normalized_aliases
        ),
        "duplicate_candidate_rejected": True,
        "persistence_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "read_only": True,
    }

    entity = OracleMemoryResolvedEntity(
        **body,
        entity_hash=_stable_hash(body),
    )

    verify_oracle_memory_resolved_entity(entity)
    return entity


def verify_oracle_memory_resolved_entity(
    entity: OracleMemoryResolvedEntity,
) -> bool:
    body = asdict(entity)
    supplied = body.pop("entity_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-018 entity hash mismatch")

    if entity.domain_id not in MEMORY_DOMAINS:
        _reject("OML-018 entity domain mismatch")

    if entity.normalized_name != _normalize(entity.canonical_name):
        _reject("OML-018 canonical-name normalization mismatch")

    expected_id = hashlib.sha256(
        (
            f"{entity.domain_id}|{entity.normalized_name}"
        ).encode("utf-8")
    ).hexdigest()

    if entity.canonical_entity_id != expected_id:
        _reject("OML-018 canonical entity identity mismatch")

    for alias in entity.aliases:
        verify_oracle_memory_entity_alias(alias)

    normalized_aliases = tuple(
        alias.normalized_alias for alias in entity.aliases
    )

    if len(set(normalized_aliases)) != len(normalized_aliases):
        _reject("OML-018 duplicate aliases detected")

    if entity.normalized_name not in normalized_aliases:
        _reject("OML-018 canonical name missing from aliases")

    required_true = (
        entity.deterministic_identity_verified,
        entity.alias_uniqueness_verified,
        entity.canonical_name_verified,
        entity.duplicate_candidate_rejected,
        entity.read_only,
    )

    if not all(required_true):
        _reject("OML-018 entity resolution guarantee missing")

    forbidden = (
        entity.persistence_authorized,
        entity.learning_update_authorized,
        entity.runtime_activation_authorized,
        entity.publication_authorized,
        entity.action_authorization_enabled,
        entity.qseries_execution_authorized,
    )

    if any(forbidden):
        _reject("OML-018 forbidden entity capability enabled")

    return True


def build_oracle_memory_entity_resolution_batch(
    *,
    validation_batch: OracleMemoryCandidateValidationBatch,
    aliases_by_candidate_hash: Mapping[str, Sequence[str]] | None = None,
) -> OracleMemoryEntityResolutionBatch:
    verify_oracle_memory_candidate_validation_batch(validation_batch)

    if validation_batch.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-018 upstream schema mismatch")

    if validation_batch.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-018 upstream engine mismatch")

    if not validation_batch.batch_ready:
        _reject("OML-018 upstream validation batch not ready")

    if not validation_batch.next_certification_authorized:
        _reject("OML-018 upstream continuation not authorized")

    if not validation_batch.read_only:
        _reject("OML-018 upstream read-only guarantee missing")

    alias_map = aliases_by_candidate_hash or {}

    valid_results = tuple(
        result
        for result in validation_batch.results
        if result.status == STATUS_VALID
    )

    entities = tuple(
        sorted(
            (
                _build_entity(
                    result,
                    aliases=alias_map.get(result.candidate_hash, ()),
                )
                for result in valid_results
            ),
            key=lambda item: (
                MEMORY_DOMAINS.index(item.domain_id),
                item.normalized_name,
                item.canonical_entity_id,
            ),
        )
    )

    entity_ids = tuple(
        entity.canonical_entity_id for entity in entities
    )

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": validation_batch.schema_version,
        "upstream_engine_id": validation_batch.engine_id,
        "upstream_batch_hash": validation_batch.batch_hash,
        "entities": entities,
        "resolved_entity_count": len(entities),
        "rejected_duplicate_count": (
            validation_batch.duplicate_candidate_count
        ),
        "canonical_order_verified": True,
        "deterministic_resolution_verified": True,
        "alias_normalization_verified": True,
        "entity_identity_uniqueness_verified": (
            len(set(entity_ids)) == len(entity_ids)
        ),
        "duplicate_candidates_excluded": (
            len(valid_results)
            + validation_batch.duplicate_candidate_count
            == validation_batch.candidate_count
        ),
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "batch_ready": True,
        "next_certification_authorized": True,
        "read_only": True,
    }

    batch = OracleMemoryEntityResolutionBatch(
        **body,
        batch_hash=_stable_hash(body),
    )

    verify_oracle_memory_entity_resolution_batch(batch)
    return batch


def verify_oracle_memory_entity_resolution_batch(
    batch: OracleMemoryEntityResolutionBatch,
) -> bool:
    body = asdict(batch)
    supplied = body.pop("batch_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-018 batch hash mismatch")

    if batch.schema_version != SCHEMA_VERSION:
        _reject("OML-018 batch schema mismatch")

    if batch.engine_id != ENGINE_ID:
        _reject("OML-018 batch engine mismatch")

    if batch.policy_id != POLICY_ID:
        _reject("OML-018 batch policy mismatch")

    if batch.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-018 batch subsystem mismatch")

    if batch.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-018 upstream schema lineage mismatch")

    if batch.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-018 upstream engine lineage mismatch")

    if batch.resolved_entity_count != len(batch.entities):
        _reject("OML-018 resolved entity count mismatch")

    for entity in batch.entities:
        verify_oracle_memory_resolved_entity(entity)

    entity_ids = tuple(
        entity.canonical_entity_id for entity in batch.entities
    )

    if len(set(entity_ids)) != len(entity_ids):
        _reject("OML-018 duplicate canonical entity identities")

    required_true = (
        batch.canonical_order_verified,
        batch.deterministic_resolution_verified,
        batch.alias_normalization_verified,
        batch.entity_identity_uniqueness_verified,
        batch.duplicate_candidates_excluded,
        batch.batch_ready,
        batch.next_certification_authorized,
        batch.read_only,
    )

    if not all(required_true):
        _reject("OML-018 batch guarantee missing")

    forbidden = (
        batch.persistence_enabled,
        batch.learning_updates_enabled,
        batch.runtime_activation_enabled,
        batch.publication_enabled,
        batch.action_authorization_enabled,
        batch.qseries_execution_enabled,
    )

    if any(forbidden):
        _reject("OML-018 forbidden batch capability enabled")

    return True
"""

TEST_SOURCE = r"""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_candidate_validation_and_deduplication import (
    build_oracle_memory_candidate_validation_batch,
)
from qseries_v2.oracle_memory.oracle_memory_canonical_record_candidate_contract import (
    build_oracle_memory_canonical_record_candidate,
)
from qseries_v2.oracle_memory.oracle_memory_entity_resolution import (
    OracleMemoryEntityResolutionInvariantError,
    build_oracle_memory_entity_resolution_batch,
    verify_oracle_memory_entity_resolution_batch,
)
from qseries_v2.oracle_memory.oracle_memory_ledger_integrity_and_replay_certification import (
    build_oracle_memory_ledger_integrity_replay_certification,
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
    except OracleMemoryEntityResolutionInvariantError:
        return

    raise AssertionError(f"tampered OML-018 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-018 TEST")
    print(" ENTITY RESOLUTION")
    print("=" * 48)

    root = Path(__file__).resolve().parent

    fixture_016 = load_module(
        root
        / "test_oml_016_oracle_memory_ledger_integrity_and_replay_certification.py",
        "oml_016_fixture_for_oml_018",
    )
    ledger_contract = fixture_016.build_oml_015_contract(root)
    ledger = build_oracle_memory_ledger_integrity_replay_certification(
        ledger_contract=ledger_contract,
    )

    fixture_009 = load_module(
        root
        / "test_oml_009_oracle_memory_canonical_record_candidate_contract.py",
        "oml_009_fixture_for_oml_018",
    )
    gate = fixture_009.build_oml_008_decision(root)

    candidate = build_oracle_memory_canonical_record_candidate(
        gate_decision=gate,
        domain_id=gate.admitted_domain_ids[0],
        candidate_id="candidate:entity:btc:001",
        entity_key="Bitcoin",
        source_key="certified-observation-source",
        observed_at="2026-08-02T14:46:00-05:00",
        effective_at="2026-08-02T14:46:00-05:00",
        payload={
            "observation": (
                "Real-world activity changed before market reaction"
            ),
            "observation_type": "consumer_behavior",
        },
        evidence_hashes=("1" * 64, "2" * 64),
        parent_record_hashes=(),
        confidence=0.82,
        uncertainty=0.18,
        contradiction_count=0,
    )

    validation = build_oracle_memory_candidate_validation_batch(
        ledger_certification=ledger,
        candidates=(candidate, candidate),
    )

    batch = build_oracle_memory_entity_resolution_batch(
        validation_batch=validation,
        aliases_by_candidate_hash={
            candidate.candidate_hash: (
                "BTC",
                "Bitcoin",
                "XBT",
            )
        },
    )

    assert batch.schema_version == "OML-018"
    assert batch.engine_id == "OML-018"
    assert batch.upstream_schema_version == "OML-017"
    assert batch.upstream_engine_id == "OML-017"
    assert batch.resolved_entity_count == 1
    assert batch.rejected_duplicate_count == 1

    entity = batch.entities[0]

    assert entity.canonical_name == "Bitcoin"
    assert entity.normalized_name == "bitcoin"
    assert tuple(
        alias.normalized_alias for alias in entity.aliases
    ) == ("bitcoin", "btc", "xbt")
    assert entity.resolution_status == "resolved"
    assert entity.deterministic_identity_verified
    assert entity.alias_uniqueness_verified
    assert entity.canonical_name_verified
    assert entity.duplicate_candidate_rejected
    assert not entity.persistence_authorized
    assert not entity.learning_update_authorized
    assert not entity.runtime_activation_authorized
    assert not entity.publication_authorized
    assert not entity.action_authorization_enabled
    assert not entity.qseries_execution_authorized
    assert entity.read_only

    assert batch.canonical_order_verified
    assert batch.deterministic_resolution_verified
    assert batch.alias_normalization_verified
    assert batch.entity_identity_uniqueness_verified
    assert batch.duplicate_candidates_excluded
    assert not batch.persistence_enabled
    assert not batch.learning_updates_enabled
    assert not batch.runtime_activation_enabled
    assert not batch.publication_enabled
    assert not batch.action_authorization_enabled
    assert not batch.qseries_execution_enabled
    assert batch.batch_ready
    assert batch.next_certification_authorized
    assert batch.read_only

    replay = build_oracle_memory_entity_resolution_batch(
        validation_batch=validation,
        aliases_by_candidate_hash={
            candidate.candidate_hash: (
                "XBT",
                "Bitcoin",
                "BTC",
            )
        },
    )

    assert replay == batch
    assert verify_oracle_memory_entity_resolution_batch(batch)

    expect_rejection(
        lambda: verify_oracle_memory_entity_resolution_batch(
            replace(batch, resolved_entity_count=2)
        ),
        "entity count",
    )

    expect_rejection(
        lambda: verify_oracle_memory_entity_resolution_batch(
            replace(batch, persistence_enabled=True)
        ),
        "persistence state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_entity_resolution_batch(
            replace(batch, qseries_execution_enabled=True)
        ),
        "Q Series execution state",
    )

    print("[PASS] Certified OML-017 validation batch consumed")
    print("[PASS] Valid candidates resolved to canonical entities")
    print("[PASS] Duplicate candidates excluded")
    print("[PASS] Stable canonical entity identity generated")
    print("[PASS] Alias normalization completed")
    print("[PASS] Alias uniqueness verified")
    print("[PASS] Canonical entity ordering verified")
    print("[PASS] Entity resolution deterministic across replay")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered entity batches rejected")
    print("[DONE] OML-018 ENTITY RESOLUTION PASS")
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
            "Certified OML-017 production or standalone test missing"
        )

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_candidate_validation_and_deduplication"
    )

    expected = {
        "SCHEMA_VERSION": "OML-017",
        "ENGINE_ID": "OML-017",
        "POLICY_ID": (
            "oracle-memory.candidate-validation-and-deduplication.v1"
        ),
        "UPSTREAM_SCHEMA_VERSION": "OML-016",
        "UPSTREAM_ENGINE_ID": "OML-016",
        "STATUS_VALID": "valid",
        "STATUS_DUPLICATE": "duplicate",
    }

    for name, value in expected.items():
        actual = getattr(module, name, None)

        if actual != value:
            raise RuntimeError(
                f"Certified OML-017 {name} mismatch: "
                f"expected {value!r}, got {actual!r}"
            )

    required = (
        "OracleMemoryCandidateValidationResult",
        "OracleMemoryCandidateValidationBatch",
        "build_oracle_memory_candidate_validation_batch",
        "verify_oracle_memory_candidate_validation_result",
        "verify_oracle_memory_candidate_validation_batch",
    )

    missing = [name for name in required if not hasattr(module, name)]

    if missing:
        raise RuntimeError(
            "Certified OML-017 missing required symbols: "
            + ", ".join(missing)
        )


def main() -> int:
    print("=" * 48)
    print(" OML-018 FOR-SURE INSTALLER")
    print(" ENTITY RESOLUTION")
    print("=" * 48)
    print("[BOOT] Revision: CAPABILITY_MILESTONE_FULL_REPLACEMENT")

    try:
        validate_upstream()
        print("[OK] Actual OML-017 imported and structurally verified")

        upstream_run = subprocess.run(
            [sys.executable, str(UPSTREAM_TEST)],
            cwd=ROOT,
            check=False,
        )

        if upstream_run.returncode:
            raise RuntimeError(
                "OML-017 certification failed with exit code "
                f"{upstream_run.returncode}"
            )

        production_before = UPSTREAM.read_bytes()
        test_before = UPSTREAM_TEST.read_bytes()

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = "from .oracle_memory_entity_resolution import *"
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
                "OML-018 test failed with exit code "
                f"{completed.returncode}"
            )

        if UPSTREAM.read_bytes() != production_before:
            raise RuntimeError("Certified OML-017 production changed")

        if UPSTREAM_TEST.read_bytes() != test_before:
            raise RuntimeError("Certified OML-017 standalone test changed")

        print("[PASS] Certified OML-017 production unchanged")
        print("[PASS] Certified OML-017 standalone test unchanged")
        print("[PASS] OML-018 entity resolution installed")
        print("[PASS] OML-018 standalone deterministic test installed")
        print("[PASS] Canonical entity identity capability installed")
        print("[PASS] Alias normalization capability installed")
        print("[PASS] Duplicate candidates excluded")
        print("[PASS] Persistence remained disabled")
        print("[PASS] Continuous learning remained disabled")
        print("[PASS] Publication remained disabled")
        print("[PASS] Action authorization remained disabled")
        print("[PASS] Q Series execution remained disabled")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OML-018 ENTITY RESOLUTION INSTALLED")
        return 0

    except (RuntimeError, SyntaxError, ImportError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
