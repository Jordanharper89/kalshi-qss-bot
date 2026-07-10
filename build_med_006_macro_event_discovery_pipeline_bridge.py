from pathlib import Path

ROOT = Path.cwd()
MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence" / "macro_event_discovery_model"
MODULE_DIR.mkdir(parents=True, exist_ok=True)

BRIDGE_FILE = MODULE_DIR / "macro_event_discovery_pipeline_bridge.py"
TEST_FILE = ROOT / "test_med_006_macro_event_discovery_pipeline_bridge.py"
INIT_FILE = MODULE_DIR / "__init__.py"

BRIDGE_CODE = r'''
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

from .macro_event_discovery_registry_bridge import (
    MacroEventDiscoveryRegistryBridge,
    MacroEventRegistryRecord,
)

SCHEMA_VERSION = "MED-006"
BRIDGE_ID = "oracle.discovery.bridge.macro_event_pipeline"


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
class MacroEventPipelinePacket:
    schema_version: str
    bridge_id: str
    packet_id: str
    registry_key: str
    opportunity_id: str
    event_id: str
    title: str
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
            "event_id": self.event_id,
            "title": self.title,
            "pipeline_status": self.pipeline_status,
            "payload": dict(self.payload),
            "audit": dict(self.audit),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class MacroEventPipelineBridgeReport:
    schema_version: str
    bridge_id: str
    status: str
    packets: Tuple[MacroEventPipelinePacket, ...]
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


class MacroEventDiscoveryPipelineBridge:
    schema_version = SCHEMA_VERSION
    bridge_id = BRIDGE_ID
    read_only = True

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "bridge_id": self.bridge_id,
            "read_only": True,
            "accepts": "MED-005 registry-ready macro event records",
            "emits": "pipeline-ready immutable macro event packets",
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

    def bridge_records(self, registry_records: Sequence[MacroEventRegistryRecord]) -> MacroEventPipelineBridgeReport:
        started_at = _utc_now_iso()
        records = tuple(registry_records or ())
        packets = tuple(sorted((self._packet_from_record(r) for r in records), key=lambda p: p.packet_id))

        telemetry = MappingProxyType({
            "schema_version": self.schema_version,
            "bridge_id": self.bridge_id,
            "started_at": started_at,
            "completed_at": _utc_now_iso(),
            "records_seen": len(records),
            "packets_emitted": len(packets),
            "read_only": True,
            "deterministic_sort": True,
            "execution_allowed": False,
            "order_allowed": False,
            "position_sizing_allowed": False,
        })

        return MacroEventPipelineBridgeReport(
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
        source_name: str = "macro_event_pipeline_bridge_source",
        min_event_score: float = 0.55,
    ) -> MacroEventPipelineBridgeReport:
        registry_bridge = MacroEventDiscoveryRegistryBridge()
        registry_report = registry_bridge.discover_and_bridge(
            raw_records,
            source_name=source_name,
            min_event_score=min_event_score,
        )
        return self.bridge_records(registry_report.records)

    def _packet_from_record(self, record: MacroEventRegistryRecord) -> MacroEventPipelinePacket:
        packet_id = f"pipeline.packet:{record.registry_key}"

        payload = MappingProxyType({
            "opportunity_id": record.opportunity_id,
            "event_id": record.event_id,
            "title": record.title,
            "opportunity_type": record.opportunity_type,
            "source_engine_id": record.source_engine_id,
            "registry_key": record.registry_key,
            "registry_payload": _freeze(record.payload),
            "validation_required": True,
            "ranking_required": True,
            "registry_required": True,
            "execution_allowed": False,
            "order_allowed": False,
            "position_sizing_allowed": False,
            "read_only": True,
        })

        audit = MappingProxyType({
            "bridge_schema_version": self.schema_version,
            "bridge_id": self.bridge_id,
            "source_registry_schema_version": record.schema_version,
            "source_registry_bridge_id": record.bridge_id,
            "created_at": _utc_now_iso(),
            "oracle_read_only": True,
            "execution_fields_present": False,
            "execution_allowed": False,
            "order_allowed": False,
            "position_sizing_allowed": False,
            "handoff_target": "OOS Opportunity Pipeline",
        })

        return MacroEventPipelinePacket(
            schema_version=self.schema_version,
            bridge_id=self.bridge_id,
            packet_id=packet_id,
            registry_key=record.registry_key,
            opportunity_id=record.opportunity_id,
            event_id=record.event_id,
            title=record.title,
            pipeline_status="pipeline_ready",
            payload=payload,
            audit=audit,
            read_only=True,
        )


__all__ = [
    "SCHEMA_VERSION",
    "BRIDGE_ID",
    "MacroEventPipelinePacket",
    "MacroEventPipelineBridgeReport",
    "MacroEventDiscoveryPipelineBridge",
]
'''

