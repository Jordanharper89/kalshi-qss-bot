"""
OI-173 — Oracle Universal Market Adapter Registry Engine

Read-only registry engine for lifecycle-approved Universal Market Adapters.

Purpose:
- Register adapters after lifecycle evaluation.
- Preserve lifecycle state, certification lineage, domain coverage, readiness,
  safety status, and institutional adapter metadata.
- Provide a clean adapter registry for future Oracle Market OS routing layers.

Oracle never executes trades, manages positions, or submits orders.
Execution ownership remains with Q Series.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, List


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _stable_text(value: Any) -> str:
    if isinstance(value, dict):
        return "{" + ",".join(f"{k}:{_stable_text(value[k])}" for k in sorted(value)) + "}"
    if isinstance(value, list):
        return "[" + ",".join(_stable_text(v) for v in value) + "]"
    return repr(value)


def _hash(value: Any, size: int = 24) -> str:
    return sha256(_stable_text(value).encode("utf-8")).hexdigest()[:size]


@dataclass
class AdapterRegistryRecord:
    registry_record_id: str
    adapter_id: str
    domain: str
    lifecycle_state: str
    lifecycle_status: str
    registry_status: str
    registered: bool
    promoted: bool
    blocked: bool
    adapter_role: str
    lineage_hash: str
    read_only: bool = True
    execution_allowed: bool = False
    execution_owner: str = "Q Series"


@dataclass
class OracleUniversalMarketAdapterRegistryEngine:
    name: str = "oracle_universal_market_adapter_registry_engine"
    version: str = "OI-173"
    read_only: bool = True
    execution_allowed: bool = False
    execution_owner: str = "Q Series"
    registry_schema_version: str = "universal_market_adapter_registry_v1"

    def classify_registry_status(self, record: Dict[str, Any]) -> str:
        record = _safe_dict(record)

        if record.get("read_only") is not True:
            return "registry_blocked_read_only_violation"
        if record.get("execution_allowed") is not False:
            return "registry_blocked_execution_violation"
        if record.get("execution_owner") != "Q Series":
            return "registry_blocked_execution_owner_violation"

        state = str(record.get("lifecycle_state") or "")
        if state == "blocked":
            return "registry_blocked_lifecycle"
        if state == "active_institutional_read_only":
            return "registered_institutional_adapter"
        if state == "active_read_only":
            return "registered_active_adapter"
        if state == "active_review_read_only":
            return "registered_review_adapter"
        return "registry_review_required"

    def adapter_role(self, record: Dict[str, Any]) -> str:
        domain = str(_safe_dict(record).get("domain") or "UNKNOWN").upper()
        return f"{domain.lower()}_umm_ingestion_adapter"

    def build_record(self, lifecycle_record: Dict[str, Any]) -> AdapterRegistryRecord:
        record = _safe_dict(lifecycle_record)
        adapter_id = str(record.get("adapter_id") or "unknown_adapter")
        domain = str(record.get("domain") or "UNKNOWN").upper()
        lifecycle_state = str(record.get("lifecycle_state") or "unknown_lifecycle_state")
        lifecycle_status = str(record.get("lifecycle_status") or "unknown_lifecycle_status")
        registry_status = self.classify_registry_status(record)

        payload = {
            "adapter_id": adapter_id,
            "domain": domain,
            "lifecycle_state": lifecycle_state,
            "lifecycle_status": lifecycle_status,
            "registry_status": registry_status,
            "source_lifecycle_record_id": record.get("lifecycle_record_id"),
        }
        lineage_hash = _hash(payload)

        return AdapterRegistryRecord(
            registry_record_id=_hash({"payload": payload, "lineage": lineage_hash}),
            adapter_id=adapter_id,
            domain=domain,
            lifecycle_state=lifecycle_state,
            lifecycle_status=lifecycle_status,
            registry_status=registry_status,
            registered=registry_status.startswith("registered_"),
            promoted=record.get("promoted") is True,
            blocked=registry_status.startswith("registry_blocked") or record.get("blocked") is True,
            adapter_role=self.adapter_role(record),
            lineage_hash=lineage_hash,
            read_only=True,
            execution_allowed=False,
            execution_owner=self.execution_owner,
        )

    def build_registry(self, lifecycle: Dict[str, Any]) -> Dict[str, Any]:
        lifecycle = _safe_dict(lifecycle)
        lifecycle_records = _safe_list(lifecycle.get("records"))

        records = [self.build_record(record) for record in lifecycle_records]
        records.sort(key=lambda r: (r.domain, r.adapter_id))

        domain_counts: Dict[str, int] = {}
        status_counts: Dict[str, int] = {}
        lifecycle_state_counts: Dict[str, int] = {}
        role_counts: Dict[str, int] = {}

        registered_count = 0
        blocked_count = 0
        promoted_count = 0

        for record in records:
            domain_counts[record.domain] = domain_counts.get(record.domain, 0) + 1
            status_counts[record.registry_status] = status_counts.get(record.registry_status, 0) + 1
            lifecycle_state_counts[record.lifecycle_state] = lifecycle_state_counts.get(record.lifecycle_state, 0) + 1
            role_counts[record.adapter_role] = role_counts.get(record.adapter_role, 0) + 1
            if record.registered:
                registered_count += 1
            if record.blocked:
                blocked_count += 1
            if record.promoted:
                promoted_count += 1

        if not records:
            registry_status = "empty_adapter_registry"
        elif blocked_count:
            registry_status = "adapter_registry_blocked"
        elif registered_count == len(records) and status_counts.get("registered_institutional_adapter", 0) == len(records):
            registry_status = "adapter_registry_institutional"
        elif registered_count == len(records):
            registry_status = "adapter_registry_ready"
        else:
            registry_status = "adapter_registry_review_required"

        registry_id = _hash({
            "source_lifecycle_batch_id": lifecycle.get("adapter_lifecycle_batch_id"),
            "registry_status": registry_status,
            "records": [record.__dict__ for record in records],
        })

        return {
            "module": self.name,
            "version": self.version,
            "registry_schema_version": self.registry_schema_version,
            "adapter_registry_id": registry_id,
            "registry_status": registry_status,
            "registered_at": _utc_now(),
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "execution_owner": self.execution_owner,
            "single_oracle_instance": True,
            "adapter_based_expansion": True,
            "source_adapter_lifecycle_batch_id": lifecycle.get("adapter_lifecycle_batch_id"),
            "source_lifecycle_status": lifecycle.get("lifecycle_status"),
            "adapter_count": len(records),
            "registered_count": registered_count,
            "promoted_count": promoted_count,
            "blocked_count": blocked_count,
            "domain_counts": domain_counts,
            "status_counts": status_counts,
            "lifecycle_state_counts": lifecycle_state_counts,
            "role_counts": role_counts,
            "executive_summary": {
                "headline": (
                    "Universal Market adapter registry is institutional."
                    if registry_status == "adapter_registry_institutional"
                    else f"Universal Market adapter registry status: {registry_status}."
                ),
                "adapter_registry_id": registry_id,
                "adapter_count": len(records),
                "registered_count": registered_count,
                "blocked_count": blocked_count,
                "operator_note": "Adapter registry is read-only. Oracle remains intelligence-only. Q Series owns execution.",
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": self.execution_owner,
            },
            "records": [record.__dict__ for record in records],
        }

    def lookup_adapter(self, registry: Dict[str, Any], adapter_id: str) -> Dict[str, Any]:
        registry = _safe_dict(registry)
        records = _safe_list(registry.get("records"))
        target = str(adapter_id or "").strip().lower()

        for record in records:
            record = _safe_dict(record)
            if str(record.get("adapter_id") or "").strip().lower() == target:
                return {
                    "module": self.name,
                    "version": self.version,
                    "found": True,
                    "adapter_id": adapter_id,
                    "record": record,
                    "read_only": True,
                    "execution_allowed": False,
                    "execution_owner": self.execution_owner,
                }

        return {
            "module": self.name,
            "version": self.version,
            "found": False,
            "adapter_id": adapter_id,
            "record": None,
            "read_only": True,
            "execution_allowed": False,
            "execution_owner": self.execution_owner,
        }

    def lookup_domain(self, registry: Dict[str, Any], domain: str) -> Dict[str, Any]:
        registry = _safe_dict(registry)
        records = _safe_list(registry.get("records"))
        target = str(domain or "").strip().upper()
        matches = [
            _safe_dict(record)
            for record in records
            if str(_safe_dict(record).get("domain") or "").strip().upper() == target
        ]

        return {
            "module": self.name,
            "version": self.version,
            "found": bool(matches),
            "domain": target,
            "match_count": len(matches),
            "records": matches,
            "read_only": True,
            "execution_allowed": False,
            "execution_owner": self.execution_owner,
        }


oracle_universal_market_adapter_registry_engine = OracleUniversalMarketAdapterRegistryEngine()
