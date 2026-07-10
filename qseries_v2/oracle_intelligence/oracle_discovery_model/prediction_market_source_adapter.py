"""
ODM-003 Prediction Market Source Adapter

Canonical read-only source adapter for prediction-market discovery.

Purpose:
- Accept raw prediction-market records from any upstream provider.
- Normalize them into PredictionMarketSnapshot objects.
- Preserve deterministic ordering, replayability, telemetry, and read-only behavior.
- Feed ODM-002 PredictionMarketDiscoveryEngine without execution logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple

from .prediction_market_discovery_engine import (
    PredictionMarketDiscoveryEngine,
    PredictionMarketSnapshot,
)


SCHEMA_VERSION = "ODM-003"
ADAPTER_ID = "oracle.discovery.source.prediction_market"
ADAPTER_NAME = "Prediction Market Source Adapter"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_text(value: Any) -> str:
    if isinstance(value, Mapping):
        return "{" + ",".join(f"{k}:{_stable_text(v)}" for k, v in sorted(value.items())) + "}"
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


def _read(raw: Any, key: str, default: Any = None) -> Any:
    if isinstance(raw, Mapping):
        return raw.get(key, default)
    return getattr(raw, key, default)


def _float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _prob(value: Any, default: float = 0.0) -> float:
    number = _float(value, default)
    if number > 1.0:
        number = number / 100.0
    return max(0.0, min(1.0, number))


@dataclass(frozen=True)
class PredictionMarketSourceBatch:
    schema_version: str
    adapter_id: str
    source_name: str
    snapshots: Tuple[PredictionMarketSnapshot, ...]
    telemetry: Mapping[str, Any]
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "adapter_id": self.adapter_id,
            "source_name": self.source_name,
            "snapshots": [s.__dict__ for s in self.snapshots],
            "telemetry": dict(self.telemetry),
            "read_only": self.read_only,
        }


class PredictionMarketSourceAdapter:
    schema_version = SCHEMA_VERSION
    adapter_id = ADAPTER_ID
    adapter_name = ADAPTER_NAME
    read_only = True

    def __init__(self, source_name: str = "generic_prediction_market") -> None:
        self.source_name = str(source_name or "generic_prediction_market")

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "adapter_id": self.adapter_id,
            "adapter_name": self.adapter_name,
            "source_name": self.source_name,
            "read_only": True,
            "normalizes_to": "PredictionMarketSnapshot",
            "compatible_engine": "oracle.discovery.prediction_market",
            "deterministic": True,
            "supports_replay": True,
            "telemetry": True,
        }

    def health(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "adapter_id": self.adapter_id,
            "source_name": self.source_name,
            "status": "ok",
            "ready": True,
            "read_only": True,
            "checked_at": _utc_now_iso(),
        }

    def normalize_batch(self, raw_markets: Sequence[Any]) -> PredictionMarketSourceBatch:
        started_at = _utc_now_iso()

        snapshots = tuple(
            sorted(
                (self.normalize_market(raw) for raw in tuple(raw_markets or ())),
                key=lambda s: (s.market_id, s.title),
            )
        )

        telemetry = MappingProxyType(
            {
                "schema_version": self.schema_version,
                "adapter_id": self.adapter_id,
                "source_name": self.source_name,
                "started_at": started_at,
                "completed_at": _utc_now_iso(),
                "raw_records_seen": len(tuple(raw_markets or ())),
                "snapshots_emitted": len(snapshots),
                "read_only": True,
                "deterministic_sort": True,
            }
        )

        return PredictionMarketSourceBatch(
            schema_version=self.schema_version,
            adapter_id=self.adapter_id,
            source_name=self.source_name,
            snapshots=snapshots,
            telemetry=telemetry,
            read_only=True,
        )

    def normalize_market(self, raw: Any) -> PredictionMarketSnapshot:
        market_id = (
            _read(raw, "market_id", None)
            or _read(raw, "id", None)
            or _read(raw, "ticker", None)
            or _stable_id("market", {"source": self.source_name, "raw": _stable_text(raw)})
        )

        title = (
            _read(raw, "title", None)
            or _read(raw, "question", None)
            or _read(raw, "name", None)
            or str(market_id)
        )

        yes_price = _read(raw, "yes_price", None)
        if yes_price is None:
            yes_price = _read(raw, "price", 0.0)

        fair_probability = _read(raw, "fair_probability", None)
        if fair_probability is None:
            fair_probability = _read(raw, "model_probability", yes_price)

        metadata = {}
        raw_metadata = _read(raw, "metadata", None)
        if isinstance(raw_metadata, Mapping):
            metadata.update(dict(raw_metadata))

        metadata["source_name"] = self.source_name
        metadata["adapter_id"] = self.adapter_id

        return PredictionMarketSnapshot(
            market_id=str(market_id),
            title=str(title),
            platform=str(_read(raw, "platform", self.source_name)),
            category=str(_read(raw, "category", "general")),
            yes_price=_prob(yes_price),
            no_price=_prob(_read(raw, "no_price", 0.0)),
            fair_probability=_prob(fair_probability),
            liquidity=max(0.0, _float(_read(raw, "liquidity", 0.0))),
            volume=max(0.0, _float(_read(raw, "volume", 0.0))),
            close_time=_read(raw, "close_time", None),
            status=str(_read(raw, "status", "open")).lower(),
            metadata=_freeze(metadata),
        ).normalized()

    def build_engine(
        self,
        raw_markets: Sequence[Any],
        min_edge: float = 0.02,
        min_liquidity: float = 1.0,
    ) -> PredictionMarketDiscoveryEngine:
        batch = self.normalize_batch(raw_markets)
        return PredictionMarketDiscoveryEngine(
            source_snapshots=batch.snapshots,
            min_edge=min_edge,
            min_liquidity=min_liquidity,
        )

    def discover(
        self,
        raw_markets: Sequence[Any],
        min_edge: float = 0.02,
        min_liquidity: float = 1.0,
    ):
        engine = self.build_engine(
            raw_markets=raw_markets,
            min_edge=min_edge,
            min_liquidity=min_liquidity,
        )
        return engine.discover()


__all__ = [
    "SCHEMA_VERSION",
    "ADAPTER_ID",
    "ADAPTER_NAME",
    "PredictionMarketSourceBatch",
    "PredictionMarketSourceAdapter",
]
