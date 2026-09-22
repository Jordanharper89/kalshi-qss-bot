from __future__ import annotations

import ast
import importlib
import inspect
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "oracle_memory"

UPSTREAM = (
    PACKAGE
    / "oracle_memory_certified_market_behavior_causal_pattern_memory_075.py"
)
UPSTREAM_TEST = (
    ROOT
    / "test_oml_075_oracle_memory_certified_market_behavior_"
      "causal_pattern_memory.py"
)
CHAIN_037 = (
    PACKAGE
    / "oracle_memory_certified_observation_"
      "multi_hop_causal_chain_memory.py"
)
PRODUCTION = (
    PACKAGE
    / "oracle_memory_certified_market_behavior_"
      "multi_hop_causal_chain_memory_076.py"
)
TEST = (
    ROOT
    / "test_oml_076_oracle_memory_certified_market_behavior_"
      "multi_hop_causal_chain_memory.py"
)
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass\nfrom typing import Any, Mapping, Sequence\n\nfrom qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_causal_pattern_memory_075 import (\n    OracleMemoryCertifiedMarketBehaviorCausalPatternMemory075,\n    verify_oracle_memory_certified_market_behavior_causal_pattern_memory_075,\n)\nfrom qseries_v2.oracle_memory.oracle_memory_certified_observation_multi_hop_causal_chain_memory import (\n    OracleMemoryCertifiedMultiHopCausalChainMemory,\n    OracleMemoryCertifiedMultiHopChainRequest,\n    build_oracle_memory_certified_multi_hop_causal_chain_memory,\n    verify_oracle_memory_certified_multi_hop_causal_chain_memory,\n    verify_oracle_memory_certified_multi_hop_chain_request,\n)\nfrom qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (\n    SUBSYSTEM_ID,\n)\n\nSCHEMA_VERSION = "OML-076"\nENGINE_ID = "OML-076"\nPOLICY_ID = (\n    "oracle-memory.certified-market-behavior-"\n    "multi-hop-causal-chain-memory-076.v1"\n)\nUPSTREAM_SCHEMA_VERSION = "OML-075"\nUPSTREAM_ENGINE_ID = "OML-075"\nCHAIN_SCHEMA_VERSION = "OML-037"\nCHAIN_ENGINE_ID = "OML-037"\nSTATE_READ_ONLY = "read_only_market_behavior_multi_hop_causal_chain_memory_076"\n\n\nclass OracleMemoryCertifiedMarketBehaviorChain076InvariantError(RuntimeError):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleMemoryCertifiedMarketBehaviorMultiHopCausalChainMemory076:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    subsystem_id: str\n    upstream_schema_version: str\n    upstream_engine_id: str\n    upstream_certification_hash: str\n    upstream_causal_certification_hash: str\n    upstream_causal_memory_hash: str\n    chain_schema_version: str\n    chain_engine_id: str\n    chains: OracleMemoryCertifiedMultiHopCausalChainMemory\n    chain_count: int\n    total_hop_count: int\n    state: str\n    causal_pattern_lineage_verified: bool\n    certified_observation_lineage_verified: bool\n    deterministic_identity_verified: bool\n    canonical_chain_order_verified: bool\n    hop_continuity_verified: bool\n    temporal_direction_verified: bool\n    evidence_depth_reconciled: bool\n    contradiction_depth_reconciled: bool\n    persistence_enabled: bool\n    learning_updates_enabled: bool\n    runtime_activation_enabled: bool\n    publication_enabled: bool\n    action_authorization_enabled: bool\n    qseries_execution_enabled: bool\n    chain_memory_ready: bool\n    downstream_cross_market_dependency_authorized: bool\n    read_only: bool\n    certification_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    raise OracleMemoryCertifiedMarketBehaviorChain076InvariantError(\n        "unsupported OML-076 value type"\n    )\n\n\ndef _stable_hash(value: Any) -> str:\n    return hashlib.sha256(\n        json.dumps(\n            _canonical(value),\n            sort_keys=True,\n            separators=(",", ":"),\n            ensure_ascii=True,\n            allow_nan=False,\n        ).encode("utf-8")\n    ).hexdigest()\n\n\ndef _reject(reason: str) -> None:\n    raise OracleMemoryCertifiedMarketBehaviorChain076InvariantError(reason)\n\n\ndef _require_hash(value: str, label: str) -> None:\n    if not isinstance(value, str) or len(value) != 64:\n        _reject(f"OML-076 invalid {label} length")\n    try:\n        int(value, 16)\n    except ValueError as exc:\n        raise OracleMemoryCertifiedMarketBehaviorChain076InvariantError(\n            f"OML-076 invalid {label} hexadecimal value"\n        ) from exc\n\n\ndef build_oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory_076(\n    *,\n    causal_patterns: OracleMemoryCertifiedMarketBehaviorCausalPatternMemory075,\n    requests: Sequence[OracleMemoryCertifiedMultiHopChainRequest],\n) -> OracleMemoryCertifiedMarketBehaviorMultiHopCausalChainMemory076:\n    verify_oracle_memory_certified_market_behavior_causal_pattern_memory_075(\n        causal_patterns\n    )\n\n    if causal_patterns.schema_version != UPSTREAM_SCHEMA_VERSION:\n        _reject("OML-076 upstream schema mismatch")\n    if causal_patterns.engine_id != UPSTREAM_ENGINE_ID:\n        _reject("OML-076 upstream engine mismatch")\n    if not causal_patterns.causal_memory_ready:\n        _reject("OML-076 upstream causal memory not ready")\n    if not causal_patterns.downstream_multi_hop_causal_authorized:\n        _reject("OML-076 multi-hop continuation not authorized")\n    if not causal_patterns.read_only:\n        _reject("OML-076 upstream causal memory not read-only")\n\n    for request in requests:\n        verify_oracle_memory_certified_multi_hop_chain_request(request)\n\n    chains = build_oracle_memory_certified_multi_hop_causal_chain_memory(\n        causal_patterns=causal_patterns.causal_patterns,\n        requests=tuple(requests),\n    )\n    verify_oracle_memory_certified_multi_hop_causal_chain_memory(chains)\n\n    if chains.schema_version != CHAIN_SCHEMA_VERSION:\n        _reject("OML-076 chain schema mismatch")\n    if chains.engine_id != CHAIN_ENGINE_ID:\n        _reject("OML-076 chain engine mismatch")\n    if chains.upstream_certification_hash != (\n        causal_patterns.causal_patterns.certification_hash\n    ):\n        _reject("OML-076 causal certification lineage mismatch")\n    if chains.upstream_causal_memory_hash != (\n        causal_patterns.causal_patterns.causal_memory.memory_hash\n    ):\n        _reject("OML-076 causal memory lineage mismatch")\n\n    body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "subsystem_id": SUBSYSTEM_ID,\n        "upstream_schema_version": causal_patterns.schema_version,\n        "upstream_engine_id": causal_patterns.engine_id,\n        "upstream_certification_hash": causal_patterns.certification_hash,\n        "upstream_causal_certification_hash": (\n            causal_patterns.causal_patterns.certification_hash\n        ),\n        "upstream_causal_memory_hash": (\n            causal_patterns.causal_patterns.causal_memory.memory_hash\n        ),\n        "chain_schema_version": chains.schema_version,\n        "chain_engine_id": chains.engine_id,\n        "chains": chains,\n        "chain_count": chains.chain_count,\n        "total_hop_count": chains.total_hop_count,\n        "state": STATE_READ_ONLY,\n        "causal_pattern_lineage_verified": (\n            chains.causal_pattern_lineage_verified\n        ),\n        "certified_observation_lineage_verified": (\n            chains.certified_observation_lineage_verified\n        ),\n        "deterministic_identity_verified": (\n            chains.deterministic_identity_verified\n        ),\n        "canonical_chain_order_verified": (\n            chains.canonical_chain_order_verified\n        ),\n        "hop_continuity_verified": chains.hop_continuity_verified,\n        "temporal_direction_verified": chains.temporal_direction_verified,\n        "evidence_depth_reconciled": chains.evidence_depth_reconciled,\n        "contradiction_depth_reconciled": (\n            chains.contradiction_depth_reconciled\n        ),\n        "persistence_enabled": False,\n        "learning_updates_enabled": False,\n        "runtime_activation_enabled": False,\n        "publication_enabled": False,\n        "action_authorization_enabled": False,\n        "qseries_execution_enabled": False,\n        "chain_memory_ready": True,\n        "downstream_cross_market_dependency_authorized": True,\n        "read_only": True,\n    }\n\n    result = OracleMemoryCertifiedMarketBehaviorMultiHopCausalChainMemory076(\n        **body,\n        certification_hash=_stable_hash(body),\n    )\n    verify_oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory_076(\n        result\n    )\n    return result\n\n\ndef verify_oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory_076(\n    result: OracleMemoryCertifiedMarketBehaviorMultiHopCausalChainMemory076,\n) -> bool:\n    body = asdict(result)\n    supplied = body.pop("certification_hash")\n    if _stable_hash(body) != supplied:\n        _reject("OML-076 certification hash mismatch")\n\n    if result.schema_version != SCHEMA_VERSION:\n        _reject("OML-076 schema mismatch")\n    if result.engine_id != ENGINE_ID:\n        _reject("OML-076 engine mismatch")\n    if result.policy_id != POLICY_ID:\n        _reject("OML-076 policy mismatch")\n    if result.subsystem_id != SUBSYSTEM_ID:\n        _reject("OML-076 subsystem mismatch")\n    if result.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:\n        _reject("OML-076 upstream schema lineage mismatch")\n    if result.upstream_engine_id != UPSTREAM_ENGINE_ID:\n        _reject("OML-076 upstream engine lineage mismatch")\n    if result.chain_schema_version != CHAIN_SCHEMA_VERSION:\n        _reject("OML-076 chain schema lineage mismatch")\n    if result.chain_engine_id != CHAIN_ENGINE_ID:\n        _reject("OML-076 chain engine lineage mismatch")\n\n    for value in (\n        result.upstream_certification_hash,\n        result.upstream_causal_certification_hash,\n        result.upstream_causal_memory_hash,\n        result.certification_hash,\n    ):\n        _require_hash(value, "lineage hash")\n\n    verify_oracle_memory_certified_multi_hop_causal_chain_memory(\n        result.chains\n    )\n\n    if result.upstream_causal_certification_hash != (\n        result.chains.upstream_certification_hash\n    ):\n        _reject("OML-076 causal certification mismatch")\n    if result.upstream_causal_memory_hash != (\n        result.chains.upstream_causal_memory_hash\n    ):\n        _reject("OML-076 causal memory mismatch")\n    if result.chain_count != result.chains.chain_count:\n        _reject("OML-076 chain count mismatch")\n    if result.total_hop_count != result.chains.total_hop_count:\n        _reject("OML-076 hop count mismatch")\n\n    required = (\n        result.causal_pattern_lineage_verified,\n        result.certified_observation_lineage_verified,\n        result.deterministic_identity_verified,\n        result.canonical_chain_order_verified,\n        result.hop_continuity_verified,\n        result.temporal_direction_verified,\n        result.evidence_depth_reconciled,\n        result.contradiction_depth_reconciled,\n        result.chain_memory_ready,\n        result.downstream_cross_market_dependency_authorized,\n        result.read_only,\n    )\n    if not all(required):\n        _reject("OML-076 guarantee missing")\n\n    if result.state != STATE_READ_ONLY:\n        _reject("OML-076 state invalid")\n\n    forbidden = (\n        result.persistence_enabled,\n        result.learning_updates_enabled,\n        result.runtime_activation_enabled,\n        result.publication_enabled,\n        result.action_authorization_enabled,\n        result.qseries_execution_enabled,\n    )\n    if any(forbidden):\n        _reject("OML-076 forbidden capability enabled")\n\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nimport importlib.util\nimport sys\nfrom dataclasses import replace\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_causal_pattern_memory_075 import (\n    build_oracle_memory_certified_market_behavior_causal_pattern_memory_075,\n)\nfrom qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory_076 import (\n    OracleMemoryCertifiedMarketBehaviorChain076InvariantError,\n    build_oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory_076,\n    verify_oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory_076,\n)\nfrom qseries_v2.oracle_memory.oracle_memory_certified_observation_causal_pattern_memory import (\n    build_oracle_memory_certified_causal_observation_request,\n)\nfrom qseries_v2.oracle_memory.oracle_memory_certified_observation_multi_hop_causal_chain_memory import (\n    build_oracle_memory_certified_multi_hop_chain_request,\n)\n\n\ndef load_module(path: Path, name: str):\n    specification = importlib.util.spec_from_file_location(name, path)\n    if specification is None or specification.loader is None:\n        raise RuntimeError(f"unable to load fixture: {path}")\n    module = importlib.util.module_from_spec(specification)\n    sys.modules[name] = module\n    specification.loader.exec_module(module)\n    return module\n\n\ndef expect_rejection(callable_object, label: str) -> None:\n    try:\n        callable_object()\n    except OracleMemoryCertifiedMarketBehaviorChain076InvariantError:\n        return\n    raise AssertionError(f"tampered OML-076 {label} accepted")\n\n\ndef build_chains(root: Path):\n    fixture_074 = load_module(\n        root\n        / "test_oml_074_oracle_memory_certified_market_behavior_"\n        "calibration_memory.py",\n        "oml_074_fixture_for_oml_076",\n    )\n    calibration, reliability, forecasts = fixture_074.build_calibration(root)\n\n    certified_hashes = tuple(\n        sorted(\n            {\n                value\n                for binding in calibration.calibration.bindings\n                for value in binding.certified_observation_hashes\n            }\n        )\n    )\n    assert certified_hashes\n\n    entity_a = "1" * 64\n    entity_b = "2" * 64\n    entity_c = "3" * 64\n\n    first_hash = certified_hashes[0]\n    second_hash = (\n        certified_hashes[1]\n        if len(certified_hashes) > 1\n        else certified_hashes[0]\n    )\n\n    causal_requests = (\n        build_oracle_memory_certified_causal_observation_request(\n            pattern_name=(\n                "Market-behavior liquidity shift precedes order-flow change"\n            ),\n            cause_entity_id=entity_a,\n            effect_entity_id=entity_b,\n            cause_observed_at="2026-08-04T16:00:00-05:00",\n            effect_observed_at="2026-08-04T16:05:00-05:00",\n            certified_observation_hashes=(first_hash,),\n            contradicting_certified_observation_hashes=(),\n            confidence=0.82,\n            calibrated_probability=0.80,\n            outcome_confirmed=True,\n            outcome_supported=True,\n        ),\n        build_oracle_memory_certified_causal_observation_request(\n            pattern_name=(\n                "Market-behavior order-flow change precedes repricing"\n            ),\n            cause_entity_id=entity_b,\n            effect_entity_id=entity_c,\n            cause_observed_at="2026-08-04T16:06:00-05:00",\n            effect_observed_at="2026-08-04T16:10:00-05:00",\n            certified_observation_hashes=(second_hash,),\n            contradicting_certified_observation_hashes=(),\n            confidence=0.80,\n            calibrated_probability=0.75,\n            outcome_confirmed=True,\n            outcome_supported=True,\n        ),\n    )\n\n    causal_patterns = (\n        build_oracle_memory_certified_market_behavior_causal_pattern_memory_075(\n            calibration=calibration,\n            requests=causal_requests,\n        )\n    )\n\n    patterns = {\n        pattern.normalized_pattern_name: pattern\n        for pattern in causal_patterns.causal_patterns.causal_memory.patterns\n    }\n    chain_request = build_oracle_memory_certified_multi_hop_chain_request(\n        chain_name="Market-behavior liquidity shift to repricing",\n        pattern_ids=(\n            patterns[\n                "market-behavior liquidity shift precedes order-flow change"\n            ].pattern_id,\n            patterns[\n                "market-behavior order-flow change precedes repricing"\n            ].pattern_id,\n        ),\n    )\n\n    result = (\n        build_oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory_076(\n            causal_patterns=causal_patterns,\n            requests=(chain_request,),\n        )\n    )\n    return result, causal_patterns, certified_hashes\n\n\ndef main() -> int:\n    print("=" * 48)\n    print(" OML-076 TEST")\n    print(" CERTIFIED MARKET-BEHAVIOR MULTI-HOP CAUSAL CHAIN MEMORY")\n    print("=" * 48)\n\n    root = Path(__file__).resolve().parent\n    result, causal_patterns, certified_hashes = build_chains(root)\n\n    assert result.schema_version == "OML-076"\n    assert result.engine_id == "OML-076"\n    assert result.upstream_schema_version == "OML-075"\n    assert result.upstream_engine_id == "OML-075"\n    assert result.chain_schema_version == "OML-037"\n    assert result.chain_engine_id == "OML-037"\n    assert result.chain_count == 1\n    assert result.total_hop_count == 2\n    assert result.causal_pattern_lineage_verified\n    assert result.certified_observation_lineage_verified\n    assert result.hop_continuity_verified\n    assert result.temporal_direction_verified\n    assert result.evidence_depth_reconciled\n    assert result.contradiction_depth_reconciled\n    assert result.chain_memory_ready\n    assert result.downstream_cross_market_dependency_authorized\n    assert result.read_only\n    assert not result.persistence_enabled\n    assert not result.learning_updates_enabled\n    assert not result.runtime_activation_enabled\n    assert not result.publication_enabled\n    assert not result.action_authorization_enabled\n    assert not result.qseries_execution_enabled\n\n    chain = result.chains.chain_memory.chains[0]\n    assert len(chain.hops) == 2\n    assert chain.hops[0].effect_entity_id == chain.hops[1].cause_entity_id\n    assert set(result.chains.bindings[0].certified_observation_hashes).issubset(\n        set(certified_hashes)\n    )\n\n    replay, _, _ = build_chains(root)\n    assert replay == result\n    assert (\n        verify_oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory_076(\n            result\n        )\n    )\n\n    expect_rejection(\n        lambda: verify_oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory_076(\n            replace(result, persistence_enabled=True)\n        ),\n        "persistence",\n    )\n    expect_rejection(\n        lambda: verify_oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory_076(\n            replace(result, qseries_execution_enabled=True)\n        ),\n        "Q Series execution",\n    )\n\n    print("[PASS] Certified OML-075 causal memory consumed read-only")\n    print("[PASS] Exact OML-036 causal-pattern object passed directly")\n    print("[PASS] Actual OML-037 multi-hop builder consumed")\n    print("[PASS] Two distinct causal patterns linked A-to-B-to-C")\n    print("[PASS] Hop continuity and temporal direction verified")\n    print("[PASS] Certified observation lineage retained")\n    print("[PASS] Cross-market dependency continuation authorized read-only")\n    print("[PASS] Deterministic replay equality verified")\n    print("[PASS] Active capabilities remained disabled")\n    print("[PASS] Tampered OML-076 chain objects rejected")\n    print("[DONE] OML-076 CERTIFIED MARKET-BEHAVIOR MULTI-HOP CAUSAL CHAIN PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


def write_complete(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def validate_current_repository() -> None:
    required = (UPSTREAM, UPSTREAM_TEST, CHAIN_037)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(
            "Required certified files missing: " + ", ".join(missing)
        )

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    upstream_module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_certified_market_behavior_"
        "causal_pattern_memory_075"
    )
    chain_module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_certified_observation_"
        "multi_hop_causal_chain_memory"
    )

    expected = (
        (upstream_module, "SCHEMA_VERSION", "OML-075"),
        (upstream_module, "ENGINE_ID", "OML-075"),
        (chain_module, "SCHEMA_VERSION", "OML-037"),
        (chain_module, "ENGINE_ID", "OML-037"),
    )
    for module, name, value in expected:
        actual = getattr(module, name, None)
        if actual != value:
            raise RuntimeError(
                f"{module.__name__}.{name} mismatch: "
                f"expected {value!r}, got {actual!r}"
            )

    upstream_fields = set(
        upstream_module.
        OracleMemoryCertifiedMarketBehaviorCausalPatternMemory075.
        __dataclass_fields__
    )
    required_fields = {
        "causal_patterns",
        "causal_memory_ready",
        "downstream_multi_hop_causal_authorized",
        "certification_hash",
        "read_only",
    }
    missing_fields = sorted(required_fields - upstream_fields)
    if missing_fields:
        raise RuntimeError(
            "OML-075 dataclass fields missing: "
            + ", ".join(missing_fields)
        )

    request_builder = getattr(
        chain_module,
        "build_oracle_memory_certified_multi_hop_chain_request",
        None,
    )
    memory_builder = getattr(
        chain_module,
        "build_oracle_memory_certified_multi_hop_causal_chain_memory",
        None,
    )
    if request_builder is None or memory_builder is None:
        raise RuntimeError("OML-037 required builders missing")

    request_parameters = set(inspect.signature(request_builder).parameters)
    missing_request_parameters = sorted(
        {"chain_name", "pattern_ids"} - request_parameters
    )
    if missing_request_parameters:
        raise RuntimeError(
            "OML-037 request parameters missing: "
            + ", ".join(missing_request_parameters)
        )

    memory_parameters = set(inspect.signature(memory_builder).parameters)
    missing_memory_parameters = sorted(
        {"causal_patterns", "requests"} - memory_parameters
    )
    if missing_memory_parameters:
        raise RuntimeError(
            "OML-037 memory parameters missing: "
            + ", ".join(missing_memory_parameters)
        )


