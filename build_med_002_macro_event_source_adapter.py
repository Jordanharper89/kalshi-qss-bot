from pathlib import Path

ROOT = Path.cwd()
MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence" / "macro_event_discovery_model"
MODULE_DIR.mkdir(parents=True, exist_ok=True)

ADAPTER_FILE = MODULE_DIR / "macro_event_source_adapter.py"
TEST_FILE = ROOT / "test_med_002_macro_event_source_adapter.py"
INIT_FILE = MODULE_DIR / "__init__.py"

ADAPTER_CODE = r'''
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

SCHEMA_VERSION = "MED-002"
ADAPTER_ID = "oracle.discovery.source.macro_event"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _freeze(v: Any) -> Any:
    if isinstance(v, Mapping):
        return MappingProxyType({str(k): _freeze(x) for k, x in v.items()})
    if isinstance(v, list):
        return tuple(_freeze(x) for x in v)
    if isinstance(v, tuple):
        return tuple(_freeze(x) for x in v)
    return v


def _read(raw: Any, key: str, default: Any = None) -> Any:
    return raw.get(key, default) if isinstance(raw, Mapping) else getattr(raw, key, default)


def _stable_text(v: Any) -> str:
    if isinstance(v, Mapping):
        return "{" + ",".join(f"{k}:{_stable_text(x)}" for k, x in sorted(v.items())) + "}"
    if isinstance(v, (list, tuple)):
        return "[" + ",".join(_stable_text(x) for x in v) + "]"
    return repr(v)


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    return prefix + "." + sha256(_stable_text(payload).encode("utf-8")).hexdigest()[:20]


@dataclass(frozen=True)
class MacroEventSnapshot:
    event_id: str
    title: str
    family: str
    region: str
    country: str
    currency: str
    impact: str
    scheduled_at: str
    source_name: str
    actual: str = ""
    forecast: str = ""
    previous: str = ""
    affected_markets: Tuple[str, ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    read_only: bool = True

    def __post_init__(self):
        object.__setattr__(self, "title", str(self.title))
        object.__setattr__(self, "family", str(self.family).lower())
        object.__setattr__(self, "region", str(self.region).upper())
        object.__setattr__(self, "country", str(self.country).upper())
        object.__setattr__(self, "currency", str(self.currency).upper())
        object.__setattr__(self, "impact", str(self.impact).lower())
        object.__setattr__(self, "affected_markets", tuple(str(m).upper() for m in self.affected_markets))
        object.__setattr__(self, "metadata", _freeze(dict(self.metadata or {})))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "title": self.title,
            "family": self.family,
            "region": self.region,
            "country": self.country,
            "currency": self.currency,
            "impact": self.impact,
            "scheduled_at": self.scheduled_at,
            "source_name": self.source_name,
            "actual": self.actual,
            "forecast": self.forecast,
            "previous": self.previous,
            "affected_markets": list(self.affected_markets),
            "metadata": dict(self.metadata),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class MacroEventSourceBatch:
    schema_version: str
    adapter_id: str
    source_name: str
    snapshots: Tuple[MacroEventSnapshot, ...]
    telemetry: Mapping[str, Any]
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "adapter_id": self.adapter_id,
            "source_name": self.source_name,
            "snapshots": [s.to_dict() for s in self.snapshots],
            "telemetry": dict(self.telemetry),
            "read_only": self.read_only,
        }


class MacroEventSourceAdapter:
    schema_version = SCHEMA_VERSION
    adapter_id = ADAPTER_ID
    read_only = True

    def __init__(self, source_name: str = "generic_macro_event") -> None:
        self.source_name = str(source_name)

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "adapter_id": self.adapter_id,
            "source_name": self.source_name,
            "read_only": True,
            "deterministic": True,
            "telemetry": True,
            "execution": False,
            "order_allowed": False,
            "position_sizing_allowed": False,
        }

    def health(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "adapter_id": self.adapter_id,
            "status": "ok",
            "ready": True,
            "read_only": True,
            "checked_at": _utc_now_iso(),
        }

    def normalize_batch(self, raw_records: Sequence[Any]) -> MacroEventSourceBatch:
        raw = tuple(raw_records or ())
        started_at = _utc_now_iso()
        snapshots = tuple(sorted((self.normalize_record(r) for r in raw), key=lambda s: (s.scheduled_at, s.impact, s.event_id)))

        telemetry = MappingProxyType({
            "schema_version": self.schema_version,
            "adapter_id": self.adapter_id,
            "source_name": self.source_name,
            "started_at": started_at,
            "completed_at": _utc_now_iso(),
            "raw_records_seen": len(raw),
            "snapshots_emitted": len(snapshots),
            "events_seen": len({s.event_id for s in snapshots}),
            "read_only": True,
            "deterministic_sort": True,
            "execution_allowed": False,
            "order_allowed": False,
            "position_sizing_allowed": False,
        })

        return MacroEventSourceBatch(
            schema_version=self.schema_version,
            adapter_id=self.adapter_id,
            source_name=self.source_name,
            snapshots=snapshots,
            telemetry=telemetry,
            read_only=True,
        )

    def normalize_record(self, raw: Any) -> MacroEventSnapshot:
        title = str(_read(raw, "title", _read(raw, "event", _read(raw, "name", "Untitled Macro Event"))))
        family = str(_read(raw, "family", _read(raw, "category", "economic_release")))
        region = str(_read(raw, "region", _read(raw, "area", "US")))
        country = str(_read(raw, "country", region))
        currency = str(_read(raw, "currency", _read(raw, "ccy", "USD")))
        impact = str(_read(raw, "impact", _read(raw, "importance", "medium"))).lower()
        scheduled_at = str(_read(raw, "scheduled_at", _read(raw, "time", _read(raw, "datetime", ""))))
        source_id = str(_read(raw, "event_id", _read(raw, "id", "")))

        event_id = source_id or _stable_id("macro.event", {
            "title": title,
            "family": family,
            "region": region,
            "currency": currency,
            "scheduled_at": scheduled_at,
            "source": self.source_name,
        })

        markets = _read(raw, "affected_markets", _read(raw, "markets", ()))
        if isinstance(markets, str):
            markets = tuple(x.strip() for x in markets.split(",") if x.strip())

        meta = dict(_read(raw, "metadata", {}) or {})
        meta["source_name"] = self.source_name
        meta["adapter_id"] = self.adapter_id

        return MacroEventSnapshot(
            event_id=str(event_id),
            title=title,
            family=family,
            region=region,
            country=country,
            currency=currency,
            impact=impact,
            scheduled_at=scheduled_at,
            source_name=self.source_name,
            actual=str(_read(raw, "actual", "")),
            forecast=str(_read(raw, "forecast", _read(raw, "consensus", ""))),
            previous=str(_read(raw, "previous", "")),
            affected_markets=tuple(markets or ()),
            metadata=meta,
            read_only=True,
        )


__all__ = [
    "SCHEMA_VERSION",
    "ADAPTER_ID",
    "MacroEventSnapshot",
    "MacroEventSourceBatch",
    "MacroEventSourceAdapter",
]
'''

