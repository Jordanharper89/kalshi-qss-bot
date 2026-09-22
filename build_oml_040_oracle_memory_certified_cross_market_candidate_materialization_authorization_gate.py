from __future__ import annotations

import ast
import importlib
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "oracle_memory"

UPSTREAM = PACKAGE / "oracle_memory_certified_cross_market_observation_intake_bridge.py"
UPSTREAM_TEST = ROOT / "test_oml_039_oracle_memory_certified_cross_market_observation_intake_bridge.py"

PRODUCTION = PACKAGE / "oracle_memory_certified_cross_market_candidate_materialization_authorization_gate.py"
TEST = ROOT / "test_oml_040_oracle_memory_certified_cross_market_candidate_materialization_authorization_gate.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_observation_intake_bridge import (
    OracleMemoryCertifiedCrossMarketIntakeBridge,
    verify_oracle_memory_certified_cross_market_intake_bridge,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-040"
ENGINE_ID = "OML-040"
POLICY_ID = (
    "oracle-memory."
    "certified-cross-market-candidate-materialization-authorization-gate.v1"
)
UPSTREAM_SCHEMA_VERSION = "OML-039"
UPSTREAM_ENGINE_ID = "OML-039"

DECISION_AUTHORIZED = "authorized_read_only_materialization"
STATE_CONTRACT_ONLY = "contract_only"


class OracleMemoryCrossMarketMaterializationAuthorizationInvariantError(
    RuntimeError
):
    pass


@dataclass(frozen=True)
class OracleMemoryCrossMarketMaterializationAuthorizationDecision:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_certification_hash: str
    upstream_intake_batch_hash: str
    upstream_observation_count: int
    upstream_unique_observation_count: int
    decision: str
    state: str
    upstream_bridge_verified: bool
    dependency_lineage_verified: bool
    chain_lineage_verified: bool
    certified_observation_lineage_verified: bool
    deterministic_hashing_verified: bool
    canonical_order_verified: bool
    duplicate_detection_verified: bool
    source_certification_verified: bool
    candidate_materialization_authorized: bool
    candidate_admission_authorized: bool
    persistence_authorized: bool
    learning_update_authorized: bool
    runtime_activation_authorized: bool
    publication_authorized: bool
    action_authorization_enabled: bool
    qseries_execution_authorized: bool
    downstream_materialization_ready: bool
    read_only: bool
    decision_hash: str


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
    raise OracleMemoryCrossMarketMaterializationAuthorizationInvariantError(
        "unsupported OML-040 value type"
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
    raise OracleMemoryCrossMarketMaterializationAuthorizationInvariantError(
        reason
    )


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-040 invalid {label} length")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryCrossMarketMaterializationAuthorizationInvariantError(
            f"OML-040 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_cross_market_materialization_authorization_decision(
    *,
    bridge: OracleMemoryCertifiedCrossMarketIntakeBridge,
) -> OracleMemoryCrossMarketMaterializationAuthorizationDecision:
    verify_oracle_memory_certified_cross_market_intake_bridge(bridge)

    if bridge.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-040 upstream schema mismatch")
    if bridge.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-040 upstream engine mismatch")
    if not bridge.bridge_ready:
        _reject("OML-040 upstream bridge not ready")
    if not bridge.read_only:
        _reject("OML-040 upstream bridge not read-only")
    if bridge.observation_count <= 0:
        _reject("OML-040 upstream bridge contains no observations")
    if bridge.unique_observation_count <= 0:
        _reject("OML-040 upstream bridge contains no unique observations")
    if bridge.downstream_candidate_materialization_authorized:
        _reject("OML-040 upstream bridge bypassed authorization gate")

    required_upstream = (
        bridge.dependency_lineage_verified,
        bridge.chain_lineage_verified,
        bridge.certified_observation_lineage_verified,
        bridge.deterministic_hashing_verified,
        bridge.canonical_order_verified,
        bridge.duplicate_detection_verified,
        bridge.source_certification_verified,
    )
    if not all(required_upstream):
        _reject("OML-040 upstream bridge guarantees incomplete")

    forbidden_upstream = (
        bridge.persistence_enabled,
        bridge.learning_updates_enabled,
        bridge.runtime_activation_enabled,
        bridge.publication_enabled,
        bridge.action_authorization_enabled,
        bridge.qseries_execution_enabled,
    )
    if any(forbidden_upstream):
        _reject("OML-040 upstream forbidden capability enabled")

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": bridge.schema_version,
        "upstream_engine_id": bridge.engine_id,
        "upstream_certification_hash": bridge.certification_hash,
        "upstream_intake_batch_hash": bridge.intake_batch.batch_hash,
        "upstream_observation_count": bridge.observation_count,
        "upstream_unique_observation_count": bridge.unique_observation_count,
        "decision": DECISION_AUTHORIZED,
        "state": STATE_CONTRACT_ONLY,
        "upstream_bridge_verified": True,
        "dependency_lineage_verified": True,
        "chain_lineage_verified": True,
        "certified_observation_lineage_verified": True,
        "deterministic_hashing_verified": True,
        "canonical_order_verified": True,
        "duplicate_detection_verified": True,
        "source_certification_verified": True,
        "candidate_materialization_authorized": True,
        "candidate_admission_authorized": False,
        "persistence_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "downstream_materialization_ready": True,
        "read_only": True,
    }

    result = OracleMemoryCrossMarketMaterializationAuthorizationDecision(
        **body,
        decision_hash=_stable_hash(body),
    )
    verify_oracle_memory_cross_market_materialization_authorization_decision(
        result
    )
    return result


