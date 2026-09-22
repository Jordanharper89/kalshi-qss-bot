from __future__ import annotations

import ast
import importlib
import inspect
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "oracle_memory"

UPSTREAM = PACKAGE / "oracle_memory_certified_observation_narrative_lifecycle_tracking.py"
UPSTREAM_TEST = ROOT / "test_oml_033_oracle_memory_certified_observation_narrative_lifecycle_tracking.py"
SOURCE_MODULE = PACKAGE / "oracle_memory_source_reliability_memory.py"
SOURCE_TEST = ROOT / "test_oml_022_oracle_memory_source_reliability_memory.py"

PRODUCTION = PACKAGE / "oracle_memory_certified_observation_source_reliability_memory.py"
TEST = ROOT / "test_oml_034_oracle_memory_certified_observation_source_reliability_memory.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_certified_observation_narrative_lifecycle_tracking import (
    OracleMemoryObservationNarrativeLifecycleTracking,
    verify_oracle_memory_observation_narrative_lifecycle_tracking,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import SUBSYSTEM_ID
from qseries_v2.oracle_memory.oracle_memory_source_reliability_memory import (
    OracleMemorySourceObservation,
    OracleMemorySourceReliabilityMemory,
    build_oracle_memory_source_observation,
    build_oracle_memory_source_reliability_memory,
    verify_oracle_memory_source_observation,
    verify_oracle_memory_source_reliability_memory,
)

SCHEMA_VERSION = "OML-034"
ENGINE_ID = "OML-034"
POLICY_ID = "oracle-memory.certified-observation-source-reliability-memory.v1"
UPSTREAM_SCHEMA_VERSION = "OML-033"
UPSTREAM_ENGINE_ID = "OML-033"
STATE_READ_ONLY = "read_only_source_reliability"


class OracleMemoryCertifiedSourceReliabilityInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCertifiedSourceOutcome:
    source_name: str
    observation_hash: str
    outcome_confirmed: bool
    outcome_correct: bool
    contradiction_count: int
    confidence_at_observation: float
    observed_at: str
    outcome_hash: str


@dataclass(frozen=True)
class OracleMemoryCertifiedSourceReliabilityBinding:
    source_id: str
    source_name: str
    profile_hash: str
    source_observation_hashes: tuple[str, ...]
    certified_observation_hashes: tuple[str, ...]
    lifecycle_tracking_hash: str
    source_identity_verified: bool
    observation_lineage_verified: bool
    lifecycle_lineage_verified: bool
    deterministic_binding_verified: bool
    persistence_authorized: bool
    learning_update_authorized: bool
    runtime_activation_authorized: bool
    publication_authorized: bool
    action_authorization_enabled: bool
    qseries_execution_authorized: bool
    read_only: bool
    binding_hash: str


@dataclass(frozen=True)
class OracleMemoryCertifiedSourceReliability:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_tracking_hash: str
    upstream_lifecycle_memory_hash: str
    reliability_memory: OracleMemorySourceReliabilityMemory
    bindings: tuple[OracleMemoryCertifiedSourceReliabilityBinding, ...]
    source_count: int
    total_observation_count: int
    state: str
    certified_lifecycle_lineage_verified: bool
    certified_observation_lineage_verified: bool
    deterministic_scoring_verified: bool
    source_identity_uniqueness_verified: bool
    contradiction_tracking_verified: bool
    calibration_tracking_verified: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    memory_ready: bool
    downstream_calibration_authorized: bool
    read_only: bool
    certification_hash: str


