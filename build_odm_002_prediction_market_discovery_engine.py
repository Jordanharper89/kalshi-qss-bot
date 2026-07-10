from pathlib import Path

ROOT = Path.cwd()

MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence" / "oracle_discovery_model"
MODULE_DIR.mkdir(parents=True, exist_ok=True)

ENGINE_FILE = MODULE_DIR / "prediction_market_discovery_engine.py"
TEST_FILE = ROOT / "test_odm_002_prediction_market_discovery_engine.py"
INIT_FILE = MODULE_DIR / "__init__.py"
ORACLE_INIT = ROOT / "qseries_v2" / "oracle_intelligence" / "__init__.py"

ENGINE_CODE = r'''"""
ODM-002 Prediction Market Discovery Engine

Read-only Oracle discovery engine for prediction-market opportunities.

This module intentionally avoids live network calls. Production adapters can pass
read-only market snapshots into the engine through DiscoveryRequest metadata or
direct source snapshots.

Oracle responsibilities:
- scan/read market snapshots
- normalize into canonical market-shaped records
- emit immutable opportunity-shaped records
- preserve telemetry, determinism, explainability, replayability

Oracle does NOT:
- place trades
- size positions
- execute orders
- manage exits
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


SCHEMA_VERSION = "ODM-002"
ENGINE_ID = "oracle.discovery.prediction_market"
ENGINE_NAME = "Prediction Market Discovery Engine"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_jsonish(value: Any) -> str:
    if isinstance(value, Mapping):
        items = sorted((str(k), _stable_jsonish(v)) for k, v in value.items())
        return "{" + ",".join(f"{k}:{v}" for k, v in items) + "}"
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(_stable_jsonish(v) for v in value) + "]"
    return repr(value)


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = sha256(_stable_jsonish(payload).encode("utf-8")).hexdigest()[:20]
    return f"{prefix}.{digest}"


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    if isinstance(value, tuple):
        return tuple(_freeze(v) for v in value)
    if isinstance(value, set):
        return tuple(sorted(_freeze(v) for v in value))
    return value


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _to_probability(value: Any, default: float = 0.0) -> float:
    number = _to_float(value, default)
    if number > 1.0:
        number = number / 100.0
    if number < 0.0:
        return 0.0
    if number > 1.0:
        return 1.0
    return number


def _read_attr(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, Mapping):
        return obj.get(key, default)
    return getattr(obj, key, default)


@dataclass(frozen=True)
class PredictionMarketSnapshot:
    market_id: str
    title: str
    platform: str = "prediction_market"
    category: str = "general"
    yes_price: float = 0.0
    no_price: float = 0.0
    fair_probability: float = 0.0
    liquidity: float = 0.0
    volume: float = 0.0
    close_time: Optional[str] = None
    status: str = "open"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def normalized(self) -> "PredictionMarketSnapshot":
        yes = _to_probability(self.yes_price)
        no = _to_probability(self.no_price)
        fair = _to_probability(self.fair_probability, yes)
        return PredictionMarketSnapshot(
            market_id=str(self.market_id),
            title=str(self.title),
            platform=str(self.platform or "prediction_market"),
            category=str(self.category or "general"),
            yes_price=yes,
            no_price=no,
            fair_probability=fair,
            liquidity=max(0.0, _to_float(self.liquidity)),
            volume=max(0.0, _to_float(self.volume)),
            close_time=self.close_time,
            status=str(self.status or "open").lower(),
            metadata=_freeze(dict(self.metadata or {})),
        )


@dataclass(frozen=True)
class DiscoveredPredictionMarketOpportunity:
    opportunity_id: str
    schema_version: str
    market_id: str
    opportunity_type: str
    source_engine_id: str
    universal_market: Mapping[str, Any]
    side: str
    edge: float
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
            "market_id": self.market_id,
            "opportunity_type": self.opportunity_type,
            "source_engine_id": self.source_engine_id,
            "universal_market": dict(self.universal_market),
            "side": self.side,
            "edge": self.edge,
            "confidence": self.confidence,
            "liquidity": self.liquidity,
            "status": self.status,
            "explanation": dict(self.explanation),
            "telemetry": dict(self.telemetry),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class PredictionMarketDiscoveryReport:
    schema_version: str
    engine_id: str
    status: str
    opportunities: Tuple[DiscoveredPredictionMarketOpportunity, ...]
    telemetry: Mapping[str, Any]
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "status": self.status,
            "opportunities": [o.to_dict() for o in self.opportunities],
            "telemetry": dict(self.telemetry),
            "read_only": self.read_only,
        }


class PredictionMarketDiscoveryEngine:
    """
    ODM-002 production discovery engine.

    Request handling is intentionally duck-typed so it remains compatible with
    the canonical ODM-001 DiscoveryRequest without creating adapter layers.
    """

    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    engine_name = ENGINE_NAME
    read_only = True

    def __init__(
        self,
        source_snapshots: Optional[Sequence[Any]] = None,
        min_edge: float = 0.02,
        min_liquidity: float = 1.0,
    ) -> None:
        self.source_snapshots = tuple(source_snapshots or ())
        self.min_edge = float(min_edge)
        self.min_liquidity = float(min_liquidity)

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "read_only": True,
            "market_family": "prediction_market",
            "produces": ["UniversalOpportunity"],
            "normalizes": ["UniversalMarket"],
            "supports_replay": True,
            "deterministic": True,
            "telemetry": True,
        }

    def health(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "status": "ok",
            "read_only": True,
            "ready": True,
            "checked_at": _utc_now_iso(),
        }

    def discover(self, request: Optional[Any] = None) -> PredictionMarketDiscoveryReport:
        started_at = _utc_now_iso()
        markets = self._resolve_markets(request)
        normalized = [self._normalize_market(m) for m in markets]

        opportunities: List[DiscoveredPredictionMarketOpportunity] = []
        rejected = 0

        for market in normalized:
            opportunity = self._build_opportunity(market)
            if opportunity is None:
                rejected += 1
                continue
            opportunities.append(opportunity)

        opportunities = sorted(
            opportunities,
            key=lambda o: (-o.edge, -o.confidence, o.market_id, o.opportunity_id),
        )

        telemetry = MappingProxyType(
            {
                "schema_version": self.schema_version,
                "engine_id": self.engine_id,
                "started_at": started_at,
                "completed_at": _utc_now_iso(),
                "markets_seen": len(markets),
                "markets_normalized": len(normalized),
                "opportunities_emitted": len(opportunities),
                "markets_rejected": rejected,
                "min_edge": self.min_edge,
                "min_liquidity": self.min_liquidity,
                "read_only": True,
                "deterministic_sort": True,
            }
        )

        status = "passed" if opportunities else "empty"
        return PredictionMarketDiscoveryReport(
            schema_version=self.schema_version,
            engine_id=self.engine_id,
            status=status,
            opportunities=tuple(opportunities),
            telemetry=telemetry,
            read_only=True,
        )

    def _resolve_markets(self, request: Optional[Any]) -> Tuple[Any, ...]:
        if request is None:
            return tuple(self.source_snapshots)

        direct = _read_attr(request, "markets", None)
        if direct is not None:
            return tuple(direct)

        metadata = _read_attr(request, "metadata", None)
        if isinstance(metadata, Mapping):
            for key in ("markets", "market_snapshots", "prediction_markets", "source_snapshots"):
                if key in metadata and metadata[key] is not None:
                    return tuple(metadata[key])

        payload = _read_attr(request, "payload", None)
        if isinstance(payload, Mapping):
            for key in ("markets", "market_snapshots", "prediction_markets", "source_snapshots"):
                if key in payload and payload[key] is not None:
                    return tuple(payload[key])

        return tuple(self.source_snapshots)

    def _normalize_market(self, raw: Any) -> PredictionMarketSnapshot:
        if isinstance(raw, PredictionMarketSnapshot):
            return raw.normalized()

        market_id = (
            _read_attr(raw, "market_id", None)
            or _read_attr(raw, "id", None)
            or _read_attr(raw, "ticker", None)
            or _stable_id("market", {"raw": _stable_jsonish(raw)})
        )

        title = (
            _read_attr(raw, "title", None)
            or _read_attr(raw, "question", None)
            or _read_attr(raw, "name", None)
            or str(market_id)
        )

        yes_price = (
            _read_attr(raw, "yes_price", None)
            if _read_attr(raw, "yes_price", None) is not None
            else _read_attr(raw, "price", 0.0)
        )

        fair_probability = (
            _read_attr(raw, "fair_probability", None)
            if _read_attr(raw, "fair_probability", None) is not None
            else _read_attr(raw, "model_probability", yes_price)
        )

        metadata: Dict[str, Any] = {}
        if isinstance(raw, Mapping):
            metadata = dict(raw.get("metadata") or {})
            metadata.update({k: v for k, v in raw.items() if k not in metadata and k not in {
                "market_id", "id", "ticker", "title", "question", "name", "yes_price",
                "no_price", "price", "fair_probability", "model_probability", "liquidity",
                "volume", "close_time", "status", "platform", "category"
            }})
        else:
            maybe_metadata = getattr(raw, "metadata", None)
            if isinstance(maybe_metadata, Mapping):
                metadata = dict(maybe_metadata)

        return PredictionMarketSnapshot(
            market_id=str(market_id),
            title=str(title),
            platform=str(_read_attr(raw, "platform", "prediction_market")),
            category=str(_read_attr(raw, "category", "general")),
            yes_price=_to_probability(yes_price),
            no_price=_to_probability(_read_attr(raw, "no_price", 0.0)),
            fair_probability=_to_probability(fair_probability),
            liquidity=max(0.0, _to_float(_read_attr(raw, "liquidity", 0.0))),
            volume=max(0.0, _to_float(_read_attr(raw, "volume", 0.0))),
            close_time=_read_attr(raw, "close_time", None),
            status=str(_read_attr(raw, "status", "open")).lower(),
            metadata=metadata,
        ).normalized()

    def _to_universal_market(self, market: PredictionMarketSnapshot) -> Mapping[str, Any]:
        market_payload = {
            "schema_family": "UMM",
            "market_type": "prediction_market",
            "market_id": market.market_id,
            "title": market.title,
            "platform": market.platform,
            "category": market.category,
            "status": market.status,
            "prices": {
                "yes": market.yes_price,
                "no": market.no_price,
                "fair_probability": market.fair_probability,
            },
            "liquidity": market.liquidity,
            "volume": market.volume,
            "close_time": market.close_time,
            "read_only": True,
        }
        return _freeze(market_payload)

    def _build_opportunity(
        self,
        market: PredictionMarketSnapshot,
    ) -> Optional[DiscoveredPredictionMarketOpportunity]:
        if market.status not in {"open", "active", "trading"}:
            return None

        if market.liquidity < self.min_liquidity:
            return None

        edge = round(market.fair_probability - market.yes_price, 6)
        if abs(edge) < self.min_edge:
            return None

        side = "YES" if edge > 0 else "NO"
        confidence = min(1.0, round(abs(edge) * 4.0 + min(market.liquidity, 10000.0) / 50000.0, 6))

        universal_market = self._to_universal_market(market)
        opportunity_payload = {
            "market_id": market.market_id,
            "side": side,
            "edge": edge,
            "fair_probability": market.fair_probability,
            "yes_price": market.yes_price,
            "liquidity": market.liquidity,
        }

        explanation = MappingProxyType(
            {
                "summary": "Prediction-market price differs from read-only fair probability estimate.",
                "side": side,
                "edge": edge,
                "yes_price": market.yes_price,
                "fair_probability": market.fair_probability,
                "liquidity": market.liquidity,
                "rules": [
                    "read_only_scan",
                    "liquidity_guardrail",
                    "minimum_edge_guardrail",
                    "deterministic_opportunity_id",
                ],
            }
        )

        telemetry = MappingProxyType(
            {
                "schema_version": self.schema_version,
                "source_engine_id": self.engine_id,
                "market_id": market.market_id,
                "created_at": _utc_now_iso(),
                "read_only": True,
            }
        )

        return DiscoveredPredictionMarketOpportunity(
            opportunity_id=_stable_id("uop.prediction", opportunity_payload),
            schema_version="UOM-compatible/ODM-002",
            market_id=market.market_id,
            opportunity_type="prediction_market_value",
            source_engine_id=self.engine_id,
            universal_market=universal_market,
            side=side,
            edge=edge,
            confidence=confidence,
            liquidity=market.liquidity,
            status="discovered",
            explanation=explanation,
            telemetry=telemetry,
            read_only=True,
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "ENGINE_NAME",
    "PredictionMarketSnapshot",
    "DiscoveredPredictionMarketOpportunity",
    "PredictionMarketDiscoveryReport",
    "PredictionMarketDiscoveryEngine",
]
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.oracle_discovery_model.prediction_market_discovery_engine import (
    PredictionMarketDiscoveryEngine,
)


def test_odm_002_prediction_market_discovery_engine():
    markets = [
        {
            "market_id": "KX.TEST.YES",
            "title": "Will test market resolve yes?",
            "platform": "kalshi",
            "category": "test",
            "yes_price": 0.41,
            "fair_probability": 0.52,
            "liquidity": 1500,
            "volume": 20000,
            "status": "open",
        },
        {
            "market_id": "KX.TEST.NO",
            "title": "Will second test market resolve yes?",
            "platform": "kalshi",
            "category": "test",
            "yes_price": 0.74,
            "fair_probability": 0.63,
            "liquidity": 1300,
            "volume": 15000,
            "status": "open",
        },
        {
            "market_id": "KX.TEST.REJECT",
            "title": "Rejected low edge market",
            "platform": "kalshi",
            "category": "test",
            "yes_price": 0.50,
            "fair_probability": 0.505,
            "liquidity": 1300,
            "status": "open",
        },
    ]

    engine = PredictionMarketDiscoveryEngine(source_snapshots=markets, min_edge=0.02, min_liquidity=100)
    caps = engine.capabilities()
    health = engine.health()
    report_1 = engine.discover()
    report_2 = engine.discover()

    assert caps["read_only"] is True
    assert caps["deterministic"] is True
    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert report_1.schema_version == "ODM-002"
    assert report_1.engine_id == "oracle.discovery.prediction_market"
    assert report_1.read_only is True
    assert report_1.status == "passed"
    assert len(report_1.opportunities) == 2

    ids_1 = [o.opportunity_id for o in report_1.opportunities]
    ids_2 = [o.opportunity_id for o in report_2.opportunities]
    assert ids_1 == ids_2

    first = report_1.opportunities[0]
    assert first.read_only is True
    assert first.universal_market["market_type"] == "prediction_market"
    assert first.universal_market["read_only"] is True
    assert first.opportunity_type == "prediction_market_value"
    assert first.source_engine_id == "oracle.discovery.prediction_market"
    assert first.status == "discovered"
    assert abs(first.edge) >= 0.02
    assert first.confidence > 0
    assert "rules" in first.explanation

    sides = sorted([o.side for o in report_1.opportunities])
    assert sides == ["NO", "YES"]

    d = report_1.to_dict()
    assert d["schema_version"] == "ODM-002"
    assert d["read_only"] is True
    assert d["telemetry"]["markets_seen"] == 3
    assert d["telemetry"]["opportunities_emitted"] == 2
    assert d["telemetry"]["markets_rejected"] == 1

    try:
        first.universal_market["read_only"] = False
        raise AssertionError("universal_market should be immutable")
    except TypeError:
        pass

    print("[PASS] ODM-002 Prediction Market Discovery Engine")
    print(
        {
            "schema_version": d["schema_version"],
            "engine_id": d["engine_id"],
            "status": d["status"],
            "opportunities": len(d["opportunities"]),
            "read_only": d["read_only"],
        }
    )


if __name__ == "__main__":
    test_odm_002_prediction_market_discovery_engine()
'''

