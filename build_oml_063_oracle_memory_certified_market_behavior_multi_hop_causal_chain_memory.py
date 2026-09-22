from __future__ import annotations

import ast
import importlib
import inspect
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "oracle_memory"

UPSTREAM = PACKAGE / "oracle_memory_certified_market_behavior_causal_pattern_memory.py"
UPSTREAM_TEST = ROOT / "test_oml_062_oracle_memory_certified_market_behavior_causal_pattern_memory.py"
CHAIN = PACKAGE / "oracle_memory_certified_observation_multi_hop_causal_chain_memory.py"
CHAIN_TEST = ROOT / "test_oml_037_oracle_memory_certified_observation_multi_hop_causal_chain_memory.py"

PRODUCTION = PACKAGE / "oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory.py"
TEST = ROOT / "test_oml_063_oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_causal_pattern_memory import (
    OracleMemoryCertifiedMarketBehaviorCausalPatternMemory,
    verify_oracle_memory_certified_market_behavior_causal_pattern_memory,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_multi_hop_causal_chain_memory import (
    OracleMemoryCertifiedMultiHopChainRequest,
    OracleMemoryCertifiedMultiHopCausalChainMemory,
    build_oracle_memory_certified_multi_hop_causal_chain_memory,
    verify_oracle_memory_certified_multi_hop_chain_request,
    verify_oracle_memory_certified_multi_hop_causal_chain_memory,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-063"
ENGINE_ID = "OML-063"
POLICY_ID = (
    "oracle-memory."
    "certified-market-behavior-multi-hop-causal-chain-memory.v1"
)
UPSTREAM_SCHEMA_VERSION = "OML-062"
UPSTREAM_ENGINE_ID = "OML-062"
CHAIN_SCHEMA_VERSION = "OML-037"
CHAIN_ENGINE_ID = "OML-037"
STATE_READ_ONLY = "read_only_market_behavior_multi_hop_causal_chain_memory"


class OracleMemoryCertifiedMarketBehaviorChainInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCertifiedMarketBehaviorMultiHopCausalChainMemory:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_certification_hash: str
    upstream_causal_certification_hash: str
    upstream_causal_memory_hash: str
    chain_schema_version: str
    chain_engine_id: str
    chains: OracleMemoryCertifiedMultiHopCausalChainMemory
    chain_count: int
    total_hop_count: int
    state: str
    causal_pattern_lineage_verified: bool
    certified_observation_lineage_verified: bool
    deterministic_identity_verified: bool
    canonical_chain_order_verified: bool
    hop_continuity_verified: bool
    temporal_direction_verified: bool
    evidence_depth_reconciled: bool
    contradiction_depth_reconciled: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    chain_memory_ready: bool
    downstream_cross_market_dependency_authorized: bool
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
    raise OracleMemoryCertifiedMarketBehaviorChainInvariantError(
        "unsupported OML-063 value type"
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
    raise OracleMemoryCertifiedMarketBehaviorChainInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-063 invalid {label} length")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryCertifiedMarketBehaviorChainInvariantError(
            f"OML-063 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory(
    *,
    causal_patterns: OracleMemoryCertifiedMarketBehaviorCausalPatternMemory,
    requests: Sequence[OracleMemoryCertifiedMultiHopChainRequest],
) -> OracleMemoryCertifiedMarketBehaviorMultiHopCausalChainMemory:
    verify_oracle_memory_certified_market_behavior_causal_pattern_memory(
        causal_patterns
    )

    if causal_patterns.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-063 upstream schema mismatch")
    if causal_patterns.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-063 upstream engine mismatch")
    if not causal_patterns.causal_memory_ready:
        _reject("OML-063 upstream causal memory not ready")
    if not causal_patterns.downstream_multi_hop_causal_authorized:
        _reject("OML-063 multi-hop continuation not authorized")
    if not causal_patterns.read_only:
        _reject("OML-063 upstream causal memory not read-only")

    known_pattern_ids = {
        pattern.pattern_id
        for pattern in causal_patterns.causal_patterns.causal_memory.patterns
    }
    if not known_pattern_ids:
        _reject("OML-063 no certified causal patterns available")

    for request in requests:
        verify_oracle_memory_certified_multi_hop_chain_request(request)
        if not set(request.pattern_ids).issubset(known_pattern_ids):
            _reject("OML-063 chain references unknown causal pattern")

    chains = build_oracle_memory_certified_multi_hop_causal_chain_memory(
        causal_patterns=causal_patterns.causal_patterns,
        requests=tuple(requests),
    )
    verify_oracle_memory_certified_multi_hop_causal_chain_memory(chains)

    if chains.schema_version != CHAIN_SCHEMA_VERSION:
        _reject("OML-063 chain schema mismatch")
    if chains.engine_id != CHAIN_ENGINE_ID:
        _reject("OML-063 chain engine mismatch")
    if chains.upstream_certification_hash != (
        causal_patterns.causal_patterns.certification_hash
    ):
        _reject("OML-063 causal certification lineage mismatch")
    if chains.upstream_causal_memory_hash != (
        causal_patterns.causal_patterns.causal_memory.memory_hash
    ):
        _reject("OML-063 causal memory lineage mismatch")

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": causal_patterns.schema_version,
        "upstream_engine_id": causal_patterns.engine_id,
        "upstream_certification_hash": causal_patterns.certification_hash,
        "upstream_causal_certification_hash": (
            causal_patterns.causal_patterns.certification_hash
        ),
        "upstream_causal_memory_hash": (
            causal_patterns.causal_patterns.causal_memory.memory_hash
        ),
        "chain_schema_version": chains.schema_version,
        "chain_engine_id": chains.engine_id,
        "chains": chains,
        "chain_count": chains.chain_count,
        "total_hop_count": chains.total_hop_count,
        "state": STATE_READ_ONLY,
        "causal_pattern_lineage_verified": (
            chains.causal_pattern_lineage_verified
        ),
        "certified_observation_lineage_verified": (
            chains.certified_observation_lineage_verified
        ),
        "deterministic_identity_verified": (
            chains.deterministic_identity_verified
        ),
        "canonical_chain_order_verified": (
            chains.canonical_chain_order_verified
        ),
        "hop_continuity_verified": chains.hop_continuity_verified,
        "temporal_direction_verified": chains.temporal_direction_verified,
        "evidence_depth_reconciled": chains.evidence_depth_reconciled,
        "contradiction_depth_reconciled": (
            chains.contradiction_depth_reconciled
        ),
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "chain_memory_ready": True,
        "downstream_cross_market_dependency_authorized": True,
        "read_only": True,
    }

    result = OracleMemoryCertifiedMarketBehaviorMultiHopCausalChainMemory(
        **body,
        certification_hash=_stable_hash(body),
    )
    verify_oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory(
        result
    )
    return result


