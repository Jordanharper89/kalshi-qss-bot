from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence"
MODULE_PATH = MODULE_DIR / "universal_market_adapter_query_resolver_engine.py"
TEST_PATH = ROOT / "test_oi_184_universal_market_adapter_query_resolver_engine.py"
INIT_PATH = MODULE_DIR / "__init__.py"

MODULE_CODE = r'''
"""
OI-184 — Oracle Universal Market Adapter Query Resolver Engine

Read-only query resolver for Universal Market Adapter lookup indexes.

This module resolves adapter lookup requests against an already-built lookup
index. It supports registry_id, lookup_key, candidate_id, market_type, namespace,
and generic query resolution.

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


ENGINE_ID = "oi.184.universal_market_adapter_query_resolver"
ENGINE_NAME = "Oracle Universal Market Adapter Query Resolver Engine"
ENGINE_VERSION = "1.0.0"
ARCHITECTURE_ROLE = "read_only_adapter_query_resolver"
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

SUPPORTED_QUERY_TYPES = (
    "registry_id",
    "lookup_key",
    "candidate_id",
    "market_type",
    "namespace",
    "generic",
)


@dataclass(frozen=True)
class AdapterQueryRequest:
    query: str
    query_type: str = "generic"
    market_type: Optional[str] = None
    namespace: Optional[str] = None
    limit: int = 25
    include_metadata: bool = True
    read_only: bool = True
    execution_owner: str = Q_SERIES_EXECUTION_OWNER

    def normalized(self) -> Dict[str, Any]:
        return {
            "query": str(self.query or "").strip(),
            "query_type": normalize_query_type(self.query_type),
            "market_type": normalize_market_type(self.market_type or ""),
            "namespace": str(self.namespace or "").strip(),
            "limit": max(1, min(250, int(self.limit))),
            "include_metadata": bool(self.include_metadata),
            "read_only": bool(self.read_only),
            "execution_owner": str(self.execution_owner),
        }


@dataclass(frozen=True)
class AdapterQueryResult:
    request: AdapterQueryRequest
    matched: bool
    match_count: int
    records: Tuple[Mapping[str, Any], ...]
    explanation: Mapping[str, Any]
    telemetry: Mapping[str, Any]
    query_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request": self.request.normalized(),
            "matched": self.matched,
            "match_count": self.match_count,
            "records": [dict(record) for record in self.records],
            "explanation": dict(self.explanation),
            "telemetry": dict(self.telemetry),
            "query_hash": self.query_hash,
        }


@dataclass(frozen=True)
class AdapterQueryResolverSnapshot:
    engine_id: str
    engine_name: str
    engine_version: str
    created_at: float
    query_count: int
    matched_query_count: int
    results: Tuple[AdapterQueryResult, ...]
    architecture: Mapping[str, Any]
    replay_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "created_at": self.created_at,
            "query_count": self.query_count,
            "matched_query_count": self.matched_query_count,
            "results": [result.to_dict() for result in self.results],
            "architecture": dict(self.architecture),
            "replay_hash": self.replay_hash,
        }


def normalize_market_type(value: str) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def normalize_query_type(value: str) -> str:
    cleaned = str(value or "generic").strip().lower().replace("-", "_").replace(" ", "_")
    return cleaned if cleaned in SUPPORTED_QUERY_TYPES else "generic"


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
        "adapter_query_resolver_ready": True,
        "guardrails": list(READ_ONLY_GUARDRAILS),
    }


def _records_by_registry_id(index: Mapping[str, Any]) -> Mapping[str, Mapping[str, Any]]:
    return index.get("records_by_registry_id", {}) or {}


def _lookup_map(index: Mapping[str, Any]) -> Mapping[str, str]:
    return index.get("registry_id_by_lookup_key", {}) or {}


def _candidate_map(index: Mapping[str, Any]) -> Mapping[str, str]:
    return index.get("registry_id_by_candidate_id", {}) or {}


def _market_map(index: Mapping[str, Any]) -> Mapping[str, Iterable[str]]:
    return index.get("registry_ids_by_market_type", {}) or {}


def _namespace_map(index: Mapping[str, Any]) -> Mapping[str, Iterable[str]]:
    return index.get("registry_ids_by_namespace", {}) or {}


def sanitize_record(record: Mapping[str, Any], include_metadata: bool) -> Dict[str, Any]:
    data = dict(record)
    if not include_metadata:
        data.pop("metadata", None)
    return data


def resolve_query(
    index: Mapping[str, Any],
    request: AdapterQueryRequest,
    resolved_at: Optional[float] = None,
) -> AdapterQueryResult:
    timestamp = float(resolved_at if resolved_at is not None else time.time())
    req = request.normalized()

    records_by_id = _records_by_registry_id(index)
    query_type = req["query_type"]
    query = req["query"]
    limit = req["limit"]

    matches = []

    if req["read_only"] is not True or req["execution_owner"] != Q_SERIES_EXECUTION_OWNER:
        matches = []
    elif query_type == "registry_id":
        record = records_by_id.get(query)
        matches = [record] if record else []
    elif query_type == "lookup_key":
        registry_id = _lookup_map(index).get(query)
        record = records_by_id.get(registry_id) if registry_id else None
        matches = [record] if record else []
    elif query_type == "candidate_id":
        registry_id = _candidate_map(index).get(query)
        record = records_by_id.get(registry_id) if registry_id else None
        matches = [record] if record else []
    elif query_type == "market_type":
        market = normalize_market_type(query or req["market_type"])
        ids = _market_map(index).get(market, ())
        matches = [records_by_id[item] for item in ids if item in records_by_id]
    elif query_type == "namespace":
        namespace = query or req["namespace"]
        ids = _namespace_map(index).get(namespace, ())
        matches = [records_by_id[item] for item in ids if item in records_by_id]
    else:
        text = query.lower()
        for record in records_by_id.values():
            haystack = " ".join(
                str(record.get(field, ""))
                for field in (
                    "registry_id",
                    "candidate_id",
                    "name",
                    "market_type",
                    "source_kind",
                    "registry_namespace",
                    "registry_owner",
                )
            ).lower()
            if text and text in haystack:
                matches.append(record)

    filtered = []
    for record in matches:
        if not record:
            continue
        if req["market_type"] and normalize_market_type(record.get("market_type", "")) != req["market_type"]:
            continue
        if req["namespace"] and str(record.get("registry_namespace", "")) != req["namespace"]:
            continue
        filtered.append(sanitize_record(record, req["include_metadata"]))

    filtered = tuple(filtered[:limit])
    matched = bool(filtered)

    explanation = {
        "summary": f"Query type {query_type} returned {len(filtered)} adapter record(s).",
        "matched": matched,
        "query_type": query_type,
        "query": query,
        "market_type_filter": req["market_type"],
        "namespace_filter": req["namespace"],
        "read_only_statement": "Query resolution is descriptive only and cannot execute, route, submit, or manage trades.",
        "q_series_boundary": "Q Series remains the sole execution owner.",
        "available_resolution_paths": list(SUPPORTED_QUERY_TYPES),
    }

    telemetry = {
        "engine_id": ENGINE_ID,
        "engine_version": ENGINE_VERSION,
        "architecture_role": ARCHITECTURE_ROLE,
        "query_type": query_type,
        "matched": matched,
        "match_count": len(filtered),
        "read_only": True,
        "execution_owner": Q_SERIES_EXECUTION_OWNER,
        "resolved_at": timestamp,
    }

    query_hash = stable_hash({
        "engine_id": ENGINE_ID,
        "engine_version": ENGINE_VERSION,
        "request": req,
        "matched_records": list(filtered),
        "telemetry": telemetry,
    })

    return AdapterQueryResult(
        request=request,
        matched=matched,
        match_count=len(filtered),
        records=filtered,
        explanation=explanation,
        telemetry=telemetry,
        query_hash=query_hash,
    )


def resolve_queries(
    index: Mapping[str, Any],
    requests: Iterable[AdapterQueryRequest],
    resolved_at: Optional[float] = None,
) -> AdapterQueryResolverSnapshot:
    timestamp = float(resolved_at if resolved_at is not None else time.time())
    results = tuple(resolve_query(index, request, resolved_at=timestamp) for request in requests)
    architecture = architecture_contract()

    replay_hash = stable_hash({
        "engine_id": ENGINE_ID,
        "engine_version": ENGINE_VERSION,
        "created_at": timestamp,
        "query_hashes": [result.query_hash for result in results],
        "architecture": architecture,
    })

    return AdapterQueryResolverSnapshot(
        engine_id=ENGINE_ID,
        engine_name=ENGINE_NAME,
        engine_version=ENGINE_VERSION,
        created_at=timestamp,
        query_count=len(results),
        matched_query_count=sum(1 for result in results if result.matched),
        results=results,
        architecture=architecture,
        replay_hash=replay_hash,
    )


def snapshot_to_json(snapshot: AdapterQueryResolverSnapshot, indent: int = 2) -> str:
    return json.dumps(snapshot.to_dict(), indent=indent, sort_keys=True, default=str)


class UniversalMarketAdapterQueryResolverEngine:
    def __init__(self) -> None:
        self._history = []

    def resolve(
        self,
        index: Mapping[str, Any],
        request: AdapterQueryRequest,
        resolved_at: Optional[float] = None,
    ) -> AdapterQueryResult:
        result = resolve_query(index, request, resolved_at=resolved_at)
        return result

    def resolve_many(
        self,
        index: Mapping[str, Any],
        requests: Iterable[AdapterQueryRequest],
        resolved_at: Optional[float] = None,
    ) -> AdapterQueryResolverSnapshot:
        snapshot = resolve_queries(index, requests, resolved_at=resolved_at)
        self._history.append(snapshot)
        return snapshot

    def latest_snapshot(self) -> Optional[AdapterQueryResolverSnapshot]:
        return self._history[-1] if self._history else None

    def history(self) -> Tuple[AdapterQueryResolverSnapshot, ...]:
        return tuple(self._history)

    def diagnostics(self) -> Dict[str, Any]:
        latest = self.latest_snapshot()
        return {
            "engine_id": ENGINE_ID,
            "engine_name": ENGINE_NAME,
            "engine_version": ENGINE_VERSION,
            "architecture_role": ARCHITECTURE_ROLE,
            "read_only": True,
            "execution_owner": Q_SERIES_EXECUTION_OWNER,
            "history_count": len(self._history),
            "latest_replay_hash": latest.replay_hash if latest else None,
            "latest_query_count": latest.query_count if latest else 0,
            "latest_matched_query_count": latest.matched_query_count if latest else 0,
            "guardrails": list(READ_ONLY_GUARDRAILS),
        }


oracle_universal_market_adapter_query_resolver_engine = UniversalMarketAdapterQueryResolverEngine()
universal_market_adapter_query_resolver_engine = oracle_universal_market_adapter_query_resolver_engine


def demo_index() -> Dict[str, Any]:
    registry_id = "oracle.adapters.prediction_markets.prediction_markets.demo.prediction.v1.0.0"
    lookup_key = "prediction_markets::oracle.adapters.prediction_markets::" + registry_id
    record = {
        "registry_id": registry_id,
        "candidate_id": "demo.prediction",
        "name": "Demo Prediction Lookup Record",
        "market_type": "prediction_markets",
        "source_kind": "api_schema",
        "registry_namespace": "oracle.adapters.prediction_markets",
        "registry_version": "1.0.0",
        "registry_owner": "oracle_intelligence",
        "availability_status": "available_for_oracle_lookup",
        "availability_score": 0.99,
        "availability_hash": "demo-availability-hash",
        "replay_hash": "demo-replay-hash",
        "lookup_key": lookup_key,
        "available": True,
        "read_only": True,
        "execution_owner": Q_SERIES_EXECUTION_OWNER,
        "metadata": {"fixture": True},
    }
    return {
        "records_by_registry_id": {registry_id: record},
        "registry_id_by_lookup_key": {lookup_key: registry_id},
        "registry_ids_by_market_type": {"prediction_markets": [registry_id]},
        "registry_ids_by_namespace": {"oracle.adapters.prediction_markets": [registry_id]},
        "registry_id_by_candidate_id": {"demo.prediction": registry_id},
    }


if __name__ == "__main__":
    snapshot = resolve_queries(
        demo_index(),
        (
            AdapterQueryRequest(query="demo.prediction", query_type="candidate_id"),
            AdapterQueryRequest(query="prediction_markets", query_type="market_type"),
        ),
        resolved_at=1760000000.0,
    )
    print(snapshot_to_json(snapshot))
'''

