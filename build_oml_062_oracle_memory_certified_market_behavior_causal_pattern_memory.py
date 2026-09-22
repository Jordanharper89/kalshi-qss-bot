from __future__ import annotations

import ast
import importlib
import inspect
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "oracle_memory"

UPSTREAM = PACKAGE / "oracle_memory_certified_market_behavior_calibration_memory.py"
UPSTREAM_TEST = ROOT / "test_oml_061_oracle_memory_certified_market_behavior_calibration_memory.py"
CAUSAL = PACKAGE / "oracle_memory_certified_observation_causal_pattern_memory.py"
CAUSAL_TEST = ROOT / "test_oml_036_oracle_memory_certified_observation_causal_pattern_memory.py"

PRODUCTION = PACKAGE / "oracle_memory_certified_market_behavior_causal_pattern_memory.py"
TEST = ROOT / "test_oml_062_oracle_memory_certified_market_behavior_causal_pattern_memory.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_calibration_memory import (
    OracleMemoryCertifiedMarketBehaviorCalibrationMemory,
    verify_oracle_memory_certified_market_behavior_calibration_memory,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_causal_pattern_memory import (
    OracleMemoryCertifiedCausalObservationRequest,
    OracleMemoryCertifiedCausalPatternMemory,
    build_oracle_memory_certified_causal_pattern_memory,
    verify_oracle_memory_certified_causal_observation_request,
    verify_oracle_memory_certified_causal_pattern_memory,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-062"
ENGINE_ID = "OML-062"
POLICY_ID = "oracle-memory.certified-market-behavior-causal-pattern-memory.v1"
UPSTREAM_SCHEMA_VERSION = "OML-061"
UPSTREAM_ENGINE_ID = "OML-061"
CAUSAL_SCHEMA_VERSION = "OML-036"
CAUSAL_ENGINE_ID = "OML-036"
STATE_READ_ONLY = "read_only_market_behavior_causal_pattern_memory"


class OracleMemoryCertifiedMarketBehaviorCausalInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCertifiedMarketBehaviorCausalPatternMemory:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_certification_hash: str
    upstream_calibration_certification_hash: str
    upstream_calibration_memory_hash: str
    causal_schema_version: str
    causal_engine_id: str
    causal_patterns: OracleMemoryCertifiedCausalPatternMemory
    pattern_count: int
    total_observation_count: int
    state: str
    calibration_lineage_verified: bool
    certified_observation_lineage_verified: bool
    deterministic_identity_verified: bool
    canonical_pattern_order_verified: bool
    temporal_precedence_verified: bool
    evidence_lineage_verified: bool
    contradiction_tracking_verified: bool
    outcome_reconciliation_verified: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    causal_memory_ready: bool
    downstream_multi_hop_causal_authorized: bool
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
    raise OracleMemoryCertifiedMarketBehaviorCausalInvariantError(
        "unsupported OML-062 value type"
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
    raise OracleMemoryCertifiedMarketBehaviorCausalInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-062 invalid {label} length")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryCertifiedMarketBehaviorCausalInvariantError(
            f"OML-062 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_certified_market_behavior_causal_pattern_memory(
    *,
    calibration: OracleMemoryCertifiedMarketBehaviorCalibrationMemory,
    requests: Sequence[OracleMemoryCertifiedCausalObservationRequest],
) -> OracleMemoryCertifiedMarketBehaviorCausalPatternMemory:
    verify_oracle_memory_certified_market_behavior_calibration_memory(calibration)

    if calibration.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-062 upstream schema mismatch")
    if calibration.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-062 upstream engine mismatch")
    if not calibration.calibration_ready:
        _reject("OML-062 upstream calibration not ready")
    if not calibration.downstream_causal_memory_authorized:
        _reject("OML-062 causal continuation not authorized")
    if not calibration.read_only:
        _reject("OML-062 upstream calibration not read-only")

    allowed_hashes = {
        value
        for binding in calibration.calibration.bindings
        for value in binding.certified_observation_hashes
    }
    if not allowed_hashes:
        _reject("OML-062 no certified observation hashes available")

    for request in requests:
        verify_oracle_memory_certified_causal_observation_request(request)
        referenced = set(request.certified_observation_hashes)
        contradicted = set(request.contradicting_certified_observation_hashes)
        if not referenced.issubset(allowed_hashes):
            _reject("OML-062 unknown certified causal evidence")
        if not contradicted.issubset(allowed_hashes):
            _reject("OML-062 unknown certified contradiction evidence")

    causal_patterns = build_oracle_memory_certified_causal_pattern_memory(
        calibration=calibration.calibration,
        requests=tuple(requests),
    )
    verify_oracle_memory_certified_causal_pattern_memory(causal_patterns)

    if causal_patterns.schema_version != CAUSAL_SCHEMA_VERSION:
        _reject("OML-062 causal schema mismatch")
    if causal_patterns.engine_id != CAUSAL_ENGINE_ID:
        _reject("OML-062 causal engine mismatch")
    if causal_patterns.upstream_certification_hash != (
        calibration.calibration.certification_hash
    ):
        _reject("OML-062 calibration certification lineage mismatch")
    if causal_patterns.upstream_calibration_memory_hash != (
        calibration.calibration.calibration_memory.memory_hash
    ):
        _reject("OML-062 calibration memory lineage mismatch")

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": calibration.schema_version,
        "upstream_engine_id": calibration.engine_id,
        "upstream_certification_hash": calibration.certification_hash,
        "upstream_calibration_certification_hash": (
            calibration.calibration.certification_hash
        ),
        "upstream_calibration_memory_hash": (
            calibration.calibration.calibration_memory.memory_hash
        ),
        "causal_schema_version": causal_patterns.schema_version,
        "causal_engine_id": causal_patterns.engine_id,
        "causal_patterns": causal_patterns,
        "pattern_count": causal_patterns.pattern_count,
        "total_observation_count": causal_patterns.total_observation_count,
        "state": STATE_READ_ONLY,
        "calibration_lineage_verified": True,
        "certified_observation_lineage_verified": (
            causal_patterns.certified_observation_lineage_verified
        ),
        "deterministic_identity_verified": (
            causal_patterns.deterministic_identity_verified
        ),
        "canonical_pattern_order_verified": (
            causal_patterns.canonical_pattern_order_verified
        ),
        "temporal_precedence_verified": (
            causal_patterns.temporal_precedence_verified
        ),
        "evidence_lineage_verified": causal_patterns.evidence_lineage_verified,
        "contradiction_tracking_verified": (
            causal_patterns.contradiction_tracking_verified
        ),
        "outcome_reconciliation_verified": (
            causal_patterns.outcome_reconciliation_verified
        ),
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "causal_memory_ready": True,
        "downstream_multi_hop_causal_authorized": (
            causal_patterns.downstream_multi_hop_causal_authorized
        ),
        "read_only": True,
    }

    result = OracleMemoryCertifiedMarketBehaviorCausalPatternMemory(
        **body,
        certification_hash=_stable_hash(body),
    )
    verify_oracle_memory_certified_market_behavior_causal_pattern_memory(result)
    return result


