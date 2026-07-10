from pathlib import Path

ROOT = Path.cwd()
MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence" / "macro_event_discovery_model"
MODULE_DIR.mkdir(parents=True, exist_ok=True)

BRIDGE_FILE = MODULE_DIR / "macro_event_discovery_registry_bridge.py"
TEST_FILE = ROOT / "test_med_005_macro_event_discovery_registry_bridge.py"
INIT_FILE = MODULE_DIR / "__init__.py"

BRIDGE_CODE = r'''
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

from .macro_event_discovery_contract import MacroEventDiscoveryFamily, MacroEventDiscoveryRequest
from .macro_event_discovery_engine import MacroEventDiscoveryEngine

SCHEMA_VERSION = "MED-005"
BRIDGE_ID = "oracle.discovery.bridge.macro_event_registry"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _freeze(v: Any) -> Any:
    if isinstance(v, Mapping):
        return MappingProxyType({str(k): _freeze(x) for k, x in v.items()})
    if isinstance(v, list):
        return tuple(_freeze(x) for x in v)
    if isinstance(v, tuple):
        return tuple(_freeze(x) for x in v)
    return v


@dataclass(frozen=True)
class MacroEventRegistryRecord:
    schema_version: str
    bridge_id: str
    opportunity_id: str
    event_id: str
    title: str
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
            "event_id": self.event_id,
            "title": self.title,
            "opportunity_type": self.opportunity_type,
            "source_engine_id": self.source_engine_id,
            "registry_status": self.registry_status,
            "registry_key": self.registry_key,
            "payload": dict(self.payload),
            "audit": dict(self.audit),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class MacroEventRegistryBridgeReport:
    schema_version: str
    bridge_id: str
    status: str
    records: Tuple[MacroEventRegistryRecord, ...]
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


class MacroEventDiscoveryRegistryBridge:
    schema_version = SCHEMA_VERSION
    bridge_id = BRIDGE_ID
    read_only = True

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "bridge_id": self.bridge_id,
            "read_only": True,
            "accepts": "MED-003 MacroEventDiscoveryResult",
            "emits": "registry-ready immutable macro event records",
            "deterministic": True,
            "telemetry": True,
            "execution": False,
            "order_allowed": False,
            "position_sizing_allowed": False,
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

    def bridge_report(self, discovery_report: Any) -> MacroEventRegistryBridgeReport:
        started_at = _utc_now_iso()
        opportunities = tuple(getattr(discovery_report, "opportunities", ()) or ())
        records = tuple(sorted((self._record_from_opportunity(o) for o in opportunities), key=lambda r: r.registry_key))

        telemetry = MappingProxyType({
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
            "position_sizing_allowed": False,
        })

        return MacroEventRegistryBridgeReport(
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
        source_name: str = "macro_event_registry_bridge_source",
        min_event_score: float = 0.55,
    ) -> MacroEventRegistryBridgeReport:
        request = MacroEventDiscoveryRequest(
            request_id="med005.macro.event.registry.bridge",
            family=MacroEventDiscoveryFamily.ECONOMIC_RELEASE,
            source_name=source_name,
            metadata={"raw_records": tuple(raw_records or ())},
        )
        report = MacroEventDiscoveryEngine(min_event_score=min_event_score).discover(request)
        return self.bridge_report(report)

    def _record_from_opportunity(self, o: Any) -> MacroEventRegistryRecord:
        opportunity_id = str(getattr(o, "opportunity_id"))
        event_id = str(getattr(o, "event_id"))
        title = str(getattr(o, "title"))
        opportunity_type = str(getattr(o, "opportunity_type"))
        source_engine_id = str(getattr(o, "source_engine_id"))
        registry_key = f"{source_engine_id}:{opportunity_type}:{event_id}:{opportunity_id}"

        payload = MappingProxyType({
            "opportunity_id": opportunity_id,
            "event_id": event_id,
            "title": title,
            "family": getattr(o, "family", None),
            "region": getattr(o, "region", None),
            "currency": getattr(o, "currency", None),
            "opportunity_type": opportunity_type,
            "source_engine_id": source_engine_id,
            "event_score": getattr(o, "event_score", None),
            "impact_score": getattr(o, "impact_score", None),
            "market_relevance_score": getattr(o, "market_relevance_score", None),
            "surprise_potential_score": getattr(o, "surprise_potential_score", None),
            "confidence": getattr(o, "confidence", None),
            "status": getattr(o, "status", None),
            "universal_market": _freeze(getattr(o, "universal_market", {})),
            "explanation": _freeze(getattr(o, "explanation", {})),
            "telemetry": _freeze(getattr(o, "telemetry", {})),
            "read_only": True,
            "execution_allowed": False,
            "order_allowed": False,
            "position_sizing_allowed": False,
        })

        audit = MappingProxyType({
            "bridge_schema_version": self.schema_version,
            "bridge_id": self.bridge_id,
            "registered_from": "MED macro event discovery",
            "created_at": _utc_now_iso(),
            "oracle_read_only": True,
            "execution_fields_present": False,
            "execution_allowed": False,
            "order_allowed": False,
            "position_sizing_allowed": False,
        })

        return MacroEventRegistryRecord(
            schema_version=self.schema_version,
            bridge_id=self.bridge_id,
            opportunity_id=opportunity_id,
            event_id=event_id,
            title=title,
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
    "MacroEventRegistryRecord",
    "MacroEventRegistryBridgeReport",
    "MacroEventDiscoveryRegistryBridge",
]
'''

