
"""
OI-183 — Oracle Universal Market Adapter Lookup Index Engine

Read-only lookup index layer for available Universal Market Adapter registry
records.

This module builds deterministic lookup indexes from adapter availability
decisions. It supports Oracle intelligence lookup by market type, namespace,
registry id, candidate id, and lookup key.

It does not execute trades, route orders, submit orders, manage positions, or
mutate external systems.

Oracle remains intelligence-only.
Q Series remains the sole execution owner.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple


ENGINE_ID = "oi.183.universal_market_adapter_lookup_index"
ENGINE_NAME = "Oracle Universal Market Adapter Lookup Index Engine"
ENGINE_VERSION = "1.0.0"
ARCHITECTURE_ROLE = "read_only_adapter_lookup_index"
Q_SERIES_EXECUTION_OWNER = "qseries.execution"

READ_ONLY_GUARDRAILS = (
    "Oracle never executes trades.",
    "Oracle never manages positions.",
    "Oracle never submits orders.",
    "Oracle never routes orders.",
    "Oracle never signs transactions.",
    "Oracle never custody-controls assets.",
    "Q Series is the only execution engine.",
)


@dataclass(frozen=True)
class AdapterLookupIndexRecord:
    registry_id: str
    candidate_id: str
    name: str
    market_type: str
    source_kind: str
    registry_namespace: str
    registry_version: str
    registry_owner: str
    availability_status: str
    availability_score: float
    availability_hash: str
    replay_hash: str
    lookup_key: str
    available: bool = True
    read_only: bool = True
    execution_owner: str = Q_SERIES_EXECUTION_OWNER
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def normalized(self) -> Dict[str, Any]:
        return {
            "registry_id": str(self.registry_id),
            "candidate_id": str(self.candidate_id),
            "name": str(self.name),
            "market_type": normalize_market_type(self.market_type),
            "source_kind": str(self.source_kind),
            "registry_namespace": str(self.registry_namespace),
            "registry_version": str(self.registry_version),
            "registry_owner": str(self.registry_owner),
            "availability_status": str(self.availability_status),
            "availability_score": clamp(self.availability_score),
            "availability_hash": str(self.availability_hash),
            "replay_hash": str(self.replay_hash),
            "lookup_key": str(self.lookup_key),
            "available": bool(self.available),
            "read_only": bool(self.read_only),
            "execution_owner": str(self.execution_owner),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class AdapterLookupIndex:
    engine_id: str
    engine_version: str
    created_at: float
    record_count: int
    available_count: int
    records_by_registry_id: Mapping[str, Mapping[str, Any]]
    registry_id_by_lookup_key: Mapping[str, str]
    registry_ids_by_market_type: Mapping[str, Tuple[str, ...]]
    registry_ids_by_namespace: Mapping[str, Tuple[str, ...]]
    registry_id_by_candidate_id: Mapping[str, str]
    architecture: Mapping[str, Any]
    replay_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_version": self.engine_version,
            "created_at": self.created_at,
            "record_count": self.record_count,
            "available_count": self.available_count,
            "records_by_registry_id": {key: dict(value) for key, value in self.records_by_registry_id.items()},
            "registry_id_by_lookup_key": dict(self.registry_id_by_lookup_key),
            "registry_ids_by_market_type": {key: list(value) for key, value in self.registry_ids_by_market_type.items()},
            "registry_ids_by_namespace": {key: list(value) for key, value in self.registry_ids_by_namespace.items()},
            "registry_id_by_candidate_id": dict(self.registry_id_by_candidate_id),
            "architecture": dict(self.architecture),
            "replay_hash": self.replay_hash,
        }

    def get_by_registry_id(self, registry_id: str) -> Optional[Mapping[str, Any]]:
        return self.records_by_registry_id.get(str(registry_id))

    def get_by_lookup_key(self, lookup_key: str) -> Optional[Mapping[str, Any]]:
        registry_id = self.registry_id_by_lookup_key.get(str(lookup_key))
        if not registry_id:
            return None
        return self.records_by_registry_id.get(registry_id)

    def get_by_candidate_id(self, candidate_id: str) -> Optional[Mapping[str, Any]]:
        registry_id = self.registry_id_by_candidate_id.get(str(candidate_id))
        if not registry_id:
            return None
        return self.records_by_registry_id.get(registry_id)

    def list_market_type(self, market_type: str) -> Tuple[Mapping[str, Any], ...]:
        normalized = normalize_market_type(market_type)
        ids = self.registry_ids_by_market_type.get(normalized, ())
        return tuple(self.records_by_registry_id[item] for item in ids if item in self.records_by_registry_id)

    def list_namespace(self, namespace: str) -> Tuple[Mapping[str, Any], ...]:
        ids = self.registry_ids_by_namespace.get(str(namespace), ())
        return tuple(self.records_by_registry_id[item] for item in ids if item in self.records_by_registry_id)


def normalize_market_type(value: str) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def clamp(value: Any) -> float:
    try:
        number = float(value)
    except Exception:
        number = 0.0
    return round(max(0.0, min(1.0, number)), 6)


def stable_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def architecture_contract() -> Dict[str, Any]:
    return {
        "oracle_mode": "read_only",
        "execution_owner": Q_SERIES_EXECUTION_OWNER,
        "universal_market_model": True,
        "single_oracle_instance": True,
        "adapter_based_expansion": True,
        "event_driven_intelligence": True,
        "explainability_by_default": True,
        "replayability_by_default": True,
        "historical_memory_ready": True,
        "institutional_telemetry": True,
        "strategy_agnostic_q_series": True,
        "architecture_registry_ready": True,
        "adapter_lookup_index_ready": True,
        "guardrails": list(READ_ONLY_GUARDRAILS),
    }


def record_is_indexable(record: AdapterLookupIndexRecord) -> bool:
    data = record.normalized()
    return (
        data["available"] is True
        and data["read_only"] is True
        and data["execution_owner"] == Q_SERIES_EXECUTION_OWNER
        and data["availability_status"] in {"available_for_oracle_lookup", "available_with_conditions", "indexed"}
        and bool(data["registry_id"])
        and bool(data["lookup_key"])
        and bool(data["market_type"])
        and data["market_type"] != "unknown"
        and bool(data["registry_namespace"])
    )


def build_lookup_index(
    records: Iterable[AdapterLookupIndexRecord],
    indexed_at: Optional[float] = None,
) -> AdapterLookupIndex:
    timestamp = float(indexed_at if indexed_at is not None else time.time())

    normalized_records = [record for record in records if record_is_indexable(record)]
    normalized_records.sort(
        key=lambda record: (
            normalize_market_type(record.market_type),
            record.registry_namespace,
            record.registry_id,
        )
    )

    records_by_registry_id: Dict[str, Mapping[str, Any]] = {}
    registry_id_by_lookup_key: Dict[str, str] = {}
    registry_ids_by_market_type: Dict[str, list] = {}
    registry_ids_by_namespace: Dict[str, list] = {}
    registry_id_by_candidate_id: Dict[str, str] = {}

    for record in normalized_records:
        data = record.normalized()
        registry_id = data["registry_id"]
        market_type = data["market_type"]
        namespace = data["registry_namespace"]
        lookup_key = data["lookup_key"]
        candidate_id = data["candidate_id"]

        records_by_registry_id[registry_id] = data
        registry_id_by_lookup_key[lookup_key] = registry_id
        registry_id_by_candidate_id[candidate_id] = registry_id

        registry_ids_by_market_type.setdefault(market_type, []).append(registry_id)
        registry_ids_by_namespace.setdefault(namespace, []).append(registry_id)

    market_type_index = {
        key: tuple(sorted(set(value)))
        for key, value in registry_ids_by_market_type.items()
    }
    namespace_index = {
        key: tuple(sorted(set(value)))
        for key, value in registry_ids_by_namespace.items()
    }

    architecture = architecture_contract()
    replay_hash = stable_hash({
        "engine_id": ENGINE_ID,
        "engine_version": ENGINE_VERSION,
        "created_at": timestamp,
        "records_by_registry_id": records_by_registry_id,
        "registry_id_by_lookup_key": registry_id_by_lookup_key,
        "registry_ids_by_market_type": market_type_index,
        "registry_ids_by_namespace": namespace_index,
        "registry_id_by_candidate_id": registry_id_by_candidate_id,
        "architecture": architecture,
    })

    return AdapterLookupIndex(
        engine_id=ENGINE_ID,
        engine_version=ENGINE_VERSION,
        created_at=timestamp,
        record_count=len(records_by_registry_id),
        available_count=len(records_by_registry_id),
        records_by_registry_id=records_by_registry_id,
        registry_id_by_lookup_key=registry_id_by_lookup_key,
        registry_ids_by_market_type=market_type_index,
        registry_ids_by_namespace=namespace_index,
        registry_id_by_candidate_id=registry_id_by_candidate_id,
        architecture=architecture,
        replay_hash=replay_hash,
    )


def record_from_availability_decision(decision: Mapping[str, Any]) -> AdapterLookupIndexRecord:
    record = decision.get("record", {})
    telemetry = decision.get("telemetry", {})
    lookup_key = telemetry.get("lookup_key") or decision.get("explanation", {}).get("lookup_key") or ""

    return AdapterLookupIndexRecord(
        registry_id=str(record.get("registry_id", telemetry.get("registry_id", ""))),
        candidate_id=str(record.get("candidate_id", telemetry.get("candidate_id", ""))),
        name=str(record.get("name", "")),
        market_type=str(record.get("market_type", telemetry.get("market_type", "unknown"))),
        source_kind=str(record.get("source_kind", "unknown")),
        registry_namespace=str(record.get("registry_namespace", "")),
        registry_version=str(record.get("registry_version", "")),
        registry_owner=str(record.get("registry_owner", "")),
        availability_status=str(decision.get("availability_status", telemetry.get("availability_status", ""))),
        availability_score=clamp(decision.get("availability_score", telemetry.get("availability_score", 0.0))),
        availability_hash=str(decision.get("availability_hash", "")),
        replay_hash=str(record.get("replay_hash", "")),
        lookup_key=str(lookup_key),
        available=bool(decision.get("available", telemetry.get("available", False))),
        read_only=bool(telemetry.get("read_only", record.get("read_only", True))),
        execution_owner=str(telemetry.get("execution_owner", record.get("execution_owner", Q_SERIES_EXECUTION_OWNER))),
        metadata=record.get("metadata", {}),
    )


def build_index_from_availability_snapshot(snapshot: Mapping[str, Any]) -> AdapterLookupIndex:
    records = [
        record_from_availability_decision(decision)
        for decision in snapshot.get("decisions", [])
    ]
    return build_lookup_index(records, indexed_at=float(snapshot.get("created_at", time.time())))


def index_to_json(index: AdapterLookupIndex, indent: int = 2) -> str:
    return json.dumps(index.to_dict(), indent=indent, sort_keys=True, default=str)


class UniversalMarketAdapterLookupIndexEngine:
    def __init__(self) -> None:
        self._history = []

    def build(
        self,
        records: Iterable[AdapterLookupIndexRecord],
        indexed_at: Optional[float] = None,
    ) -> AdapterLookupIndex:
        index = build_lookup_index(records, indexed_at=indexed_at)
        self._history.append(index)
        return index

    def build_from_availability_snapshot(self, snapshot: Mapping[str, Any]) -> AdapterLookupIndex:
        index = build_index_from_availability_snapshot(snapshot)
        self._history.append(index)
        return index

    def latest_index(self) -> Optional[AdapterLookupIndex]:
        return self._history[-1] if self._history else None

    def history(self) -> Tuple[AdapterLookupIndex, ...]:
        return tuple(self._history)

    def diagnostics(self) -> Dict[str, Any]:
        latest = self.latest_index()
        return {
            "engine_id": ENGINE_ID,
            "engine_name": ENGINE_NAME,
            "engine_version": ENGINE_VERSION,
            "architecture_role": ARCHITECTURE_ROLE,
            "read_only": True,
            "execution_owner": Q_SERIES_EXECUTION_OWNER,
            "history_count": len(self._history),
            "latest_replay_hash": latest.replay_hash if latest else None,
            "latest_record_count": latest.record_count if latest else 0,
            "guardrails": list(READ_ONLY_GUARDRAILS),
        }


oracle_universal_market_adapter_lookup_index_engine = UniversalMarketAdapterLookupIndexEngine()
universal_market_adapter_lookup_index_engine = oracle_universal_market_adapter_lookup_index_engine


def demo_records() -> Tuple[AdapterLookupIndexRecord, ...]:
    return (
        AdapterLookupIndexRecord(
            registry_id="oracle.adapters.prediction_markets.prediction_markets.demo.prediction.v1.0.0",
            candidate_id="demo.prediction",
            name="Demo Prediction Lookup Record",
            market_type="prediction_markets",
            source_kind="api_schema",
            registry_namespace="oracle.adapters.prediction_markets",
            registry_version="1.0.0",
            registry_owner="oracle_intelligence",
            availability_status="available_for_oracle_lookup",
            availability_score=0.99,
            availability_hash="demo-availability-hash",
            replay_hash="demo-replay-hash",
            lookup_key="prediction_markets::oracle.adapters.prediction_markets::oracle.adapters.prediction_markets.prediction_markets.demo.prediction.v1.0.0",
            available=True,
        ),
        AdapterLookupIndexRecord(
            registry_id="",
            candidate_id="demo.crypto",
            name="Demo Crypto Non-Indexable Record",
            market_type="crypto",
            source_kind="vendor_export",
            registry_namespace="",
            registry_version="",
            registry_owner="",
            availability_status="not_available",
            availability_score=0.10,
            availability_hash="",
            replay_hash="",
            lookup_key="crypto::::",
            available=False,
        ),
    )


if __name__ == "__main__":
    index = build_lookup_index(demo_records(), indexed_at=1760000000.0)
    print(index_to_json(index))