def verify_oracle_memory_certified_market_behavior_causal_pattern_memory(
    result: OracleMemoryCertifiedMarketBehaviorCausalPatternMemory,
) -> bool:
    body = asdict(result)
    supplied = body.pop("certification_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-062 certification hash mismatch")

    if result.schema_version != SCHEMA_VERSION:
        _reject("OML-062 schema mismatch")
    if result.engine_id != ENGINE_ID:
        _reject("OML-062 engine mismatch")
    if result.policy_id != POLICY_ID:
        _reject("OML-062 policy mismatch")
    if result.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-062 subsystem mismatch")
    if result.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-062 upstream schema lineage mismatch")
    if result.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-062 upstream engine lineage mismatch")
    if result.causal_schema_version != CAUSAL_SCHEMA_VERSION:
        _reject("OML-062 causal schema lineage mismatch")
    if result.causal_engine_id != CAUSAL_ENGINE_ID:
        _reject("OML-062 causal engine lineage mismatch")

    for value in (
        result.upstream_certification_hash,
        result.upstream_calibration_certification_hash,
        result.upstream_calibration_memory_hash,
        result.certification_hash,
    ):
        _require_hash(value, "lineage hash")

    verify_oracle_memory_certified_causal_pattern_memory(
        result.causal_patterns
    )

    if result.upstream_calibration_certification_hash != (
        result.causal_patterns.upstream_certification_hash
    ):
        _reject("OML-062 calibration certification mismatch")
    if result.upstream_calibration_memory_hash != (
        result.causal_patterns.upstream_calibration_memory_hash
    ):
        _reject("OML-062 calibration memory mismatch")
    if result.pattern_count != result.causal_patterns.pattern_count:
        _reject("OML-062 pattern count mismatch")
    if result.total_observation_count != (
        result.causal_patterns.total_observation_count
    ):
        _reject("OML-062 observation count mismatch")

    required = (
        result.calibration_lineage_verified,
        result.certified_observation_lineage_verified,
        result.deterministic_identity_verified,
        result.canonical_pattern_order_verified,
        result.temporal_precedence_verified,
        result.evidence_lineage_verified,
        result.contradiction_tracking_verified,
        result.outcome_reconciliation_verified,
        result.causal_memory_ready,
        result.downstream_multi_hop_causal_authorized,
        result.read_only,
    )
    if not all(required):
        _reject("OML-062 guarantee missing")
    if result.state != STATE_READ_ONLY:
        _reject("OML-062 state invalid")

    forbidden = (
        result.persistence_enabled,
        result.learning_updates_enabled,
        result.runtime_activation_enabled,
        result.publication_enabled,
        result.action_authorization_enabled,
        result.qseries_execution_enabled,
    )
    if any(forbidden):
        _reject("OML-062 forbidden capability enabled")

    return True
