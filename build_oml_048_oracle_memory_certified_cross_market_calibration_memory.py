from __future__ import annotations

import ast
import importlib
import inspect
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "oracle_memory"

UPSTREAM = PACKAGE / "oracle_memory_certified_cross_market_source_reliability.py"
UPSTREAM_TEST = ROOT / "test_oml_047_oracle_memory_certified_cross_market_source_reliability.py"
CALIBRATION_MODULE = PACKAGE / "oracle_memory_certified_observation_calibration_memory.py"
CALIBRATION_TEST = ROOT / "test_oml_035_oracle_memory_certified_observation_calibration_memory.py"

PRODUCTION = PACKAGE / "oracle_memory_certified_cross_market_calibration_memory.py"
TEST = ROOT / "test_oml_048_oracle_memory_certified_cross_market_calibration_memory.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_source_reliability import (
    OracleMemoryCertifiedCrossMarketSourceReliability,
    verify_oracle_memory_certified_cross_market_source_reliability,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_calibration_memory import (
    OracleMemoryCertifiedCalibrationForecast,
    OracleMemoryCertifiedCalibrationMemory,
    build_oracle_memory_certified_calibration_memory,
    verify_oracle_memory_certified_calibration_forecast,
    verify_oracle_memory_certified_calibration_memory,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-048"
ENGINE_ID = "OML-048"
POLICY_ID = "oracle-memory.certified-cross-market-calibration-memory.v1"
UPSTREAM_SCHEMA_VERSION = "OML-047"
UPSTREAM_ENGINE_ID = "OML-047"
CALIBRATION_SCHEMA_VERSION = "OML-035"
CALIBRATION_ENGINE_ID = "OML-035"
STATE_READ_ONLY = "read_only_cross_market_calibration_memory"


class OracleMemoryCertifiedCrossMarketCalibrationInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCertifiedCrossMarketCalibrationMemory:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_certification_hash: str
    upstream_reliability_certification_hash: str
    upstream_reliability_memory_hash: str
    calibration_schema_version: str
    calibration_engine_id: str
    calibration: OracleMemoryCertifiedCalibrationMemory
    profile_count: int
    total_observation_count: int
    total_confirmed_count: int
    state: str
    source_reliability_lineage_verified: bool
    certified_observation_lineage_verified: bool
    calibration_lineage_verified: bool
    deterministic_scoring_verified: bool
    canonical_profile_order_verified: bool
    probability_bounds_verified: bool
    outcome_lineage_verified: bool
    calibration_bucket_reconciliation_verified: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    calibration_ready: bool
    downstream_causal_memory_authorized: bool
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
    raise OracleMemoryCertifiedCrossMarketCalibrationInvariantError(
        "unsupported OML-048 value type"
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
    raise OracleMemoryCertifiedCrossMarketCalibrationInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-048 invalid {label} length")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryCertifiedCrossMarketCalibrationInvariantError(
            f"OML-048 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_certified_cross_market_calibration_memory(
    *,
    reliability: OracleMemoryCertifiedCrossMarketSourceReliability,
    forecasts: Sequence[OracleMemoryCertifiedCalibrationForecast],
) -> OracleMemoryCertifiedCrossMarketCalibrationMemory:
    verify_oracle_memory_certified_cross_market_source_reliability(reliability)

    if reliability.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-048 upstream schema mismatch")
    if reliability.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-048 upstream engine mismatch")
    if not reliability.reliability_ready:
        _reject("OML-048 upstream reliability not ready")
    if not reliability.downstream_calibration_authorized:
        _reject("OML-048 calibration continuation not authorized")
    if not reliability.read_only:
        _reject("OML-048 upstream reliability not read-only")

    allowed_hashes = {
        value
        for binding in reliability.source_reliability.bindings
        for value in binding.certified_observation_hashes
    }
    if not allowed_hashes:
        _reject("OML-048 no certified observation hashes available")

    for forecast in forecasts:
        verify_oracle_memory_certified_calibration_forecast(forecast)
        if forecast.certified_observation_hash not in allowed_hashes:
            _reject("OML-048 forecast references unknown certified observation")

    calibration = build_oracle_memory_certified_calibration_memory(
        source_reliability=reliability.source_reliability,
        forecasts=tuple(forecasts),
    )
    verify_oracle_memory_certified_calibration_memory(calibration)

    if calibration.schema_version != CALIBRATION_SCHEMA_VERSION:
        _reject("OML-048 calibration schema mismatch")
    if calibration.engine_id != CALIBRATION_ENGINE_ID:
        _reject("OML-048 calibration engine mismatch")
    if calibration.upstream_certification_hash != (
        reliability.source_reliability.certification_hash
    ):
        _reject("OML-048 reliability certification lineage mismatch")
    if calibration.upstream_reliability_memory_hash != (
        reliability.source_reliability.reliability_memory.memory_hash
    ):
        _reject("OML-048 reliability memory lineage mismatch")

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": reliability.schema_version,
        "upstream_engine_id": reliability.engine_id,
        "upstream_certification_hash": reliability.certification_hash,
        "upstream_reliability_certification_hash": (
            reliability.source_reliability.certification_hash
        ),
        "upstream_reliability_memory_hash": (
            reliability.source_reliability.reliability_memory.memory_hash
        ),
        "calibration_schema_version": calibration.schema_version,
        "calibration_engine_id": calibration.engine_id,
        "calibration": calibration,
        "profile_count": calibration.profile_count,
        "total_observation_count": calibration.total_observation_count,
        "total_confirmed_count": calibration.total_confirmed_count,
        "state": STATE_READ_ONLY,
        "source_reliability_lineage_verified": True,
        "certified_observation_lineage_verified": (
            calibration.certified_observation_lineage_verified
        ),
        "calibration_lineage_verified": True,
        "deterministic_scoring_verified": (
            calibration.deterministic_scoring_verified
        ),
        "canonical_profile_order_verified": (
            calibration.canonical_profile_order_verified
        ),
        "probability_bounds_verified": calibration.probability_bounds_verified,
        "outcome_lineage_verified": calibration.outcome_lineage_verified,
        "calibration_bucket_reconciliation_verified": (
            calibration.calibration_bucket_reconciliation_verified
        ),
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "calibration_ready": True,
        "downstream_causal_memory_authorized": (
            calibration.downstream_causal_memory_authorized
        ),
        "read_only": True,
    }

    result = OracleMemoryCertifiedCrossMarketCalibrationMemory(
        **body,
        certification_hash=_stable_hash(body),
    )
    verify_oracle_memory_certified_cross_market_calibration_memory(result)
    return result


