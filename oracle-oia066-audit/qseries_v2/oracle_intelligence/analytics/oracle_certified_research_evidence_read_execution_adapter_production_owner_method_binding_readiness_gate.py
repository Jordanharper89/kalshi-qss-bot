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

SCHEMA_VERSION = "OIA-056"
ENGINE_ID = "OIA-056"
POLICY_ID = "oracle.certified-research-evidence-read-execution-adapter-production-owner-method-binding-readiness.v1"
STATUS_METHOD_BINDING_READY = "evidence_read_execution_adapter_production_owner_method_binding_ready"
STATUS_READINESS_ISSUED = "evidence_read_execution_adapter_production_owner_method_binding_readiness_issued"

DEFAULT_CONSTRUCTION_DIRECTORY = Path(
    "runtime/oracle_intelligence/certified_research_evidence_read_execution_adapter_production_owner_construction"
)
DEFAULT_READINESS_DIRECTORY = Path(
    "runtime/oracle_intelligence/certified_research_evidence_read_execution_adapter_production_owner_method_binding_readiness"
)

APPROVED = {
    "oracle_read_only_canonical_observation_adapter.v1": (
        "qseries_v2.oracle_intelligence.analytics.oracle_live_corpus_inspector",
        "OracleLiveCorpusInspector",
        "inspect",
    ),
    "oracle_read_only_market_state_lineage_adapter.v1": (
        "qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_market_lineage_ledger",
        "OracleCanonicalMarketLineageLedger",
        "records",
    ),
}


class ProductionOwnerMethodBindingReadinessInvariantError(RuntimeError):
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
            raise ProductionOwnerMethodBindingReadinessInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
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


def _aware(value: datetime, field_name: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise ProductionOwnerMethodBindingReadinessInvariantError(
            f"{field_name} must be timezone-aware"
        )
    return value.astimezone(timezone.utc)


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        delete=False,
        dir=str(path.parent),
    )
    temporary = Path(handle.name)
    try:
        with handle:
            json.dump(
                _canonical(payload),
                handle,
                sort_keys=True,
                indent=2,
                ensure_ascii=False,
            )
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


@dataclass(frozen=True)
class ProductionOwnerMethodBindingReadinessEntry:
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
    owner_state_fingerprint: str
    owner_construction_hash: str
    method_descriptor_type: str
    method_descriptor_module: str
    method_descriptor_qualname: str
    method_signature_verified: bool
    instance_parameter_verified: bool
    descriptor_static_resolution_verified: bool
    owner_reconstruction_required: bool
    owner_reconstructed: bool
    method_bound_to_owner: bool
    method_invoked: bool
    adapter_executed: bool
    readiness_checks: tuple[str, ...]
    readiness_status: str
    source_owner_construction_authorization_hash: str
    source_owner_construction_readiness_hash: str
    source_callable_argument_binding_hash: str
    owner_method_binding_readiness_hash: str


@dataclass(frozen=True)
class ProductionOwnerMethodBindingReadinessManifest:
    schema_version: str
    engine_id: str
    evaluated_at: str
    owner_method_binding_readiness_id: str
    owner_method_binding_readiness_status: str
    owner_method_binding_readiness_policy_id: str
    worker_id: str
    readiness_entry_count: int
    readiness_entries: tuple[ProductionOwnerMethodBindingReadinessEntry, ...]
    source_owner_construction_id: str
    source_owner_construction_manifest_hash: str
    source_owner_construction_authorization_id: str
    source_owner_construction_authorization_manifest_hash: str
    source_lineage: dict[str, Any]
    owner_method_binding_readiness_issued: bool
    owner_method_binding_authorization_evaluation_allowed: bool
    owner_reconstruction_allowed: bool
    owner_reconstruction_performed: bool
    callable_binding_to_owner_allowed: bool
    callable_binding_to_owner_performed: bool
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
    owner_method_binding_readiness_manifest_hash: str


