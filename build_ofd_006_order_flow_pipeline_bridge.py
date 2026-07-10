from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence" / "order_flow_discovery_model"
PKG.mkdir(parents=True, exist_ok=True)

MODULE = PKG / "order_flow_pipeline_bridge.py"
TEST = ROOT / "test_ofd_006_order_flow_pipeline_bridge.py"
INIT = PKG / "__init__.py"

MODULE.write_text(r'''
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Dict, Iterable, Mapping, Optional

from .order_flow_discovery_engine import (
    OrderFlowDiscoveryEngine,
    OrderFlowDiscoveryResult,
)
from .order_flow_pipeline_gate import (
    OrderFlowPipelineGate,
    OrderFlowPipelineGateResult,
)
from .order_flow_registry_bridge import (
    OrderFlowRegistryBridge,
    OrderFlowRegistryEntry,
)


READ_ONLY = True
SCHEMA_VERSION = "OFD-006"
ENGINE_ID = "oracle.discovery.order_flow.pipeline_bridge"


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
class OrderFlowPipelineBridgeResult:
    schema_version: str
    engine_id: str
    status: str
    accepted: bool
    source_name: str
    observed_at: str
    discovery: OrderFlowDiscoveryResult
    gate: OrderFlowPipelineGateResult
    registry_entry: OrderFlowRegistryEntry
    opportunity_count: int
    read_only: bool = True
    pipeline_hash: str = ""
    audit: Dict[str, Any] = field(default_factory=dict)

    def canonical(self) -> Dict[str, Any]:
        data = asdict(self)
        return _deep_sort(data)


class OrderFlowPipelineBridge:
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    read_only = READ_ONLY

    def __init__(
        self,
        source_name: str = "order_flow.generic",
        min_abs_imbalance: float = 0.25,
        min_volume: float = 0.0,
        min_open_interest: float = 0.0,
    ) -> None:
        self.source_name = str(source_name or "order_flow.generic")
        self.discovery_engine = OrderFlowDiscoveryEngine(
            min_abs_imbalance=min_abs_imbalance,
            min_volume=min_volume,
            min_open_interest=min_open_interest,
        )
        self.pipeline_gate = OrderFlowPipelineGate()
        self.registry_bridge = OrderFlowRegistryBridge()

    def run(
        self,
        raw_records: Iterable[Mapping[str, Any]],
        observed_at: Optional[str] = None,
    ) -> OrderFlowPipelineBridgeResult:
        discovery = self.discovery_engine.discover_from_raw(
            raw_records=raw_records,
            source_name=self.source_name,
            observed_at=observed_at,
        )
        gate = self.pipeline_gate.validate(discovery)
        registry_entry = self.registry_bridge.bridge(gate)

        accepted = gate.accepted and registry_entry.accepted
        status = "accepted" if accepted else "rejected"

        audit = {
            "read_only": True,
            "deterministic": True,
            "replayable": True,
            "immutable": True,
            "pipeline_steps": [
                "source_adapter",
                "discovery_engine",
                "pipeline_gate",
                "registry_bridge",
            ],
            "discovery_result_hash": discovery.result_hash,
            "gate_hash": gate.gate_hash,
            "registry_hash": registry_entry.registry_hash,
        }

        unsigned = OrderFlowPipelineBridgeResult(
            schema_version=self.schema_version,
            engine_id=self.engine_id,
            status=status,
            accepted=accepted,
            source_name=self.source_name,
            observed_at=discovery.observed_at,
            discovery=discovery,
            gate=gate,
            registry_entry=registry_entry,
            opportunity_count=discovery.opportunity_count,
            read_only=True,
            pipeline_hash="",
            audit=audit,
        )

        return OrderFlowPipelineBridgeResult(
            schema_version=unsigned.schema_version,
            engine_id=unsigned.engine_id,
            status=unsigned.status,
            accepted=unsigned.accepted,
            source_name=unsigned.source_name,
            observed_at=unsigned.observed_at,
            discovery=unsigned.discovery,
            gate=unsigned.gate,
            registry_entry=unsigned.registry_entry,
            opportunity_count=unsigned.opportunity_count,
            read_only=True,
            pipeline_hash=_stable_hash(unsigned.canonical()),
            audit=unsigned.audit,
        )

    def assert_read_only(self) -> bool:
        forbidden = ["buy", "sell", "trade", "execute", "order", "sign", "submit", "broadcast"]
        offenders = sorted(word for word in forbidden if word in set(dir(self)))
        if offenders:
            raise AssertionError(f"mutation-like methods are forbidden: {offenders}")
        self.discovery_engine.assert_read_only()
        self.pipeline_gate.assert_read_only()
        self.registry_bridge.assert_read_only()
        return True


def run_order_flow_pipeline(
    raw_records: Iterable[Mapping[str, Any]],
    source_name: str = "order_flow.generic",
    observed_at: Optional[str] = None,
    min_abs_imbalance: float = 0.25,
    min_volume: float = 0.0,
    min_open_interest: float = 0.0,
) -> OrderFlowPipelineBridgeResult:
    bridge = OrderFlowPipelineBridge(
        source_name=source_name,
        min_abs_imbalance=min_abs_imbalance,
        min_volume=min_volume,
        min_open_interest=min_open_interest,
    )
    return bridge.run(raw_records=raw_records, observed_at=observed_at)


__all__ = [
    "READ_ONLY",
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "OrderFlowPipelineBridge",
    "OrderFlowPipelineBridgeResult",
    "run_order_flow_pipeline",
]
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.order_flow_discovery_model.order_flow_pipeline_bridge import (
    OrderFlowPipelineBridge,
    run_order_flow_pipeline,
)


RAW = [
    {
        "market_id": "KXTEST-YES",
        "venue": "kalshi",
        "instrument": "binary_event",
        "bid_size": 80,
        "ask_size": 20,
        "bid_price": 0.42,
        "ask_price": 0.45,
        "last_price": 0.43,
        "volume": 2000,
        "open_interest": 7000,
        "observed_at": "2026-07-09T00:00:00+00:00",
    },
    {
        "market_id": "KXTEST-NO",
        "venue": "kalshi",
        "instrument": "binary_event",
        "bid_size": 20,
        "ask_size": 80,
        "bid_price": 0.55,
        "ask_price": 0.58,
        "last_price": 0.56,
        "volume": 1900,
        "open_interest": 6500,
        "observed_at": "2026-07-09T00:00:00+00:00",
    },
]


def test_order_flow_pipeline_bridge_runs_full_pipeline():
    bridge = OrderFlowPipelineBridge(source_name="order_flow.test")

    assert bridge.assert_read_only() is True

    result = bridge.run(
        RAW,
        observed_at="2026-07-09T00:00:00+00:00",
    )

    assert result.schema_version == "OFD-006"
    assert result.engine_id == "oracle.discovery.order_flow.pipeline_bridge"
    assert result.status == "accepted"
    assert result.accepted is True
    assert result.read_only is True
    assert result.opportunity_count == 2
    assert result.discovery.schema_version == "OFD-003"
    assert result.gate.schema_version == "OFD-004"
    assert result.registry_entry.schema_version == "OFD-005"
    assert result.gate.accepted is True
    assert result.registry_entry.accepted is True
    assert result.pipeline_hash
    assert result.audit["read_only"] is True
    assert result.audit["deterministic"] is True


def test_order_flow_pipeline_bridge_is_replayable_and_order_independent():
    result1 = run_order_flow_pipeline(
        RAW,
        source_name="order_flow.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )
    result2 = run_order_flow_pipeline(
        list(reversed(RAW)),
        source_name="order_flow.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    assert result1.pipeline_hash == result2.pipeline_hash
    assert result1.discovery.result_hash == result2.discovery.result_hash
    assert result1.gate.gate_hash == result2.gate.gate_hash
    assert result1.registry_entry.registry_hash == result2.registry_entry.registry_hash


def test_order_flow_pipeline_bridge_accepts_empty_valid_pipeline():
    result = run_order_flow_pipeline(
        [],
        source_name="order_flow.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    assert result.status == "accepted"
    assert result.accepted is True
    assert result.opportunity_count == 0
    assert result.discovery.status == "empty"
    assert result.gate.accepted is True
    assert result.registry_entry.accepted is True
    assert result.read_only is True
    assert result.pipeline_hash


if __name__ == "__main__":
    test_order_flow_pipeline_bridge_runs_full_pipeline()
    test_order_flow_pipeline_bridge_is_replayable_and_order_independent()
    test_order_flow_pipeline_bridge_accepts_empty_valid_pipeline()

    result = run_order_flow_pipeline(
        [],
        source_name="order_flow.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    print("[PASS] OFD-006 Order Flow Pipeline Bridge")
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
from .order_flow_pipeline_bridge import (
    OrderFlowPipelineBridge,
    OrderFlowPipelineBridgeResult,
    run_order_flow_pipeline,
)
'''
if "order_flow_pipeline_bridge" not in existing:
    INIT.write_text(existing.rstrip() + "\n" + exports.lstrip(), encoding="utf-8")

print("========================================")
print(" OFD-006 INSTALLER")
print(" Order Flow Pipeline Bridge")
print("========================================")
print(f"[OK] Wrote {MODULE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OFD-006 installed")
print()
print("Run:")
print("py test_ofd_006_order_flow_pipeline_bridge.py")