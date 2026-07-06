from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

MODULE = PKG / "universal_market_adapter_replay_registry_engine.py"
TEST = ROOT / "test_oi_190_universal_market_adapter_replay_registry_engine.py"
INIT = PKG / "__init__.py"

MODULE.write_text(r'''
"""
OI-190 — Oracle Universal Market Adapter Replay Registry Engine

Clean integration-refactor rewrite.

Registers certified replay artifacts produced by OI-189 using one canonical
contract. Oracle remains read-only. Q Series remains the only execution engine.
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
class ReplayRegistryFinding:
    code: str
    severity: str
    message: str
    evidence: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReplayRegistryRecord:
    registration_id: str
    created_at: str
    oracle_instance_id: str
    module_id: str
    module_name: str
    certification_id: str
    certification_hash: str
    certification_level: str
    validation_id: str
    validation_hash: str
    manifest_id: str
    manifest_hash: str
    chain_hash: str
    entry_count: int
    certified: bool
    registered: bool
    registry_status: str
    registry_hash: str
    replay_artifact_key: str
    read_only_guardrails: Dict[str, Any]
    findings: List[ReplayRegistryFinding]
    telemetry: Dict[str, Any]
    explainability: Dict[str, Any]

    @property
    def passed(self) -> bool:
        return self.registered and not any(f.severity in {"critical", "error"} for f in self.findings)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["passed"] = self.passed
        return data


@dataclass(frozen=True)
class ReplayRegistrySnapshot:
    module_id: str
    module_name: str
    oracle_instance_id: str
    record_count: int
    registered_count: int
    rejected_count: int
    certified_count: int
    manifest_count: int
    certification_count: int
    validation_count: int
    registry_integrity_hash: str
    read_only_guardrails: Dict[str, Any]
    telemetry: Dict[str, Any]
    explainability: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class UniversalMarketAdapterReplayRegistryEngine:
    """Read-only registry for canonical OI-189 replay certification records."""

    module_id = "OI-190"
    module_name = "Oracle Universal Market Adapter Replay Registry Engine"

    def __init__(self, oracle_instance_id: str = "oracle.default") -> None:
        self.oracle_instance_id = oracle_instance_id
        self._records: List[ReplayRegistryRecord] = []
        self._by_registration_id: Dict[str, ReplayRegistryRecord] = {}
        self._by_certification_id: Dict[str, List[ReplayRegistryRecord]] = {}
        self._by_manifest_id: Dict[str, List[ReplayRegistryRecord]] = {}
        self._by_validation_id: Dict[str, List[ReplayRegistryRecord]] = {}
        self._by_artifact_key: Dict[str, ReplayRegistryRecord] = {}

    def register_certification(self, certification: Any, *, registry_context: Optional[Mapping[str, Any]] = None, **_: Any) -> ReplayRegistryRecord:
        cert = _safe_dict(certification)
        context = _safe_dict(registry_context)
        findings = self._evaluate_certification(cert)

        certification_id = str(cert.get("certification_id") or "")
        certification_hash = str(cert.get("certification_hash") or "")
        certification_level = str(cert.get("certification_level") or "unknown")
        validation_id = str(cert.get("validation_id") or "")
        validation_hash = str(cert.get("validation_hash") or "")
        manifest_id = str(cert.get("manifest_id") or "")
        manifest_hash = str(cert.get("manifest_hash") or "")
        chain_hash = str(cert.get("chain_hash") or "")
        entry_count = int(cert.get("entry_count") or 0)
        certified = bool(cert.get("certified") is True)

        blocker_count = sum(1 for f in findings if f.severity in {"critical", "error"})
        registered = certified and blocker_count == 0
        registry_status = "registered" if registered else "rejected"

        replay_artifact_key = _hash({
            "certification_id": certification_id,
            "validation_id": validation_id,
            "manifest_id": manifest_id,
            "manifest_hash": manifest_hash,
            "chain_hash": chain_hash,
        })
        registry_hash = _hash({
            "oracle_instance_id": self.oracle_instance_id,
            "certification_id": certification_id,
            "certification_hash": certification_hash,
            "certification_level": certification_level,
            "validation_id": validation_id,
            "validation_hash": validation_hash,
            "manifest_id": manifest_id,
            "manifest_hash": manifest_hash,
            "chain_hash": chain_hash,
            "entry_count": entry_count,
            "certified": certified,
            "registered": registered,
            "registry_status": registry_status,
            "findings": [f.to_dict() for f in findings],
            "context": context,
        })

        record = ReplayRegistryRecord(
            registration_id="oi190.registration." + registry_hash[:24],
            created_at=_utc_now(),
            oracle_instance_id=self.oracle_instance_id,
            module_id=self.module_id,
            module_name=self.module_name,
            certification_id=certification_id,
            certification_hash=certification_hash,
            certification_level=certification_level,
            validation_id=validation_id,
            validation_hash=validation_hash,
            manifest_id=manifest_id,
            manifest_hash=manifest_hash,
            chain_hash=chain_hash,
            entry_count=entry_count,
            certified=certified,
            registered=registered,
            registry_status=registry_status,
            registry_hash=registry_hash,
            replay_artifact_key=replay_artifact_key,
            read_only_guardrails=dict(READ_ONLY_GUARDRAILS),
            findings=findings,
            telemetry={
                "module_id": self.module_id,
                "oracle_instance_id": self.oracle_instance_id,
                "registration_id": "oi190.registration." + registry_hash[:24],
                "certification_id": certification_id,
                "validation_id": validation_id,
                "manifest_id": manifest_id,
                "entry_count": entry_count,
                "certified": certified,
                "registered": registered,
                "registry_status": registry_status,
                "finding_count": len(findings),
                "blocker_count": blocker_count,
            },
            explainability={
                "purpose": "Register certified replay artifacts for institutional lookup and replay governance.",
                "read_only_reason": "Registry stores replay metadata only and cannot execute, route, submit, or manage trades.",
                "execution_boundary": "Q Series remains the only execution engine.",
            },
        )
        self._upsert(record)
        return record

    def register_many(self, certifications: Iterable[Any], *, registry_context: Optional[Mapping[str, Any]] = None) -> List[ReplayRegistryRecord]:
        return [self.register_certification(c, registry_context=registry_context) for c in certifications]

    def records(self) -> List[ReplayRegistryRecord]:
        return list(self._records)

    def lookup_by_registration_id(self, registration_id: str) -> Optional[ReplayRegistryRecord]:
        return self._by_registration_id.get(str(registration_id))

    def lookup_by_certification_id(self, certification_id: str) -> List[ReplayRegistryRecord]:
        return list(self._by_certification_id.get(str(certification_id), []))

    def lookup_by_manifest_id(self, manifest_id: str) -> List[ReplayRegistryRecord]:
        return list(self._by_manifest_id.get(str(manifest_id), []))

    def lookup_by_validation_id(self, validation_id: str) -> List[ReplayRegistryRecord]:
        return list(self._by_validation_id.get(str(validation_id), []))

    def lookup_by_artifact_key(self, replay_artifact_key: str) -> Optional[ReplayRegistryRecord]:
        return self._by_artifact_key.get(str(replay_artifact_key))

    def snapshot(self) -> ReplayRegistrySnapshot:
        records = self.records()
        registered_count = sum(1 for r in records if r.registered)
        certified_count = sum(1 for r in records if r.certified)
        rejected_count = len(records) - registered_count
        integrity_hash = _hash([
            {
                "registration_id": r.registration_id,
                "certification_id": r.certification_id,
                "validation_id": r.validation_id,
                "manifest_id": r.manifest_id,
                "registry_hash": r.registry_hash,
                "registered": r.registered,
            }
            for r in sorted(records, key=lambda item: item.registration_id)
        ])
        return ReplayRegistrySnapshot(
            module_id=self.module_id,
            module_name=self.module_name,
            oracle_instance_id=self.oracle_instance_id,
            record_count=len(records),
            registered_count=registered_count,
            rejected_count=rejected_count,
            certified_count=certified_count,
            manifest_count=len(self._by_manifest_id),
            certification_count=len(self._by_certification_id),
            validation_count=len(self._by_validation_id),
            registry_integrity_hash=integrity_hash,
            read_only_guardrails=dict(READ_ONLY_GUARDRAILS),
            telemetry={
                "record_count": len(records),
                "registered_count": registered_count,
                "rejected_count": rejected_count,
                "certified_count": certified_count,
                "latest_registration_id": records[-1].registration_id if records else None,
            },
            explainability={
                "purpose": "Summarize replay registry state for institutional audit and lookup readiness.",
                "integrity_method": "Deterministic SHA-256 over sorted registry records.",
                "execution_boundary": "Q Series remains the only execution engine.",
            },
        )

    def replay_registry_manifest(self) -> Dict[str, Any]:
        snap = self.snapshot()
        return {
            "module_id": self.module_id,
            "module_name": self.module_name,
            "oracle_instance_id": self.oracle_instance_id,
            "registry_integrity_hash": snap.registry_integrity_hash,
            "record_count": snap.record_count,
            "records": [r.to_dict() for r in self.records()],
            "read_only_guardrails": dict(READ_ONLY_GUARDRAILS),
        }

    def telemetry_snapshot(self) -> Dict[str, Any]:
        snap = self.snapshot()
        return {
            "module_id": self.module_id,
            "module_name": self.module_name,
            "oracle_instance_id": self.oracle_instance_id,
            "record_count": snap.record_count,
            "registered_count": snap.registered_count,
            "rejected_count": snap.rejected_count,
            "certified_count": snap.certified_count,
            "registry_integrity_hash": snap.registry_integrity_hash,
            "read_only_guardrails": dict(READ_ONLY_GUARDRAILS),
        }

    def _upsert(self, record: ReplayRegistryRecord) -> None:
        existing = self._by_registration_id.get(record.registration_id)
        if existing is not None:
            self._remove(existing)
        self._records.append(record)
        self._by_registration_id[record.registration_id] = record
        self._by_artifact_key[record.replay_artifact_key] = record
        self._by_certification_id.setdefault(record.certification_id, []).append(record)
        self._by_manifest_id.setdefault(record.manifest_id, []).append(record)
        self._by_validation_id.setdefault(record.validation_id, []).append(record)

    def _remove(self, record: ReplayRegistryRecord) -> None:
        self._records = [r for r in self._records if r.registration_id != record.registration_id]
        self._by_registration_id.pop(record.registration_id, None)
        self._by_artifact_key.pop(record.replay_artifact_key, None)
        for index, key in ((self._by_certification_id, record.certification_id), (self._by_manifest_id, record.manifest_id), (self._by_validation_id, record.validation_id)):
            if key in index:
                index[key] = [r for r in index[key] if r.registration_id != record.registration_id]
                if not index[key]:
                    del index[key]

    def _evaluate_certification(self, cert: Dict[str, Any]) -> List[ReplayRegistryFinding]:
        findings: List[ReplayRegistryFinding] = []
        required = ["certification_id", "certification_hash", "validation_id", "validation_hash", "manifest_id", "manifest_hash", "chain_hash", "certified", "certification_level"]
        missing = [field for field in required if cert.get(field) in (None, "")]
        if missing:
            findings.append(ReplayRegistryFinding("CERTIFICATION_FIELDS_MISSING", "error", "Certification record is missing required registry fields.", {"missing": missing}))
        if cert.get("certified") is not True:
            findings.append(ReplayRegistryFinding("CERTIFICATION_NOT_APPROVED", "critical", "Only certified replay artifacts can be registered as active registry records.", {"certified": cert.get("certified")}))
        for field_name in ("certification_hash", "validation_hash", "manifest_hash", "chain_hash"):
            value = str(cert.get(field_name) or "")
            if value and len(value) != 64:
                findings.append(ReplayRegistryFinding("HASH_SHAPE_INVALID", "error", "Registry hash fields must be 64-character SHA-256 digests.", {"field": field_name, "value": value}))
        guardrails = _safe_dict(cert.get("read_only_guardrails"))
        if guardrails:
            for key, expected in READ_ONLY_GUARDRAILS.items():
                if guardrails.get(key) != expected:
                    findings.append(ReplayRegistryFinding("READ_ONLY_GUARDRAIL_MISMATCH", "critical", "Certification guardrails do not preserve Oracle read-only boundaries.", {"key": key, "expected": expected, "actual": guardrails.get(key)}))
        return findings


def create_replay_registry_engine(oracle_instance_id: str = "oracle.default") -> UniversalMarketAdapterReplayRegistryEngine:
    return UniversalMarketAdapterReplayRegistryEngine(oracle_instance_id=oracle_instance_id)


__all__ = [
    "READ_ONLY_GUARDRAILS",
    "ReplayRegistryFinding",
    "ReplayRegistryRecord",
    "ReplayRegistrySnapshot",
    "UniversalMarketAdapterReplayRegistryEngine",
    "create_replay_registry_engine",
]
'''.lstrip(), encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.universal_market_adapter_replay_registry_engine import (
    READ_ONLY_GUARDRAILS,
    create_replay_registry_engine,
)


def _certification(certified=True, suffix="001"):
    return {
        "certification_id": f"oi189.certification.{suffix}",
        "certification_hash": "a" * 64,
        "certification_level": "certified" if certified else "not_certified",
        "certified": certified,
        "validation_id": f"oi188.validation.{suffix}",
        "validation_hash": "b" * 64,
        "manifest_id": f"oi187.manifest.{suffix}",
        "manifest_hash": "c" * 64,
        "chain_hash": "d" * 64,
        "entry_count": 2,
        "read_only_guardrails": READ_ONLY_GUARDRAILS,
    }


def test_oi_190_universal_market_adapter_replay_registry_engine():
    engine = create_replay_registry_engine("oracle.test")
    record = engine.register_certification(_certification(True, "001"))

    assert record.module_id == "OI-190"
    assert record.certified is True
    assert record.registered is True
    assert record.passed is True
    assert record.registry_status == "registered"
    assert record.certification_id == "oi189.certification.001"
    assert record.validation_id == "oi188.validation.001"
    assert record.manifest_id == "oi187.manifest.001"
    assert len(record.registry_hash) == 64
    assert len(record.replay_artifact_key) == 64
    assert record.read_only_guardrails == READ_ONLY_GUARDRAILS

    assert engine.lookup_by_registration_id(record.registration_id).registration_id == record.registration_id
    assert len(engine.lookup_by_certification_id("oi189.certification.001")) == 1
    assert len(engine.lookup_by_validation_id("oi188.validation.001")) == 1
    assert len(engine.lookup_by_manifest_id("oi187.manifest.001")) == 1
    assert engine.lookup_by_artifact_key(record.replay_artifact_key).registration_id == record.registration_id

    rejected = engine.register_certification(_certification(False, "002"))
    assert rejected.certified is False
    assert rejected.registered is False
    assert rejected.passed is False
    assert any(f.code == "CERTIFICATION_NOT_APPROVED" for f in rejected.findings)

    batch = engine.register_many([_certification(True, "003"), _certification(True, "004")])
    assert len(batch) == 2

    snapshot = engine.snapshot()
    assert snapshot.module_id == "OI-190"
    assert snapshot.record_count == 4
    assert snapshot.registered_count == 3
    assert snapshot.rejected_count == 1
    assert snapshot.certified_count == 3
    assert snapshot.certification_count == 4
    assert snapshot.manifest_count == 4
    assert snapshot.validation_count == 4
    assert len(snapshot.registry_integrity_hash) == 64

    telemetry = engine.telemetry_snapshot()
    assert telemetry["record_count"] == 4
    assert telemetry["registered_count"] == 3
    assert telemetry["read_only_guardrails"] == READ_ONLY_GUARDRAILS

    manifest = engine.replay_registry_manifest()
    assert manifest["module_id"] == "OI-190"
    assert manifest["record_count"] == 4
    assert len(manifest["records"]) == 4


if __name__ == "__main__":
    test_oi_190_universal_market_adapter_replay_registry_engine()
    print("[PASS] OI-190 Universal Market Adapter Replay Registry Engine")
'''.lstrip(), encoding="utf-8")

init_text = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
import_line = "from .universal_market_adapter_replay_registry_engine import UniversalMarketAdapterReplayRegistryEngine, create_replay_registry_engine\n"
if import_line not in init_text:
    init_text += ("\n" if init_text and not init_text.endswith("\n") else "") + import_line
INIT.write_text(init_text, encoding="utf-8")

print("========================================")
print(" OI-190 INSTALLER")
print(" Universal Market Adapter Replay Registry Engine")
print("========================================")
print(f"[OK] Wrote {MODULE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-190 installed")
print()
print("Run:")
print("py test_oi_190_universal_market_adapter_replay_registry_engine.py")
