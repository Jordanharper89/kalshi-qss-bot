from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import (
    UMD_SUBSYSTEM_ID,
    ImmutableLineage,
    deterministic_sha256,
)

UMD_094_BUILD_ID = "UMD-094"
UMD_094_BUILD_NAME = "Market Normalization Foundation"
UMD_094_REVISION = "UMD_094_MARKET_NORMALIZATION_FOUNDATION_V1"
UMD_094_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_invocation", "persistence", "mutation", "publication", "execution",
)

_WS = re.compile(r"\\s+")
_PUNCT = re.compile(r"[^a-z0-9]+")


def _text(value: str, field_name: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    value = unicodedata.normalize("NFKC", value)
    value = _WS.sub(" ", value.strip())
    if not value and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    return value


def _key(value: str, field_name: str) -> str:
    value = _text(value, field_name).casefold()
    value = _PUNCT.sub("-", value).strip("-")
    if not value:
        raise ValueError(f"{field_name} must contain letters or digits")
    return value


def _freeze(value: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if value is None:
        value = {}
    if not isinstance(value, Mapping):
        raise TypeError("metadata must be a mapping")
    return MappingProxyType(dict(sorted((str(k), v) for k, v in value.items())))


def _tuple_text(values, field_name: str) -> Tuple[str, ...]:
    if isinstance(values, str):
        raise TypeError(f"{field_name} must be an iterable of strings")
    result = tuple(_text(v, field_name) for v in values)
    if len(set(x.casefold() for x in result)) != len(result):
        raise ValueError(f"{field_name} must not contain duplicates")
    return result


@dataclass(frozen=True, slots=True)
class MarketObservation:
    venue: str
    venue_market_id: str
    title: str
    description: str = ""
    category: str = "uncategorized"
    status: str = "unknown"
    close_time: str = ""
    settlement_time: str = ""
    outcomes: Tuple[str, ...] = ()
    rules: str = ""
    source_ref: str = ""
    metadata: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "venue", _text(self.venue, "venue"))
        object.__setattr__(self, "venue_market_id", _text(self.venue_market_id, "venue_market_id"))
        object.__setattr__(self, "title", _text(self.title, "title"))
        object.__setattr__(self, "description", _text(self.description, "description", allow_empty=True))
        object.__setattr__(self, "category", _text(self.category, "category"))
        object.__setattr__(self, "status", _text(self.status, "status"))
        object.__setattr__(self, "close_time", _text(self.close_time, "close_time", allow_empty=True))
        object.__setattr__(self, "settlement_time", _text(self.settlement_time, "settlement_time", allow_empty=True))
        object.__setattr__(self, "outcomes", _tuple_text(self.outcomes, "outcome"))
        object.__setattr__(self, "rules", _text(self.rules, "rules", allow_empty=True))
        object.__setattr__(self, "source_ref", _text(self.source_ref, "source_ref", allow_empty=True))
        object.__setattr__(self, "metadata", _freeze(self.metadata))

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "venue": self.venue, "venue_market_id": self.venue_market_id,
            "title": self.title, "description": self.description,
            "category": self.category, "status": self.status,
            "close_time": self.close_time, "settlement_time": self.settlement_time,
            "outcomes": self.outcomes, "rules": self.rules,
            "source_ref": self.source_ref, "metadata": self.metadata,
        }

    @property
    def observation_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())


@dataclass(frozen=True, slots=True)
class NormalizedMarket:
    venue: str
    venue_key: str
    venue_market_id: str
    title: str
    title_key: str
    description: str
    category: str
    category_key: str
    status: str
    status_key: str
    close_time: str
    settlement_time: str
    outcomes: Tuple[str, ...]
    outcome_keys: Tuple[str, ...]
    rules: str
    source_ref: str
    source_observation_hash: str
    metadata: Mapping[str, Any]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        for name in ("venue", "venue_key", "venue_market_id", "title", "title_key", "category", "category_key", "status", "status_key", "source_observation_hash"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise ValueError(f"{name} must be non-empty")
        object.__setattr__(self, "metadata", _freeze(self.metadata))
        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("lineage must belong to UMD")
        if self.lineage.build_id != UMD_094_BUILD_ID:
            raise ValueError("lineage build_id must be UMD-094")
        if self.source_observation_hash not in self.lineage.parent_hashes:
            raise ValueError("lineage must include source observation hash")

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "venue": self.venue, "venue_key": self.venue_key,
            "venue_market_id": self.venue_market_id, "title": self.title,
            "title_key": self.title_key, "description": self.description,
            "category": self.category, "category_key": self.category_key,
            "status": self.status, "status_key": self.status_key,
            "close_time": self.close_time, "settlement_time": self.settlement_time,
            "outcomes": self.outcomes, "outcome_keys": self.outcome_keys,
            "rules": self.rules, "source_ref": self.source_ref,
            "source_observation_hash": self.source_observation_hash,
            "metadata": self.metadata, "lineage": self.lineage,
        }

    @property
    def normalized_market_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())


class MarketNormalizer:
    __slots__ = ()

    def normalize(self, observation: MarketObservation, *, lineage: ImmutableLineage) -> NormalizedMarket:
        if not isinstance(observation, MarketObservation):
            raise TypeError("observation must be MarketObservation")
        return NormalizedMarket(
            venue=observation.venue,
            venue_key=_key(observation.venue, "venue"),
            venue_market_id=observation.venue_market_id,
            title=observation.title,
            title_key=_key(observation.title, "title"),
            description=observation.description,
            category=observation.category,
            category_key=_key(observation.category, "category"),
            status=observation.status,
            status_key=_key(observation.status, "status"),
            close_time=observation.close_time,
            settlement_time=observation.settlement_time,
            outcomes=observation.outcomes,
            outcome_keys=tuple(_key(v, "outcome") for v in observation.outcomes),
            rules=observation.rules,
            source_ref=observation.source_ref,
            source_observation_hash=observation.observation_hash,
            metadata=observation.metadata,
            lineage=lineage,
        )


def build_umd_094_certification_manifest() -> Mapping[str, Any]:
    data = {
        "subsystem_id": "UMD", "build_id": UMD_094_BUILD_ID,
        "revision": UMD_094_REVISION, "schema_version": UMD_094_SCHEMA_VERSION,
        "upstream_build": "UMD-093", "mode": "deterministic_read_only_normalization",
        "prohibited_capabilities": PROHIBITED_CAPABILITIES,
        "network_enabled": False, "persistence_enabled": False,
        "mutation_enabled": False, "publication_enabled": False, "execution_enabled": False,
    }
    return MappingProxyType({**data, "manifest_hash": deterministic_sha256(data)})


def verify_umd_094_market_normalization_foundation() -> bool:
    manifest = build_umd_094_certification_manifest()
    return all((manifest["build_id"] == "UMD-094", manifest["upstream_build"] == "UMD-093", not manifest["network_enabled"], not manifest["persistence_enabled"], not manifest["mutation_enabled"], not manifest["publication_enabled"], not manifest["execution_enabled"]))
