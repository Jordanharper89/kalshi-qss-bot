from pathlib import Path

ROOT = Path.cwd()

MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence" / "oracle_discovery_model"
MODULE_DIR.mkdir(parents=True, exist_ok=True)

BRIDGE_FILE = MODULE_DIR / "prediction_market_discovery_registry_bridge.py"
TEST_FILE = ROOT / "test_odm_005_prediction_market_discovery_registry_bridge.py"
INIT_FILE = MODULE_DIR / "__init__.py"

BRIDGE_CODE = r'''"""
ODM-005 Prediction Market Discovery Registry Bridge

Read-only bridge between ODM prediction-market discovery output and the
Opportunity Operating System registry lane.

This bridge does NOT execute trades. It only prepares immutable registry-ready
records from discovered opportunities.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

from .prediction_market_source_adapter import PredictionMarketSourceAdapter


SCHEMA_VERSION = "ODM-005"
BRIDGE_ID = "oracle.discovery.bridge.prediction_market_registry"
BRIDGE_NAME = "Prediction Market Discovery Registry Bridge"


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
class PredictionMarketRegistryRecord:
    schema_version: str
    bridge_id: str
    opportunity_id: str
    market_id: str
    opportunity_type: str
    source_engine_id: str
    registry_status: str
    registry_key: str
    payload: Mapping[str, Any]
    audit: Mapping[str, Any]
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "bridge_id": self.bridge_id,
            "opportunity_id": self.opportunity_id,
            "market_id": self.market_id,
            "opportunity_type": self.opportunity_type,
            "source_engine_id": self.source_engine_id,
            "registry_status": self.registry_status,
            "registry_key": self.registry_key,
            "payload": dict(self.payload),
            "audit": dict(self.audit),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class PredictionMarketRegistryBridgeReport:
    schema_version: str
    bridge_id: str
    status: str
    records: Tuple[PredictionMarketRegistryRecord, ...]
    telemetry: Mapping[str, Any]
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "bridge_id": self.bridge_id,
            "status": self.status,
            "records": [r.to_dict() for r in self.records],
            "telemetry": dict(self.telemetry),
            "read_only": self.read_only,
        }


class PredictionMarketDiscoveryRegistryBridge:
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
            "accepts": "ODM-002 PredictionMarketDiscoveryReport",
            "emits": "registry-ready immutable records",
            "compatible_with": ["OOS-001 Registry", "OOS-003 Pipeline"],
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

    def bridge_report(self, discovery_report: Any) -> PredictionMarketRegistryBridgeReport:
        started_at = _utc_now_iso()

        opportunities = tuple(getattr(discovery_report, "opportunities", ()) or ())
        records = tuple(
            sorted(
                (self._record_from_opportunity(o) for o in opportunities),
                key=lambda r: (r.registry_key, r.opportunity_id),
            )
        )

        telemetry = MappingProxyType(
            {
                "schema_version": self.schema_version,
                "bridge_id": self.bridge_id,
                "started_at": started_at,
                "completed_at": _utc_now_iso(),
                "opportunities_seen": len(opportunities),
                "records_emitted": len(records),
                "read_only": True,
                "deterministic_sort": True,
            }
        )

        return PredictionMarketRegistryBridgeReport(
            schema_version=self.schema_version,
            bridge_id=self.bridge_id,
            status="passed" if records else "empty",
            records=records,
            telemetry=telemetry,
            read_only=True,
        )

    def discover_and_bridge(
        self,
        raw_markets: Sequence[Any],
        source_name: str = "prediction_market_registry_bridge_source",
        min_edge: float = 0.02,
        min_liquidity: float = 100.0,
    ) -> PredictionMarketRegistryBridgeReport:
        adapter = PredictionMarketSourceAdapter(source_name=source_name)
        discovery_report = adapter.discover(
            raw_markets,
            min_edge=min_edge,
            min_liquidity=min_liquidity,
        )
        return self.bridge_report(discovery_report)

    def _record_from_opportunity(self, opportunity: Any) -> PredictionMarketRegistryRecord:
        opportunity_id = str(getattr(opportunity, "opportunity_id"))
        market_id = str(getattr(opportunity, "market_id"))
        opportunity_type = str(getattr(opportunity, "opportunity_type"))
        source_engine_id = str(getattr(opportunity, "source_engine_id"))

        registry_key = f"{source_engine_id}:{opportunity_type}:{market_id}:{opportunity_id}"

        payload = MappingProxyType(
            {
                "opportunity_id": opportunity_id,
                "market_id": market_id,
                "opportunity_type": opportunity_type,
                "source_engine_id": source_engine_id,
                "side": getattr(opportunity, "side", None),
                "edge": getattr(opportunity, "edge", None),
                "confidence": getattr(opportunity, "confidence", None),
                "liquidity": getattr(opportunity, "liquidity", None),
                "status": getattr(opportunity, "status", None),
                "universal_market": _freeze(getattr(opportunity, "universal_market", {})),
                "explanation": _freeze(getattr(opportunity, "explanation", {})),
                "telemetry": _freeze(getattr(opportunity, "telemetry", {})),
                "read_only": True,
            }
        )

        audit = MappingProxyType(
            {
                "bridge_schema_version": self.schema_version,
                "bridge_id": self.bridge_id,
                "registered_from": "ODM prediction market discovery",
                "created_at": _utc_now_iso(),
                "oracle_read_only": True,
                "execution_fields_present": False,
            }
        )

        return PredictionMarketRegistryRecord(
            schema_version=self.schema_version,
            bridge_id=self.bridge_id,
            opportunity_id=opportunity_id,
            market_id=market_id,
            opportunity_type=opportunity_type,
            source_engine_id=source_engine_id,
            registry_status="registry_ready",
            registry_key=registry_key,
            payload=payload,
            audit=audit,
            read_only=True,
        )


__all__ = [
    "SCHEMA_VERSION",
    "BRIDGE_ID",
    "BRIDGE_NAME",
    "PredictionMarketRegistryRecord",
    "PredictionMarketRegistryBridgeReport",
    "PredictionMarketDiscoveryRegistryBridge",
]
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.oracle_discovery_model.prediction_market_discovery_registry_bridge import (
    PredictionMarketDiscoveryRegistryBridge,
)


def test_odm_005_prediction_market_discovery_registry_bridge():
    raw_markets = [
        {
            "ticker": "KX.ODM005.YES",
            "question": "Will ODM-005 fixture one resolve yes?",
            "platform": "kalshi",
            "category": "oracle_test",
            "price": 40,
            "model_probability": 54,
            "liquidity": 2500,
            "volume": 10000,
            "status": "open",
        },
        {
            "ticker": "KX.ODM005.NO",
            "question": "Will ODM-005 fixture two resolve yes?",
            "platform": "kalshi",
            "category": "oracle_test",
            "price": 76,
            "model_probability": 64,
            "liquidity": 3000,
            "volume": 15000,
            "status": "open",
        },
        {
            "ticker": "KX.ODM005.REJECT",
            "question": "Will ODM-005 low-edge fixture resolve yes?",
            "platform": "kalshi",
            "category": "oracle_test",
            "price": 50,
            "model_probability": 50.5,
            "liquidity": 3000,
            "status": "open",
        },
    ]

    bridge = PredictionMarketDiscoveryRegistryBridge()
    caps = bridge.capabilities()
    health = bridge.health()

    report_a = bridge.discover_and_bridge(
        raw_markets,
        source_name="odm_005_test_source",
        min_edge=0.02,
        min_liquidity=100,
    )
    report_b = bridge.discover_and_bridge(
        list(reversed(raw_markets)),
        source_name="odm_005_test_source",
        min_edge=0.02,
        min_liquidity=100,
    )

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert report_a.schema_version == "ODM-005"
    assert report_a.bridge_id == "oracle.discovery.bridge.prediction_market_registry"
    assert report_a.status == "passed"
    assert report_a.read_only is True
    assert len(report_a.records) == 2

    keys_a = [r.registry_key for r in report_a.records]
    keys_b = [r.registry_key for r in report_b.records]
    assert keys_a == keys_b

    first = report_a.records[0]
    assert first.read_only is True
    assert first.registry_status == "registry_ready"
    assert first.payload["read_only"] is True
    assert first.audit["oracle_read_only"] is True
    assert first.audit["execution_fields_present"] is False
    assert first.payload["universal_market"]["market_type"] == "prediction_market"

    try:
        first.payload["read_only"] = False
        raise AssertionError("registry payload should be immutable")
    except TypeError:
        pass

    d = report_a.to_dict()
    assert d["schema_version"] == "ODM-005"
    assert d["read_only"] is True
    assert d["telemetry"]["opportunities_seen"] == 2
    assert d["telemetry"]["records_emitted"] == 2
    assert d["telemetry"]["read_only"] is True

    print("[PASS] ODM-005 Prediction Market Discovery Registry Bridge")
    print(
        {
            "schema_version": d["schema_version"],
            "bridge_id": d["bridge_id"],
            "status": d["status"],
            "records": len(d["records"]),
            "read_only": d["read_only"],
        }
    )


if __name__ == "__main__":
    test_odm_005_prediction_market_discovery_registry_bridge()
'''

INIT_EXPORT = '''
try:
    from .prediction_market_discovery_registry_bridge import (
        PredictionMarketDiscoveryRegistryBridge,
        PredictionMarketRegistryBridgeReport,
        PredictionMarketRegistryRecord,
    )
except Exception:
    pass
'''

BRIDGE_FILE.write_text(BRIDGE_CODE, encoding="utf-8")
TEST_FILE.write_text(TEST_CODE, encoding="utf-8")

existing_init = INIT_FILE.read_text(encoding="utf-8") if INIT_FILE.exists() else ""
if "PredictionMarketDiscoveryRegistryBridge" not in existing_init:
    INIT_FILE.write_text(existing_init.rstrip() + "\n" + INIT_EXPORT.lstrip(), encoding="utf-8")

print("========================================")
print(" ODM-005 INSTALLER")
print(" Prediction Market Discovery Registry Bridge")
print("========================================")
print(f"[OK] Wrote {BRIDGE_FILE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT_FILE}")
print()
print("[DONE] ODM-005 installed")
print()
print("Run:")
print("py test_odm_005_prediction_market_discovery_registry_bridge.py")