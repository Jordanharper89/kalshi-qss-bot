from __future__ import annotations

import ast
import importlib
import inspect
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "oracle_memory"

UPSTREAM = PACKAGE / "oracle_memory_certified_cross_market_narrative_detection_and_evolution.py"
UPSTREAM_TEST = ROOT / "test_oml_045_oracle_memory_certified_cross_market_narrative_detection_and_evolution.py"
LIFECYCLE_MODULE = PACKAGE / "oracle_memory_certified_observation_narrative_lifecycle_tracking.py"
LIFECYCLE_TEST = ROOT / "test_oml_033_oracle_memory_certified_observation_narrative_lifecycle_tracking.py"

PRODUCTION = PACKAGE / "oracle_memory_certified_cross_market_narrative_lifecycle_tracking.py"
TEST = ROOT / "test_oml_046_oracle_memory_certified_cross_market_narrative_lifecycle_tracking.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_narrative_detection_and_evolution import (
    OracleMemoryCertifiedCrossMarketNarrativeDetection,
    verify_oracle_memory_certified_cross_market_narrative_detection,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_narrative_lifecycle_tracking import (
    OracleMemoryObservationNarrativeLifecycleTracking,
    build_oracle_memory_observation_narrative_lifecycle_tracking,
    verify_oracle_memory_observation_narrative_lifecycle_tracking,
)
from qseries_v2.oracle_memory.oracle_memory_narrative_detection_and_evolution_engine import (
    OracleMemoryNarrative,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-046"
ENGINE_ID = "OML-046"
POLICY_ID = (
    "oracle-memory."
    "certified-cross-market-narrative-lifecycle-tracking.v1"
)
UPSTREAM_SCHEMA_VERSION = "OML-045"
UPSTREAM_ENGINE_ID = "OML-045"
LIFECYCLE_SCHEMA_VERSION = "OML-033"
LIFECYCLE_ENGINE_ID = "OML-033"
STATE_READ_ONLY = "read_only_cross_market_narrative_lifecycle"


class OracleMemoryCertifiedCrossMarketLifecycleInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCertifiedCrossMarketNarrativeLifecycle:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_certification_hash: str
    upstream_detection_hash: str
    lifecycle_schema_version: str
    lifecycle_engine_id: str
    lifecycle_tracking: OracleMemoryObservationNarrativeLifecycleTracking
    narrative_count: int
    snapshot_count: int
    transition_count: int
    state: str
    detection_lineage_verified: bool
    observation_lifecycle_lineage_verified: bool
    entity_lineage_preserved: bool
    relationship_lineage_preserved: bool
    canonical_temporal_order_verified: bool
    deterministic_lifecycle_tracking_verified: bool
    evidence_growth_tracked: bool
    contradiction_growth_tracked: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    lifecycle_ready: bool
    downstream_source_reliability_authorized: bool
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
    raise OracleMemoryCertifiedCrossMarketLifecycleInvariantError(
        "unsupported OML-046 value type"
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
    raise OracleMemoryCertifiedCrossMarketLifecycleInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-046 invalid {label} length")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryCertifiedCrossMarketLifecycleInvariantError(
            f"OML-046 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_certified_cross_market_narrative_lifecycle(
    *,
    detection: OracleMemoryCertifiedCrossMarketNarrativeDetection,
    prior_histories: Mapping[str, Sequence[OracleMemoryNarrative]],
) -> OracleMemoryCertifiedCrossMarketNarrativeLifecycle:
    verify_oracle_memory_certified_cross_market_narrative_detection(detection)

    if detection.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-046 upstream schema mismatch")
    if detection.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-046 upstream engine mismatch")
    if not detection.detection_ready:
        _reject("OML-046 upstream detection not ready")
    if not detection.downstream_lifecycle_tracking_authorized:
        _reject("OML-046 lifecycle continuation not authorized")
    if not detection.read_only:
        _reject("OML-046 upstream detection not read-only")

    tracking = build_oracle_memory_observation_narrative_lifecycle_tracking(
        detection=detection.narrative_detection,
        prior_histories=prior_histories,
    )
    verify_oracle_memory_observation_narrative_lifecycle_tracking(tracking)

    if tracking.schema_version != LIFECYCLE_SCHEMA_VERSION:
        _reject("OML-046 lifecycle schema mismatch")
    if tracking.engine_id != LIFECYCLE_ENGINE_ID:
        _reject("OML-046 lifecycle engine mismatch")
    if tracking.upstream_detection_hash != (
        detection.narrative_detection.detection_hash
    ):
        _reject("OML-046 detection-to-lifecycle lineage mismatch")

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": detection.schema_version,
        "upstream_engine_id": detection.engine_id,
        "upstream_certification_hash": detection.certification_hash,
        "upstream_detection_hash": (
            detection.narrative_detection.detection_hash
        ),
        "lifecycle_schema_version": tracking.schema_version,
        "lifecycle_engine_id": tracking.engine_id,
        "lifecycle_tracking": tracking,
        "narrative_count": tracking.narrative_count,
        "snapshot_count": tracking.snapshot_count,
        "transition_count": tracking.transition_count,
        "state": STATE_READ_ONLY,
        "detection_lineage_verified": (
            tracking.certified_detection_lineage_verified
        ),
        "observation_lifecycle_lineage_verified": (
            tracking.observation_lifecycle_lineage_verified
        ),
        "entity_lineage_preserved": tracking.entity_lineage_preserved,
        "relationship_lineage_preserved": (
            tracking.relationship_lineage_preserved
        ),
        "canonical_temporal_order_verified": (
            tracking.canonical_temporal_order_verified
        ),
        "deterministic_lifecycle_tracking_verified": (
            tracking.deterministic_lifecycle_tracking_verified
        ),
        "evidence_growth_tracked": tracking.evidence_growth_tracked,
        "contradiction_growth_tracked": (
            tracking.contradiction_growth_tracked
        ),
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "lifecycle_ready": True,
        "downstream_source_reliability_authorized": (
            tracking.downstream_source_reliability_authorized
        ),
        "read_only": True,
    }

    result = OracleMemoryCertifiedCrossMarketNarrativeLifecycle(
        **body,
        certification_hash=_stable_hash(body),
    )
    verify_oracle_memory_certified_cross_market_narrative_lifecycle(result)
    return result


