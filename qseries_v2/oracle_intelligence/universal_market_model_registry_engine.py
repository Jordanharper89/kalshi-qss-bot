"""
OI-164 — Oracle Universal Market Model Registry Engine

Read-only registry engine for Universal Market Model domain support.

Purpose:
- Register supported market domains for Oracle Intelligence expansion.
- Preserve adapter requirements, data model expectations, domain readiness,
  replayability, explainability, and execution boundaries.
- Keep Oracle as one universal intelligence engine, not separate Oracle instances.

Oracle never executes trades, manages positions, or submits orders.
Execution ownership remains with Q Series.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, Iterable, List


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
class UniversalMarketDomainRecord:
    domain_record_id: str
    domain: str
    adapter_type: str
    data_model: str
    readiness_status: str
    adapter_required: bool
    replayable: bool
    explainable: bool
    historical_memory_enabled: bool
    telemetry_enabled: bool
    execution_allowed: bool
    execution_owner: str
    read_only: bool
    required_fields: List[str] = field(default_factory=list)
    optional_fields: List[str] = field(default_factory=list)
    lineage_hash: str = ""


@dataclass
class OracleUniversalMarketModelRegistryEngine:
    name: str = "oracle_universal_market_model_registry_engine"
    version: str = "OI-164"
    read_only: bool = True
    execution_allowed: bool = False
    execution_owner: str = "Q Series"
    registry_schema_version: str = "universal_market_model_registry_v1"

    default_domains: List[str] = field(default_factory=lambda: [
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

    default_required_fields: List[str] = field(default_factory=lambda: [
        "domain",
        "symbol",
        "timestamp",
        "source",
        "price",
        "confidence",
        "lineage",
    ])

    default_optional_fields: List[str] = field(default_factory=lambda: [
        "volume",
        "open_interest",
        "bid",
        "ask",
        "spread",
        "event_id",
        "contract_id",
        "forecast_value",
        "sentiment_score",
        "macro_series_id",
    ])

    def classify_readiness(self, domain: Dict[str, Any]) -> str:
        domain = _safe_dict(domain)

        if domain.get("read_only") is not True:
            return "blocked_read_only_violation"
        if domain.get("execution_allowed") is not False:
            return "blocked_execution_violation"
        if domain.get("execution_owner") != "Q Series":
            return "blocked_execution_owner_violation"

        adapter_required = domain.get("adapter_required", True) is True
        data_model = str(domain.get("data_model") or "").strip()
        replayable = domain.get("replayable", True) is True
        explainable = domain.get("explainable", True) is True
        telemetry_enabled = domain.get("telemetry_enabled", True) is True
        historical_memory_enabled = domain.get("historical_memory_enabled", True) is True

        if adapter_required and data_model and replayable and explainable and telemetry_enabled and historical_memory_enabled:
            return "umm_domain_ready"

        if data_model and replayable and explainable:
            return "umm_domain_ready_with_review"

        return "umm_domain_incomplete"

    def register_domain(self, domain: Dict[str, Any]) -> UniversalMarketDomainRecord:
        domain = _safe_dict(domain)

        domain_name = str(domain.get("domain") or "UNKNOWN").upper()
        adapter_type = str(domain.get("adapter_type") or f"{domain_name.lower()}_adapter")
        data_model = str(domain.get("data_model") or "UniversalMarketRecord")

        required_fields = _safe_list(domain.get("required_fields")) or list(self.default_required_fields)
        optional_fields = _safe_list(domain.get("optional_fields")) or list(self.default_optional_fields)

        payload = {
            "domain": domain_name,
            "adapter_type": adapter_type,
            "data_model": data_model,
            "required_fields": required_fields,
            "optional_fields": optional_fields,
            "read_only": domain.get("read_only", True),
            "execution_allowed": domain.get("execution_allowed", False),
            "execution_owner": domain.get("execution_owner", "Q Series"),
        }

        lineage_hash = _hash(payload)

        return UniversalMarketDomainRecord(
            domain_record_id=_hash({"domain": payload, "lineage": lineage_hash}),
            domain=domain_name,
            adapter_type=adapter_type,
            data_model=data_model,
            readiness_status=self.classify_readiness({
                **domain,
                "data_model": data_model,
                "read_only": domain.get("read_only", True),
                "execution_allowed": domain.get("execution_allowed", False),
                "execution_owner": domain.get("execution_owner", "Q Series"),
            }),
            adapter_required=domain.get("adapter_required", True) is True,
            replayable=domain.get("replayable", True) is True,
            explainable=domain.get("explainable", True) is True,
            historical_memory_enabled=domain.get("historical_memory_enabled", True) is True,
            telemetry_enabled=domain.get("telemetry_enabled", True) is True,
            execution_allowed=domain.get("execution_allowed", False) is True,
            execution_owner=str(domain.get("execution_owner") or "Q Series"),
            read_only=domain.get("read_only", True) is True,
            required_fields=[str(x) for x in required_fields],
            optional_fields=[str(x) for x in optional_fields],
            lineage_hash=lineage_hash,
        )

    def build_registry(self, domains: Iterable[Dict[str, Any]] = None) -> Dict[str, Any]:
        if domains is None:
            domains = [{"domain": d} for d in self.default_domains]

        records = [self.register_domain(domain) for domain in domains]
        records.sort(key=lambda r: r.domain)

        status_counts: Dict[str, int] = {}
        adapter_counts: Dict[str, int] = {}
        violation_count = 0
        ready_count = 0

        for record in records:
            status_counts[record.readiness_status] = status_counts.get(record.readiness_status, 0) + 1
            adapter_counts[record.adapter_type] = adapter_counts.get(record.adapter_type, 0) + 1

            if "blocked" in record.readiness_status:
                violation_count += 1
            if record.readiness_status == "umm_domain_ready":
                ready_count += 1

        registry_id = _hash([record.__dict__ for record in records])

        if not records:
            registry_status = "empty_umm_registry"
        elif violation_count:
            registry_status = "umm_registry_blocked"
        elif ready_count == len(records):
            registry_status = "umm_registry_ready"
        else:
            registry_status = "umm_registry_ready_with_review"

        return {
            "module": self.name,
            "version": self.version,
            "registry_schema_version": self.registry_schema_version,
            "umm_registry_id": registry_id,
            "registry_status": registry_status,
            "created_at": _utc_now(),
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "execution_owner": self.execution_owner,
            "single_oracle_instance": True,
            "adapter_based_expansion": True,
            "domain_count": len(records),
            "ready_count": ready_count,
            "violation_count": violation_count,
            "status_counts": status_counts,
            "adapter_counts": adapter_counts,
            "executive_summary": {
                "headline": (
                    "Universal Market Model registry is ready."
                    if registry_status == "umm_registry_ready"
                    else f"Universal Market Model registry status: {registry_status}."
                ),
                "umm_registry_id": registry_id,
                "domain_count": len(records),
                "ready_count": ready_count,
                "violation_count": violation_count,
                "operator_note": "Oracle remains one read-only universal intelligence engine. Q Series owns execution.",
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": self.execution_owner,
            },
            "records": [record.__dict__ for record in records],
        }

    def lookup_domain(self, registry: Dict[str, Any], domain: str) -> Dict[str, Any]:
        registry = _safe_dict(registry)
        records = _safe_list(registry.get("records"))
        target = str(domain or "").strip().upper()

        for record in records:
            record = _safe_dict(record)
            if str(record.get("domain") or "").strip().upper() == target:
                return {
                    "module": self.name,
                    "version": self.version,
                    "found": True,
                    "domain": target,
                    "record": record,
                    "read_only": True,
                    "execution_allowed": False,
                    "execution_owner": self.execution_owner,
                }

        return {
            "module": self.name,
            "version": self.version,
            "found": False,
            "domain": target,
            "record": None,
            "read_only": True,
            "execution_allowed": False,
            "execution_owner": self.execution_owner,
        }


oracle_universal_market_model_registry_engine = OracleUniversalMarketModelRegistryEngine()
