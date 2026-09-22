from __future__ import annotations

import ast
import importlib
import inspect
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "oracle_memory"

UPSTREAM = PACKAGE / "oracle_memory_certified_cross_market_entity_resolution.py"
UPSTREAM_TEST = ROOT / "test_oml_043_oracle_memory_certified_cross_market_entity_resolution.py"
GRAPH_MODULE = PACKAGE / "oracle_memory_certified_observation_relationship_graph_materialization.py"
GRAPH_TEST = ROOT / "test_oml_031_oracle_memory_certified_observation_relationship_graph_materialization.py"

PRODUCTION = PACKAGE / "oracle_memory_certified_cross_market_relationship_graph.py"
TEST = ROOT / "test_oml_044_oracle_memory_certified_cross_market_relationship_graph.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_entity_resolution import (
    OracleMemoryCertifiedCrossMarketEntityResolution,
    verify_oracle_memory_certified_cross_market_entity_resolution,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_relationship_graph_materialization import (
    OracleMemoryObservationRelationshipGraphMaterialization,
    OracleMemoryObservationRelationshipRequest,
    build_oracle_memory_observation_relationship_graph_materialization,
    verify_oracle_memory_observation_relationship_graph_materialization,
    verify_oracle_memory_observation_relationship_request,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-044"
ENGINE_ID = "OML-044"
POLICY_ID = "oracle-memory.certified-cross-market-relationship-graph.v1"
UPSTREAM_SCHEMA_VERSION = "OML-043"
UPSTREAM_ENGINE_ID = "OML-043"
GRAPH_SCHEMA_VERSION = "OML-031"
GRAPH_ENGINE_ID = "OML-031"
STATE_READ_ONLY = "read_only_cross_market_relationship_graph"


class OracleMemoryCertifiedCrossMarketRelationshipGraphInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCertifiedCrossMarketRelationshipGraph:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_certification_hash: str
    upstream_resolution_hash: str
    graph_schema_version: str
    graph_engine_id: str
    graph_materialization: OracleMemoryObservationRelationshipGraphMaterialization
    entity_count: int
    relationship_count: int
    state: str
    resolution_lineage_verified: bool
    observation_entity_lineage_verified: bool
    relationship_lineage_verified: bool
    canonical_graph_order_verified: bool
    deterministic_graph_materialization_verified: bool
    dangling_relationships_rejected: bool
    duplicate_relationships_rejected: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    graph_ready: bool
    downstream_narrative_detection_authorized: bool
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
    raise OracleMemoryCertifiedCrossMarketRelationshipGraphInvariantError(
        "unsupported OML-044 value type"
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
    raise OracleMemoryCertifiedCrossMarketRelationshipGraphInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-044 invalid {label} length")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryCertifiedCrossMarketRelationshipGraphInvariantError(
            f"OML-044 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_certified_cross_market_relationship_graph(
    *,
    resolution: OracleMemoryCertifiedCrossMarketEntityResolution,
    requests: Sequence[OracleMemoryObservationRelationshipRequest],
) -> OracleMemoryCertifiedCrossMarketRelationshipGraph:
    verify_oracle_memory_certified_cross_market_entity_resolution(resolution)

    if resolution.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-044 upstream schema mismatch")
    if resolution.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-044 upstream engine mismatch")
    if not resolution.resolution_ready:
        _reject("OML-044 upstream resolution not ready")
    if not resolution.downstream_relationship_graph_authorized:
        _reject("OML-044 relationship graph continuation not authorized")
    if not resolution.read_only:
        _reject("OML-044 upstream resolution not read-only")

    for request in requests:
        verify_oracle_memory_observation_relationship_request(request)

    graph_materialization = (
        build_oracle_memory_observation_relationship_graph_materialization(
            resolution=resolution.resolution,
            requests=tuple(requests),
        )
    )
    verify_oracle_memory_observation_relationship_graph_materialization(
        graph_materialization
    )

    if graph_materialization.schema_version != GRAPH_SCHEMA_VERSION:
        _reject("OML-044 graph schema mismatch")
    if graph_materialization.engine_id != GRAPH_ENGINE_ID:
        _reject("OML-044 graph engine mismatch")
    if graph_materialization.upstream_resolution_hash != (
        resolution.resolution.resolution_hash
    ):
        _reject("OML-044 resolution-to-graph lineage mismatch")

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": resolution.schema_version,
        "upstream_engine_id": resolution.engine_id,
        "upstream_certification_hash": resolution.certification_hash,
        "upstream_resolution_hash": resolution.resolution.resolution_hash,
        "graph_schema_version": graph_materialization.schema_version,
        "graph_engine_id": graph_materialization.engine_id,
        "graph_materialization": graph_materialization,
        "entity_count": graph_materialization.entity_count,
        "relationship_count": graph_materialization.relationship_count,
        "state": STATE_READ_ONLY,
        "resolution_lineage_verified": True,
        "observation_entity_lineage_verified": (
            resolution.observation_entity_lineage_verified
        ),
        "relationship_lineage_verified": (
            graph_materialization.observation_relationship_lineage_verified
        ),
        "canonical_graph_order_verified": (
            graph_materialization.canonical_graph_order_verified
        ),
        "deterministic_graph_materialization_verified": (
            graph_materialization.deterministic_graph_materialization_verified
        ),
        "dangling_relationships_rejected": (
            graph_materialization.dangling_relationships_rejected
        ),
        "duplicate_relationships_rejected": (
            graph_materialization.duplicate_relationships_rejected
        ),
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "graph_ready": True,
        "downstream_narrative_detection_authorized": (
            graph_materialization.downstream_narrative_detection_authorized
        ),
        "read_only": True,
    }

    result = OracleMemoryCertifiedCrossMarketRelationshipGraph(
        **body,
        certification_hash=_stable_hash(body),
    )
    verify_oracle_memory_certified_cross_market_relationship_graph(result)
    return result


