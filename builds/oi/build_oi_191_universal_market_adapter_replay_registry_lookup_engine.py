from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

MODULE = PKG / "universal_market_adapter_replay_registry_lookup_engine.py"
TEST = ROOT / "test_oi_191_universal_market_adapter_replay_registry_lookup_engine.py"
INIT = PKG / "__init__.py"

module_code = r'''
"""
OI-191 — Oracle Universal Market Adapter Replay Registry Lookup Engine

Clean rewrite aligned to the canonical OI-189/OI-190 replay certification and
registry contract.

This engine provides read-only lookup over registered certified replay artifacts.
It never executes trades, routes orders, submits orders, manages positions, or
mutates market state. Q Series remains the only execution engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, Iterable, List, Mapping, Optional
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


@dataclass(frozen=True)
class ReplayRegistryLookupEntry:
    registration_id: str
    registry_id: str
    certification_id: str
    validation_id: str
    manifest_id: str
    certification_hash: str
    validation_hash: str
    manifest_hash: str
    chain_hash: str
    registry_hash: str
    adapter_id: str
    market_id: str
    query_id: str
    status: str
    certified: bool
    certification_level: str
    created_at: str
    loaded_at: str
    source_hash: str
    telemetry: Dict[str, Any] = field(default_factory=dict)
    explainability: Dict[str, Any] = field(default_factory=dict)
    read_only_guardrails: Dict[str, Any] = field(default_factory=lambda: dict(READ_ONLY_GUARDRAILS))

    @property
    def passed(self) -> bool:
        return self.certified and self.status in {"registered", "active", "available"}

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["passed"] = self.passed
        return data


@dataclass(frozen=True)
class ReplayRegistryLookupLoadResult:
    lookup_index_id: str
    created_at: str
    oracle_instance_id: str
    module_id: str
    module_name: str
    entry_count: int
    registration_id_count: int
    certification_id_count: int
    manifest_id_count: int
    validation_id_count: int
    adapter_id_count: int
    market_id_count: int
    query_id_count: int
    integrity_hash: str
    read_only_guardrails: Dict[str, Any]
    telemetry: Dict[str, Any]
    explainability: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class UniversalMarketAdapterReplayRegistryLookupEngine:
    """
    Read-only lookup index over OI-190 registered replay artifacts.
    """

    module_id = "OI-191"
    module_name = "Oracle Universal Market Adapter Replay Registry Lookup Engine"

    def __init__(self, oracle_instance_id: str = "oracle.default") -> None:
        self.oracle_instance_id = oracle_instance_id
        self._reset()

    def load_registry_records(self, records: Iterable[Any]) -> ReplayRegistryLookupLoadResult:
        self._reset()
        for record in records or []:
            entry = self._normalize_record(record)
            self._add_entry(entry)
        return self.snapshot()

    def load_from_registry_engine(self, registry_engine: Any) -> ReplayRegistryLookupLoadResult:
        if not hasattr(registry_engine, "records"):
            raise TypeError("registry_engine must expose a records() method")
        return self.load_registry_records(registry_engine.records())

    def lookup_by_registration_id(self, registration_id: str) -> Optional[ReplayRegistryLookupEntry]:
        return self._by_registration_id.get(str(registration_id))

    def lookup_by_registry_id(self, registry_id: str) -> List[ReplayRegistryLookupEntry]:
        return list(self._by_registry_id.get(str(registry_id), []))

    def lookup_by_certification_id(self, certification_id: str) -> List[ReplayRegistryLookupEntry]:
        return list(self._by_certification_id.get(str(certification_id), []))

    def lookup_by_validation_id(self, validation_id: str) -> List[ReplayRegistryLookupEntry]:
        return list(self._by_validation_id.get(str(validation_id), []))

    def lookup_by_manifest_id(self, manifest_id: str) -> List[ReplayRegistryLookupEntry]:
        return list(self._by_manifest_id.get(str(manifest_id), []))

    def lookup_by_adapter_id(self, adapter_id: str) -> List[ReplayRegistryLookupEntry]:
        return list(self._by_adapter_id.get(str(adapter_id), []))

    def lookup_by_market_id(self, market_id: str) -> List[ReplayRegistryLookupEntry]:
        return list(self._by_market_id.get(str(market_id), []))

    def lookup_by_query_id(self, query_id: str) -> List[ReplayRegistryLookupEntry]:
        return list(self._by_query_id.get(str(query_id), []))

    def lookup_by_status(self, status: str) -> List[ReplayRegistryLookupEntry]:
        return list(self._by_status.get(str(status), []))

    def lookup_certified(self) -> List[ReplayRegistryLookupEntry]:
        return [entry for entry in self._entries if entry.certified]

    def lookup_rejected(self) -> List[ReplayRegistryLookupEntry]:
        return [entry for entry in self._entries if not entry.certified]

    def entries(self) -> List[ReplayRegistryLookupEntry]:
        return list(self._entries)

    def snapshot(self) -> ReplayRegistryLookupLoadResult:
        payload = [entry.to_dict() for entry in sorted(self._entries, key=lambda e: e.registration_id)]
        integrity_hash = _hash(payload)
        return ReplayRegistryLookupLoadResult(
            lookup_index_id="oi191.lookup." + integrity_hash[:24],
            created_at=_utc_now(),
            oracle_instance_id=self.oracle_instance_id,
            module_id=self.module_id,
            module_name=self.module_name,
            entry_count=len(self._entries),
            registration_id_count=len(self._by_registration_id),
            certification_id_count=len(self._by_certification_id),
            manifest_id_count=len(self._by_manifest_id),
            validation_id_count=len(self._by_validation_id),
            adapter_id_count=len(self._by_adapter_id),
            market_id_count=len(self._by_market_id),
            query_id_count=len(self._by_query_id),
            integrity_hash=integrity_hash,
            read_only_guardrails=dict(READ_ONLY_GUARDRAILS),
            telemetry={
                "module_id": self.module_id,
                "module_name": self.module_name,
                "oracle_instance_id": self.oracle_instance_id,
                "entry_count": len(self._entries),
                "certified_count": len(self.lookup_certified()),
                "rejected_count": len(self.lookup_rejected()),
                "registration_id_count": len(self._by_registration_id),
            },
            explainability={
                "purpose": "Provide read-only lookup over registered certified replay artifacts.",
                "read_only_reason": "Lookup indexes registry metadata only; it does not execute or mutate markets.",
                "execution_boundary": "Q Series remains the only execution engine.",
                "lookup_dimensions": [
                    "registration_id", "registry_id", "certification_id", "validation_id",
                    "manifest_id", "adapter_id", "market_id", "query_id", "status", "certified",
                ],
                "contract_alignment": "Aligned to OI-189 certification and OI-190 registry records.",
            },
        )

    def telemetry_snapshot(self) -> Dict[str, Any]:
        snap = self.snapshot()
        return {
            "module_id": snap.module_id,
            "module_name": snap.module_name,
            "oracle_instance_id": snap.oracle_instance_id,
            "entry_count": snap.entry_count,
            "certified_count": snap.telemetry["certified_count"],
            "rejected_count": snap.telemetry["rejected_count"],
            "integrity_hash": snap.integrity_hash,
            "read_only_guardrails": dict(READ_ONLY_GUARDRAILS),
        }

    def replay_lookup_manifest(self) -> Dict[str, Any]:
        snap = self.snapshot()
        return {
            "module_id": self.module_id,
            "oracle_instance_id": self.oracle_instance_id,
            "lookup_index_id": snap.lookup_index_id,
            "integrity_hash": snap.integrity_hash,
            "entry_count": snap.entry_count,
            "entries": [entry.to_dict() for entry in self._entries],
            "read_only_guardrails": dict(READ_ONLY_GUARDRAILS),
        }

    def _reset(self) -> None:
        self._entries: List[ReplayRegistryLookupEntry] = []
        self._by_registration_id: Dict[str, ReplayRegistryLookupEntry] = {}
        self._by_registry_id: Dict[str, List[ReplayRegistryLookupEntry]] = {}
        self._by_certification_id: Dict[str, List[ReplayRegistryLookupEntry]] = {}
        self._by_validation_id: Dict[str, List[ReplayRegistryLookupEntry]] = {}
        self._by_manifest_id: Dict[str, List[ReplayRegistryLookupEntry]] = {}
        self._by_adapter_id: Dict[str, List[ReplayRegistryLookupEntry]] = {}
        self._by_market_id: Dict[str, List[ReplayRegistryLookupEntry]] = {}
        self._by_query_id: Dict[str, List[ReplayRegistryLookupEntry]] = {}
        self._by_status: Dict[str, List[ReplayRegistryLookupEntry]] = {}

    def _normalize_record(self, record: Any) -> ReplayRegistryLookupEntry:
        data = _safe_dict(record)
        telemetry = _safe_dict(data.get("telemetry"))
        explainability = _safe_dict(data.get("explainability"))
        registration_id = str(data.get("registration_id") or data.get("registry_entry_id") or "")
        if not registration_id:
            registration_id = "oi190.registration." + _hash(data)[:24]
        registry_id = str(data.get("registry_id") or telemetry.get("registry_id") or "oi190.registry.default")
        certification_id = str(data.get("certification_id") or telemetry.get("certification_id") or "")
        validation_id = str(data.get("validation_id") or telemetry.get("validation_id") or "")
        manifest_id = str(data.get("manifest_id") or telemetry.get("manifest_id") or "")
        adapter_id = str(data.get("adapter_id") or telemetry.get("adapter_id") or "unknown.adapter")
        market_id = str(data.get("market_id") or data.get("universal_market_id") or telemetry.get("market_id") or telemetry.get("universal_market_id") or "unknown.market")
        query_id = str(data.get("query_id") or telemetry.get("query_id") or "unknown.query")
        certified = bool(data.get("certified") is True or data.get("passed") is True)
        status = str(data.get("status") or ("registered" if certified else "rejected"))
        certification_level = str(data.get("certification_level") or telemetry.get("certification_level") or ("certified" if certified else "not_certified"))
        return ReplayRegistryLookupEntry(
            registration_id=registration_id,
            registry_id=registry_id,
            certification_id=certification_id,
            validation_id=validation_id,
            manifest_id=manifest_id,
            certification_hash=str(data.get("certification_hash") or telemetry.get("certification_hash") or ""),
            validation_hash=str(data.get("validation_hash") or telemetry.get("validation_hash") or ""),
            manifest_hash=str(data.get("manifest_hash") or telemetry.get("manifest_hash") or ""),
            chain_hash=str(data.get("chain_hash") or telemetry.get("chain_hash") or ""),
            registry_hash=str(data.get("registry_hash") or telemetry.get("registry_hash") or _hash(data)),
            adapter_id=adapter_id,
            market_id=market_id,
            query_id=query_id,
            status=status,
            certified=certified,
            certification_level=certification_level,
            created_at=str(data.get("created_at") or telemetry.get("created_at") or ""),
            loaded_at=_utc_now(),
            source_hash=_hash(data),
            telemetry=telemetry,
            explainability=explainability,
            read_only_guardrails=dict(READ_ONLY_GUARDRAILS),
        )

    def _add_entry(self, entry: ReplayRegistryLookupEntry) -> None:
        self._entries.append(entry)
        self._by_registration_id[entry.registration_id] = entry
        self._by_registry_id.setdefault(entry.registry_id, []).append(entry)
        self._by_certification_id.setdefault(entry.certification_id, []).append(entry)
        self._by_validation_id.setdefault(entry.validation_id, []).append(entry)
        self._by_manifest_id.setdefault(entry.manifest_id, []).append(entry)
        self._by_adapter_id.setdefault(entry.adapter_id, []).append(entry)
        self._by_market_id.setdefault(entry.market_id, []).append(entry)
        self._by_query_id.setdefault(entry.query_id, []).append(entry)
        self._by_status.setdefault(entry.status, []).append(entry)


def create_replay_registry_lookup_engine(
    oracle_instance_id: str = "oracle.default",
) -> UniversalMarketAdapterReplayRegistryLookupEngine:
    return UniversalMarketAdapterReplayRegistryLookupEngine(oracle_instance_id=oracle_instance_id)


__all__ = [
    "READ_ONLY_GUARDRAILS",
    "ReplayRegistryLookupEntry",
    "ReplayRegistryLookupLoadResult",
    "UniversalMarketAdapterReplayRegistryLookupEngine",
    "create_replay_registry_lookup_engine",
]
'''

