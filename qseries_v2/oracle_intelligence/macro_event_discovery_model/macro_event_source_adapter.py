
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
