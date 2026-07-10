from pathlib import Path

ROOT = Path.cwd()

MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence" / "crypto_discovery_model"
MODULE_DIR.mkdir(parents=True, exist_ok=True)

BRIDGE_FILE = MODULE_DIR / "crypto_spot_discovery_registry_bridge.py"
TEST_FILE = ROOT / "test_cdm_005_crypto_spot_discovery_registry_bridge.py"
INIT_FILE = MODULE_DIR / "__init__.py"

BRIDGE_CODE = r'''"""
CDM-005 Crypto Spot Discovery Registry Bridge

Read-only bridge from CDM-003 crypto spot discovery output to
registry-ready immutable records for the Opportunity Operating System lane.

No trading, swapping, sizing, routing, or execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

from .crypto_discovery_contract import CryptoDiscoveryFamily, CryptoDiscoveryRequest
from .crypto_spot_discovery_engine import CryptoSpotDiscoveryEngine


SCHEMA_VERSION = "CDM-005"
BRIDGE_ID = "oracle.discovery.bridge.crypto_spot_registry"
BRIDGE_NAME = "Crypto Spot Discovery Registry Bridge"


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
class CryptoSpotRegistryRecord:
    schema_version: str
    bridge_id: str
    opportunity_id: str
    symbol: str
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
            "symbol": self.symbol,
            "opportunity_type": self.opportunity_type,
            "source_engine_id": self.source_engine_id,
            "registry_status": self.registry_status,
            "registry_key": self.registry_key,
            "payload": dict(self.payload),
            "audit": dict(self.audit),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class CryptoSpotRegistryBridgeReport:
    schema_version: str
    bridge_id: str
    status: str
    records: Tuple[CryptoSpotRegistryRecord, ...]
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


class CryptoSpotDiscoveryRegistryBridge:
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
            "accepts": "CDM-003 CryptoDiscoveryResult",
            "emits": "registry-ready immutable crypto spot records",
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

    def bridge_report(self, discovery_report: Any) -> CryptoSpotRegistryBridgeReport:
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
                "execution_allowed": False,
            }
        )

        return CryptoSpotRegistryBridgeReport(
            schema_version=self.schema_version,
            bridge_id=self.bridge_id,
            status="passed" if records else "empty",
            records=records,
            telemetry=telemetry,
            read_only=True,
        )

    def discover_and_bridge(
        self,
        raw_records: Sequence[Any],
        source_name: str = "crypto_spot_registry_bridge_source",
        min_edge_percent: float = 0.01,
        min_liquidity: float = 1000.0,
    ) -> CryptoSpotRegistryBridgeReport:
        request = CryptoDiscoveryRequest(
            request_id="cdm005.crypto.spot.registry.bridge",
            family=CryptoDiscoveryFamily.CRYPTO_SPOT,
            source_name=source_name,
            metadata={"raw_records": tuple(raw_records or ())},
        )

        engine = CryptoSpotDiscoveryEngine(
            min_edge_percent=min_edge_percent,
            min_liquidity=min_liquidity,
        )
        discovery_report = engine.discover(request)
        return self.bridge_report(discovery_report)

    def _record_from_opportunity(self, opportunity: Any) -> CryptoSpotRegistryRecord:
        opportunity_id = str(getattr(opportunity, "opportunity_id"))
        symbol = str(getattr(opportunity, "symbol"))
        opportunity_type = str(getattr(opportunity, "opportunity_type"))
        source_engine_id = str(getattr(opportunity, "source_engine_id"))

        registry_key = f"{source_engine_id}:{opportunity_type}:{symbol}:{opportunity_id}"

        payload = MappingProxyType(
            {
                "opportunity_id": opportunity_id,
                "symbol": symbol,
                "opportunity_type": opportunity_type,
                "source_engine_id": source_engine_id,
                "side": getattr(opportunity, "side", None),
                "edge": getattr(opportunity, "edge", None),
                "edge_percent": getattr(opportunity, "edge_percent", None),
                "confidence": getattr(opportunity, "confidence", None),
                "liquidity": getattr(opportunity, "liquidity", None),
                "status": getattr(opportunity, "status", None),
                "universal_market": _freeze(getattr(opportunity, "universal_market", {})),
                "explanation": _freeze(getattr(opportunity, "explanation", {})),
                "telemetry": _freeze(getattr(opportunity, "telemetry", {})),
                "read_only": True,
                "execution_allowed": False,
            }
        )

        audit = MappingProxyType(
            {
                "bridge_schema_version": self.schema_version,
                "bridge_id": self.bridge_id,
                "registered_from": "CDM crypto spot discovery",
                "created_at": _utc_now_iso(),
                "oracle_read_only": True,
                "execution_fields_present": False,
                "execution_allowed": False,
            }
        )

        return CryptoSpotRegistryRecord(
            schema_version=self.schema_version,
            bridge_id=self.bridge_id,
            opportunity_id=opportunity_id,
            symbol=symbol,
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
    "CryptoSpotRegistryRecord",
    "CryptoSpotRegistryBridgeReport",
    "CryptoSpotDiscoveryRegistryBridge",
]
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.crypto_discovery_model.crypto_spot_discovery_registry_bridge import (
    CryptoSpotDiscoveryRegistryBridge,
)


def test_cdm_005_crypto_spot_discovery_registry_bridge():
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

    bridge = CryptoSpotDiscoveryRegistryBridge()
    caps = bridge.capabilities()
    health = bridge.health()

    report_a = bridge.discover_and_bridge(
        raw_records,
        source_name="cdm_005_test_source",
        min_edge_percent=0.01,
        min_liquidity=1000,
    )
    report_b = bridge.discover_and_bridge(
        list(reversed(raw_records)),
        source_name="cdm_005_test_source",
        min_edge_percent=0.01,
        min_liquidity=1000,
    )

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert report_a.schema_version == "CDM-005"
    assert report_a.bridge_id == "oracle.discovery.bridge.crypto_spot_registry"
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
    assert first.payload["execution_allowed"] is False
    assert first.audit["oracle_read_only"] is True
    assert first.audit["execution_fields_present"] is False
    assert first.audit["execution_allowed"] is False
    assert first.payload["universal_market"]["market_type"] == "crypto_spot"

    try:
        first.payload["execution_allowed"] = True
        raise AssertionError("registry payload should be immutable")
    except TypeError:
        pass

    d = report_a.to_dict()
    assert d["schema_version"] == "CDM-005"
    assert d["read_only"] is True
    assert d["telemetry"]["opportunities_seen"] == 2
    assert d["telemetry"]["records_emitted"] == 2
    assert d["telemetry"]["read_only"] is True
    assert d["telemetry"]["execution_allowed"] is False

    print("[PASS] CDM-005 Crypto Spot Discovery Registry Bridge")
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
    test_cdm_005_crypto_spot_discovery_registry_bridge()
'''

INIT_EXPORT = '''
try:
    from .crypto_spot_discovery_registry_bridge import (
        CryptoSpotDiscoveryRegistryBridge,
        CryptoSpotRegistryBridgeReport,
        CryptoSpotRegistryRecord,
    )
except Exception:
    pass
'''

BRIDGE_FILE.write_text(BRIDGE_CODE, encoding="utf-8")
TEST_FILE.write_text(TEST_CODE, encoding="utf-8")

existing_init = INIT_FILE.read_text(encoding="utf-8") if INIT_FILE.exists() else ""
if "CryptoSpotDiscoveryRegistryBridge" not in existing_init:
    INIT_FILE.write_text(existing_init.rstrip() + "\n" + INIT_EXPORT.lstrip(), encoding="utf-8")

print("========================================")
print(" CDM-005 INSTALLER")
print(" Crypto Spot Discovery Registry Bridge")
print("========================================")
print(f"[OK] Wrote {BRIDGE_FILE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT_FILE}")
print()
print("[DONE] CDM-005 installed")
print()
print("Run:")
print("py test_cdm_005_crypto_spot_discovery_registry_bridge.py")