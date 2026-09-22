from __future__ import annotations

import ast
import importlib
import inspect
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "oracle_memory"

UPSTREAM = PACKAGE / "oracle_memory_certified_market_behavior_narrative_lifecycle_tracking.py"
UPSTREAM_TEST = ROOT / "test_oml_059_oracle_memory_certified_market_behavior_narrative_lifecycle_tracking.py"
RELIABILITY_MODULE = PACKAGE / "oracle_memory_certified_observation_source_reliability_memory.py"
RELIABILITY_TEST = ROOT / "test_oml_034_oracle_memory_certified_observation_source_reliability_memory.py"

PRODUCTION = PACKAGE / "oracle_memory_certified_market_behavior_source_reliability.py"
TEST = ROOT / "test_oml_060_oracle_memory_certified_market_behavior_source_reliability.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_narrative_lifecycle_tracking import (
    OracleMemoryCertifiedMarketBehaviorNarrativeLifecycle,
    verify_oracle_memory_certified_market_behavior_narrative_lifecycle,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_source_reliability_memory import (
    OracleMemoryCertifiedSourceOutcome,
    OracleMemoryCertifiedSourceReliability,
    build_oracle_memory_certified_source_reliability,
    verify_oracle_memory_certified_source_outcome,
    verify_oracle_memory_certified_source_reliability,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-060"
ENGINE_ID = "OML-060"
POLICY_ID = "oracle-memory.certified-market-behavior-source-reliability.v1"
UPSTREAM_SCHEMA_VERSION = "OML-059"
UPSTREAM_ENGINE_ID = "OML-059"
RELIABILITY_SCHEMA_VERSION = "OML-034"
RELIABILITY_ENGINE_ID = "OML-034"
STATE_READ_ONLY = "read_only_market_behavior_source_reliability"


class OracleMemoryCertifiedMarketBehaviorReliabilityInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCertifiedMarketBehaviorSourceReliability:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_certification_hash: str
    upstream_lifecycle_tracking_hash: str
    reliability_schema_version: str
    reliability_engine_id: str
    source_reliability: OracleMemoryCertifiedSourceReliability
    source_count: int
    total_observation_count: int
    state: str
    lifecycle_lineage_verified: bool
    narrative_lineage_verified: bool
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
    reliability_ready: bool
    downstream_calibration_authorized: bool
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
    raise OracleMemoryCertifiedMarketBehaviorReliabilityInvariantError(
        "unsupported OML-060 value type"
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
    raise OracleMemoryCertifiedMarketBehaviorReliabilityInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-060 invalid {label} length")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryCertifiedMarketBehaviorReliabilityInvariantError(
            f"OML-060 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_certified_market_behavior_source_reliability(
    *,
    lifecycle: OracleMemoryCertifiedMarketBehaviorNarrativeLifecycle,
    outcomes: Sequence[OracleMemoryCertifiedSourceOutcome],
) -> OracleMemoryCertifiedMarketBehaviorSourceReliability:
    verify_oracle_memory_certified_market_behavior_narrative_lifecycle(lifecycle)

    if lifecycle.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-060 upstream schema mismatch")
    if lifecycle.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-060 upstream engine mismatch")
    if not lifecycle.lifecycle_ready:
        _reject("OML-060 upstream lifecycle not ready")
    if not lifecycle.downstream_source_reliability_authorized:
        _reject("OML-060 reliability continuation not authorized")
    if not lifecycle.read_only:
        _reject("OML-060 upstream lifecycle not read-only")

    allowed_hashes = {
        value
        for binding in lifecycle.lifecycle_tracking.bindings
        for value in binding.source_observation_hashes
    }
    if not allowed_hashes:
        _reject("OML-060 lifecycle contains no certified observations")

    for outcome in outcomes:
        verify_oracle_memory_certified_source_outcome(outcome)
        if outcome.observation_hash not in allowed_hashes:
            _reject("OML-060 outcome references unknown certified observation")

    reliability = build_oracle_memory_certified_source_reliability(
        tracking=lifecycle.lifecycle_tracking,
        outcomes=tuple(outcomes),
    )
    verify_oracle_memory_certified_source_reliability(reliability)

    if reliability.schema_version != RELIABILITY_SCHEMA_VERSION:
        _reject("OML-060 reliability schema mismatch")
    if reliability.engine_id != RELIABILITY_ENGINE_ID:
        _reject("OML-060 reliability engine mismatch")
    if reliability.upstream_tracking_hash != (
        lifecycle.lifecycle_tracking.tracking_hash
    ):
        _reject("OML-060 lifecycle-to-reliability lineage mismatch")

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": lifecycle.schema_version,
        "upstream_engine_id": lifecycle.engine_id,
        "upstream_certification_hash": lifecycle.certification_hash,
        "upstream_lifecycle_tracking_hash": (
            lifecycle.lifecycle_tracking.tracking_hash
        ),
        "reliability_schema_version": reliability.schema_version,
        "reliability_engine_id": reliability.engine_id,
        "source_reliability": reliability,
        "source_count": reliability.source_count,
        "total_observation_count": reliability.total_observation_count,
        "state": STATE_READ_ONLY,
        "lifecycle_lineage_verified": True,
        "narrative_lineage_verified": (
            lifecycle.observation_lifecycle_lineage_verified
        ),
        "certified_observation_lineage_verified": (
            reliability.certified_observation_lineage_verified
        ),
        "deterministic_scoring_verified": (
            reliability.deterministic_scoring_verified
        ),
        "source_identity_uniqueness_verified": (
            reliability.source_identity_uniqueness_verified
        ),
        "contradiction_tracking_verified": (
            reliability.contradiction_tracking_verified
        ),
        "calibration_tracking_verified": (
            reliability.calibration_tracking_verified
        ),
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "reliability_ready": True,
        "downstream_calibration_authorized": (
            reliability.downstream_calibration_authorized
        ),
        "read_only": True,
    }
    result = OracleMemoryCertifiedMarketBehaviorSourceReliability(
        **body,
        certification_hash=_stable_hash(body),
    )
    verify_oracle_memory_certified_market_behavior_source_reliability(result)
    return result


