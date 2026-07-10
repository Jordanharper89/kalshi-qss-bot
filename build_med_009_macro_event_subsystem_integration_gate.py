from pathlib import Path

ROOT = Path.cwd()
MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence" / "macro_event_discovery_model"
MODULE_DIR.mkdir(parents=True, exist_ok=True)

GATE_FILE = MODULE_DIR / "macro_event_subsystem_integration_gate.py"
TEST_FILE = ROOT / "test_med_009_macro_event_subsystem_integration_gate.py"
INIT_FILE = MODULE_DIR / "__init__.py"

GATE_CODE = r'''
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

from .macro_event_discovery_contract import (
    SCHEMA_VERSION as CONTRACT_SCHEMA_VERSION,
    MacroEventDiscoveryFamily,
    MacroEventDiscoveryRequest,
)
from .macro_event_source_adapter import MacroEventSourceAdapter
from .macro_event_discovery_engine import MacroEventDiscoveryEngine
from .macro_event_discovery_pipeline_gate import MacroEventDiscoveryPipelineGate
from .macro_event_discovery_registry_bridge import MacroEventDiscoveryRegistryBridge
from .macro_event_discovery_pipeline_bridge import MacroEventDiscoveryPipelineBridge
from .macro_event_discovery_oos_runtime_gate import MacroEventDiscoveryOOSRuntimeGate
from .macro_event_discovery_replay_ledger import MacroEventDiscoveryReplayLedger

SCHEMA_VERSION = "MED-009"
GATE_ID = "oracle.discovery.gate.macro_event_subsystem_integration"


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
class MacroEventSubsystemIntegrationReport:
    schema_version: str
    gate_id: str
    status: str
    passed_checks: int
    failed_checks: int
    warning_count: int
    checks: Mapping[str, bool]
    telemetry: Mapping[str, Any]
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "gate_id": self.gate_id,
            "status": self.status,
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks,
            "warning_count": self.warning_count,
            "checks": dict(self.checks),
            "telemetry": dict(self.telemetry),
            "read_only": self.read_only,
        }


class MacroEventSubsystemIntegrationGate:
    schema_version = SCHEMA_VERSION
    gate_id = GATE_ID
    read_only = True

    def __init__(self, source_name: str = "macro_event_subsystem_gate_source", min_event_score: float = 0.55) -> None:
        self.source_name = str(source_name)
        self.min_event_score = float(min_event_score)

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "gate_id": self.gate_id,
            "read_only": True,
            "validates": [
                "MED-001 contract",
                "MED-002 source adapter",
                "MED-003 discovery engine",
                "MED-004 pipeline gate",
                "MED-005 registry bridge",
                "MED-006 pipeline bridge",
                "MED-007 OOS runtime gate",
                "MED-008 replay ledger",
                "deterministic replay",
                "immutable payloads",
                "no execution authority",
            ],
            "execution": False,
            "order_allowed": False,
            "position_sizing_allowed": False,
            "broker_connectivity_allowed": False,
            "deterministic": True,
            "telemetry": True,
        }

    def health(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "gate_id": self.gate_id,
            "status": "ok",
            "ready": True,
            "read_only": True,
            "checked_at": _utc_now_iso(),
        }

    def run(self, raw_records: Sequence[Any] | None = None) -> MacroEventSubsystemIntegrationReport:
        started_at = _utc_now_iso()
        raw = tuple(raw_records or self._fixture_records())

        adapter = MacroEventSourceAdapter(source_name=self.source_name)
        batch = adapter.normalize_batch(raw)

        request = MacroEventDiscoveryRequest(
            request_id="med009.macro.event.subsystem.integration",
            family=MacroEventDiscoveryFamily.ECONOMIC_RELEASE,
            source_name=self.source_name,
            event_ids=tuple(sorted({s.event_id for s in batch.snapshots})),
            regions=tuple(sorted({s.region for s in batch.snapshots})),
            markets=tuple(sorted({m for s in batch.snapshots for m in s.affected_markets})),
            metadata={"snapshots": batch.snapshots},
        )

        engine = MacroEventDiscoveryEngine(min_event_score=self.min_event_score)
        discovery_report = engine.discover(request)

        pipeline_gate = MacroEventDiscoveryPipelineGate(
            source_name=self.source_name,
            min_event_score=self.min_event_score,
        )
        pipeline_gate_report = pipeline_gate.run(raw)

        registry_bridge = MacroEventDiscoveryRegistryBridge()
        registry_report = registry_bridge.bridge_report(discovery_report)

        pipeline_bridge = MacroEventDiscoveryPipelineBridge()
        pipeline_report = pipeline_bridge.bridge_records(registry_report.records)

        oos_gate = MacroEventDiscoveryOOSRuntimeGate(
            source_name=self.source_name,
            min_event_score=self.min_event_score,
        )
        oos_report = oos_gate.run(raw)

        replay_ledger = MacroEventDiscoveryReplayLedger()
        replay_a = replay_ledger.record_packets(oos_report.packets)
        replay_b = replay_ledger.record_packets(oos_gate.run(tuple(reversed(raw))).packets)
        replay_compare = replay_ledger.compare(replay_a, replay_b)

        checks = {
            "gate_is_read_only": self.read_only is True,
            "contract_schema_ok": CONTRACT_SCHEMA_VERSION == "MED-001",
            "request_is_read_only": request.read_only is True,
            "adapter_is_read_only": adapter.read_only is True,
            "engine_is_read_only": engine.read_only is True,
            "pipeline_gate_is_read_only": pipeline_gate.read_only is True,
            "registry_bridge_is_read_only": registry_bridge.read_only is True,
            "pipeline_bridge_is_read_only": pipeline_bridge.read_only is True,
            "oos_gate_is_read_only": oos_gate.read_only is True,
            "replay_ledger_is_read_only": replay_ledger.read_only is True,

            "adapter_schema_ok": batch.schema_version == "MED-002",
            "engine_contract_schema_ok": discovery_report.schema_version == "MED-001",
            "pipeline_gate_schema_ok": pipeline_gate_report.schema_version == "MED-004",
            "registry_bridge_schema_ok": registry_report.schema_version == "MED-005",
            "pipeline_bridge_schema_ok": pipeline_report.schema_version == "MED-006",
            "oos_gate_schema_ok": oos_report.schema_version == "MED-007",
            "replay_ledger_schema_ok": replay_a.schema_version == "MED-008",

            "snapshots_emitted": len(batch.snapshots) == len(raw),
            "events_seen": discovery_report.telemetry.events_seen == 3,
            "opportunities_emitted": len(discovery_report.opportunities) == 2,
            "registry_records_emitted": len(registry_report.records) == 2,
            "pipeline_packets_emitted": len(pipeline_report.packets) == 2,
            "oos_packets_emitted": len(oos_report.packets) == 2,
            "replay_entries_emitted": len(replay_a.entries) == 2,

            "pipeline_gate_passed": pipeline_gate_report.status == "passed",
            "registry_bridge_passed": registry_report.status == "passed",
            "pipeline_bridge_passed": pipeline_report.status == "passed",
            "oos_gate_passed": oos_report.status == "passed",
            "replay_ledger_passed": replay_a.status == "passed",
            "replay_comparison_matched": replay_compare.matching is True,

            "all_opportunities_read_only": all(o.read_only is True for o in discovery_report.opportunities),
            "all_registry_records_read_only": all(r.read_only is True for r in registry_report.records),
            "all_pipeline_packets_read_only": all(p.read_only is True for p in pipeline_report.packets),
            "all_oos_packets_read_only": all(p.read_only is True for p in oos_report.packets),
            "all_replay_entries_read_only": all(e.read_only is True for e in replay_a.entries),

            "all_macro_markets_shape": all(
                o.universal_market.get("market_type") == "macro_event"
                and o.universal_market.get("execution_allowed") is False
                and o.universal_market.get("order_allowed") is False
                and o.universal_market.get("position_sizing_allowed") is False
                for o in discovery_report.opportunities
            ),
            "all_pipeline_packets_validation_ready": all(p.payload.get("validation_required") is True for p in pipeline_report.packets),
            "all_pipeline_packets_registry_ready": all(p.payload.get("registry_required") is True for p in pipeline_report.packets),
            "all_pipeline_packets_ranking_ready": all(p.payload.get("ranking_required") is True for p in pipeline_report.packets),
            "execution_not_allowed": all(p.payload.get("execution_allowed") is False for p in pipeline_report.packets),
            "order_not_allowed": all(p.payload.get("order_allowed") is False for p in pipeline_report.packets),
            "position_sizing_not_allowed": all(p.payload.get("position_sizing_allowed") is False for p in pipeline_report.packets),
            "no_execution_fields_in_registry": all(r.audit.get("execution_fields_present") is False for r in registry_report.records),
            "no_execution_fields_in_pipeline": all(p.audit.get("execution_fields_present") is False for p in pipeline_report.packets),

            "immutable_registry_payload": self._immutable_mapping_check(registry_report.records[0].payload if registry_report.records else {}),
            "immutable_pipeline_payload": self._immutable_mapping_check(pipeline_report.packets[0].payload if pipeline_report.packets else {}),
            "immutable_replay_summary": self._immutable_mapping_check(replay_a.entries[0].payload_summary if replay_a.entries else {}),

            "telemetry_present_adapter": bool(batch.telemetry),
            "telemetry_present_engine": bool(discovery_report.telemetry),
            "telemetry_present_pipeline_gate": bool(pipeline_gate_report.telemetry),
            "telemetry_present_registry": bool(registry_report.telemetry),
            "telemetry_present_pipeline": bool(pipeline_report.telemetry),
            "telemetry_present_oos_gate": bool(oos_report.telemetry),
            "telemetry_present_replay": bool(replay_a.telemetry),

            "deterministic_replay_fingerprint": replay_a.run_fingerprint == replay_b.run_fingerprint,
            "read_only_telemetry_all": all(
                item.get("read_only") is True
                for item in (
                    batch.telemetry,
                    discovery_report.telemetry.to_dict(),
                    pipeline_gate_report.telemetry,
                    registry_report.telemetry,
                    pipeline_report.telemetry,
                    oos_report.telemetry,
                    replay_a.telemetry,
                )
            ),
        }

        passed = sum(1 for ok in checks.values() if ok)
        failed = sum(1 for ok in checks.values() if not ok)

        telemetry = MappingProxyType({
            "schema_version": self.schema_version,
            "gate_id": self.gate_id,
            "started_at": started_at,
            "completed_at": _utc_now_iso(),
            "raw_records_seen": len(raw),
            "snapshots_emitted": len(batch.snapshots),
            "events_seen": discovery_report.telemetry.events_seen,
            "opportunities_emitted": len(discovery_report.opportunities),
            "registry_records_emitted": len(registry_report.records),
            "pipeline_packets_emitted": len(pipeline_report.packets),
            "oos_packets_emitted": len(oos_report.packets),
            "replay_entries_emitted": len(replay_a.entries),
            "passed_checks": passed,
            "failed_checks": failed,
            "warning_count": 0,
            "read_only": True,
            "execution_allowed": False,
            "order_allowed": False,
            "position_sizing_allowed": False,
            "broker_connectivity_allowed": False,
            "replay_match": replay_compare.matching,
            "run_fingerprint": replay_a.run_fingerprint,
        })

        return MacroEventSubsystemIntegrationReport(
            schema_version=self.schema_version,
            gate_id=self.gate_id,
            status="passed" if failed == 0 else "failed",
            passed_checks=passed,
            failed_checks=failed,
            warning_count=0,
            checks=_freeze(checks),
            telemetry=telemetry,
            read_only=True,
        )

    def _immutable_mapping_check(self, mapping: Any) -> bool:
        try:
            mapping["__mutation_test__"] = True
            return False
        except TypeError:
            return True
        except Exception:
            return False

    def _fixture_records(self) -> Tuple[Mapping[str, Any], ...]:
        return (
            {"event_id": "fomc_2026_01", "title": "FOMC Rate Decision", "family": "fed_event", "region": "us", "currency": "usd", "impact": "high", "scheduled_at": "2026-01-28T19:00:00Z", "forecast": "4.50%", "previous": "4.50%", "affected_markets": ["RATES", "PREDICTION_MARKETS"]},
            {"id": "cpi_2026_01", "event": "US CPI YoY", "category": "inflation_event", "area": "us", "ccy": "usd", "importance": "high", "time": "2026-01-15T13:30:00Z", "consensus": "2.9%", "previous": "3.0%", "markets": "RATES, EQUITIES, PREDICTION_MARKETS"},
            {"event_id": "minor_2026_01", "title": "Minor Survey", "family": "economic_release", "region": "us", "currency": "usd", "impact": "low", "scheduled_at": "2026-01-12T14:00:00Z", "affected_markets": ["LOCAL"]},
        )


__all__ = [
    "SCHEMA_VERSION",
    "GATE_ID",
    "MacroEventSubsystemIntegrationReport",
    "MacroEventSubsystemIntegrationGate",
]
'''