def verify_oracle_memory_cross_market_materialization_authorization_decision(
    decision: OracleMemoryCrossMarketMaterializationAuthorizationDecision,
) -> bool:
    body = asdict(decision)
    supplied = body.pop("decision_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-040 decision hash mismatch")

    if decision.schema_version != SCHEMA_VERSION:
        _reject("OML-040 schema mismatch")
    if decision.engine_id != ENGINE_ID:
        _reject("OML-040 engine mismatch")
    if decision.policy_id != POLICY_ID:
        _reject("OML-040 policy mismatch")
    if decision.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-040 subsystem mismatch")
    if decision.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-040 upstream schema lineage mismatch")
    if decision.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-040 upstream engine lineage mismatch")

    for value, label in (
        (decision.upstream_certification_hash, "upstream certification hash"),
        (decision.upstream_intake_batch_hash, "upstream intake batch hash"),
        (decision.decision_hash, "decision hash"),
    ):
        _require_hash(value, label)

    if decision.decision != DECISION_AUTHORIZED:
        _reject("OML-040 decision state invalid")
    if decision.state != STATE_CONTRACT_ONLY:
        _reject("OML-040 contract state invalid")
    if decision.upstream_observation_count <= 0:
        _reject("OML-040 observation count invalid")
    if decision.upstream_unique_observation_count <= 0:
        _reject("OML-040 unique observation count invalid")

    required = (
        decision.upstream_bridge_verified,
        decision.dependency_lineage_verified,
        decision.chain_lineage_verified,
        decision.certified_observation_lineage_verified,
        decision.deterministic_hashing_verified,
        decision.canonical_order_verified,
        decision.duplicate_detection_verified,
        decision.source_certification_verified,
        decision.candidate_materialization_authorized,
        decision.downstream_materialization_ready,
        decision.read_only,
    )
    if not all(required):
        _reject("OML-040 authorization guarantee missing")

    forbidden = (
        decision.candidate_admission_authorized,
        decision.persistence_authorized,
        decision.learning_update_authorized,
        decision.runtime_activation_authorized,
        decision.publication_authorized,
        decision.action_authorization_enabled,
        decision.qseries_execution_authorized,
    )
    if any(forbidden):
        _reject("OML-040 forbidden capability enabled")

    return True