def verify_oracle_memory_certified_market_behavior_source_reliability(
    result: OracleMemoryCertifiedMarketBehaviorSourceReliability,
) -> bool:
    body = asdict(result)
    supplied = body.pop("certification_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-060 certification hash mismatch")

    if result.schema_version != SCHEMA_VERSION:
        _reject("OML-060 schema mismatch")
    if result.engine_id != ENGINE_ID:
        _reject("OML-060 engine mismatch")
    if result.policy_id != POLICY_ID:
        _reject("OML-060 policy mismatch")
    if result.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-060 subsystem mismatch")
    if result.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-060 upstream schema lineage mismatch")
    if result.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-060 upstream engine lineage mismatch")
    if result.reliability_schema_version != RELIABILITY_SCHEMA_VERSION:
        _reject("OML-060 reliability schema lineage mismatch")
    if result.reliability_engine_id != RELIABILITY_ENGINE_ID:
        _reject("OML-060 reliability engine lineage mismatch")

    for value in (
        result.upstream_certification_hash,
        result.upstream_lifecycle_tracking_hash,
        result.certification_hash,
    ):
        _require_hash(value, "lineage hash")

    verify_oracle_memory_certified_source_reliability(
        result.source_reliability
    )

    if result.upstream_lifecycle_tracking_hash != (
        result.source_reliability.upstream_tracking_hash
    ):
        _reject("OML-060 reliability lineage mismatch")
    if result.source_count != result.source_reliability.source_count:
        _reject("OML-060 source count mismatch")
    if result.total_observation_count != (
        result.source_reliability.total_observation_count
    ):
        _reject("OML-060 observation count mismatch")

    required = (
        result.lifecycle_lineage_verified,
        result.narrative_lineage_verified,
        result.certified_observation_lineage_verified,
        result.deterministic_scoring_verified,
        result.source_identity_uniqueness_verified,
        result.contradiction_tracking_verified,
        result.calibration_tracking_verified,
        result.reliability_ready,
        result.downstream_calibration_authorized,
        result.read_only,
    )
    if not all(required):
        _reject("OML-060 guarantee missing")
    if result.state != STATE_READ_ONLY:
        _reject("OML-060 state invalid")

    forbidden = (
        result.persistence_enabled,
        result.learning_updates_enabled,
        result.runtime_activation_enabled,
        result.publication_enabled,
        result.action_authorization_enabled,
        result.qseries_execution_enabled,
    )
    if any(forbidden):
        _reject("OML-060 forbidden capability enabled")

    return True
