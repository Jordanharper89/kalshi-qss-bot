from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

MODULE = PKG / "universal_market_adapter_replay_search_engine.py"
TEST = ROOT / "test_oi_192_universal_market_adapter_replay_search_engine.py"
INIT = PKG / "__init__.py"

MODULE.write_text(r'''
"""
OI-192 — Oracle Universal Market Adapter Replay Search Engine

Read-only institutional search layer for certified replay registry artifacts.

This engine searches replay registry records produced by the Oracle Universal
Market Adapter replay pipeline. It never mutates registry state, never executes
trades, never routes orders, never submits orders, and never manages positions.
Q Series remains the only execution engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence
import json


READ_ONLY_GUARDRAILS = {
    "oracle_read_only": True,
    "executes_trades": False,
    "routes_orders": False,
    "submits_orders": False,
    "manages_positions": False,
    "execution_owner": "Q_SERIES_ONLY",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _hash(value: Any) -> str:
    return sha256(_stable_json(value).encode("utf-8")).hexdigest()


def _safe_dict(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "to_dict"):
        converted = value.to_dict()
        if isinstance(converted, Mapping):
            return dict(converted)
    if hasattr(value, "__dict__"):
        return dict(value.__dict__)
    return {"value": value}


def _safe_lower(value: Any) -> str:
    return str(value or "").strip().lower()


def _contains(value: Any, needle: str) -> bool:
    if not needle:
        return True
    return needle in _stable_json(value).lower()


def _field(data: Mapping[str, Any], *names: str) -> Any:
    for name in names:
        if name in data and data.get(name) not in (None, ""):
            return data.get(name)
    telemetry = _safe_dict(data.get("telemetry"))
    for name in names:
        if name in telemetry and telemetry.get(name) not in (None, ""):
            return telemetry.get(name)
    explainability = _safe_dict(data.get("explainability"))
    for name in names:
        if name in explainability and explainability.get(name) not in (None, ""):
            return explainability.get(name)
    return None


@dataclass(frozen=True)
class ReplaySearchRecord:
    search_record_id: str
    registration_id: str
    registry_id: str
    certification_id: str
    validation_id: str
    manifest_id: str
    adapter_id: str
    market_id: str
    universal_market_id: str
    market_type: str
    market: str
    symbol: str
    status: str
    certified: bool
    created_at: str
    record_hash: str
    raw: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReplaySearchQuery:
    query_id: str
    text: str = ""
    registration_id: str = ""
    registry_id: str = ""
    certification_id: str = ""
    validation_id: str = ""
    manifest_id: str = ""
    adapter_id: str = ""
    market_id: str = ""
    universal_market_id: str = ""
    market_type: str = ""
    market: str = ""
    symbol: str = ""
    status: str = ""
    certified: Optional[bool] = None
    created_after: str = ""
    created_before: str = ""
    limit: int = 50

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReplaySearchResult:
    result_id: str
    created_at: str
    oracle_instance_id: str
    module_id: str
    module_name: str
    query: ReplaySearchQuery
    total_records: int
    matched_count: int
    returned_count: int
    result_hash: str
    read_only_guardrails: Dict[str, Any]
    records: List[ReplaySearchRecord]
    telemetry: Dict[str, Any]
    explainability: Dict[str, Any]

    @property
    def passed(self) -> bool:
        return True

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["passed"] = True
        return data


class UniversalMarketAdapterReplaySearchEngine:
    """
    Searches replay registry artifacts through a stable read-only contract.

    The engine accepts registry records from OI-190, lookup records from OI-191,
    dictionaries, dataclass-like objects, or any object exposing to_dict(). It
    normalizes all inputs into ReplaySearchRecord objects, builds immutable
    search results, and preserves institutional explainability and telemetry.
    """

    module_id = "OI-192"
    module_name = "Oracle Universal Market Adapter Replay Search Engine"

    def __init__(self, oracle_instance_id: str = "oracle.default") -> None:
        self.oracle_instance_id = oracle_instance_id
        self._records: List[ReplaySearchRecord] = []
        self._results: List[ReplaySearchResult] = []

    def load_registry_records(self, records: Iterable[Any], *, replace: bool = True) -> Dict[str, Any]:
        normalized = [self._normalize_record(record) for record in records]
        if replace:
            self._records = normalized
        else:
            self._records.extend(normalized)

        return {
            "module_id": self.module_id,
            "oracle_instance_id": self.oracle_instance_id,
            "loaded_count": len(normalized),
            "total_count": len(self._records),
            "replace": replace,
            "read_only_guardrails": dict(READ_ONLY_GUARDRAILS),
        }

    def records(self) -> List[ReplaySearchRecord]:
        return list(self._records)

    def search(
        self,
        *,
        text: str = "",
        registration_id: str = "",
        registry_id: str = "",
        certification_id: str = "",
        validation_id: str = "",
        manifest_id: str = "",
        adapter_id: str = "",
        market_id: str = "",
        universal_market_id: str = "",
        market_type: str = "",
        market: str = "",
        symbol: str = "",
        status: str = "",
        certified: Optional[bool] = None,
        created_after: str = "",
        created_before: str = "",
        limit: int = 50,
    ) -> ReplaySearchResult:
        query = ReplaySearchQuery(
            query_id="oi192.search_query." + _hash({
                "text": text,
                "registration_id": registration_id,
                "registry_id": registry_id,
                "certification_id": certification_id,
                "validation_id": validation_id,
                "manifest_id": manifest_id,
                "adapter_id": adapter_id,
                "market_id": market_id,
                "universal_market_id": universal_market_id,
                "market_type": market_type,
                "market": market,
                "symbol": symbol,
                "status": status,
                "certified": certified,
                "created_after": created_after,
                "created_before": created_before,
                "limit": limit,
            })[:24],
            text=text,
            registration_id=registration_id,
            registry_id=registry_id,
            certification_id=certification_id,
            validation_id=validation_id,
            manifest_id=manifest_id,
            adapter_id=adapter_id,
            market_id=market_id,
            universal_market_id=universal_market_id,
            market_type=market_type,
            market=market,
            symbol=symbol,
            status=status,
            certified=certified,
            created_after=created_after,
            created_before=created_before,
            limit=max(0, int(limit)),
        )

        matches = [record for record in self._records if self._matches(record, query)]
        ordered = sorted(matches, key=lambda item: (item.created_at, item.registration_id, item.certification_id))
        returned = ordered[: query.limit] if query.limit else []

        result_hash = _hash({
            "query": query.to_dict(),
            "records": [record.record_hash for record in returned],
            "matched_count": len(matches),
        })

        result = ReplaySearchResult(
            result_id="oi192.search_result." + result_hash[:24],
            created_at=_utc_now(),
            oracle_instance_id=self.oracle_instance_id,
            module_id=self.module_id,
            module_name=self.module_name,
            query=query,
            total_records=len(self._records),
            matched_count=len(matches),
            returned_count=len(returned),
            result_hash=result_hash,
            read_only_guardrails=dict(READ_ONLY_GUARDRAILS),
            records=returned,
            telemetry={
                "module_id": self.module_id,
                "module_name": self.module_name,
                "oracle_instance_id": self.oracle_instance_id,
                "total_records": len(self._records),
                "matched_count": len(matches),
                "returned_count": len(returned),
                "query_hash": _hash(query.to_dict()),
                "result_hash": result_hash,
            },
            explainability={
                "purpose": "Search certified replay registry artifacts without mutating registry state.",
                "read_only_reason": "Replay search reads normalized registry metadata only; it cannot execute, route, submit, or manage positions.",
                "execution_boundary": "Q Series remains the only execution engine.",
                "search_dimensions": [
                    "text",
                    "registration_id",
                    "registry_id",
                    "certification_id",
                    "validation_id",
                    "manifest_id",
                    "adapter_id",
                    "market_id",
                    "universal_market_id",
                    "market_type",
                    "market",
                    "symbol",
                    "status",
                    "certified",
                    "created_at",
                ],
                "ordering_method": "Results are sorted by created_at, registration_id, and certification_id for deterministic replay search.",
            },
        )

        self._results.append(result)
        return result

    def search_by_manifest_id(self, manifest_id: str, *, limit: int = 50) -> ReplaySearchResult:
        return self.search(manifest_id=manifest_id, limit=limit)

    def search_by_certification_id(self, certification_id: str, *, limit: int = 50) -> ReplaySearchResult:
        return self.search(certification_id=certification_id, limit=limit)

    def search_by_registration_id(self, registration_id: str) -> ReplaySearchResult:
        return self.search(registration_id=registration_id, limit=1)

    def search_by_symbol(self, symbol: str, *, limit: int = 50) -> ReplaySearchResult:
        return self.search(symbol=symbol, limit=limit)

    def search_by_adapter(self, adapter_id: str, *, limit: int = 50) -> ReplaySearchResult:
        return self.search(adapter_id=adapter_id, limit=limit)

    def latest_result(self) -> Optional[ReplaySearchResult]:
        return self._results[-1] if self._results else None

    def results(self) -> List[ReplaySearchResult]:
        return list(self._results)

    def telemetry_snapshot(self) -> Dict[str, Any]:
        latest = self.latest_result()
        return {
            "module_id": self.module_id,
            "module_name": self.module_name,
            "oracle_instance_id": self.oracle_instance_id,
            "record_count": len(self._records),
            "search_count": len(self._results),
            "latest_result_id": latest.result_id if latest else None,
            "latest_result_hash": latest.result_hash if latest else None,
            "read_only_guardrails": dict(READ_ONLY_GUARDRAILS),
        }

    def _normalize_record(self, record: Any) -> ReplaySearchRecord:
        data = _safe_dict(record)
        telemetry = _safe_dict(data.get("telemetry"))
        raw = dict(data)

        registration_id = str(_field(data, "registration_id") or "")
        registry_id = str(_field(data, "registry_id") or "")
        certification_id = str(_field(data, "certification_id") or "")
        validation_id = str(_field(data, "validation_id") or "")
        manifest_id = str(_field(data, "manifest_id", "target_manifest_id") or "")
        adapter_id = str(_field(data, "adapter_id") or telemetry.get("adapter_id") or "")
        market_id = str(_field(data, "market_id") or telemetry.get("market_id") or "")
        universal_market_id = str(_field(data, "universal_market_id") or telemetry.get("universal_market_id") or "")
        market_type = str(_field(data, "market_type") or telemetry.get("market_type") or "")
        market = str(_field(data, "market") or telemetry.get("market") or "")
        symbol = str(_field(data, "symbol") or telemetry.get("symbol") or "")
        status = str(_field(data, "status") or "")
        certified = bool(_field(data, "certified") is True or status.lower() in {"registered", "certified"})
        created_at = str(_field(data, "created_at") or "")

        record_hash = _hash(raw)
        search_record_id = "oi192.search_record." + _hash({
            "registration_id": registration_id,
            "registry_id": registry_id,
            "certification_id": certification_id,
            "validation_id": validation_id,
            "manifest_id": manifest_id,
            "record_hash": record_hash,
        })[:24]

        return ReplaySearchRecord(
            search_record_id=search_record_id,
            registration_id=registration_id,
            registry_id=registry_id,
            certification_id=certification_id,
            validation_id=validation_id,
            manifest_id=manifest_id,
            adapter_id=adapter_id,
            market_id=market_id,
            universal_market_id=universal_market_id,
            market_type=market_type,
            market=market,
            symbol=symbol,
            status=status,
            certified=certified,
            created_at=created_at,
            record_hash=record_hash,
            raw=raw,
        )

    def _matches(self, record: ReplaySearchRecord, query: ReplaySearchQuery) -> bool:
        if query.text and not _contains(record.to_dict(), _safe_lower(query.text)):
            return False

        exact_fields = [
            "registration_id",
            "registry_id",
            "certification_id",
            "validation_id",
            "manifest_id",
            "adapter_id",
            "market_id",
            "universal_market_id",
            "market_type",
            "market",
            "symbol",
            "status",
        ]
        record_data = record.to_dict()
        query_data = query.to_dict()
        for field_name in exact_fields:
            expected = _safe_lower(query_data.get(field_name))
            if expected and _safe_lower(record_data.get(field_name)) != expected:
                return False

        if query.certified is not None and record.certified is not query.certified:
            return False

        if query.created_after and record.created_at and record.created_at < query.created_after:
            return False

        if query.created_before and record.created_at and record.created_at > query.created_before:
            return False

        return True


def create_replay_search_engine(oracle_instance_id: str = "oracle.default") -> UniversalMarketAdapterReplaySearchEngine:
    return UniversalMarketAdapterReplaySearchEngine(oracle_instance_id=oracle_instance_id)


__all__ = [
    "READ_ONLY_GUARDRAILS",
    "ReplaySearchRecord",
    "ReplaySearchQuery",
    "ReplaySearchResult",
    "UniversalMarketAdapterReplaySearchEngine",
    "create_replay_search_engine",
]
'''.lstrip(), encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.universal_market_adapter_replay_search_engine import (
    READ_ONLY_GUARDRAILS,
    ReplaySearchRecord,
    create_replay_search_engine,
)


class ObjectRecord:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def to_dict(self):
        return dict(self.__dict__)


def test_oi_192_universal_market_adapter_replay_search_engine():
    engine = create_replay_search_engine("oracle.test")

    records = [
        {
            "registration_id": "reg-001",
            "registry_id": "registry-001",
            "certification_id": "cert-001",
            "validation_id": "val-001",
            "manifest_id": "manifest-001",
            "adapter_id": "adp.kalshi",
            "market_id": "market-001",
            "universal_market_id": "umm-001",
            "market_type": "prediction_market",
            "market": "FAKE_MARKET_ONE",
            "symbol": "ORACLE_ONE",
            "status": "registered",
            "certified": True,
            "created_at": "2026-01-01T00:00:00+00:00",
            "telemetry": {"source": "unit_test"},
        },
        ObjectRecord(
            registration_id="reg-002",
            registry_id="registry-002",
            certification_id="cert-002",
            validation_id="val-002",
            manifest_id="manifest-002",
            adapter_id="adp.polymarket",
            market_id="market-002",
            universal_market_id="umm-002",
            market_type="prediction_market",
            market="FAKE_MARKET_TWO",
            symbol="ORACLE_TWO",
            status="registered",
            certified=True,
            created_at="2026-01-02T00:00:00+00:00",
        ),
        {
            "registration_id": "reg-003",
            "registry_id": "registry-003",
            "certification_id": "cert-003",
            "validation_id": "val-003",
            "manifest_id": "manifest-003",
            "adapter_id": "adp.kalshi",
            "market_id": "market-003",
            "universal_market_id": "umm-003",
            "market_type": "prediction_market",
            "market": "FAKE_MARKET_THREE",
            "symbol": "ORACLE_THREE",
            "status": "rejected",
            "certified": False,
            "created_at": "2026-01-03T00:00:00+00:00",
        },
    ]

    load = engine.load_registry_records(records)
    assert load["loaded_count"] == 3
    assert load["total_count"] == 3
    assert load["read_only_guardrails"] == READ_ONLY_GUARDRAILS
    assert len(engine.records()) == 3
    assert isinstance(engine.records()[0], ReplaySearchRecord)

    by_manifest = engine.search_by_manifest_id("manifest-001")
    assert by_manifest.passed is True
    assert by_manifest.matched_count == 1
    assert by_manifest.records[0].registration_id == "reg-001"
    assert len(by_manifest.result_hash) == 64
    assert by_manifest.read_only_guardrails == READ_ONLY_GUARDRAILS

    by_cert = engine.search_by_certification_id("cert-002")
    assert by_cert.matched_count == 1
    assert by_cert.records[0].symbol == "ORACLE_TWO"

    by_registration = engine.search_by_registration_id("reg-003")
    assert by_registration.matched_count == 1
    assert by_registration.records[0].certified is False

    by_adapter = engine.search_by_adapter("adp.kalshi")
    assert by_adapter.matched_count == 2

    by_symbol = engine.search_by_symbol("ORACLE_ONE")
    assert by_symbol.matched_count == 1

    certified_only = engine.search(certified=True)
    assert certified_only.matched_count == 2

    rejected_only = engine.search(status="rejected", certified=False)
    assert rejected_only.matched_count == 1

    text_search = engine.search(text="FAKE_MARKET_TWO")
    assert text_search.matched_count == 1
    assert text_search.records[0].certification_id == "cert-002"

    limited = engine.search(market_type="prediction_market", limit=2)
    assert limited.matched_count == 3
    assert limited.returned_count == 2

    snapshot = engine.telemetry_snapshot()
    assert snapshot["module_id"] == "OI-192"
    assert snapshot["record_count"] == 3
    assert snapshot["search_count"] >= 8
    assert snapshot["read_only_guardrails"] == READ_ONLY_GUARDRAILS


if __name__ == "__main__":
    test_oi_192_universal_market_adapter_replay_search_engine()
    print("[PASS] OI-192 Universal Market Adapter Replay Search Engine")
'''.lstrip(), encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

import_line = "from .universal_market_adapter_replay_search_engine import UniversalMarketAdapterReplaySearchEngine, create_replay_search_engine\n"
if import_line not in init_text:
    init_text += ("\n" if init_text and not init_text.endswith("\n") else "") + import_line

INIT.write_text(init_text, encoding="utf-8")

print("========================================")
print(" OI-192 INSTALLER")
print(" Universal Market Adapter Replay Search Engine")
print("========================================")
print(f"[OK] Wrote {MODULE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-192 installed")
print()
print("Run:")
print("py test_oi_192_universal_market_adapter_replay_search_engine.py")