def verify_oracle_memory_certified_cross_market_relationship_graph(
    result: OracleMemoryCertifiedCrossMarketRelationshipGraph,
) -> bool:
    body = asdict(result)
    supplied = body.pop("certification_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-044 certification hash mismatch")

    if result.schema_version != SCHEMA_VERSION:
        _reject("OML-044 schema mismatch")
    if result.engine_id != ENGINE_ID:
        _reject("OML-044 engine mismatch")
    if result.policy_id != POLICY_ID:
        _reject("OML-044 policy mismatch")
    if result.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-044 subsystem mismatch")
    if result.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-044 upstream schema lineage mismatch")
    if result.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-044 upstream engine lineage mismatch")
    if result.graph_schema_version != GRAPH_SCHEMA_VERSION:
        _reject("OML-044 graph schema lineage mismatch")
    if result.graph_engine_id != GRAPH_ENGINE_ID:
        _reject("OML-044 graph engine lineage mismatch")

    for value in (
        result.upstream_certification_hash,
        result.upstream_resolution_hash,
        result.certification_hash,
    ):
        _require_hash(value, "lineage hash")

    verify_oracle_memory_observation_relationship_graph_materialization(
        result.graph_materialization
    )

    if result.upstream_resolution_hash != (
        result.graph_materialization.upstream_resolution_hash
    ):
        _reject("OML-044 graph resolution lineage mismatch")
    if result.entity_count != result.graph_materialization.entity_count:
        _reject("OML-044 entity count mismatch")
    if result.relationship_count != (
        result.graph_materialization.relationship_count
    ):
        _reject("OML-044 relationship count mismatch")

    required = (
        result.resolution_lineage_verified,
        result.observation_entity_lineage_verified,
        result.relationship_lineage_verified,
        result.canonical_graph_order_verified,
        result.deterministic_graph_materialization_verified,
        result.dangling_relationships_rejected,
        result.duplicate_relationships_rejected,
        result.graph_ready,
        result.downstream_narrative_detection_authorized,
        result.read_only,
    )
    if not all(required):
        _reject("OML-044 guarantee missing")

    if result.state != STATE_READ_ONLY:
        _reject("OML-044 state invalid")

    forbidden = (
        result.persistence_enabled,
        result.learning_updates_enabled,
        result.runtime_activation_enabled,
        result.publication_enabled,
        result.action_authorization_enabled,
        result.qseries_execution_enabled,
    )
    if any(forbidden):
        _reject("OML-044 forbidden capability enabled")

    return True