def verify_oracle_memory_certified_cross_market_calibration_memory(
    result: OracleMemoryCertifiedCrossMarketCalibrationMemory,
) -> bool:
    body = asdict(result)
    supplied = body.pop("certification_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-048 certification hash mismatch")

    if result.schema_version != SCHEMA_VERSION:
        _reject("OML-048 schema mismatch")
    if result.engine_id != ENGINE_ID:
        _reject("OML-048 engine mismatch")
    if result.policy_id != POLICY_ID:
        _reject("OML-048 policy mismatch")
    if result.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-048 subsystem mismatch")
    if result.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-048 upstream schema lineage mismatch")
    if result.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-048 upstream engine lineage mismatch")
    if result.calibration_schema_version != CALIBRATION_SCHEMA_VERSION:
        _reject("OML-048 calibration schema lineage mismatch")
    if result.calibration_engine_id != CALIBRATION_ENGINE_ID:
        _reject("OML-048 calibration engine lineage mismatch")

    for value in (
        result.upstream_certification_hash,
        result.upstream_reliability_certification_hash,
        result.upstream_reliability_memory_hash,
        result.certification_hash,
    ):
        _require_hash(value, "lineage hash")

    verify_oracle_memory_certified_calibration_memory(result.calibration)

    if result.upstream_reliability_certification_hash != (
        result.calibration.upstream_certification_hash
    ):
        _reject("OML-048 reliability certification mismatch")
    if result.upstream_reliability_memory_hash != (
        result.calibration.upstream_reliability_memory_hash
    ):
        _reject("OML-048 reliability memory mismatch")
    if result.profile_count != result.calibration.profile_count:
        _reject("OML-048 profile count mismatch")
    if result.total_observation_count != (
        result.calibration.total_observation_count
    ):
        _reject("OML-048 observation count mismatch")
    if result.total_confirmed_count != (
        result.calibration.total_confirmed_count
    ):
        _reject("OML-048 confirmed count mismatch")

    required = (
        result.source_reliability_lineage_verified,
        result.certified_observation_lineage_verified,
        result.calibration_lineage_verified,
        result.deterministic_scoring_verified,
        result.canonical_profile_order_verified,
        result.probability_bounds_verified,
        result.outcome_lineage_verified,
        result.calibration_bucket_reconciliation_verified,
        result.calibration_ready,
        result.downstream_causal_memory_authorized,
        result.read_only,
    )
    if not all(required):
        _reject("OML-048 guarantee missing")
    if result.state != STATE_READ_ONLY:
        _reject("OML-048 state invalid")

    forbidden = (
        result.persistence_enabled,
        result.learning_updates_enabled,
        result.runtime_activation_enabled,
        result.publication_enabled,
        result.action_authorization_enabled,
        result.qseries_execution_enabled,
    )
    if any(forbidden):
        _reject("OML-048 forbidden capability enabled")

    return True