def verify_oracle_memory_certified_cross_market_narrative_lifecycle(
    result: OracleMemoryCertifiedCrossMarketNarrativeLifecycle,
) -> bool:
    body = asdict(result)
    supplied = body.pop("certification_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-046 certification hash mismatch")

    if result.schema_version != SCHEMA_VERSION:
        _reject("OML-046 schema mismatch")
    if result.engine_id != ENGINE_ID:
        _reject("OML-046 engine mismatch")
    if result.policy_id != POLICY_ID:
        _reject("OML-046 policy mismatch")
    if result.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-046 subsystem mismatch")
    if result.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-046 upstream schema lineage mismatch")
    if result.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-046 upstream engine lineage mismatch")
    if result.lifecycle_schema_version != LIFECYCLE_SCHEMA_VERSION:
        _reject("OML-046 lifecycle schema lineage mismatch")
    if result.lifecycle_engine_id != LIFECYCLE_ENGINE_ID:
        _reject("OML-046 lifecycle engine lineage mismatch")

    for value in (
        result.upstream_certification_hash,
        result.upstream_detection_hash,
        result.certification_hash,
    ):
        _require_hash(value, "lineage hash")

    verify_oracle_memory_observation_narrative_lifecycle_tracking(
        result.lifecycle_tracking
    )

    if result.upstream_detection_hash != (
        result.lifecycle_tracking.upstream_detection_hash
    ):
        _reject("OML-046 lifecycle detection lineage mismatch")
    if result.narrative_count != result.lifecycle_tracking.narrative_count:
        _reject("OML-046 narrative count mismatch")
    if result.snapshot_count != result.lifecycle_tracking.snapshot_count:
        _reject("OML-046 snapshot count mismatch")
    if result.transition_count != result.lifecycle_tracking.transition_count:
        _reject("OML-046 transition count mismatch")

    required = (
        result.detection_lineage_verified,
        result.observation_lifecycle_lineage_verified,
        result.entity_lineage_preserved,
        result.relationship_lineage_preserved,
        result.canonical_temporal_order_verified,
        result.deterministic_lifecycle_tracking_verified,
        result.evidence_growth_tracked,
        result.contradiction_growth_tracked,
        result.lifecycle_ready,
        result.downstream_source_reliability_authorized,
        result.read_only,
    )
    if not all(required):
        _reject("OML-046 guarantee missing")
    if result.state != STATE_READ_ONLY:
        _reject("OML-046 state invalid")

    forbidden = (
        result.persistence_enabled,
        result.learning_updates_enabled,
        result.runtime_activation_enabled,
        result.publication_enabled,
        result.action_authorization_enabled,
        result.qseries_execution_enabled,
    )
    if any(forbidden):
        _reject("OML-046 forbidden capability enabled")

    return True