INIT_EXPORT = '''
try:
    from .prediction_market_discovery_engine import (
        PredictionMarketDiscoveryEngine,
        PredictionMarketSnapshot,
        PredictionMarketDiscoveryReport,
        DiscoveredPredictionMarketOpportunity,
    )
except Exception:
    pass
'''

ENGINE_FILE.write_text(ENGINE_CODE, encoding="utf-8")
TEST_FILE.write_text(TEST_CODE, encoding="utf-8")

existing_init = INIT_FILE.read_text(encoding="utf-8") if INIT_FILE.exists() else ""
if "PredictionMarketDiscoveryEngine" not in existing_init:
    INIT_FILE.write_text(existing_init.rstrip() + "\n" + INIT_EXPORT.lstrip(), encoding="utf-8")

if ORACLE_INIT.exists():
    existing_oracle_init = ORACLE_INIT.read_text(encoding="utf-8")
else:
    existing_oracle_init = ""

oracle_export = '''
try:
    from .oracle_discovery_model.prediction_market_discovery_engine import PredictionMarketDiscoveryEngine
except Exception:
    pass
'''

if "PredictionMarketDiscoveryEngine" not in existing_oracle_init:
    ORACLE_INIT.write_text(existing_oracle_init.rstrip() + "\n" + oracle_export.lstrip(), encoding="utf-8")

print("========================================")
print(" ODM-002 INSTALLER")
print(" Prediction Market Discovery Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE_FILE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT_FILE}")
print(f"[OK] Updated {ORACLE_INIT}")
print()
print("[DONE] ODM-002 installed")
print()
print("Run:")
print("py test_odm_002_prediction_market_discovery_engine.py")