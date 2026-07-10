from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence" / "volatility_discovery_model"
PKG.mkdir(parents=True, exist_ok=True)

MODULE = PKG / "volatility_oos_runtime_gate.py"
TEST = ROOT / "test_vld_007_volatility_oos_runtime_gate.py"
INIT = PKG / "__init__.py"

MODULE.write_text(r'''
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Dict, Iterable, Mapping, Optional

from .volatility_pipeline_bridge import (
    VolatilityPipelineBridgeResult,
    run_volatility_pipeline,
)


READ_ONLY = True
SCHEMA_VERSION = "VLD-007"
ENGINE_ID = "oracle.discovery.volatility.oos_runtime_gate"


def _deep_sort(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _deep_sort(value[k]) for k in sorted(value.keys(), key=str)}
    if isinstance(value, list):
        return [_deep_sort(v) for v in value]
    if isinstance(value, tuple):
        return tuple(_deep_sort(v) for v in value)
    return value


def _stable_hash(payload: Mapping[str, Any]) -> str:
    return sha256(repr(_deep_sort(payload)).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class VolatilityOOSRuntimeGateResult:
    schema_version: str
    engine_id: str
    status: str
    accepted: bool
    reason: str
    pipeline_hash: str
    opportunity_count: int
    checks: Dict[str, bool] = field(default_factory=dict)
    runtime_context: Dict[str, Any] = field(default_factory=dict)
    read_only: bool = True
    oos_hash: str = ""

    def canonical(self) -> Dict[str, Any]:
        return _deep_sort(asdict(self))


class VolatilityOOSRuntimeGate:
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    read_only = READ_ONLY

    def __init__(
        self,
        require_accepted_pipeline: bool = True,
        max_opportunities: int = 10000,
    ) -> None:
        self.require_accepted_pipeline = bool(require_accepted_pipeline)
        self.max_opportunities = int(max_opportunities)

    def validate(
        self,
        pipeline_result: VolatilityPipelineBridgeResult,
        runtime_context: Optional[Mapping[str, Any]] = None,
    ) -> VolatilityOOSRuntimeGateResult:
        if not isinstance(pipeline_result, VolatilityPipelineBridgeResult):
            raise TypeError("pipeline_result must be a VolatilityPipelineBridgeResult")

        context = dict(runtime_context or {})
        mode = str(context.get("mode", "oos"))

        checks = {
            "read_only": pipeline_result.read_only is True,
            "schema_present": bool(pipeline_result.schema_version),
            "engine_present": bool(pipeline_result.engine_id),
            "pipeline_hash_present": bool(pipeline_result.pipeline_hash),
            "pipeline_accepted": (pipeline_result.accepted is True) if self.require_accepted_pipeline else True,
            "opportunity_count_matches": pipeline_result.opportunity_count == pipeline_result.discovery.opportunity_count,
            "opportunity_count_within_limit": 0 <= pipeline_result.opportunity_count <= self.max_opportunities,
            "gate_accepted": pipeline_result.gate.accepted is True,
            "registry_accepted": pipeline_result.registry_entry.accepted is True,
            "runtime_mode_valid": mode in {"oos", "replay", "paper", "shadow"},
            "no_execution_context": not bool(
                context.get("execute")
                or context.get("trade")
                or context.get("submit_order")
                or context.get("place_order")
                or context.get("sign_transaction")
            ),
        }

        accepted = all(checks.values())
        status = "accepted" if accepted else "rejected"
        failed = [name for name, passed in checks.items() if not passed]
        reason = "all volatility OOS runtime checks passed" if accepted else "failed checks: " + ", ".join(failed)

        unsigned = VolatilityOOSRuntimeGateResult(
            schema_version=self.schema_version,
            engine_id=self.engine_id,
            status=status,
            accepted=accepted,
            reason=reason,
            pipeline_hash=pipeline_result.pipeline_hash,
            opportunity_count=pipeline_result.opportunity_count,
            checks=checks,
            runtime_context=_deep_sort(context),
            read_only=True,
            oos_hash="",
        )

        return VolatilityOOSRuntimeGateResult(
            schema_version=unsigned.schema_version,
            engine_id=unsigned.engine_id,
            status=unsigned.status,
            accepted=unsigned.accepted,
            reason=unsigned.reason,
            pipeline_hash=unsigned.pipeline_hash,
            opportunity_count=unsigned.opportunity_count,
            checks=unsigned.checks,
            runtime_context=unsigned.runtime_context,
            read_only=True,
            oos_hash=_stable_hash(unsigned.canonical()),
        )

    def assert_read_only(self) -> bool:
        forbidden = ["buy", "sell", "trade", "execute", "order", "sign", "submit", "broadcast"]
        offenders = sorted(word for word in forbidden if word in set(dir(self)))
        if offenders:
            raise AssertionError(f"mutation-like methods are forbidden: {offenders}")
        return True


def validate_volatility_oos_runtime(
    pipeline_result: VolatilityPipelineBridgeResult,
    runtime_context: Optional[Mapping[str, Any]] = None,
) -> VolatilityOOSRuntimeGateResult:
    return VolatilityOOSRuntimeGate().validate(
        pipeline_result=pipeline_result,
        runtime_context=runtime_context,
    )


def run_volatility_oos_runtime_gate(
    raw_records: Iterable[Mapping[str, Any]],
    source_name: str = "volatility.generic",
    observed_at: Optional[str] = None,
    runtime_context: Optional[Mapping[str, Any]] = None,
) -> VolatilityOOSRuntimeGateResult:
    pipeline = run_volatility_pipeline(
        raw_records=raw_records,
        source_name=source_name,
        observed_at=observed_at,
    )
    return validate_volatility_oos_runtime(
        pipeline_result=pipeline,
        runtime_context=runtime_context,
    )


__all__ = [
    "READ_ONLY",
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "VolatilityOOSRuntimeGate",
    "VolatilityOOSRuntimeGateResult",
    "validate_volatility_oos_runtime",
    "run_volatility_oos_runtime_gate",
]
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.volatility_discovery_model.volatility_oos_runtime_gate import (
    VolatilityOOSRuntimeGate,
    run_volatility_oos_runtime_gate,
    validate_volatility_oos_runtime,
)
from qseries_v2.oracle_intelligence.volatility_discovery_model.volatility_pipeline_bridge import (
    run_volatility_pipeline,
)


RAW = [
    {
        "market_id": "KXVOL-EXPAND",
        "venue": "kalshi",
        "asset": "binary_event",
        "realized_volatility": 0.42,
        "implied_volatility": 0.20,
        "baseline_volatility": 0.20,
        "price_change": 0.08,
        "volume": 12000,
        "window": "1d",
        "observed_at": "2026-07-09T00:00:00+00:00",
    }
]


def test_volatility_oos_runtime_gate_accepts_valid_pipeline():
    pipeline = run_volatility_pipeline(
        RAW,
        source_name="volatility.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    gate = VolatilityOOSRuntimeGate()
    assert gate.assert_read_only() is True

    result = gate.validate(
        pipeline,
        runtime_context={"mode": "oos", "fold": "test-fold-001"},
    )

    assert result.schema_version == "VLD-007"
    assert result.engine_id == "oracle.discovery.volatility.oos_runtime_gate"
    assert result.status == "accepted"
    assert result.accepted is True
    assert result.read_only is True
    assert result.pipeline_hash == pipeline.pipeline_hash
    assert result.opportunity_count == pipeline.opportunity_count
    assert result.checks["no_execution_context"] is True
    assert result.oos_hash


def test_volatility_oos_runtime_gate_rejects_execution_context():
    pipeline = run_volatility_pipeline(
        RAW,
        source_name="volatility.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    result = validate_volatility_oos_runtime(
        pipeline,
        runtime_context={"mode": "oos", "execute": True},
    )

    assert result.status == "rejected"
    assert result.accepted is False
    assert result.checks["no_execution_context"] is False
    assert result.read_only is True


def test_volatility_oos_runtime_gate_is_replayable():
    r1 = run_volatility_oos_runtime_gate(
        RAW,
        source_name="volatility.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "replay", "fold": "A"},
    )
    r2 = run_volatility_oos_runtime_gate(
        list(reversed(RAW)),
        source_name="volatility.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"fold": "A", "mode": "replay"},
    )

    assert r1.oos_hash == r2.oos_hash


def test_volatility_oos_runtime_gate_accepts_empty_pipeline():
    result = run_volatility_oos_runtime_gate(
        [],
        source_name="volatility.empty",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "shadow"},
    )

    assert result.status == "accepted"
    assert result.accepted is True
    assert result.opportunity_count == 0
    assert result.read_only is True


if __name__ == "__main__":
    test_volatility_oos_runtime_gate_accepts_valid_pipeline()
    test_volatility_oos_runtime_gate_rejects_execution_context()
    test_volatility_oos_runtime_gate_is_replayable()
    test_volatility_oos_runtime_gate_accepts_empty_pipeline()

    result = run_volatility_oos_runtime_gate(
        [],
        source_name="volatility.empty",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "oos"},
    )

    print("[PASS] VLD-007 Volatility OOS Runtime Gate")
    print(
        {
            "schema_version": result.schema_version,
            "engine_id": result.engine_id,
            "status": result.status,
            "accepted": result.accepted,
            "opportunities": result.opportunity_count,
            "read_only": result.read_only,
        }
    )
''', encoding="utf-8")

existing = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
exports = '''
from .volatility_oos_runtime_gate import (
    VolatilityOOSRuntimeGate,
    VolatilityOOSRuntimeGateResult,
    validate_volatility_oos_runtime,
    run_volatility_oos_runtime_gate,
)
'''
if "volatility_oos_runtime_gate" not in existing:
    INIT.write_text(existing.rstrip() + "\n" + exports.lstrip(), encoding="utf-8")

print("========================================")
print(" VLD-007 INSTALLER")
print(" Volatility OOS Runtime Gate")
print("========================================")
print(f"[OK] Wrote {MODULE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] VLD-007 installed")
print()
print("Run:")
print("py test_vld_007_volatility_oos_runtime_gate.py")