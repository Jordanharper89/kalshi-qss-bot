"""
SLD-004 Solana Launch Discovery Pipeline Gate

Read-only integration gate for:
SLD-002 Solana Launch Source Adapter
    -> SLD-003 Solana Launch Discovery Engine
    -> UniversalOpportunity-shaped Solana launch output

No signing, fund movement, swaps, sniping, routing, buying, selling, or execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

from .solana_launch_discovery_contract import (
    SolanaLaunchDiscoveryFamily,
    SolanaLaunchDiscoveryRequest,
)
from .solana_launch_source_adapter import SolanaLaunchSourceAdapter
from .solana_launch_discovery_engine import SolanaLaunchDiscoveryEngine


SCHEMA_VERSION = "SLD-004"
GATE_ID = "oracle.discovery.gate.solana_launch_pipeline"
GATE_NAME = "Solana Launch Discovery Pipeline Gate"


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
class SolanaLaunchDiscoveryGateReport:
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


class SolanaLaunchDiscoveryPipelineGate:
    schema_version = SCHEMA_VERSION
    gate_id = GATE_ID
    gate_name = GATE_NAME
    read_only = True

    def __init__(
        self,
        source_name: str = "solana_launch_gate_source",
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
                "SLD-002 source adapter",
                "SLD-003 discovery engine",
                "solana launch UniversalMarket shape",
                "solana launch UniversalOpportunity shape",
                "deterministic replay",
                "immutable output",
                "no signing authority",
                "no fund movement authority",
                "no swap authority",
                "no snipe authority",
                "no execution authority",
            ],
            "deterministic": True,
            "telemetry": True,
            "execution": False,
            "signing_allowed": False,
            "fund_movement_allowed": False,
            "swap_allowed": False,
            "snipe_allowed": False,
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

    def run(self, raw_records: Sequence[Any] | None = None) -> SolanaLaunchDiscoveryGateReport:
        started_at = _utc_now_iso()
        raw = tuple(raw_records or self._fixture_records())

        adapter = SolanaLaunchSourceAdapter(source_name=self.source_name)
        batch_a = adapter.normalize_batch(raw)
        batch_b = adapter.normalize_batch(tuple(reversed(raw)))

        request_a = SolanaLaunchDiscoveryRequest(
            request_id="sld004.solana.launch.pipeline.gate.a",
            family=SolanaLaunchDiscoveryFamily.NEW_TOKEN_LAUNCH,
            source_name=self.source_name,
            mints=tuple(sorted({s.mint for s in batch_a.snapshots})),
            pools=tuple(sorted({s.pool_address for s in batch_a.snapshots})),
            metadata={"snapshots": batch_a.snapshots},
        )
        request_b = SolanaLaunchDiscoveryRequest(
            request_id="sld004.solana.launch.pipeline.gate.b",
            family=SolanaLaunchDiscoveryFamily.NEW_TOKEN_LAUNCH,
            source_name=self.source_name,
            mints=tuple(sorted({s.mint for s in batch_b.snapshots})),
            pools=tuple(sorted({s.pool_address for s in batch_b.snapshots})),
            metadata={"snapshots": batch_b.snapshots},
        )

        engine = SolanaLaunchDiscoveryEngine(
            min_liquidity_usd=self.min_liquidity_usd,
            max_age_seconds=self.max_age_seconds,
            min_launch_score=self.min_launch_score,
        )

        report_a = engine.discover(request_a)
        report_b = engine.discover(request_b)

        opportunity_ids_a = tuple(o.opportunity_id for o in report_a.opportunities)
        opportunity_ids_b = tuple(o.opportunity_id for o in report_b.opportunities)

        checks = {
            "gate_is_read_only": self.read_only is True,
            "adapter_is_read_only": adapter.read_only is True,
            "batch_is_read_only": batch_a.read_only is True,
            "engine_is_read_only": engine.read_only is True,
            "discovery_report_is_read_only": report_a.read_only is True,
            "adapter_schema_ok": batch_a.schema_version == "SLD-002",
            "engine_contract_schema_ok": report_a.schema_version == "SLD-001",
            "raw_records_seen": batch_a.telemetry.get("raw_records_seen") == len(raw),
            "snapshots_emitted": len(batch_a.snapshots) == len(raw),
            "launches_seen": batch_a.telemetry.get("launches_seen") == 3,
            "adapter_deterministic_order": tuple((s.age_seconds, s.symbol, s.mint, s.pool_address) for s in batch_a.snapshots)
            == tuple((s.age_seconds, s.symbol, s.mint, s.pool_address) for s in batch_b.snapshots),
            "engine_emits_opportunities": len(report_a.opportunities) == 2,
            "engine_replay_deterministic": opportunity_ids_a == opportunity_ids_b,
            "all_opportunities_read_only": all(o.read_only is True for o in report_a.opportunities),
            "all_opportunities_have_ids": all(bool(o.opportunity_id) for o in report_a.opportunities),
            "all_opportunities_have_mint": all(bool(o.mint) for o in report_a.opportunities),
            "all_opportunities_have_symbol": all(bool(o.symbol) for o in report_a.opportunities),
            "all_opportunities_have_launch_score": all(
                o.launch_score >= self.min_launch_score for o in report_a.opportunities
            ),
            "all_opportunities_have_confidence": all(
                0.0 <= o.confidence <= 1.0 for o in report_a.opportunities
            ),
            "all_opportunities_have_liquidity": all(
                o.liquidity_usd >= self.min_liquidity_usd for o in report_a.opportunities
            ),
            "all_opportunities_are_fresh": all(
                o.age_seconds <= self.max_age_seconds for o in report_a.opportunities
            ),
            "all_opportunities_have_explanation": all(
                bool(o.explanation) for o in report_a.opportunities
            ),
            "all_opportunities_have_telemetry": all(
                bool(o.telemetry) for o in report_a.opportunities
            ),
            "universal_market_shape": all(
                o.universal_market.get("market_type") == "solana_launch"
                and o.universal_market.get("read_only") is True
                and o.universal_market.get("execution_allowed") is False
                and o.universal_market.get("signing_allowed") is False
                and o.universal_market.get("fund_movement_allowed") is False
                and o.universal_market.get("swap_allowed") is False
                and o.universal_market.get("snipe_allowed") is False
                for o in report_a.opportunities
            ),
            "source_engine_id_present": all(
                o.source_engine_id == "oracle.discovery.solana_launch"
                for o in report_a.opportunities
            ),
            "telemetry_present": bool(batch_a.telemetry) and bool(report_a.telemetry),
            "no_execution_fields": all(
                not hasattr(o, "order_id")
                and not hasattr(o, "position_size")
                and not hasattr(o, "execution_id")
                and not hasattr(o, "signature")
                and not hasattr(o, "private_key")
                and not hasattr(o, "swap_route")
                for o in report_a.opportunities
            ),
            "immutable_universal_market": self._check_immutable_market(report_a),
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
                "snapshots_emitted": len(batch_a.snapshots),
                "launches_seen": batch_a.telemetry.get("launches_seen"),
                "opportunities_emitted": len(report_a.opportunities),
                "adapter_schema_version": batch_a.schema_version,
                "engine_contract_schema_version": report_a.schema_version,
                "passed_checks": passed,
                "failed_checks": failed,
                "warning_count": 0,
                "read_only": True,
                "execution_allowed": False,
                "signing_allowed": False,
                "fund_movement_allowed": False,
                "swap_allowed": False,
                "snipe_allowed": False,
                "deterministic_replay": opportunity_ids_a == opportunity_ids_b,
            }
        )

        return SolanaLaunchDiscoveryGateReport(
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

    def _check_immutable_market(self, report: Any) -> bool:
        if not report.opportunities:
            return False
        try:
            report.opportunities[0].universal_market["execution_allowed"] = True
            return False
        except TypeError:
            return True

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
    "SolanaLaunchDiscoveryGateReport",
    "SolanaLaunchDiscoveryPipelineGate",
]