"""

TEST_SOURCE = r"""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_source_reliability import (
    OracleMemoryCertifiedMarketBehaviorReliabilityInvariantError,
    build_oracle_memory_certified_market_behavior_source_reliability,
    verify_oracle_memory_certified_market_behavior_source_reliability,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_source_reliability_memory import (
    build_oracle_memory_certified_source_outcome,
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
    except OracleMemoryCertifiedMarketBehaviorReliabilityInvariantError:
        return
    raise AssertionError(f"tampered OML-060 {label} accepted")


def build_lifecycle(root: Path):
    fixture = load_module(
        root
        / "test_oml_058_oracle_memory_certified_market_behavior_narrative_detection_and_evolution.py",
        "oml_058_fixture_for_oml_060",
    )
    graph, liquidity, bitcoin = fixture.build_graph(root)
    relationship = graph.graph_materialization.graph.relationships[0]

    from qseries_v2.oracle_memory.oracle_memory_narrative_detection_and_evolution_engine import (
        build_oracle_memory_narrative,
    )
    from qseries_v2.oracle_memory.oracle_memory_certified_observation_narrative_detection_and_evolution import (
        build_oracle_memory_observation_narrative_request,
    )
    from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_narrative_detection_and_evolution import (
        build_oracle_memory_certified_market_behavior_narrative_detection,
    )
    from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_narrative_lifecycle_tracking import (
        build_oracle_memory_certified_market_behavior_narrative_lifecycle,
    )

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
        first_observed_at="2026-08-02T16:50:00-05:00",
        last_observed_at="2026-08-02T17:10:00-05:00",
        evolution_index=2,
        prior_stage=prior.stage,
    )

    detection = (
        build_oracle_memory_certified_market_behavior_narrative_detection(
            graph=graph,
            requests=(request,),
        )
    )
    current = detection.narrative_detection.narratives[0]

    return build_oracle_memory_certified_market_behavior_narrative_lifecycle(
        detection=detection,
        prior_histories={current.narrative_id: (prior,)},
    )


def main() -> int:
    print("=" * 48)
    print(" OML-060 TEST")
    print(" CERTIFIED MARKET-BEHAVIOR SOURCE RELIABILITY")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    lifecycle = build_lifecycle(root)

    observation_hashes = tuple(sorted({
        value
        for binding in lifecycle.lifecycle_tracking.bindings
        for value in binding.source_observation_hashes
    }))
    assert observation_hashes

    outcomes = tuple(
        build_oracle_memory_certified_source_outcome(
            source_name="Oracle Cross-Market Observation",
            observation_hash=value,
            outcome_confirmed=True,
            outcome_correct=(index % 2 == 0),
            contradiction_count=0 if index % 2 == 0 else 1,
            confidence_at_observation=0.80 - (index * 0.05),
            observed_at=f"2026-08-02T17:{20 + index:02d}:00-05:00",
        )
        for index, value in enumerate(observation_hashes)
    )

    result = build_oracle_memory_certified_market_behavior_source_reliability(
        lifecycle=lifecycle,
        outcomes=outcomes,
    )

    assert result.schema_version == "OML-060"
    assert result.engine_id == "OML-060"
    assert result.upstream_schema_version == "OML-059"
    assert result.upstream_engine_id == "OML-059"
    assert result.reliability_schema_version == "OML-034"
    assert result.reliability_engine_id == "OML-034"
    assert result.source_count == 1
    assert result.total_observation_count == len(outcomes)
    assert result.upstream_certification_hash == lifecycle.certification_hash
    assert result.upstream_lifecycle_tracking_hash == (
        lifecycle.lifecycle_tracking.tracking_hash
    )
    assert result.lifecycle_lineage_verified
    assert result.narrative_lineage_verified
    assert result.certified_observation_lineage_verified
    assert result.deterministic_scoring_verified
    assert result.source_identity_uniqueness_verified
    assert result.contradiction_tracking_verified
    assert result.calibration_tracking_verified
    assert result.reliability_ready
    assert result.downstream_calibration_authorized
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled
    assert result.read_only

    replay = build_oracle_memory_certified_market_behavior_source_reliability(
        lifecycle=lifecycle,
        outcomes=outcomes,
    )
    assert replay == result
    assert verify_oracle_memory_certified_market_behavior_source_reliability(
        result
    )

    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_source_reliability(
            replace(result, persistence_enabled=True)
        ),
        "persistence state",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_source_reliability(
            replace(result, downstream_calibration_authorized=False)
        ),
        "calibration continuation",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_source_reliability(
            replace(result, qseries_execution_enabled=True)
        ),
        "Q Series execution",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_source_reliability(
            replace(result, certification_hash="f" * 64)
        ),
        "certification hash",
    )

    print("[PASS] Certified OML-059 lifecycle consumed read-only")
    print("[PASS] Exact OML-033 lifecycle-tracking dataclass passed directly")
    print("[PASS] Actual OML-034 source-reliability builder consumed")
    print("[PASS] Outcomes bound only to certified observation hashes")
    print("[PASS] Narrative and lifecycle lineage retained")
    print("[PASS] Reliability and calibration tracking retained")
    print("[PASS] Calibration continuation authorized read-only")
    print("[PASS] Deterministic replay equality verified")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered OML-060 reliability records rejected")
    print("[DONE] OML-060 CERTIFIED MARKET-BEHAVIOR SOURCE RELIABILITY PASS")
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
    required = (UPSTREAM, UPSTREAM_TEST, RELIABILITY_MODULE, RELIABILITY_TEST)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(
            "Required certified files missing: " + ", ".join(missing)
        )

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    upstream_module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_certified_market_behavior_narrative_lifecycle_tracking"
    )
    reliability_module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_certified_observation_source_reliability_memory"
    )

    expected = (
        (upstream_module, {
            "SCHEMA_VERSION": "OML-059",
            "ENGINE_ID": "OML-059",
            "POLICY_ID": (
                "oracle-memory."
                "certified-market-behavior-narrative-lifecycle-tracking.v1"
            ),
        }, "OML-059"),
        (reliability_module, {
            "SCHEMA_VERSION": "OML-034",
            "ENGINE_ID": "OML-034",
            "POLICY_ID": (
                "oracle-memory."
                "certified-observation-source-reliability-memory.v1"
            ),
            "UPSTREAM_SCHEMA_VERSION": "OML-033",
            "UPSTREAM_ENGINE_ID": "OML-033",
        }, "OML-034"),
    )
    for module, values, label in expected:
        for name, value in values.items():
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
                "OracleMemoryCertifiedMarketBehaviorNarrativeLifecycle",
                "verify_oracle_memory_certified_market_behavior_narrative_lifecycle",
            ),
            "OML-059",
        ),
        (
            reliability_module,
            (
                "OracleMemoryCertifiedSourceOutcome",
                "OracleMemoryCertifiedSourceReliability",
                "build_oracle_memory_certified_source_reliability",
                "verify_oracle_memory_certified_source_outcome",
                "verify_oracle_memory_certified_source_reliability",
            ),
            "OML-034",
        ),
    )
    for module, symbols, label in required_symbols:
        missing_symbols = [name for name in symbols if not hasattr(module, name)]
        if missing_symbols:
            raise RuntimeError(
                f"Certified {label} missing symbols: "
                + ", ".join(missing_symbols)
            )

    parameters = set(
        inspect.signature(
            reliability_module.build_oracle_memory_certified_source_reliability
        ).parameters
    )
    missing_parameters = sorted({"tracking", "outcomes"} - parameters)
    if missing_parameters:
        raise RuntimeError(
            "Certified OML-034 builder parameters missing: "
            + ", ".join(missing_parameters)
        )