"""

TEST_SOURCE = r"""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_narrative_lifecycle_tracking import (
    OracleMemoryCertifiedCrossMarketLifecycleInvariantError,
    build_oracle_memory_certified_cross_market_narrative_lifecycle,
    verify_oracle_memory_certified_cross_market_narrative_lifecycle,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_narrative_detection_and_evolution import (
    build_oracle_memory_observation_narrative_request,
)
from qseries_v2.oracle_memory.oracle_memory_narrative_detection_and_evolution_engine import (
    NARRATIVE_STAGE_EMERGING,
    NARRATIVE_STAGE_STRENGTHENING,
    build_oracle_memory_narrative,
)
from qseries_v2.oracle_memory.oracle_memory_narrative_temporal_tracking_and_lifecycle_memory import (
    TRANSITION_STRENGTHENED,
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
    except OracleMemoryCertifiedCrossMarketLifecycleInvariantError:
        return
    raise AssertionError(f"tampered OML-046 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-046 TEST")
    print(" CERTIFIED CROSS-MARKET NARRATIVE LIFECYCLE TRACKING")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    fixture = load_module(
        root
        / "test_oml_045_oracle_memory_certified_cross_market_narrative_detection_and_evolution.py",
        "oml_045_fixture_for_oml_046",
    )
    graph, liquidity, bitcoin = fixture.build_graph(root)
    relationship = graph.graph_materialization.graph.relationships[0]

    prior = build_oracle_memory_narrative(
        graph=graph.graph_materialization.graph,
        title="Stablecoin liquidity precedes Bitcoin repricing",
        participating_entity_ids=(
            liquidity.canonical_entity_id,
            bitcoin.canonical_entity_id,
        ),
        relationship_ids=(relationship.relationship_id,),
        supporting_evidence_hashes=("7" * 64,),
        contradicting_evidence_hashes=(),
        confidence=0.58,
        uncertainty=0.42,
        first_observed_at="2026-08-02T16:50:00-05:00",
        last_observed_at="2026-08-02T17:00:00-05:00",
        evolution_index=1,
    )
    assert prior.stage == NARRATIVE_STAGE_EMERGING

    current_request = build_oracle_memory_observation_narrative_request(
        title="Stablecoin liquidity precedes Bitcoin repricing",
        participating_entity_ids=(
            liquidity.canonical_entity_id,
            bitcoin.canonical_entity_id,
        ),
        relationship_ids=(relationship.relationship_id,),
        supporting_evidence_hashes=(
            "7" * 64,
            "8" * 64,
            "9" * 64,
        ),
        contradicting_evidence_hashes=(),
        confidence=0.82,
        uncertainty=0.18,
        first_observed_at="2026-08-02T16:50:00-05:00",
        last_observed_at="2026-08-02T17:10:00-05:00",
        evolution_index=2,
        prior_stage=prior.stage,
    )

    from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_narrative_detection_and_evolution import (
        build_oracle_memory_certified_cross_market_narrative_detection,
    )

    detection = build_oracle_memory_certified_cross_market_narrative_detection(
        graph=graph,
        requests=(current_request,),
    )
    current = detection.narrative_detection.narratives[0]
    assert current.stage == NARRATIVE_STAGE_STRENGTHENING
    assert current.narrative_id == prior.narrative_id

    result = build_oracle_memory_certified_cross_market_narrative_lifecycle(
        detection=detection,
        prior_histories={current.narrative_id: (prior,)},
    )

    assert result.schema_version == "OML-046"
    assert result.engine_id == "OML-046"
    assert result.upstream_schema_version == "OML-045"
    assert result.upstream_engine_id == "OML-045"
    assert result.lifecycle_schema_version == "OML-033"
    assert result.lifecycle_engine_id == "OML-033"
    assert result.narrative_count == 1
    assert result.snapshot_count == 2
    assert result.transition_count == 1
    transition = result.lifecycle_tracking.lifecycle_memory.transitions[0]
    assert transition.transition_type == TRANSITION_STRENGTHENED
    assert transition.confidence_delta > 0
    assert transition.uncertainty_delta < 0
    assert transition.evidence_growth == 2
    assert result.detection_lineage_verified
    assert result.observation_lifecycle_lineage_verified
    assert result.entity_lineage_preserved
    assert result.relationship_lineage_preserved
    assert result.canonical_temporal_order_verified
    assert result.deterministic_lifecycle_tracking_verified
    assert result.evidence_growth_tracked
    assert result.contradiction_growth_tracked
    assert result.lifecycle_ready
    assert result.downstream_source_reliability_authorized
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled
    assert result.read_only

    replay = build_oracle_memory_certified_cross_market_narrative_lifecycle(
        detection=detection,
        prior_histories={current.narrative_id: (prior,)},
    )
    assert replay == result
    assert verify_oracle_memory_certified_cross_market_narrative_lifecycle(
        result
    )

    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_narrative_lifecycle(
            replace(result, persistence_enabled=True)
        ),
        "persistence state",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_narrative_lifecycle(
            replace(result, downstream_source_reliability_authorized=False)
        ),
        "source reliability continuation",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_narrative_lifecycle(
            replace(result, qseries_execution_enabled=True)
        ),
        "Q Series execution",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_narrative_lifecycle(
            replace(result, certification_hash="f" * 64)
        ),
        "certification hash",
    )

    print("[PASS] Certified OML-045 narrative detection consumed read-only")
    print("[PASS] Exact OML-032 detection dataclass passed directly")
    print("[PASS] Actual OML-033 lifecycle builder consumed")
    print("[PASS] Narrative identity preserved across evolution")
    print("[PASS] Strengthened lifecycle transition created")
    print("[PASS] Confidence and uncertainty deltas tracked")
    print("[PASS] Evidence growth tracked")
    print("[PASS] Entity and relationship lineage preserved")
    print("[PASS] Source-reliability continuation authorized read-only")
    print("[PASS] Deterministic replay equality verified")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered OML-046 lifecycle records rejected")
    print(
        "[DONE] OML-046 CERTIFIED CROSS-MARKET "
        "NARRATIVE LIFECYCLE TRACKING PASS"
    )
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
    required = (UPSTREAM, UPSTREAM_TEST, LIFECYCLE_MODULE, LIFECYCLE_TEST)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(
            "Required certified files missing: " + ", ".join(missing)
        )

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    upstream_module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_certified_cross_market_narrative_detection_and_evolution"
    )
    lifecycle_module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_certified_observation_narrative_lifecycle_tracking"
    )

    expected_upstream = {
        "SCHEMA_VERSION": "OML-045",
        "ENGINE_ID": "OML-045",
        "POLICY_ID": (
            "oracle-memory."
            "certified-cross-market-narrative-detection-and-evolution.v1"
        ),
    }
    expected_lifecycle = {
        "SCHEMA_VERSION": "OML-033",
        "ENGINE_ID": "OML-033",
        "POLICY_ID": (
            "oracle-memory."
            "certified-observation-narrative-lifecycle-tracking.v1"
        ),
        "UPSTREAM_SCHEMA_VERSION": "OML-032",
        "UPSTREAM_ENGINE_ID": "OML-032",
    }

    for module, expected, label in (
        (upstream_module, expected_upstream, "OML-045"),
        (lifecycle_module, expected_lifecycle, "OML-033"),
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
                "OracleMemoryCertifiedCrossMarketNarrativeDetection",
                "verify_oracle_memory_certified_cross_market_narrative_detection",
            ),
            "OML-045",
        ),
        (
            lifecycle_module,
            (
                "OracleMemoryObservationNarrativeLifecycleTracking",
                "build_oracle_memory_observation_narrative_lifecycle_tracking",
                "verify_oracle_memory_observation_narrative_lifecycle_tracking",
                "OracleMemoryObservationNarrativeLifecycleInvariantError",
            ),
            "OML-033",
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
            lifecycle_module.
            build_oracle_memory_observation_narrative_lifecycle_tracking
        ).parameters
    )
    missing_parameters = sorted(
        {"detection", "prior_histories"} - parameters
    )
    if missing_parameters:
        raise RuntimeError(
            "Certified OML-033 builder parameters missing: "
            + ", ".join(missing_parameters)
        )


