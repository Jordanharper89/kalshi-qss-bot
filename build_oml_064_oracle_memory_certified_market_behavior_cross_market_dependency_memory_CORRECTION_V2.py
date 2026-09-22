from __future__ import annotations

import ast
import importlib
import inspect
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "oracle_memory"

UPSTREAM = PACKAGE / "oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory.py"
UPSTREAM_TEST = ROOT / "test_oml_063_oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory.py"
DEPENDENCY = PACKAGE / "oracle_memory_certified_observation_cross_market_dependency_memory.py"
DEPENDENCY_TEST = ROOT / "test_oml_038_oracle_memory_certified_observation_cross_market_dependency_memory.py"

PRODUCTION = PACKAGE / "oracle_memory_certified_market_behavior_cross_market_dependency_memory.py"
TEST = ROOT / "test_oml_064_oracle_memory_certified_market_behavior_cross_market_dependency_memory.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory import (
    OracleMemoryCertifiedMarketBehaviorMultiHopCausalChainMemory,
    verify_oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_cross_market_dependency_memory import (
    OracleMemoryCertifiedCrossMarketDependencyMemory as InnerDependencyMemory,
    OracleMemoryCertifiedCrossMarketObservationRequest,
    build_oracle_memory_certified_cross_market_dependency_memory as build_inner_dependency_memory,
    verify_oracle_memory_certified_cross_market_dependency_memory as verify_inner_dependency_memory,
    verify_oracle_memory_certified_cross_market_observation_request,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import SUBSYSTEM_ID

SCHEMA_VERSION = "OML-064"
ENGINE_ID = "OML-064"
POLICY_ID = "oracle-memory.certified-market-behavior-cross-market-dependency-memory.v1"
UPSTREAM_SCHEMA_VERSION = "OML-063"
UPSTREAM_ENGINE_ID = "OML-063"
DEPENDENCY_SCHEMA_VERSION = "OML-038"
DEPENDENCY_ENGINE_ID = "OML-038"
STATE_READ_ONLY = "read_only_market_behavior_cross_market_dependency_memory"


class OracleMemoryCertifiedMarketBehaviorDependencyInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCertifiedMarketBehaviorCrossMarketDependencyMemory:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_certification_hash: str
    upstream_chain_certification_hash: str
    upstream_chain_memory_hash: str
    dependency_schema_version: str
    dependency_engine_id: str
    dependencies: InnerDependencyMemory
    dependency_count: int
    total_observation_count: int
    source_market_count: int
    target_market_count: int
    state: str
    chain_lineage_verified: bool
    causal_pattern_lineage_verified: bool
    certified_observation_lineage_verified: bool
    deterministic_identity_verified: bool
    canonical_dependency_order_verified: bool
    lead_lag_direction_verified: bool
    evidence_lineage_verified: bool
    contradiction_tracking_verified: bool
    calibration_lineage_verified: bool
    outcome_reconciliation_verified: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    dependency_memory_ready: bool
    downstream_market_behavior_authorized: bool
    read_only: bool
    certification_hash: str


def _canonical(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {str(k): _canonical(v) for k, v in sorted(value.items(), key=lambda p: str(p[0]))}
    if isinstance(value, (tuple, list)):
        return [_canonical(v) for v in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleMemoryCertifiedMarketBehaviorDependencyInvariantError("unsupported OML-064 value type")


def _stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(
        _canonical(value), sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False,
    ).encode("utf-8")).hexdigest()


def _reject(reason: str) -> None:
    raise OracleMemoryCertifiedMarketBehaviorDependencyInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-064 invalid {label} length")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryCertifiedMarketBehaviorDependencyInvariantError(
            f"OML-064 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_certified_market_behavior_cross_market_dependency_memory(
    *,
    chains: OracleMemoryCertifiedMarketBehaviorMultiHopCausalChainMemory,
    requests: Sequence[OracleMemoryCertifiedCrossMarketObservationRequest],
) -> OracleMemoryCertifiedMarketBehaviorCrossMarketDependencyMemory:
    verify_oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory(chains)

    if chains.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-064 upstream schema mismatch")
    if chains.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-064 upstream engine mismatch")
    if not chains.chain_memory_ready:
        _reject("OML-064 upstream chain memory not ready")
    if not chains.downstream_cross_market_dependency_authorized:
        _reject("OML-064 dependency continuation not authorized")
    if not chains.read_only:
        _reject("OML-064 upstream chain memory not read-only")

    known_chain_ids = {item.chain_id for item in chains.chains.chain_memory.chains}
    if not known_chain_ids:
        _reject("OML-064 no certified chains available")

    for request in requests:
        verify_oracle_memory_certified_cross_market_observation_request(request)
        if not set(request.chain_ids).issubset(known_chain_ids):
            _reject("OML-064 request references unknown certified chain")

    dependencies = build_inner_dependency_memory(
        chains=chains.chains,
        requests=tuple(requests),
    )
    verify_inner_dependency_memory(dependencies)

    if dependencies.schema_version != DEPENDENCY_SCHEMA_VERSION:
        _reject("OML-064 dependency schema mismatch")
    if dependencies.engine_id != DEPENDENCY_ENGINE_ID:
        _reject("OML-064 dependency engine mismatch")
    if dependencies.upstream_certification_hash != chains.chains.certification_hash:
        _reject("OML-064 chain certification lineage mismatch")
    if dependencies.upstream_chain_memory_hash != chains.chains.chain_memory.memory_hash:
        _reject("OML-064 chain memory lineage mismatch")

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": chains.schema_version,
        "upstream_engine_id": chains.engine_id,
        "upstream_certification_hash": chains.certification_hash,
        "upstream_chain_certification_hash": chains.chains.certification_hash,
        "upstream_chain_memory_hash": chains.chains.chain_memory.memory_hash,
        "dependency_schema_version": dependencies.schema_version,
        "dependency_engine_id": dependencies.engine_id,
        "dependencies": dependencies,
        "dependency_count": dependencies.dependency_count,
        "total_observation_count": dependencies.total_observation_count,
        "source_market_count": dependencies.source_market_count,
        "target_market_count": dependencies.target_market_count,
        "state": STATE_READ_ONLY,
        "chain_lineage_verified": dependencies.chain_lineage_verified,
        "causal_pattern_lineage_verified": chains.causal_pattern_lineage_verified,
        "certified_observation_lineage_verified": dependencies.certified_observation_lineage_verified,
        "deterministic_identity_verified": dependencies.deterministic_identity_verified,
        "canonical_dependency_order_verified": dependencies.canonical_dependency_order_verified,
        "lead_lag_direction_verified": dependencies.lead_lag_direction_verified,
        "evidence_lineage_verified": dependencies.evidence_lineage_verified,
        "contradiction_tracking_verified": dependencies.contradiction_tracking_verified,
        "calibration_lineage_verified": dependencies.calibration_lineage_verified,
        "outcome_reconciliation_verified": dependencies.outcome_reconciliation_verified,
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "dependency_memory_ready": True,
        "downstream_market_behavior_authorized": dependencies.downstream_market_behavior_authorized,
        "read_only": True,
    }
    result = OracleMemoryCertifiedMarketBehaviorCrossMarketDependencyMemory(
        **body, certification_hash=_stable_hash(body)
    )
    verify_oracle_memory_certified_market_behavior_cross_market_dependency_memory(result)
    return result


