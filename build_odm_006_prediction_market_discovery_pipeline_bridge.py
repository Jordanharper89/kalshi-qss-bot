from pathlib import Path

ROOT = Path.cwd()

MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence" / "oracle_discovery_model"
MODULE_DIR.mkdir(parents=True, exist_ok=True)

BRIDGE_FILE = MODULE_DIR / "prediction_market_discovery_pipeline_bridge.py"
TEST_FILE = ROOT / "test_odm_006_prediction_market_discovery_pipeline_bridge.py"
INIT_FILE = MODULE_DIR / "__init__.py"

BRIDGE_CODE = r'''"""
ODM-006 Prediction Market Discovery Pipeline Bridge

Read-only bridge from ODM-005 registry-ready discovery records into
pipeline-ready packets for the Opportunity Operating System lane.

This module does not execute, size, enter, exit, or manage trades.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

from .prediction_market_discovery_registry_bridge import (
    PredictionMarketDiscoveryRegistryBridge,
    PredictionMarketRegistryRecord,
)


SCHEMA_VERSION = "ODM-006"
BRIDGE_ID = "oracle.discovery.bridge.prediction_market_pipeline"
BRIDGE_NAME = "Prediction Market Discovery Pipeline Bridge"


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
class PredictionMarketPipelinePacket:
    schema_version: str
    bridge_id: str
    packet_id: str
    registry_key: str
    opportunity_id: str
    market_id: str
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
            "market_id": self.market_id,
            "pipeline_status": self.pipeline_status,
            "payload": dict(self.payload),
            "audit": dict(self.audit),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class PredictionMarketPipelineBridgeReport:
    schema_version: str
    bridge_id: str
    status: str
    packets: Tuple[PredictionMarketPipelinePacket, ...]
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


class PredictionMarketDiscoveryPipelineBridge:
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
            "accepts": "ODM-005 registry-ready records",
            "emits": "pipeline-ready immutable packets",
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
        registry_records: Sequence[PredictionMarketRegistryRecord],
    ) -> PredictionMarketPipelineBridgeReport:
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
            }
        )

        return PredictionMarketPipelineBridgeReport(
            schema_version=self.schema_version,
            bridge_id=self.bridge_id,
            status="passed" if packets else "empty",
            packets=packets,
            telemetry=telemetry,
            read_only=True,
        )

    def discover_registry_and_bridge(
        self,
        raw_markets: Sequence[Any],
        source_name: str = "prediction_market_pipeline_bridge_source",
        min_edge: float = 0.02,
        min_liquidity: float = 100.0,
    ) -> PredictionMarketPipelineBridgeReport:
        registry_bridge = PredictionMarketDiscoveryRegistryBridge()
        registry_report = registry_bridge.discover_and_bridge(
            raw_markets,
            source_name=source_name,
            min_edge=min_edge,
            min_liquidity=min_liquidity,
        )
        return self.bridge_records(registry_report.records)

    def _packet_from_record(
        self,
        record: PredictionMarketRegistryRecord,
    ) -> PredictionMarketPipelinePacket:
        packet_id = f"pipeline.packet:{record.registry_key}"

        payload = MappingProxyType(
            {
                "opportunity_id": record.opportunity_id,
                "market_id": record.market_id,
                "opportunity_type": record.opportunity_type,
                "source_engine_id": record.source_engine_id,
                "registry_key": record.registry_key,
                "registry_payload": _freeze(record.payload),
                "validation_required": True,
                "ranking_required": True,
                "registry_required": True,
                "execution_allowed": False,
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
                "handoff_target": "OOS Opportunity Pipeline",
            }
        )

        return PredictionMarketPipelinePacket(
            schema_version=self.schema_version,
            bridge_id=self.bridge_id,
            packet_id=packet_id,
            registry_key=record.registry_key,
            opportunity_id=record.opportunity_id,
            market_id=record.market_id,
            pipeline_status="pipeline_ready",
            payload=payload,
            audit=audit,
            read_only=True,
        )


__all__ = [
    "SCHEMA_VERSION",
    "BRIDGE_ID",
    "BRIDGE_NAME",
    "PredictionMarketPipelinePacket",
    "PredictionMarketPipelineBridgeReport",
    "PredictionMarketDiscoveryPipelineBridge",
]
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.oracle_discovery_model.prediction_market_discovery_pipeline_bridge import (
    PredictionMarketDiscoveryPipelineBridge,
)


def test_odm_006_prediction_market_discovery_pipeline_bridge():
    raw_markets = [
        {
            "ticker": "KX.ODM006.YES",
            "question": "Will ODM-006 fixture one resolve yes?",
            "platform": "kalshi",
            "category": "oracle_test",
            "price": 40,
            "model_probability": 54,
            "liquidity": 2500,
            "volume": 10000,
            "status": "open",
        },
        {
            "ticker": "KX.ODM006.NO",
            "question": "Will ODM-006 fixture two resolve yes?",
            "platform": "kalshi",
            "category": "oracle_test",
            "price": 76,
            "model_probability": 64,
            "liquidity": 3000,
            "volume": 15000,
            "status": "open",
        },
        {
            "ticker": "KX.ODM006.REJECT",
            "question": "Will ODM-006 low-edge fixture resolve yes?",
            "platform": "kalshi",
            "category": "oracle_test",
            "price": 50,
            "model_probability": 50.5,
            "liquidity": 3000,
            "status": "open",
        },
    ]

    bridge = PredictionMarketDiscoveryPipelineBridge()
    caps = bridge.capabilities()
    health = bridge.health()

    report_a = bridge.discover_registry_and_bridge(
        raw_markets,
        source_name="odm_006_test_source",
        min_edge=0.02,
        min_liquidity=100,
    )
    report_b = bridge.discover_registry_and_bridge(
        list(reversed(raw_markets)),
        source_name="odm_006_test_source",
        min_edge=0.02,
        min_liquidity=100,
    )

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert report_a.schema_version == "ODM-006"
    assert report_a.bridge_id == "oracle.discovery.bridge.prediction_market_pipeline"
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
    assert first.audit["oracle_read_only"] is True
    assert first.audit["execution_fields_present"] is False
    assert first.audit["handoff_target"] == "OOS Opportunity Pipeline"

    try:
        first.payload["execution_allowed"] = True
        raise AssertionError("pipeline payload should be immutable")
    except TypeError:
        pass

    d = report_a.to_dict()
    assert d["schema_version"] == "ODM-006"
    assert d["read_only"] is True
    assert d["telemetry"]["records_seen"] == 2
    assert d["telemetry"]["packets_emitted"] == 2
    assert d["telemetry"]["read_only"] is True

    print("[PASS] ODM-006 Prediction Market Discovery Pipeline Bridge")
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
    test_odm_006_prediction_market_discovery_pipeline_bridge()
'''

INIT_EXPORT = '''
try:
    from .prediction_market_discovery_pipeline_bridge import (
        PredictionMarketDiscoveryPipelineBridge,
        PredictionMarketPipelineBridgeReport,
        PredictionMarketPipelinePacket,
    )
except Exception:
    pass
'''

BRIDGE_FILE.write_text(BRIDGE_CODE, encoding="utf-8")
TEST_FILE.write_text(TEST_CODE, encoding="utf-8")

existing_init = INIT_FILE.read_text(encoding="utf-8") if INIT_FILE.exists() else ""
if "PredictionMarketDiscoveryPipelineBridge" not in existing_init:
    INIT_FILE.write_text(existing_init.rstrip() + "\n" + INIT_EXPORT.lstrip(), encoding="utf-8")

print("========================================")
print(" ODM-006 INSTALLER")
print(" Prediction Market Discovery Pipeline Bridge")
print("========================================")
print(f"[OK] Wrote {BRIDGE_FILE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT_FILE}")
print()
print("[DONE] ODM-006 installed")
print()
print("Run:")
print("py test_odm_006_prediction_market_discovery_pipeline_bridge.py")