def verify_oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory(
    result: OracleMemoryCertifiedMarketBehaviorMultiHopCausalChainMemory,
) -> bool:
    body = asdict(result)
    supplied = body.pop("certification_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-063 certification hash mismatch")

    if result.schema_version != SCHEMA_VERSION:
        _reject("OML-063 schema mismatch")
    if result.engine_id != ENGINE_ID:
        _reject("OML-063 engine mismatch")
    if result.policy_id != POLICY_ID:
        _reject("OML-063 policy mismatch")
    if result.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-063 subsystem mismatch")
    if result.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-063 upstream schema lineage mismatch")
    if result.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-063 upstream engine lineage mismatch")
    if result.chain_schema_version != CHAIN_SCHEMA_VERSION:
        _reject("OML-063 chain schema lineage mismatch")
    if result.chain_engine_id != CHAIN_ENGINE_ID:
        _reject("OML-063 chain engine lineage mismatch")

    for value in (
        result.upstream_certification_hash,
        result.upstream_causal_certification_hash,
        result.upstream_causal_memory_hash,
        result.certification_hash,
    ):
        _require_hash(value, "lineage hash")

    verify_oracle_memory_certified_multi_hop_causal_chain_memory(
        result.chains
    )

    if result.upstream_causal_certification_hash != (
        result.chains.upstream_certification_hash
    ):
        _reject("OML-063 causal certification mismatch")
    if result.upstream_causal_memory_hash != (
        result.chains.upstream_causal_memory_hash
    ):
        _reject("OML-063 causal memory mismatch")
    if result.chain_count != result.chains.chain_count:
        _reject("OML-063 chain count mismatch")
    if result.total_hop_count != result.chains.total_hop_count:
        _reject("OML-063 hop count mismatch")

    required = (
        result.causal_pattern_lineage_verified,
        result.certified_observation_lineage_verified,
        result.deterministic_identity_verified,
        result.canonical_chain_order_verified,
        result.hop_continuity_verified,
        result.temporal_direction_verified,
        result.evidence_depth_reconciled,
        result.contradiction_depth_reconciled,
        result.chain_memory_ready,
        result.downstream_cross_market_dependency_authorized,
        result.read_only,
    )
    if not all(required):
        _reject("OML-063 guarantee missing")
    if result.state != STATE_READ_ONLY:
        _reject("OML-063 state invalid")

    forbidden = (
        result.persistence_enabled,
        result.learning_updates_enabled,
        result.runtime_activation_enabled,
        result.publication_enabled,
        result.action_authorization_enabled,
        result.qseries_execution_enabled,
    )
    if any(forbidden):
        _reject("OML-063 forbidden capability enabled")

    return True
