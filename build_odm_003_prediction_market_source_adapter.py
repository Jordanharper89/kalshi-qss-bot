from pathlib import Path

ROOT = Path.cwd()

MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence" / "oracle_discovery_model"
MODULE_DIR.mkdir(parents=True, exist_ok=True)

ADAPTER_FILE = MODULE_DIR / "prediction_market_source_adapter.py"
TEST_FILE = ROOT / "test_odm_003_prediction_market_source_adapter.py"
INIT_FILE = MODULE_DIR / "__init__.py"

ADAPTER_CODE = r'''"""
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
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.oracle_discovery_model.prediction_market_source_adapter import (
    PredictionMarketSourceAdapter,
)


def test_odm_003_prediction_market_source_adapter():
    raw_markets = [
        {
            "ticker": "KX.Z",
            "question": "Will Z happen?",
            "platform": "kalshi",
            "category": "macro",
            "price": 42,
            "model_probability": 55,
            "liquidity": 2500,
            "volume": 9000,
            "status": "open",
        },
        {
            "ticker": "KX.A",
            "question": "Will A happen?",
            "platform": "kalshi",
            "category": "macro",
            "price": 71,
            "model_probability": 61,
            "liquidity": 3000,
            "volume": 12000,
            "status": "open",
        },
    ]

    adapter = PredictionMarketSourceAdapter(source_name="kalshi_snapshot")
    caps = adapter.capabilities()
    health = adapter.health()
    batch_1 = adapter.normalize_batch(raw_markets)
    batch_2 = adapter.normalize_batch(list(reversed(raw_markets)))

    assert caps["read_only"] is True
    assert caps["deterministic"] is True
    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert batch_1.schema_version == "ODM-003"
    assert batch_1.adapter_id == "oracle.discovery.source.prediction_market"
    assert batch_1.read_only is True
    assert len(batch_1.snapshots) == 2

    ids_1 = [s.market_id for s in batch_1.snapshots]
    ids_2 = [s.market_id for s in batch_2.snapshots]
    assert ids_1 == ids_2
    assert ids_1 == ["KX.A", "KX.Z"]

    first = batch_1.snapshots[0]
    assert first.yes_price == 0.71
    assert first.fair_probability == 0.61
    assert first.metadata["source_name"] == "kalshi_snapshot"

    report = adapter.discover(raw_markets, min_edge=0.02, min_liquidity=100)
    assert report.read_only is True
    assert report.status == "passed"
    assert len(report.opportunities) == 2

    sides = sorted([o.side for o in report.opportunities])
    assert sides == ["NO", "YES"]

    d = batch_1.to_dict()
    assert d["schema_version"] == "ODM-003"
    assert d["read_only"] is True
    assert d["telemetry"]["raw_records_seen"] == 2
    assert d["telemetry"]["snapshots_emitted"] == 2

    print("[PASS] ODM-003 Prediction Market Source Adapter")
    print(
        {
            "schema_version": d["schema_version"],
            "adapter_id": d["adapter_id"],
            "snapshots": len(d["snapshots"]),
            "read_only": d["read_only"],
            "discovered_opportunities": len(report.opportunities),
        }
    )


if __name__ == "__main__":
    test_odm_003_prediction_market_source_adapter()
'''

INIT_EXPORT = '''
try:
    from .prediction_market_source_adapter import (
        PredictionMarketSourceAdapter,
        PredictionMarketSourceBatch,
    )
except Exception:
    pass
'''

ADAPTER_FILE.write_text(ADAPTER_CODE, encoding="utf-8")
TEST_FILE.write_text(TEST_CODE, encoding="utf-8")

existing_init = INIT_FILE.read_text(encoding="utf-8") if INIT_FILE.exists() else ""
if "PredictionMarketSourceAdapter" not in existing_init:
    INIT_FILE.write_text(existing_init.rstrip() + "\n" + INIT_EXPORT.lstrip(), encoding="utf-8")

print("========================================")
print(" ODM-003 INSTALLER")
print(" Prediction Market Source Adapter")
print("========================================")
print(f"[OK] Wrote {ADAPTER_FILE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT_FILE}")
print()
print("[DONE] ODM-003 installed")
print()
print("Run:")
print("py test_odm_003_prediction_market_source_adapter.py")