TEST_CODE = r'''
from qseries_v2.oracle_intelligence.macro_event_discovery_model.macro_event_subsystem_integration_gate import (
    MacroEventSubsystemIntegrationGate,
)


def test_med_009_macro_event_subsystem_integration_gate():
    gate = MacroEventSubsystemIntegrationGate(source_name="med_009_test_source", min_event_score=0.55)

    caps = gate.capabilities()
    health = gate.health()
    report = gate.run()

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["order_allowed"] is False
    assert caps["position_sizing_allowed"] is False
    assert caps["broker_connectivity_allowed"] is False
    assert caps["deterministic"] is True

    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert report.schema_version == "MED-009"
    assert report.gate_id == "oracle.discovery.gate.macro_event_subsystem_integration"
    assert report.status == "passed"
    assert report.failed_checks == 0
    assert report.warning_count == 0
    assert report.read_only is True

    assert report.checks["contract_schema_ok"] is True
    assert report.checks["adapter_schema_ok"] is True
    assert report.checks["engine_contract_schema_ok"] is True
    assert report.checks["pipeline_gate_schema_ok"] is True
    assert report.checks["registry_bridge_schema_ok"] is True
    assert report.checks["pipeline_bridge_schema_ok"] is True
    assert report.checks["oos_gate_schema_ok"] is True
    assert report.checks["replay_ledger_schema_ok"] is True

    assert report.checks["opportunities_emitted"] is True
    assert report.checks["registry_records_emitted"] is True
    assert report.checks["pipeline_packets_emitted"] is True
    assert report.checks["oos_packets_emitted"] is True
    assert report.checks["replay_entries_emitted"] is True

    assert report.checks["execution_not_allowed"] is True
    assert report.checks["order_not_allowed"] is True
    assert report.checks["position_sizing_not_allowed"] is True
    assert report.checks["deterministic_replay_fingerprint"] is True
    assert report.checks["immutable_registry_payload"] is True
    assert report.checks["immutable_pipeline_payload"] is True
    assert report.checks["immutable_replay_summary"] is True
    assert report.checks["read_only_telemetry_all"] is True

    d = report.to_dict()
    assert d["telemetry"]["opportunities_emitted"] == 2
    assert d["telemetry"]["registry_records_emitted"] == 2
    assert d["telemetry"]["pipeline_packets_emitted"] == 2
    assert d["telemetry"]["oos_packets_emitted"] == 2
    assert d["telemetry"]["replay_entries_emitted"] == 2
    assert d["telemetry"]["execution_allowed"] is False
    assert d["telemetry"]["order_allowed"] is False
    assert d["telemetry"]["position_sizing_allowed"] is False
    assert d["telemetry"]["replay_match"] is True

    print("[PASS] MED-009 Macro Event Subsystem Integration Gate")
    print({
        "schema_version": d["schema_version"],
        "gate_id": d["gate_id"],
        "status": d["status"],
        "passed_checks": d["passed_checks"],
        "failed_checks": d["failed_checks"],
        "opportunities": d["telemetry"]["opportunities_emitted"],
        "packets": d["telemetry"]["pipeline_packets_emitted"],
        "replay_match": d["telemetry"]["replay_match"],
        "read_only": d["read_only"],
    })


if __name__ == "__main__":
    test_med_009_macro_event_subsystem_integration_gate()
'''

INIT_EXPORT = '''
try:
    from .macro_event_subsystem_integration_gate import (
        MacroEventSubsystemIntegrationGate,
        MacroEventSubsystemIntegrationReport,
    )
except Exception:
    pass
'''

GATE_FILE.write_text(GATE_CODE, encoding="utf-8")
TEST_FILE.write_text(TEST_CODE, encoding="utf-8")

existing = INIT_FILE.read_text(encoding="utf-8") if INIT_FILE.exists() else ""
if "MacroEventSubsystemIntegrationGate" not in existing:
    INIT_FILE.write_text(existing.rstrip() + "\n" + INIT_EXPORT.lstrip(), encoding="utf-8")

print("========================================")
print(" MED-009 INSTALLER")
print(" Macro Event Subsystem Integration Gate")
print("========================================")
print(f"[OK] Wrote {GATE_FILE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT_FILE}")
print()
print("[DONE] MED-009 installed")
print()
print("Run:")
print("py test_med_009_macro_event_subsystem_integration_gate.py")