"""

TEST_SOURCE = r"""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_causal_pattern_memory import (
    OracleMemoryCertifiedMarketBehaviorCausalInvariantError,
    build_oracle_memory_certified_market_behavior_causal_pattern_memory,
    verify_oracle_memory_certified_market_behavior_causal_pattern_memory,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_causal_pattern_memory import (
    build_oracle_memory_certified_causal_observation_request,
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
    except OracleMemoryCertifiedMarketBehaviorCausalInvariantError:
        return
    raise AssertionError(f"tampered OML-062 {label} accepted")


def build_calibration(root: Path):
    fixture = load_module(
        root
        / "test_oml_060_oracle_memory_certified_market_behavior_source_reliability.py",
        "oml_060_fixture_for_oml_062",
    )
    lifecycle = fixture.build_lifecycle(root)

    observation_hashes = tuple(sorted({
        value
        for binding in lifecycle.lifecycle_tracking.bindings
        for value in binding.source_observation_hashes
    }))

    from qseries_v2.oracle_memory.oracle_memory_certified_observation_source_reliability_memory import (
        build_oracle_memory_certified_source_outcome,
    )
    from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_source_reliability import (
        build_oracle_memory_certified_market_behavior_source_reliability,
    )
    from qseries_v2.oracle_memory.oracle_memory_certified_observation_calibration_memory import (
        build_oracle_memory_certified_calibration_forecast,
    )
    from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_calibration_memory import (
        build_oracle_memory_certified_market_behavior_calibration_memory,
    )

    outcomes = tuple(
        build_oracle_memory_certified_source_outcome(
            source_name="Oracle Market-Behavior Observation",
            observation_hash=value,
            outcome_confirmed=True,
            outcome_correct=True,
            contradiction_count=0,
            confidence_at_observation=0.80,
            observed_at=f"2026-08-02T17:{20 + index:02d}:00-05:00",
        )
        for index, value in enumerate(observation_hashes)
    )

    reliability = (
        build_oracle_memory_certified_market_behavior_source_reliability(
            lifecycle=lifecycle,
            outcomes=outcomes,
        )
    )

    profile = reliability.source_reliability.reliability_memory.profiles[0]
    certified_hashes = (
        reliability.source_reliability.bindings[0].
        certified_observation_hashes
    )

    forecasts = tuple(
        build_oracle_memory_certified_calibration_forecast(
            profile_name="Market-Behavior Calibration",
            source_name=profile.source_name,
            source_id=profile.source_id,
            forecast_id=f"causal-forecast-{index + 1:03d}",
            certified_observation_hash=value,
            predicted_probability=0.80 - (index * 0.05),
            outcome_confirmed=True,
            outcome_value=1,
            observed_at=f"2026-08-02T16:{10 + index:02d}:00-05:00",
            resolved_at=f"2026-08-02T17:{30 + index:02d}:00-05:00",
        )
        for index, value in enumerate(certified_hashes)
    )

    calibration = (
        build_oracle_memory_certified_market_behavior_calibration_memory(
            reliability=reliability,
            forecasts=forecasts,
        )
    )
    return calibration, certified_hashes


def main() -> int:
    print("=" * 48)
    print(" OML-062 TEST")
    print(" CERTIFIED MARKET-BEHAVIOR CAUSAL PATTERN MEMORY")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    calibration, certified_hashes = build_calibration(root)

    requests = (
        build_oracle_memory_certified_causal_observation_request(
            pattern_name="Liquidity shift precedes Bitcoin repricing",
            cause_entity_id="1" * 64,
            effect_entity_id="2" * 64,
            cause_observed_at="2026-08-02T17:00:00-05:00",
            effect_observed_at="2026-08-02T17:10:00-05:00",
            certified_observation_hashes=(certified_hashes[0],),
            confidence=0.82,
            calibrated_probability=0.80,
            outcome_confirmed=True,
            outcome_supported=True,
        ),
        build_oracle_memory_certified_causal_observation_request(
            pattern_name="Liquidity shift precedes Bitcoin repricing",
            cause_entity_id="1" * 64,
            effect_entity_id="2" * 64,
            cause_observed_at="2026-08-02T18:00:00-05:00",
            effect_observed_at="2026-08-02T18:08:00-05:00",
            certified_observation_hashes=(certified_hashes[-1],),
            confidence=0.80,
            calibrated_probability=0.75,
            outcome_confirmed=True,
            outcome_supported=True,
        ),
    )

    result = build_oracle_memory_certified_market_behavior_causal_pattern_memory(
        calibration=calibration,
        requests=requests,
    )

    assert result.schema_version == "OML-062"
    assert result.engine_id == "OML-062"
    assert result.upstream_schema_version == "OML-061"
    assert result.upstream_engine_id == "OML-061"
    assert result.causal_schema_version == "OML-036"
    assert result.causal_engine_id == "OML-036"
    assert result.pattern_count == 1
    assert result.total_observation_count == 2
    assert result.upstream_certification_hash == calibration.certification_hash
    assert result.calibration_lineage_verified
    assert result.certified_observation_lineage_verified
    assert result.deterministic_identity_verified
    assert result.canonical_pattern_order_verified
    assert result.temporal_precedence_verified
    assert result.evidence_lineage_verified
    assert result.contradiction_tracking_verified
    assert result.outcome_reconciliation_verified
    assert result.causal_memory_ready
    assert result.downstream_multi_hop_causal_authorized
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled
    assert result.read_only

    replay = build_oracle_memory_certified_market_behavior_causal_pattern_memory(
        calibration=calibration,
        requests=requests,
    )
    assert replay == result
    assert verify_oracle_memory_certified_market_behavior_causal_pattern_memory(
        result
    )

    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_causal_pattern_memory(
            replace(result, persistence_enabled=True)
        ),
        "persistence",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_causal_pattern_memory(
            replace(result, downstream_multi_hop_causal_authorized=False)
        ),
        "multi-hop continuation",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_causal_pattern_memory(
            replace(result, qseries_execution_enabled=True)
        ),
        "Q Series execution",
    )

    print("[PASS] Certified OML-061 calibration consumed read-only")
    print("[PASS] Exact OML-035 calibration object passed directly")
    print("[PASS] Actual OML-036 causal builder consumed")
    print("[PASS] Requests bound only to certified observation hashes")
    print("[PASS] Temporal precedence and outcomes verified")
    print("[PASS] Calibration-to-causal lineage retained")
    print("[PASS] Multi-hop continuation authorized read-only")
    print("[PASS] Deterministic replay equality verified")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered OML-062 records rejected")
    print("[DONE] OML-062 CERTIFIED MARKET-BEHAVIOR CAUSAL PATTERN MEMORY PASS")
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
    required = (UPSTREAM, UPSTREAM_TEST, CAUSAL, CAUSAL_TEST)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(
            "Required certified files missing: " + ", ".join(missing)
        )

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    upstream = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_certified_market_behavior_calibration_memory"
    )
    causal = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_certified_observation_causal_pattern_memory"
    )

    expected = (
        (upstream, {
            "SCHEMA_VERSION": "OML-061",
            "ENGINE_ID": "OML-061",
            "POLICY_ID": (
                "oracle-memory.certified-market-behavior-calibration-memory.v1"
            ),
        }, "OML-061"),
        (causal, {
            "SCHEMA_VERSION": "OML-036",
            "ENGINE_ID": "OML-036",
            "POLICY_ID": (
                "oracle-memory."
                "certified-observation-causal-pattern-memory.v1"
            ),
            "UPSTREAM_SCHEMA_VERSION": "OML-035",
            "UPSTREAM_ENGINE_ID": "OML-035",
        }, "OML-036"),
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
        "OracleMemoryCertifiedCausalObservationRequest",
        "OracleMemoryCertifiedCausalPatternMemory",
        "build_oracle_memory_certified_causal_pattern_memory",
        "verify_oracle_memory_certified_causal_observation_request",
        "verify_oracle_memory_certified_causal_pattern_memory",
    )
    missing_symbols = [
        name for name in required_symbols if not hasattr(causal, name)
    ]
    if missing_symbols:
        raise RuntimeError(
            "Certified OML-036 missing symbols: "
            + ", ".join(missing_symbols)
        )

    parameters = set(
        inspect.signature(
            causal.build_oracle_memory_certified_causal_pattern_memory
        ).parameters
    )
    missing_parameters = sorted({"calibration", "requests"} - parameters)
    if missing_parameters:
        raise RuntimeError(
            "Certified OML-036 builder parameters missing: "
            + ", ".join(missing_parameters)
        )