class OracleCertifiedResearchEvidenceReadExecutionAdapterProductionOwnerMethodBindingReadinessGate:
    # OIA-056 validates the repository-approved owner method descriptor.
    # It performs static descriptor inspection only and never invokes it.

    def __init__(
        self,
        *,
        construction_directory: Path | str = DEFAULT_CONSTRUCTION_DIRECTORY,
        readiness_directory: Path | str = DEFAULT_READINESS_DIRECTORY,
    ) -> None:
        self.construction_directory = Path(construction_directory)
        self.readiness_directory = Path(readiness_directory)

    def _load_construction(self) -> dict[str, Any]:
        path = self.construction_directory / "current.json"
        if not path.exists():
            raise ProductionOwnerMethodBindingReadinessInvariantError(
                f"OIA-055 current construction artifact missing: {path}"
            )
        try:
            source = json.loads(path.read_text(encoding="utf-8"))
        except Exception as error:
            raise ProductionOwnerMethodBindingReadinessInvariantError(
                "OIA-055 construction artifact could not be decoded"
            ) from error

        manifest_hash = source.pop("owner_construction_manifest_hash", None)
        if not _valid_hash(manifest_hash) or stable_hash(source) != manifest_hash:
            raise ProductionOwnerMethodBindingReadinessInvariantError(
                "OIA-055 construction manifest hash verification failed"
            )
        source["owner_construction_manifest_hash"] = manifest_hash

        expected = {
            "schema_version": "OIA-055",
            "engine_id": "OIA-055",
            "owner_construction_performed": True,
            "owner_instances_retained": False,
            "callable_binding_to_owner_allowed": False,
            "callable_binding_to_owner_performed": False,
            "callable_invocation_allowed": False,
            "callable_invocation_performed": False,
            "adapter_execution_allowed": False,
            "adapter_execution_performed": False,
            "corpus_read_execution_allowed": False,
            "corpus_read_execution_performed": False,
            "qseries_handoff_allowed": False,
            "execution_allowed": False,
            "market_order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
        }
        for field_name, expected_value in expected.items():
            if source.get(field_name) != expected_value:
                raise ProductionOwnerMethodBindingReadinessInvariantError(
                    f"OIA-055 invariant failed: {field_name}"
                )

        for field_name in (
            "owner_construction_id",
            "source_owner_construction_authorization_id",
            "worker_id",
        ):
            if not isinstance(source.get(field_name), str) or not source[field_name]:
                raise ProductionOwnerMethodBindingReadinessInvariantError(
                    f"OIA-055 identifier invalid: {field_name}"
                )

        if not _valid_hash(source.get("source_owner_construction_authorization_manifest_hash")):
            raise ProductionOwnerMethodBindingReadinessInvariantError(
                "OIA-055 authorization lineage hash invalid"
            )

        entries = source.get("construction_entries")
        if (
            not isinstance(entries, list)
            or not entries
            or len(entries) != source.get("construction_entry_count")
        ):
            raise ProductionOwnerMethodBindingReadinessInvariantError(
                "OIA-055 construction entries invalid"
            )

        seen_work_items: set[str] = set()
        seen_hashes: set[str] = set()
        for expected_sequence, entry in enumerate(entries, start=1):
            if not isinstance(entry, dict) or entry.get("sequence") != expected_sequence:
                raise ProductionOwnerMethodBindingReadinessInvariantError(
                    "OIA-055 construction entry sequence invalid"
                )
            entry_hash = entry.pop("owner_construction_hash", None)
            if not _valid_hash(entry_hash) or stable_hash(entry) != entry_hash:
                raise ProductionOwnerMethodBindingReadinessInvariantError(
                    "OIA-055 construction entry hash verification failed"
                )
            entry["owner_construction_hash"] = entry_hash
            if entry_hash in seen_hashes:
                raise ProductionOwnerMethodBindingReadinessInvariantError(
                    "duplicate OIA-055 construction hash"
                )
            seen_hashes.add(entry_hash)

            work_item_id = entry.get("work_item_id")
            if not isinstance(work_item_id, str) or not work_item_id:
                raise ProductionOwnerMethodBindingReadinessInvariantError(
                    "OIA-055 work item invalid"
                )
            if work_item_id in seen_work_items:
                raise ProductionOwnerMethodBindingReadinessInvariantError(
                    "duplicate OIA-055 work item"
                )
            seen_work_items.add(work_item_id)

            adapter_id = entry.get("adapter_id")
            identity = APPROVED.get(adapter_id)
            if identity is None or identity != (
                entry.get("module_path"),
                entry.get("owner_name"),
                entry.get("callable_name"),
            ):
                raise ProductionOwnerMethodBindingReadinessInvariantError(
                    "unapproved OIA-055 owner method identity"
                )

            safety = {
                "owner_constructed": True,
                "owner_type_verified": True,
                "owner_read_only_verified": True,
                "owner_execution_disabled_verified": True,
                "callable_bound_to_owner": False,
                "callable_invoked": False,
                "adapter_executed": False,
            }
            for field_name, expected_value in safety.items():
                if entry.get(field_name) != expected_value:
                    raise ProductionOwnerMethodBindingReadinessInvariantError(
                        f"unsafe OIA-055 entry: {field_name}"
                    )

            for hash_field in (
                "source_owner_construction_authorization_hash",
                "source_owner_construction_readiness_hash",
                "source_callable_argument_binding_hash",
                "owner_state_fingerprint",
            ):
                if not _valid_hash(entry.get(hash_field)):
                    raise ProductionOwnerMethodBindingReadinessInvariantError(
                        f"OIA-055 entry hash invalid: {hash_field}"
                    )

        if not isinstance(source.get("source_lineage"), dict) or not source["source_lineage"]:
            raise ProductionOwnerMethodBindingReadinessInvariantError(
                "OIA-055 source lineage missing"
            )
        return source

    def evaluate(
        self,
        *,
        evaluated_at: datetime,
        persist: bool = True,
    ) -> ProductionOwnerMethodBindingReadinessManifest:
        evaluated_at = _aware(evaluated_at, "evaluated_at")
        source = self._load_construction()
        readiness_entries: list[ProductionOwnerMethodBindingReadinessEntry] = []

        for sequence, construction_entry in enumerate(
            source["construction_entries"], start=1
        ):
            module = importlib.import_module(construction_entry["module_path"])
            owner_type = getattr(module, construction_entry["owner_name"], None)
            if not isinstance(owner_type, type):
                raise ProductionOwnerMethodBindingReadinessInvariantError(
                    "approved owner class could not be resolved"
                )

            descriptor = inspect.getattr_static(
                owner_type,
                construction_entry["callable_name"],
                None,
            )
            if descriptor is None or not inspect.isfunction(descriptor):
                raise ProductionOwnerMethodBindingReadinessInvariantError(
                    "approved owner method descriptor is not a plain function"
                )

            descriptor_module = getattr(descriptor, "__module__", "")
            descriptor_qualname = getattr(descriptor, "__qualname__", "")
            if descriptor_module != construction_entry["module_path"]:
                raise ProductionOwnerMethodBindingReadinessInvariantError(
                    "method descriptor module mismatch"
                )
            expected_qualname = (
                f'{construction_entry["owner_name"]}.'
                f'{construction_entry["callable_name"]}'
            )
            if descriptor_qualname != expected_qualname:
                raise ProductionOwnerMethodBindingReadinessInvariantError(
                    "method descriptor qualified-name mismatch"
                )

            signature = inspect.signature(descriptor)
            if str(signature) != construction_entry["callable_signature"]:
                raise ProductionOwnerMethodBindingReadinessInvariantError(
                    "method signature drift detected"
                )
            parameters = tuple(signature.parameters.values())
            if (
                not parameters
                or parameters[0].name != "self"
                or parameters[0].kind
                not in (
                    inspect.Parameter.POSITIONAL_ONLY,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                )
            ):
                raise ProductionOwnerMethodBindingReadinessInvariantError(
                    "approved owner method lacks canonical self parameter"
                )
            if any(
                parameter.kind
                in (
                    inspect.Parameter.VAR_POSITIONAL,
                    inspect.Parameter.VAR_KEYWORD,
                )
                for parameter in parameters
            ):
                raise ProductionOwnerMethodBindingReadinessInvariantError(
                    "variadic owner method is prohibited"
                )

            body = {
                "sequence": sequence,
                "worker_id": construction_entry["worker_id"],
                "work_item_id": construction_entry["work_item_id"],
                "adapter_id": construction_entry["adapter_id"],
                "read_operation": construction_entry["read_operation"],
                "module_path": construction_entry["module_path"],
                "owner_name": construction_entry["owner_name"],
                "callable_name": construction_entry["callable_name"],
                "constructor_signature": construction_entry["constructor_signature"],
                "callable_signature": construction_entry["callable_signature"],
                "owner_state_fingerprint": construction_entry["owner_state_fingerprint"],
                "owner_construction_hash": construction_entry["owner_construction_hash"],
                "method_descriptor_type": type(descriptor).__name__,
                "method_descriptor_module": descriptor_module,
                "method_descriptor_qualname": descriptor_qualname,
                "method_signature_verified": True,
                "instance_parameter_verified": True,
                "descriptor_static_resolution_verified": True,
                "owner_reconstruction_required": True,
                "owner_reconstructed": False,
                "method_bound_to_owner": False,
                "method_invoked": False,
                "adapter_executed": False,
                "readiness_checks": (
                    "owner_construction_manifest_hash_verified",
                    "owner_construction_entry_hash_verified",
                    "approved_owner_identity_verified",
                    "approved_method_descriptor_statically_resolved",
                    "method_descriptor_module_verified",
                    "method_descriptor_qualname_verified",
                    "method_signature_verified",
                    "canonical_self_parameter_verified",
                    "variadic_parameters_rejected",
                    "owner_not_reconstructed",
                    "method_not_bound_to_owner",
                    "method_not_invoked",
                    "adapter_not_executed",
                    "corpus_execution_remained_disabled",
                    "oracle_qseries_boundary_verified",
                ),
                "readiness_status": STATUS_METHOD_BINDING_READY,
                "source_owner_construction_authorization_hash": construction_entry[
                    "source_owner_construction_authorization_hash"
                ],
                "source_owner_construction_readiness_hash": construction_entry[
                    "source_owner_construction_readiness_hash"
                ],
                "source_callable_argument_binding_hash": construction_entry[
                    "source_callable_argument_binding_hash"
                ],
            }
            readiness_entries.append(
                ProductionOwnerMethodBindingReadinessEntry(
                    **body,
                    owner_method_binding_readiness_hash=stable_hash(body),
                )
            )

        source_manifest_hash = source["owner_construction_manifest_hash"]
        readiness_id = "oia056-owner-method-binding-readiness-" + stable_hash(
            {
                "source_owner_construction_manifest_hash": source_manifest_hash,
                "policy_id": POLICY_ID,
            }
        )[:32]

        manifest_body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "evaluated_at": evaluated_at.isoformat(),
            "owner_method_binding_readiness_id": readiness_id,
            "owner_method_binding_readiness_status": STATUS_READINESS_ISSUED,
            "owner_method_binding_readiness_policy_id": POLICY_ID,
            "worker_id": source["worker_id"],
            "readiness_entry_count": len(readiness_entries),
            "readiness_entries": tuple(readiness_entries),
            "source_owner_construction_id": source["owner_construction_id"],
            "source_owner_construction_manifest_hash": source_manifest_hash,
            "source_owner_construction_authorization_id": source[
                "source_owner_construction_authorization_id"
            ],
            "source_owner_construction_authorization_manifest_hash": source[
                "source_owner_construction_authorization_manifest_hash"
            ],
            "source_lineage": dict(source["source_lineage"]),
            "owner_method_binding_readiness_issued": True,
            "owner_method_binding_authorization_evaluation_allowed": True,
            "owner_reconstruction_allowed": False,
            "owner_reconstruction_performed": False,
            "callable_binding_to_owner_allowed": False,
            "callable_binding_to_owner_performed": False,
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
        serializable["readiness_entries"] = [
            asdict(entry) for entry in readiness_entries
        ]
        result = ProductionOwnerMethodBindingReadinessManifest(
            **manifest_body,
            owner_method_binding_readiness_manifest_hash=stable_hash(serializable),
        )

        if persist:
            payload = asdict(result)
            _atomic_write(self.readiness_directory / "current.json", payload)
            _atomic_write(
                self.readiness_directory / "readiness" / f"{readiness_id}.json",
                payload,
            )
            _atomic_write(
                self.readiness_directory
                / "workers"
                / result.worker_id
                / f"{readiness_id}.json",
                payload,
            )
        return result
