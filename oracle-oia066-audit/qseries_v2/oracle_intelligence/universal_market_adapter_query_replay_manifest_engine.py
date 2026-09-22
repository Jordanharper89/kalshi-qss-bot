"""
OI-187 — Oracle Universal Market Adapter Query Replay Manifest Engine

Read-only replay manifest layer for Universal Market Adapter query audit records
and audit index entries.

This module creates deterministic institutional replay manifests for audited
adapter query resolution activity. It does not execute trades, route orders,
submit orders, manage positions, mutate market state, or provide execution
authority. Q Series remains the only execution engine.
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


def _safe_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, tuple):
        return list(value)
    return [value]


@dataclass(frozen=True)
class ReplayManifestFinding:
    code: str
    severity: str
    message: str
    evidence: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReplayManifestEntry:
    sequence: int
    audit_id: str
    adapter_id: str
    query_id: str
    replay_key: str
    passed: bool
    query_hash: str
    resolver_hash: str
    market_model_hash: str
    source_hash: str
    finding_codes: List[str]
    dependency_keys: List[str]
    lineage: Dict[str, Any]
    integrity_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReplayManifest:
    manifest_id: str
    created_at: str
    oracle_instance_id: str
    module_id: str
    module_name: str
    manifest_version: str
    entry_count: int
    passed_count: int
    failed_count: int
    adapter_count: int
    query_count: int
    dependency_count: int
    manifest_hash: str
    chain_hash: str
    read_only_guardrails: Dict[str, Any]
    entries: List[ReplayManifestEntry]
    findings: List[ReplayManifestFinding]
    telemetry: Dict[str, Any]
    explainability: Dict[str, Any]

    @property
    def passed(self) -> bool:
        return not any(f.severity in {"error", "critical"} for f in self.findings)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["passed"] = self.passed
        return data


class UniversalMarketAdapterQueryReplayManifestEngine:
    """
    Builds deterministic replay manifests from query audit records or query audit
    index entries.

    The manifest is designed for replayability, institutional telemetry,
    explainability, architecture-registry traceability, and strict Oracle
    execution-boundary preservation.
    """

    module_id = "OI-187"
    module_name = "Oracle Universal Market Adapter Query Replay Manifest Engine"
    manifest_version = "1.0"

    def __init__(self, oracle_instance_id: str = "oracle.default") -> None:
        self.oracle_instance_id = oracle_instance_id
        self._manifests: List[ReplayManifest] = []

    def build_manifest(
        self,
        records: Iterable[Any],
        *,
        manifest_context: Optional[Mapping[str, Any]] = None,
        dependency_map: Optional[Mapping[str, Iterable[str]]] = None,
    ) -> ReplayManifest:
        context = _safe_dict(manifest_context)
        dependencies = {
            str(key): [str(item) for item in _safe_list(value)]
            for key, value in _safe_dict(dependency_map).items()
        }

        normalized = [self._normalize_record(record) for record in records]
        ordered = self._deterministic_order(normalized)

        entries = [
            self._build_entry(
                sequence=sequence,
                record=record,
                dependency_map=dependencies,
            )
            for sequence, record in enumerate(ordered, start=1)
        ]

        findings = self._evaluate_manifest(entries, context, dependencies)

        manifest_payload = {
            "oracle_instance_id": self.oracle_instance_id,
            "module_id": self.module_id,
            "manifest_version": self.manifest_version,
            "entries": [entry.to_dict() for entry in entries],
            "context": context,
            "findings": [finding.to_dict() for finding in findings],
        }

        manifest_hash = _hash(manifest_payload)
        chain_hash = self._chain_hash(entries)

        passed_count = sum(1 for entry in entries if entry.passed)
        failed_count = len(entries) - passed_count
        adapter_count = len({entry.adapter_id for entry in entries})
        query_count = len({entry.query_id for entry in entries})
        dependency_count = sum(len(entry.dependency_keys) for entry in entries)

        manifest = ReplayManifest(
            manifest_id="oi187.manifest." + manifest_hash[:24],
            created_at=_utc_now(),
            oracle_instance_id=self.oracle_instance_id,
            module_id=self.module_id,
            module_name=self.module_name,
            manifest_version=self.manifest_version,
            entry_count=len(entries),
            passed_count=passed_count,
            failed_count=failed_count,
            adapter_count=adapter_count,
            query_count=query_count,
            dependency_count=dependency_count,
            manifest_hash=manifest_hash,
            chain_hash=chain_hash,
            read_only_guardrails=dict(READ_ONLY_GUARDRAILS),
            entries=entries,
            findings=findings,
            telemetry={
                "oracle_instance_id": self.oracle_instance_id,
                "module_id": self.module_id,
                "module_name": self.module_name,
                "manifest_version": self.manifest_version,
                "entry_count": len(entries),
                "passed_count": passed_count,
                "failed_count": failed_count,
                "adapter_count": adapter_count,
                "query_count": query_count,
                "dependency_count": dependency_count,
                "finding_count": len(findings),
                "critical_or_error_count": sum(
                    1 for finding in findings
                    if finding.severity in {"critical", "error"}
                ),
                "context_hash": _hash(context),
            },
            explainability={
                "purpose": "Create a deterministic replay manifest for audited Universal Market Adapter queries.",
                "read_only_reason": "Replay manifest construction organizes audit metadata only and does not create execution authority.",
                "execution_boundary": "Q Series is the only execution engine.",
                "ordering_method": "Entries are sorted deterministically by replay_key, audit_id, adapter_id, and query_id.",
                "integrity_method": "SHA-256 hashes over normalized entries and chained entry integrity hashes.",
                "lineage_fields": [
                    "audit_id",
                    "adapter_id",
                    "query_id",
                    "replay_key",
                    "query_hash",
                    "resolver_hash",
                    "market_model_hash",
                    "source_hash",
                ],
                "universal_market_model_compatibility": "The manifest preserves market_model_hash and lineage metadata for replay without requiring market-state mutation.",
            },
        )

        self._manifests.append(manifest)
        return manifest

    def build_from_index_engine(
        self,
        index_engine: Any,
        *,
        manifest_context: Optional[Mapping[str, Any]] = None,
        dependency_map: Optional[Mapping[str, Iterable[str]]] = None,
    ) -> ReplayManifest:
        if not hasattr(index_engine, "entries"):
            raise TypeError("index_engine must expose an entries() method")
        return self.build_manifest(
            index_engine.entries(),
            manifest_context=manifest_context,
            dependency_map=dependency_map,
        )

    def manifests(self) -> List[ReplayManifest]:
        return list(self._manifests)

    def latest_manifest(self) -> Optional[ReplayManifest]:
        return self._manifests[-1] if self._manifests else None

    def telemetry_snapshot(self) -> Dict[str, Any]:
        latest = self.latest_manifest()
        return {
            "module_id": self.module_id,
            "module_name": self.module_name,
            "oracle_instance_id": self.oracle_instance_id,
            "manifest_count": len(self._manifests),
            "latest_manifest_id": latest.manifest_id if latest else None,
            "latest_manifest_hash": latest.manifest_hash if latest else None,
            "latest_chain_hash": latest.chain_hash if latest else None,
            "read_only_guardrails": dict(READ_ONLY_GUARDRAILS),
        }

    def replay_package(self, manifest: Optional[ReplayManifest] = None) -> Dict[str, Any]:
        selected = manifest or self.latest_manifest()
        if selected is None:
            return {
                "module_id": self.module_id,
                "oracle_instance_id": self.oracle_instance_id,
                "package_status": "empty",
                "read_only_guardrails": dict(READ_ONLY_GUARDRAILS),
                "entries": [],
            }

        return {
            "package_id": "oi187.replay_package." + selected.manifest_hash[:24],
            "package_status": "ready",
            "manifest_id": selected.manifest_id,
            "manifest_hash": selected.manifest_hash,
            "chain_hash": selected.chain_hash,
            "oracle_instance_id": self.oracle_instance_id,
            "module_id": self.module_id,
            "manifest_version": self.manifest_version,
            "read_only_guardrails": dict(READ_ONLY_GUARDRAILS),
            "entries": [entry.to_dict() for entry in selected.entries],
            "findings": [finding.to_dict() for finding in selected.findings],
            "explainability": selected.explainability,
        }

    def _normalize_record(self, record: Any) -> Dict[str, Any]:
        data = _safe_dict(record)

        audit_id = str(data.get("audit_id") or data.get("id") or "").strip()
        adapter_id = str(data.get("adapter_id") or "unknown.adapter").strip()
        query_id = str(data.get("query_id") or "unknown.query").strip()
        replay_key = str(
            data.get("replay_key")
            or _hash({"audit_id": audit_id, "adapter_id": adapter_id, "query_id": query_id})
        )

        findings = _safe_list(data.get("findings"))
        finding_codes = list(data.get("finding_codes") or [])
        if not finding_codes:
            finding_codes = self._extract_finding_codes(findings)

        return {
            "audit_id": audit_id or "audit." + _hash(data)[:24],
            "adapter_id": adapter_id,
            "query_id": query_id,
            "replay_key": replay_key,
            "passed": bool(data.get("passed", False)),
            "query_hash": str(data.get("query_hash") or ""),
            "resolver_hash": str(data.get("resolver_hash") or ""),
            "market_model_hash": str(data.get("market_model_hash") or ""),
            "source_hash": str(data.get("source_hash") or _hash(data)),
            "finding_codes": [str(code) for code in finding_codes],
            "created_at": str(data.get("created_at") or ""),
            "raw_hash": _hash(data),
        }

    def _deterministic_order(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return sorted(
            records,
            key=lambda item: (
                item.get("replay_key", ""),
                item.get("audit_id", ""),
                item.get("adapter_id", ""),
                item.get("query_id", ""),
            ),
        )

    def _build_entry(
        self,
        *,
        sequence: int,
        record: Dict[str, Any],
        dependency_map: Dict[str, List[str]],
    ) -> ReplayManifestEntry:
        replay_key = record["replay_key"]
        dependency_keys = list(dependency_map.get(replay_key, []))

        lineage = {
            "audit_id": record["audit_id"],
            "adapter_id": record["adapter_id"],
            "query_id": record["query_id"],
            "replay_key": replay_key,
            "query_hash": record["query_hash"],
            "resolver_hash": record["resolver_hash"],
            "market_model_hash": record["market_model_hash"],
            "source_hash": record["source_hash"],
            "raw_hash": record["raw_hash"],
        }

        integrity_payload = {
            "sequence": sequence,
            "lineage": lineage,
            "passed": record["passed"],
            "finding_codes": record["finding_codes"],
            "dependency_keys": dependency_keys,
        }

        return ReplayManifestEntry(
            sequence=sequence,
            audit_id=record["audit_id"],
            adapter_id=record["adapter_id"],
            query_id=record["query_id"],
            replay_key=replay_key,
            passed=record["passed"],
            query_hash=record["query_hash"],
            resolver_hash=record["resolver_hash"],
            market_model_hash=record["market_model_hash"],
            source_hash=record["source_hash"],
            finding_codes=record["finding_codes"],
            dependency_keys=dependency_keys,
            lineage=lineage,
            integrity_hash=_hash(integrity_payload),
        )

    def _evaluate_manifest(
        self,
        entries: List[ReplayManifestEntry],
        context: Dict[str, Any],
        dependency_map: Dict[str, List[str]],
    ) -> List[ReplayManifestFinding]:
        findings: List[ReplayManifestFinding] = []

        if not entries:
            findings.append(ReplayManifestFinding(
                code="REPLAY_MANIFEST_EMPTY",
                severity="warning",
                message="Replay manifest contains no entries.",
            ))
            return findings

        replay_keys = [entry.replay_key for entry in entries]
        duplicate_replay_keys = sorted(key for key in set(replay_keys) if replay_keys.count(key) > 1)
        if duplicate_replay_keys:
            findings.append(ReplayManifestFinding(
                code="DUPLICATE_REPLAY_KEYS",
                severity="error",
                message="Replay manifest contains duplicate replay keys.",
                evidence={"duplicate_replay_keys": duplicate_replay_keys},
            ))

        audit_ids = [entry.audit_id for entry in entries]
        duplicate_audit_ids = sorted(audit_id for audit_id in set(audit_ids) if audit_ids.count(audit_id) > 1)
        if duplicate_audit_ids:
            findings.append(ReplayManifestFinding(
                code="DUPLICATE_AUDIT_IDS",
                severity="error",
                message="Replay manifest contains duplicate audit identifiers.",
                evidence={"duplicate_audit_ids": duplicate_audit_ids},
            ))

        missing_hash_entries = [
            entry.audit_id for entry in entries
            if not entry.query_hash or not entry.resolver_hash
        ]
        if missing_hash_entries:
            findings.append(ReplayManifestFinding(
                code="REPLAY_HASH_CONTEXT_WEAK",
                severity="warning",
                message="Some replay entries are missing query or resolver hashes.",
                evidence={"audit_ids": missing_hash_entries},
            ))

        failed_entries = [entry.audit_id for entry in entries if not entry.passed]
        if failed_entries:
            findings.append(ReplayManifestFinding(
                code="FAILED_AUDIT_ENTRIES_INCLUDED",
                severity="info",
                message="Manifest includes failed audit entries for replay visibility.",
                evidence={"failed_audit_ids": failed_entries},
            ))

        execution_codes = [
            entry.audit_id for entry in entries
            if "EXECUTION_BOUNDARY_VIOLATION" in entry.finding_codes
        ]
        if execution_codes:
            findings.append(ReplayManifestFinding(
                code="EXECUTION_BOUNDARY_REPLAY_ALERT",
                severity="critical",
                message="Manifest includes records with execution-boundary violations. Oracle remains read-only; Q Series owns execution.",
                evidence={"audit_ids": execution_codes},
            ))

        known_replay_keys = set(replay_keys)
        dangling_dependencies: Dict[str, List[str]] = {}
        for replay_key, deps in dependency_map.items():
            missing = [dep for dep in deps if dep not in known_replay_keys]
            if missing:
                dangling_dependencies[replay_key] = missing

        if dangling_dependencies:
            findings.append(ReplayManifestFinding(
                code="DANGLING_REPLAY_DEPENDENCIES",
                severity="warning",
                message="Dependency map references replay keys not present in manifest.",
                evidence={"dangling_dependencies": dangling_dependencies},
            ))

        execution_like_context_keys = {
            "execute", "executed", "submit_order", "route_order", "trade", "order", "position"
        }
        detected_context_keys = [
            str(key) for key in context.keys()
            if str(key).lower() in execution_like_context_keys
        ]
        if detected_context_keys:
            findings.append(ReplayManifestFinding(
                code="CONTEXT_EXECUTION_LANGUAGE_DETECTED",
                severity="warning",
                message="Manifest context contains execution-like keys. Oracle manifest remains read-only.",
                evidence={"context_keys": sorted(detected_context_keys)},
            ))

        return findings

    def _extract_finding_codes(self, findings: List[Any]) -> List[str]:
        codes: List[str] = []
        for finding in findings:
            data = _safe_dict(finding)
            code = data.get("code")
            if code:
                codes.append(str(code))
        return codes

    def _chain_hash(self, entries: List[ReplayManifestEntry]) -> str:
        chain = "oi187.chain.root"
        for entry in entries:
            chain = _hash({
                "previous_chain_hash": chain,
                "entry_integrity_hash": entry.integrity_hash,
                "audit_id": entry.audit_id,
                "replay_key": entry.replay_key,
                "sequence": entry.sequence,
            })
        return chain


def create_query_replay_manifest_engine(
    oracle_instance_id: str = "oracle.default",
) -> UniversalMarketAdapterQueryReplayManifestEngine:
    return UniversalMarketAdapterQueryReplayManifestEngine(oracle_instance_id=oracle_instance_id)


__all__ = [
    "READ_ONLY_GUARDRAILS",
    "ReplayManifestFinding",
    "ReplayManifestEntry",
    "ReplayManifest",
    "UniversalMarketAdapterQueryReplayManifestEngine",
    "create_query_replay_manifest_engine",
]