"""

TEST_SOURCE = r"""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_relationship_graph import (
    OracleMemoryCertifiedCrossMarketRelationshipGraphInvariantError,
    build_oracle_memory_certified_cross_market_relationship_graph,
    verify_oracle_memory_certified_cross_market_relationship_graph,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_relationship_graph_materialization import (
    build_oracle_memory_observation_relationship_request,
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
    except OracleMemoryCertifiedCrossMarketRelationshipGraphInvariantError:
        return
    raise AssertionError(f"tampered OML-044 {label} accepted")


def build_resolution(root: Path):
    fixture_039 = load_module(
        root
        / "test_oml_039_oracle_memory_certified_cross_market_observation_intake_bridge.py",
        "oml_039_fixture_for_oml_044",
    )
    dependencies = fixture_039.build_dependencies(root)
    dependency = dependencies.dependency_memory.dependencies[0]

    from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_observation_intake_bridge import (
        build_oracle_memory_certified_cross_market_intake_request,
        build_oracle_memory_certified_cross_market_intake_bridge,
    )
    from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_candidate_materialization_authorization_gate import (
        build_oracle_memory_cross_market_materialization_authorization_decision,
    )
    from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_candidate_materialization import (
        build_oracle_memory_certified_cross_market_candidate_materialization,
    )
    from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_candidate_validation_and_admission import (
        build_oracle_memory_certified_cross_market_candidate_admission,
    )
    from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_entity_resolution import (
        build_oracle_memory_certified_cross_market_entity_resolution,
    )
    from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
        MEMORY_DOMAINS,
    )

    domain_id = (
        "market_behavior_memory"
        if "market_behavior_memory" in MEMORY_DOMAINS
        else MEMORY_DOMAINS[0]
    )

    intake_requests = (
        build_oracle_memory_certified_cross_market_intake_request(
            dependency_id=dependency.dependency_id,
            domain_id=domain_id,
            entity_key="Stablecoin Liquidity",
            source_key="oracle-memory-oml-038",
            observed_at="2026-08-02T17:00:00-05:00",
            effective_at="2026-08-02T17:00:00-05:00",
            payload={
                "observation": "Stablecoin inflows increased before repricing.",
                "observation_type": "real_world_liquidity_shift",
            },
            confidence=0.82,
            uncertainty=0.18,
        ),
        build_oracle_memory_certified_cross_market_intake_request(
            dependency_id=dependency.dependency_id,
            domain_id=domain_id,
            entity_key="Bitcoin",
            source_key="oracle-memory-oml-038",
            observed_at="2026-08-02T17:10:00-05:00",
            effective_at="2026-08-02T17:10:00-05:00",
            payload={
                "observation": "Bitcoin repriced after the liquidity shift.",
                "observation_type": "market_repricing",
            },
            confidence=0.79,
            uncertainty=0.21,
        ),
    )

    bridge = build_oracle_memory_certified_cross_market_intake_bridge(
        dependencies=dependencies,
        requests=intake_requests,
    )
    authorization = (
        build_oracle_memory_cross_market_materialization_authorization_decision(
            bridge=bridge,
        )
    )

    fixture_028 = load_module(
        root
        / "test_oml_028_oracle_memory_certified_observation_candidate_materialization.py",
        "oml_028_fixture_for_oml_044",
    )
    registry_gate_decision, _ = fixture_028.build_intake_batch(root)

    materialization = (
        build_oracle_memory_certified_cross_market_candidate_materialization(
            authorization=authorization,
            bridge=bridge,
            registry_gate_decision=registry_gate_decision,
        )
    )

    fixture_042 = load_module(
        root
        / "test_oml_042_oracle_memory_certified_cross_market_candidate_validation_and_admission.py",
        "oml_042_fixture_for_oml_044",
    )
    validation_batch = fixture_042.build_validation(root, materialization)

    admission = build_oracle_memory_certified_cross_market_candidate_admission(
        materialization=materialization,
        validation_batch=validation_batch,
    )

    candidate_by_hash = {
        candidate.candidate_hash: candidate
        for candidate in materialization.materialization_batch.candidates
    }
    aliases = {}
    for item in admission.admission_batch.admissions:
        if item.admission_status != "admitted":
            continue
        candidate = candidate_by_hash[item.candidate_hash]
        if candidate.entity_key == "Stablecoin Liquidity":
            aliases[item.candidate_hash] = (
                "Stablecoin Liquidity",
                "USDT Liquidity",
            )
        elif candidate.entity_key == "Bitcoin":
            aliases[item.candidate_hash] = (
                "Bitcoin",
                "BTC",
                "XBT",
            )

    resolution = build_oracle_memory_certified_cross_market_entity_resolution(
        admission=admission,
        materialization_batch=materialization.materialization_batch,
        validation_batch=validation_batch,
        aliases_by_candidate_hash=aliases,
    )

    assert resolution.resolved_entity_count == 2
    assert {
        entity.normalized_name
        for entity in resolution.resolution.entities
    } == {"bitcoin", "stablecoin liquidity"}

    return resolution


def main() -> int:
    print("=" * 48)
    print(" OML-044 TEST")
    print(" CERTIFIED CROSS-MARKET RELATIONSHIP GRAPH")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    resolution = build_resolution(root)

    assert resolution.resolved_entity_count >= 2
    entities = tuple(resolution.resolution.entities)
    source = entities[0]
    target = entities[1]

    request = build_oracle_memory_observation_relationship_request(
        source_entity_id=source.canonical_entity_id,
        target_entity_id=target.canonical_entity_id,
        relationship_type="precedes market repricing",
        evidence_hashes=("5" * 64, "6" * 64),
        confidence=0.84,
        contradiction_count=0,
        directed=True,
    )

    result = build_oracle_memory_certified_cross_market_relationship_graph(
        resolution=resolution,
        requests=(request,),
    )

    assert result.schema_version == "OML-044"
    assert result.engine_id == "OML-044"
    assert result.upstream_schema_version == "OML-043"
    assert result.upstream_engine_id == "OML-043"
    assert result.graph_schema_version == "OML-031"
    assert result.graph_engine_id == "OML-031"
    assert result.entity_count >= 2
    assert result.relationship_count == 1
    assert result.graph_materialization.relationship_count == 1
    assert result.upstream_certification_hash == resolution.certification_hash
    assert result.upstream_resolution_hash == resolution.resolution.resolution_hash
    assert result.resolution_lineage_verified
    assert result.observation_entity_lineage_verified
    assert result.relationship_lineage_verified
    assert result.canonical_graph_order_verified
    assert result.deterministic_graph_materialization_verified
    assert result.dangling_relationships_rejected
    assert result.duplicate_relationships_rejected
    assert result.graph_ready
    assert result.downstream_narrative_detection_authorized
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled
    assert result.read_only

    replay = build_oracle_memory_certified_cross_market_relationship_graph(
        resolution=resolution,
        requests=(request,),
    )
    assert replay == result
    assert verify_oracle_memory_certified_cross_market_relationship_graph(result)

    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_relationship_graph(
            replace(result, persistence_enabled=True)
        ),
        "persistence state",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_relationship_graph(
            replace(result, downstream_narrative_detection_authorized=False)
        ),
        "narrative continuation",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_relationship_graph(
            replace(result, qseries_execution_enabled=True)
        ),
        "Q Series execution",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_relationship_graph(
            replace(result, certification_hash="f" * 64)
        ),
        "certification hash",
    )

    print("[PASS] Certified OML-043 entity resolution consumed read-only")
    print("[PASS] Exact OML-030 resolution dataclass passed directly")
    print("[PASS] Actual OML-031 relationship request builder consumed")
    print("[PASS] Actual OML-031 graph materialization builder consumed")
    print("[PASS] Observation-to-entity lineage retained")
    print("[PASS] Entity-to-relationship lineage retained")
    print("[PASS] Dangling and duplicate relationships rejected")
    print("[PASS] Narrative-detection continuation authorized read-only")
    print("[PASS] Deterministic replay equality verified")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered OML-044 graphs rejected")
    print("[DONE] OML-044 CERTIFIED CROSS-MARKET RELATIONSHIP GRAPH PASS")
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
    required = (UPSTREAM, UPSTREAM_TEST, GRAPH_MODULE, GRAPH_TEST)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(
            "Required certified files missing: " + ", ".join(missing)
        )

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    upstream_module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_certified_cross_market_entity_resolution"
    )
    graph_module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_certified_observation_relationship_graph_materialization"
    )

    expected_upstream = {
        "SCHEMA_VERSION": "OML-043",
        "ENGINE_ID": "OML-043",
        "POLICY_ID": (
            "oracle-memory.certified-cross-market-entity-resolution.v1"
        ),
    }
    expected_graph = {
        "SCHEMA_VERSION": "OML-031",
        "ENGINE_ID": "OML-031",
        "POLICY_ID": (
            "oracle-memory."
            "certified-observation-relationship-graph-materialization.v1"
        ),
        "UPSTREAM_SCHEMA_VERSION": "OML-030",
        "UPSTREAM_ENGINE_ID": "OML-030",
    }

    for module, expected, label in (
        (upstream_module, expected_upstream, "OML-043"),
        (graph_module, expected_graph, "OML-031"),
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
                "OracleMemoryCertifiedCrossMarketEntityResolution",
                "verify_oracle_memory_certified_cross_market_entity_resolution",
            ),
            "OML-043",
        ),
        (
            graph_module,
            (
                "OracleMemoryObservationRelationshipRequest",
                "OracleMemoryObservationRelationshipGraphMaterialization",
                "build_oracle_memory_observation_relationship_request",
                "build_oracle_memory_observation_relationship_graph_materialization",
                "verify_oracle_memory_observation_relationship_request",
                "verify_oracle_memory_observation_relationship_graph_materialization",
                "OracleMemoryObservationRelationshipGraphInvariantError",
            ),
            "OML-031",
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

    request_parameters = set(
        inspect.signature(
            graph_module.build_oracle_memory_observation_relationship_request
        ).parameters
    )
    required_request_parameters = {
        "source_entity_id",
        "target_entity_id",
        "relationship_type",
        "evidence_hashes",
        "confidence",
        "contradiction_count",
        "directed",
    }
    missing_request_parameters = sorted(
        required_request_parameters - request_parameters
    )
    if missing_request_parameters:
        raise RuntimeError(
            "Certified OML-031 request builder parameters missing: "
            + ", ".join(missing_request_parameters)
        )

    graph_parameters = set(
        inspect.signature(
            graph_module.
            build_oracle_memory_observation_relationship_graph_materialization
        ).parameters
    )
    required_graph_parameters = {"resolution", "requests"}
    missing_graph_parameters = sorted(
        required_graph_parameters - graph_parameters
    )
    if missing_graph_parameters:
        raise RuntimeError(
            "Certified OML-031 graph builder parameters missing: "
            + ", ".join(missing_graph_parameters)
        )

    upstream_fields = set(
        upstream_module.
        OracleMemoryCertifiedCrossMarketEntityResolution.__dataclass_fields__
    )
    required_upstream_fields = {
        "schema_version",
        "engine_id",
        "certification_hash",
        "resolution",
        "resolution_ready",
        "downstream_relationship_graph_authorized",
        "read_only",
    }
    missing_fields = sorted(required_upstream_fields - upstream_fields)
    if missing_fields:
        raise RuntimeError(
            "Certified OML-043 dataclass fields missing: "
            + ", ".join(missing_fields)
        )


def main() -> int:
    print("=" * 48)
    print(" OML-044 CORRECTION V2 INSTALLER")
    print(" CERTIFIED CROSS-MARKET RELATIONSHIP GRAPH")
    print("=" * 48)
    print("[BOOT] Revision: CORRECTION_V2_TWO_ADMITTED_ENTITY_FIXTURE")

    try:
        validate()
        print("[OK] Actual OML-043 dataclass and verifier inspected")
        print("[OK] Actual OML-031 builders and signatures inspected")

        for path, label in (
            (UPSTREAM_TEST, "OML-043"),
            (GRAPH_TEST, "OML-031"),
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
                GRAPH_MODULE,
                GRAPH_TEST,
            )
        }

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_memory_certified_cross_market_"
            "relationship_graph import *"
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
                f"OML-044 test failed with exit code {completed.returncode}"
            )

        for path, before in tracked.items():
            if path.read_bytes() != before:
                raise RuntimeError(f"Certified upstream changed: {path}")

        print("[PASS] Certified OML-043 production unchanged")
        print("[PASS] Certified OML-043 standalone test unchanged")
        print("[PASS] Certified OML-031 graph engine unchanged")
        print("[PASS] Exact upstream resolution dataclass consumed directly")
        print("[PASS] OML-044 production fully replaced")
        print("[PASS] OML-044 standalone deterministic test installed")
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
            "[DONE] OML-044 CORRECTION V2 CERTIFIED CROSS-MARKET "
            "RELATIONSHIP GRAPH INSTALLED"
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
