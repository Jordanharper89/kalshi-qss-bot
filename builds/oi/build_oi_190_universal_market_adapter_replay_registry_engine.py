from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

MODULE = PKG / "universal_market_adapter_replay_registry_engine.py"
TEST = ROOT / "test_oi_190_universal_market_adapter_replay_registry_engine.py"
INIT = PKG / "__init__.py"

module_code = r'''
"""
OI-190 — Oracle Universal Market Adapter Replay Registry Engine

Read-only institutional registry for certified Universal Market Adapter replay
artifacts.

This engine registers replay manifests, replay validation results, and replay
certification artifacts into an immutable in-memory registry view suitable for
lookup, telemetry, replay lineage, explainability, and architecture governance.

Oracle remains read-only. This module never executes trades, routes orders,
submits orders, manages positions, or mutates market/execution state. Q Series
remains the only execution engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, Iterable, List, Mapping, Optional
import json
import uuid


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


def _safe_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, tuple):
        return list(value)
    return [value]


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
    registry_id: str
    registered_at: str
    artifact_type: str
    artifact_id: str
    manifest_id: str
    manifest_hash: str
    certification_id: str
    certification_hash: str
    validation_id: str
    validation_hash: str
    adapter_ids: List[str]
    query_ids: List[str]
    replay_keys: List[str]
    entry_count: int
    certified: bool
    passed: bool
    source_hash: str
    lineage_hash: str
    registry_hash: str
    read_only_guardrails: Dict[str, Any]
    telemetry: Dict[str, Any]
    explainability: Dict[str, Any]
    findings: List[ReplayRegistryFinding]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReplayRegistrySnapshot:
    snapshot_id: str
    created_at: str
    module_id: str
    module_name: str
    oracle_instance_id: str
    record_count: int
    certified_count: int
    failed_count: int
    adapter_count: int
    query_count: int
    replay_key_count: int
    registry_integrity_hash: str
    read_only_guardrails: Dict[str, Any]
    telemetry: Dict[str, Any]
    explainability: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class UniversalMarketAdapterReplayRegistryEngine:
    """
    Registers certified replay artifacts into a read-only Oracle registry.

    The registry is an institutional lookup and telemetry layer. It is not an
    execution router and cannot create orders or positions.
    """

    module_id = "OI-190"
    module_name = "Oracle Universal Market Adapter Replay Registry Engine"

    def __init__(self, oracle_instance_id: str = "oracle.default") -> None:
        self.oracle_instance_id = oracle_instance_id
        self._records: Dict[str, ReplayRegistryRecord] = {}
        self._by_manifest_id: Dict[str, str] = {}
        self._by_certification_id: Dict[str, str] = {}
        self._by_validation_id: Dict[str, str] = {}
        self._by_adapter_id: Dict[str, List[str]] = {}
        self._by_query_id: Dict[str, List[str]] = {}
        self._by_replay_key: Dict[str, List[str]] = {}

    def register_certified_replay(
        self,
        *,
        certification: Any,
        manifest: Optional[Any] = None,
        validation: Optional[Any] = None,
        context: Optional[Mapping[str, Any]] = None,
    ) -> ReplayRegistryRecord:
        cert = _safe_dict(certification)
        manifest_data = _safe_dict(manifest)
        validation_data = _safe_dict(validation)
        context_data = _safe_dict(context)

        merged = self._merge_artifact_data(cert, manifest_data, validation_data)
        findings = self._evaluate_registration(cert, manifest_data, validation_data, context_data)

        manifest_id = str(merged.get("manifest_id") or "")
        manifest_hash = str(merged.get("manifest_hash") or "")
        certification_id = str(cert.get("certification_id") or cert.get("certificate_id") or "")
        certification_hash = str(cert.get("certification_hash") or cert.get("certificate_hash") or "")
        validation_id = str(merged.get("validation_id") or "")
        validation_hash = str(merged.get("validation_hash") or "")

        entries = self._extract_entries(merged)
        adapter_ids = sorted({str(entry.get("adapter_id")) for entry in entries if entry.get("adapter_id")})
        query_ids = sorted({str(entry.get("query_id")) for entry in entries if entry.get("query_id")})
        replay_keys = sorted({str(entry.get("replay_key")) for entry in entries if entry.get("replay_key")})

        certified = bool(cert.get("certified", cert.get("passed", False)))
        passed = certified and not any(f.severity in {"error", "critical"} for f in findings)

        artifact_id = certification_id or manifest_id or validation_id or "artifact." + uuid.uuid4().hex
        source_hash = _hash({"certification": cert, "manifest": manifest_data, "validation": validation_data, "context": context_data})
        lineage_payload = {
            "manifest_id": manifest_id,
            "manifest_hash": manifest_hash,
            "certification_id": certification_id,
            "certification_hash": certification_hash,
            "validation_id": validation_id,
            "validation_hash": validation_hash,
            "adapter_ids": adapter_ids,
            "query_ids": query_ids,
            "replay_keys": replay_keys,
        }
        lineage_hash = _hash(lineage_payload)
        registry_hash = _hash({"artifact_id": artifact_id, "source_hash": source_hash, "lineage_hash": lineage_hash})
        registry_id = "oi190.registry." + registry_hash[:24]

        record = ReplayRegistryRecord(
            registry_id=registry_id,
            registered_at=_utc_now(),
            artifact_type="certified_replay",
            artifact_id=str(artifact_id),
            manifest_id=manifest_id,
            manifest_hash=manifest_hash,
            certification_id=certification_id,
            certification_hash=certification_hash,
            validation_id=validation_id,
            validation_hash=validation_hash,
            adapter_ids=adapter_ids,
            query_ids=query_ids,
            replay_keys=replay_keys,
            entry_count=len(entries),
            certified=certified,
            passed=passed,
            source_hash=source_hash,
            lineage_hash=lineage_hash,
            registry_hash=registry_hash,
            read_only_guardrails=dict(READ_ONLY_GUARDRAILS),
            telemetry={
                "oracle_instance_id": self.oracle_instance_id,
                "module_id": self.module_id,
                "module_name": self.module_name,
                "artifact_type": "certified_replay",
                "artifact_id": str(artifact_id),
                "entry_count": len(entries),
                "adapter_count": len(adapter_ids),
                "query_count": len(query_ids),
                "replay_key_count": len(replay_keys),
                "finding_count": len(findings),
                "critical_or_error_count": sum(1 for f in findings if f.severity in {"critical", "error"}),
                "certified": certified,
                "passed": passed,
            },
            explainability={
                "purpose": "Register certified replay artifacts for institutional lookup, lineage, telemetry, and governance.",
                "read_only_reason": "The registry records replay metadata only and does not create execution authority.",
                "execution_boundary": "Q Series remains the only execution engine.",
                "lineage_method": "Registry lineage hash is built from manifest, validation, certification, adapters, queries, and replay keys.",
                "integrity_method": "Registry hash is a deterministic SHA-256 hash over source and lineage hashes.",
                "universal_market_model_compatibility": "Replay registry preserves replay keys, adapter ids, query ids, and manifest hashes without mutating market state.",
            },
            findings=findings,
        )

        self._upsert(record)
        return record

    def register_many(self, artifacts: Iterable[Mapping[str, Any]]) -> List[ReplayRegistryRecord]:
        records: List[ReplayRegistryRecord] = []
        for artifact in artifacts:
            data = _safe_dict(artifact)
            records.append(self.register_certified_replay(
                certification=data.get("certification", data),
                manifest=data.get("manifest"),
                validation=data.get("validation"),
                context=data.get("context"),
            ))
        return records

    def lookup_by_registry_id(self, registry_id: str) -> Optional[ReplayRegistryRecord]:
        return self._records.get(str(registry_id))

    def lookup_by_manifest_id(self, manifest_id: str) -> Optional[ReplayRegistryRecord]:
        registry_id = self._by_manifest_id.get(str(manifest_id))
        return self._records.get(registry_id) if registry_id else None

    def lookup_by_certification_id(self, certification_id: str) -> Optional[ReplayRegistryRecord]:
        registry_id = self._by_certification_id.get(str(certification_id))
        return self._records.get(registry_id) if registry_id else None

    def lookup_by_validation_id(self, validation_id: str) -> Optional[ReplayRegistryRecord]:
        registry_id = self._by_validation_id.get(str(validation_id))
        return self._records.get(registry_id) if registry_id else None

    def lookup_by_adapter_id(self, adapter_id: str) -> List[ReplayRegistryRecord]:
        return [self._records[rid] for rid in self._by_adapter_id.get(str(adapter_id), [])]

    def lookup_by_query_id(self, query_id: str) -> List[ReplayRegistryRecord]:
        return [self._records[rid] for rid in self._by_query_id.get(str(query_id), [])]

    def lookup_by_replay_key(self, replay_key: str) -> List[ReplayRegistryRecord]:
        return [self._records[rid] for rid in self._by_replay_key.get(str(replay_key), [])]

    def records(self) -> List[ReplayRegistryRecord]:
        return list(self._records.values())

    def snapshot(self) -> ReplayRegistrySnapshot:
        records = self.records()
        certified_count = sum(1 for record in records if record.certified)
        failed_count = sum(1 for record in records if not record.passed)
        adapter_ids = sorted({adapter for record in records for adapter in record.adapter_ids})
        query_ids = sorted({query for record in records for query in record.query_ids})
        replay_keys = sorted({key for record in records for key in record.replay_keys})
        registry_integrity_hash = _hash([
            {
                "registry_id": record.registry_id,
                "artifact_id": record.artifact_id,
                "manifest_id": record.manifest_id,
                "certification_id": record.certification_id,
                "registry_hash": record.registry_hash,
                "passed": record.passed,
            }
            for record in sorted(records, key=lambda item: item.registry_id)
        ])

        return ReplayRegistrySnapshot(
            snapshot_id="oi190.snapshot." + registry_integrity_hash[:24],
            created_at=_utc_now(),
            module_id=self.module_id,
            module_name=self.module_name,
            oracle_instance_id=self.oracle_instance_id,
            record_count=len(records),
            certified_count=certified_count,
            failed_count=failed_count,
            adapter_count=len(adapter_ids),
            query_count=len(query_ids),
            replay_key_count=len(replay_keys),
            registry_integrity_hash=registry_integrity_hash,
            read_only_guardrails=dict(READ_ONLY_GUARDRAILS),
            telemetry={
                "oracle_instance_id": self.oracle_instance_id,
                "module_id": self.module_id,
                "module_name": self.module_name,
                "record_count": len(records),
                "certified_count": certified_count,
                "failed_count": failed_count,
                "adapter_count": len(adapter_ids),
                "query_count": len(query_ids),
                "replay_key_count": len(replay_keys),
            },
            explainability={
                "purpose": "Provide a read-only institutional snapshot of certified replay registrations.",
                "integrity_method": "Deterministic SHA-256 hash over sorted registry records.",
                "lookup_dimensions": [
                    "registry_id",
                    "manifest_id",
                    "certification_id",
                    "validation_id",
                    "adapter_id",
                    "query_id",
                    "replay_key",
                ],
                "execution_boundary": "Registry is Oracle intelligence only; Q Series owns execution.",
            },
        )

    def telemetry_snapshot(self) -> Dict[str, Any]:
        return self.snapshot().telemetry | {"read_only_guardrails": dict(READ_ONLY_GUARDRAILS)}

    def replay_registry_manifest(self) -> Dict[str, Any]:
        snap = self.snapshot()
        return {
            "module_id": self.module_id,
            "module_name": self.module_name,
            "oracle_instance_id": self.oracle_instance_id,
            "snapshot_id": snap.snapshot_id,
            "registry_integrity_hash": snap.registry_integrity_hash,
            "record_count": snap.record_count,
            "read_only_guardrails": dict(READ_ONLY_GUARDRAILS),
            "records": [
                {
                    "registry_id": record.registry_id,
                    "artifact_id": record.artifact_id,
                    "manifest_id": record.manifest_id,
                    "certification_id": record.certification_id,
                    "validation_id": record.validation_id,
                    "adapter_ids": record.adapter_ids,
                    "query_ids": record.query_ids,
                    "replay_keys": record.replay_keys,
                    "passed": record.passed,
                    "registry_hash": record.registry_hash,
                }
                for record in sorted(self.records(), key=lambda item: item.registry_id)
            ],
        }

    def verify_registry_integrity(self) -> Dict[str, Any]:
        snap = self.snapshot()
        broken = [
            record.registry_id
            for record in self.records()
            if record.registry_hash != _hash({
                "artifact_id": record.artifact_id,
                "source_hash": record.source_hash,
                "lineage_hash": record.lineage_hash,
            })
        ]
        return {
            "module_id": self.module_id,
            "oracle_instance_id": self.oracle_instance_id,
            "verified": not broken,
            "broken_registry_ids": broken,
            "registry_integrity_hash": snap.registry_integrity_hash,
            "read_only_guardrails": dict(READ_ONLY_GUARDRAILS),
        }

    def _merge_artifact_data(
        self,
        certification: Dict[str, Any],
        manifest: Dict[str, Any],
        validation: Dict[str, Any],
    ) -> Dict[str, Any]:
        merged = {}
        merged.update(manifest)
        merged.update(validation)
        merged.update(certification)
        if "entries" not in merged:
            for source in (manifest, certification, validation):
                if source.get("entries"):
                    merged["entries"] = source.get("entries")
                    break
        return merged

    def _extract_entries(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        entries = [_safe_dict(entry) for entry in _safe_list(data.get("entries"))]
        if entries:
            return entries
        replay_keys = _safe_list(data.get("replay_keys"))
        adapter_ids = _safe_list(data.get("adapter_ids"))
        query_ids = _safe_list(data.get("query_ids"))
        synthetic: List[Dict[str, Any]] = []
        for index, replay_key in enumerate(replay_keys):
            synthetic.append({
                "replay_key": str(replay_key),
                "adapter_id": str(adapter_ids[index]) if index < len(adapter_ids) else "",
                "query_id": str(query_ids[index]) if index < len(query_ids) else "",
            })
        return synthetic

    def _evaluate_registration(
        self,
        certification: Dict[str, Any],
        manifest: Dict[str, Any],
        validation: Dict[str, Any],
        context: Dict[str, Any],
    ) -> List[ReplayRegistryFinding]:
        findings: List[ReplayRegistryFinding] = []
        merged = self._merge_artifact_data(certification, manifest, validation)

        if not (certification.get("certification_id") or certification.get("certificate_id")):
            findings.append(ReplayRegistryFinding(
                code="CERTIFICATION_ID_MISSING",
                severity="error",
                message="Certified replay registration requires a certification identifier.",
            ))

        if not certification.get("certified", certification.get("passed", False)):
            findings.append(ReplayRegistryFinding(
                code="CERTIFICATION_NOT_PASSED",
                severity="error",
                message="Replay artifact is not certified as passed.",
            ))

        if not merged.get("manifest_id"):
            findings.append(ReplayRegistryFinding(
                code="MANIFEST_ID_MISSING",
                severity="error",
                message="Certified replay registration requires manifest lineage.",
            ))

        manifest_hash = str(merged.get("manifest_hash") or "")
        if manifest_hash and len(manifest_hash) != 64:
            findings.append(ReplayRegistryFinding(
                code="MANIFEST_HASH_INVALID",
                severity="warning",
                message="Manifest hash is present but is not a 64-character SHA-256 digest.",
                evidence={"manifest_hash": manifest_hash},
            ))

        guardrails = _safe_dict(merged.get("read_only_guardrails")) or _safe_dict(certification.get("read_only_guardrails"))
        for key, expected in READ_ONLY_GUARDRAILS.items():
            if guardrails and guardrails.get(key) != expected:
                findings.append(ReplayRegistryFinding(
                    code="READ_ONLY_GUARDRAIL_MISMATCH",
                    severity="critical",
                    message="Replay registry artifact does not preserve Oracle read-only guardrails.",
                    evidence={"key": key, "expected": expected, "actual": guardrails.get(key)},
                ))

        scan_text = _stable_json({"certification": certification, "manifest": manifest, "validation": validation, "context": context}).lower()
        execution_terms = ["executed", "submit_order", "order_submitted", "trade_routed", "position_opened", "manage_position"]
        detected = [term for term in execution_terms if term in scan_text]
        if detected:
            findings.append(ReplayRegistryFinding(
                code="EXECUTION_LANGUAGE_DETECTED",
                severity="warning",
                message="Execution-like language detected in replay registry artifact. Oracle remains read-only.",
                evidence={"detected_terms": detected},
            ))

        return findings

    def _upsert(self, record: ReplayRegistryRecord) -> None:
        if record.registry_id in self._records:
            self._remove_indexes(self._records[record.registry_id])

        self._records[record.registry_id] = record
        if record.manifest_id:
            self._by_manifest_id[record.manifest_id] = record.registry_id
        if record.certification_id:
            self._by_certification_id[record.certification_id] = record.registry_id
        if record.validation_id:
            self._by_validation_id[record.validation_id] = record.registry_id
        for adapter_id in record.adapter_ids:
            self._by_adapter_id.setdefault(adapter_id, []).append(record.registry_id)
        for query_id in record.query_ids:
            self._by_query_id.setdefault(query_id, []).append(record.registry_id)
        for replay_key in record.replay_keys:
            self._by_replay_key.setdefault(replay_key, []).append(record.registry_id)

    def _remove_indexes(self, record: ReplayRegistryRecord) -> None:
        for mapping, key in (
            (self._by_manifest_id, record.manifest_id),
            (self._by_certification_id, record.certification_id),
            (self._by_validation_id, record.validation_id),
        ):
            if key and mapping.get(key) == record.registry_id:
                del mapping[key]

        for mapping in (self._by_adapter_id, self._by_query_id, self._by_replay_key):
            for key in list(mapping.keys()):
                mapping[key] = [rid for rid in mapping[key] if rid != record.registry_id]
                if not mapping[key]:
                    del mapping[key]


def create_replay_registry_engine(
    oracle_instance_id: str = "oracle.default",
) -> UniversalMarketAdapterReplayRegistryEngine:
    return UniversalMarketAdapterReplayRegistryEngine(oracle_instance_id=oracle_instance_id)


__all__ = [
    "READ_ONLY_GUARDRAILS",
    "ReplayRegistryFinding",
    "ReplayRegistryRecord",
    "ReplayRegistrySnapshot",
    "UniversalMarketAdapterReplayRegistryEngine",
    "create_replay_registry_engine",
]
'''.lstrip()


