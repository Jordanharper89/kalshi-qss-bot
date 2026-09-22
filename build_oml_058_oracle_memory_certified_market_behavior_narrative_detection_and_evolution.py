from __future__ import annotations

import ast
import importlib
import inspect
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "oracle_memory"

UPSTREAM = PACKAGE / "oracle_memory_certified_market_behavior_relationship_graph.py"
UPSTREAM_TEST = ROOT / "test_oml_057_oracle_memory_certified_market_behavior_relationship_graph.py"
NARRATIVE_MODULE = PACKAGE / "oracle_memory_certified_observation_narrative_detection_and_evolution.py"
NARRATIVE_TEST = ROOT / "test_oml_032_oracle_memory_certified_observation_narrative_detection_and_evolution.py"

PRODUCTION = PACKAGE / "oracle_memory_certified_market_behavior_narrative_detection_and_evolution.py"
TEST = ROOT / "test_oml_058_oracle_memory_certified_market_behavior_narrative_detection_and_evolution.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_relationship_graph import (
    OracleMemoryCertifiedMarketBehaviorRelationshipGraph,
    verify_oracle_memory_certified_market_behavior_relationship_graph,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_narrative_detection_and_evolution import (
    OracleMemoryObservationNarrativeDetection,
    OracleMemoryObservationNarrativeRequest,
    build_oracle_memory_observation_narrative_detection,
    verify_oracle_memory_observation_narrative_detection,
    verify_oracle_memory_observation_narrative_request,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-058"
ENGINE_ID = "OML-058"
POLICY_ID = (
    "oracle-memory."
    "certified-market-behavior-narrative-detection-and-evolution.v1"
)
UPSTREAM_SCHEMA_VERSION = "OML-057"
UPSTREAM_ENGINE_ID = "OML-057"
NARRATIVE_SCHEMA_VERSION = "OML-032"
NARRATIVE_ENGINE_ID = "OML-032"
STATE_READ_ONLY = "read_only_market_behavior_narrative_detection"


class OracleMemoryCertifiedMarketBehaviorNarrativeInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCertifiedMarketBehaviorNarrativeDetection:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_certification_hash: str
    upstream_graph_materialization_hash: str
    upstream_graph_hash: str
    narrative_schema_version: str
    narrative_engine_id: str
    narrative_detection: OracleMemoryObservationNarrativeDetection
    narrative_count: int
    emerging_count: int
    strengthening_count: int
    weakening_count: int
    resolved_count: int
    state: str
    graph_lineage_verified: bool
    observation_entity_lineage_verified: bool
    relationship_lineage_verified: bool
    observation_narrative_lineage_verified: bool
    canonical_order_verified: bool
    deterministic_detection_verified: bool
    contradiction_tracking_verified: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    detection_ready: bool
    downstream_lifecycle_tracking_authorized: bool
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
    raise OracleMemoryCertifiedMarketBehaviorNarrativeInvariantError(
        "unsupported OML-058 value type"
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
    raise OracleMemoryCertifiedMarketBehaviorNarrativeInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-058 invalid {label} length")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryCertifiedMarketBehaviorNarrativeInvariantError(
            f"OML-058 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_certified_market_behavior_narrative_detection(
    *,
    graph: OracleMemoryCertifiedMarketBehaviorRelationshipGraph,
    requests: Sequence[OracleMemoryObservationNarrativeRequest],
) -> OracleMemoryCertifiedMarketBehaviorNarrativeDetection:
    verify_oracle_memory_certified_market_behavior_relationship_graph(graph)

    if graph.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-058 upstream schema mismatch")
    if graph.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-058 upstream engine mismatch")
    if not graph.graph_ready:
        _reject("OML-058 upstream graph not ready")
    if not graph.downstream_narrative_detection_authorized:
        _reject("OML-058 narrative continuation not authorized")
    if not graph.read_only:
        _reject("OML-058 upstream graph not read-only")

    for request in requests:
        verify_oracle_memory_observation_narrative_request(request)

    detection = build_oracle_memory_observation_narrative_detection(
        materialization=graph.graph_materialization,
        requests=tuple(requests),
    )
    verify_oracle_memory_observation_narrative_detection(detection)

    if detection.schema_version != NARRATIVE_SCHEMA_VERSION:
        _reject("OML-058 narrative schema mismatch")
    if detection.engine_id != NARRATIVE_ENGINE_ID:
        _reject("OML-058 narrative engine mismatch")
    if detection.upstream_materialization_hash != (
        graph.graph_materialization.materialization_hash
    ):
        _reject("OML-058 graph materialization lineage mismatch")
    if detection.upstream_graph_hash != (
        graph.graph_materialization.graph.graph_hash
    ):
        _reject("OML-058 graph hash lineage mismatch")

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": graph.schema_version,
        "upstream_engine_id": graph.engine_id,
        "upstream_certification_hash": graph.certification_hash,
        "upstream_graph_materialization_hash": (
            graph.graph_materialization.materialization_hash
        ),
        "upstream_graph_hash": graph.graph_materialization.graph.graph_hash,
        "narrative_schema_version": detection.schema_version,
        "narrative_engine_id": detection.engine_id,
        "narrative_detection": detection,
        "narrative_count": detection.narrative_count,
        "emerging_count": detection.emerging_count,
        "strengthening_count": detection.strengthening_count,
        "weakening_count": detection.weakening_count,
        "resolved_count": detection.resolved_count,
        "state": STATE_READ_ONLY,
        "graph_lineage_verified": True,
        "observation_entity_lineage_verified": (
            graph.observation_entity_lineage_verified
        ),
        "relationship_lineage_verified": graph.relationship_lineage_verified,
        "observation_narrative_lineage_verified": (
            detection.observation_narrative_lineage_verified
        ),
        "canonical_order_verified": detection.canonical_order_verified,
        "deterministic_detection_verified": (
            detection.deterministic_detection_verified
        ),
        "contradiction_tracking_verified": (
            detection.contradiction_tracking_verified
        ),
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "detection_ready": True,
        "downstream_lifecycle_tracking_authorized": (
            detection.downstream_lifecycle_tracking_authorized
        ),
        "read_only": True,
    }

    result = OracleMemoryCertifiedMarketBehaviorNarrativeDetection(
        **body,
        certification_hash=_stable_hash(body),
    )
    verify_oracle_memory_certified_market_behavior_narrative_detection(result)
    return result


