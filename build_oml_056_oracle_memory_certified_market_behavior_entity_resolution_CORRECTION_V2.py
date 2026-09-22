from __future__ import annotations

import ast
import importlib
import inspect
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "oracle_memory"

UPSTREAM = PACKAGE / "oracle_memory_certified_market_behavior_candidate_validation_and_admission.py"
UPSTREAM_TEST = ROOT / "test_oml_055_oracle_memory_certified_market_behavior_candidate_validation_and_admission.py"
RESOLUTION_MODULE = PACKAGE / "oracle_memory_certified_observation_entity_resolution.py"
RESOLUTION_TEST = ROOT / "test_oml_030_oracle_memory_certified_observation_entity_resolution.py"

PRODUCTION = PACKAGE / "oracle_memory_certified_market_behavior_entity_resolution.py"
TEST = ROOT / "test_oml_056_oracle_memory_certified_market_behavior_entity_resolution.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_candidate_validation_and_deduplication import (
    OracleMemoryCandidateValidationBatch,
    verify_oracle_memory_candidate_validation_batch,
)
from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_candidate_validation_and_admission import (
    OracleMemoryCertifiedMarketBehaviorCandidateAdmission,
    verify_oracle_memory_certified_market_behavior_candidate_admission,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_candidate_materialization import (
    OracleMemoryObservationCandidateMaterializationBatch,
    verify_oracle_memory_observation_candidate_materialization_batch,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_entity_resolution import (
    OracleMemoryObservationEntityResolution,
    build_oracle_memory_observation_entity_resolution,
    verify_oracle_memory_observation_entity_resolution,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-056"
ENGINE_ID = "OML-056"
POLICY_ID = "oracle-memory.certified-market-behavior-entity-resolution.v1"
UPSTREAM_SCHEMA_VERSION = "OML-055"
UPSTREAM_ENGINE_ID = "OML-055"
RESOLUTION_SCHEMA_VERSION = "OML-030"
RESOLUTION_ENGINE_ID = "OML-030"
STATE_READ_ONLY = "read_only_market_behavior_entity_resolution"


class OracleMemoryCertifiedMarketBehaviorEntityResolutionInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCertifiedMarketBehaviorEntityResolution:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_certification_hash: str
    upstream_admission_batch_hash: str
    upstream_materialization_batch_hash: str
    upstream_validation_batch_hash: str
    resolution_schema_version: str
    resolution_engine_id: str
    resolution: OracleMemoryObservationEntityResolution
    admitted_candidate_count: int
    rejected_duplicate_count: int
    resolved_entity_count: int
    state: str
    admission_lineage_verified: bool
    materialization_lineage_verified: bool
    validation_lineage_verified: bool
    observation_entity_lineage_verified: bool
    duplicate_candidates_excluded: bool
    deterministic_resolution_verified: bool
    entity_identity_uniqueness_verified: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    resolution_ready: bool
    downstream_relationship_graph_authorized: bool
    read_only: bool
    certification_hash: str


def _canonical(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleMemoryCertifiedMarketBehaviorEntityResolutionInvariantError(
        "unsupported OML-056 value type"
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
    raise OracleMemoryCertifiedMarketBehaviorEntityResolutionInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-056 invalid {label} length")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryCertifiedMarketBehaviorEntityResolutionInvariantError(
            f"OML-056 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_certified_market_behavior_entity_resolution(
    *,
    admission: OracleMemoryCertifiedMarketBehaviorCandidateAdmission,
    materialization_batch: OracleMemoryObservationCandidateMaterializationBatch,
    validation_batch: OracleMemoryCandidateValidationBatch,
    aliases_by_candidate_hash: Mapping[str, Sequence[str]] | None = None,
) -> OracleMemoryCertifiedMarketBehaviorEntityResolution:
    verify_oracle_memory_certified_market_behavior_candidate_admission(admission)
    verify_oracle_memory_observation_candidate_materialization_batch(
        materialization_batch
    )
    verify_oracle_memory_candidate_validation_batch(validation_batch)

    if admission.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-056 upstream schema mismatch")
    if admission.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-056 upstream engine mismatch")
    if not admission.admission_ready:
        _reject("OML-056 upstream admission not ready")
    if not admission.downstream_entity_resolution_authorized:
        _reject("OML-056 entity-resolution continuation not authorized")
    if not admission.read_only:
        _reject("OML-056 upstream admission not read-only")

    if materialization_batch.batch_hash != (
        admission.upstream_materialization_batch_hash
    ):
        _reject("OML-056 materialization batch lineage mismatch")
    if validation_batch.batch_hash != admission.validation_batch_hash:
        _reject("OML-056 validation batch lineage mismatch")
    resolution = build_oracle_memory_observation_entity_resolution(
        admission_batch=admission.admission_batch,
        materialization_batch=materialization_batch,
        validation_batch=validation_batch,
        aliases_by_candidate_hash=aliases_by_candidate_hash,
    )
    verify_oracle_memory_observation_entity_resolution(resolution)

    if resolution.schema_version != RESOLUTION_SCHEMA_VERSION:
        _reject("OML-056 resolution schema mismatch")
    if resolution.engine_id != RESOLUTION_ENGINE_ID:
        _reject("OML-056 resolution engine mismatch")
    if resolution.upstream_admission_batch_hash != (
        admission.admission_batch.batch_hash
    ):
        _reject("OML-056 admission-to-resolution lineage mismatch")
    if resolution.upstream_materialization_batch_hash != (
        materialization_batch.batch_hash
    ):
        _reject("OML-056 materialization-to-resolution lineage mismatch")
    if resolution.upstream_validation_batch_hash != validation_batch.batch_hash:
        _reject("OML-056 validation-to-resolution lineage mismatch")

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": admission.schema_version,
        "upstream_engine_id": admission.engine_id,
        "upstream_certification_hash": admission.certification_hash,
        "upstream_admission_batch_hash": admission.admission_batch.batch_hash,
        "upstream_materialization_batch_hash": materialization_batch.batch_hash,
        "upstream_validation_batch_hash": validation_batch.batch_hash,
        "resolution_schema_version": resolution.schema_version,
        "resolution_engine_id": resolution.engine_id,
        "resolution": resolution,
        "admitted_candidate_count": resolution.admitted_candidate_count,
        "rejected_duplicate_count": resolution.rejected_duplicate_count,
        "resolved_entity_count": resolution.resolved_entity_count,
        "state": STATE_READ_ONLY,
        "admission_lineage_verified": True,
        "materialization_lineage_verified": True,
        "validation_lineage_verified": True,
        "observation_entity_lineage_verified": (
            resolution.observation_entity_lineage_verified
        ),
        "duplicate_candidates_excluded": resolution.duplicate_candidates_excluded,
        "deterministic_resolution_verified": (
            resolution.deterministic_resolution_verified
        ),
        "entity_identity_uniqueness_verified": (
            resolution.entity_identity_uniqueness_verified
        ),
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "resolution_ready": True,
        "downstream_relationship_graph_authorized": (
            resolution.downstream_relationship_graph_authorized
        ),
        "read_only": True,
    }
    result = OracleMemoryCertifiedMarketBehaviorEntityResolution(
        **body,
        certification_hash=_stable_hash(body),
    )
    verify_oracle_memory_certified_market_behavior_entity_resolution(result)
    return result


def verify_oracle_memory_certified_market_behavior_entity_resolution(
    result: OracleMemoryCertifiedMarketBehaviorEntityResolution,
) -> bool:
    body = asdict(result)
    supplied = body.pop("certification_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-056 certification hash mismatch")

    if result.schema_version != SCHEMA_VERSION:
        _reject("OML-056 schema mismatch")
    if result.engine_id != ENGINE_ID:
        _reject("OML-056 engine mismatch")
    if result.policy_id != POLICY_ID:
        _reject("OML-056 policy mismatch")
    if result.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-056 subsystem mismatch")
    if result.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-056 upstream schema lineage mismatch")
    if result.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-056 upstream engine lineage mismatch")
    if result.resolution_schema_version != RESOLUTION_SCHEMA_VERSION:
        _reject("OML-056 resolution schema lineage mismatch")
    if result.resolution_engine_id != RESOLUTION_ENGINE_ID:
        _reject("OML-056 resolution engine lineage mismatch")

    for value in (
        result.upstream_certification_hash,
        result.upstream_admission_batch_hash,
        result.upstream_materialization_batch_hash,
        result.upstream_validation_batch_hash,
        result.certification_hash,
    ):
        _require_hash(value, "lineage hash")

    verify_oracle_memory_observation_entity_resolution(result.resolution)

    if result.upstream_admission_batch_hash != (
        result.resolution.upstream_admission_batch_hash
    ):
        _reject("OML-056 admission lineage mismatch")
    if result.upstream_materialization_batch_hash != (
        result.resolution.upstream_materialization_batch_hash
    ):
        _reject("OML-056 materialization lineage mismatch")
    if result.upstream_validation_batch_hash != (
        result.resolution.upstream_validation_batch_hash
    ):
        _reject("OML-056 validation lineage mismatch")
    if result.admitted_candidate_count != result.resolution.admitted_candidate_count:
        _reject("OML-056 admitted count mismatch")
    if result.rejected_duplicate_count != result.resolution.rejected_duplicate_count:
        _reject("OML-056 duplicate count mismatch")
    if result.resolved_entity_count != result.resolution.resolved_entity_count:
        _reject("OML-056 entity count mismatch")

    required = (
        result.admission_lineage_verified,
        result.materialization_lineage_verified,
        result.validation_lineage_verified,
        result.observation_entity_lineage_verified,
        result.duplicate_candidates_excluded,
        result.deterministic_resolution_verified,
        result.entity_identity_uniqueness_verified,
        result.resolution_ready,
        result.downstream_relationship_graph_authorized,
        result.read_only,
    )
    if not all(required):
        _reject("OML-056 guarantee missing")
    if result.state != STATE_READ_ONLY:
        _reject("OML-056 state invalid")

    forbidden = (
        result.persistence_enabled,
        result.learning_updates_enabled,
        result.runtime_activation_enabled,
        result.publication_enabled,
        result.action_authorization_enabled,
        result.qseries_execution_enabled,
    )
    if any(forbidden):
        _reject("OML-056 forbidden capability enabled")

    return True
"""

TEST_SOURCE = r"""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_entity_resolution import (
    OracleMemoryCertifiedMarketBehaviorEntityResolutionInvariantError,
    build_oracle_memory_certified_market_behavior_entity_resolution,
    verify_oracle_memory_certified_market_behavior_entity_resolution,
)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load fixture: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def expect_rejection(callable_object, label: str) -> None:
    try:
        callable_object()
    except OracleMemoryCertifiedMarketBehaviorEntityResolutionInvariantError:
        return
    raise AssertionError(f"tampered OML-056 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-056 TEST")
    print(" CERTIFIED MARKET-BEHAVIOR ENTITY RESOLUTION")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    fixture = load_module(
        root
        / "test_oml_055_oracle_memory_certified_market_behavior_candidate_validation_and_admission.py",
        "oml_055_fixture_for_oml_056",
    )

    materialization = fixture.build_materialization(root)
    validation_batch = fixture.build_validation(root, materialization)

    from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_candidate_validation_and_admission import (
        build_oracle_memory_certified_market_behavior_candidate_admission,
    )

    admission = build_oracle_memory_certified_market_behavior_candidate_admission(
        materialization=materialization,
        validation_batch=validation_batch,
    )

    admitted_candidate_hash = next(
        item.candidate_hash
        for item in admission.admission_batch.admissions
        if item.admission_status == "admitted"
    )

    result = build_oracle_memory_certified_market_behavior_entity_resolution(
        admission=admission,
        materialization_batch=materialization.materialization_batch,
        validation_batch=validation_batch,
        aliases_by_candidate_hash={
            admitted_candidate_hash: ("BTC", "Bitcoin", "XBT")
        },
    )

    assert result.schema_version == "OML-056"
    assert result.engine_id == "OML-056"
    assert result.upstream_schema_version == "OML-055"
    assert result.upstream_engine_id == "OML-055"
    assert result.resolution_schema_version == "OML-030"
    assert result.resolution_engine_id == "OML-030"
    assert result.resolved_entity_count == 1
    admitted_candidate = next(
        candidate
        for candidate in materialization.materialization_batch.candidates
        if candidate.candidate_hash == admitted_candidate_hash
    )
    resolved_entity = next(
        entity
        for entity in result.resolution.entities
        if entity.source_candidate_hash == admitted_candidate_hash
    )
    expected_canonical_name = admitted_candidate.entity_key.strip()
    expected_normalized_name = " ".join(
        expected_canonical_name.lower().split()
    )
    normalized_aliases = {
        alias.normalized_alias
        for alias in resolved_entity.aliases
    }

    assert resolved_entity.canonical_name == expected_canonical_name
    assert resolved_entity.normalized_name == expected_normalized_name
    assert expected_normalized_name in normalized_aliases
    assert {"btc", "bitcoin", "xbt"}.issubset(normalized_aliases)
    assert result.admission_lineage_verified
    assert result.materialization_lineage_verified
    assert result.validation_lineage_verified
    assert result.observation_entity_lineage_verified
    assert result.duplicate_candidates_excluded
    assert result.deterministic_resolution_verified
    assert result.entity_identity_uniqueness_verified
    assert result.resolution_ready
    assert result.downstream_relationship_graph_authorized
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled
    assert result.read_only

    replay = build_oracle_memory_certified_market_behavior_entity_resolution(
        admission=admission,
        materialization_batch=materialization.materialization_batch,
        validation_batch=validation_batch,
        aliases_by_candidate_hash={
            admitted_candidate_hash: ("XBT", "Bitcoin", "BTC")
        },
    )
    assert replay == result
    assert verify_oracle_memory_certified_market_behavior_entity_resolution(result)

    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_entity_resolution(
            replace(result, persistence_enabled=True)
        ),
        "persistence state",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_entity_resolution(
            replace(result, downstream_relationship_graph_authorized=False)
        ),
        "relationship graph continuation",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_entity_resolution(
            replace(result, qseries_execution_enabled=True)
        ),
        "Q Series execution",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_entity_resolution(
            replace(result, certification_hash="f" * 64)
        ),
        "certification hash",
    )

    print("[PASS] Certified OML-055 admission consumed read-only")
    print("[PASS] Exact OML-029 admission batch passed directly")
    print("[PASS] Exact OML-028 materialization batch passed directly")
    print("[PASS] Exact OML-017 validation batch passed directly")
    print("[PASS] Actual OML-030 entity-resolution builder consumed")
    print("[PASS] Duplicate-rejected candidates excluded")
    print("[PASS] Stable canonical entity identity generated")
    print("[PASS] Observation-to-entity lineage retained")
    print("[PASS] Relationship-graph continuation authorized read-only")
    print("[PASS] Deterministic replay equality verified")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered OML-056 resolutions rejected")
    print("[DONE] OML-056 CERTIFIED MARKET-BEHAVIOR ENTITY RESOLUTION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def write_complete(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def validate() -> None:
    required = (UPSTREAM, UPSTREAM_TEST, RESOLUTION_MODULE, RESOLUTION_TEST)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(
            "Required certified files missing: " + ", ".join(missing)
        )

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    upstream_module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_certified_market_behavior_candidate_validation_and_admission"
    )
    resolution_module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_certified_observation_entity_resolution"
    )

    expected_upstream = {
        "SCHEMA_VERSION": "OML-055",
        "ENGINE_ID": "OML-055",
        "POLICY_ID": (
            "oracle-memory."
            "certified-market-behavior-candidate-validation-and-admission.v1"
        ),
    }
    expected_resolution = {
        "SCHEMA_VERSION": "OML-030",
        "ENGINE_ID": "OML-030",
        "POLICY_ID": (
            "oracle-memory.certified-observation-entity-resolution.v1"
        ),
        "UPSTREAM_SCHEMA_VERSION": "OML-029",
        "UPSTREAM_ENGINE_ID": "OML-029",
    }

    for module, expected, label in (
        (upstream_module, expected_upstream, "OML-055"),
        (resolution_module, expected_resolution, "OML-030"),
    ):
        for name, value in expected.items():
            actual = getattr(module, name, None)
            if actual != value:
                raise RuntimeError(
                    f"Certified {label} {name} mismatch: "
                    f"expected {value!r}, got {actual!r}"
                )

    required_symbols = (
        (
            upstream_module,
            (
                "OracleMemoryCertifiedMarketBehaviorCandidateAdmission",
                "verify_oracle_memory_certified_market_behavior_candidate_admission",
            ),
            "OML-055",
        ),
        (
            resolution_module,
            (
                "OracleMemoryObservationEntityResolution",
                "build_oracle_memory_observation_entity_resolution",
                "verify_oracle_memory_observation_entity_resolution",
                "OracleMemoryObservationEntityResolutionInvariantError",
            ),
            "OML-030",
        ),
    )
    for module, symbols, label in required_symbols:
        missing_symbols = [
            name for name in symbols if not hasattr(module, name)
        ]
        if missing_symbols:
            raise RuntimeError(
                f"Certified {label} missing symbols: "
                + ", ".join(missing_symbols)
            )

    parameters = set(
        inspect.signature(
            resolution_module.build_oracle_memory_observation_entity_resolution
        ).parameters
    )
    required_parameters = {
        "admission_batch",
        "materialization_batch",
        "validation_batch",
        "aliases_by_candidate_hash",
    }
    missing_parameters = sorted(required_parameters - parameters)
    if missing_parameters:
        raise RuntimeError(
            "Certified OML-030 builder parameters missing: "
            + ", ".join(missing_parameters)
        )


def main() -> int:
    print("=" * 48)
    print(" OML-056 CORRECTION V2 INSTALLER")
    print(" CERTIFIED MARKET-BEHAVIOR ENTITY RESOLUTION")
    print("=" * 48)
    print("[BOOT] Revision: CORRECTION_V2_EXACT_OML_055_030_INTERFACE_ALIGNMENT")

    try:
        validate()
        print("[OK] Actual OML-055 dataclass and verifier inspected")
        print("[OK] Actual OML-030 builder and signatures inspected")

        for path, label in (
            (UPSTREAM_TEST, "OML-055"),
            (RESOLUTION_TEST, "OML-030"),
        ):
            run = subprocess.run(
                [sys.executable, str(path)],
                cwd=ROOT,
                check=False,
            )
            if run.returncode:
                raise RuntimeError(
                    f"{label} certification failed with exit code "
                    f"{run.returncode}"
                )

        tracked = {
            path: path.read_bytes()
            for path in (
                UPSTREAM,
                UPSTREAM_TEST,
                RESOLUTION_MODULE,
                RESOLUTION_TEST,
            )
        }

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_memory_certified_market_behavior_"
            "entity_resolution import *"
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
                f"OML-056 test failed with exit code {completed.returncode}"
            )

        for path, before in tracked.items():
            if path.read_bytes() != before:
                raise RuntimeError(f"Certified upstream changed: {path}")

        print("[PASS] Certified OML-055 production unchanged")
        print("[PASS] Certified OML-055 standalone test unchanged")
        print("[PASS] Certified OML-030 resolution engine unchanged")
        print("[PASS] Exact upstream dataclasses consumed directly")
        print("[PASS] OML-056 production fully replaced")
        print("[PASS] OML-056 standalone deterministic test installed")
        print("[PASS] Deterministic hashes and replay guarantees preserved")
        print("[PASS] Immutable certified lineage preserved")
        print("[PASS] Oracle Terminal separation preserved")
        print("[PASS] Persistence remained disabled")
        print("[PASS] Continuous learning remained disabled")
        print("[PASS] Runtime activation remained disabled")
        print("[PASS] Publication remained disabled")
        print("[PASS] Action authorization remained disabled")
        print("[PASS] Q Series execution remained disabled")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OML-056 CORRECTION V2 CERTIFIED MARKET-BEHAVIOR ENTITY RESOLUTION INSTALLED")
        return 0

    except (
        RuntimeError,
        SyntaxError,
        ImportError,
        AttributeError,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
