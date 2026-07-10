from pathlib import Path

ROOT = Path.cwd()

MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence" / "arbitrage_discovery_model"
MODULE_DIR.mkdir(parents=True, exist_ok=True)

ENGINE_FILE = MODULE_DIR / "cross_venue_arbitrage_discovery_engine.py"
TEST_FILE = ROOT / "test_adm_003_cross_venue_arbitrage_discovery_engine.py"
INIT_FILE = MODULE_DIR / "__init__.py"

ENGINE_CODE = r'''"""
ADM-003 Cross-Venue Arbitrage Discovery Engine

Read-only Oracle discovery engine for cross-venue arbitrage gaps.

Consumes ADM-002 CrossVenueQuoteSnapshot records and emits immutable
UniversalOpportunity-shaped arbitrage opportunities.

No trading, routing, order placement, sizing, leg execution, or exits.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from .arbitrage_discovery_contract import (
    SCHEMA_VERSION as CONTRACT_SCHEMA_VERSION,
    ArbitrageDiscoveryCapability,
    ArbitrageDiscoveryEngineContract,
    ArbitrageDiscoveryFamily,
    ArbitrageDiscoveryHealth,
    ArbitrageDiscoveryRequest,
    ArbitrageDiscoveryResult,
    ArbitrageDiscoveryTelemetry,
)
from .cross_venue_arbitrage_source_adapter import (
    CrossVenueArbitrageSourceAdapter,
    CrossVenueQuoteSnapshot,
)


SCHEMA_VERSION = "ADM-003"
ENGINE_ID = "oracle.discovery.cross_venue_arbitrage"
ENGINE_NAME = "Cross-Venue Arbitrage Discovery Engine"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_text(value: Any) -> str:
    if isinstance(value, Mapping):
        return "{" + ",".join(
            f"{str(k)}:{_stable_text(v)}"
            for k, v in sorted(value.items(), key=lambda x: str(x[0]))
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
class CrossVenueArbitrageOpportunity:
    opportunity_id: str
    schema_version: str
    symbol: str
    opportunity_type: str
    source_engine_id: str
    buy_venue: str
    sell_venue: str
    buy_price: float
    sell_price: float
    gross_edge: float
    gross_edge_percent: float
    estimated_fee_percent: float
    net_edge: float
    net_edge_percent: float
    confidence: float
    liquidity: float
    universal_market: Mapping[str, Any]
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
            "buy_venue": self.buy_venue,
            "sell_venue": self.sell_venue,
            "buy_price": self.buy_price,
            "sell_price": self.sell_price,
            "gross_edge": self.gross_edge,
            "gross_edge_percent": self.gross_edge_percent,
            "estimated_fee_percent": self.estimated_fee_percent,
            "net_edge": self.net_edge,
            "net_edge_percent": self.net_edge_percent,
            "confidence": self.confidence,
            "liquidity": self.liquidity,
            "universal_market": dict(self.universal_market),
            "status": self.status,
            "explanation": dict(self.explanation),
            "telemetry": dict(self.telemetry),
            "read_only": self.read_only,
        }


class CrossVenueArbitrageDiscoveryEngine(ArbitrageDiscoveryEngineContract):
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    engine_name = ENGINE_NAME
    read_only = True

    def __init__(
        self,
        source_snapshots: Optional[Sequence[CrossVenueQuoteSnapshot]] = None,
        min_net_edge_percent: float = 0.001,
        min_liquidity: float = 1000.0,
    ) -> None:
        self.source_snapshots = tuple(source_snapshots or ())
        self.min_net_edge_percent = float(min_net_edge_percent)
        self.min_liquidity = float(min_liquidity)

    def capabilities(self) -> ArbitrageDiscoveryCapability:
        return ArbitrageDiscoveryCapability(
            schema_version=CONTRACT_SCHEMA_VERSION,
            engine_id=self.engine_id,
            family=ArbitrageDiscoveryFamily.CROSS_EXCHANGE,
            source_name="cross_venue_quote_snapshot",
            supports_replay=True,
            deterministic=True,
            telemetry=True,
            read_only=True,
            metadata={
                "engine_schema_version": self.schema_version,
                "engine_name": self.engine_name,
                "produces": "UniversalOpportunity-shaped cross-venue arbitrage opportunities",
                "execution": False,
                "order_allowed": False,
                "route_allowed": False,
                "leg_execution_allowed": False,
            },
        )

    def health(self) -> ArbitrageDiscoveryHealth:
        return ArbitrageDiscoveryHealth(
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

    def discover(self, request: ArbitrageDiscoveryRequest | None = None) -> ArbitrageDiscoveryResult:
        started_at = _utc_now_iso()
        snapshots = self._resolve_snapshots(request)
        grouped = self._group_by_symbol(snapshots)

        opportunities = []
        pairs_evaluated = 0
        rejected = 0

        for symbol, quotes in grouped.items():
            for buy_quote in quotes:
                for sell_quote in quotes:
                    if buy_quote.venue == sell_quote.venue:
                        continue
                    pairs_evaluated += 1
                    opportunity = self._build_opportunity(symbol, buy_quote, sell_quote)
                    if opportunity is None:
                        rejected += 1
                        continue
                    opportunities.append(opportunity)

        opportunities = tuple(
            sorted(
                opportunities,
                key=lambda o: (-o.net_edge_percent, -o.confidence, o.symbol, o.buy_venue, o.sell_venue),
            )
        )

        request_id = request.request_id if request is not None else "arbitrage.discovery.default"

        telemetry = ArbitrageDiscoveryTelemetry(
            schema_version=CONTRACT_SCHEMA_VERSION,
            engine_id=self.engine_id,
            request_id=request_id,
            started_at=started_at,
            completed_at=_utc_now_iso(),
            records_seen=len(snapshots),
            pairs_evaluated=pairs_evaluated,
            opportunities_emitted=len(opportunities),
            rejected_records=rejected,
            metadata={
                "engine_schema_version": self.schema_version,
                "min_net_edge_percent": self.min_net_edge_percent,
                "min_liquidity": self.min_liquidity,
                "deterministic_sort": True,
                "read_only": True,
                "execution_allowed": False,
            },
            read_only=True,
        )

        return ArbitrageDiscoveryResult(
            schema_version=CONTRACT_SCHEMA_VERSION,
            engine_id=self.engine_id,
            request_id=request_id,
            status="passed" if opportunities else "empty",
            opportunities=opportunities,
            telemetry=telemetry,
            health=self.health(),
            read_only=True,
        )

    def _resolve_snapshots(
        self,
        request: ArbitrageDiscoveryRequest | None,
    ) -> Tuple[CrossVenueQuoteSnapshot, ...]:
        if request is None:
            return tuple(self.source_snapshots)

        metadata = request.metadata or {}
        records = None
        for key in ("snapshots", "quote_snapshots", "cross_venue_quotes", "records", "raw_records"):
            if key in metadata:
                records = metadata[key]
                break

        if records is None:
            return tuple(self.source_snapshots)

        record_tuple = tuple(records)
        if all(isinstance(record, CrossVenueQuoteSnapshot) for record in record_tuple):
            return record_tuple

        adapter = CrossVenueArbitrageSourceAdapter(source_name=request.source_name)
        return adapter.normalize_batch(record_tuple).snapshots

    def _group_by_symbol(
        self,
        snapshots: Sequence[CrossVenueQuoteSnapshot],
    ) -> Dict[str, Tuple[CrossVenueQuoteSnapshot, ...]]:
        grouped: Dict[str, list] = {}
        for snapshot in snapshots:
            if snapshot.status not in {"active", "open", "trading"}:
                continue
            grouped.setdefault(snapshot.symbol, []).append(snapshot)

        return {
            symbol: tuple(sorted(quotes, key=lambda q: (q.venue, q.quote_id)))
            for symbol, quotes in sorted(grouped.items())
            if len(quotes) >= 2
        }

    def _to_universal_market(
        self,
        symbol: str,
        buy_quote: CrossVenueQuoteSnapshot,
        sell_quote: CrossVenueQuoteSnapshot,
    ) -> Mapping[str, Any]:
        payload = {
            "schema_family": "UMM",
            "market_type": "cross_venue_arbitrage",
            "symbol": symbol,
            "base_asset": buy_quote.base_asset,
            "quote_asset": buy_quote.quote_asset,
            "buy_venue": buy_quote.venue,
            "sell_venue": sell_quote.venue,
            "buy_quote": buy_quote.to_dict(),
            "sell_quote": sell_quote.to_dict(),
            "read_only": True,
            "execution_allowed": False,
        }
        return _freeze(payload)

    def _build_opportunity(
        self,
        symbol: str,
        buy_quote: CrossVenueQuoteSnapshot,
        sell_quote: CrossVenueQuoteSnapshot,
    ) -> Optional[CrossVenueArbitrageOpportunity]:
        if buy_quote.ask <= 0.0 or sell_quote.bid <= 0.0:
            return None

        if buy_quote.ask >= sell_quote.bid:
            return None

        liquidity = min(buy_quote.liquidity, sell_quote.liquidity)
        if liquidity < self.min_liquidity:
            return None

        gross_edge = round(sell_quote.bid - buy_quote.ask, 12)
        gross_edge_percent = round(gross_edge / buy_quote.ask, 12)

        estimated_fee_percent = round((buy_quote.fee_bps + sell_quote.fee_bps) / 10000.0, 12)
        net_edge_percent = round(gross_edge_percent - estimated_fee_percent, 12)
        net_edge = round(buy_quote.ask * net_edge_percent, 12)

        if net_edge_percent < self.min_net_edge_percent:
            return None

        liquidity_score = min(liquidity, 1_000_000.0) / 1_000_000.0
        volume_score = min(min(buy_quote.volume_24h, sell_quote.volume_24h), 5_000_000.0) / 5_000_000.0
        edge_score = min(net_edge_percent, 0.02) / 0.02
        latency_penalty = min((buy_quote.latency_ms + sell_quote.latency_ms) / 2000.0, 0.25)
        confidence = round(max(0.0, min(1.0, edge_score * 0.60 + liquidity_score * 0.25 + volume_score * 0.15 - latency_penalty)), 6)

        identity_payload = {
            "symbol": symbol,
            "buy_venue": buy_quote.venue,
            "sell_venue": sell_quote.venue,
            "buy_price": buy_quote.ask,
            "sell_price": sell_quote.bid,
            "net_edge_percent": net_edge_percent,
        }

        explanation = MappingProxyType(
            {
                "summary": "Cross-venue quote spread creates a read-only arbitrage observation.",
                "symbol": symbol,
                "buy_venue": buy_quote.venue,
                "sell_venue": sell_quote.venue,
                "buy_price": buy_quote.ask,
                "sell_price": sell_quote.bid,
                "gross_edge": gross_edge,
                "gross_edge_percent": gross_edge_percent,
                "estimated_fee_percent": estimated_fee_percent,
                "net_edge": net_edge,
                "net_edge_percent": net_edge_percent,
                "liquidity": liquidity,
                "rules": [
                    "read_only_scan",
                    "ask_below_bid_guardrail",
                    "minimum_liquidity_guardrail",
                    "minimum_net_edge_guardrail",
                    "deterministic_opportunity_id",
                    "no_execution_authority",
                ],
            }
        )

        telemetry = MappingProxyType(
            {
                "schema_version": self.schema_version,
                "source_engine_id": self.engine_id,
                "symbol": symbol,
                "buy_venue": buy_quote.venue,
                "sell_venue": sell_quote.venue,
                "created_at": _utc_now_iso(),
                "read_only": True,
                "execution_allowed": False,
            }
        )

        return CrossVenueArbitrageOpportunity(
            opportunity_id=_stable_id("uop.arbitrage.cross_venue", identity_payload),
            schema_version="UOM-compatible/ADM-003",
            symbol=symbol,
            opportunity_type="cross_venue_arbitrage",
            source_engine_id=self.engine_id,
            buy_venue=buy_quote.venue,
            sell_venue=sell_quote.venue,
            buy_price=buy_quote.ask,
            sell_price=sell_quote.bid,
            gross_edge=gross_edge,
            gross_edge_percent=gross_edge_percent,
            estimated_fee_percent=estimated_fee_percent,
            net_edge=net_edge,
            net_edge_percent=net_edge_percent,
            confidence=confidence,
            liquidity=liquidity,
            universal_market=self._to_universal_market(symbol, buy_quote, sell_quote),
            status="discovered",
            explanation=explanation,
            telemetry=telemetry,
            read_only=True,
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "ENGINE_NAME",
    "CrossVenueArbitrageOpportunity",
    "CrossVenueArbitrageDiscoveryEngine",
]
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.arbitrage_discovery_model.arbitrage_discovery_contract import (
    ArbitrageDiscoveryFamily,
    ArbitrageDiscoveryRequest,
)
from qseries_v2.oracle_intelligence.arbitrage_discovery_model.cross_venue_arbitrage_discovery_engine import (
    CrossVenueArbitrageDiscoveryEngine,
)


def test_adm_003_cross_venue_arbitrage_discovery_engine():
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

    request = ArbitrageDiscoveryRequest(
        request_id="adm003.test.request",
        family=ArbitrageDiscoveryFamily.CROSS_EXCHANGE,
        source_name="adm_003_test_feed",
        symbols=("BTC-USD", "ETH-USD"),
        venues=("coinbase", "kraken"),
        metadata={"raw_records": raw_records},
    )

    engine = CrossVenueArbitrageDiscoveryEngine(
        min_net_edge_percent=0.001,
        min_liquidity=1000,
    )

    caps = engine.capabilities()
    health = engine.health()
    report_1 = engine.discover(request)
    report_2 = engine.discover(request)

    assert engine.read_only is True
    assert caps.read_only is True
    assert caps.deterministic is True
    assert caps.telemetry is True
    assert health.status == "ok"
    assert health.read_only is True

    assert report_1.schema_version == "ADM-001"
    assert report_1.engine_id == "oracle.discovery.cross_venue_arbitrage"
    assert report_1.status == "passed"
    assert report_1.read_only is True
    assert len(report_1.opportunities) == 1

    ids_1 = [o.opportunity_id for o in report_1.opportunities]
    ids_2 = [o.opportunity_id for o in report_2.opportunities]
    assert ids_1 == ids_2

    opp = report_1.opportunities[0]
    assert opp.read_only is True
    assert opp.symbol == "BTC-USD"
    assert opp.opportunity_type == "cross_venue_arbitrage"
    assert opp.source_engine_id == "oracle.discovery.cross_venue_arbitrage"
    assert opp.buy_venue == "coinbase"
    assert opp.sell_venue == "kraken"
    assert opp.buy_price == 65020.0
    assert opp.sell_price == 65300.0
    assert opp.gross_edge > 0
    assert opp.net_edge_percent >= 0.001
    assert 0.0 <= opp.confidence <= 1.0
    assert opp.status == "discovered"
    assert opp.universal_market["market_type"] == "cross_venue_arbitrage"
    assert opp.universal_market["read_only"] is True
    assert opp.universal_market["execution_allowed"] is False
    assert opp.explanation["rules"]

    try:
        opp.universal_market["execution_allowed"] = True
        raise AssertionError("universal_market should be immutable")
    except TypeError:
        pass

    d = report_1.to_dict()
    assert d["read_only"] is True
    assert d["telemetry"]["records_seen"] == 3
    assert d["telemetry"]["pairs_evaluated"] == 2
    assert d["telemetry"]["opportunities_emitted"] == 1
    assert d["telemetry"]["read_only"] is True

    print("[PASS] ADM-003 Cross-Venue Arbitrage Discovery Engine")
    print(
        {
            "schema_version": "ADM-003",
            "engine_id": d["engine_id"],
            "status": d["status"],
            "opportunities": len(d["opportunities"]),
            "read_only": d["read_only"],
        }
    )


if __name__ == "__main__":
    test_adm_003_cross_venue_arbitrage_discovery_engine()
'''

INIT_EXPORT = '''
try:
    from .cross_venue_arbitrage_discovery_engine import (
        CrossVenueArbitrageDiscoveryEngine,
        CrossVenueArbitrageOpportunity,
    )
except Exception:
    pass
'''

ENGINE_FILE.write_text(ENGINE_CODE, encoding="utf-8")
TEST_FILE.write_text(TEST_CODE, encoding="utf-8")

existing_init = INIT_FILE.read_text(encoding="utf-8") if INIT_FILE.exists() else ""
if "CrossVenueArbitrageDiscoveryEngine" not in existing_init:
    INIT_FILE.write_text(existing_init.rstrip() + "\n" + INIT_EXPORT.lstrip(), encoding="utf-8")

print("========================================")
print(" ADM-003 INSTALLER")
print(" Cross-Venue Arbitrage Discovery Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE_FILE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT_FILE}")
print()
print("[DONE] ADM-003 installed")
print()
print("Run:")
print("py test_adm_003_cross_venue_arbitrage_discovery_engine.py")