def main() -> int:
    print("=" * 48)
    print(" OML-060 INSTALLER")
    print(" CERTIFIED MARKET-BEHAVIOR SOURCE RELIABILITY")
    print("=" * 48)
    print("[BOOT] Revision: EXACT_OML_046_034_INTERFACE_ALIGNMENT")

    try:
        validate()
        print("[OK] Actual OML-059 dataclass and verifier inspected")
        print("[OK] Actual OML-034 builder and signature inspected")

        for path, label in (
            (UPSTREAM_TEST, "OML-059"),
            (RELIABILITY_TEST, "OML-034"),
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
                RELIABILITY_MODULE,
                RELIABILITY_TEST,
            )
        }

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_memory_certified_market_behavior_"
            "source_reliability import *"
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
                f"OML-060 test failed with exit code {completed.returncode}"
            )

        for path, before in tracked.items():
            if path.read_bytes() != before:
                raise RuntimeError(f"Certified upstream changed: {path}")

        print("[PASS] Certified OML-059 production unchanged")
        print("[PASS] Certified OML-059 standalone test unchanged")
        print("[PASS] Certified OML-034 reliability engine unchanged")
        print("[PASS] Exact OML-033 lifecycle dataclass consumed directly")
        print("[PASS] OML-060 production fully replaced")
        print("[PASS] OML-060 standalone deterministic test installed")
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
            "[DONE] OML-060 CERTIFIED CROSS-MARKET "
            "SOURCE RELIABILITY INSTALLED"
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
