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
from types import MappingProxyType
from typing import Any, Mapping

SCHEMA_VERSION = "OIA-050"
ENGINE_ID = "OIA-050"
POLICY_ID = (
    "oracle.certified-research-evidence-read-execution-adapter-"
    "production-callable-binding-readiness.v1"
)
STATUS_BINDING_READY = (
    "evidence_read_execution_adapter_production_callable_binding_ready"
)
STATUS_BINDING_READINESS_ISSUED = (
    "evidence_read_execution_adapter_production_callable_binding_readiness_issued"
)

DEFAULT_RESOLUTION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "certified_research_evidence_read_execution_adapter_production_callable_resolution"
)
DEFAULT_BINDING_READINESS_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "certified_research_evidence_read_execution_adapter_production_callable_binding_readiness"
)

APPROVED_BINDING_SIGNATURE_REGISTRY = MappingProxyType({
    "oracle_read_only_canonical_observation_adapter.v1": MappingProxyType({
        "read_operation": "read_canonical_observations",
        "module_path": (
            "qseries_v2.oracle_intelligence.analytics."
            "oracle_live_corpus_inspector"
        ),
        "owner_name": "OracleLiveCorpusInspector",
        "callable_name": "inspect",
        "callable_kind": "instance_method",
        "constructor_signature": (
            "(*, connection_factory: 'Callable[[], Any]', "
            "stale_after_seconds: 'int' = 300, market_limit: 'int' = 100)"
        ),
        "callable_signature": (
            "(self, *, inspected_at: 'Optional[datetime]' = None) "
            "-> 'OracleLiveCorpusReport'"
        ),
        "required_constructor_parameters": ("connection_factory",),
        "optional_constructor_parameters": (
            "stale_after_seconds",
            "market_limit",
        ),
        "required_callable_parameters": (),
        "optional_callable_parameters": ("inspected_at",),
    }),
    "oracle_read_only_market_state_lineage_adapter.v1": MappingProxyType({
        "read_operation": "read_market_state_lineage",
        "module_path": (
            "qseries_v2.oracle_intelligence.live_acquisition."
            "oracle_canonical_market_lineage_ledger"
        ),
        "owner_name": "OracleCanonicalMarketLineageLedger",
        "callable_name": "records",
        "callable_kind": "instance_method",
        "constructor_signature": "() -> 'None'",
        "callable_signature": (
            "(self) -> "
            "'tuple[CanonicalMarketStateDwellChangeLineage, ...]'"
        ),
        "required_constructor_parameters": (),
        "optional_constructor_parameters": (),
        "required_callable_parameters": (),
        "optional_callable_parameters": (),
    }),
})


class ProductionCallableBindingReadinessError(RuntimeError):
    pass


class ProductionCallableBindingReadinessInvariantError(
    ProductionCallableBindingReadinessError
):
    pass


class ProductionCallableBindingReadinessImportError(
    ProductionCallableBindingReadinessError
):
    pass


