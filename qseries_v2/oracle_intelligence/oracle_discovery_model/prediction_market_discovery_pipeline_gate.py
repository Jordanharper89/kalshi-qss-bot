"""
ODM-004 Prediction Market Discovery Pipeline Gate

Canonical regression/integration gate for:

raw prediction-market records
    -> ODM-003 PredictionMarketSourceAdapter
    -> ODM-002 PredictionMarketDiscoveryEngine
    -> UniversalOpportunity-shaped output

This gate is read-only and deterministic. It does not place trades, size
positions, execute orders, or manage exits.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

from .prediction_market_source_adapter import PredictionMarketSourceAdapter


SCHEMA_VERSION = "ODM-004"
GATE_ID = "oracle.discovery.gate.prediction_market_pipeline"
GATE_NAME = "Prediction Market Discovery Pipeline Gate"


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
class PredictionMarketDiscoveryGateReport:
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


class PredictionMarketDiscoveryPipelineGate:
    schema_version = SCHEMA_VERSION
    gate_id = GATE_ID
    gate_name = GATE_NAME
    read_only = True

    def __init__(
        self,
        source_name: str = "prediction_market_gate_source",
        min_edge: float = 0.02,
        min_liquidity: float = 100.0,
    ) -> None:
        self.source_name = source_name
        self.min_edge = float(min_edge)
        self.min_liquidity = float(min_liquidity)

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "gate_id": self.gate_id,
            "gate_name": self.gate_name,
            "read_only": True,
            "validates": [
                "ODM-003 source adapter",
                "ODM-002 discovery engine",
                "UniversalMarket-shaped normalization",
                "UniversalOpportunity-shaped emission",
                "deterministic replay",
                "immutable canonical output",
            ],
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

    def run(self, raw_markets: Sequence[Any] | None = None) -> PredictionMarketDiscoveryGateReport:
        started_at = _utc_now_iso()
        raw = tuple(raw_markets or self._fixture_markets())

        adapter = PredictionMarketSourceAdapter(source_name=self.source_name)

        batch_a = adapter.normalize_batch(raw)
        batch_b = adapter.normalize_batch(tuple(reversed(raw)))

        report_a = adapter.discover(
            raw,
            min_edge=self.min_edge,
            min_liquidity=self.min_liquidity,
        )
        report_b = adapter.discover(
            tuple(reversed(raw)),
            min_edge=self.min_edge,
            min_liquidity=self.min_liquidity,
        )

        opportunity_ids_a = tuple(o.opportunity_id for o in report_a.opportunities)
        opportunity_ids_b = tuple(o.opportunity_id for o in report_b.opportunities)

        checks = {
            "gate_is_read_only": self.read_only is True,
            "adapter_is_read_only": adapter.read_only is True,
            "adapter_batch_is_read_only": batch_a.read_only is True,
            "discovery_report_is_read_only": report_a.read_only is True,
            "raw_records_seen": batch_a.telemetry.get("raw_records_seen") == len(raw),
            "snapshots_emitted": len(batch_a.snapshots) == len(raw),
            "adapter_deterministic_order": tuple(s.market_id for s in batch_a.snapshots)
            == tuple(s.market_id for s in batch_b.snapshots),
            "engine_emits_opportunities": len(report_a.opportunities) >= 1,
            "engine_replay_deterministic": opportunity_ids_a == opportunity_ids_b,
            "all_opportunities_read_only": all(o.read_only is True for o in report_a.opportunities),
            "all_opportunities_have_ids": all(bool(o.opportunity_id) for o in report_a.opportunities),
            "all_opportunities_have_market_ids": all(bool(o.market_id) for o in report_a.opportunities),
            "all_opportunities_have_side": all(o.side in {"YES", "NO"} for o in report_a.opportunities),
            "all_opportunities_have_edge": all(abs(o.edge) >= self.min_edge for o in report_a.opportunities),
            "all_opportunities_have_confidence": all(0.0 <= o.confidence <= 1.0 for o in report_a.opportunities),
            "all_opportunities_have_explanation": all(bool(o.explanation) for o in report_a.opportunities),
            "all_opportunities_have_telemetry": all(bool(o.telemetry) for o in report_a.opportunities),
            "universal_market_shape": all(
                o.universal_market.get("market_type") == "prediction_market"
                and o.universal_market.get("read_only") is True
                for o in report_a.opportunities
            ),
            "source_engine_id_present": all(
                o.source_engine_id == "oracle.discovery.prediction_market"
                for o in report_a.opportunities
            ),
            "schema_versions_present": (
                batch_a.schema_version == "ODM-003"
                and report_a.schema_version == "ODM-002"
            ),
            "telemetry_present": bool(batch_a.telemetry) and bool(report_a.telemetry),
            "no_execution_fields": all(
                not hasattr(o, "order_id")
                and not hasattr(o, "position_size")
                and not hasattr(o, "execution_id")
                for o in report_a.opportunities
            ),
            "immutable_market_output": self._check_immutable_market(report_a),
        }

        frozen_checks = _freeze(checks)
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
                "engine_schema_version": report_a.schema_version,
                "read_only": True,
                "deterministic_replay": opportunity_ids_a == opportunity_ids_b,
            }
        )

        return PredictionMarketDiscoveryGateReport(
            schema_version=self.schema_version,
            gate_id=self.gate_id,
            status="passed" if failed == 0 else "failed",
            passed_checks=passed,
            failed_checks=failed,
            warning_count=0,
            checks=frozen_checks,
            telemetry=telemetry,
            read_only=True,
        )

    def _check_immutable_market(self, report: Any) -> bool:
        if not report.opportunities:
            return False

        market = report.opportunities[0].universal_market
        try:
            market["read_only"] = False
            return False
        except TypeError:
            return True

    def _fixture_markets(self) -> Tuple[Mapping[str, Any], ...]:
        return (
            {
                "ticker": "KX.ODM004.YES",
                "question": "Will ODM-004 fixture one resolve yes?",
                "platform": "kalshi",
                "category": "oracle_test",
                "price": 40,
                "model_probability": 54,
                "liquidity": 2500,
                "volume": 10000,
                "status": "open",
            },
            {
                "ticker": "KX.ODM004.NO",
                "question": "Will ODM-004 fixture two resolve yes?",
                "platform": "kalshi",
                "category": "oracle_test",
                "price": 76,
                "model_probability": 64,
                "liquidity": 3000,
                "volume": 15000,
                "status": "open",
            },
            {
                "ticker": "KX.ODM004.REJECT",
                "question": "Will ODM-004 low-edge fixture resolve yes?",
                "platform": "kalshi",
                "category": "oracle_test",
                "price": 50,
                "model_probability": 50.5,
                "liquidity": 3000,
                "volume": 15000,
                "status": "open",
            },
        )


__all__ = [
    "SCHEMA_VERSION",
    "GATE_ID",
    "GATE_NAME",
    "PredictionMarketDiscoveryGateReport",
    "PredictionMarketDiscoveryPipelineGate",
]