TEST_CODE = r'''
from qseries_v2.oracle_intelligence.universal_market_adapter_query_resolver_engine import (
    ENGINE_ID,
    Q_SERIES_EXECUTION_OWNER,
    AdapterQueryRequest,
    UniversalMarketAdapterQueryResolverEngine,
    architecture_contract,
    demo_index,
    resolve_queries,
    resolve_query,
    snapshot_to_json,
)


def test_query_resolver_candidate_lookup():
    result = resolve_query(
        demo_index(),
        AdapterQueryRequest(query="demo.prediction", query_type="candidate_id"),
        resolved_at=1760000000.0,
    )

    assert result.matched is True
    assert result.match_count == 1
    assert result.records[0]["candidate_id"] == "demo.prediction"
    assert result.telemetry["read_only"] is True
    assert result.telemetry["execution_owner"] == Q_SERIES_EXECUTION_OWNER


def test_query_resolver_market_type_lookup():
    result = resolve_query(
        demo_index(),
        AdapterQueryRequest(query="prediction_markets", query_type="market_type"),
        resolved_at=1760000000.0,
    )

    assert result.matched is True
    assert result.match_count == 1
    assert result.records[0]["market_type"] == "prediction_markets"


def test_query_resolver_namespace_lookup():
    result = resolve_query(
        demo_index(),
        AdapterQueryRequest(query="oracle.adapters.prediction_markets", query_type="namespace"),
        resolved_at=1760000000.0,
    )

    assert result.matched is True
    assert result.match_count == 1
    assert result.records[0]["registry_namespace"] == "oracle.adapters.prediction_markets"


def test_query_resolver_registry_and_lookup_key():
    index = demo_index()
    registry_id = list(index["records_by_registry_id"].keys())[0]
    lookup_key = list(index["registry_id_by_lookup_key"].keys())[0]

    by_registry = resolve_query(index, AdapterQueryRequest(query=registry_id, query_type="registry_id"), resolved_at=1760000000.0)
    by_lookup = resolve_query(index, AdapterQueryRequest(query=lookup_key, query_type="lookup_key"), resolved_at=1760000000.0)

    assert by_registry.matched is True
    assert by_lookup.matched is True
    assert by_registry.records[0]["registry_id"] == by_lookup.records[0]["registry_id"]


def test_query_resolver_snapshot_contract():
    snapshot = resolve_queries(
        demo_index(),
        (
            AdapterQueryRequest(query="demo.prediction", query_type="candidate_id"),
            AdapterQueryRequest(query="missing", query_type="candidate_id"),
        ),
        resolved_at=1760000000.0,
    )

    assert snapshot.engine_id == ENGINE_ID
    assert snapshot.query_count == 2
    assert snapshot.matched_query_count == 1
    assert snapshot.architecture["oracle_mode"] == "read_only"
    assert snapshot.architecture["execution_owner"] == Q_SERIES_EXECUTION_OWNER
    assert snapshot.replay_hash


def test_engine_history_and_json():
    engine = UniversalMarketAdapterQueryResolverEngine()
    snapshot = engine.resolve_many(
        demo_index(),
        (AdapterQueryRequest(query="prediction", query_type="generic"),),
        resolved_at=1760000000.0,
    )

    assert engine.latest_snapshot() == snapshot
    assert len(engine.history()) == 1

    text = snapshot_to_json(snapshot)
    assert "Oracle Universal Market Adapter Query Resolver Engine" in text
    assert "read_only" in text


def test_architecture_contract():
    contract = architecture_contract()

    assert contract["oracle_mode"] == "read_only"
    assert contract["universal_market_model"] is True
    assert contract["adapter_based_expansion"] is True
    assert contract["explainability_by_default"] is True
    assert contract["replayability_by_default"] is True
    assert contract["institutional_telemetry"] is True
    assert contract["adapter_query_resolver_ready"] is True
    assert contract["execution_owner"] == Q_SERIES_EXECUTION_OWNER


if __name__ == "__main__":
    test_query_resolver_candidate_lookup()
    test_query_resolver_market_type_lookup()
    test_query_resolver_namespace_lookup()
    test_query_resolver_registry_and_lookup_key()
    test_query_resolver_snapshot_contract()
    test_engine_history_and_json()
    test_architecture_contract()
    print("[PASS] OI-184 Universal Market Adapter Query Resolver Engine")
    print(resolve_queries(demo_index(), (AdapterQueryRequest(query="demo.prediction", query_type="candidate_id"),), resolved_at=1760000000.0).to_dict())
'''


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def update_init() -> None:
    INIT_PATH.parent.mkdir(parents=True, exist_ok=True)

    if INIT_PATH.exists():
        existing = INIT_PATH.read_text(encoding="utf-8")
    else:
        existing = ""

    export_line = (
        "from .universal_market_adapter_query_resolver_engine import "
        "UniversalMarketAdapterQueryResolverEngine, "
        "oracle_universal_market_adapter_query_resolver_engine, "
        "universal_market_adapter_query_resolver_engine\n"
    )

    additions = [
        "UniversalMarketAdapterQueryResolverEngine",
        "oracle_universal_market_adapter_query_resolver_engine",
        "universal_market_adapter_query_resolver_engine",
    ]

    if export_line not in existing:
        existing = existing.rstrip() + "\n" + export_line

    if "__all__" not in existing:
        existing += "\n__all__ = [\n"
        for item in additions:
            existing += f'    "{item}",\n'
        existing += "]\n"
    else:
        for item in additions:
            token = f'"{item}"'
            if token not in existing:
                existing = existing.replace("__all__ = [", f'__all__ = [\n    "{item}",')

    INIT_PATH.write_text(existing, encoding="utf-8")


def main() -> None:
    print("========================================")
    print(" OI-184 INSTALLER")
    print(" Universal Market Adapter Query Resolver Engine")
    print("========================================")

    write_file(MODULE_PATH, MODULE_CODE)
    print(f"[OK] Wrote {MODULE_PATH}")

    write_file(TEST_PATH, TEST_CODE)
    print(f"[OK] Wrote {TEST_PATH}")

    update_init()
    print(f"[OK] Updated {INIT_PATH}")

    print()
    print("[DONE] OI-184 installed")
    print()
    print("Run:")
    print("py test_oi_184_universal_market_adapter_query_resolver_engine.py")


if __name__ == "__main__":
    main()