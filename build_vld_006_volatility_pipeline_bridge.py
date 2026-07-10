from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence" / "volatility_discovery_model"
PKG.mkdir(parents=True, exist_ok=True)

MODULE = PKG / "volatility_pipeline_bridge.py"
TEST = ROOT / "test_vld_006_volatility_pipeline_bridge.py"
INIT = PKG / "__init__.py"

MODULE.write_text(r'''
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Dict, Iterable, Mapping, Optional

from .volatility_discovery_engine import VolatilityDiscoveryEngine, VolatilityDiscoveryResult
from .volatility_pipeline_gate import VolatilityPipelineGate, VolatilityPipelineGateResult
from .volatility_registry_bridge import VolatilityRegistryBridge, VolatilityRegistryEntry


READ_ONLY = True
SCHEMA_VERSION = "VLD-006"
ENGINE_ID = "oracle.discovery.volatility.pipeline_bridge"


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
class VolatilityPipelineBridgeResult:
    schema_version: str
    engine_id: str
    status: str
    accepted: bool
    source_name: str
    observed_at: str
    discovery: VolatilityDiscoveryResult
    gate: VolatilityPipelineGateResult
    registry_entry: VolatilityRegistryEntry
    opportunity_count: int
    read_only: bool = True
    pipeline_hash: str = ""
    audit: Dict[str, Any] = field(default_factory=dict)

    def canonical(self) -> Dict[str, Any]:
        return _deep_sort(asdict(self))


class VolatilityPipelineBridge:
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    read_only = READ_ONLY

    def __init__(
        self,
        source_name: str = "volatility.generic",
        expansion_ratio_threshold: float = 1.50,
        contraction_ratio_threshold: float = 0.70,
        iv_rv_gap_threshold: float = 0.10,
        shock_return_threshold: float = 0.05,
        min_volume: float = 0.0,
    ) -> None:
        self.source_name = str(source_name or "volatility.generic")
        self.discovery_engine = VolatilityDiscoveryEngine(
            expansion_ratio_threshold=expansion_ratio_threshold,
            contraction_ratio_threshold=contraction_ratio_threshold,
            iv_rv_gap_threshold=iv_rv_gap_threshold,
            shock_return_threshold=shock_return_threshold,
            min_volume=min_volume,
        )
        self.pipeline_gate = VolatilityPipelineGate()
        self.registry_bridge = VolatilityRegistryBridge()

    def run(
        self,
        raw_records: Iterable[Mapping[str, Any]],
        observed_at: Optional[str] = None,
    ) -> VolatilityPipelineBridgeResult:
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

        unsigned = VolatilityPipelineBridgeResult(
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

        return VolatilityPipelineBridgeResult(
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


def run_volatility_pipeline(
    raw_records: Iterable[Mapping[str, Any]],
    source_name: str = "volatility.generic",
    observed_at: Optional[str] = None,
    expansion_ratio_threshold: float = 1.50,
    contraction_ratio_threshold: float = 0.70,
    iv_rv_gap_threshold: float = 0.10,
    shock_return_threshold: float = 0.05,
    min_volume: float = 0.0,
) -> VolatilityPipelineBridgeResult:
    bridge = VolatilityPipelineBridge(
        source_name=source_name,
        expansion_ratio_threshold=expansion_ratio_threshold,
        contraction_ratio_threshold=contraction_ratio_threshold,
        iv_rv_gap_threshold=iv_rv_gap_threshold,
        shock_return_threshold=shock_return_threshold,
        min_volume=min_volume,
    )
    return bridge.run(raw_records=raw_records, observed_at=observed_at)


__all__ = [
    "READ_ONLY",
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "VolatilityPipelineBridge",
    "VolatilityPipelineBridgeResult",
    "run_volatility_pipeline",
]
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.volatility_discovery_model.volatility_pipeline_bridge import (
    VolatilityPipelineBridge,
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
    },
    {
        "market_id": "KXVOL-CONTRACT",
        "venue": "kalshi",
        "asset": "binary_event",
        "realized_volatility": 0.10,
        "implied_volatility": 0.24,
        "baseline_volatility": 0.20,
        "price_change": 0.01,
        "volume": 9000,
        "window": "1d",
        "observed_at": "2026-07-09T00:00:00+00:00",
    },
]


def test_volatility_pipeline_bridge_runs_full_pipeline():
    bridge = VolatilityPipelineBridge(source_name="volatility.test")

    assert bridge.assert_read_only() is True

    result = bridge.run(
        RAW,
        observed_at="2026-07-09T00:00:00+00:00",
    )

    assert result.schema_version == "VLD-006"
    assert result.engine_id == "oracle.discovery.volatility.pipeline_bridge"
    assert result.status == "accepted"
    assert result.accepted is True
    assert result.read_only is True
    assert result.opportunity_count >= 4
    assert result.discovery.schema_version == "VLD-003"
    assert result.gate.schema_version == "VLD-004"
    assert result.registry_entry.schema_version == "VLD-005"
    assert result.gate.accepted is True
    assert result.registry_entry.accepted is True
    assert result.pipeline_hash
    assert result.audit["read_only"] is True
    assert result.audit["deterministic"] is True


def test_volatility_pipeline_bridge_is_replayable_and_order_independent():
    result1 = run_volatility_pipeline(
        RAW,
        source_name="volatility.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )
    result2 = run_volatility_pipeline(
        list(reversed(RAW)),
        source_name="volatility.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    assert result1.pipeline_hash == result2.pipeline_hash
    assert result1.discovery.result_hash == result2.discovery.result_hash
    assert result1.gate.gate_hash == result2.gate.gate_hash
    assert result1.registry_entry.registry_hash == result2.registry_entry.registry_hash


def test_volatility_pipeline_bridge_accepts_empty_valid_pipeline():
    result = run_volatility_pipeline(
        [],
        source_name="volatility.empty",
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
    test_volatility_pipeline_bridge_runs_full_pipeline()
    test_volatility_pipeline_bridge_is_replayable_and_order_independent()
    test_volatility_pipeline_bridge_accepts_empty_valid_pipeline()

    result = run_volatility_pipeline(
        [],
        source_name="volatility.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    print("[PASS] VLD-006 Volatility Pipeline Bridge")
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
from .volatility_pipeline_bridge import (
    VolatilityPipelineBridge,
    VolatilityPipelineBridgeResult,
    run_volatility_pipeline,
)
'''
if "volatility_pipeline_bridge" not in existing:
    INIT.write_text(existing.rstrip() + "\n" + exports.lstrip(), encoding="utf-8")

print("========================================")
print(" VLD-006 INSTALLER")
print(" Volatility Pipeline Bridge")
print("========================================")
print(f"[OK] Wrote {MODULE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] VLD-006 installed")
print()
print("Run:")
print("py test_vld_006_volatility_pipeline_bridge.py")