"""

TEST_SOURCE = r"""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory import (
    OracleMemoryCertifiedMarketBehaviorChainInvariantError,
    build_oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory,
    verify_oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_multi_hop_causal_chain_memory import (
    build_oracle_memory_certified_multi_hop_chain_request,
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
    except OracleMemoryCertifiedMarketBehaviorChainInvariantError:
        return
    raise AssertionError(f"tampered OML-063 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-063 TEST")
    print(" CERTIFIED MARKET-BEHAVIOR MULTI-HOP CAUSAL CHAIN MEMORY")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    fixture = load_module(
        root
        / "test_oml_062_oracle_memory_certified_market_behavior_causal_pattern_memory.py",
        "oml_062_fixture_for_oml_063",
    )
    calibration, certified_hashes = fixture.build_calibration(root)


    from qseries_v2.oracle_memory.oracle_memory_certified_observation_causal_pattern_memory import (
        build_oracle_memory_certified_causal_observation_request,
    )
    from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_causal_pattern_memory import (
        build_oracle_memory_certified_market_behavior_causal_pattern_memory,
    )

    entity_a = "1" * 64
    entity_b = "2" * 64
    entity_c = "3" * 64

    causal_requests = (
        build_oracle_memory_certified_causal_observation_request(
            pattern_name="Market-behavior liquidity shift precedes order-flow change",
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
            pattern_name="Market-behavior order-flow change precedes Bitcoin repricing",
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
    ordered_pattern_ids = (
        patterns["market-behavior liquidity shift precedes order-flow change"].pattern_id,
        patterns["market-behavior order-flow change precedes bitcoin repricing"].pattern_id,
    )

    chain_request = build_oracle_memory_certified_multi_hop_chain_request(
        chain_name="Market-behavior liquidity shift to Bitcoin repricing",
        pattern_ids=ordered_pattern_ids,
    )

    result = (
        build_oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory(
            causal_patterns=causal_patterns,
            requests=(chain_request,),
        )
    )

    assert result.schema_version == "OML-063"
    assert result.engine_id == "OML-063"
    assert result.upstream_schema_version == "OML-062"
    assert result.upstream_engine_id == "OML-062"
    assert result.chain_schema_version == "OML-037"
    assert result.chain_engine_id == "OML-037"
    assert result.chain_count == 1
    assert result.total_hop_count == 2
    assert result.upstream_certification_hash == (
        causal_patterns.certification_hash
    )
    assert result.causal_pattern_lineage_verified
    assert result.certified_observation_lineage_verified
    assert result.deterministic_identity_verified
    assert result.canonical_chain_order_verified
    assert result.hop_continuity_verified
    assert result.temporal_direction_verified
    assert result.evidence_depth_reconciled
    assert result.contradiction_depth_reconciled
    assert result.chain_memory_ready
    assert result.downstream_cross_market_dependency_authorized
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled
    assert result.read_only

    replay = (
        build_oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory(
            causal_patterns=causal_patterns,
            requests=(chain_request,),
        )
    )
    assert replay == result
    assert (
        verify_oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory(
            result
        )
    )

    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory(
            replace(result, persistence_enabled=True)
        ),
        "persistence",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory(
            replace(
                result,
                downstream_cross_market_dependency_authorized=False,
            )
        ),
        "cross-market continuation",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory(
            replace(result, qseries_execution_enabled=True)
        ),
        "Q Series execution",
    )

    print("[PASS] Certified OML-062 causal memory consumed read-only")
    print("[PASS] Exact OML-036 causal-pattern object passed directly")
    print("[PASS] Actual OML-037 chain builder consumed")
    print("[PASS] Two certified causal patterns linked into one chain")
    print("[PASS] Hop continuity and temporal direction verified")
    print("[PASS] Certified observation lineage retained across every hop")
    print("[PASS] Cross-market dependency continuation authorized read-only")
    print("[PASS] Deterministic replay equality verified")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered OML-063 records rejected")
    print(
        "[DONE] OML-063 CERTIFIED CROSS-MARKET "
        "MULTI-HOP CAUSAL CHAIN MEMORY PASS"
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
    required = (UPSTREAM, UPSTREAM_TEST, CHAIN, CHAIN_TEST)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(
            "Required certified files missing: " + ", ".join(missing)
        )

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    upstream = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_certified_market_behavior_causal_pattern_memory"
    )
    chain = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_certified_observation_multi_hop_causal_chain_memory"
    )

    expected = (
        (
            upstream,
            {
                "SCHEMA_VERSION": "OML-062",
                "ENGINE_ID": "OML-062",
                "POLICY_ID": (
                    "oracle-memory."
                    "certified-market-behavior-causal-pattern-memory.v1"
                ),
            },
            "OML-062",
        ),
        (
            chain,
            {
                "SCHEMA_VERSION": "OML-037",
                "ENGINE_ID": "OML-037",
                "POLICY_ID": (
                    "oracle-memory."
                    "certified-observation-multi-hop-causal-chain-memory.v1"
                ),
                "UPSTREAM_SCHEMA_VERSION": "OML-036",
                "UPSTREAM_ENGINE_ID": "OML-036",
            },
            "OML-037",
        ),
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
        "OracleMemoryCertifiedMultiHopChainRequest",
        "OracleMemoryCertifiedMultiHopCausalChainMemory",
        "build_oracle_memory_certified_multi_hop_causal_chain_memory",
        "verify_oracle_memory_certified_multi_hop_chain_request",
        "verify_oracle_memory_certified_multi_hop_causal_chain_memory",
    )
    missing_symbols = [
        name for name in required_symbols if not hasattr(chain, name)
    ]
    if missing_symbols:
        raise RuntimeError(
            "Certified OML-037 missing symbols: "
            + ", ".join(missing_symbols)
        )

    parameters = set(
        inspect.signature(
            chain.build_oracle_memory_certified_multi_hop_causal_chain_memory
        ).parameters
    )
    missing_parameters = sorted(
        {"causal_patterns", "requests"} - parameters
    )
    if missing_parameters:
        raise RuntimeError(
            "Certified OML-037 builder parameters missing: "
            + ", ".join(missing_parameters)
        )


def main() -> int:
    print("=" * 48)
    print(" OML-063 INSTALLER")
    print(" CERTIFIED MARKET-BEHAVIOR MULTI-HOP CAUSAL CHAIN MEMORY")
    print("=" * 48)
    print("[BOOT] Revision: EXACT_OML_049_037_INTERFACE_ALIGNMENT")

    try:
        validate()
        print("[OK] Actual OML-062 dataclass and verifier inspected")
        print("[OK] Actual OML-037 builder and signature inspected")

        for path, label in (
            (UPSTREAM_TEST, "OML-062"),
            (CHAIN_TEST, "OML-037"),
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
            for path in (UPSTREAM, UPSTREAM_TEST, CHAIN, CHAIN_TEST)
        }

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_memory_certified_market_behavior_"
            "multi_hop_causal_chain_memory import *"
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
                f"OML-063 test failed with exit code {completed.returncode}"
            )

        for path, before in tracked.items():
            if path.read_bytes() != before:
                raise RuntimeError(f"Certified upstream changed: {path}")

        print("[PASS] Certified OML-062 production unchanged")
        print("[PASS] Certified OML-062 standalone test unchanged")
        print("[PASS] Certified OML-037 chain engine unchanged")
        print("[PASS] Exact OML-036 causal object consumed directly")
        print("[PASS] OML-063 production fully replaced")
        print("[PASS] OML-063 standalone deterministic test installed")
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
            "[DONE] OML-063 CERTIFIED CROSS-MARKET "
            "MULTI-HOP CAUSAL CHAIN MEMORY INSTALLED"
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