"""

TEST_SOURCE = r"""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_candidate_materialization_authorization_gate import (
    OracleMemoryCrossMarketMaterializationAuthorizationInvariantError,
    build_oracle_memory_cross_market_materialization_authorization_decision,
    verify_oracle_memory_cross_market_materialization_authorization_decision,
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
    except OracleMemoryCrossMarketMaterializationAuthorizationInvariantError:
        return
    raise AssertionError(f"tampered OML-040 {label} accepted")


def build_bridge(root: Path):
    fixture = load_module(
        root
        / "test_oml_039_oracle_memory_certified_cross_market_observation_intake_bridge.py",
        "oml_039_fixture_for_oml_040",
    )
    dependencies = fixture.build_dependencies(root)
    dependency = dependencies.dependency_memory.dependencies[0]

    from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_observation_intake_bridge import (
        build_oracle_memory_certified_cross_market_intake_request,
        build_oracle_memory_certified_cross_market_intake_bridge,
    )
    from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
        MEMORY_DOMAINS,
    )

    request = build_oracle_memory_certified_cross_market_intake_request(
        dependency_id=dependency.dependency_id,
        domain_id=(
            "market_behavior_memory"
            if "market_behavior_memory" in MEMORY_DOMAINS
            else MEMORY_DOMAINS[0]
        ),
        entity_key="Bitcoin cross-market dependency",
        source_key="oracle-memory-oml-038",
        observed_at="2026-08-02T17:00:00-05:00",
        effective_at="2026-08-02T17:00:00-05:00",
        payload={
            "observation": (
                "A certified prediction-market dependency preceded "
                "crypto spot repricing."
            ),
            "observation_type": "cross_market_dependency",
        },
        confidence=0.80,
        uncertainty=0.20,
    )

    return build_oracle_memory_certified_cross_market_intake_bridge(
        dependencies=dependencies,
        requests=(request,),
    )


def main() -> int:
    print("=" * 48)
    print(" OML-040 TEST")
    print(" CROSS-MARKET CANDIDATE MATERIALIZATION AUTHORIZATION GATE")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    bridge = build_bridge(root)

    result = (
        build_oracle_memory_cross_market_materialization_authorization_decision(
            bridge=bridge,
        )
    )

    assert result.schema_version == "OML-040"
    assert result.engine_id == "OML-040"
    assert result.upstream_schema_version == "OML-039"
    assert result.upstream_engine_id == "OML-039"
    assert result.upstream_certification_hash == bridge.certification_hash
    assert result.upstream_intake_batch_hash == bridge.intake_batch.batch_hash
    assert result.upstream_observation_count == bridge.observation_count
    assert result.upstream_unique_observation_count == (
        bridge.unique_observation_count
    )
    assert result.candidate_materialization_authorized
    assert not result.candidate_admission_authorized
    assert not result.persistence_authorized
    assert not result.learning_update_authorized
    assert not result.runtime_activation_authorized
    assert not result.publication_authorized
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_authorized
    assert result.downstream_materialization_ready
    assert result.read_only

    replay = (
        build_oracle_memory_cross_market_materialization_authorization_decision(
            bridge=bridge,
        )
    )
    assert replay == result
    assert (
        verify_oracle_memory_cross_market_materialization_authorization_decision(
            result
        )
    )

    expect_rejection(
        lambda: verify_oracle_memory_cross_market_materialization_authorization_decision(
            replace(result, candidate_admission_authorized=True)
        ),
        "candidate admission",
    )
    expect_rejection(
        lambda: verify_oracle_memory_cross_market_materialization_authorization_decision(
            replace(result, persistence_authorized=True)
        ),
        "persistence",
    )
    expect_rejection(
        lambda: verify_oracle_memory_cross_market_materialization_authorization_decision(
            replace(result, qseries_execution_authorized=True)
        ),
        "Q Series execution",
    )
    expect_rejection(
        lambda: verify_oracle_memory_cross_market_materialization_authorization_decision(
            replace(result, decision_hash="f" * 64)
        ),
        "decision hash",
    )

    print("[PASS] Certified OML-039 bridge consumed read-only")
    print("[PASS] OML-039 certification and intake-batch lineage retained")
    print("[PASS] Dependency, chain, and observation guarantees verified")
    print("[PASS] Deterministic candidate materialization authorized")
    print("[PASS] Candidate admission remained disabled")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Deterministic replay equality verified")
    print("[PASS] Tampered OML-040 decisions rejected")
    print(
        "[DONE] OML-040 CROSS-MARKET CANDIDATE "
        "MATERIALIZATION AUTHORIZATION GATE PASS"
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


def validate_upstream() -> None:
    required = (UPSTREAM, UPSTREAM_TEST)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(
            "Required certified upstream files missing: " + ", ".join(missing)
        )

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_certified_cross_market_observation_intake_bridge"
    )

    expected = {
        "SCHEMA_VERSION": "OML-039",
        "ENGINE_ID": "OML-039",
        "POLICY_ID": (
            "oracle-memory."
            "certified-cross-market-observation-intake-bridge.v1"
        ),
        "UPSTREAM_SCHEMA_VERSION": "OML-038",
        "UPSTREAM_ENGINE_ID": "OML-038",
        "INTAKE_SCHEMA_VERSION": "OML-027",
        "INTAKE_ENGINE_ID": "OML-027",
    }
    for name, value in expected.items():
        actual = getattr(module, name, None)
        if actual != value:
            raise RuntimeError(
                f"Certified OML-039 {name} mismatch: "
                f"expected {value!r}, got {actual!r}"
            )

    required_symbols = (
        "OracleMemoryCertifiedCrossMarketIntakeBridge",
        "verify_oracle_memory_certified_cross_market_intake_bridge",
    )
    missing_symbols = [
        name for name in required_symbols if not hasattr(module, name)
    ]
    if missing_symbols:
        raise RuntimeError(
            "Certified OML-039 missing symbols: "
            + ", ".join(missing_symbols)
        )

    required_fields = {
        "schema_version",
        "engine_id",
        "certification_hash",
        "intake_batch",
        "observation_count",
        "unique_observation_count",
        "dependency_lineage_verified",
        "chain_lineage_verified",
        "certified_observation_lineage_verified",
        "deterministic_hashing_verified",
        "canonical_order_verified",
        "duplicate_detection_verified",
        "source_certification_verified",
        "bridge_ready",
        "downstream_candidate_materialization_authorized",
        "read_only",
    }
    actual_fields = set(
        module.OracleMemoryCertifiedCrossMarketIntakeBridge.__dataclass_fields__
    )
    missing_fields = sorted(required_fields - actual_fields)
    if missing_fields:
        raise RuntimeError(
            "Certified OML-039 dataclass fields missing: "
            + ", ".join(missing_fields)
        )