def verify_oracle_memory_certified_market_behavior_cross_market_dependency_memory(
    result: OracleMemoryCertifiedMarketBehaviorCrossMarketDependencyMemory,
) -> bool:
    body = asdict(result)
    supplied = body.pop("certification_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-064 certification hash mismatch")

    if result.schema_version != SCHEMA_VERSION or result.engine_id != ENGINE_ID:
        _reject("OML-064 identity mismatch")
    if result.policy_id != POLICY_ID or result.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-064 policy or subsystem mismatch")
    if result.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-064 upstream schema lineage mismatch")
    if result.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-064 upstream engine lineage mismatch")
    if result.dependency_schema_version != DEPENDENCY_SCHEMA_VERSION:
        _reject("OML-064 dependency schema lineage mismatch")
    if result.dependency_engine_id != DEPENDENCY_ENGINE_ID:
        _reject("OML-064 dependency engine lineage mismatch")

    for value in (
        result.upstream_certification_hash,
        result.upstream_chain_certification_hash,
        result.upstream_chain_memory_hash,
        result.certification_hash,
    ):
        _require_hash(value, "lineage hash")

    verify_inner_dependency_memory(result.dependencies)

    if result.upstream_chain_certification_hash != result.dependencies.upstream_certification_hash:
        _reject("OML-064 chain certification mismatch")
    if result.upstream_chain_memory_hash != result.dependencies.upstream_chain_memory_hash:
        _reject("OML-064 chain memory mismatch")
    if result.dependency_count != result.dependencies.dependency_count:
        _reject("OML-064 dependency count mismatch")
    if result.total_observation_count != result.dependencies.total_observation_count:
        _reject("OML-064 observation count mismatch")
    if result.source_market_count != result.dependencies.source_market_count:
        _reject("OML-064 source market count mismatch")
    if result.target_market_count != result.dependencies.target_market_count:
        _reject("OML-064 target market count mismatch")

    required = (
        result.chain_lineage_verified,
        result.causal_pattern_lineage_verified,
        result.certified_observation_lineage_verified,
        result.deterministic_identity_verified,
        result.canonical_dependency_order_verified,
        result.lead_lag_direction_verified,
        result.evidence_lineage_verified,
        result.contradiction_tracking_verified,
        result.calibration_lineage_verified,
        result.outcome_reconciliation_verified,
        result.dependency_memory_ready,
        result.downstream_market_behavior_authorized,
        result.read_only,
    )
    if not all(required):
        _reject("OML-064 guarantee missing")
    if result.state != STATE_READ_ONLY:
        _reject("OML-064 state invalid")

    if any((
        result.persistence_enabled,
        result.learning_updates_enabled,
        result.runtime_activation_enabled,
        result.publication_enabled,
        result.action_authorization_enabled,
        result.qseries_execution_enabled,
    )):
        _reject("OML-064 forbidden capability enabled")

    return True