TEST_CODE = r'''
from qseries_v2.oracle_intelligence.macro_event_discovery_model.macro_event_source_adapter import MacroEventSourceAdapter


def test_med_002_macro_event_source_adapter():
    raw = [
        {
            "event_id": "fomc_2026_01",
            "title": "FOMC Rate Decision",
            "family": "fed_event",
            "region": "us",
            "country": "us",
            "currency": "usd",
            "impact": "high",
            "scheduled_at": "2026-01-28T19:00:00Z",
            "forecast": "4.50%",
            "previous": "4.50%",
            "affected_markets": ["RATES", "PREDICTION_MARKETS"],
        },
        {
            "id": "cpi_2026_01",
            "event": "US CPI YoY",
            "category": "inflation_event",
            "area": "us",
            "ccy": "usd",
            "importance": "high",
            "time": "2026-01-15T13:30:00Z",
            "consensus": "2.9%",
            "previous": "3.0%",
            "markets": "RATES, EQUITIES, PREDICTION_MARKETS",
        },
    ]

    adapter = MacroEventSourceAdapter(source_name="med_002_test_feed")
    caps = adapter.capabilities()
    health = adapter.health()

    batch_a = adapter.normalize_batch(raw)
    batch_b = adapter.normalize_batch(list(reversed(raw)))

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["order_allowed"] is False
    assert caps["position_sizing_allowed"] is False
    assert caps["deterministic"] is True

    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert batch_a.schema_version == "MED-002"
    assert batch_a.adapter_id == "oracle.discovery.source.macro_event"
    assert batch_a.read_only is True
    assert len(batch_a.snapshots) == 2

    order_a = [s.event_id for s in batch_a.snapshots]
    order_b = [s.event_id for s in batch_b.snapshots]
    assert order_a == order_b
    assert order_a == ["cpi_2026_01", "fomc_2026_01"]

    first = batch_a.snapshots[0]
    assert first.title == "US CPI YoY"
    assert first.family == "inflation_event"
    assert first.region == "US"
    assert first.country == "US"
    assert first.currency == "USD"
    assert first.impact == "high"
    assert first.forecast == "2.9%"
    assert first.previous == "3.0%"
    assert first.affected_markets == ("RATES", "EQUITIES", "PREDICTION_MARKETS")
    assert first.read_only is True

    try:
        first.metadata["x"] = "mutation"
        raise AssertionError("metadata should be immutable")
    except TypeError:
        pass

    d = batch_a.to_dict()
    assert d["schema_version"] == "MED-002"
    assert d["telemetry"]["raw_records_seen"] == 2
    assert d["telemetry"]["snapshots_emitted"] == 2
    assert d["telemetry"]["events_seen"] == 2
    assert d["telemetry"]["read_only"] is True
    assert d["telemetry"]["execution_allowed"] is False

    print("[PASS] MED-002 Macro Event Source Adapter")
    print({
        "schema_version": d["schema_version"],
        "adapter_id": d["adapter_id"],
        "snapshots": len(d["snapshots"]),
        "events_seen": d["telemetry"]["events_seen"],
        "read_only": d["read_only"],
    })


if __name__ == "__main__":
    test_med_002_macro_event_source_adapter()
'''

INIT_EXPORT = '''
try:
    from .macro_event_source_adapter import (
        MacroEventSnapshot,
        MacroEventSourceBatch,
        MacroEventSourceAdapter,
    )
except Exception:
    pass
'''

ADAPTER_FILE.write_text(ADAPTER_CODE, encoding="utf-8")
TEST_FILE.write_text(TEST_CODE, encoding="utf-8")

existing = INIT_FILE.read_text(encoding="utf-8") if INIT_FILE.exists() else ""
if "MacroEventSourceAdapter" not in existing:
    INIT_FILE.write_text(existing.rstrip() + "\n" + INIT_EXPORT.lstrip(), encoding="utf-8")

print("========================================")
print(" MED-002 INSTALLER")
print(" Macro Event Source Adapter")
print("========================================")
print(f"[OK] Wrote {ADAPTER_FILE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT_FILE}")
print()
print("[DONE] MED-002 installed")
print()
print("Run:")
print("py test_med_002_macro_event_source_adapter.py")