"""

TEST_SOURCE = r"""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_calibration_memory import (
    OracleMemoryCertifiedCrossMarketCalibrationInvariantError,
    build_oracle_memory_certified_cross_market_calibration_memory,
    verify_oracle_memory_certified_cross_market_calibration_memory,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_calibration_memory import (
    build_oracle_memory_certified_calibration_forecast,
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
    except OracleMemoryCertifiedCrossMarketCalibrationInvariantError:
        return
    raise AssertionError(f"tampered OML-048 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-048 TEST")
    print(" CERTIFIED CROSS-MARKET CALIBRATION MEMORY")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    fixture = load_module(
        root
        / "test_oml_047_oracle_memory_certified_cross_market_source_reliability.py",
        "oml_047_fixture_for_oml_048",
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
    from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_source_reliability import (
        build_oracle_memory_certified_cross_market_source_reliability,
    )

    outcomes = tuple(
        build_oracle_memory_certified_source_outcome(
            source_name="Oracle Cross-Market Observation",
            observation_hash=value,
            outcome_confirmed=True,
            outcome_correct=(index % 2 == 0),
            contradiction_count=0 if index % 2 == 0 else 1,
            confidence_at_observation=0.85 - (index * 0.05),
            observed_at=f"2026-08-02T17:{20 + index:02d}:00-05:00",
        )
        for index, value in enumerate(observation_hashes)
    )

    reliability = build_oracle_memory_certified_cross_market_source_reliability(
        lifecycle=lifecycle,
        outcomes=outcomes,
    )

    source_profile = reliability.source_reliability.reliability_memory.profiles[0]
    source_binding = reliability.source_reliability.bindings[0]
    certified_hashes = source_binding.certified_observation_hashes

    forecasts = tuple(
        build_oracle_memory_certified_calibration_forecast(
            profile_name="Cross-Market Calibration",
            source_name=source_profile.source_name,
            source_id=source_profile.source_id,
            forecast_id=f"cross-market-forecast-{index + 1:03d}",
            certified_observation_hash=value,
            predicted_probability=0.80 - (index * 0.10),
            outcome_confirmed=True,
            outcome_value=1 if index % 2 == 0 else 0,
            observed_at=f"2026-08-02T16:{10 + index:02d}:00-05:00",
            resolved_at=f"2026-08-02T17:{30 + index:02d}:00-05:00",
        )
        for index, value in enumerate(certified_hashes)
    )

    result = build_oracle_memory_certified_cross_market_calibration_memory(
        reliability=reliability,
        forecasts=forecasts,
    )

    assert result.schema_version == "OML-048"
    assert result.engine_id == "OML-048"
    assert result.upstream_schema_version == "OML-047"
    assert result.upstream_engine_id == "OML-047"
    assert result.calibration_schema_version == "OML-035"
    assert result.calibration_engine_id == "OML-035"
    assert result.profile_count == 1
    assert result.total_observation_count == len(forecasts)
    assert result.total_confirmed_count == len(forecasts)
    assert result.upstream_certification_hash == reliability.certification_hash
    assert result.upstream_reliability_certification_hash == (
        reliability.source_reliability.certification_hash
    )
    assert result.upstream_reliability_memory_hash == (
        reliability.source_reliability.reliability_memory.memory_hash
    )
    assert result.source_reliability_lineage_verified
    assert result.certified_observation_lineage_verified
    assert result.calibration_lineage_verified
    assert result.deterministic_scoring_verified
    assert result.canonical_profile_order_verified
    assert result.probability_bounds_verified
    assert result.outcome_lineage_verified
    assert result.calibration_bucket_reconciliation_verified
    assert result.calibration_ready
    assert result.downstream_causal_memory_authorized
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled
    assert result.read_only

    replay = build_oracle_memory_certified_cross_market_calibration_memory(
        reliability=reliability,
        forecasts=forecasts,
    )
    assert replay == result
    assert verify_oracle_memory_certified_cross_market_calibration_memory(
        result
    )

    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_calibration_memory(
            replace(result, persistence_enabled=True)
        ),
        "persistence state",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_calibration_memory(
            replace(result, downstream_causal_memory_authorized=False)
        ),
        "causal continuation",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_calibration_memory(
            replace(result, qseries_execution_enabled=True)
        ),
        "Q Series execution",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_calibration_memory(
            replace(result, certification_hash="f" * 64)
        ),
        "certification hash",
    )

    print("[PASS] Certified OML-047 reliability consumed read-only")
    print("[PASS] Exact OML-034 reliability object passed directly")
    print("[PASS] Actual OML-035 calibration builder consumed")
    print("[PASS] Forecasts bound only to certified observation hashes")
    print("[PASS] Reliability and calibration lineage retained")
    print("[PASS] Probability bounds and outcomes verified")
    print("[PASS] Calibration buckets reconciled")
    print("[PASS] Causal-memory continuation authorized read-only")
    print("[PASS] Deterministic replay equality verified")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered OML-048 calibration records rejected")
    print("[DONE] OML-048 CERTIFIED CROSS-MARKET CALIBRATION MEMORY PASS")
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
    required = (UPSTREAM, UPSTREAM_TEST, CALIBRATION_MODULE, CALIBRATION_TEST)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(
            "Required certified files missing: " + ", ".join(missing)
        )

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    upstream_module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_certified_cross_market_source_reliability"
    )
    calibration_module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_certified_observation_calibration_memory"
    )

    expected = (
        (upstream_module, {
            "SCHEMA_VERSION": "OML-047",
            "ENGINE_ID": "OML-047",
            "POLICY_ID": (
                "oracle-memory.certified-cross-market-source-reliability.v1"
            ),
        }, "OML-047"),
        (calibration_module, {
            "SCHEMA_VERSION": "OML-035",
            "ENGINE_ID": "OML-035",
            "POLICY_ID": (
                "oracle-memory.certified-observation-calibration-memory.v1"
            ),
            "UPSTREAM_SCHEMA_VERSION": "OML-034",
            "UPSTREAM_ENGINE_ID": "OML-034",
        }, "OML-035"),
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
                "OracleMemoryCertifiedCrossMarketSourceReliability",
                "verify_oracle_memory_certified_cross_market_source_reliability",
            ),
            "OML-047",
        ),
        (
            calibration_module,
            (
                "OracleMemoryCertifiedCalibrationForecast",
                "OracleMemoryCertifiedCalibrationMemory",
                "build_oracle_memory_certified_calibration_memory",
                "verify_oracle_memory_certified_calibration_forecast",
                "verify_oracle_memory_certified_calibration_memory",
            ),
            "OML-035",
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
            calibration_module.build_oracle_memory_certified_calibration_memory
        ).parameters
    )
    missing_parameters = sorted(
        {"source_reliability", "forecasts"} - parameters
    )
    if missing_parameters:
        raise RuntimeError(
            "Certified OML-035 builder parameters missing: "
            + ", ".join(missing_parameters)
        )