TEST_CODE = r'''
from qseries_v2.oracle_intelligence.macro_event_discovery_model.macro_event_discovery_registry_bridge import (
    MacroEventDiscoveryRegistryBridge,
)


def test_med_005_macro_event_discovery_registry_bridge():
    raw = [
        {"event_id": "fomc_2026_01", "title": "FOMC Rate Decision", "family": "fed_event", "region": "us", "currency": "usd", "impact": "high", "scheduled_at": "2026-01-28T19:00:00Z", "forecast": "4.50%", "previous": "4.50%", "affected_markets": ["RATES", "PREDICTION_MARKETS"]},
        {"id": "cpi_2026_01", "event": "US CPI YoY", "category": "inflation_event", "area": "us", "ccy": "usd", "importance": "high", "time": "2026-01-15T13:30:00Z", "consensus": "2.9%", "previous": "3.0%", "markets": "RATES, EQUITIES, PREDICTION_MARKETS"},
        {"event_id": "minor_2026_01", "title": "Minor Survey", "family": "economic_release", "region": "us", "currency": "usd", "impact": "low", "scheduled_at": "2026-01-12T14:00:00Z", "affected_markets": ["LOCAL"]},
    ]

    bridge = MacroEventDiscoveryRegistryBridge()
    caps = bridge.capabilities()
    health = bridge.health()
    report_a = bridge.discover_and_bridge(raw, source_name="med_005_test_source", min_event_score=0.55)
    report_b = bridge.discover_and_bridge(list(reversed(raw)), source_name="med_005_test_source", min_event_score=0.55)

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["order_allowed"] is False
    assert caps["position_sizing_allowed"] is False
    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert report_a.schema_version == "MED-005"
    assert report_a.bridge_id == "oracle.discovery.bridge.macro_event_registry"
    assert report_a.status == "passed"
    assert report_a.read_only is True
    assert len(report_a.records) == 2

    assert [r.registry_key for r in report_a.records] == [r.registry_key for r in report_b.records]

    first = report_a.records[0]
    assert first.read_only is True
    assert first.registry_status == "registry_ready"
    assert first.payload["read_only"] is True
    assert first.payload["execution_allowed"] is False
    assert first.payload["order_allowed"] is False
    assert first.payload["position_sizing_allowed"] is False
    assert first.audit["oracle_read_only"] is True
    assert first.audit["execution_fields_present"] is False
    assert first.payload["universal_market"]["market_type"] == "macro_event"

    try:
        first.payload["execution_allowed"] = True
        raise AssertionError("registry payload should be immutable")
    except TypeError:
        pass

    d = report_a.to_dict()
    assert d["telemetry"]["opportunities_seen"] == 2
    assert d["telemetry"]["records_emitted"] == 2
    assert d["telemetry"]["read_only"] is True
    assert d["telemetry"]["execution_allowed"] is False

    print("[PASS] MED-005 Macro Event Discovery Registry Bridge")
    print({
        "schema_version": d["schema_version"],
        "bridge_id": d["bridge_id"],
        "status": d["status"],
        "records": len(d["records"]),
        "read_only": d["read_only"],
    })


if __name__ == "__main__":
    test_med_005_macro_event_discovery_registry_bridge()
'''

INIT_EXPORT = '''
try:
    from .macro_event_discovery_registry_bridge import (
        MacroEventDiscoveryRegistryBridge,
        MacroEventRegistryBridgeReport,
        MacroEventRegistryRecord,
    )
except Exception:
    pass
'''

BRIDGE_FILE.write_text(BRIDGE_CODE, encoding="utf-8")
TEST_FILE.write_text(TEST_CODE, encoding="utf-8")

existing = INIT_FILE.read_text(encoding="utf-8") if INIT_FILE.exists() else ""
if "MacroEventDiscoveryRegistryBridge" not in existing:
    INIT_FILE.write_text(existing.rstrip() + "\n" + INIT_EXPORT.lstrip(), encoding="utf-8")

print("========================================")
print(" MED-005 INSTALLER")
print(" Macro Event Discovery Registry Bridge")
print("========================================")
print(f"[OK] Wrote {BRIDGE_FILE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT_FILE}")
print()
print("[DONE] MED-005 installed")
print()
print("Run:")
print("py test_med_005_macro_event_discovery_registry_bridge.py")