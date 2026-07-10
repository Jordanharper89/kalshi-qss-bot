from pathlib import Path

ROOT = Path.cwd()

MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence" / "arbitrage_discovery_model"
MODULE_DIR.mkdir(parents=True, exist_ok=True)

BRIDGE_FILE = MODULE_DIR / "cross_venue_arbitrage_discovery_registry_bridge.py"
TEST_FILE = ROOT / "test_adm_005_cross_venue_arbitrage_discovery_registry_bridge.py"
INIT_FILE = MODULE_DIR / "__init__.py"

BRIDGE_CODE = r'''"""
ADM-005 Cross-Venue Arbitrage Discovery Registry Bridge

Read-only bridge from ADM-003 cross-venue arbitrage discovery output to
registry-ready immutable records for the Opportunity Operating System lane.

No trading, routing, order placement, sizing, leg execution, or exits.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

from .arbitrage_discovery_contract import ArbitrageDiscoveryFamily, ArbitrageDiscoveryRequest
from .cross_venue_arbitrage_discovery_engine import CrossVenueArbitrageDiscoveryEngine


SCHEMA_VERSION = "ADM-005"
BRIDGE_ID = "oracle.discovery.bridge.cross_venue_arbitrage_registry"
BRIDGE_NAME = "Cross-Venue Arbitrage Discovery Registry Bridge"


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
class CrossVenueArbitrageRegistryRecord:
    schema_version: str
    bridge_id: str
    opportunity_id: str
    symbol: str
    opportunity_type: str
    source_engine_id: str
    buy_venue: str
    sell_venue: str
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
            "buy_venue": self.buy_venue,
            "sell_venue": self.sell_venue,
            "registry_status": self.registry_status,
            "registry_key": self.registry_key,
            "payload": dict(self.payload),
            "audit": dict(self.audit),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class CrossVenueArbitrageRegistryBridgeReport:
    schema_version: str
    bridge_id: str
    status: str
    records: Tuple[CrossVenueArbitrageRegistryRecord, ...]
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


class CrossVenueArbitrageDiscoveryRegistryBridge:
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
            "accepts": "ADM-003 ArbitrageDiscoveryResult",
            "emits": "registry-ready immutable cross-venue arbitrage records",
            "compatible_with": ["OOS-001 Registry", "OOS-003 Pipeline"],
            "deterministic": True,
            "telemetry": True,
            "execution": False,
            "order_allowed": False,
            "route_allowed": False,
            "leg_execution_allowed": False,
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

    def bridge_report(self, discovery_report: Any) -> CrossVenueArbitrageRegistryBridgeReport:
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
                "order_allowed": False,
                "route_allowed": False,
                "leg_execution_allowed": False,
            }
        )

        return CrossVenueArbitrageRegistryBridgeReport(
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
        source_name: str = "cross_venue_arbitrage_registry_bridge_source",
        min_net_edge_percent: float = 0.001,
        min_liquidity: float = 1000.0,
    ) -> CrossVenueArbitrageRegistryBridgeReport:
        request = ArbitrageDiscoveryRequest(
            request_id="adm005.cross.venue.arbitrage.registry.bridge",
            family=ArbitrageDiscoveryFamily.CROSS_EXCHANGE,
            source_name=source_name,
            metadata={"raw_records": tuple(raw_records or ())},
        )

        engine = CrossVenueArbitrageDiscoveryEngine(
            min_net_edge_percent=min_net_edge_percent,
            min_liquidity=min_liquidity,
        )
        discovery_report = engine.discover(request)
        return self.bridge_report(discovery_report)

    def _record_from_opportunity(self, opportunity: Any) -> CrossVenueArbitrageRegistryRecord:
        opportunity_id = str(getattr(opportunity, "opportunity_id"))
        symbol = str(getattr(opportunity, "symbol"))
        opportunity_type = str(getattr(opportunity, "opportunity_type"))
        source_engine_id = str(getattr(opportunity, "source_engine_id"))
        buy_venue = str(getattr(opportunity, "buy_venue"))
        sell_venue = str(getattr(opportunity, "sell_venue"))

        registry_key = (
            f"{source_engine_id}:{opportunity_type}:{symbol}:"
            f"{buy_venue}->{sell_venue}:{opportunity_id}"
        )

        payload = MappingProxyType(
            {
                "opportunity_id": opportunity_id,
                "symbol": symbol,
                "opportunity_type": opportunity_type,
                "source_engine_id": source_engine_id,
                "buy_venue": buy_venue,
                "sell_venue": sell_venue,
                "buy_price": getattr(opportunity, "buy_price", None),
                "sell_price": getattr(opportunity, "sell_price", None),
                "gross_edge": getattr(opportunity, "gross_edge", None),
                "gross_edge_percent": getattr(opportunity, "gross_edge_percent", None),
                "estimated_fee_percent": getattr(opportunity, "estimated_fee_percent", None),
                "net_edge": getattr(opportunity, "net_edge", None),
                "net_edge_percent": getattr(opportunity, "net_edge_percent", None),
                "confidence": getattr(opportunity, "confidence", None),
                "liquidity": getattr(opportunity, "liquidity", None),
                "status": getattr(opportunity, "status", None),
                "universal_market": _freeze(getattr(opportunity, "universal_market", {})),
                "explanation": _freeze(getattr(opportunity, "explanation", {})),
                "telemetry": _freeze(getattr(opportunity, "telemetry", {})),
                "read_only": True,
                "execution_allowed": False,
                "order_allowed": False,
                "route_allowed": False,
                "leg_execution_allowed": False,
            }
        )

        audit = MappingProxyType(
            {
                "bridge_schema_version": self.schema_version,
                "bridge_id": self.bridge_id,
                "registered_from": "ADM cross-venue arbitrage discovery",
                "created_at": _utc_now_iso(),
                "oracle_read_only": True,
                "execution_fields_present": False,
                "execution_allowed": False,
                "order_allowed": False,
                "route_allowed": False,
                "leg_execution_allowed": False,
            }
        )

        return CrossVenueArbitrageRegistryRecord(
            schema_version=self.schema_version,
            bridge_id=self.bridge_id,
            opportunity_id=opportunity_id,
            symbol=symbol,
            opportunity_type=opportunity_type,
            source_engine_id=source_engine_id,
            buy_venue=buy_venue,
            sell_venue=sell_venue,
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
    "CrossVenueArbitrageRegistryRecord",
    "CrossVenueArbitrageRegistryBridgeReport",
    "CrossVenueArbitrageDiscoveryRegistryBridge",
]
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.arbitrage_discovery_model.cross_venue_arbitrage_discovery_registry_bridge import (
    CrossVenueArbitrageDiscoveryRegistryBridge,
)


def test_adm_005_cross_venue_arbitrage_discovery_registry_bridge():
    raw_records = [
        {
            "symbol": "BTC-USD",
            "venue": "coinbase",
            "bid": 65000,
            "ask": 65020,
            "last_price": 65010,
            "fee_bps": 8,
            "liquidity": 2500000,
            "volume_24h": 5000000,
            "latency_ms": 40,
            "status": "active",
        },
        {
            "symbol": "BTC/USD",
            "exchange": "kraken",
            "bid": 65300,
            "ask": 65320,
            "last": 65310,
            "taker_fee_bps": 10,
            "depth": 1500000,
            "volume": 4000000,
            "latency_ms": 80,
            "status": "active",
        },
        {
            "pair": "ETH/USD",
            "venue": "coinbase",
            "best_bid": 3500,
            "best_ask": 3502,
            "price": 3501,
            "fee_bps": 8,
            "liquidity": 800000,
            "volume_24h": 2000000,
            "status": "active",
        },
    ]

    bridge = CrossVenueArbitrageDiscoveryRegistryBridge()
    caps = bridge.capabilities()
    health = bridge.health()

    report_a = bridge.discover_and_bridge(
        raw_records,
        source_name="adm_005_test_source",
        min_net_edge_percent=0.001,
        min_liquidity=1000,
    )
    report_b = bridge.discover_and_bridge(
        list(reversed(raw_records)),
        source_name="adm_005_test_source",
        min_net_edge_percent=0.001,
        min_liquidity=1000,
    )

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["order_allowed"] is False
    assert caps["route_allowed"] is False
    assert caps["leg_execution_allowed"] is False
    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert report_a.schema_version == "ADM-005"
    assert report_a.bridge_id == "oracle.discovery.bridge.cross_venue_arbitrage_registry"
    assert report_a.status == "passed"
    assert report_a.read_only is True
    assert len(report_a.records) == 1

    keys_a = [r.registry_key for r in report_a.records]
    keys_b = [r.registry_key for r in report_b.records]
    assert keys_a == keys_b

    first = report_a.records[0]
    assert first.read_only is True
    assert first.registry_status == "registry_ready"
    assert first.symbol == "BTC-USD"
    assert first.buy_venue == "coinbase"
    assert first.sell_venue == "kraken"
    assert first.payload["read_only"] is True
    assert first.payload["execution_allowed"] is False
    assert first.payload["order_allowed"] is False
    assert first.payload["route_allowed"] is False
    assert first.payload["leg_execution_allowed"] is False
    assert first.audit["oracle_read_only"] is True
    assert first.audit["execution_fields_present"] is False
    assert first.audit["execution_allowed"] is False
    assert first.payload["universal_market"]["market_type"] == "cross_venue_arbitrage"

    try:
        first.payload["execution_allowed"] = True
        raise AssertionError("registry payload should be immutable")
    except TypeError:
        pass

    d = report_a.to_dict()
    assert d["schema_version"] == "ADM-005"
    assert d["read_only"] is True
    assert d["telemetry"]["opportunities_seen"] == 1
    assert d["telemetry"]["records_emitted"] == 1
    assert d["telemetry"]["read_only"] is True
    assert d["telemetry"]["execution_allowed"] is False
    assert d["telemetry"]["route_allowed"] is False

    print("[PASS] ADM-005 Cross-Venue Arbitrage Discovery Registry Bridge")
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
    test_adm_005_cross_venue_arbitrage_discovery_registry_bridge()
'''

INIT_EXPORT = '''
try:
    from .cross_venue_arbitrage_discovery_registry_bridge import (
        CrossVenueArbitrageDiscoveryRegistryBridge,
        CrossVenueArbitrageRegistryBridgeReport,
        CrossVenueArbitrageRegistryRecord,
    )
except Exception:
    pass
'''

BRIDGE_FILE.write_text(BRIDGE_CODE, encoding="utf-8")
TEST_FILE.write_text(TEST_CODE, encoding="utf-8")

existing_init = INIT_FILE.read_text(encoding="utf-8") if INIT_FILE.exists() else ""
if "CrossVenueArbitrageDiscoveryRegistryBridge" not in existing_init:
    INIT_FILE.write_text(existing_init.rstrip() + "\n" + INIT_EXPORT.lstrip(), encoding="utf-8")

print("========================================")
print(" ADM-005 INSTALLER")
print(" Cross-Venue Arbitrage Discovery Registry Bridge")
print("========================================")
print(f"[OK] Wrote {BRIDGE_FILE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT_FILE}")
print()
print("[DONE] ADM-005 installed")
print()
print("Run:")
print("py test_adm_005_cross_venue_arbitrage_discovery_registry_bridge.py")