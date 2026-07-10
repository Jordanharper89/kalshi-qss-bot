
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

SCHEMA_VERSION = "SID-002"
ADAPTER_ID = "oracle.discovery.source.social_intelligence"


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


def _float(v: Any, default: float = 0.0) -> float:
    try:
        if v is None:
            return default
        return float(v)
    except Exception:
        return default


def _stable_text(v: Any) -> str:
    if isinstance(v, Mapping):
        return "{" + ",".join(f"{k}:{_stable_text(x)}" for k, x in sorted(v.items())) + "}"
    if isinstance(v, (list, tuple)):
        return "[" + ",".join(_stable_text(x) for x in v) + "]"
    return repr(v)


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    return prefix + "." + sha256(_stable_text(payload).encode("utf-8")).hexdigest()[:20]


@dataclass(frozen=True)
class SocialSignalSnapshot:
    post_id: str
    platform: str
    author: str
    topic: str
    text: str
    posted_at: str
    sentiment: str
    engagement_score: float
    velocity_score: float
    credibility_score: float
    affected_markets: Tuple[str, ...] = field(default_factory=tuple)
    entities: Tuple[str, ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    read_only: bool = True

    def __post_init__(self):
        object.__setattr__(self, "post_id", str(self.post_id))
        object.__setattr__(self, "platform", str(self.platform).lower())
        object.__setattr__(self, "author", str(self.author))
        object.__setattr__(self, "topic", str(self.topic).lower())
        object.__setattr__(self, "text", str(self.text))
        object.__setattr__(self, "posted_at", str(self.posted_at))
        object.__setattr__(self, "sentiment", str(self.sentiment).lower())
        object.__setattr__(self, "engagement_score", max(0.0, min(1.0, _float(self.engagement_score))))
        object.__setattr__(self, "velocity_score", max(0.0, min(1.0, _float(self.velocity_score))))
        object.__setattr__(self, "credibility_score", max(0.0, min(1.0, _float(self.credibility_score))))
        object.__setattr__(self, "affected_markets", tuple(str(m).upper() for m in self.affected_markets))
        object.__setattr__(self, "entities", tuple(str(e).upper() for e in self.entities))
        object.__setattr__(self, "metadata", _freeze(dict(self.metadata or {})))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "post_id": self.post_id,
            "platform": self.platform,
            "author": self.author,
            "topic": self.topic,
            "text": self.text,
            "posted_at": self.posted_at,
            "sentiment": self.sentiment,
            "engagement_score": self.engagement_score,
            "velocity_score": self.velocity_score,
            "credibility_score": self.credibility_score,
            "affected_markets": list(self.affected_markets),
            "entities": list(self.entities),
            "metadata": dict(self.metadata),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class SocialIntelligenceSourceBatch:
    schema_version: str
    adapter_id: str
    source_name: str
    snapshots: Tuple[SocialSignalSnapshot, ...]
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


class SocialIntelligenceSourceAdapter:
    schema_version = SCHEMA_VERSION
    adapter_id = ADAPTER_ID
    read_only = True

    def __init__(self, source_name: str = "generic_social_intelligence") -> None:
        self.source_name = str(source_name)

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "adapter_id": self.adapter_id,
            "source_name": self.source_name,
            "read_only": True,
            "normalizes_to": "SocialSignalSnapshot",
            "deterministic": True,
            "telemetry": True,
            "execution": False,
            "order_allowed": False,
            "position_sizing_allowed": False,
            "posting_allowed": False,
            "dm_allowed": False,
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

    def normalize_batch(self, raw_records: Sequence[Any]) -> SocialIntelligenceSourceBatch:
        started_at = _utc_now_iso()
        raw = tuple(raw_records or ())
        snapshots = tuple(sorted((self.normalize_record(r) for r in raw), key=lambda s: (s.posted_at, s.platform, s.post_id)))

        telemetry = MappingProxyType({
            "schema_version": self.schema_version,
            "adapter_id": self.adapter_id,
            "source_name": self.source_name,
            "started_at": started_at,
            "completed_at": _utc_now_iso(),
            "raw_records_seen": len(raw),
            "snapshots_emitted": len(snapshots),
            "posts_seen": len({s.post_id for s in snapshots}),
            "read_only": True,
            "deterministic_sort": True,
            "execution_allowed": False,
            "order_allowed": False,
            "position_sizing_allowed": False,
            "posting_allowed": False,
            "dm_allowed": False,
        })

        return SocialIntelligenceSourceBatch(
            schema_version=self.schema_version,
            adapter_id=self.adapter_id,
            source_name=self.source_name,
            snapshots=snapshots,
            telemetry=telemetry,
            read_only=True,
        )

    def normalize_record(self, raw: Any) -> SocialSignalSnapshot:
        platform = str(_read(raw, "platform", _read(raw, "network", "x")))
        author = str(_read(raw, "author", _read(raw, "username", "unknown")))
        topic = str(_read(raw, "topic", _read(raw, "category", "social_momentum")))
        text = str(_read(raw, "text", _read(raw, "content", "")))
        posted_at = str(_read(raw, "posted_at", _read(raw, "time", _read(raw, "timestamp", ""))))
        sentiment = str(_read(raw, "sentiment", "neutral"))

        post_id = str(_read(raw, "post_id", _read(raw, "id", ""))) or _stable_id("social.post", {
            "platform": platform,
            "author": author,
            "topic": topic,
            "text": text,
            "posted_at": posted_at,
        })

        markets = _read(raw, "affected_markets", _read(raw, "markets", ()))
        if isinstance(markets, str):
            markets = tuple(x.strip() for x in markets.split(",") if x.strip())

        entities = _read(raw, "entities", _read(raw, "symbols", ()))
        if isinstance(entities, str):
            entities = tuple(x.strip() for x in entities.split(",") if x.strip())

        meta = dict(_read(raw, "metadata", {}) or {})
        meta["source_name"] = self.source_name
        meta["adapter_id"] = self.adapter_id

        return SocialSignalSnapshot(
            post_id=post_id,
            platform=platform,
            author=author,
            topic=topic,
            text=text,
            posted_at=posted_at,
            sentiment=sentiment,
            engagement_score=_float(_read(raw, "engagement_score", _read(raw, "engagement", 0.0))),
            velocity_score=_float(_read(raw, "velocity_score", _read(raw, "velocity", 0.0))),
            credibility_score=_float(_read(raw, "credibility_score", _read(raw, "credibility", 0.5))),
            affected_markets=tuple(markets or ()),
            entities=tuple(entities or ()),
            metadata=meta,
            read_only=True,
        )


__all__ = [
    "SCHEMA_VERSION",
    "ADAPTER_ID",
    "SocialSignalSnapshot",
    "SocialIntelligenceSourceBatch",
    "SocialIntelligenceSourceAdapter",
]
