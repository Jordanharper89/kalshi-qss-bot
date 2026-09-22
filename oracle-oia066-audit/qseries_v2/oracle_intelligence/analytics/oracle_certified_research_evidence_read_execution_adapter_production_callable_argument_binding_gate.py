from __future__ import annotations

import hashlib
import importlib
import inspect
import json
import os
import tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "OIA-052"
ENGINE_ID = "OIA-052"
POLICY_ID = "oracle.certified-research-evidence-read-execution-adapter-production-callable-argument-binding.v1"
STATUS_ARGUMENTS_BOUND = "evidence_read_execution_adapter_production_callable_arguments_bound"
STATUS_BINDING_ISSUED = "evidence_read_execution_adapter_production_callable_argument_binding_issued"

DEFAULT_AUTHORIZATION_DIRECTORY = Path("runtime/oracle_intelligence/certified_research_evidence_read_execution_adapter_production_callable_binding_authorization")
DEFAULT_BINDING_DIRECTORY = Path("runtime/oracle_intelligence/certified_research_evidence_read_execution_adapter_production_callable_argument_binding")

APPROVED_CALLABLES = {
    "oracle_read_only_canonical_observation_adapter.v1": {
        "module_path": "qseries_v2.oracle_intelligence.analytics.oracle_live_corpus_inspector",
        "owner_name": "OracleLiveCorpusInspector",
        "callable_name": "inspect",
        "constructor_values": {
            "connection_factory": "symbolic://oracle/runtime/connection_factory",
            "stale_after_seconds": 300,
            "market_limit": 100,
        },
        "callable_values": {"inspected_at": None},
    },
    "oracle_read_only_market_state_lineage_adapter.v1": {
        "module_path": "qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_market_lineage_ledger",
        "owner_name": "OracleCanonicalMarketLineageLedger",
        "callable_name": "records",
        "constructor_values": {},
        "callable_values": {},
    },
}