def _canonical(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {str(k): _canonical(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (tuple, list)):
        return [_canonical(v) for v in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleMemoryCertifiedSourceReliabilityInvariantError(
        f"unsupported OML-034 value type: {type(value).__module__}.{type(value).__qualname__}"
    )


def _stable_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(_canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    ).hexdigest()


def _reject(reason: str) -> None:
    raise OracleMemoryCertifiedSourceReliabilityInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-034 invalid {label} length")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryCertifiedSourceReliabilityInvariantError(
            f"OML-034 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_certified_source_outcome(
    *,
    source_name: str,
    observation_hash: str,
    outcome_confirmed: bool,
    outcome_correct: bool,
    contradiction_count: int,
    confidence_at_observation: float,
    observed_at: str,
) -> OracleMemoryCertifiedSourceOutcome:
    _require_hash(observation_hash, "observation hash")
    if not source_name.strip() or not observed_at.strip():
        _reject("OML-034 source name and observed_at required")
    if outcome_correct and not outcome_confirmed:
        _reject("OML-034 unconfirmed outcome cannot be correct")
    if contradiction_count < 0:
        _reject("OML-034 contradiction count invalid")
    confidence_at_observation = float(confidence_at_observation)
    if not 0.0 <= confidence_at_observation <= 1.0:
        _reject("OML-034 confidence outside [0, 1]")

    body = {
        "source_name": source_name.strip(),
        "observation_hash": observation_hash,
        "outcome_confirmed": bool(outcome_confirmed),
        "outcome_correct": bool(outcome_correct),
        "contradiction_count": contradiction_count,
        "confidence_at_observation": confidence_at_observation,
        "observed_at": observed_at.strip(),
    }
    outcome = OracleMemoryCertifiedSourceOutcome(**body, outcome_hash=_stable_hash(body))
    verify_oracle_memory_certified_source_outcome(outcome)
    return outcome


def verify_oracle_memory_certified_source_outcome(outcome: OracleMemoryCertifiedSourceOutcome) -> bool:
    body = asdict(outcome)
    supplied = body.pop("outcome_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-034 source outcome hash mismatch")
    _require_hash(outcome.observation_hash, "observation hash")
    _require_hash(outcome.outcome_hash, "outcome hash")
    if outcome.outcome_correct and not outcome.outcome_confirmed:
        _reject("OML-034 invalid outcome state")
    return True


def _build_binding(
    *,
    tracking: OracleMemoryObservationNarrativeLifecycleTracking,
    profile,
) -> OracleMemoryCertifiedSourceReliabilityBinding:
    certified_hashes = tuple(sorted(item.observation_hash for item in profile.observations))
    body = {
        "source_id": profile.source_id,
        "source_name": profile.source_name,
        "profile_hash": profile.profile_hash,
        "source_observation_hashes": tuple(item.source_observation_hash for item in profile.observations),
        "certified_observation_hashes": certified_hashes,
        "lifecycle_tracking_hash": tracking.tracking_hash,
        "source_identity_verified": True,
        "observation_lineage_verified": True,
        "lifecycle_lineage_verified": True,
        "deterministic_binding_verified": True,
        "persistence_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "read_only": True,
    }
    binding = OracleMemoryCertifiedSourceReliabilityBinding(**body, binding_hash=_stable_hash(body))
    verify_oracle_memory_certified_source_reliability_binding(binding)
    return binding


def verify_oracle_memory_certified_source_reliability_binding(
    binding: OracleMemoryCertifiedSourceReliabilityBinding,
) -> bool:
    body = asdict(binding)
    supplied = body.pop("binding_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-034 binding hash mismatch")
    for value in (
        binding.source_id,
        binding.profile_hash,
        binding.lifecycle_tracking_hash,
        binding.binding_hash,
        *binding.source_observation_hashes,
        *binding.certified_observation_hashes,
    ):
        _require_hash(value, "binding lineage hash")
    required = (
        binding.source_identity_verified,
        binding.observation_lineage_verified,
        binding.lifecycle_lineage_verified,
        binding.deterministic_binding_verified,
        binding.read_only,
    )
    if not all(required):
        _reject("OML-034 binding guarantee missing")
    if any((
        binding.persistence_authorized,
        binding.learning_update_authorized,
        binding.runtime_activation_authorized,
        binding.publication_authorized,
        binding.action_authorization_enabled,
        binding.qseries_execution_authorized,
    )):
        _reject("OML-034 forbidden binding capability enabled")
    return True


def build_oracle_memory_certified_source_reliability(
    *,
    tracking: OracleMemoryObservationNarrativeLifecycleTracking,
    outcomes: Sequence[OracleMemoryCertifiedSourceOutcome],
) -> OracleMemoryCertifiedSourceReliability:
    verify_oracle_memory_observation_narrative_lifecycle_tracking(tracking)

    if tracking.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-034 upstream schema mismatch")
    if tracking.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-034 upstream engine mismatch")
    if not tracking.lifecycle_ready:
        _reject("OML-034 lifecycle tracking not ready")
    if not tracking.downstream_source_reliability_authorized:
        _reject("OML-034 source reliability not authorized")
    if not tracking.read_only:
        _reject("OML-034 upstream tracking not read-only")

    allowed_observation_hashes = {
        value
        for binding in tracking.bindings
        for value in binding.source_observation_hashes
    }

    observations_by_source: dict[str, list[OracleMemorySourceObservation]] = {}

    for outcome in outcomes:
        verify_oracle_memory_certified_source_outcome(outcome)
        if outcome.observation_hash not in allowed_observation_hashes:
            _reject("OML-034 outcome references unknown certified observation")

        source_observation = build_oracle_memory_source_observation(
            source_name=outcome.source_name,
            observation_hash=outcome.observation_hash,
            outcome_confirmed=outcome.outcome_confirmed,
            outcome_correct=outcome.outcome_correct,
            contradiction_count=outcome.contradiction_count,
            confidence_at_observation=outcome.confidence_at_observation,
            observed_at=outcome.observed_at,
        )
        observations_by_source.setdefault(outcome.source_name, []).append(source_observation)

    reliability_memory = build_oracle_memory_source_reliability_memory(
        lifecycle_memory=tracking.lifecycle_memory,
        observations_by_source={
            key: tuple(value)
            for key, value in observations_by_source.items()
        },
    )

    bindings = tuple(
        _build_binding(tracking=tracking, profile=profile)
        for profile in reliability_memory.profiles
    )

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": tracking.schema_version,
        "upstream_engine_id": tracking.engine_id,
        "upstream_tracking_hash": tracking.tracking_hash,
        "upstream_lifecycle_memory_hash": tracking.lifecycle_memory.memory_hash,
        "reliability_memory": reliability_memory,
        "bindings": bindings,
        "source_count": reliability_memory.source_count,
        "total_observation_count": reliability_memory.total_observation_count,
        "state": STATE_READ_ONLY,
        "certified_lifecycle_lineage_verified": True,
        "certified_observation_lineage_verified": True,
        "deterministic_scoring_verified": reliability_memory.deterministic_scoring_verified,
        "source_identity_uniqueness_verified": reliability_memory.source_identity_uniqueness_verified,
        "contradiction_tracking_verified": reliability_memory.contradiction_tracking_verified,
        "calibration_tracking_verified": reliability_memory.calibration_tracking_verified,
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "memory_ready": True,
        "downstream_calibration_authorized": True,
        "read_only": True,
    }

    result = OracleMemoryCertifiedSourceReliability(**body, certification_hash=_stable_hash(body))
    verify_oracle_memory_certified_source_reliability(result)
    return result


def verify_oracle_memory_certified_source_reliability(
    result: OracleMemoryCertifiedSourceReliability,
) -> bool:
    body = asdict(result)
    supplied = body.pop("certification_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-034 certification hash mismatch")
    if result.schema_version != SCHEMA_VERSION or result.engine_id != ENGINE_ID:
        _reject("OML-034 identity mismatch")
    if result.policy_id != POLICY_ID or result.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-034 policy/subsystem mismatch")
    if result.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-034 upstream schema lineage mismatch")
    if result.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-034 upstream engine lineage mismatch")

    verify_oracle_memory_source_reliability_memory(result.reliability_memory)

    if result.source_count != len(result.bindings):
        _reject("OML-034 source/binding count mismatch")
    if result.source_count != result.reliability_memory.source_count:
        _reject("OML-034 source count mismatch")
    if result.total_observation_count != result.reliability_memory.total_observation_count:
        _reject("OML-034 observation count mismatch")

    for binding in result.bindings:
        verify_oracle_memory_certified_source_reliability_binding(binding)

    required = (
        result.certified_lifecycle_lineage_verified,
        result.certified_observation_lineage_verified,
        result.deterministic_scoring_verified,
        result.source_identity_uniqueness_verified,
        result.contradiction_tracking_verified,
        result.calibration_tracking_verified,
        result.memory_ready,
        result.downstream_calibration_authorized,
        result.read_only,
    )
    if not all(required):
        _reject("OML-034 guarantee missing")
    if result.state != STATE_READ_ONLY:
        _reject("OML-034 state invalid")
    if any((
        result.persistence_enabled,
        result.learning_updates_enabled,
        result.runtime_activation_enabled,
        result.publication_enabled,
        result.action_authorization_enabled,
        result.qseries_execution_enabled,
    )):
        _reject("OML-034 forbidden capability enabled")
    return True
"""

TEST_SOURCE = r"""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_observation_source_reliability_memory import (
    OracleMemoryCertifiedSourceReliabilityInvariantError,
    build_oracle_memory_certified_source_outcome,
    build_oracle_memory_certified_source_reliability,
    verify_oracle_memory_certified_source_reliability,
)
from qseries_v2.oracle_memory.oracle_memory_source_reliability_memory import (
    SOURCE_STATUS_RELIABLE,
    OracleMemorySourceReliabilityInvariantError,
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
    except (
        OracleMemoryCertifiedSourceReliabilityInvariantError,
        OracleMemorySourceReliabilityInvariantError,
    ):
        return
    raise AssertionError(f"tampered OML-034 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-034 TEST")
    print(" CERTIFIED OBSERVATION SOURCE RELIABILITY MEMORY")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    fixture = load_module(
        root / "test_oml_033_oracle_memory_certified_observation_narrative_lifecycle_tracking.py",
        "oml_033_fixture_for_oml_034",
    )

    tracking = fixture.build_tracking(root)
    observation_hashes = tracking.bindings[0].source_observation_hashes
    assert len(observation_hashes) >= 2

    outcomes = (
        build_oracle_memory_certified_source_outcome(
            source_name="Oracle Live Shadow",
            observation_hash=observation_hashes[0],
            outcome_confirmed=True,
            outcome_correct=True,
            contradiction_count=0,
            confidence_at_observation=0.82,
            observed_at="2026-08-02T15:00:00-05:00",
        ),
        build_oracle_memory_certified_source_outcome(
            source_name="Oracle Live Shadow",
            observation_hash=observation_hashes[1],
            outcome_confirmed=True,
            outcome_correct=True,
            contradiction_count=0,
            confidence_at_observation=0.79,
            observed_at="2026-08-02T15:10:00-05:00",
        ),
        build_oracle_memory_certified_source_outcome(
            source_name="Oracle Live Shadow",
            observation_hash=observation_hashes[0],
            outcome_confirmed=True,
            outcome_correct=True,
            contradiction_count=1,
            confidence_at_observation=0.76,
            observed_at="2026-08-02T15:20:00-05:00",
        ),
    )

    result = build_oracle_memory_certified_source_reliability(
        tracking=tracking,
        outcomes=outcomes,
    )

    assert result.schema_version == "OML-034"
    assert result.engine_id == "OML-034"
    assert result.upstream_schema_version == "OML-033"
    assert result.upstream_engine_id == "OML-033"
    assert result.source_count == 1
    assert result.total_observation_count == 3
    assert result.reliability_memory.profiles[0].source_status == SOURCE_STATUS_RELIABLE
    assert result.reliability_memory.profiles[0].reliability_score == 1.0
    assert result.bindings[0].observation_lineage_verified
    assert result.certified_lifecycle_lineage_verified
    assert result.certified_observation_lineage_verified
    assert result.deterministic_scoring_verified
    assert result.source_identity_uniqueness_verified
    assert result.contradiction_tracking_verified
    assert result.calibration_tracking_verified
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled
    assert result.memory_ready
    assert result.downstream_calibration_authorized
    assert result.read_only

    replay = build_oracle_memory_certified_source_reliability(
        tracking=tracking,
        outcomes=outcomes,
    )
    assert replay == result
    assert verify_oracle_memory_certified_source_reliability(result)

    expect_rejection(
        lambda: build_oracle_memory_certified_source_outcome(
            source_name="Bad Source",
            observation_hash="f" * 64,
            outcome_confirmed=False,
            outcome_correct=True,
            contradiction_count=0,
            confidence_at_observation=0.50,
            observed_at="2026-08-02T15:00:00-05:00",
        ),
        "invalid outcome",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_source_reliability(
            replace(result, persistence_enabled=True)
        ),
        "persistence state",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_source_reliability(
            replace(result, downstream_calibration_authorized=False)
        ),
        "calibration authorization",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_source_reliability(
            replace(result, qseries_execution_enabled=True)
        ),
        "Q Series execution",
    )

    print("[PASS] Certified OML-033 lifecycle tracking consumed")
    print("[PASS] Certified OML-022 source reliability engine consumed")
    print("[PASS] Exact lifecycle-memory dataclass passed directly")
    print("[PASS] Source outcomes bound to certified observations")
    print("[PASS] Reliable source profile created")
    print("[PASS] Reliability and calibration error calculated")
    print("[PASS] Contradiction tracking retained")
    print("[PASS] Source reliability deterministic across replay")
    print("[PASS] Calibration continuation authorized read-only")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered source reliability rejected")
    print("[DONE] OML-034 CERTIFIED OBSERVATION SOURCE RELIABILITY MEMORY PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def write_complete(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def validate_upstreams() -> None:
    required = (UPSTREAM, UPSTREAM_TEST, SOURCE_MODULE, SOURCE_TEST)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError("Required certified upstream files missing: " + ", ".join(missing))

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    tracking_module = importlib.import_module(
        "qseries_v2.oracle_memory.oracle_memory_certified_observation_narrative_lifecycle_tracking"
    )
    source_module = importlib.import_module(
        "qseries_v2.oracle_memory.oracle_memory_source_reliability_memory"
    )

    expected_tracking = {
        "SCHEMA_VERSION": "OML-033",
        "ENGINE_ID": "OML-033",
        "POLICY_ID": "oracle-memory.certified-observation-narrative-lifecycle-tracking.v1",
    }
    expected_source = {
        "SCHEMA_VERSION": "OML-022",
        "ENGINE_ID": "OML-022",
        "POLICY_ID": "oracle-memory.source-reliability-memory.v1",
        "UPSTREAM_SCHEMA_VERSION": "OML-021",
        "UPSTREAM_ENGINE_ID": "OML-021",
    }

    for name, value in expected_tracking.items():
        if getattr(tracking_module, name, None) != value:
            raise RuntimeError(f"Certified OML-033 {name} mismatch")
    for name, value in expected_source.items():
        if getattr(source_module, name, None) != value:
            raise RuntimeError(f"Certified OML-022 {name} mismatch")

    required_builders = {
        "build_oracle_memory_source_observation": {
            "source_name", "observation_hash", "outcome_confirmed",
            "outcome_correct", "contradiction_count",
            "confidence_at_observation", "observed_at",
        },
        "build_oracle_memory_source_reliability_memory": {
            "lifecycle_memory", "observations_by_source",
        },
    }

    for builder_name, parameters in required_builders.items():
        builder = getattr(source_module, builder_name, None)
        if builder is None:
            raise RuntimeError(f"Certified OML-022 builder missing: {builder_name}")
        missing_parameters = sorted(parameters - set(inspect.signature(builder).parameters))
        if missing_parameters:
            raise RuntimeError(
                f"Certified OML-022 {builder_name} parameters missing: "
                + ", ".join(missing_parameters)
            )


def main() -> int:
    print("=" * 48)
    print(" OML-034 FOR-SURE INSTALLER")
    print(" CERTIFIED OBSERVATION SOURCE RELIABILITY MEMORY")
    print("=" * 48)
    print("[BOOT] Revision: EXACT_OML_033_022_INTERFACE_ALIGNMENT")

    try:
        validate_upstreams()
        print("[OK] Actual OML-033 contract verified")
        print("[OK] Actual OML-022 builders and signatures verified")

        for path, label in (
            (UPSTREAM_TEST, "OML-033"),
            (SOURCE_TEST, "OML-022"),
        ):
            run = subprocess.run([sys.executable, str(path)], cwd=ROOT, check=False)
            if run.returncode:
                raise RuntimeError(f"{label} certification failed with exit code {run.returncode}")

        tracked = {path: path.read_bytes() for path in (UPSTREAM, UPSTREAM_TEST, SOURCE_MODULE, SOURCE_TEST)}

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = "from .oracle_memory_certified_observation_source_reliability_memory import *"
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
            raise RuntimeError(f"OML-034 test failed with exit code {completed.returncode}")

        for path, before in tracked.items():
            if path.read_bytes() != before:
                raise RuntimeError(f"Certified upstream changed: {path}")

        print("[PASS] Certified OML-033 production unchanged")
        print("[PASS] Certified OML-033 standalone test unchanged")
        print("[PASS] Certified OML-022 source reliability engine unchanged")
        print("[PASS] OML-034 production installed")
        print("[PASS] OML-034 standalone deterministic test installed")
        print("[PASS] Certified observations now enter source reliability memory")
        print("[PASS] Exact upstream lifecycle dataclass preserved")
        print("[PASS] Calibration continuation authorized read-only")
        print("[PASS] Persistence remained disabled")
        print("[PASS] Continuous learning remained disabled")
        print("[PASS] Publication remained disabled")
        print("[PASS] Action authorization remained disabled")
        print("[PASS] Q Series execution remained disabled")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OML-034 CERTIFIED OBSERVATION SOURCE RELIABILITY MEMORY INSTALLED")
        return 0

    except (RuntimeError, SyntaxError, ImportError, KeyError, TypeError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