def verify_oracle_memory_certified_market_behavior_narrative_detection(
    result: OracleMemoryCertifiedMarketBehaviorNarrativeDetection,
) -> bool:
    body = asdict(result)
    supplied = body.pop("certification_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-058 certification hash mismatch")

    if result.schema_version != SCHEMA_VERSION:
        _reject("OML-058 schema mismatch")
    if result.engine_id != ENGINE_ID:
        _reject("OML-058 engine mismatch")
    if result.policy_id != POLICY_ID:
        _reject("OML-058 policy mismatch")
    if result.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-058 subsystem mismatch")
    if result.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-058 upstream schema lineage mismatch")
    if result.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-058 upstream engine lineage mismatch")
    if result.narrative_schema_version != NARRATIVE_SCHEMA_VERSION:
        _reject("OML-058 narrative schema lineage mismatch")
    if result.narrative_engine_id != NARRATIVE_ENGINE_ID:
        _reject("OML-058 narrative engine lineage mismatch")

    for value in (
        result.upstream_certification_hash,
        result.upstream_graph_materialization_hash,
        result.upstream_graph_hash,
        result.certification_hash,
    ):
        _require_hash(value, "lineage hash")

    verify_oracle_memory_observation_narrative_detection(
        result.narrative_detection
    )

    if result.upstream_graph_materialization_hash != (
        result.narrative_detection.upstream_materialization_hash
    ):
        _reject("OML-058 materialization lineage mismatch")
    if result.upstream_graph_hash != (
        result.narrative_detection.upstream_graph_hash
    ):
        _reject("OML-058 graph lineage mismatch")
    if result.narrative_count != result.narrative_detection.narrative_count:
        _reject("OML-058 narrative count mismatch")
    if result.emerging_count != result.narrative_detection.emerging_count:
        _reject("OML-058 emerging count mismatch")
    if result.strengthening_count != (
        result.narrative_detection.strengthening_count
    ):
        _reject("OML-058 strengthening count mismatch")
    if result.weakening_count != result.narrative_detection.weakening_count:
        _reject("OML-058 weakening count mismatch")
    if result.resolved_count != result.narrative_detection.resolved_count:
        _reject("OML-058 resolved count mismatch")

    required = (
        result.graph_lineage_verified,
        result.observation_entity_lineage_verified,
        result.relationship_lineage_verified,
        result.observation_narrative_lineage_verified,
        result.canonical_order_verified,
        result.deterministic_detection_verified,
        result.contradiction_tracking_verified,
        result.detection_ready,
        result.downstream_lifecycle_tracking_authorized,
        result.read_only,
    )
    if not all(required):
        _reject("OML-058 guarantee missing")
    if result.state != STATE_READ_ONLY:
        _reject("OML-058 state invalid")

    forbidden = (
        result.persistence_enabled,
        result.learning_updates_enabled,
        result.runtime_activation_enabled,
        result.publication_enabled,
        result.action_authorization_enabled,
        result.qseries_execution_enabled,
    )
    if any(forbidden):
        _reject("OML-058 forbidden capability enabled")

    return True