TEST_CODE = r'''
from qseries_v2.oracle_intelligence.macro_event_discovery_model.macro_event_discovery_pipeline_bridge import (
    MacroEventDiscoveryPipelineBridge,
)


def test_med_006_macro_event_discovery_pipeline_bridge():
    raw = [
        {"event_id": "fomc_2026_01", "title": "FOMC Rate Decision", "family": "fed_event", "region": "us", "currency": "usd", "impact": "high", "scheduled_at": "2026-01-28T19:00:00Z", "forecast": "4.50%", "previous": "4.50%", "affected_markets": ["RATES", "PREDICTION_MARKETS"]},
        {"id": "cpi_2026_01", "event": "US CPI YoY", "category": "inflation_event", "area": "us", "ccy": "usd", "importance": "high", "time": "2026-01-15T13:30:00Z", "consensus": "2.9%", "previous": "3.0%", "markets": "RATES, EQUITIES, PREDICTION_MARKETS"},
        {"event_id": "minor_2026_01", "title": "Minor Survey", "family": "economic_release", "region": "us", "currency": "usd", "impact": "low", "scheduled_at": "2026-01-12T14:00:00Z", "affected_markets": ["LOCAL"]},
    ]

    bridge = MacroEventDiscoveryPipelineBridge()
    caps = bridge.capabilities()
    health = bridge.health()

    report_a = bridge.discover_registry_and_bridge(raw, source_name="med_006_test_source", min_event_score=0.55)
    report_b = bridge.discover_registry_and_bridge(list(reversed(raw)), source_name="med_006_test_source", min_event_score=0.55)

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["order_allowed"] is False
    assert caps["position_sizing_allowed"] is False
    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert report_a.schema_version == "MED-006"
    assert report_a.bridge_id == "oracle.discovery.bridge.macro_event_pipeline"
    assert report_a.status == "passed"
    assert report_a.read_only is True
    assert len(report_a.packets) == 2

    assert [p.packet_id for p in report_a.packets] == [p.packet_id for p in report_b.packets]

    first = report_a.packets[0]
    assert first.read_only is True
    assert first.pipeline_status == "pipeline_ready"
    assert first.payload["read_only"] is True
    assert first.payload["validation_required"] is True
    assert first.payload["ranking_required"] is True
    assert first.payload["registry_required"] is True
    assert first.payload["execution_allowed"] is False
    assert first.payload["order_allowed"] is False
    assert first.payload["position_sizing_allowed"] is False
    assert first.audit["oracle_read_only"] is True
    assert first.audit["execution_fields_present"] is False
    assert first.audit["handoff_target"] == "OOS Opportunity Pipeline"
    assert first.payload["registry_payload"]["universal_market"]["market_type"] == "macro_event"

    try:
        first.payload["execution_allowed"] = True
        raise AssertionError("pipeline payload should be immutable")
    except TypeError:
        pass

    d = report_a.to_dict()
    assert d["schema_version"] == "MED-006"
    assert d["telemetry"]["records_seen"] == 2
    assert d["telemetry"]["packets_emitted"] == 2
    assert d["telemetry"]["read_only"] is True
    assert d["telemetry"]["execution_allowed"] is False

    print("[PASS] MED-006 Macro Event Discovery Pipeline Bridge")
    print({
        "schema_version": d["schema_version"],
        "bridge_id": d["bridge_id"],
        "status": d["status"],
        "packets": len(d["packets"]),
        "read_only": d["read_only"],
    })


if __name__ == "__main__":
    test_med_006_macro_event_discovery_pipeline_bridge()
'''

INIT_EXPORT = '''
try:
    from .macro_event_discovery_pipeline_bridge import (
        MacroEventDiscoveryPipelineBridge,
        MacroEventPipelineBridgeReport,
        MacroEventPipelinePacket,
    )
except Exception:
    pass
'''

BRIDGE_FILE.write_text(BRIDGE_CODE, encoding="utf-8")
TEST_FILE.write_text(TEST_CODE, encoding="utf-8")

existing = INIT_FILE.read_text(encoding="utf-8") if INIT_FILE.exists() else ""
if "MacroEventDiscoveryPipelineBridge" not in existing:
    INIT_FILE.write_text(existing.rstrip() + "\n" + INIT_EXPORT.lstrip(), encoding="utf-8")

print("========================================")
print(" MED-006 INSTALLER")
print(" Macro Event Discovery Pipeline Bridge")
print("========================================")
print(f"[OK] Wrote {BRIDGE_FILE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT_FILE}")
print()
print("[DONE] MED-006 installed")
print()
print("Run:")
print("py test_med_006_macro_event_discovery_pipeline_bridge.py")