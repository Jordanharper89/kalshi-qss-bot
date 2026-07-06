"""
OI-162 — Oracle Architecture Registry Engine

Read-only architecture registry for Oracle Intelligence.

Purpose:
- Register institutional Oracle modules and architecture layers.
- Preserve module ownership, read-only constraints, execution boundaries,
  lifecycle phase, and Universal Market Model readiness.
- Provide registry reports for the Architecture Manual and future terminal views.

Oracle never executes trades, manages positions, or submits orders.
Execution ownership remains with Q Series.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, Iterable, List, Optional


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
class ArchitectureRegistryRecord:
    registry_record_id: str
    module_id: str
    module_name: str
    architecture_layer: str
    lifecycle_phase: str
    ownership: str
    read_only: bool
    execution_allowed: bool
    execution_owner: str
    universal_market_model_ready: bool
    adapter_ready: bool
    replayable: bool
    explainable: bool
    institutional_status: str
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    lineage_hash: str = ""


@dataclass
class OracleArchitectureRegistryEngine:
    name: str = "oracle_architecture_registry_engine"
    version: str = "OI-162"
    read_only: bool = True
    execution_allowed: bool = False
    execution_owner: str = "Q Series"
    registry_schema_version: str = "architecture_registry_v1"

    permanent_principles: List[str] = field(default_factory=lambda: [
        "Oracle is strictly read-only.",
        "Q Series is the only execution engine.",
        "Universal Market Model for all data.",
        "Adapter-based expansion.",
        "Event-driven intelligence.",
        "Explainability by default.",
        "Replayability by default.",
        "Historical memory is permanent.",
        "Institutional telemetry.",
        "Strategy-agnostic Q Series.",
        "Single responsibility per module.",
        "Architecture Registry and Architecture Manual maintained as platform grows.",
    ])

    supported_domains: List[str] = field(default_factory=lambda: [
        "PREDICTION_MARKETS",
        "CRYPTO",
        "STOCKS",
        "ETFS",
        "FUTURES",
        "COMMODITIES",
        "FOREX",
        "MACROECONOMICS",
        "WEATHER",
        "NEWS",
        "ALTERNATIVE_DATA",
    ])

    def classify_status(self, module: Dict[str, Any]) -> str:
        module = _safe_dict(module)

        if module.get("read_only") is not True:
            return "blocked_read_only_violation"
        if module.get("execution_allowed") is not False:
            return "blocked_execution_violation"
        if module.get("execution_owner") != "Q Series":
            return "blocked_execution_owner_violation"

        if module.get("replayable") and module.get("explainable") and module.get("universal_market_model_ready"):
            return "institutional_registered"

        if module.get("explainable") and module.get("read_only"):
            return "registered_with_review"

        return "registered_limited"

    def register_module(self, module: Dict[str, Any]) -> ArchitectureRegistryRecord:
        module = _safe_dict(module)

        module_id = str(module.get("module_id") or module.get("version") or _hash(module, 12))
        module_name = str(module.get("module_name") or module.get("name") or "unknown_oracle_module")
        architecture_layer = str(module.get("architecture_layer") or "Oracle Intelligence")
        lifecycle_phase = str(module.get("lifecycle_phase") or "production")
        ownership = str(module.get("ownership") or "Oracle Intelligence")

        record_payload = {
            "module_id": module_id,
            "module_name": module_name,
            "architecture_layer": architecture_layer,
            "lifecycle_phase": lifecycle_phase,
            "ownership": ownership,
            "read_only": module.get("read_only", True),
            "execution_allowed": module.get("execution_allowed", False),
            "execution_owner": module.get("execution_owner", "Q Series"),
        }

        lineage_hash = _hash(record_payload)

        return ArchitectureRegistryRecord(
            registry_record_id=_hash({"record": record_payload, "lineage": lineage_hash}),
            module_id=module_id,
            module_name=module_name,
            architecture_layer=architecture_layer,
            lifecycle_phase=lifecycle_phase,
            ownership=ownership,
            read_only=module.get("read_only", True) is True,
            execution_allowed=module.get("execution_allowed", False) is True,
            execution_owner=str(module.get("execution_owner") or "Q Series"),
            universal_market_model_ready=module.get("universal_market_model_ready", True) is True,
            adapter_ready=module.get("adapter_ready", False) is True,
            replayable=module.get("replayable", True) is True,
            explainable=module.get("explainable", True) is True,
            institutional_status=self.classify_status(module),
            dependencies=[str(x) for x in _safe_list(module.get("dependencies"))],
            tags=[str(x) for x in _safe_list(module.get("tags"))],
            lineage_hash=lineage_hash,
        )

    def build_registry(self, modules: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        records = [self.register_module(module) for module in modules]
        records.sort(key=lambda r: r.module_id)

        layer_counts: Dict[str, int] = {}
        status_counts: Dict[str, int] = {}
        phase_counts: Dict[str, int] = {}

        violation_count = 0
        replayable_count = 0
        explainable_count = 0
        umm_count = 0

        for record in records:
            layer_counts[record.architecture_layer] = layer_counts.get(record.architecture_layer, 0) + 1
            status_counts[record.institutional_status] = status_counts.get(record.institutional_status, 0) + 1
            phase_counts[record.lifecycle_phase] = phase_counts.get(record.lifecycle_phase, 0) + 1

            if "blocked" in record.institutional_status:
                violation_count += 1
            if record.replayable:
                replayable_count += 1
            if record.explainable:
                explainable_count += 1
            if record.universal_market_model_ready:
                umm_count += 1

        registry_id = _hash([record.__dict__ for record in records])

        if not records:
            registry_status = "empty_architecture_registry"
        elif violation_count:
            registry_status = "architecture_registry_blocked"
        else:
            registry_status = "architecture_registry_ready"

        return {
            "module": self.name,
            "version": self.version,
            "registry_schema_version": self.registry_schema_version,
            "architecture_registry_id": registry_id,
            "registry_status": registry_status,
            "created_at": _utc_now(),
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "execution_owner": self.execution_owner,
            "supported_domains": list(self.supported_domains),
            "permanent_principles": list(self.permanent_principles),
            "record_count": len(records),
            "violation_count": violation_count,
            "replayable_count": replayable_count,
            "explainable_count": explainable_count,
            "universal_market_model_ready_count": umm_count,
            "layer_counts": layer_counts,
            "status_counts": status_counts,
            "phase_counts": phase_counts,
            "executive_summary": {
                "headline": (
                    "Oracle architecture registry is ready."
                    if registry_status == "architecture_registry_ready"
                    else f"Oracle architecture registry status: {registry_status}."
                ),
                "architecture_registry_id": registry_id,
                "record_count": len(records),
                "violation_count": violation_count,
                "operator_note": "Oracle remains read-only. Q Series owns execution.",
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": self.execution_owner,
            },
            "records": [record.__dict__ for record in records],
        }

    def lookup_module(self, registry: Dict[str, Any], module_id: str) -> Dict[str, Any]:
        registry = _safe_dict(registry)
        records = _safe_list(registry.get("records"))
        target = str(module_id or "").strip().lower()

        for record in records:
            record = _safe_dict(record)
            if str(record.get("module_id") or "").strip().lower() == target:
                return {
                    "module": self.name,
                    "version": self.version,
                    "found": True,
                    "module_id": module_id,
                    "record": record,
                    "read_only": True,
                    "execution_allowed": False,
                    "execution_owner": self.execution_owner,
                }

        return {
            "module": self.name,
            "version": self.version,
            "found": False,
            "module_id": module_id,
            "record": None,
            "read_only": True,
            "execution_allowed": False,
            "execution_owner": self.execution_owner,
        }


oracle_architecture_registry_engine = OracleArchitectureRegistryEngine()