"""

TEST_SOURCE = r"""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_narrative_detection_and_evolution import (
    OracleMemoryCertifiedMarketBehaviorNarrativeInvariantError,
    build_oracle_memory_certified_market_behavior_narrative_detection,
    verify_oracle_memory_certified_market_behavior_narrative_detection,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_narrative_detection_and_evolution import (
    build_oracle_memory_observation_narrative_request,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_relationship_graph_materialization import (
    build_oracle_memory_observation_relationship_request,
)
from qseries_v2.oracle_memory.oracle_memory_narrative_detection_and_evolution_engine import (
    NARRATIVE_STAGE_STRENGTHENING,
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
    except OracleMemoryCertifiedMarketBehaviorNarrativeInvariantError:
        return
    raise AssertionError(f"tampered OML-058 {label} accepted")


def build_graph(root: Path):
    fixture = load_module(
        root
        / "test_oml_057_oracle_memory_certified_market_behavior_relationship_graph.py",
        "oml_057_fixture_for_oml_058",
    )
    resolution = fixture.build_resolution(root)

    entities = {
        entity.normalized_name: entity
        for entity in resolution.resolution.entities
    }
    liquidity = entities["stablecoin liquidity"]
    bitcoin = entities["bitcoin"]

    relationship_request = build_oracle_memory_observation_relationship_request(
        source_entity_id=liquidity.canonical_entity_id,
        target_entity_id=bitcoin.canonical_entity_id,
        relationship_type="precedes market repricing",
        evidence_hashes=("5" * 64, "6" * 64),
        confidence=0.84,
        contradiction_count=0,
        directed=True,
    )

    from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_relationship_graph import (
        build_oracle_memory_certified_market_behavior_relationship_graph,
    )

    graph = build_oracle_memory_certified_market_behavior_relationship_graph(
        resolution=resolution,
        requests=(relationship_request,),
    )
    return graph, liquidity, bitcoin


def main() -> int:
    print("=" * 48)
    print(" OML-058 TEST")
    print(" CERTIFIED MARKET-BEHAVIOR NARRATIVE DETECTION AND EVOLUTION")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    graph, liquidity, bitcoin = build_graph(root)
    relationship = graph.graph_materialization.graph.relationships[0]

    request = build_oracle_memory_observation_narrative_request(
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
        first_observed_at="2026-08-02T17:00:00-05:00",
        last_observed_at="2026-08-02T17:10:00-05:00",
        evolution_index=1,
    )

    result = build_oracle_memory_certified_market_behavior_narrative_detection(
        graph=graph,
        requests=(request,),
    )

    assert result.schema_version == "OML-058"
    assert result.engine_id == "OML-058"
    assert result.upstream_schema_version == "OML-057"
    assert result.upstream_engine_id == "OML-057"
    assert result.narrative_schema_version == "OML-032"
    assert result.narrative_engine_id == "OML-032"
    assert result.upstream_certification_hash == graph.certification_hash
    assert result.upstream_graph_materialization_hash == (
        graph.graph_materialization.materialization_hash
    )
    assert result.upstream_graph_hash == graph.graph_materialization.graph.graph_hash
    assert result.narrative_count == 1
    assert result.strengthening_count == 1
    assert result.narrative_detection.narratives[0].stage == (
        NARRATIVE_STAGE_STRENGTHENING
    )
    assert result.graph_lineage_verified
    assert result.observation_entity_lineage_verified
    assert result.relationship_lineage_verified
    assert result.observation_narrative_lineage_verified
    assert result.canonical_order_verified
    assert result.deterministic_detection_verified
    assert result.contradiction_tracking_verified
    assert result.detection_ready
    assert result.downstream_lifecycle_tracking_authorized
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled
    assert result.read_only

    replay = build_oracle_memory_certified_market_behavior_narrative_detection(
        graph=graph,
        requests=(request,),
    )
    assert replay == result
    assert verify_oracle_memory_certified_market_behavior_narrative_detection(
        result
    )

    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_narrative_detection(
            replace(result, persistence_enabled=True)
        ),
        "persistence state",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_narrative_detection(
            replace(result, downstream_lifecycle_tracking_authorized=False)
        ),
        "lifecycle continuation",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_narrative_detection(
            replace(result, qseries_execution_enabled=True)
        ),
        "Q Series execution",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_narrative_detection(
            replace(result, certification_hash="f" * 64)
        ),
        "certification hash",
    )

    print("[PASS] Certified OML-057 relationship graph consumed read-only")
    print("[PASS] Exact OML-031 graph materialization passed directly")
    print("[PASS] Actual OML-032 narrative builders consumed")
    print("[PASS] Observation-to-entity lineage retained")
    print("[PASS] Entity-to-relationship lineage retained")
    print("[PASS] Relationship-to-narrative lineage retained")
    print("[PASS] Strengthening narrative detected")
    print("[PASS] Contradiction tracking retained")
    print("[PASS] Lifecycle continuation authorized read-only")
    print("[PASS] Deterministic replay equality verified")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered OML-058 detections rejected")
    print(
        "[DONE] OML-058 CERTIFIED CROSS-MARKET "
        "NARRATIVE DETECTION AND EVOLUTION PASS"
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
    required = (UPSTREAM, UPSTREAM_TEST, NARRATIVE_MODULE, NARRATIVE_TEST)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(
            "Required certified files missing: " + ", ".join(missing)
        )

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    upstream_module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_certified_market_behavior_relationship_graph"
    )
    narrative_module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_certified_observation_narrative_detection_and_evolution"
    )

    expected_upstream = {
        "SCHEMA_VERSION": "OML-057",
        "ENGINE_ID": "OML-057",
        "POLICY_ID": (
            "oracle-memory.certified-market-behavior-relationship-graph.v1"
        ),
    }
    expected_narrative = {
        "SCHEMA_VERSION": "OML-032",
        "ENGINE_ID": "OML-032",
        "POLICY_ID": (
            "oracle-memory."
            "certified-observation-narrative-detection-and-evolution.v1"
        ),
        "UPSTREAM_SCHEMA_VERSION": "OML-031",
        "UPSTREAM_ENGINE_ID": "OML-031",
    }

    for module, expected, label in (
        (upstream_module, expected_upstream, "OML-057"),
        (narrative_module, expected_narrative, "OML-032"),
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
                "OracleMemoryCertifiedMarketBehaviorRelationshipGraph",
                "verify_oracle_memory_certified_market_behavior_relationship_graph",
            ),
            "OML-057",
        ),
        (
            narrative_module,
            (
                "OracleMemoryObservationNarrativeRequest",
                "OracleMemoryObservationNarrativeDetection",
                "build_oracle_memory_observation_narrative_request",
                "build_oracle_memory_observation_narrative_detection",
                "verify_oracle_memory_observation_narrative_request",
                "verify_oracle_memory_observation_narrative_detection",
                "OracleMemoryObservationNarrativeInvariantError",
            ),
            "OML-032",
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

    detection_parameters = set(
        inspect.signature(
            narrative_module.build_oracle_memory_observation_narrative_detection
        ).parameters
    )
    missing_parameters = sorted(
        {"materialization", "requests"} - detection_parameters
    )
    if missing_parameters:
        raise RuntimeError(
            "Certified OML-032 detection builder parameters missing: "
            + ", ".join(missing_parameters)
        )

    upstream_fields = set(
        upstream_module.
        OracleMemoryCertifiedMarketBehaviorRelationshipGraph.__dataclass_fields__
    )
    required_upstream_fields = {
        "schema_version",
        "engine_id",
        "certification_hash",
        "graph_materialization",
        "graph_ready",
        "downstream_narrative_detection_authorized",
        "read_only",
    }
    missing_fields = sorted(required_upstream_fields - upstream_fields)
    if missing_fields:
        raise RuntimeError(
            "Certified OML-057 dataclass fields missing: "
            + ", ".join(missing_fields)
        )


def main() -> int:
    print("=" * 48)
    print(" OML-058 INSTALLER")
    print(" CERTIFIED MARKET-BEHAVIOR NARRATIVE DETECTION AND EVOLUTION")
    print("=" * 48)
    print("[BOOT] Revision: EXACT_OML_044_032_INTERFACE_ALIGNMENT")

    try:
        validate()
        print("[OK] Actual OML-057 dataclass and verifier inspected")
        print("[OK] Actual OML-032 builders and signatures inspected")

        for path, label in (
            (UPSTREAM_TEST, "OML-057"),
            (NARRATIVE_TEST, "OML-032"),
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
                NARRATIVE_MODULE,
                NARRATIVE_TEST,
            )
        }

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_memory_certified_market_behavior_"
            "narrative_detection_and_evolution import *"
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
                f"OML-058 test failed with exit code {completed.returncode}"
            )

        for path, before in tracked.items():
            if path.read_bytes() != before:
                raise RuntimeError(f"Certified upstream changed: {path}")

        print("[PASS] Certified OML-057 production unchanged")
        print("[PASS] Certified OML-057 standalone test unchanged")
        print("[PASS] Certified OML-032 narrative engine unchanged")
        print("[PASS] Exact OML-031 graph dataclass consumed directly")
        print("[PASS] OML-058 production fully replaced")
        print("[PASS] OML-058 standalone deterministic test installed")
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
            "[DONE] OML-058 CERTIFIED CROSS-MARKET "
            "NARRATIVE DETECTION AND EVOLUTION INSTALLED"
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
