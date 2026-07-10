from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence" / "order_flow_discovery_model"
PKG.mkdir(parents=True, exist_ok=True)

MODULE = PKG / "order_flow_pipeline_gate.py"
TEST = ROOT / "test_ofd_004_order_flow_pipeline_gate.py"
INIT = PKG / "__init__.py"

MODULE.write_text(r'''
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Dict, List, Mapping, Tuple

from .order_flow_discovery_engine import OrderFlowDiscoveryResult, discover_order_flow_opportunities


READ_ONLY = True
SCHEMA_VERSION = "OFD-004"
ENGINE_ID = "oracle.discovery.order_flow.pipeline_gate"


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
class OrderFlowPipelineGateResult:
    schema_version: str
    engine_id: str
    status: str
    accepted: bool
    reason: str
    discovery_result_hash: str
    opportunity_count: int
    checks: Dict[str, bool] = field(default_factory=dict)
    read_only: bool = True
    gate_hash: str = ""

    def canonical(self) -> Dict[str, Any]:
        return _deep_sort(asdict(self))


class OrderFlowPipelineGate:
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    read_only = READ_ONLY

    def validate(self, result: OrderFlowDiscoveryResult) -> OrderFlowPipelineGateResult:
        if not isinstance(result, OrderFlowDiscoveryResult):
            raise TypeError("result must be an OrderFlowDiscoveryResult")

        checks = {
            "read_only": result.read_only is True,
            "schema_present": bool(result.schema_version),
            "engine_present": bool(result.engine_id),
            "hash_present": bool(result.result_hash),
            "count_matches": result.opportunity_count == len(result.opportunities),
            "valid_status": result.status in {"ok", "empty"},
            "opportunities_have_ids": all(bool(o.opportunity_id) for o in result.opportunities),
            "opportunities_have_hashes": all(bool(o.opportunity_hash) for o in result.opportunities),
            "confidence_in_range": all(0.0 <= o.confidence <= 1.0 for o in result.opportunities),
            "magnitude_non_negative": all(o.magnitude >= 0.0 for o in result.opportunities),
        }

        accepted = all(checks.values())
        status = "accepted" if accepted else "rejected"
        failed = [name for name, passed in checks.items() if not passed]
        reason = "all checks passed" if accepted else "failed checks: " + ", ".join(failed)

        unsigned = OrderFlowPipelineGateResult(
            schema_version=self.schema_version,
            engine_id=self.engine_id,
            status=status,
            accepted=accepted,
            reason=reason,
            discovery_result_hash=result.result_hash,
            opportunity_count=result.opportunity_count,
            checks=checks,
            read_only=True,
            gate_hash="",
        )

        return OrderFlowPipelineGateResult(
            schema_version=unsigned.schema_version,
            engine_id=unsigned.engine_id,
            status=unsigned.status,
            accepted=unsigned.accepted,
            reason=unsigned.reason,
            discovery_result_hash=unsigned.discovery_result_hash,
            opportunity_count=unsigned.opportunity_count,
            checks=unsigned.checks,
            read_only=True,
            gate_hash=_stable_hash(unsigned.canonical()),
        )

    def assert_read_only(self) -> bool:
        forbidden = ["buy", "sell", "trade", "execute", "order", "sign", "submit", "broadcast"]
        offenders = sorted(word for word in forbidden if word in set(dir(self)))
        if offenders:
            raise AssertionError(f"mutation-like methods are forbidden: {offenders}")
        return True


def validate_order_flow_discovery_result(result: OrderFlowDiscoveryResult) -> OrderFlowPipelineGateResult:
    return OrderFlowPipelineGate().validate(result)


__all__ = [
    "READ_ONLY",
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "OrderFlowPipelineGate",
    "OrderFlowPipelineGateResult",
    "validate_order_flow_discovery_result",
]
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.order_flow_discovery_model.order_flow_discovery_engine import (
    discover_order_flow_opportunities,
)
from qseries_v2.oracle_intelligence.order_flow_discovery_model.order_flow_pipeline_gate import (
    OrderFlowPipelineGate,
    validate_order_flow_discovery_result,
)


def test_order_flow_pipeline_gate_accepts_valid_result():
    raw = [
        {
            "market_id": "KXTEST-YES",
            "venue": "kalshi",
            "instrument": "binary_event",
            "bid_size": 80,
            "ask_size": 20,
            "volume": 2000,
            "open_interest": 7000,
            "observed_at": "2026-07-09T00:00:00+00:00",
        }
    ]

    result = discover_order_flow_opportunities(
        raw,
        source_name="order_flow.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    gate = OrderFlowPipelineGate()
    assert gate.assert_read_only() is True

    gated = gate.validate(result)

    assert gated.schema_version == "OFD-004"
    assert gated.engine_id == "oracle.discovery.order_flow.pipeline_gate"
    assert gated.status == "accepted"
    assert gated.accepted is True
    assert gated.read_only is True
    assert gated.discovery_result_hash == result.result_hash
    assert gated.opportunity_count == result.opportunity_count
    assert gated.gate_hash


def test_order_flow_pipeline_gate_accepts_empty_valid_result():
    result = discover_order_flow_opportunities(
        [],
        source_name="order_flow.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    gated = validate_order_flow_discovery_result(result)

    assert gated.status == "accepted"
    assert gated.accepted is True
    assert gated.opportunity_count == 0
    assert all(gated.checks.values())


def test_order_flow_pipeline_gate_is_replayable():
    result = discover_order_flow_opportunities(
        [],
        source_name="order_flow.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    gated1 = validate_order_flow_discovery_result(result)
    gated2 = validate_order_flow_discovery_result(result)

    assert gated1.gate_hash == gated2.gate_hash


if __name__ == "__main__":
    test_order_flow_pipeline_gate_accepts_valid_result()
    test_order_flow_pipeline_gate_accepts_empty_valid_result()
    test_order_flow_pipeline_gate_is_replayable()

    result = discover_order_flow_opportunities(
        [],
        source_name="order_flow.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )
    gated = validate_order_flow_discovery_result(result)

    print("[PASS] OFD-004 Order Flow Pipeline Gate")
    print(
        {
            "schema_version": gated.schema_version,
            "engine_id": gated.engine_id,
            "status": gated.status,
            "accepted": gated.accepted,
            "read_only": gated.read_only,
        }
    )
''', encoding="utf-8")

existing = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
exports = '''
from .order_flow_pipeline_gate import (
    OrderFlowPipelineGate,
    OrderFlowPipelineGateResult,
    validate_order_flow_discovery_result,
)
'''
if "order_flow_pipeline_gate" not in existing:
    INIT.write_text(existing.rstrip() + "\n" + exports.lstrip(), encoding="utf-8")

print("========================================")
print(" OFD-004 INSTALLER")
print(" Order Flow Pipeline Gate")
print("========================================")
print(f"[OK] Wrote {MODULE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OFD-004 installed")
print()
print("Run:")
print("py test_ofd_004_order_flow_pipeline_gate.py")