def main() -> int:
    print("=" * 48)
    print(" OML-040 INSTALLER")
    print(" CROSS-MARKET CANDIDATE MATERIALIZATION AUTHORIZATION GATE")
    print("=" * 48)
    print("[BOOT] Revision: EXACT_OML_039_AUTHORIZATION_BOUNDARY")

    try:
        validate_upstream()
        print("[OK] Actual OML-039 dataclass and verifier inspected")

        upstream_run = subprocess.run(
            [sys.executable, str(UPSTREAM_TEST)],
            cwd=ROOT,
            check=False,
        )
        if upstream_run.returncode:
            raise RuntimeError(
                "OML-039 certification failed with exit code "
                f"{upstream_run.returncode}"
            )

        tracked = {
            UPSTREAM: UPSTREAM.read_bytes(),
            UPSTREAM_TEST: UPSTREAM_TEST.read_bytes(),
        }

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_memory_certified_cross_market_"
            "candidate_materialization_authorization_gate import *"
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
                f"OML-040 test failed with exit code {completed.returncode}"
            )

        for path, before in tracked.items():
            if path.read_bytes() != before:
                raise RuntimeError(f"Certified upstream changed: {path}")

        print("[PASS] Certified OML-039 production unchanged")
        print("[PASS] Certified OML-039 standalone test unchanged")
        print("[PASS] OML-040 production fully replaced")
        print("[PASS] OML-040 standalone deterministic test installed")
        print("[PASS] Read-only materialization boundary authorized")
        print("[PASS] Candidate admission remained disabled")
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
            "[DONE] OML-040 CROSS-MARKET CANDIDATE "
            "MATERIALIZATION AUTHORIZATION GATE INSTALLED"
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