class ProductionCallableArgumentBindingInvariantError(RuntimeError):
    pass


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _canonical(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ProductionCallableArgumentBindingInvariantError("datetime must be timezone-aware")
        return value.astimezone(timezone.utc).isoformat()
    return value


def stable_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(_canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    ).hexdigest()


def _valid_hash(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _aware(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ProductionCallableArgumentBindingInvariantError(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _atomic_write(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", delete=False, dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    temporary = Path(handle.name)
    try:
        with handle:
            json.dump(_canonical(payload), handle, sort_keys=True, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


@dataclass(frozen=True)
class ProductionCallableArgumentBindingEntry:
    sequence: int
    worker_id: str
    work_item_id: str
    adapter_id: str
    read_operation: str
    module_path: str
    owner_name: str
    callable_name: str
    constructor_signature: str
    callable_signature: str
    bound_constructor_arguments: dict[str, Any]
    bound_callable_arguments: dict[str, Any]
    constructor_binding_hash: str
    callable_binding_hash: str
    owner_instantiated: bool
    callable_bound_to_owner: bool
    callable_invoked: bool
    adapter_executed: bool
    binding_checks: tuple[str, ...]
    binding_status: str
    source_callable_binding_authorization_hash: str
    source_callable_binding_readiness_hash: str
    source_callable_resolution_hash: str
    source_active_invocation_execution_authorization_hash: str
    source_active_invocation_execution_readiness_hash: str
    source_active_execution_invocation_hash: str
    source_execution_invocation_hash: str
    source_authorization_entry_hash: str
    source_readiness_entry_hash: str
    source_active_adapter_invocation_hash: str
    callable_argument_binding_hash: str


@dataclass(frozen=True)
class ProductionCallableArgumentBindingManifest:
    schema_version: str
    engine_id: str
    bound_at: str
    callable_argument_binding_id: str
    callable_argument_binding_status: str
    callable_argument_binding_policy_id: str
    worker_id: str
    binding_entry_count: int
    binding_entries: tuple[ProductionCallableArgumentBindingEntry, ...]
    source_callable_binding_authorization_id: str
    source_callable_binding_authorization_manifest_hash: str
    source_callable_binding_readiness_id: str
    source_callable_binding_readiness_manifest_hash: str
    source_callable_resolution_id: str
    source_callable_resolution_manifest_hash: str
    source_execution_authorization_id: str
    source_execution_authorization_manifest_hash: str
    source_execution_readiness_id: str
    source_execution_readiness_manifest_hash: str
    source_invocation_activation_id: str
    source_invocation_activation_manifest_hash: str
    source_execution_invocation_manifest_id: str
    source_execution_invocation_manifest_hash: str
    source_prior_execution_authorization_id: str
    source_prior_execution_authorization_manifest_hash: str
    source_prior_execution_readiness_id: str
    source_prior_execution_readiness_manifest_hash: str
    source_activation_hash: str
    source_lineage: dict[str, Any]
    symbolic_binding_only: bool
    owner_instantiation_allowed: bool
    owner_instantiation_performed: bool
    constructor_argument_binding_allowed: bool
    constructor_argument_binding_performed: bool
    callable_argument_binding_allowed: bool
    callable_argument_binding_performed: bool
    callable_invocation_evaluation_allowed: bool
    callable_invocation_allowed: bool
    callable_invocation_performed: bool
    adapter_execution_allowed: bool
    adapter_execution_performed: bool
    corpus_read_execution_allowed: bool
    corpus_read_execution_performed: bool
    research_execution_allowed: bool
    analytic_conclusion_allowed: bool
    forecast_creation_allowed: bool
    signals_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    execution_allowed: bool
    trading_recommendations_allowed: bool
    source_mutation_allowed: bool
    market_order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    binding_artifact_persistence_allowed: bool
    callable_argument_binding_manifest_hash: str


class OracleCertifiedResearchEvidenceReadExecutionAdapterProductionCallableArgumentBindingGate:
    def __init__(self, *, authorization_directory: Path | str = DEFAULT_AUTHORIZATION_DIRECTORY, binding_directory: Path | str = DEFAULT_BINDING_DIRECTORY) -> None:
        self.authorization_directory = Path(authorization_directory)
        self.binding_directory = Path(binding_directory)

    def _load_authorization(self) -> dict[str, Any]:
        path = self.authorization_directory / "current.json"
        if not path.exists():
            raise ProductionCallableArgumentBindingInvariantError(f"OIA-051 current authorization artifact missing: {path}")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as error:
            raise ProductionCallableArgumentBindingInvariantError("OIA-051 authorization artifact could not be decoded") from error
        digest = payload.pop("callable_binding_authorization_manifest_hash", None)
        if not _valid_hash(digest) or stable_hash(payload) != digest:
            raise ProductionCallableArgumentBindingInvariantError("OIA-051 authorization manifest hash verification failed")
        payload["callable_binding_authorization_manifest_hash"] = digest
        expected = {
            "schema_version": "OIA-051",
            "engine_id": "OIA-051",
            "callable_binding_authorization_issued": True,
            "constructor_argument_binding_evaluation_allowed": True,
            "callable_argument_binding_evaluation_allowed": True,
            "owner_instantiation_allowed": False,
            "owner_instantiation_performed": False,
            "constructor_argument_binding_allowed": False,
            "constructor_argument_binding_performed": False,
            "callable_argument_binding_allowed": False,
            "callable_argument_binding_performed": False,
            "callable_invocation_allowed": False,
            "callable_invocation_performed": False,
            "adapter_execution_allowed": False,
            "adapter_execution_performed": False,
            "corpus_read_execution_allowed": False,
            "corpus_read_execution_performed": False,
            "signals_allowed": False,
            "alerts_allowed": False,
            "qseries_handoff_allowed": False,
            "execution_allowed": False,
            "market_order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
        }
        for field_name, expected_value in expected.items():
            if payload.get(field_name) != expected_value:
                raise ProductionCallableArgumentBindingInvariantError(f"OIA-051 invariant failed: {field_name}")
        entries = payload.get("authorization_entries")
        count = payload.get("authorization_entry_count")
        if not isinstance(entries, list) or not isinstance(count, int) or isinstance(count, bool) or count < 1 or len(entries) != count:
            raise ProductionCallableArgumentBindingInvariantError("OIA-051 authorization entries invalid")
        seen: set[str] = set()
        for sequence, entry in enumerate(entries, 1):
            if not isinstance(entry, dict):
                raise ProductionCallableArgumentBindingInvariantError("OIA-051 authorization entry invalid")
            entry_hash = entry.pop("callable_binding_authorization_hash", None)
            if not _valid_hash(entry_hash) or stable_hash(entry) != entry_hash:
                raise ProductionCallableArgumentBindingInvariantError("OIA-051 authorization entry hash verification failed")
            entry["callable_binding_authorization_hash"] = entry_hash
            if entry.get("sequence") != sequence:
                raise ProductionCallableArgumentBindingInvariantError("OIA-051 authorization sequence invalid")
            adapter_id = entry.get("adapter_id")
            if adapter_id not in APPROVED_CALLABLES or adapter_id in seen:
                raise ProductionCallableArgumentBindingInvariantError("OIA-051 adapter identity unknown or duplicate")
            seen.add(adapter_id)
            approved = APPROVED_CALLABLES[adapter_id]
            for field_name in ("module_path", "owner_name", "callable_name"):
                if entry.get(field_name) != approved[field_name]:
                    raise ProductionCallableArgumentBindingInvariantError(f"OIA-051 approved callable mismatch: {field_name}")
            for field_name, expected_value in {
                "binding_authorized": True,
                "owner_instantiated": False,
                "constructor_arguments_bound": False,
                "callable_arguments_bound": False,
                "callable_invoked": False,
                "adapter_executed": False,
            }.items():
                if entry.get(field_name) != expected_value:
                    raise ProductionCallableArgumentBindingInvariantError(f"OIA-051 entry invariant failed: {field_name}")
            expected_constructor = tuple(approved["constructor_values"].keys())
            expected_callable = tuple(approved["callable_values"].keys())
            if tuple(entry.get("authorized_constructor_parameters", ())) != expected_constructor:
                raise ProductionCallableArgumentBindingInvariantError("OIA-051 constructor parameter authorization mismatch")
            if tuple(entry.get("authorized_callable_parameters", ())) != expected_callable:
                raise ProductionCallableArgumentBindingInvariantError("OIA-051 callable parameter authorization mismatch")
        return payload

    def bind(self, *, bound_at: datetime, persist: bool = True) -> ProductionCallableArgumentBindingManifest:
        bound_at = _aware(bound_at, "bound_at")
        source = self._load_authorization()
        output: list[ProductionCallableArgumentBindingEntry] = []
        for sequence, authorization in enumerate(source["authorization_entries"], 1):
            adapter_id = authorization["adapter_id"]
            approved = APPROVED_CALLABLES[adapter_id]
            module = importlib.import_module(approved["module_path"])
            owner = getattr(module, approved["owner_name"], None)
            if not inspect.isclass(owner):
                raise ProductionCallableArgumentBindingInvariantError("Approved owner class did not resolve")
            callable_object = inspect.getattr_static(owner, approved["callable_name"], None)
            if callable_object is None or not callable(callable_object):
                raise ProductionCallableArgumentBindingInvariantError("Approved callable did not resolve")
            constructor_signature = inspect.signature(owner)
            callable_signature = inspect.signature(callable_object)
            if str(constructor_signature) != authorization["constructor_signature"]:
                raise ProductionCallableArgumentBindingInvariantError("Constructor signature changed after OIA-051")
            if str(callable_signature) != authorization["callable_signature"]:
                raise ProductionCallableArgumentBindingInvariantError("Callable signature changed after OIA-051")
            constructor_values = dict(approved["constructor_values"])
            callable_values = dict(approved["callable_values"])
            try:
                constructor_bound = constructor_signature.bind(**constructor_values)
                constructor_bound.apply_defaults()
                callable_bound = callable_signature.bind("symbolic://oracle/owner_instance", **callable_values)
                callable_bound.apply_defaults()
            except TypeError as error:
                raise ProductionCallableArgumentBindingInvariantError("Approved symbolic argument binding failed") from error
            bound_constructor_arguments = dict(constructor_bound.arguments)
            bound_callable_arguments = dict(callable_bound.arguments)
            if "self" in bound_callable_arguments:
                bound_callable_arguments["self"] = "symbolic://oracle/owner_instance"
            entry_body = {
                "sequence": sequence,
                "worker_id": authorization["worker_id"],
                "work_item_id": authorization["work_item_id"],
                "adapter_id": adapter_id,
                "read_operation": authorization["read_operation"],
                "module_path": approved["module_path"],
                "owner_name": approved["owner_name"],
                "callable_name": approved["callable_name"],
                "constructor_signature": str(constructor_signature),
                "callable_signature": str(callable_signature),
                "bound_constructor_arguments": bound_constructor_arguments,
                "bound_callable_arguments": bound_callable_arguments,
                "constructor_binding_hash": stable_hash(bound_constructor_arguments),
                "callable_binding_hash": stable_hash(bound_callable_arguments),
                "owner_instantiated": False,
                "callable_bound_to_owner": False,
                "callable_invoked": False,
                "adapter_executed": False,
                "binding_checks": (
                    "oia051_authorization_manifest_hash_verified",
                    "oia051_authorization_entry_hash_verified",
                    "approved_module_identity_verified",
                    "approved_owner_identity_verified",
                    "approved_callable_identity_verified",
                    "constructor_signature_verified",
                    "callable_signature_verified",
                    "constructor_parameter_allowlist_verified",
                    "callable_parameter_allowlist_verified",
                    "symbolic_constructor_arguments_bound",
                    "symbolic_callable_arguments_bound",
                    "owner_not_instantiated",
                    "callable_not_bound_to_owner",
                    "callable_not_invoked",
                    "adapter_not_executed",
                    "oracle_qseries_boundary_verified",
                ),
                "binding_status": STATUS_ARGUMENTS_BOUND,
                "source_callable_binding_authorization_hash": authorization["callable_binding_authorization_hash"],
                "source_callable_binding_readiness_hash": authorization["source_callable_binding_readiness_hash"],
                "source_callable_resolution_hash": authorization["source_callable_resolution_hash"],
                "source_active_invocation_execution_authorization_hash": authorization["source_active_invocation_execution_authorization_hash"],
                "source_active_invocation_execution_readiness_hash": authorization["source_active_invocation_execution_readiness_hash"],
                "source_active_execution_invocation_hash": authorization["source_active_execution_invocation_hash"],
                "source_execution_invocation_hash": authorization["source_execution_invocation_hash"],
                "source_authorization_entry_hash": authorization["source_authorization_entry_hash"],
                "source_readiness_entry_hash": authorization["source_readiness_entry_hash"],
                "source_active_adapter_invocation_hash": authorization["source_active_adapter_invocation_hash"],
            }
            output.append(ProductionCallableArgumentBindingEntry(**entry_body, callable_argument_binding_hash=stable_hash(entry_body)))
        source_manifest_hash = source["callable_binding_authorization_manifest_hash"]
        binding_id = "oia052-callable-argument-binding-" + stable_hash({"source": source_manifest_hash, "policy": POLICY_ID})[:32]
        manifest_body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "bound_at": bound_at.isoformat(),
            "callable_argument_binding_id": binding_id,
            "callable_argument_binding_status": STATUS_BINDING_ISSUED,
            "callable_argument_binding_policy_id": POLICY_ID,
            "worker_id": source["worker_id"],
            "binding_entry_count": len(output),
            "binding_entries": tuple(output),
            "source_callable_binding_authorization_id": source["callable_binding_authorization_id"],
            "source_callable_binding_authorization_manifest_hash": source_manifest_hash,
            "source_callable_binding_readiness_id": source["source_callable_binding_readiness_id"],
            "source_callable_binding_readiness_manifest_hash": source["source_callable_binding_readiness_manifest_hash"],
            "source_callable_resolution_id": source["source_callable_resolution_id"],
            "source_callable_resolution_manifest_hash": source["source_callable_resolution_manifest_hash"],
            "source_execution_authorization_id": source["source_execution_authorization_id"],
            "source_execution_authorization_manifest_hash": source["source_execution_authorization_manifest_hash"],
            "source_execution_readiness_id": source["source_execution_readiness_id"],
            "source_execution_readiness_manifest_hash": source["source_execution_readiness_manifest_hash"],
            "source_invocation_activation_id": source["source_invocation_activation_id"],
            "source_invocation_activation_manifest_hash": source["source_invocation_activation_manifest_hash"],
            "source_execution_invocation_manifest_id": source["source_execution_invocation_manifest_id"],
            "source_execution_invocation_manifest_hash": source["source_execution_invocation_manifest_hash"],
            "source_prior_execution_authorization_id": source["source_prior_execution_authorization_id"],
            "source_prior_execution_authorization_manifest_hash": source["source_prior_execution_authorization_manifest_hash"],
            "source_prior_execution_readiness_id": source["source_prior_execution_readiness_id"],
            "source_prior_execution_readiness_manifest_hash": source["source_prior_execution_readiness_manifest_hash"],
            "source_activation_hash": source["source_activation_hash"],
            "source_lineage": dict(source["source_lineage"]),
            "symbolic_binding_only": True,
            "owner_instantiation_allowed": False,
            "owner_instantiation_performed": False,
            "constructor_argument_binding_allowed": True,
            "constructor_argument_binding_performed": True,
            "callable_argument_binding_allowed": True,
            "callable_argument_binding_performed": True,
            "callable_invocation_evaluation_allowed": True,
            "callable_invocation_allowed": False,
            "callable_invocation_performed": False,
            "adapter_execution_allowed": False,
            "adapter_execution_performed": False,
            "corpus_read_execution_allowed": False,
            "corpus_read_execution_performed": False,
            "research_execution_allowed": False,
            "analytic_conclusion_allowed": False,
            "forecast_creation_allowed": False,
            "signals_allowed": False,
            "alerts_allowed": False,
            "qseries_handoff_allowed": False,
            "execution_allowed": False,
            "trading_recommendations_allowed": False,
            "source_mutation_allowed": False,
            "market_order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
            "binding_artifact_persistence_allowed": True,
        }
        serializable = dict(manifest_body)
        serializable["binding_entries"] = [asdict(entry) for entry in output]
        result = ProductionCallableArgumentBindingManifest(**manifest_body, callable_argument_binding_manifest_hash=stable_hash(serializable))
        if persist:
            payload = asdict(result)
            _atomic_write(self.binding_directory / "current.json", payload)
            _atomic_write(self.binding_directory / "bindings" / f"{binding_id}.json", payload)
            _atomic_write(self.binding_directory / "workers" / result.worker_id / f"{binding_id}.json", payload)
        return result