MODULE.write_text(module_code.lstrip(), encoding="utf-8")

test_code = r'''
from qseries_v2.oracle_intelligence.universal_market_adapter_replay_registry_lookup_engine import (
    READ_ONLY_GUARDRAILS,
    ReplayRegistryLookupEntry,
    ReplayRegistryLookupLoadResult,
    UniversalMarketAdapterReplayRegistryLookupEngine,
    create_replay_registry_lookup_engine,
)


def test_oi_191_replay_registry_lookup_engine():
    engine = create_replay_registry_lookup_engine("oracle.test")
    records = [
        {
            "registration_id": "reg-001", "registry_id": "registry-main", "certification_id": "cert-001",
            "validation_id": "val-001", "manifest_id": "manifest-001", "certification_hash": "a" * 64,
            "validation_hash": "b" * 64, "manifest_hash": "c" * 64, "chain_hash": "d" * 64,
            "registry_hash": "e" * 64, "adapter_id": "adp.kalshi", "market_id": "umm.market.001",
            "query_id": "query-001", "status": "registered", "certified": True,
            "certification_level": "certified", "telemetry": {"source": "unit_test"},
        },
        {
            "registration_id": "reg-002", "registry_id": "registry-main", "certification_id": "cert-002",
            "validation_id": "val-002", "manifest_id": "manifest-002", "adapter_id": "adp.kalshi",
            "market_id": "umm.market.002", "query_id": "query-002", "status": "registered",
            "certified": True, "certification_level": "certified_with_warnings",
        },
        {
            "registration_id": "reg-003", "registry_id": "registry-main", "certification_id": "cert-003",
            "validation_id": "val-003", "manifest_id": "manifest-003", "adapter_id": "adp.polymarket",
            "market_id": "umm.market.003", "query_id": "query-003", "status": "rejected",
            "certified": False, "certification_level": "not_certified",
        },
    ]
    load = engine.load_registry_records(records)
    assert isinstance(load, ReplayRegistryLookupLoadResult)
    assert load.module_id == "OI-191"
    assert load.entry_count == 3
    assert load.registration_id_count == 3
    assert load.certification_id_count == 3
    assert load.manifest_id_count == 3
    assert load.validation_id_count == 3
    assert load.adapter_id_count == 2
    assert load.market_id_count == 3
    assert load.query_id_count == 3
    assert len(load.integrity_hash) == 64
    assert load.read_only_guardrails == READ_ONLY_GUARDRAILS
    reg = engine.lookup_by_registration_id("reg-001")
    assert isinstance(reg, ReplayRegistryLookupEntry)
    assert reg.certification_id == "cert-001"
    assert reg.passed is True
    assert len(engine.lookup_by_registry_id("registry-main")) == 3
    assert len(engine.lookup_by_certification_id("cert-002")) == 1
    assert len(engine.lookup_by_validation_id("val-002")) == 1
    assert len(engine.lookup_by_manifest_id("manifest-003")) == 1
    assert len(engine.lookup_by_adapter_id("adp.kalshi")) == 2
    assert len(engine.lookup_by_adapter_id("adp.polymarket")) == 1
    assert len(engine.lookup_by_market_id("umm.market.002")) == 1
    assert len(engine.lookup_by_query_id("query-003")) == 1
    assert len(engine.lookup_by_status("registered")) == 2
    assert len(engine.lookup_by_status("rejected")) == 1
    assert len(engine.lookup_certified()) == 2
    assert len(engine.lookup_rejected()) == 1
    snapshot = engine.snapshot()
    assert snapshot.entry_count == 3
    assert snapshot.telemetry["certified_count"] == 2
    assert snapshot.telemetry["rejected_count"] == 1
    telemetry = engine.telemetry_snapshot()
    assert telemetry["entry_count"] == 3
    assert telemetry["certified_count"] == 2
    assert telemetry["read_only_guardrails"] == READ_ONLY_GUARDRAILS
    manifest = engine.replay_lookup_manifest()
    assert manifest["module_id"] == "OI-191"
    assert manifest["entry_count"] == 3
    assert len(manifest["entries"]) == 3

    class RegistryLike:
        def records(self):
            return records

    engine2 = UniversalMarketAdapterReplayRegistryLookupEngine("oracle.test2")
    load2 = engine2.load_from_registry_engine(RegistryLike())
    assert load2.entry_count == 3
    assert engine2.lookup_by_registration_id("reg-001").certification_id == "cert-001"


if __name__ == "__main__":
    test_oi_191_replay_registry_lookup_engine()
    print("[PASS] OI-191 Universal Market Adapter Replay Registry Lookup Engine")
'''

TEST.write_text(test_code.lstrip(), encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

import_line = "from .universal_market_adapter_replay_registry_lookup_engine import UniversalMarketAdapterReplayRegistryLookupEngine, create_replay_registry_lookup_engine\n"
if import_line not in init_text:
    init_text += ("\n" if init_text and not init_text.endswith("\n") else "") + import_line
INIT.write_text(init_text, encoding="utf-8")

print("========================================")
print(" OI-191 INSTALLER")
print(" Universal Market Adapter Replay Registry Lookup Engine")
print("========================================")
print(f"[OK] Wrote {MODULE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-191 installed")
print()
print("Run:")
print("py test_oi_191_universal_market_adapter_replay_registry_lookup_engine.py")
