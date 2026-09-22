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

SCHEMA_VERSION = "OIA-049"
ENGINE_ID = "OIA-049"
POLICY_ID = (
    "oracle.certified-research-evidence-read-execution-adapter-"
    "production-callable-resolution.v1"
)
STATUS_CALLABLE_RESOLVED = (
    "evidence_read_execution_adapter_production_callable_resolved"
)
STATUS_RESOLUTION_MANIFEST_ISSUED = (
    "evidence_read_execution_adapter_production_callable_resolution_issued"
)

DEFAULT_AUTHORIZATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "certified_research_evidence_read_execution_adapter_active_invocation_execution_authorization"
)
DEFAULT_RESOLUTION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "certified_research_evidence_read_execution_adapter_production_callable_resolution"
)

APPROVED_PRODUCTION_CALLABLE_REGISTRY = MappingProxyType({
    "oracle_read_only_canonical_observation_adapter.v1": MappingProxyType({
        "read_operation": "read_canonical_observations",
        "module_path": (
            "qseries_v2.oracle_intelligence.analytics."
            "oracle_live_corpus_inspector"
        ),
        "owner_name": "OracleLiveCorpusInspector",
        "callable_name": "inspect",
        "callable_kind": "instance_method",
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
    }),
})


class ProductionCallableResolutionError(RuntimeError):
    pass


class ProductionCallableResolutionInvariantError(
    ProductionCallableResolutionError
):
    pass


class ProductionCallableResolutionImportError(
    ProductionCallableResolutionError
):
    pass


def _aware_utc(value: datetime, field_name: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise ProductionCallableResolutionInvariantError(
            f"{field_name} must be timezone-aware."
        )
    return value.astimezone(timezone.utc)


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in value.items()
        }
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


@dataclass(frozen=True)
class ProductionCallableResolutionEntry:
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
    module_imported: bool
    owner_resolved: bool
    callable_resolved: bool
    owner_instantiated: bool
    callable_bound: bool
    callable_invoked: bool
    adapter_executed: bool
    resolution_checks: tuple[str, ...]
    resolution_status: str
    source_active_invocation_execution_authorization_hash: str
    source_active_invocation_execution_readiness_hash: str
    source_active_execution_invocation_hash: str
    source_execution_invocation_hash: str
    source_authorization_entry_hash: str
    source_readiness_entry_hash: str
    source_active_adapter_invocation_hash: str
    callable_resolution_hash: str


@dataclass(frozen=True)
class ProductionCallableResolutionManifest:
    schema_version: str
    engine_id: str
    resolved_at: str
    callable_resolution_id: str
    callable_resolution_status: str
    callable_resolution_policy_id: str
    worker_id: str
    resolution_entry_count: int
    resolution_entries: tuple[ProductionCallableResolutionEntry, ...]
    approved_registry_hash: str
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
    callable_resolution_issued: bool
    module_import_allowed: bool
    module_import_performed: bool
    owner_resolution_allowed: bool
    owner_resolution_performed: bool
    callable_resolution_allowed: bool
    callable_resolution_performed: bool
    owner_instantiation_allowed: bool
    owner_instantiation_performed: bool
    callable_binding_allowed: bool
    callable_binding_performed: bool
    adapter_invocation_allowed: bool
    adapter_invocation_performed: bool
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
    resolution_artifact_persistence_allowed: bool
    callable_resolution_manifest_hash: str


