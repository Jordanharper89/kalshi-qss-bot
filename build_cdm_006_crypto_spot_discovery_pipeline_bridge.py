from pathlib import Path

ROOT = Path.cwd()

MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence" / "crypto_discovery_model"
MODULE_DIR.mkdir(parents=True, exist_ok=True)

BRIDGE_FILE = MODULE_DIR / "crypto_spot_discovery_pipeline_bridge.py"
TEST_FILE = ROOT / "test_cdm_006_crypto_spot_discovery_pipeline_bridge.py"
INIT_FILE = MODULE_DIR / "__init__.py"

BRIDGE_CODE = r'''"""
CDM-006 Crypto Spot Discovery Pipeline Bridge

Read-only bridge from CDM-005 registry-ready crypto spot records into
pipeline-ready packets for the Opportunity Operating System lane.

No trading, swapping, sizing, routing, or execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

from .crypto_spot_discovery_registry_bridge import (
    CryptoSpotDiscoveryRegistryBridge,
    CryptoSpotRegistryRecord,
)


SCHEMA_VERSION = "CDM-006"
BRIDGE_ID = "oracle.discovery.bridge.crypto_spot_pipeline"
BRIDGE_NAME = "Crypto Spot Discovery Pipeline Bridge"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    if isinstance(value, tuple):
        return tuple(_freeze(v) for v in value)
    return value


@dataclass(frozen=True)
class CryptoSpotPipelinePacket:
    schema_version: str
    bridge_id: str
    packet_id: str
    registry_key: str
    opportunity_id: str
    symbol: str
    pipeline_status: str
    payload: Mapping[str, Any]
    audit: Mapping[str, Any]
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "bridge_id": self.bridge_id,
            "packet_id": self.packet_id,
            "registry_key": self.registry_key,
            "opportunity_id": self.opportunity_id,
            "symbol": self.symbol,
            "pipeline_status": self.pipeline_status,
            "payload": dict(self.payload),
            "audit": dict(self.audit),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class CryptoSpotPipelineBridgeReport:
    schema_version: str
    bridge_id: str
    status: str
    packets: Tuple[CryptoSpotPipelinePacket, ...]
    telemetry: Mapping[str, Any]
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "bridge_id": self.bridge_id,
            "status": self.status,
            "packets": [p.to_dict() for p in self.packets],
            "telemetry": dict(self.telemetry),
            "read_only": self.read_only,
        }


class CryptoSpotDiscoveryPipelineBridge:
    schema_version = SCHEMA_VERSION
    bridge_id = BRIDGE_ID
    bridge_name = BRIDGE_NAME
    read_only = True

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "bridge_id": self.bridge_id,
            "bridge_name": self.bridge_name,
            "read_only": True,
            "accepts": "CDM-005 registry-ready crypto spot records",
            "emits": "pipeline-ready immutable crypto spot packets",
            "compatible_with": ["OOS-003 Opportunity Pipeline", "OOS-004 Validation"],
            "deterministic": True,
            "telemetry": True,
            "execution": False,
        }

    def health(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "bridge_id": self.bridge_id,
            "status": "ok",
            "ready": True,
            "read_only": True,
            "checked_at": _utc_now_iso(),
        }

    def bridge_records(
        self,
        registry_records: Sequence[CryptoSpotRegistryRecord],
    ) -> CryptoSpotPipelineBridgeReport:
        started_at = _utc_now_iso()
        records = tuple(registry_records or ())

        packets = tuple(
            sorted(
                (self._packet_from_record(record) for record in records),
                key=lambda p: (p.registry_key, p.packet_id),
            )
        )

        telemetry = MappingProxyType(
            {
                "schema_version": self.schema_version,
                "bridge_id": self.bridge_id,
                "started_at": started_at,
                "completed_at": _utc_now_iso(),
                "records_seen": len(records),
                "packets_emitted": len(packets),
                "read_only": True,
                "deterministic_sort": True,
                "execution_allowed": False,
            }
        )

        return CryptoSpotPipelineBridgeReport(
            schema_version=self.schema_version,
            bridge_id=self.bridge_id,
            status="passed" if packets else "empty",
            packets=packets,
            telemetry=telemetry,
            read_only=True,
        )

    def discover_registry_and_bridge(
        self,
        raw_records: Sequence[Any],
        source_name: str = "crypto_spot_pipeline_bridge_source",
        min_edge_percent: float = 0.01,
        min_liquidity: float = 1000.0,
    ) -> CryptoSpotPipelineBridgeReport:
        registry_bridge = CryptoSpotDiscoveryRegistryBridge()
        registry_report = registry_bridge.discover_and_bridge(
            raw_records,
            source_name=source_name,
            min_edge_percent=min_edge_percent,
            min_liquidity=min_liquidity,
        )
        return self.bridge_records(registry_report.records)

    def _packet_from_record(self, record: CryptoSpotRegistryRecord) -> CryptoSpotPipelinePacket:
        packet_id = f"pipeline.packet:{record.registry_key}"

        payload = MappingProxyType(
            {
                "opportunity_id": record.opportunity_id,
                "symbol": record.symbol,
                "opportunity_type": record.opportunity_type,
                "source_engine_id": record.source_engine_id,
                "registry_key": record.registry_key,
                "registry_payload": _freeze(record.payload),
                "validation_required": True,
                "ranking_required": True,
                "registry_required": True,
                "execution_allowed": False,
                "swap_allowed": False,
                "order_allowed": False,
                "read_only": True,
            }
        )

        audit = MappingProxyType(
            {
                "bridge_schema_version": self.schema_version,
                "bridge_id": self.bridge_id,
                "source_registry_schema_version": record.schema_version,
                "source_registry_bridge_id": record.bridge_id,
                "created_at": _utc_now_iso(),
                "oracle_read_only": True,
                "execution_fields_present": False,
                "execution_allowed": False,
                "handoff_target": "OOS Opportunity Pipeline",
            }
        )

        return CryptoSpotPipelinePacket(
            schema_version=self.schema_version,
            bridge_id=self.bridge_id,
            packet_id=packet_id,
            registry_key=record.registry_key,
            opportunity_id=record.opportunity_id,
            symbol=record.symbol,
            pipeline_status="pipeline_ready",
            payload=payload,
            audit=audit,
            read_only=True,
        )


__all__ = [
    "SCHEMA_VERSION",
    "BRIDGE_ID",
    "BRIDGE_NAME",
    "CryptoSpotPipelinePacket",
    "CryptoSpotPipelineBridgeReport",
    "CryptoSpotDiscoveryPipelineBridge",
]
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.crypto_discovery_model.crypto_spot_discovery_pipeline_bridge import (
    CryptoSpotDiscoveryPipelineBridge,
)


def test_cdm_006_crypto_spot_discovery_pipeline_bridge():
    raw_records = [
        {
            "symbol": "BTC-USD",
            "exchange": "coinbase",
            "price": 65000,
            "fair_value": 67000,
            "bid": 64990,
            "ask": 65010,
            "volume": 5000000,
            "depth": 2500000,
            "volatility_24h": 0.03,
            "status": "active",
        },
        {
            "symbol": "ETH/USD",
            "exchange": "coinbase",
            "price": 3500,
            "model_price": 3400,
            "bid": 3499,
            "ask": 3501,
            "volume_24h": 1000000,
            "liquidity": 500000,
            "volatility": 0.04,
            "status": "active",
        },
        {
            "symbol": "SOL-USD",
            "exchange": "coinbase",
            "price": 150,
            "fair_value": 151,
            "volume": 1000000,
            "depth": 500000,
            "status": "active",
        },
    ]

    bridge = CryptoSpotDiscoveryPipelineBridge()
    caps = bridge.capabilities()
    health = bridge.health()

    report_a = bridge.discover_registry_and_bridge(
        raw_records,
        source_name="cdm_006_test_source",
        min_edge_percent=0.01,
        min_liquidity=1000,
    )
    report_b = bridge.discover_registry_and_bridge(
        list(reversed(raw_records)),
        source_name="cdm_006_test_source",
        min_edge_percent=0.01,
        min_liquidity=1000,
    )

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["deterministic"] is True
    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert report_a.schema_version == "CDM-006"
    assert report_a.bridge_id == "oracle.discovery.bridge.crypto_spot_pipeline"
    assert report_a.status == "passed"
    assert report_a.read_only is True
    assert len(report_a.packets) == 2

    packet_ids_a = [p.packet_id for p in report_a.packets]
    packet_ids_b = [p.packet_id for p in report_b.packets]
    assert packet_ids_a == packet_ids_b

    first = report_a.packets[0]
    assert first.read_only is True
    assert first.pipeline_status == "pipeline_ready"
    assert first.payload["read_only"] is True
    assert first.payload["validation_required"] is True
    assert first.payload["ranking_required"] is True
    assert first.payload["registry_required"] is True
    assert first.payload["execution_allowed"] is False
    assert first.payload["swap_allowed"] is False
    assert first.payload["order_allowed"] is False
    assert first.audit["oracle_read_only"] is True
    assert first.audit["execution_fields_present"] is False
    assert first.audit["execution_allowed"] is False
    assert first.audit["handoff_target"] == "OOS Opportunity Pipeline"

    assert first.payload["registry_payload"]["universal_market"]["market_type"] == "crypto_spot"
    assert first.payload["registry_payload"]["read_only"] is True
    assert first.payload["registry_payload"]["execution_allowed"] is False

    try:
        first.payload["execution_allowed"] = True
        raise AssertionError("pipeline payload should be immutable")
    except TypeError:
        pass

    d = report_a.to_dict()
    assert d["schema_version"] == "CDM-006"
    assert d["read_only"] is True
    assert d["telemetry"]["records_seen"] == 2
    assert d["telemetry"]["packets_emitted"] == 2
    assert d["telemetry"]["read_only"] is True
    assert d["telemetry"]["execution_allowed"] is False

    print("[PASS] CDM-006 Crypto Spot Discovery Pipeline Bridge")
    print(
        {
            "schema_version": d["schema_version"],
            "bridge_id": d["bridge_id"],
            "status": d["status"],
            "packets": len(d["packets"]),
            "read_only": d["read_only"],
        }
    )


if __name__ == "__main__":
    test_cdm_006_crypto_spot_discovery_pipeline_bridge()
'''

INIT_EXPORT = '''
try:
    from .crypto_spot_discovery_pipeline_bridge import (
        CryptoSpotDiscoveryPipelineBridge,
        CryptoSpotPipelineBridgeReport,
        CryptoSpotPipelinePacket,
    )
except Exception:
    pass
'''

BRIDGE_FILE.write_text(BRIDGE_CODE, encoding="utf-8")
TEST_FILE.write_text(TEST_CODE, encoding="utf-8")

existing_init = INIT_FILE.read_text(encoding="utf-8") if INIT_FILE.exists() else ""
if "CryptoSpotDiscoveryPipelineBridge" not in existing_init:
    INIT_FILE.write_text(existing_init.rstrip() + "\n" + INIT_EXPORT.lstrip(), encoding="utf-8")

print("========================================")
print(" CDM-006 INSTALLER")
print(" Crypto Spot Discovery Pipeline Bridge")
print("========================================")
print(f"[OK] Wrote {BRIDGE_FILE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT_FILE}")
print()
print("[DONE] CDM-006 installed")
print()
print("Run:")
print("py test_cdm_006_crypto_spot_discovery_pipeline_bridge.py")