"""
ADM-004 Cross-Venue Arbitrage Discovery Pipeline Gate

Read-only integration gate for:
ADM-002 Cross-Venue Arbitrage Source Adapter
    -> ADM-003 Cross-Venue Arbitrage Discovery Engine
    -> UniversalOpportunity-shaped arbitrage output

No trading, routing, sizing, leg execution, or exits.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

from .arbitrage_discovery_contract import ArbitrageDiscoveryFamily, ArbitrageDiscoveryRequest
from .cross_venue_arbitrage_source_adapter import CrossVenueArbitrageSourceAdapter
from .cross_venue_arbitrage_discovery_engine import CrossVenueArbitrageDiscoveryEngine


SCHEMA_VERSION = "ADM-004"
GATE_ID = "oracle.discovery.gate.cross_venue_arbitrage_pipeline"
GATE_NAME = "Cross-Venue Arbitrage Discovery Pipeline Gate"


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
class CrossVenueArbitrageDiscoveryGateReport:
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


class CrossVenueArbitrageDiscoveryPipelineGate:
    schema_version = SCHEMA_VERSION
    gate_id = GATE_ID
    gate_name = GATE_NAME
    read_only = True

    def __init__(
        self,
        source_name: str = "cross_venue_arbitrage_gate_source",
        min_net_edge_percent: float = 0.001,
        min_liquidity: float = 1000.0,
    ) -> None:
        self.source_name = str(source_name)
        self.min_net_edge_percent = float(min_net_edge_percent)
        self.min_liquidity = float(min_liquidity)

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "gate_id": self.gate_id,
            "gate_name": self.gate_name,
            "read_only": True,
            "validates": [
                "ADM-002 source adapter",
                "ADM-003 discovery engine",
                "cross-venue arbitrage UniversalMarket shape",
                "cross-venue arbitrage UniversalOpportunity shape",
                "deterministic replay",
                "immutable output",
                "no execution authority",
            ],
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
            "gate_id": self.gate_id,
            "status": "ok",
            "ready": True,
            "read_only": True,
            "checked_at": _utc_now_iso(),
        }

    def run(self, raw_records: Sequence[Any] | None = None) -> CrossVenueArbitrageDiscoveryGateReport:
        started_at = _utc_now_iso()
        raw = tuple(raw_records or self._fixture_records())

        adapter = CrossVenueArbitrageSourceAdapter(source_name=self.source_name)
        batch_a = adapter.normalize_batch(raw)
        batch_b = adapter.normalize_batch(tuple(reversed(raw)))

        request_a = ArbitrageDiscoveryRequest(
            request_id="adm004.cross.venue.pipeline.gate.a",
            family=ArbitrageDiscoveryFamily.CROSS_EXCHANGE,
            source_name=self.source_name,
            symbols=tuple(sorted({s.symbol for s in batch_a.snapshots})),
            venues=tuple(sorted({s.venue for s in batch_a.snapshots})),
            metadata={"snapshots": batch_a.snapshots},
        )
        request_b = ArbitrageDiscoveryRequest(
            request_id="adm004.cross.venue.pipeline.gate.b",
            family=ArbitrageDiscoveryFamily.CROSS_EXCHANGE,
            source_name=self.source_name,
            symbols=tuple(sorted({s.symbol for s in batch_b.snapshots})),
            venues=tuple(sorted({s.venue for s in batch_b.snapshots})),
            metadata={"snapshots": batch_b.snapshots},
        )

        engine = CrossVenueArbitrageDiscoveryEngine(
            min_net_edge_percent=self.min_net_edge_percent,
            min_liquidity=self.min_liquidity,
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
            "adapter_schema_ok": batch_a.schema_version == "ADM-002",
            "engine_contract_schema_ok": report_a.schema_version == "ADM-001",
            "raw_records_seen": batch_a.telemetry.get("raw_records_seen") == len(raw),
            "snapshots_emitted": len(batch_a.snapshots) == len(raw),
            "adapter_deterministic_order": tuple((s.symbol, s.venue, s.quote_id) for s in batch_a.snapshots)
            == tuple((s.symbol, s.venue, s.quote_id) for s in batch_b.snapshots),
            "engine_emits_opportunities": len(report_a.opportunities) >= 1,
            "engine_replay_deterministic": opportunity_ids_a == opportunity_ids_b,
            "pairs_evaluated": report_a.telemetry.pairs_evaluated >= 1,
            "all_opportunities_read_only": all(o.read_only is True for o in report_a.opportunities),
            "all_opportunities_have_ids": all(bool(o.opportunity_id) for o in report_a.opportunities),
            "all_opportunities_have_symbol": all(bool(o.symbol) for o in report_a.opportunities),
            "all_opportunities_have_buy_sell_venues": all(
                bool(o.buy_venue) and bool(o.sell_venue) and o.buy_venue != o.sell_venue
                for o in report_a.opportunities
            ),
            "all_opportunities_have_positive_prices": all(
                o.buy_price > 0.0 and o.sell_price > 0.0 for o in report_a.opportunities
            ),
            "all_opportunities_have_positive_net_edge": all(
                o.net_edge_percent >= self.min_net_edge_percent for o in report_a.opportunities
            ),
            "all_opportunities_have_confidence": all(
                0.0 <= o.confidence <= 1.0 for o in report_a.opportunities
            ),
            "all_opportunities_have_explanation": all(
                bool(o.explanation) for o in report_a.opportunities
            ),
            "all_opportunities_have_telemetry": all(
                bool(o.telemetry) for o in report_a.opportunities
            ),
            "universal_market_shape": all(
                o.universal_market.get("market_type") == "cross_venue_arbitrage"
                and o.universal_market.get("read_only") is True
                and o.universal_market.get("execution_allowed") is False
                for o in report_a.opportunities
            ),
            "source_engine_id_present": all(
                o.source_engine_id == "oracle.discovery.cross_venue_arbitrage"
                for o in report_a.opportunities
            ),
            "telemetry_present": bool(batch_a.telemetry) and bool(report_a.telemetry),
            "no_execution_fields": all(
                not hasattr(o, "order_id")
                and not hasattr(o, "position_size")
                and not hasattr(o, "execution_id")
                and not hasattr(o, "route_id")
                and not hasattr(o, "leg_execution_id")
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
                "pairs_evaluated": report_a.telemetry.pairs_evaluated,
                "opportunities_emitted": len(report_a.opportunities),
                "adapter_schema_version": batch_a.schema_version,
                "engine_contract_schema_version": report_a.schema_version,
                "passed_checks": passed,
                "failed_checks": failed,
                "warning_count": 0,
                "read_only": True,
                "execution_allowed": False,
                "order_allowed": False,
                "route_allowed": False,
                "leg_execution_allowed": False,
                "deterministic_replay": opportunity_ids_a == opportunity_ids_b,
            }
        )

        return CrossVenueArbitrageDiscoveryGateReport(
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
        )


__all__ = [
    "SCHEMA_VERSION",
    "GATE_ID",
    "GATE_NAME",
    "CrossVenueArbitrageDiscoveryGateReport",
    "CrossVenueArbitrageDiscoveryPipelineGate",
]