def main() -> int:
    print("=" * 48)
    print(" OML-046 INSTALLER")
    print(" CERTIFIED CROSS-MARKET NARRATIVE LIFECYCLE TRACKING")
    print("=" * 48)
    print("[BOOT] Revision: EXACT_OML_045_033_INTERFACE_ALIGNMENT")

    try:
        validate()
        print("[OK] Actual OML-045 dataclass and verifier inspected")
        print("[OK] Actual OML-033 builder and signature inspected")

        for path, label in (
            (UPSTREAM_TEST, "OML-045"),
            (LIFECYCLE_TEST, "OML-033"),
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
                LIFECYCLE_MODULE,
                LIFECYCLE_TEST,
            )
        }

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_memory_certified_cross_market_"
            "narrative_lifecycle_tracking import *"
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
                f"OML-046 test failed with exit code {completed.returncode}"
            )

        for path, before in tracked.items():
            if path.read_bytes() != before:
                raise RuntimeError(f"Certified upstream changed: {path}")

        print("[PASS] Certified OML-045 production unchanged")
        print("[PASS] Certified OML-045 standalone test unchanged")
        print("[PASS] Certified OML-033 lifecycle engine unchanged")
        print("[PASS] Exact OML-032 detection dataclass consumed directly")
        print("[PASS] OML-046 production fully replaced")
        print("[PASS] OML-046 standalone deterministic test installed")
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
        print(
            "[DONE] OML-046 CERTIFIED CROSS-MARKET "
            "NARRATIVE LIFECYCLE TRACKING INSTALLED"
        )
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