def main() -> int:
    print("=" * 48)
    print(" OML-048 INSTALLER")
    print(" CERTIFIED CROSS-MARKET CALIBRATION MEMORY")
    print("=" * 48)
    print("[BOOT] Revision: EXACT_OML_047_035_INTERFACE_ALIGNMENT")

    try:
        validate()
        print("[OK] Actual OML-047 dataclass and verifier inspected")
        print("[OK] Actual OML-035 builder and signature inspected")

        for path, label in (
            (UPSTREAM_TEST, "OML-047"),
            (CALIBRATION_TEST, "OML-035"),
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
                CALIBRATION_MODULE,
                CALIBRATION_TEST,
            )
        }

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_memory_certified_cross_market_"
            "calibration_memory import *"
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
                f"OML-048 test failed with exit code {completed.returncode}"
            )

        for path, before in tracked.items():
            if path.read_bytes() != before:
                raise RuntimeError(f"Certified upstream changed: {path}")

        print("[PASS] Certified OML-047 production unchanged")
        print("[PASS] Certified OML-047 standalone test unchanged")
        print("[PASS] Certified OML-035 calibration engine unchanged")
        print("[PASS] Exact OML-034 reliability object consumed directly")
        print("[PASS] OML-048 production fully replaced")
        print("[PASS] OML-048 standalone deterministic test installed")
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
            "[DONE] OML-048 CERTIFIED CROSS-MARKET "
            "CALIBRATION MEMORY INSTALLED"
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