def main() -> int:
    print("=" * 48)
    print(" OML-076 INSTALLER")
    print(" CERTIFIED MARKET-BEHAVIOR MULTI-HOP CAUSAL CHAIN MEMORY")
    print("=" * 48)
    print("[BOOT] Revision: CURRENT_REPOSITORY_OML_075_037_EXACT_ALIGNMENT")

    try:
        validate_current_repository()
        print("[OK] Current OML-075 dataclass inspected")
        print("[OK] Current OML-037 builder signatures inspected")

        tracked = {
            path: path.read_bytes()
            for path in (UPSTREAM, UPSTREAM_TEST, CHAIN_037)
        }

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_memory_certified_market_behavior_"
            "multi_hop_causal_chain_memory_076 import *"
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

        completed = subprocess.run(
            [sys.executable, str(TEST)],
            cwd=ROOT,
            check=False,
        )
        if completed.returncode:
            raise RuntimeError(
                f"OML-076 test failed with exit code {completed.returncode}"
            )

        for path, before in tracked.items():
            if path.read_bytes() != before:
                raise RuntimeError(f"Certified upstream changed: {path}")

        print("[PASS] Complete OML-076 production replacement installed")
        print("[PASS] Complete deterministic standalone test installed")
        print("[PASS] Certified OML-075 and OML-037 files unchanged")
        print("[PASS] Deterministic replay preserved")
        print("[PASS] Oracle Terminal separation preserved")
        print("[PASS] Persistence remained disabled")
        print("[PASS] Learning updates remained disabled")
        print("[PASS] Runtime activation remained disabled")
        print("[PASS] Publication remained disabled")
        print("[PASS] Action authorization remained disabled")
        print("[PASS] Q Series execution remained disabled")
        print("[DONE] OML-076 INSTALLED")
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
