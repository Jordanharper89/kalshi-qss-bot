"""
CDM-004 Crypto Spot Discovery Pipeline Gate

Read-only integration gate for:
CDM-002 Crypto Spot Source Adapter
    -> CDM-003 Crypto Spot Discovery Engine
    -> UniversalOpportunity-shaped crypto spot output

No execution authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

from .crypto_discovery_contract import CryptoDiscoveryFamily, CryptoDiscoveryRequest
from .crypto_spot_source_adapter import CryptoSpotSourceAdapter
from .crypto_spot_discovery_engine import CryptoSpotDiscoveryEngine


SCHEMA_VERSION = "CDM-004"
GATE_ID = "oracle.discovery.gate.crypto_spot_pipeline"
GATE_NAME = "Crypto Spot Discovery Pipeline Gate"


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
class CryptoSpotDiscoveryGateReport:
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


class CryptoSpotDiscoveryPipelineGate:
    schema_version = SCHEMA_VERSION
    gate_id = GATE_ID
    gate_name = GATE_NAME
    read_only = True

    def __init__(
        self,
        source_name: str = "crypto_spot_gate_source",
        min_edge_percent: float = 0.01,
        min_liquidity: float = 1000.0,
    ) -> None:
        self.source_name = str(source_name)
        self.min_edge_percent = float(min_edge_percent)
        self.min_liquidity = float(min_liquidity)

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "gate_id": self.gate_id,
            "gate_name": self.gate_name,
            "read_only": True,
            "validates": [
                "CDM-002 source adapter",
                "CDM-003 discovery engine",
                "crypto spot UniversalMarket shape",
                "crypto spot UniversalOpportunity shape",
                "deterministic replay",
                "immutable output",
                "no execution authority",
            ],
            "deterministic": True,
            "telemetry": True,
            "execution": False,
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

    def run(self, raw_records: Sequence[Any] | None = None) -> CryptoSpotDiscoveryGateReport:
        started_at = _utc_now_iso()
        raw = tuple(raw_records or self._fixture_records())

        adapter = CryptoSpotSourceAdapter(source_name=self.source_name)
        batch_a = adapter.normalize_batch(raw)
        batch_b = adapter.normalize_batch(tuple(reversed(raw)))

        request_a = CryptoDiscoveryRequest(
            request_id="cdm004.crypto.spot.pipeline.gate.a",
            family=CryptoDiscoveryFamily.CRYPTO_SPOT,
            source_name=self.source_name,
            symbols=tuple(s.symbol for s in batch_a.snapshots),
            metadata={"snapshots": batch_a.snapshots},
        )
        request_b = CryptoDiscoveryRequest(
            request_id="cdm004.crypto.spot.pipeline.gate.b",
            family=CryptoDiscoveryFamily.CRYPTO_SPOT,
            source_name=self.source_name,
            symbols=tuple(s.symbol for s in batch_b.snapshots),
            metadata={"snapshots": batch_b.snapshots},
        )

        engine = CryptoSpotDiscoveryEngine(
            min_edge_percent=self.min_edge_percent,
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
            "adapter_schema_ok": batch_a.schema_version == "CDM-002",
            "engine_contract_schema_ok": report_a.schema_version == "CDM-001",
            "raw_records_seen": batch_a.telemetry.get("raw_records_seen") == len(raw),
            "snapshots_emitted": len(batch_a.snapshots) == len(raw),
            "adapter_deterministic_order": tuple(s.symbol for s in batch_a.snapshots)
            == tuple(s.symbol for s in batch_b.snapshots),
            "engine_emits_opportunities": len(report_a.opportunities) >= 1,
            "engine_replay_deterministic": opportunity_ids_a == opportunity_ids_b,
            "all_opportunities_read_only": all(o.read_only is True for o in report_a.opportunities),
            "all_opportunities_have_ids": all(bool(o.opportunity_id) for o in report_a.opportunities),
            "all_opportunities_have_symbol": all(bool(o.symbol) for o in report_a.opportunities),
            "all_opportunities_have_side": all(
                o.side in {"LONG_SPOT_OBSERVATION", "SHORT_SPOT_OBSERVATION"}
                for o in report_a.opportunities
            ),
            "all_opportunities_have_edge": all(
                abs(o.edge_percent) >= self.min_edge_percent
                for o in report_a.opportunities
            ),
            "all_opportunities_have_confidence": all(
                0.0 <= o.confidence <= 1.0
                for o in report_a.opportunities
            ),
            "all_opportunities_have_explanation": all(
                bool(o.explanation) for o in report_a.opportunities
            ),
            "all_opportunities_have_telemetry": all(
                bool(o.telemetry) for o in report_a.opportunities
            ),
            "universal_market_shape": all(
                o.universal_market.get("market_type") == "crypto_spot"
                and o.universal_market.get("read_only") is True
                for o in report_a.opportunities
            ),
            "source_engine_id_present": all(
                o.source_engine_id == "oracle.discovery.crypto_spot"
                for o in report_a.opportunities
            ),
            "telemetry_present": bool(batch_a.telemetry) and bool(report_a.telemetry),
            "no_execution_fields": all(
                not hasattr(o, "order_id")
                and not hasattr(o, "position_size")
                and not hasattr(o, "execution_id")
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
                "opportunities_emitted": len(report_a.opportunities),
                "adapter_schema_version": batch_a.schema_version,
                "engine_contract_schema_version": report_a.schema_version,
                "passed_checks": passed,
                "failed_checks": failed,
                "warning_count": 0,
                "read_only": True,
                "execution_allowed": False,
                "deterministic_replay": opportunity_ids_a == opportunity_ids_b,
            }
        )

        return CryptoSpotDiscoveryGateReport(
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
            report.opportunities[0].universal_market["read_only"] = False
            return False
        except TypeError:
            return True

    def _fixture_records(self) -> Tuple[Mapping[str, Any], ...]:
        return (
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
        )


__all__ = [
    "SCHEMA_VERSION",
    "GATE_ID",
    "GATE_NAME",
    "CryptoSpotDiscoveryGateReport",
    "CryptoSpotDiscoveryPipelineGate",
]
