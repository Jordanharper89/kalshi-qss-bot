"""
SLD-009 Solana Launch Subsystem Integration Gate

Full read-only integration gate for Solana Launch Discovery Division.

Verifies:
- SLD-001 Contract
- SLD-002 Source Adapter
- SLD-003 Discovery Engine
- SLD-004 Pipeline Gate
- SLD-005 Registry Bridge
- SLD-006 Pipeline Bridge
- SLD-007 OOS Runtime Gate
- SLD-008 Replay Ledger
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

from .solana_launch_discovery_contract import (
    SCHEMA_VERSION as CONTRACT_SCHEMA_VERSION,
    SolanaLaunchDiscoveryFamily,
    SolanaLaunchDiscoveryRequest,
)
from .solana_launch_source_adapter import SolanaLaunchSourceAdapter
from .solana_launch_discovery_engine import SolanaLaunchDiscoveryEngine
from .solana_launch_discovery_pipeline_gate import SolanaLaunchDiscoveryPipelineGate
from .solana_launch_discovery_registry_bridge import SolanaLaunchDiscoveryRegistryBridge
from .solana_launch_discovery_pipeline_bridge import SolanaLaunchDiscoveryPipelineBridge
from .solana_launch_discovery_oos_runtime_gate import SolanaLaunchDiscoveryOOSRuntimeGate
from .solana_launch_discovery_replay_ledger import SolanaLaunchDiscoveryReplayLedger


SCHEMA_VERSION = "SLD-009"
GATE_ID = "oracle.discovery.gate.solana_launch_subsystem_integration"
GATE_NAME = "Solana Launch Subsystem Integration Gate"


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
class SolanaLaunchSubsystemIntegrationReport:
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


class SolanaLaunchSubsystemIntegrationGate:
    schema_version = SCHEMA_VERSION
    gate_id = GATE_ID
    gate_name = GATE_NAME
    read_only = True

    def __init__(
        self,
        source_name: str = "solana_launch_subsystem_gate_source",
        min_liquidity_usd: float = 1000.0,
        max_age_seconds: float = 600.0,
        min_launch_score: float = 0.55,
    ) -> None:
        self.source_name = str(source_name)
        self.min_liquidity_usd = float(min_liquidity_usd)
        self.max_age_seconds = float(max_age_seconds)
        self.min_launch_score = float(min_launch_score)

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "gate_id": self.gate_id,
            "gate_name": self.gate_name,
            "read_only": True,
            "validates": [
                "SLD-001 contract",
                "SLD-002 source adapter",
                "SLD-003 discovery engine",
                "SLD-004 pipeline gate",
                "SLD-005 registry bridge",
                "SLD-006 pipeline bridge",
                "SLD-007 OOS runtime gate",
                "SLD-008 replay ledger",
                "deterministic replay",
                "immutable payloads",
                "no signing authority",
                "no fund movement authority",
                "no swap authority",
                "no snipe authority",
                "no execution authority",
            ],
            "execution": False,
            "signing_allowed": False,
            "fund_movement_allowed": False,
            "swap_allowed": False,
            "snipe_allowed": False,
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

    def run(self, raw_records: Sequence[Any] | None = None) -> SolanaLaunchSubsystemIntegrationReport:
        started_at = _utc_now_iso()
        raw = tuple(raw_records or self._fixture_records())

        adapter = SolanaLaunchSourceAdapter(source_name=self.source_name)
        batch = adapter.normalize_batch(raw)

        request = SolanaLaunchDiscoveryRequest(
            request_id="sld009.solana.launch.subsystem.integration",
            family=SolanaLaunchDiscoveryFamily.NEW_TOKEN_LAUNCH,
            source_name=self.source_name,
            mints=tuple(sorted({s.mint for s in batch.snapshots})),
            pools=tuple(sorted({s.pool_address for s in batch.snapshots})),
            metadata={"snapshots": batch.snapshots},
        )

        engine = SolanaLaunchDiscoveryEngine(
            min_liquidity_usd=self.min_liquidity_usd,
            max_age_seconds=self.max_age_seconds,
            min_launch_score=self.min_launch_score,
        )
        discovery_report = engine.discover(request)

        pipeline_gate = SolanaLaunchDiscoveryPipelineGate(
            source_name=self.source_name,
            min_liquidity_usd=self.min_liquidity_usd,
            max_age_seconds=self.max_age_seconds,
            min_launch_score=self.min_launch_score,
        )
        pipeline_gate_report = pipeline_gate.run(raw)

        registry_bridge = SolanaLaunchDiscoveryRegistryBridge()
        registry_report = registry_bridge.bridge_report(discovery_report)

        pipeline_bridge = SolanaLaunchDiscoveryPipelineBridge()
        pipeline_report = pipeline_bridge.bridge_records(registry_report.records)

        oos_gate = SolanaLaunchDiscoveryOOSRuntimeGate(
            source_name=self.source_name,
            min_liquidity_usd=self.min_liquidity_usd,
            max_age_seconds=self.max_age_seconds,
            min_launch_score=self.min_launch_score,
        )
        oos_report = oos_gate.run(raw)

        replay_ledger = SolanaLaunchDiscoveryReplayLedger()
        replay_a = replay_ledger.record_packets(oos_report.packets)
        replay_b = replay_ledger.record_packets(oos_gate.run(tuple(reversed(raw))).packets)
        replay_compare = replay_ledger.compare(replay_a, replay_b)

        checks = {
            "gate_is_read_only": self.read_only is True,
            "contract_schema_ok": CONTRACT_SCHEMA_VERSION == "SLD-001",
            "request_is_read_only": request.read_only is True,
            "adapter_is_read_only": adapter.read_only is True,
            "engine_is_read_only": engine.read_only is True,
            "pipeline_gate_is_read_only": pipeline_gate.read_only is True,
            "registry_bridge_is_read_only": registry_bridge.read_only is True,
            "pipeline_bridge_is_read_only": pipeline_bridge.read_only is True,
            "oos_gate_is_read_only": oos_gate.read_only is True,
            "replay_ledger_is_read_only": replay_ledger.read_only is True,

            "adapter_schema_ok": batch.schema_version == "SLD-002",
            "engine_contract_schema_ok": discovery_report.schema_version == "SLD-001",
            "pipeline_gate_schema_ok": pipeline_gate_report.schema_version == "SLD-004",
            "registry_bridge_schema_ok": registry_report.schema_version == "SLD-005",
            "pipeline_bridge_schema_ok": pipeline_report.schema_version == "SLD-006",
            "oos_gate_schema_ok": oos_report.schema_version == "SLD-007",
            "replay_ledger_schema_ok": replay_a.schema_version == "SLD-008",

            "snapshots_emitted": len(batch.snapshots) == len(raw),
            "launches_seen": discovery_report.telemetry.launches_seen == 3,
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

            "all_solana_launch_markets_shape": all(
                o.universal_market.get("market_type") == "solana_launch"
                and o.universal_market.get("execution_allowed") is False
                and o.universal_market.get("signing_allowed") is False
                and o.universal_market.get("fund_movement_allowed") is False
                and o.universal_market.get("swap_allowed") is False
                and o.universal_market.get("snipe_allowed") is False
                for o in discovery_report.opportunities
            ),
            "all_pipeline_packets_validation_ready": all(
                p.payload.get("validation_required") is True for p in pipeline_report.packets
            ),
            "all_pipeline_packets_registry_ready": all(
                p.payload.get("registry_required") is True for p in pipeline_report.packets
            ),
            "all_pipeline_packets_ranking_ready": all(
                p.payload.get("ranking_required") is True for p in pipeline_report.packets
            ),
            "execution_not_allowed": all(
                p.payload.get("execution_allowed") is False for p in pipeline_report.packets
            ),
            "signing_not_allowed": all(
                p.payload.get("signing_allowed") is False for p in pipeline_report.packets
            ),
            "fund_movement_not_allowed": all(
                p.payload.get("fund_movement_allowed") is False for p in pipeline_report.packets
            ),
            "swap_not_allowed": all(
                p.payload.get("swap_allowed") is False for p in pipeline_report.packets
            ),
            "snipe_not_allowed": all(
                p.payload.get("snipe_allowed") is False for p in pipeline_report.packets
            ),
            "no_execution_fields_in_registry": all(
                r.audit.get("execution_fields_present") is False for r in registry_report.records
            ),
            "no_execution_fields_in_pipeline": all(
                p.audit.get("execution_fields_present") is False for p in pipeline_report.packets
            ),

            "immutable_registry_payload": self._immutable_mapping_check(
                registry_report.records[0].payload if registry_report.records else {}
            ),
            "immutable_pipeline_payload": self._immutable_mapping_check(
                pipeline_report.packets[0].payload if pipeline_report.packets else {}
            ),
            "immutable_replay_summary": self._immutable_mapping_check(
                replay_a.entries[0].payload_summary if replay_a.entries else {}
            ),

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

        telemetry = MappingProxyType(
            {
                "schema_version": self.schema_version,
                "gate_id": self.gate_id,
                "started_at": started_at,
                "completed_at": _utc_now_iso(),
                "raw_records_seen": len(raw),
                "snapshots_emitted": len(batch.snapshots),
                "launches_seen": discovery_report.telemetry.launches_seen,
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
                "signing_allowed": False,
                "fund_movement_allowed": False,
                "swap_allowed": False,
                "snipe_allowed": False,
                "replay_match": replay_compare.matching,
                "run_fingerprint": replay_a.run_fingerprint,
            }
        )

        return SolanaLaunchSubsystemIntegrationReport(
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
            {
                "token_mint": "mint_a",
                "ticker": "ALPHA",
                "name": "Alpha Token",
                "pool_address": "pool_a",
                "dex": "raydium",
                "quote_asset": "SOL",
                "liquidity_usd": 50000,
                "market_cap_usd": 200000,
                "volume_5m_usd": 15000,
                "holder_count": 250,
                "age_seconds": 30,
                "mint_authority_disabled": True,
                "freeze_authority_disabled": True,
                "lp_burned": True,
                "pool_status": "active",
                "deployer_wallet": "wallet_a",
                "tx_signature": "tx_a",
                "detected_at": "2026-01-01T00:01:00Z",
            },
            {
                "mint": "mint_b",
                "symbol": "BETA",
                "name": "Beta Token",
                "pool": "pool_b",
                "dex": "Raydium",
                "quote": "SOL",
                "liquidity": 25000,
                "market_cap": 120000,
                "volume_5m": 8000,
                "holders": 120,
                "age": 90,
                "mint_disabled": True,
                "freeze_disabled": True,
                "liquidity_burned": True,
                "status": "active",
                "creator": "wallet_b",
                "signature": "tx_b",
                "timestamp": "2026-01-01T00:02:00Z",
            },
            {
                "mint": "mint_bad",
                "symbol": "BAD",
                "pool": "pool_bad",
                "liquidity": 100,
                "age": 900,
                "mint_disabled": False,
                "freeze_disabled": False,
                "liquidity_burned": False,
                "status": "active",
            },
        )


__all__ = [
    "SCHEMA_VERSION",
    "GATE_ID",
    "GATE_NAME",
    "SolanaLaunchSubsystemIntegrationReport",
    "SolanaLaunchSubsystemIntegrationGate",
]