test_code = r'''
from qseries_v2.oracle_intelligence.universal_market_adapter_replay_registry_engine import (
    READ_ONLY_GUARDRAILS,
    UniversalMarketAdapterReplayRegistryEngine,
    create_replay_registry_engine,
)


def test_oi_190_universal_market_adapter_replay_registry_engine():
    engine = create_replay_registry_engine("oracle.test")

    certification = {
        "certification_id": "cert-001",
        "certification_hash": "a" * 64,
        "certified": True,
        "manifest_id": "manifest-001",
        "manifest_hash": "b" * 64,
        "validation_id": "validation-001",
        "validation_hash": "c" * 64,
        "read_only_guardrails": READ_ONLY_GUARDRAILS,
    }
    manifest = {
        "manifest_id": "manifest-001",
        "manifest_hash": "b" * 64,
        "entries": [
            {
                "adapter_id": "adp.kalshi",
                "query_id": "q-001",
                "replay_key": "replay-001",
            },
            {
                "adapter_id": "adp.polymarket",
                "query_id": "q-002",
                "replay_key": "replay-002",
            },
        ],
    }
    validation = {
        "validation_id": "validation-001",
        "validation_hash": "c" * 64,
        "passed": True,
    }

    record = engine.register_certified_replay(
        certification=certification,
        manifest=manifest,
        validation=validation,
    )

    assert record.passed is True
    assert record.certified is True
    assert record.manifest_id == "manifest-001"
    assert record.certification_id == "cert-001"
    assert record.validation_id == "validation-001"
    assert record.entry_count == 2
    assert record.adapter_ids == ["adp.kalshi", "adp.polymarket"]
    assert record.query_ids == ["q-001", "q-002"]
    assert record.replay_keys == ["replay-001", "replay-002"]
    assert len(record.registry_hash) == 64
    assert len(record.lineage_hash) == 64
    assert record.read_only_guardrails == READ_ONLY_GUARDRAILS

    assert engine.lookup_by_registry_id(record.registry_id).manifest_id == "manifest-001"
    assert engine.lookup_by_manifest_id("manifest-001").registry_id == record.registry_id
    assert engine.lookup_by_certification_id("cert-001").registry_id == record.registry_id
    assert engine.lookup_by_validation_id("validation-001").registry_id == record.registry_id
    assert engine.lookup_by_adapter_id("adp.kalshi")[0].registry_id == record.registry_id
    assert engine.lookup_by_query_id("q-002")[0].registry_id == record.registry_id
    assert engine.lookup_by_replay_key("replay-001")[0].registry_id == record.registry_id

    bad = engine.register_certified_replay(
        certification={
            "certification_id": "cert-002",
            "certified": False,
            "manifest_id": "manifest-002",
            "manifest_hash": "bad-hash",
            "read_only_guardrails": {
                "oracle_read_only": False,
                "executes_trades": True,
                "routes_orders": True,
                "submits_orders": True,
                "manages_positions": True,
                "execution_owner": "ORACLE",
            },
        },
        manifest={
            "manifest_id": "manifest-002",
            "manifest_hash": "bad-hash",
            "entries": [
                {"adapter_id": "adp.bad", "query_id": "q-bad", "replay_key": "replay-bad"}
            ],
        },
        context={"submit_order": True},
    )
    codes = {finding.code for finding in bad.findings}
    assert bad.passed is False
    assert "CERTIFICATION_NOT_PASSED" in codes
    assert "MANIFEST_HASH_INVALID" in codes
    assert "READ_ONLY_GUARDRAIL_MISMATCH" in codes
    assert "EXECUTION_LANGUAGE_DETECTED" in codes

    snapshot = engine.snapshot()
    assert snapshot.module_id == "OI-190"
    assert snapshot.record_count == 2
    assert snapshot.certified_count == 1
    assert snapshot.failed_count == 1
    assert snapshot.adapter_count == 3
    assert snapshot.query_count == 3
    assert snapshot.replay_key_count == 3
    assert len(snapshot.registry_integrity_hash) == 64
    assert snapshot.read_only_guardrails == READ_ONLY_GUARDRAILS

    telemetry = engine.telemetry_snapshot()
    assert telemetry["record_count"] == 2
    assert telemetry["read_only_guardrails"] == READ_ONLY_GUARDRAILS

    manifest_out = engine.replay_registry_manifest()
    assert manifest_out["module_id"] == "OI-190"
    assert manifest_out["record_count"] == 2
    assert len(manifest_out["records"]) == 2

    integrity = engine.verify_registry_integrity()
    assert integrity["verified"] is True
    assert integrity["broken_registry_ids"] == []

    batch = engine.register_many([
        {
            "certification": {
                "certification_id": "cert-003",
                "certified": True,
                "manifest_id": "manifest-003",
                "manifest_hash": "d" * 64,
                "read_only_guardrails": READ_ONLY_GUARDRAILS,
                "replay_keys": ["replay-003"],
                "adapter_ids": ["adp.batch"],
                "query_ids": ["q-003"],
            }
        }
    ])
    assert len(batch) == 1
    assert batch[0].certification_id == "cert-003"
    assert engine.lookup_by_replay_key("replay-003")[0].certification_id == "cert-003"

    empty = UniversalMarketAdapterReplayRegistryEngine("oracle.empty")
    assert empty.snapshot().record_count == 0


if __name__ == "__main__":
    test_oi_190_universal_market_adapter_replay_registry_engine()
    print("[PASS] OI-190 Universal Market Adapter Replay Registry Engine")
'''.lstrip()

MODULE.write_text(module_code, encoding="utf-8")
TEST.write_text(test_code, encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

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
