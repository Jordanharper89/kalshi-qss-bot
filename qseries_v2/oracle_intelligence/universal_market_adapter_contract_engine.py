"""
OI-166 — Oracle Universal Market Adapter Contract Engine

Read-only adapter contract engine for Universal Market Model expansion.

Purpose:
- Define adapter contracts for every market domain before data enters Oracle.
- Validate adapter metadata, required capabilities, schema compatibility,
  replayability, explainability, lineage, telemetry, and safety boundaries.
- Keep Oracle universal and read-only while adapters normalize external data.

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
class AdapterContractIssue:
    adapter_id: str
    severity: str
    code: str
    message: str


@dataclass
class UniversalMarketAdapterContract:
    contract_id: str
    adapter_id: str
    adapter_name: str
    domain: str
    adapter_type: str
    schema_version: str
    contract_status: str
    required_capabilities: List[str]
    provided_capabilities: List[str]
    missing_capabilities: List[str]
    lineage_hash: str
    read_only: bool = True
    execution_allowed: bool = False
    execution_owner: str = "Q Series"


@dataclass
class OracleUniversalMarketAdapterContractEngine:
    name: str = "oracle_universal_market_adapter_contract_engine"
    version: str = "OI-166"
    read_only: bool = True
    execution_allowed: bool = False
    execution_owner: str = "Q Series"
    contract_schema_version: str = "universal_market_adapter_contract_v1"

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

    required_capabilities: List[str] = field(default_factory=lambda: [
        "normalize_to_umm",
        "preserve_lineage",
        "provide_timestamp",
        "provide_source",
        "provide_confidence",
        "read_only_ingestion",
        "replayable_output",
        "explainable_output",
        "telemetry_enabled",
    ])

    def evaluate_contract_status(self, adapter: Dict[str, Any]) -> str:
        adapter = _safe_dict(adapter)

        if adapter.get("read_only") is not True:
            return "blocked_read_only_violation"
        if adapter.get("execution_allowed") is not False:
            return "blocked_execution_violation"
        if adapter.get("execution_owner") != "Q Series":
            return "blocked_execution_owner_violation"

        domain = str(adapter.get("domain") or "").upper()
        if domain not in self.supported_domains:
            return "adapter_domain_unsupported"

        provided = set(str(x) for x in _safe_list(adapter.get("provided_capabilities")))
        missing = [cap for cap in self.required_capabilities if cap not in provided]

        if not missing:
            return "adapter_contract_ready"
        if len(missing) <= 2:
            return "adapter_contract_ready_with_review"
        return "adapter_contract_incomplete"

    def create_contract(self, adapter: Dict[str, Any]) -> UniversalMarketAdapterContract:
        adapter = _safe_dict(adapter)

        adapter_id = str(adapter.get("adapter_id") or _hash(adapter, 12))
        adapter_name = str(adapter.get("adapter_name") or adapter.get("name") or "unknown_adapter")
        domain = str(adapter.get("domain") or "UNKNOWN").upper()
        adapter_type = str(adapter.get("adapter_type") or f"{domain.lower()}_adapter")
        schema_version = str(adapter.get("schema_version") or "universal_market_model_schema_v1")

        provided = [str(x) for x in _safe_list(adapter.get("provided_capabilities"))]
        missing = [cap for cap in self.required_capabilities if cap not in set(provided)]

        payload = {
            "adapter_id": adapter_id,
            "adapter_name": adapter_name,
            "domain": domain,
            "adapter_type": adapter_type,
            "schema_version": schema_version,
            "provided_capabilities": provided,
            "read_only": adapter.get("read_only", True),
            "execution_allowed": adapter.get("execution_allowed", False),
            "execution_owner": adapter.get("execution_owner", "Q Series"),
        }

        lineage_hash = _hash(payload)

        return UniversalMarketAdapterContract(
            contract_id=_hash({"payload": payload, "lineage": lineage_hash}),
            adapter_id=adapter_id,
            adapter_name=adapter_name,
            domain=domain,
            adapter_type=adapter_type,
            schema_version=schema_version,
            contract_status=self.evaluate_contract_status({
                **adapter,
                "domain": domain,
                "provided_capabilities": provided,
                "read_only": adapter.get("read_only", True),
                "execution_allowed": adapter.get("execution_allowed", False),
                "execution_owner": adapter.get("execution_owner", "Q Series"),
            }),
            required_capabilities=list(self.required_capabilities),
            provided_capabilities=provided,
            missing_capabilities=missing,
            lineage_hash=lineage_hash,
            read_only=adapter.get("read_only", True) is True,
            execution_allowed=adapter.get("execution_allowed", False) is True,
            execution_owner=str(adapter.get("execution_owner") or "Q Series"),
        )

    def validate_contract(self, contract: UniversalMarketAdapterContract) -> List[AdapterContractIssue]:
        issues: List[AdapterContractIssue] = []

        if contract.read_only is not True:
            issues.append(AdapterContractIssue(
                adapter_id=contract.adapter_id,
                severity="critical",
                code="read_only_violation",
                message="Adapter contract must be read_only=True.",
            ))

        if contract.execution_allowed is not False:
            issues.append(AdapterContractIssue(
                adapter_id=contract.adapter_id,
                severity="critical",
                code="execution_violation",
                message="Adapter contract must not allow execution.",
            ))

        if contract.execution_owner != "Q Series":
            issues.append(AdapterContractIssue(
                adapter_id=contract.adapter_id,
                severity="critical",
                code="execution_owner_violation",
                message="Adapter contract execution_owner must be Q Series.",
            ))

        if contract.domain not in self.supported_domains:
            issues.append(AdapterContractIssue(
                adapter_id=contract.adapter_id,
                severity="warning",
                code="unsupported_domain",
                message=f"Adapter domain {contract.domain} is not currently supported.",
            ))

        for capability in contract.missing_capabilities:
            issues.append(AdapterContractIssue(
                adapter_id=contract.adapter_id,
                severity="warning",
                code="missing_capability",
                message=f"Adapter missing required capability: {capability}",
            ))

        if not contract.lineage_hash:
            issues.append(AdapterContractIssue(
                adapter_id=contract.adapter_id,
                severity="critical",
                code="missing_lineage",
                message="Adapter contract missing lineage hash.",
            ))

        return issues

    def build_contract_registry(self, adapters: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        contracts = [self.create_contract(adapter) for adapter in adapters]
        contracts.sort(key=lambda c: c.adapter_id)

        all_issues: List[AdapterContractIssue] = []
        status_counts: Dict[str, int] = {}
        domain_counts: Dict[str, int] = {}

        for contract in contracts:
            status_counts[contract.contract_status] = status_counts.get(contract.contract_status, 0) + 1
            domain_counts[contract.domain] = domain_counts.get(contract.domain, 0) + 1
            all_issues.extend(self.validate_contract(contract))

        critical_count = sum(1 for issue in all_issues if issue.severity == "critical")
        warning_count = sum(1 for issue in all_issues if issue.severity == "warning")
        ready_count = sum(1 for c in contracts if c.contract_status == "adapter_contract_ready")

        if not contracts:
            registry_status = "empty_adapter_contract_registry"
        elif critical_count:
            registry_status = "adapter_contract_registry_blocked"
        elif warning_count:
            registry_status = "adapter_contract_registry_ready_with_warnings"
        else:
            registry_status = "adapter_contract_registry_ready"

        registry_id = _hash({
            "contracts": [contract.__dict__ for contract in contracts],
            "issues": [issue.__dict__ for issue in all_issues],
        })

        return {
            "module": self.name,
            "version": self.version,
            "contract_schema_version": self.contract_schema_version,
            "adapter_contract_registry_id": registry_id,
            "registry_status": registry_status,
            "created_at": _utc_now(),
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "execution_owner": self.execution_owner,
            "single_oracle_instance": True,
            "adapter_based_expansion": True,
            "contract_count": len(contracts),
            "ready_count": ready_count,
            "issue_count": len(all_issues),
            "critical_count": critical_count,
            "warning_count": warning_count,
            "status_counts": status_counts,
            "domain_counts": domain_counts,
            "executive_summary": {
                "headline": (
                    "Universal Market adapter contract registry is ready."
                    if registry_status == "adapter_contract_registry_ready"
                    else f"Universal Market adapter contract registry status: {registry_status}."
                ),
                "adapter_contract_registry_id": registry_id,
                "contract_count": len(contracts),
                "ready_count": ready_count,
                "issue_count": len(all_issues),
                "operator_note": "Adapters normalize data only. Oracle remains read-only. Q Series owns execution.",
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": self.execution_owner,
            },
            "contracts": [contract.__dict__ for contract in contracts],
            "issues": [issue.__dict__ for issue in all_issues],
        }


oracle_universal_market_adapter_contract_engine = OracleUniversalMarketAdapterContractEngine()
