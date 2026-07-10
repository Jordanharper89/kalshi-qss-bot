"""
CDM-003 Crypto Spot Discovery Engine

Read-only Oracle discovery engine for crypto spot opportunities.

Consumes CDM-002 CryptoSpotSnapshot records and emits immutable
UniversalOpportunity-shaped crypto spot opportunities.

No trading, swapping, sizing, routing, or execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from .crypto_discovery_contract import (
    SCHEMA_VERSION as CONTRACT_SCHEMA_VERSION,
    CryptoDiscoveryCapability,
    CryptoDiscoveryEngineContract,
    CryptoDiscoveryFamily,
    CryptoDiscoveryHealth,
    CryptoDiscoveryRequest,
    CryptoDiscoveryResult,
    CryptoDiscoveryTelemetry,
)
from .crypto_spot_source_adapter import CryptoSpotSnapshot, CryptoSpotSourceAdapter


SCHEMA_VERSION = "CDM-003"
ENGINE_ID = "oracle.discovery.crypto_spot"
ENGINE_NAME = "Crypto Spot Discovery Engine"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_text(value: Any) -> str:
    if isinstance(value, Mapping):
        return "{" + ",".join(
            f"{str(k)}:{_stable_text(v)}" for k, v in sorted(value.items(), key=lambda x: str(x[0]))
        ) + "}"
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(_stable_text(v) for v in value) + "]"
    return repr(value)


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = sha256(_stable_text(payload).encode("utf-8")).hexdigest()[:20]
    return f"{prefix}.{digest}"


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    if isinstance(value, tuple):
        return tuple(_freeze(v) for v in value)
    return value


@dataclass(frozen=True)
class CryptoSpotOpportunity:
    opportunity_id: str
    schema_version: str
    symbol: str
    opportunity_type: str
    source_engine_id: str
    universal_market: Mapping[str, Any]
    side: str
    edge: float
    edge_percent: float
    confidence: float
    liquidity: float
    status: str
    explanation: Mapping[str, Any]
    telemetry: Mapping[str, Any]
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "opportunity_id": self.opportunity_id,
            "schema_version": self.schema_version,
            "symbol": self.symbol,
            "opportunity_type": self.opportunity_type,
            "source_engine_id": self.source_engine_id,
            "universal_market": dict(self.universal_market),
            "side": self.side,
            "edge": self.edge,
            "edge_percent": self.edge_percent,
            "confidence": self.confidence,
            "liquidity": self.liquidity,
            "status": self.status,
            "explanation": dict(self.explanation),
            "telemetry": dict(self.telemetry),
            "read_only": self.read_only,
        }


class CryptoSpotDiscoveryEngine(CryptoDiscoveryEngineContract):
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    engine_name = ENGINE_NAME
    read_only = True

    def __init__(
        self,
        source_snapshots: Optional[Sequence[CryptoSpotSnapshot]] = None,
        min_edge_percent: float = 0.01,
        min_liquidity: float = 1000.0,
    ) -> None:
        self.source_snapshots = tuple(source_snapshots or ())
        self.min_edge_percent = float(min_edge_percent)
        self.min_liquidity = float(min_liquidity)

    def capabilities(self) -> CryptoDiscoveryCapability:
        return CryptoDiscoveryCapability(
            schema_version=CONTRACT_SCHEMA_VERSION,
            engine_id=self.engine_id,
            family=CryptoDiscoveryFamily.CRYPTO_SPOT,
            source_name="crypto_spot_snapshot",
            supports_replay=True,
            deterministic=True,
            telemetry=True,
            read_only=True,
            metadata={
                "engine_schema_version": self.schema_version,
                "engine_name": self.engine_name,
                "produces": "UniversalOpportunity-shaped crypto spot opportunities",
                "execution": False,
            },
        )

    def health(self) -> CryptoDiscoveryHealth:
        return CryptoDiscoveryHealth(
            schema_version=CONTRACT_SCHEMA_VERSION,
            engine_id=self.engine_id,
            status="ok",
            ready=True,
            details={
                "engine_schema_version": self.schema_version,
                "read_only": True,
                "execution": False,
            },
        )

    def discover(self, request: CryptoDiscoveryRequest | None = None) -> CryptoDiscoveryResult:
        started_at = _utc_now_iso()
        snapshots = self._resolve_snapshots(request)

        opportunities = []
        rejected = 0

        for snapshot in snapshots:
            opportunity = self._build_opportunity(snapshot)
            if opportunity is None:
                rejected += 1
                continue
            opportunities.append(opportunity)

        opportunities = tuple(
            sorted(
                opportunities,
                key=lambda o: (-abs(o.edge_percent), -o.confidence, o.symbol, o.opportunity_id),
            )
        )

        request_id = request.request_id if request is not None else "crypto.spot.discovery.default"

        telemetry = CryptoDiscoveryTelemetry(
            schema_version=CONTRACT_SCHEMA_VERSION,
            engine_id=self.engine_id,
            request_id=request_id,
            started_at=started_at,
            completed_at=_utc_now_iso(),
            records_seen=len(snapshots),
            opportunities_emitted=len(opportunities),
            rejected_records=rejected,
            metadata={
                "engine_schema_version": self.schema_version,
                "min_edge_percent": self.min_edge_percent,
                "min_liquidity": self.min_liquidity,
                "deterministic_sort": True,
                "read_only": True,
            },
            read_only=True,
        )

        return CryptoDiscoveryResult(
            schema_version=CONTRACT_SCHEMA_VERSION,
            engine_id=self.engine_id,
            request_id=request_id,
            status="passed" if opportunities else "empty",
            opportunities=opportunities,
            telemetry=telemetry,
            health=self.health(),
            read_only=True,
        )

    def _resolve_snapshots(self, request: CryptoDiscoveryRequest | None) -> Tuple[CryptoSpotSnapshot, ...]:
        if request is None:
            return tuple(self.source_snapshots)

        records = None
        metadata = request.metadata or {}

        for key in ("snapshots", "crypto_spot_snapshots", "records", "raw_records"):
            if key in metadata:
                records = metadata[key]
                break

        if records is None:
            return tuple(self.source_snapshots)

        if all(isinstance(record, CryptoSpotSnapshot) for record in tuple(records)):
            return tuple(records)

        adapter = CryptoSpotSourceAdapter(source_name=request.source_name)
        return adapter.normalize_batch(tuple(records)).snapshots

    def _to_universal_market(self, snapshot: CryptoSpotSnapshot) -> Mapping[str, Any]:
        payload = {
            "schema_family": "UMM",
            "market_type": "crypto_spot",
            "symbol": snapshot.symbol,
            "base_asset": snapshot.base_asset,
            "quote_asset": snapshot.quote_asset,
            "exchange": snapshot.exchange,
            "status": snapshot.status,
            "prices": {
                "spot": snapshot.price,
                "fair_value": snapshot.fair_value,
                "bid": snapshot.bid,
                "ask": snapshot.ask,
                "spread": snapshot.spread,
            },
            "liquidity": snapshot.liquidity,
            "volume_24h": snapshot.volume_24h,
            "volatility": snapshot.volatility,
            "read_only": True,
        }
        return _freeze(payload)

    def _build_opportunity(self, snapshot: CryptoSpotSnapshot) -> Optional[CryptoSpotOpportunity]:
        if snapshot.status not in {"active", "open", "trading"}:
            return None

        if snapshot.price <= 0.0 or snapshot.fair_value <= 0.0:
            return None

        if snapshot.liquidity < self.min_liquidity:
            return None

        edge = round(snapshot.fair_value - snapshot.price, 8)
        edge_percent = round(edge / snapshot.price, 8)

        if abs(edge_percent) < self.min_edge_percent:
            return None

        side = "LONG_SPOT_OBSERVATION" if edge > 0 else "SHORT_SPOT_OBSERVATION"

        liquidity_score = min(snapshot.liquidity, 1_000_000.0) / 1_000_000.0
        volume_score = min(snapshot.volume_24h, 5_000_000.0) / 5_000_000.0
        edge_score = min(abs(edge_percent), 0.10) / 0.10
        confidence = round(min(1.0, edge_score * 0.65 + liquidity_score * 0.20 + volume_score * 0.15), 6)

        universal_market = self._to_universal_market(snapshot)

        identity_payload = {
            "symbol": snapshot.symbol,
            "exchange": snapshot.exchange,
            "side": side,
            "price": snapshot.price,
            "fair_value": snapshot.fair_value,
            "edge_percent": edge_percent,
        }

        explanation = MappingProxyType(
            {
                "summary": "Crypto spot price differs from read-only fair value estimate.",
                "symbol": snapshot.symbol,
                "exchange": snapshot.exchange,
                "side": side,
                "price": snapshot.price,
                "fair_value": snapshot.fair_value,
                "edge": edge,
                "edge_percent": edge_percent,
                "liquidity": snapshot.liquidity,
                "rules": [
                    "read_only_scan",
                    "minimum_liquidity_guardrail",
                    "minimum_edge_percent_guardrail",
                    "deterministic_opportunity_id",
                    "no_execution_authority",
                ],
            }
        )

        telemetry = MappingProxyType(
            {
                "schema_version": self.schema_version,
                "source_engine_id": self.engine_id,
                "symbol": snapshot.symbol,
                "exchange": snapshot.exchange,
                "created_at": _utc_now_iso(),
                "read_only": True,
                "execution": False,
            }
        )

        return CryptoSpotOpportunity(
            opportunity_id=_stable_id("uop.crypto_spot", identity_payload),
            schema_version="UOM-compatible/CDM-003",
            symbol=snapshot.symbol,
            opportunity_type="crypto_spot_value",
            source_engine_id=self.engine_id,
            universal_market=universal_market,
            side=side,
            edge=edge,
            edge_percent=edge_percent,
            confidence=confidence,
            liquidity=snapshot.liquidity,
            status="discovered",
            explanation=explanation,
            telemetry=telemetry,
            read_only=True,
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "ENGINE_NAME",
    "CryptoSpotOpportunity",
    "CryptoSpotDiscoveryEngine",
]
