from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence" / "order_flow_discovery_model"
PKG.mkdir(parents=True, exist_ok=True)

MODULE = PKG / "order_flow_oos_runtime_gate.py"
TEST = ROOT / "test_ofd_007_order_flow_oos_runtime_gate.py"
INIT = PKG / "__init__.py"

MODULE.write_text(r'''
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Dict, Iterable, Mapping, Optional

from .order_flow_pipeline_bridge import (
    OrderFlowPipelineBridgeResult,
    run_order_flow_pipeline,
)


READ_ONLY = True
SCHEMA_VERSION = "OFD-007"
ENGINE_ID = "oracle.discovery.order_flow.oos_runtime_gate"


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
class OrderFlowOOSRuntimeGateResult:
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


class OrderFlowOOSRuntimeGate:
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
        pipeline_result: OrderFlowPipelineBridgeResult,
        runtime_context: Optional[Mapping[str, Any]] = None,
    ) -> OrderFlowOOSRuntimeGateResult:
        if not isinstance(pipeline_result, OrderFlowPipelineBridgeResult):
            raise TypeError("pipeline_result must be an OrderFlowPipelineBridgeResult")

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
            "no_execution_context": not bool(context.get("execute") or context.get("trade") or context.get("submit_order")),
        }

        accepted = all(checks.values())
        status = "accepted" if accepted else "rejected"
        failed = [name for name, passed in checks.items() if not passed]
        reason = "all OOS runtime checks passed" if accepted else "failed checks: " + ", ".join(failed)

        clean_context = _deep_sort(context)

        unsigned = OrderFlowOOSRuntimeGateResult(
            schema_version=self.schema_version,
            engine_id=self.engine_id,
            status=status,
            accepted=accepted,
            reason=reason,
            pipeline_hash=pipeline_result.pipeline_hash,
            opportunity_count=pipeline_result.opportunity_count,
            checks=checks,
            runtime_context=clean_context,
            read_only=True,
            oos_hash="",
        )

        return OrderFlowOOSRuntimeGateResult(
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


def validate_order_flow_oos_runtime(
    pipeline_result: OrderFlowPipelineBridgeResult,
    runtime_context: Optional[Mapping[str, Any]] = None,
) -> OrderFlowOOSRuntimeGateResult:
    return OrderFlowOOSRuntimeGate().validate(
        pipeline_result=pipeline_result,
        runtime_context=runtime_context,
    )


def run_order_flow_oos_runtime_gate(
    raw_records: Iterable[Mapping[str, Any]],
    source_name: str = "order_flow.generic",
    observed_at: Optional[str] = None,
    runtime_context: Optional[Mapping[str, Any]] = None,
) -> OrderFlowOOSRuntimeGateResult:
    pipeline = run_order_flow_pipeline(
        raw_records=raw_records,
        source_name=source_name,
        observed_at=observed_at,
    )
    return validate_order_flow_oos_runtime(
        pipeline_result=pipeline,
        runtime_context=runtime_context,
    )


__all__ = [
    "READ_ONLY",
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "OrderFlowOOSRuntimeGate",
    "OrderFlowOOSRuntimeGateResult",
    "validate_order_flow_oos_runtime",
    "run_order_flow_oos_runtime_gate",
]
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.order_flow_discovery_model.order_flow_oos_runtime_gate import (
    OrderFlowOOSRuntimeGate,
    run_order_flow_oos_runtime_gate,
    validate_order_flow_oos_runtime,
)
from qseries_v2.oracle_intelligence.order_flow_discovery_model.order_flow_pipeline_bridge import (
    run_order_flow_pipeline,
)


RAW = [
    {
        "market_id": "KXTEST-YES",
        "venue": "kalshi",
        "instrument": "binary_event",
        "bid_size": 85,
        "ask_size": 15,
        "bid_price": 0.42,
        "ask_price": 0.45,
        "last_price": 0.43,
        "volume": 2500,
        "open_interest": 7000,
        "observed_at": "2026-07-09T00:00:00+00:00",
    }
]


def test_order_flow_oos_runtime_gate_accepts_valid_pipeline():
    pipeline = run_order_flow_pipeline(
        RAW,
        source_name="order_flow.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    gate = OrderFlowOOSRuntimeGate()
    assert gate.assert_read_only() is True

    result = gate.validate(
        pipeline,
        runtime_context={"mode": "oos", "fold": "test-fold-001"},
    )

    assert result.schema_version == "OFD-007"
    assert result.engine_id == "oracle.discovery.order_flow.oos_runtime_gate"
    assert result.status == "accepted"
    assert result.accepted is True
    assert result.read_only is True
    assert result.pipeline_hash == pipeline.pipeline_hash
    assert result.opportunity_count == pipeline.opportunity_count
    assert result.checks["no_execution_context"] is True
    assert result.oos_hash


def test_order_flow_oos_runtime_gate_rejects_execution_context():
    pipeline = run_order_flow_pipeline(
        RAW,
        source_name="order_flow.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    result = validate_order_flow_oos_runtime(
        pipeline,
        runtime_context={"mode": "oos", "execute": True},
    )

    assert result.status == "rejected"
    assert result.accepted is False
    assert result.checks["no_execution_context"] is False
    assert result.read_only is True


def test_order_flow_oos_runtime_gate_is_replayable():
    r1 = run_order_flow_oos_runtime_gate(
        RAW,
        source_name="order_flow.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "replay", "fold": "A"},
    )
    r2 = run_order_flow_oos_runtime_gate(
        list(reversed(RAW)),
        source_name="order_flow.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"fold": "A", "mode": "replay"},
    )

    assert r1.oos_hash == r2.oos_hash


def test_order_flow_oos_runtime_gate_accepts_empty_pipeline():
    result = run_order_flow_oos_runtime_gate(
        [],
        source_name="order_flow.empty",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "shadow"},
    )

    assert result.status == "accepted"
    assert result.accepted is True
    assert result.opportunity_count == 0
    assert result.read_only is True


if __name__ == "__main__":
    test_order_flow_oos_runtime_gate_accepts_valid_pipeline()
    test_order_flow_oos_runtime_gate_rejects_execution_context()
    test_order_flow_oos_runtime_gate_is_replayable()
    test_order_flow_oos_runtime_gate_accepts_empty_pipeline()

    result = run_order_flow_oos_runtime_gate(
        [],
        source_name="order_flow.empty",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "oos"},
    )

    print("[PASS] OFD-007 Order Flow OOS Runtime Gate")
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
from .order_flow_oos_runtime_gate import (
    OrderFlowOOSRuntimeGate,
    OrderFlowOOSRuntimeGateResult,
    validate_order_flow_oos_runtime,
    run_order_flow_oos_runtime_gate,
)
'''
if "order_flow_oos_runtime_gate" not in existing:
    INIT.write_text(existing.rstrip() + "\n" + exports.lstrip(), encoding="utf-8")

print("========================================")
print(" OFD-007 INSTALLER")
print(" Order Flow OOS Runtime Gate")
print("========================================")
print(f"[OK] Wrote {MODULE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OFD-007 installed")
print()
print("Run:")
print("py test_ofd_007_order_flow_oos_runtime_gate.py")