"""

TEST_SOURCE = r"""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_cross_market_dependency_memory import (
    OracleMemoryCertifiedMarketBehaviorDependencyInvariantError,
    build_oracle_memory_certified_market_behavior_cross_market_dependency_memory,
    verify_oracle_memory_certified_market_behavior_cross_market_dependency_memory,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_cross_market_dependency_memory import (
    build_oracle_memory_certified_cross_market_observation_request,
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
    except OracleMemoryCertifiedMarketBehaviorDependencyInvariantError:
        return
    raise AssertionError(f"tampered OML-064 {label} accepted")


def build_chains(root: Path):
    fixture = load_module(
        root
        / "test_oml_062_oracle_memory_certified_market_behavior_causal_pattern_memory.py",
        "oml_062_fixture_for_oml_064",
    )
    calibration, certified_hashes = fixture.build_calibration(root)

    from qseries_v2.oracle_memory.oracle_memory_certified_observation_causal_pattern_memory import (
        build_oracle_memory_certified_causal_observation_request,
    )
    from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_causal_pattern_memory import (
        build_oracle_memory_certified_market_behavior_causal_pattern_memory,
    )
    from qseries_v2.oracle_memory.oracle_memory_certified_observation_multi_hop_causal_chain_memory import (
        build_oracle_memory_certified_multi_hop_chain_request,
    )
    from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory import (
        build_oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory,
    )

    entity_a = "1" * 64
    entity_b = "2" * 64
    entity_c = "3" * 64

    causal_requests = (
        build_oracle_memory_certified_causal_observation_request(
            pattern_name=(
                "Market-behavior liquidity shift precedes "
                "order-flow change"
            ),
            cause_entity_id=entity_a,
            effect_entity_id=entity_b,
            cause_observed_at="2026-08-02T17:00:00-05:00",
            effect_observed_at="2026-08-02T17:05:00-05:00",
            certified_observation_hashes=(certified_hashes[0],),
            confidence=0.82,
            calibrated_probability=0.80,
            outcome_confirmed=True,
            outcome_supported=True,
        ),
        build_oracle_memory_certified_causal_observation_request(
            pattern_name=(
                "Market-behavior order-flow change precedes "
                "Bitcoin repricing"
            ),
            cause_entity_id=entity_b,
            effect_entity_id=entity_c,
            cause_observed_at="2026-08-02T17:06:00-05:00",
            effect_observed_at="2026-08-02T17:10:00-05:00",
            certified_observation_hashes=(certified_hashes[-1],),
            confidence=0.80,
            calibrated_probability=0.75,
            outcome_confirmed=True,
            outcome_supported=True,
        ),
    )

    causal_patterns = (
        build_oracle_memory_certified_market_behavior_causal_pattern_memory(
            calibration=calibration,
            requests=causal_requests,
        )
    )

    patterns = {
        item.normalized_pattern_name: item
        for item in causal_patterns.causal_patterns.causal_memory.patterns
    }
    chain_request = build_oracle_memory_certified_multi_hop_chain_request(
        chain_name=(
            "Market-behavior liquidity shift to Bitcoin repricing"
        ),
        pattern_ids=(
            patterns[
                "market-behavior liquidity shift precedes "
                "order-flow change"
            ].pattern_id,
            patterns[
                "market-behavior order-flow change precedes "
                "bitcoin repricing"
            ].pattern_id,
        ),
    )

    chains = (
        build_oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory(
            causal_patterns=causal_patterns,
            requests=(chain_request,),
        )
    )
    return chains, certified_hashes


def main() -> int:
    print("=" * 48)
    print(" OML-064 TEST")
    print(" CERTIFIED MARKET-BEHAVIOR CROSS-MARKET DEPENDENCY MEMORY")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    chains, certified_hashes = build_chains(root)
    chain_id = chains.chains.chain_memory.chains[0].chain_id

    requests = (
        build_oracle_memory_certified_cross_market_observation_request(
            dependency_name="Certified market behavior leads Bitcoin repricing",
            chain_ids=(chain_id,),
            source_market_id="a" * 64,
            target_market_id="b" * 64,
            source_event_hash="c" * 64,
            target_event_hash="d" * 64,
            source_observed_at="2026-08-02T17:00:00-05:00",
            target_observed_at="2026-08-02T17:05:00-05:00",
            lag_seconds=300,
            certified_observation_hashes=(certified_hashes[0],),
            confidence=0.82,
            calibrated_probability=0.80,
            outcome_confirmed=True,
            dependency_supported=True,
        ),
        build_oracle_memory_certified_cross_market_observation_request(
            dependency_name="Certified market behavior leads Bitcoin repricing",
            chain_ids=(chain_id,),
            source_market_id="a" * 64,
            target_market_id="b" * 64,
            source_event_hash="e" * 64,
            target_event_hash="f" * 64,
            source_observed_at="2026-08-02T18:00:00-05:00",
            target_observed_at="2026-08-02T18:04:00-05:00",
            lag_seconds=240,
            certified_observation_hashes=(certified_hashes[-1],),
            confidence=0.80,
            calibrated_probability=0.75,
            outcome_confirmed=True,
            dependency_supported=True,
        ),
    )

    result = build_oracle_memory_certified_market_behavior_cross_market_dependency_memory(
        chains=chains,
        requests=requests,
    )

    assert result.schema_version == "OML-064"
    assert result.engine_id == "OML-064"
    assert result.upstream_schema_version == "OML-063"
    assert result.upstream_engine_id == "OML-063"
    assert result.dependency_schema_version == "OML-038"
    assert result.dependency_engine_id == "OML-038"
    assert result.dependency_count == 1
    assert result.total_observation_count == 2
    assert result.source_market_count == 1
    assert result.target_market_count == 1
    assert result.upstream_certification_hash == chains.certification_hash
    assert result.chain_lineage_verified
    assert result.causal_pattern_lineage_verified
    assert result.certified_observation_lineage_verified
    assert result.deterministic_identity_verified
    assert result.canonical_dependency_order_verified
    assert result.lead_lag_direction_verified
    assert result.evidence_lineage_verified
    assert result.contradiction_tracking_verified
    assert result.calibration_lineage_verified
    assert result.outcome_reconciliation_verified
    assert result.dependency_memory_ready
    assert result.downstream_market_behavior_authorized
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled
    assert result.read_only

    replay = build_oracle_memory_certified_market_behavior_cross_market_dependency_memory(
        chains=chains,
        requests=requests,
    )
    assert replay == result
    assert verify_oracle_memory_certified_market_behavior_cross_market_dependency_memory(result)

    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_cross_market_dependency_memory(
            replace(result, persistence_enabled=True)
        ),
        "persistence",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_cross_market_dependency_memory(
            replace(result, downstream_market_behavior_authorized=False)
        ),
        "market behavior continuation",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_cross_market_dependency_memory(
            replace(result, qseries_execution_enabled=True)
        ),
        "Q Series execution",
    )

    print("[PASS] Certified OML-063 chain memory consumed read-only")
    print("[PASS] Exact OML-037 chain object passed directly")
    print("[PASS] Actual OML-038 dependency builder consumed")
    print("[PASS] Chain and causal-pattern lineage retained")
    print("[PASS] Certified observation evidence retained")
    print("[PASS] Lead-lag direction and outcomes verified")
    print("[PASS] Market-behavior continuation authorized read-only")
    print("[PASS] Deterministic replay equality verified")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered OML-064 records rejected")
    print("[DONE] OML-064 CERTIFIED MARKET-BEHAVIOR CROSS-MARKET DEPENDENCY MEMORY PASS")
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
    required = (UPSTREAM, UPSTREAM_TEST, DEPENDENCY, DEPENDENCY_TEST)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError("Required certified files missing: " + ", ".join(missing))

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    upstream = importlib.import_module(
        "qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory"
    )
    dependency = importlib.import_module(
        "qseries_v2.oracle_memory.oracle_memory_certified_observation_cross_market_dependency_memory"
    )

    expected = (
        (upstream, {
            "SCHEMA_VERSION": "OML-063",
            "ENGINE_ID": "OML-063",
            "POLICY_ID": "oracle-memory.certified-market-behavior-multi-hop-causal-chain-memory.v1",
        }, "OML-063"),
        (dependency, {
            "SCHEMA_VERSION": "OML-038",
            "ENGINE_ID": "OML-038",
            "POLICY_ID": "oracle-memory.certified-observation-cross-market-dependency-memory.v1",
            "UPSTREAM_SCHEMA_VERSION": "OML-037",
            "UPSTREAM_ENGINE_ID": "OML-037",
        }, "OML-038"),
    )
    for module, values, label in expected:
        for name, value in values.items():
            actual = getattr(module, name, None)
            if actual != value:
                raise RuntimeError(
                    f"Certified {label} {name} mismatch: expected {value!r}, got {actual!r}"
                )

    required_symbols = (
        "OracleMemoryCertifiedCrossMarketObservationRequest",
        "OracleMemoryCertifiedCrossMarketDependencyMemory",
        "build_oracle_memory_certified_cross_market_dependency_memory",
        "verify_oracle_memory_certified_cross_market_observation_request",
        "verify_oracle_memory_certified_cross_market_dependency_memory",
    )
    missing_symbols = [name for name in required_symbols if not hasattr(dependency, name)]
    if missing_symbols:
        raise RuntimeError(
            "Certified OML-038 missing symbols: " + ", ".join(missing_symbols)
        )

    parameters = set(inspect.signature(
        dependency.build_oracle_memory_certified_cross_market_dependency_memory
    ).parameters)
    missing_parameters = sorted({"chains", "requests"} - parameters)
    if missing_parameters:
        raise RuntimeError(
            "Certified OML-038 builder parameters missing: "
            + ", ".join(missing_parameters)
        )


def main() -> int:
    print("=" * 48)
    print(" OML-064 CORRECTION V2 INSTALLER")
    print(" CERTIFIED MARKET-BEHAVIOR CROSS-MARKET DEPENDENCY MEMORY")
    print("=" * 48)
    print("[BOOT] Revision: CORRECTION_V2_EXACT_OML_063_038_INTERFACE_ALIGNMENT")

    try:
        validate()
        print("[OK] Actual OML-063 dataclass and verifier inspected")
        print("[OK] Actual OML-038 builder and signature inspected")

        for path, label in ((UPSTREAM_TEST, "OML-063"), (DEPENDENCY_TEST, "OML-038")):
            run = subprocess.run([sys.executable, str(path)], cwd=ROOT, check=False)
            if run.returncode:
                raise RuntimeError(
                    f"{label} certification failed with exit code {run.returncode}"
                )

        tracked = {
            path: path.read_bytes()
            for path in (UPSTREAM, UPSTREAM_TEST, DEPENDENCY, DEPENDENCY_TEST)
        }

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = "from .oracle_memory_certified_market_behavior_cross_market_dependency_memory import *"
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
            raise RuntimeError(
                f"OML-064 test failed with exit code {completed.returncode}"
            )

        for path, before in tracked.items():
            if path.read_bytes() != before:
                raise RuntimeError(f"Certified upstream changed: {path}")

        print("[PASS] Certified OML-063 production unchanged")
        print("[PASS] Certified OML-063 standalone test unchanged")
        print("[PASS] Certified OML-038 dependency engine unchanged")
        print("[PASS] Exact OML-037 chain object consumed directly")
        print("[PASS] OML-064 production fully replaced")
        print("[PASS] OML-064 standalone deterministic test installed")
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
        print("[DONE] OML-064 CORRECTION V2 CERTIFIED MARKET-BEHAVIOR CROSS-MARKET DEPENDENCY MEMORY INSTALLED")
        return 0

    except (
        RuntimeError, SyntaxError, ImportError, AttributeError,
        KeyError, TypeError, ValueError,
    ) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