class OracleCertifiedResearchEvidenceReadExecutionAdapterProductionCallableResolutionGate:
    """Resolve approved production read-only callable identities without binding or invocation."""

    def __init__(
        self,
        *,
        authorization_directory: Path | str = DEFAULT_AUTHORIZATION_DIRECTORY,
        resolution_directory: Path | str = DEFAULT_RESOLUTION_DIRECTORY,
    ) -> None:
        self.authorization_directory = Path(authorization_directory)
        self.resolution_directory = Path(resolution_directory)

    def _load_authorization(self) -> dict[str, Any]:
        current = self.authorization_directory / "current.json"
        if not current.exists():
            raise ProductionCallableResolutionInvariantError(
                f"OIA-048 current authorization artifact missing: {current}"
            )
        try:
            source = json.loads(current.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ProductionCallableResolutionInvariantError(
                "OIA-048 authorization artifact could not be decoded."
            ) from error
        if not isinstance(source, dict):
            raise ProductionCallableResolutionInvariantError(
                "OIA-048 authorization artifact must be a JSON object."
            )
        manifest_hash = source.pop(
            "execution_authorization_manifest_hash", None
        )
        if not _valid_hash(manifest_hash) or stable_hash(source) != manifest_hash:
            raise ProductionCallableResolutionInvariantError(
                "OIA-048 authorization manifest hash verification failed."
            )
        source["execution_authorization_manifest_hash"] = manifest_hash

        expected = {
            "schema_version": "OIA-048",
            "engine_id": "OIA-048",
            "execution_authorization_status":
                "evidence_read_execution_adapter_active_invocation_execution_authorization_issued",
            "execution_authorization_policy_id":
                "oracle.certified-research-evidence-read-execution-adapter-"
                "active-invocation-execution-authorization.v1",
            "execution_authorization_issued": True,
            "callable_resolution_evaluation_allowed": True,
            "callable_resolution_allowed": False,
            "callable_resolution_performed": False,
            "callable_binding_allowed": False,
            "callable_binding_performed": False,
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
            "authorization_artifact_persistence_allowed": True,
        }
        for field_name, expected_value in expected.items():
            if source.get(field_name) != expected_value:
                raise ProductionCallableResolutionInvariantError(
                    f"OIA-048 invariant failed: {field_name}."
                )

        identifier_fields = {
            "execution_authorization_id",
            "worker_id",
            "source_execution_readiness_id",
            "source_invocation_activation_id",
            "source_execution_invocation_manifest_id",
            "source_prior_execution_authorization_id",
            "source_prior_execution_readiness_id",
        }
        for field_name in identifier_fields:
            value = source.get(field_name)
            if not isinstance(value, str) or not value:
                raise ProductionCallableResolutionInvariantError(
                    f"OIA-048 identifier is invalid: {field_name}."
                )

        hash_fields = {
            "source_execution_readiness_manifest_hash",
            "source_invocation_activation_manifest_hash",
            "source_execution_invocation_manifest_hash",
            "source_prior_execution_authorization_manifest_hash",
            "source_prior_execution_readiness_manifest_hash",
            "source_activation_hash",
        }
        for field_name in hash_fields:
            if not _valid_hash(source.get(field_name)):
                raise ProductionCallableResolutionInvariantError(
                    f"OIA-048 hash field is invalid: {field_name}."
                )

        count = source.get("authorization_entry_count")
        entries = source.get("authorization_entries")
        if (
            not isinstance(count, int)
            or isinstance(count, bool)
            or count < 1
            or not isinstance(entries, list)
            or len(entries) != count
        ):
            raise ProductionCallableResolutionInvariantError(
                "OIA-048 authorization-entry collection is invalid."
            )

        source_lineage = source.get("source_lineage")
        required_lineage_fields = {
            "source_evidence_read_execution_adapter_invocation_manifest_id",
            "source_evidence_read_execution_adapter_authorization_manifest_id",
            "source_evidence_read_execution_adapter_readiness_manifest_id",
            "source_evidence_read_execution_adapter_binding_manifest_id",
            "source_evidence_read_execution_invocation_activation_id",
            "source_evidence_read_execution_invocation_manifest_id",
            "source_evidence_read_execution_authorization_id",
            "source_evidence_read_execution_readiness_id",
            "source_evidence_read_request_activation_id",
            "source_evidence_read_request_manifest_id",
            "source_evidence_task_activation_id",
            "source_evidence_task_manifest_id",
            "source_evidence_batch_activation_id",
            "source_evidence_batch_id",
            "source_evidence_session_id",
            "source_evidence_manifest_id",
            "source_certification_id",
            "source_readiness_id",
            "source_session_id",
            "source_activation_id",
            "source_claim_id",
            "dispatch_manifest_id",
            "selected_batch_id",
            "selected_batch_number",
        }
        if not isinstance(source_lineage, dict):
            raise ProductionCallableResolutionInvariantError(
                "OIA-048 source lineage is missing."
            )
        missing = required_lineage_fields - set(source_lineage)
        if missing:
            raise ProductionCallableResolutionInvariantError(
                f"OIA-048 lineage is incomplete: {sorted(missing)}"
            )

        required_checks = {
            "execution_readiness_manifest_hash_verified",
            "execution_readiness_entry_hash_verified",
            "invocation_activation_lineage_verified",
            "execution_invocation_lineage_verified",
            "prior_authorization_lineage_verified",
            "prior_readiness_lineage_verified",
            "adapter_read_only_identity_verified",
            "operation_read_only_verified",
            "authorization_argument_allowlist_verified",
            "callable_resolution_authorized_but_not_requested",
            "callable_resolution_not_performed",
            "callable_binding_remained_disabled",
            "adapter_execution_remained_disabled",
            "corpus_execution_remained_disabled",
            "oracle_qseries_boundary_verified",
        }
        seen_work_items: set[str] = set()
        seen_hashes: set[str] = set()
        for expected_sequence, entry in enumerate(entries, start=1):
            if not isinstance(entry, dict):
                raise ProductionCallableResolutionInvariantError(
                    "OIA-048 authorization entry must be an object."
                )
            entry_hash = entry.pop(
                "active_invocation_execution_authorization_hash", None
            )
            if not _valid_hash(entry_hash) or stable_hash(entry) != entry_hash:
                raise ProductionCallableResolutionInvariantError(
                    "OIA-048 authorization-entry hash verification failed."
                )
            entry["active_invocation_execution_authorization_hash"] = entry_hash
            if entry_hash in seen_hashes:
                raise ProductionCallableResolutionInvariantError(
                    "OIA-048 contains a duplicate authorization-entry hash."
                )
            seen_hashes.add(entry_hash)
            if entry.get("sequence") != expected_sequence:
                raise ProductionCallableResolutionInvariantError(
                    "OIA-048 authorization-entry sequence is non-canonical."
                )
            if entry.get("worker_id") != source["worker_id"]:
                raise ProductionCallableResolutionInvariantError(
                    "OIA-048 authorization-entry worker mismatch."
                )
            if entry.get("authorization_status") != (
                "evidence_read_execution_adapter_active_invocation_execution_authorized"
            ):
                raise ProductionCallableResolutionInvariantError(
                    "OIA-048 invocation is not authorized."
                )
            work_item_id = entry.get("work_item_id")
            if not isinstance(work_item_id, str) or not work_item_id:
                raise ProductionCallableResolutionInvariantError(
                    "OIA-048 work-item identity is invalid."
                )
            if work_item_id in seen_work_items:
                raise ProductionCallableResolutionInvariantError(
                    "OIA-048 contains duplicate work-item identities."
                )
            seen_work_items.add(work_item_id)
            adapter_id = entry.get("adapter_id")
            operation = entry.get("read_operation")
            registry = APPROVED_PRODUCTION_CALLABLE_REGISTRY.get(adapter_id)
            if registry is None:
                raise ProductionCallableResolutionInvariantError(
                    f"Adapter is absent from the approved production registry: {adapter_id}"
                )
            if registry["read_operation"] != operation:
                raise ProductionCallableResolutionInvariantError(
                    "OIA-048 adapter and operation do not match the approved registry."
                )
            arguments = entry.get("authorization_arguments")
            if not isinstance(arguments, dict) or set(arguments) != {
                "activated",
                "read_only",
                "execute",
                "callable_resolution_requested",
                "callable_resolution_authorized",
            }:
                raise ProductionCallableResolutionInvariantError(
                    "OIA-048 authorization argument allowlist mismatch."
                )
            if arguments != {
                "activated": True,
                "read_only": True,
                "execute": False,
                "callable_resolution_requested": False,
                "callable_resolution_authorized": True,
            }:
                raise ProductionCallableResolutionInvariantError(
                    "OIA-048 authorization arguments are unsafe."
                )
            checks = entry.get("authorization_checks")
            if not isinstance(checks, list) or not required_checks.issubset(set(checks)):
                raise ProductionCallableResolutionInvariantError(
                    "OIA-048 authorization checks are incomplete."
                )
            for field_name in {
                "source_active_invocation_execution_readiness_hash",
                "source_active_execution_invocation_hash",
                "source_execution_invocation_hash",
                "source_authorization_entry_hash",
                "source_readiness_entry_hash",
                "source_active_adapter_invocation_hash",
            }:
                if not _valid_hash(entry.get(field_name)):
                    raise ProductionCallableResolutionInvariantError(
                        f"OIA-048 lineage hash is invalid: {field_name}."
                    )
        return source

    @staticmethod
    def _resolve_registry_entry(
        adapter_id: str,
        read_operation: str,
    ) -> tuple[dict[str, str], Any]:
        registry = APPROVED_PRODUCTION_CALLABLE_REGISTRY.get(adapter_id)
        if registry is None or registry["read_operation"] != read_operation:
            raise ProductionCallableResolutionInvariantError(
                "Requested callable is not in the approved production registry."
            )
        module_path = str(registry["module_path"])
        owner_name = str(registry["owner_name"])
        callable_name = str(registry["callable_name"])
        try:
            module = importlib.import_module(module_path)
        except Exception as error:
            raise ProductionCallableResolutionImportError(
                f"Unable to import approved module: {module_path}"
            ) from error
        owner = getattr(module, owner_name, None)
        if owner is None or not inspect.isclass(owner):
            raise ProductionCallableResolutionInvariantError(
                f"Approved callable owner is missing or not a class: {owner_name}"
            )
        resolved = inspect.getattr_static(owner, callable_name, None)
        if resolved is None or not callable(resolved):
            raise ProductionCallableResolutionInvariantError(
                f"Approved callable is missing or non-callable: {callable_name}"
            )
        if callable_name.startswith("_"):
            raise ProductionCallableResolutionInvariantError(
                "Private callables cannot cross the resolution boundary."
            )
        metadata = {
            "module_path": module_path,
            "owner_name": owner_name,
            "callable_name": callable_name,
            "callable_kind": str(registry["callable_kind"]),
            "callable_qualified_name": f"{module_path}:{owner_name}.{callable_name}",
        }
        return metadata, resolved

    def resolve(
        self,
        *,
        resolved_at: datetime,
        persist: bool = True,
    ) -> ProductionCallableResolutionManifest:
        resolved_at = _aware_utc(resolved_at, "resolved_at")
        source = self._load_authorization()
        entries: list[ProductionCallableResolutionEntry] = []
        for sequence, authorization_entry in enumerate(
            source["authorization_entries"], start=1
        ):
            metadata, resolved_callable = self._resolve_registry_entry(
                authorization_entry["adapter_id"],
                authorization_entry["read_operation"],
            )
            del resolved_callable
            entry_body = {
                "sequence": sequence,
                "worker_id": authorization_entry["worker_id"],
                "work_item_id": authorization_entry["work_item_id"],
                "adapter_id": authorization_entry["adapter_id"],
                "read_operation": authorization_entry["read_operation"],
                **metadata,
                "module_imported": True,
                "owner_resolved": True,
                "callable_resolved": True,
                "owner_instantiated": False,
                "callable_bound": False,
                "callable_invoked": False,
                "adapter_executed": False,
                "resolution_checks": (
                    "oia048_manifest_hash_verified",
                    "oia048_authorization_entry_hash_verified",
                    "oia038_adapter_operation_identity_preserved",
                    "approved_production_registry_match_verified",
                    "approved_module_imported",
                    "approved_owner_class_resolved",
                    "approved_public_callable_resolved_statically",
                    "owner_not_instantiated",
                    "callable_not_bound",
                    "callable_not_invoked",
                    "adapter_not_executed",
                    "corpus_read_execution_remained_disabled",
                    "oracle_qseries_boundary_verified",
                ),
                "resolution_status": STATUS_CALLABLE_RESOLVED,
                "source_active_invocation_execution_authorization_hash":
                    authorization_entry[
                        "active_invocation_execution_authorization_hash"
                    ],
                "source_active_invocation_execution_readiness_hash":
                    authorization_entry[
                        "source_active_invocation_execution_readiness_hash"
                    ],
                "source_active_execution_invocation_hash":
                    authorization_entry[
                        "source_active_execution_invocation_hash"
                    ],
                "source_execution_invocation_hash":
                    authorization_entry["source_execution_invocation_hash"],
                "source_authorization_entry_hash":
                    authorization_entry["source_authorization_entry_hash"],
                "source_readiness_entry_hash":
                    authorization_entry["source_readiness_entry_hash"],
                "source_active_adapter_invocation_hash":
                    authorization_entry[
                        "source_active_adapter_invocation_hash"
                    ],
            }
            entries.append(ProductionCallableResolutionEntry(
                **entry_body,
                callable_resolution_hash=stable_hash(entry_body),
            ))

        registry_payload = {
            adapter_id: dict(config)
            for adapter_id, config in APPROVED_PRODUCTION_CALLABLE_REGISTRY.items()
        }
        approved_registry_hash = stable_hash(registry_payload)
        resolution_id = (
            "oia049-production-callable-resolution-"
            + stable_hash({
                "source_execution_authorization_manifest_hash":
                    source["execution_authorization_manifest_hash"],
                "approved_registry_hash": approved_registry_hash,
                "policy_id": POLICY_ID,
            })[:32]
        )
        manifest_body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "resolved_at": resolved_at.isoformat(),
            "callable_resolution_id": resolution_id,
            "callable_resolution_status": STATUS_RESOLUTION_MANIFEST_ISSUED,
            "callable_resolution_policy_id": POLICY_ID,
            "worker_id": source["worker_id"],
            "resolution_entry_count": len(entries),
            "resolution_entries": tuple(entries),
            "approved_registry_hash": approved_registry_hash,
            "source_execution_authorization_id":
                source["execution_authorization_id"],
            "source_execution_authorization_manifest_hash":
                source["execution_authorization_manifest_hash"],
            "source_execution_readiness_id":
                source["source_execution_readiness_id"],
            "source_execution_readiness_manifest_hash":
                source["source_execution_readiness_manifest_hash"],
            "source_invocation_activation_id":
                source["source_invocation_activation_id"],
            "source_invocation_activation_manifest_hash":
                source["source_invocation_activation_manifest_hash"],
            "source_execution_invocation_manifest_id":
                source["source_execution_invocation_manifest_id"],
            "source_execution_invocation_manifest_hash":
                source["source_execution_invocation_manifest_hash"],
            "source_prior_execution_authorization_id":
                source["source_prior_execution_authorization_id"],
            "source_prior_execution_authorization_manifest_hash":
                source["source_prior_execution_authorization_manifest_hash"],
            "source_prior_execution_readiness_id":
                source["source_prior_execution_readiness_id"],
            "source_prior_execution_readiness_manifest_hash":
                source["source_prior_execution_readiness_manifest_hash"],
            "source_activation_hash": source["source_activation_hash"],
            "source_lineage": dict(source["source_lineage"]),
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
            "adapter_invocation_allowed": False,
            "adapter_invocation_performed": False,
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
            "resolution_artifact_persistence_allowed": True,
        }
        serializable = dict(manifest_body)
        serializable["resolution_entries"] = [asdict(entry) for entry in entries]
        result = ProductionCallableResolutionManifest(
            **manifest_body,
            callable_resolution_manifest_hash=stable_hash(serializable),
        )
        if persist:
            payload = asdict(result)
            _atomic_write(self.resolution_directory / "current.json", payload)
            _atomic_write(
                self.resolution_directory / "resolutions" / f"{resolution_id}.json",
                payload,
            )
            _atomic_write(
                self.resolution_directory / "workers" / result.worker_id
                / f"{resolution_id}.json",
                payload,
            )
        return result
