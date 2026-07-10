from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence" / "liquidity_discovery_model"
PKG.mkdir(parents=True, exist_ok=True)

MODULE = PKG / "liquidity_registry_bridge.py"
TEST = ROOT / "test_lqd_005_liquidity_registry_bridge.py"
INIT = PKG / "__init__.py"

MODULE.write_text(r'''
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Dict, Mapping

from .liquidity_pipeline_gate import LiquidityPipelineGateResult


READ_ONLY = True
SCHEMA_VERSION = "LQD-005"
ENGINE_ID = "oracle.discovery.liquidity.registry_bridge"


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
class LiquidityRegistryEntry:
    schema_version: str
    engine_id: str
    family: str
    bridge_status: str
    accepted: bool
    registry_key: str
    source_gate_hash: str
    source_result_hash: str
    opportunity_count: int
    capabilities: Dict[str, Any] = field(default_factory=dict)
    read_only: bool = True
    registry_hash: str = ""

    def canonical(self) -> Dict[str, Any]:
        return _deep_sort(asdict(self))


class LiquidityRegistryBridge:
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    read_only = READ_ONLY

    def __init__(self, family: str = "liquidity_discovery") -> None:
        self.family = str(family or "liquidity_discovery")

    def bridge(self, gate_result: LiquidityPipelineGateResult) -> LiquidityRegistryEntry:
        if not isinstance(gate_result, LiquidityPipelineGateResult):
            raise TypeError("gate_result must be a LiquidityPipelineGateResult")

        registry_key = _stable_hash(
            {
                "family": self.family,
                "source_gate_hash": gate_result.gate_hash,
                "source_result_hash": gate_result.discovery_result_hash,
                "source_schema_version": gate_result.schema_version,
            }
        )

        capabilities = {
            "family": self.family,
            "read_only": True,
            "deterministic": True,
            "replayable": True,
            "immutable": True,
            "auditable": True,
            "source_schema_version": gate_result.schema_version,
            "source_engine_id": gate_result.engine_id,
            "source_status": gate_result.status,
            "checks": dict(gate_result.checks),
        }

        unsigned = LiquidityRegistryEntry(
            schema_version=self.schema_version,
            engine_id=self.engine_id,
            family=self.family,
            bridge_status="registered" if gate_result.accepted else "rejected",
            accepted=gate_result.accepted,
            registry_key=registry_key,
            source_gate_hash=gate_result.gate_hash,
            source_result_hash=gate_result.discovery_result_hash,
            opportunity_count=gate_result.opportunity_count,
            capabilities=capabilities,
            read_only=True,
            registry_hash="",
        )

        return LiquidityRegistryEntry(
            schema_version=unsigned.schema_version,
            engine_id=unsigned.engine_id,
            family=unsigned.family,
            bridge_status=unsigned.bridge_status,
            accepted=unsigned.accepted,
            registry_key=unsigned.registry_key,
            source_gate_hash=unsigned.source_gate_hash,
            source_result_hash=unsigned.source_result_hash,
            opportunity_count=unsigned.opportunity_count,
            capabilities=unsigned.capabilities,
            read_only=True,
            registry_hash=_stable_hash(unsigned.canonical()),
        )

    def assert_read_only(self) -> bool:
        forbidden = ["buy", "sell", "trade", "execute", "order", "sign", "submit", "broadcast"]
        offenders = sorted(word for word in forbidden if word in set(dir(self)))
        if offenders:
            raise AssertionError(f"mutation-like methods are forbidden: {offenders}")
        return True


def bridge_liquidity_registry(gate_result: LiquidityPipelineGateResult) -> LiquidityRegistryEntry:
    return LiquidityRegistryBridge().bridge(gate_result)


__all__ = [
    "READ_ONLY",
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "LiquidityRegistryBridge",
    "LiquidityRegistryEntry",
    "bridge_liquidity_registry",
]
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.liquidity_discovery_model.liquidity_discovery_engine import (
    discover_liquidity_opportunities,
)
from qseries_v2.oracle_intelligence.liquidity_discovery_model.liquidity_pipeline_gate import (
    validate_liquidity_discovery_result,
)
from qseries_v2.oracle_intelligence.liquidity_discovery_model.liquidity_registry_bridge import (
    LiquidityRegistryBridge,
    bridge_liquidity_registry,
)


def _build_gate():
    raw = [
        {
            "market_id": "KXTHIN",
            "venue": "kalshi",
            "asset": "binary_event",
            "bid_price": 0.40,
            "ask_price": 0.48,
            "bid_depth": 100,
            "ask_depth": 50,
            "volume_24h": 12000,
            "open_interest": 50000,
            "observed_at": "2026-07-09T00:00:00+00:00",
        }
    ]
    result = discover_liquidity_opportunities(
        raw,
        source_name="liquidity.test",
        observed_at="2026-07-09T00:00:00+00:00",
        min_spread_bps=250,
        max_total_depth=1000,
        min_depth_imbalance=0.30,
    )
    return validate_liquidity_discovery_result(result)


def test_liquidity_registry_bridge_registers_valid_gate():
    gate = _build_gate()
    bridge = LiquidityRegistryBridge()

    assert bridge.assert_read_only() is True

    entry = bridge.bridge(gate)

    assert entry.schema_version == "LQD-005"
    assert entry.engine_id == "oracle.discovery.liquidity.registry_bridge"
    assert entry.family == "liquidity_discovery"
    assert entry.bridge_status == "registered"
    assert entry.accepted is True
    assert entry.read_only is True
    assert entry.source_gate_hash == gate.gate_hash
    assert entry.source_result_hash == gate.discovery_result_hash
    assert entry.opportunity_count == gate.opportunity_count
    assert entry.registry_key
    assert entry.registry_hash
    assert entry.capabilities["deterministic"] is True
    assert entry.capabilities["replayable"] is True
    assert entry.capabilities["read_only"] is True


def test_liquidity_registry_bridge_is_replayable():
    gate = _build_gate()

    entry1 = bridge_liquidity_registry(gate)
    entry2 = bridge_liquidity_registry(gate)

    assert entry1.registry_key == entry2.registry_key
    assert entry1.registry_hash == entry2.registry_hash


def test_liquidity_registry_bridge_accepts_empty_valid_gate():
    result = discover_liquidity_opportunities(
        [],
        source_name="liquidity.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )
    gate = validate_liquidity_discovery_result(result)
    entry = bridge_liquidity_registry(gate)

    assert entry.bridge_status == "registered"
    assert entry.accepted is True
    assert entry.opportunity_count == 0
    assert entry.read_only is True


if __name__ == "__main__":
    test_liquidity_registry_bridge_registers_valid_gate()
    test_liquidity_registry_bridge_is_replayable()
    test_liquidity_registry_bridge_accepts_empty_valid_gate()

    gate = _build_gate()
    entry = bridge_liquidity_registry(gate)

    print("[PASS] LQD-005 Liquidity Registry Bridge")
    print(
        {
            "schema_version": entry.schema_version,
            "engine_id": entry.engine_id,
            "bridge_status": entry.bridge_status,
            "accepted": entry.accepted,
            "opportunities": entry.opportunity_count,
            "read_only": entry.read_only,
        }
    )
''', encoding="utf-8")

existing = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
exports = '''
from .liquidity_registry_bridge import (
    LiquidityRegistryBridge,
    LiquidityRegistryEntry,
    bridge_liquidity_registry,
)
'''
if "liquidity_registry_bridge" not in existing:
    INIT.write_text(existing.rstrip() + "\n" + exports.lstrip(), encoding="utf-8")

print("========================================")
print(" LQD-005 INSTALLER")
print(" Liquidity Registry Bridge")
print("========================================")
print(f"[OK] Wrote {MODULE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] LQD-005 installed")
print()
print("Run:")
print("py test_lqd_005_liquidity_registry_bridge.py")