def _aware_utc(value: datetime, field_name: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise ProductionCallableBindingReadinessInvariantError(
            f"{field_name} must be timezone-aware."
        )
    return value.astimezone(timezone.utc)


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _canonical(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    if isinstance(value, datetime):
        return _aware_utc(value, "datetime").isoformat()
    return value


def stable_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            _canonical(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _valid_hash(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _atomic_write(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(
        _canonical(payload),
        sort_keys=True,
        indent=2,
        ensure_ascii=False,
    ) + "\n"
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        delete=False,
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary = Path(handle.name)
    try:
        with handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _parameter_groups(signature: inspect.Signature, *, skip_self: bool) -> tuple[tuple[str, ...], tuple[str, ...]]:
    required: list[str] = []
    optional: list[str] = []
    for name, parameter in signature.parameters.items():
        if skip_self and name in {"self", "cls"}:
            continue
        if parameter.kind in {
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        }:
            raise ProductionCallableBindingReadinessInvariantError(
                "Variadic parameters are prohibited at the deterministic binding boundary."
            )
        if parameter.default is inspect.Parameter.empty:
            required.append(name)
        else:
            optional.append(name)
    return tuple(required), tuple(optional)


@dataclass(frozen=True)
class ProductionCallableBindingReadinessEntry:
    sequence: int
    worker_id: str
    work_item_id: str
    adapter_id: str
    read_operation: str
    module_path: str
    owner_name: str
    callable_name: str
    callable_kind: str
    callable_qualified_name: str
    constructor_signature: str
    callable_signature: str
    required_constructor_parameters: tuple[str, ...]
    optional_constructor_parameters: tuple[str, ...]
    required_callable_parameters: tuple[str, ...]
    optional_callable_parameters: tuple[str, ...]
    module_imported: bool
    owner_resolved: bool
    callable_resolved: bool
    signature_inspection_performed: bool
    owner_instantiated: bool
    constructor_arguments_bound: bool
    callable_arguments_bound: bool
    callable_invoked: bool
    adapter_executed: bool
    readiness_checks: tuple[str, ...]
    readiness_status: str
    source_callable_resolution_hash: str
    source_active_invocation_execution_authorization_hash: str
    source_active_invocation_execution_readiness_hash: str
    source_active_execution_invocation_hash: str
    source_execution_invocation_hash: str
    source_authorization_entry_hash: str
    source_readiness_entry_hash: str
    source_active_adapter_invocation_hash: str
    callable_binding_readiness_hash: str


@dataclass(frozen=True)
class ProductionCallableBindingReadinessManifest:
    schema_version: str
    engine_id: str
    evaluated_at: str
    callable_binding_readiness_id: str
    callable_binding_readiness_status: str
    callable_binding_readiness_policy_id: str
    worker_id: str
    readiness_entry_count: int
    readiness_entries: tuple[ProductionCallableBindingReadinessEntry, ...]
    approved_binding_signature_registry_hash: str
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
    callable_binding_readiness_issued: bool
    module_import_allowed: bool
    module_import_performed: bool
    signature_inspection_allowed: bool
    signature_inspection_performed: bool
    owner_instantiation_allowed: bool
    owner_instantiation_performed: bool
    constructor_argument_binding_allowed: bool
    constructor_argument_binding_performed: bool
    callable_argument_binding_allowed: bool
    callable_argument_binding_performed: bool
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
    readiness_artifact_persistence_allowed: bool
    callable_binding_readiness_manifest_hash: str


class OracleCertifiedResearchEvidenceReadExecutionAdapterProductionCallableBindingReadinessGate:
    """OIA-050 static signature-certification boundary.

    Approved modules may be imported and their class/method signatures inspected.
    Owners are never instantiated. Constructor and method arguments are never
    bound. Callables are never invoked. No corpus read or execution occurs.
    """

    def __init__(
        self,
        *,
        resolution_directory: Path | str = DEFAULT_RESOLUTION_DIRECTORY,
        binding_readiness_directory: Path | str = DEFAULT_BINDING_READINESS_DIRECTORY,
    ) -> None:
        self.resolution_directory = Path(resolution_directory)
        self.binding_readiness_directory = Path(binding_readiness_directory)

    def _load_resolution_manifest(self) -> dict[str, Any]:
        current = self.resolution_directory / "current.json"
        if not current.exists():
            raise ProductionCallableBindingReadinessInvariantError(
                f"OIA-049 current callable-resolution artifact missing: {current}"
            )
        try:
            source = json.loads(current.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ProductionCallableBindingReadinessInvariantError(
                "OIA-049 callable-resolution artifact could not be decoded."
            ) from error
        if not isinstance(source, dict):
            raise ProductionCallableBindingReadinessInvariantError(
                "OIA-049 callable-resolution artifact must be an object."
            )
        manifest_hash = source.pop("callable_resolution_manifest_hash", None)
        if not _valid_hash(manifest_hash) or stable_hash(source) != manifest_hash:
            raise ProductionCallableBindingReadinessInvariantError(
                "OIA-049 callable-resolution manifest hash verification failed."
            )
        source["callable_resolution_manifest_hash"] = manifest_hash

        expected = {
            "schema_version": "OIA-049",
            "engine_id": "OIA-049",
            "callable_resolution_status": (
                "evidence_read_execution_adapter_production_callable_resolution_issued"
            ),
            "callable_resolution_issued": True,
            "module_import_allowed": True,
            "module_import_performed": True,
            "owner_resolution_allowed": True,
            "owner_resolution_performed": True,
            "callable_resolution_allowed": True,
            "callable_resolution_performed": True,
            "owner_instantiation_allowed": False,
            "owner_instantiation_performed": False,
            "callable_binding_allowed": False,
            "callable_binding_performed": False,
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
            "resolution_artifact_persistence_allowed": True,
        }
        for field_name, expected_value in expected.items():
            if source.get(field_name) != expected_value:
                raise ProductionCallableBindingReadinessInvariantError(
                    f"OIA-049 invariant failed: {field_name}."
                )

        entries = source.get("resolution_entries")
        count = source.get("resolution_entry_count")
        if not isinstance(entries, list) or not isinstance(count, int) or count < 1 or len(entries) != count:
            raise ProductionCallableBindingReadinessInvariantError(
                "OIA-049 resolution-entry collection is invalid."
            )
        if count != len(APPROVED_BINDING_SIGNATURE_REGISTRY):
            raise ProductionCallableBindingReadinessInvariantError(
                "OIA-049 did not resolve the complete approved callable registry."
            )

        seen: set[str] = set()
        for expected_sequence, entry in enumerate(entries, start=1):
            if not isinstance(entry, dict):
                raise ProductionCallableBindingReadinessInvariantError(
                    "OIA-049 resolution entry must be an object."
                )
            entry_hash = entry.pop("callable_resolution_hash", None)
            if not _valid_hash(entry_hash) or stable_hash(entry) != entry_hash:
                raise ProductionCallableBindingReadinessInvariantError(
                    "OIA-049 callable-resolution entry hash verification failed."
                )
            entry["callable_resolution_hash"] = entry_hash
            if entry.get("sequence") != expected_sequence:
                raise ProductionCallableBindingReadinessInvariantError(
                    "OIA-049 resolution-entry sequence is non-canonical."
                )
            adapter_id = entry.get("adapter_id")
            if adapter_id in seen:
                raise ProductionCallableBindingReadinessInvariantError(
                    "OIA-049 contains a duplicate adapter identity."
                )
            seen.add(adapter_id)
            registry = APPROVED_BINDING_SIGNATURE_REGISTRY.get(adapter_id)
            if registry is None:
                raise ProductionCallableBindingReadinessInvariantError(
                    "OIA-049 contains an unapproved adapter identity."
                )
            for field_name in (
                "read_operation", "module_path", "owner_name",
                "callable_name", "callable_kind",
            ):
                if entry.get(field_name) != registry[field_name]:
                    raise ProductionCallableBindingReadinessInvariantError(
                        f"OIA-049 callable identity mismatch: {field_name}."
                    )
            for field_name, expected_value in {
                "module_imported": True,
                "owner_resolved": True,
                "callable_resolved": True,
                "owner_instantiated": False,
                "callable_bound": False,
                "callable_invoked": False,
                "adapter_executed": False,
                "resolution_status": (
                    "evidence_read_execution_adapter_production_callable_resolved"
                ),
            }.items():
                if entry.get(field_name) != expected_value:
                    raise ProductionCallableBindingReadinessInvariantError(
                        f"OIA-049 resolution entry invariant failed: {field_name}."
                    )
            for hash_field in (
                "source_active_invocation_execution_authorization_hash",
                "source_active_invocation_execution_readiness_hash",
                "source_active_execution_invocation_hash",
                "source_execution_invocation_hash",
                "source_authorization_entry_hash",
                "source_readiness_entry_hash",
                "source_active_adapter_invocation_hash",
            ):
                if not _valid_hash(entry.get(hash_field)):
                    raise ProductionCallableBindingReadinessInvariantError(
                        f"OIA-049 lineage hash invalid: {hash_field}."
                    )
        if seen != set(APPROVED_BINDING_SIGNATURE_REGISTRY):
            raise ProductionCallableBindingReadinessInvariantError(
                "OIA-049 approved callable registry coverage is incomplete."
            )
        if not isinstance(source.get("source_lineage"), dict) or not source["source_lineage"]:
            raise ProductionCallableBindingReadinessInvariantError(
                "OIA-049 lineage is missing."
            )
        return source

    def _inspect_entry(self, source_entry: Mapping[str, Any]) -> ProductionCallableBindingReadinessEntry:
        adapter_id = str(source_entry["adapter_id"])
        registry = APPROVED_BINDING_SIGNATURE_REGISTRY[adapter_id]
        try:
            module = importlib.import_module(str(registry["module_path"]))
        except Exception as error:
            raise ProductionCallableBindingReadinessImportError(
                f"Approved module import failed for {adapter_id}."
            ) from error
        owner = getattr(module, str(registry["owner_name"]), None)
        if not inspect.isclass(owner):
            raise ProductionCallableBindingReadinessInvariantError(
                f"Approved owner class missing for {adapter_id}."
            )
        callable_object = inspect.getattr_static(owner, str(registry["callable_name"]), None)
        if callable_object is None or not inspect.isfunction(callable_object):
            raise ProductionCallableBindingReadinessInvariantError(
                f"Approved unbound method missing for {adapter_id}."
            )
        constructor_signature = inspect.signature(owner)
        callable_signature = inspect.signature(callable_object)
        constructor_rendered = str(constructor_signature)
        callable_rendered = str(callable_signature)
        if constructor_rendered != registry["constructor_signature"]:
            raise ProductionCallableBindingReadinessInvariantError(
                f"Constructor signature drift detected for {adapter_id}: {constructor_rendered}"
            )
        if callable_rendered != registry["callable_signature"]:
            raise ProductionCallableBindingReadinessInvariantError(
                f"Callable signature drift detected for {adapter_id}: {callable_rendered}"
            )
        constructor_required, constructor_optional = _parameter_groups(
            constructor_signature,
            skip_self=False,
        )
        callable_required, callable_optional = _parameter_groups(
            callable_signature,
            skip_self=True,
        )
        expected_groups = (
            tuple(registry["required_constructor_parameters"]),
            tuple(registry["optional_constructor_parameters"]),
            tuple(registry["required_callable_parameters"]),
            tuple(registry["optional_callable_parameters"]),
        )
        actual_groups = (
            constructor_required,
            constructor_optional,
            callable_required,
            callable_optional,
        )
        if actual_groups != expected_groups:
            raise ProductionCallableBindingReadinessInvariantError(
                f"Binding parameter classification drift detected for {adapter_id}."
            )
        entry_body = {
            "sequence": int(source_entry["sequence"]),
            "worker_id": str(source_entry["worker_id"]),
            "work_item_id": str(source_entry["work_item_id"]),
            "adapter_id": adapter_id,
            "read_operation": str(registry["read_operation"]),
            "module_path": str(registry["module_path"]),
            "owner_name": str(registry["owner_name"]),
            "callable_name": str(registry["callable_name"]),
            "callable_kind": str(registry["callable_kind"]),
            "callable_qualified_name": (
                f"{registry['module_path']}.{registry['owner_name']}.{registry['callable_name']}"
            ),
            "constructor_signature": constructor_rendered,
            "callable_signature": callable_rendered,
            "required_constructor_parameters": constructor_required,
            "optional_constructor_parameters": constructor_optional,
            "required_callable_parameters": callable_required,
            "optional_callable_parameters": callable_optional,
            "module_imported": True,
            "owner_resolved": True,
            "callable_resolved": True,
            "signature_inspection_performed": True,
            "owner_instantiated": False,
            "constructor_arguments_bound": False,
            "callable_arguments_bound": False,
            "callable_invoked": False,
            "adapter_executed": False,
            "readiness_checks": (
                "oia049_manifest_hash_verified",
                "oia049_resolution_entry_hash_verified",
                "approved_adapter_identity_verified",
                "approved_module_path_verified",
                "approved_owner_class_verified",
                "approved_unbound_method_verified",
                "constructor_signature_verified",
                "callable_signature_verified",
                "required_parameter_set_verified",
                "optional_parameter_set_verified",
                "variadic_parameters_absent",
                "owner_not_instantiated",
                "constructor_arguments_not_bound",
                "callable_arguments_not_bound",
                "callable_not_invoked",
                "adapter_not_executed",
                "oracle_qseries_boundary_verified",
            ),
            "readiness_status": STATUS_BINDING_READY,
            "source_callable_resolution_hash": str(source_entry["callable_resolution_hash"]),
            "source_active_invocation_execution_authorization_hash": str(source_entry["source_active_invocation_execution_authorization_hash"]),
            "source_active_invocation_execution_readiness_hash": str(source_entry["source_active_invocation_execution_readiness_hash"]),
            "source_active_execution_invocation_hash": str(source_entry["source_active_execution_invocation_hash"]),
            "source_execution_invocation_hash": str(source_entry["source_execution_invocation_hash"]),
            "source_authorization_entry_hash": str(source_entry["source_authorization_entry_hash"]),
            "source_readiness_entry_hash": str(source_entry["source_readiness_entry_hash"]),
            "source_active_adapter_invocation_hash": str(source_entry["source_active_adapter_invocation_hash"]),
        }
        return ProductionCallableBindingReadinessEntry(
            **entry_body,
            callable_binding_readiness_hash=stable_hash(entry_body),
        )

    def evaluate(
        self,
        *,
        evaluated_at: datetime,
        persist: bool = True,
    ) -> ProductionCallableBindingReadinessManifest:
        evaluated_at = _aware_utc(evaluated_at, "evaluated_at")
        source = self._load_resolution_manifest()
        entries = tuple(self._inspect_entry(item) for item in source["resolution_entries"])
        registry_hash = stable_hash({
            adapter_id: dict(config)
            for adapter_id, config in APPROVED_BINDING_SIGNATURE_REGISTRY.items()
        })
        readiness_id = "oia050-production-callable-binding-readiness-" + stable_hash({
            "source_callable_resolution_manifest_hash": source["callable_resolution_manifest_hash"],
            "approved_binding_signature_registry_hash": registry_hash,
            "policy_id": POLICY_ID,
        })[:32]
        manifest_body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "evaluated_at": evaluated_at.isoformat(),
            "callable_binding_readiness_id": readiness_id,
            "callable_binding_readiness_status": STATUS_BINDING_READINESS_ISSUED,
            "callable_binding_readiness_policy_id": POLICY_ID,
            "worker_id": source["worker_id"],
            "readiness_entry_count": len(entries),
            "readiness_entries": entries,
            "approved_binding_signature_registry_hash": registry_hash,
            "source_callable_resolution_id": source["callable_resolution_id"],
            "source_callable_resolution_manifest_hash": source["callable_resolution_manifest_hash"],
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
            "callable_binding_readiness_issued": True,
            "module_import_allowed": True,
            "module_import_performed": True,
            "signature_inspection_allowed": True,
            "signature_inspection_performed": True,
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
            "readiness_artifact_persistence_allowed": True,
        }
        serializable = dict(manifest_body)
        serializable["readiness_entries"] = [asdict(entry) for entry in entries]
        result = ProductionCallableBindingReadinessManifest(
            **manifest_body,
            callable_binding_readiness_manifest_hash=stable_hash(serializable),
        )
        if persist:
            payload = asdict(result)
            _atomic_write(self.binding_readiness_directory / "current.json", payload)
            _atomic_write(
                self.binding_readiness_directory / "readiness" / f"{readiness_id}.json",
                payload,
            )
            _atomic_write(
                self.binding_readiness_directory / "workers" / result.worker_id / f"{readiness_id}.json",
                payload,
            )
        return result