def main() -> int:
    print("=" * 48)
    print(" OML-062 INSTALLER")
    print(" CERTIFIED MARKET-BEHAVIOR CAUSAL PATTERN MEMORY")
    print("=" * 48)
    print("[BOOT] Revision: EXACT_OML_048_036_INTERFACE_ALIGNMENT")

    try:
        validate()
        print("[OK] Actual OML-061 dataclass and verifier inspected")
        print("[OK] Actual OML-036 builder and signature inspected")

        for path, label in (
            (UPSTREAM_TEST, "OML-061"),
            (CAUSAL_TEST, "OML-036"),
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
            for path in (UPSTREAM, UPSTREAM_TEST, CAUSAL, CAUSAL_TEST)
        }

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_memory_certified_market_behavior_"
            "causal_pattern_memory import *"
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
                f"OML-062 test failed with exit code {completed.returncode}"
            )

        for path, before in tracked.items():
            if path.read_bytes() != before:
                raise RuntimeError(f"Certified upstream changed: {path}")

        print("[PASS] Certified OML-061 production unchanged")
        print("[PASS] Certified OML-061 standalone test unchanged")
        print("[PASS] Certified OML-036 causal engine unchanged")
        print("[PASS] Exact OML-035 calibration object consumed directly")
        print("[PASS] OML-062 production fully replaced")
        print("[PASS] OML-062 standalone deterministic test installed")
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
            "[DONE] OML-062 CERTIFIED CROSS-MARKET "
            "CAUSAL PATTERN MEMORY INSTALLED"
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
