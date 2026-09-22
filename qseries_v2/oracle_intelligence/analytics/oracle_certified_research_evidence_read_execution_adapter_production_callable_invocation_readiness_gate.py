
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "OIA-059"
ENGINE_ID = "OIA-059"
POLICY_ID = (
    "oracle.certified-research-evidence-read-execution-adapter-"
    "production-callable-invocation-readiness.v1"
)
STATUS_INVOCATION_READY = (
    "evidence_read_execution_adapter_production_callable_invocation_ready"
)
STATUS_READINESS_ISSUED = (
    "evidence_read_execution_adapter_production_callable_invocation_readiness_issued"
)

DEFAULT_BINDING_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "certified_research_evidence_read_execution_adapter_production_owner_method_binding"
)
DEFAULT_READINESS_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "certified_research_evidence_read_execution_adapter_production_callable_invocation_readiness"
)

APPROVED_INVOCATION_ENVELOPES = {
    "oracle_read_only_canonical_observation_adapter.v1": {
        "read_operation": "read_canonical_observations",
        "module_path": (
            "qseries_v2.oracle_intelligence.analytics.oracle_live_corpus_inspector"
        ),
        "owner_name": "OracleLiveCorpusInspector",
        "callable_name": "inspect",
        "bound_method_qualname": "OracleLiveCorpusInspector.inspect",
        "bound_method_signature": (
            "(*, inspected_at: 'Optional[datetime]' = None) "
            "-> 'OracleLiveCorpusReport'"
        ),
        "invocation_arguments": {"inspected_at": None},
    },
    "oracle_read_only_market_state_lineage_adapter.v1": {
        "read_operation": "read_market_state_lineage",
        "module_path": (
            "qseries_v2.oracle_intelligence.live_acquisition."
            "oracle_canonical_market_lineage_ledger"
        ),
        "owner_name": "OracleCanonicalMarketLineageLedger",
        "callable_name": "records",
        "bound_method_qualname": "OracleCanonicalMarketLineageLedger.records",
        "bound_method_signature": (
            "() -> 'tuple[CanonicalMarketStateDwellChangeLineage, ...]'"
        ),
        "invocation_arguments": {},
    },
}


class ProductionCallableInvocationReadinessInvariantError(RuntimeError):
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
            raise ProductionCallableInvocationReadinessInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    return value


def stable_hash(value: Any) -> str:
    encoded = json.dumps(
        _canonical(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _valid_hash(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _aware(value: datetime, name: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise ProductionCallableInvocationReadinessInvariantError(
            f"{name} must be timezone-aware"
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
class ProductionCallableInvocationReadinessEntry:
    sequence: int
    worker_id: str
    work_item_id: str
    adapter_id: str
    read_operation: str
    module_path: str
    owner_name: str
    callable_name: str
    bound_method_module: str
    bound_method_qualname: str
    bound_method_signature: str
    invocation_arguments: dict[str, Any]
    invocation_argument_hash: str
    source_owner_method_binding_hash: str
    source_owner_method_binding_authorization_hash: str
    source_owner_method_binding_readiness_hash: str
    source_owner_construction_authorization_hash: str
    source_owner_construction_readiness_hash: str
    source_callable_argument_binding_hash: str
    owner_reconstruction_required: bool
    owner_reconstructed: bool
    method_binding_required: bool
    method_bound_to_owner: bool
    invocation_envelope_verified: bool
    callable_invocation_ready: bool
    callable_invoked: bool
    adapter_executed: bool
    corpus_read_executed: bool
    readiness_checks: tuple[str, ...]
    readiness_status: str
    callable_invocation_readiness_hash: str


@dataclass(frozen=True)
class ProductionCallableInvocationReadinessManifest:
    schema_version: str
    engine_id: str
    evaluated_at: str
    callable_invocation_readiness_id: str
    callable_invocation_readiness_status: str
    callable_invocation_readiness_policy_id: str
    worker_id: str
    readiness_entry_count: int
    readiness_entries: tuple[ProductionCallableInvocationReadinessEntry, ...]
    source_owner_method_binding_id: str
    source_owner_method_binding_manifest_hash: str
    source_owner_method_binding_authorization_id: str
    source_owner_method_binding_authorization_manifest_hash: str
    source_owner_method_binding_readiness_id: str
    source_owner_method_binding_readiness_manifest_hash: str
    source_owner_construction_id: str
    source_owner_construction_manifest_hash: str
    source_lineage: dict[str, Any]
    callable_invocation_readiness_issued: bool
    owner_reconstruction_allowed: bool
    owner_reconstruction_performed: bool
    callable_binding_to_owner_allowed: bool
    callable_binding_to_owner_performed: bool
    callable_invocation_authorization_evaluation_allowed: bool
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
    owner_instances_retained: bool
    bound_methods_retained: bool
    callable_invocation_readiness_manifest_hash: str


class OracleCertifiedResearchEvidenceReadExecutionAdapterProductionCallableInvocationReadinessGate:
    def __init__(
        self,
        *,
        binding_directory: Path | str = DEFAULT_BINDING_DIRECTORY,
        readiness_directory: Path | str = DEFAULT_READINESS_DIRECTORY,
    ) -> None:
        self.binding_directory = Path(binding_directory)
        self.readiness_directory = Path(readiness_directory)

    def _load_binding(self) -> dict[str, Any]:
        path = self.binding_directory / "current.json"
        if not path.exists():
            raise ProductionCallableInvocationReadinessInvariantError(
                f"OIA-058 current binding artifact missing: {path}"
            )
        try:
            source = json.loads(path.read_text(encoding="utf-8"))
        except Exception as error:
            raise ProductionCallableInvocationReadinessInvariantError(
                "OIA-058 binding artifact could not be decoded"
            ) from error

        manifest_hash = source.pop("owner_method_binding_manifest_hash", None)
        if not _valid_hash(manifest_hash) or stable_hash(source) != manifest_hash:
            raise ProductionCallableInvocationReadinessInvariantError(
                "OIA-058 binding manifest hash verification failed"
            )
        source["owner_method_binding_manifest_hash"] = manifest_hash

        required_flags = {
            "owner_reconstruction_allowed": True,
            "owner_reconstruction_performed": True,
            "callable_binding_to_owner_allowed": True,
            "callable_binding_to_owner_performed": True,
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
            "owner_instances_retained": False,
            "bound_methods_retained": False,
        }
        for field, expected in required_flags.items():
            if source.get(field) != expected:
                raise ProductionCallableInvocationReadinessInvariantError(
                    f"unsafe OIA-058 binding manifest: {field}"
                )

        entries = source.get("binding_entries")
        if (
            not isinstance(entries, list)
            or not entries
            or source.get("binding_entry_count") != len(entries)
        ):
            raise ProductionCallableInvocationReadinessInvariantError(
                "OIA-058 binding entry count invalid"
            )

        seen: set[tuple[str, str, str]] = set()
        for entry in entries:
            entry_hash = entry.pop("owner_method_binding_hash", None)
            if not _valid_hash(entry_hash) or stable_hash(entry) != entry_hash:
                raise ProductionCallableInvocationReadinessInvariantError(
                    "OIA-058 binding entry hash verification failed"
                )
            entry["owner_method_binding_hash"] = entry_hash

            adapter_id = entry.get("adapter_id")
            approved = APPROVED_INVOCATION_ENVELOPES.get(adapter_id)
            if approved is None:
                raise ProductionCallableInvocationReadinessInvariantError(
                    "unapproved OIA-058 adapter identity"
                )

            exact_fields = (
                "read_operation",
                "module_path",
                "owner_name",
                "callable_name",
                "bound_method_qualname",
                "bound_method_signature",
            )
            for field in exact_fields:
                if entry.get(field) != approved[field]:
                    raise ProductionCallableInvocationReadinessInvariantError(
                        f"OIA-058 production callable drift: {field}"
                    )

            if entry.get("bound_method_module") != approved["module_path"]:
                raise ProductionCallableInvocationReadinessInvariantError(
                    "OIA-058 bound method module drift"
                )

            key = (
                str(entry.get("worker_id")),
                str(entry.get("work_item_id")),
                str(adapter_id),
            )
            if key in seen:
                raise ProductionCallableInvocationReadinessInvariantError(
                    "duplicate OIA-058 binding entry"
                )
            seen.add(key)

            safe_entry = {
                "owner_reconstructed": True,
                "method_binding_requested": True,
                "method_bound_to_owner": True,
                "bound_method_self_verified": True,
                "bound_method_function_verified": True,
                "method_invoked": False,
                "adapter_executed": False,
                "corpus_read_executed": False,
            }
            for field, expected in safe_entry.items():
                if entry.get(field) != expected:
                    raise ProductionCallableInvocationReadinessInvariantError(
                        f"unsafe OIA-058 binding entry: {field}"
                    )

            for hash_field in (
                "owner_state_fingerprint",
                "owner_construction_hash",
                "source_owner_method_binding_authorization_hash",
                "source_owner_method_binding_readiness_hash",
                "source_owner_construction_authorization_hash",
                "source_owner_construction_readiness_hash",
                "source_callable_argument_binding_hash",
            ):
                if not _valid_hash(entry.get(hash_field)):
                    raise ProductionCallableInvocationReadinessInvariantError(
                        f"OIA-058 entry hash invalid: {hash_field}"
                    )

        if not isinstance(source.get("source_lineage"), dict) or not source["source_lineage"]:
            raise ProductionCallableInvocationReadinessInvariantError(
                "OIA-058 source lineage missing"
            )
        return source

    def evaluate(
        self,
        *,
        evaluated_at: datetime,
        persist: bool = True,
    ) -> ProductionCallableInvocationReadinessManifest:
        evaluated_at = _aware(evaluated_at, "evaluated_at")
        source = self._load_binding()
        results: list[ProductionCallableInvocationReadinessEntry] = []

        for sequence, entry in enumerate(source["binding_entries"], start=1):
            approved = APPROVED_INVOCATION_ENVELOPES[entry["adapter_id"]]
            invocation_arguments = dict(approved["invocation_arguments"])
            invocation_argument_hash = stable_hash(invocation_arguments)

            body = {
                "sequence": sequence,
                "worker_id": entry["worker_id"],
                "work_item_id": entry["work_item_id"],
                "adapter_id": entry["adapter_id"],
                "read_operation": entry["read_operation"],
                "module_path": entry["module_path"],
                "owner_name": entry["owner_name"],
                "callable_name": entry["callable_name"],
                "bound_method_module": entry["bound_method_module"],
                "bound_method_qualname": entry["bound_method_qualname"],
                "bound_method_signature": entry["bound_method_signature"],
                "invocation_arguments": invocation_arguments,
                "invocation_argument_hash": invocation_argument_hash,
                "source_owner_method_binding_hash": entry[
                    "owner_method_binding_hash"
                ],
                "source_owner_method_binding_authorization_hash": entry[
                    "source_owner_method_binding_authorization_hash"
                ],
                "source_owner_method_binding_readiness_hash": entry[
                    "source_owner_method_binding_readiness_hash"
                ],
                "source_owner_construction_authorization_hash": entry[
                    "source_owner_construction_authorization_hash"
                ],
                "source_owner_construction_readiness_hash": entry[
                    "source_owner_construction_readiness_hash"
                ],
                "source_callable_argument_binding_hash": entry[
                    "source_callable_argument_binding_hash"
                ],
                "owner_reconstruction_required": True,
                "owner_reconstructed": False,
                "method_binding_required": True,
                "method_bound_to_owner": False,
                "invocation_envelope_verified": True,
                "callable_invocation_ready": True,
                "callable_invoked": False,
                "adapter_executed": False,
                "corpus_read_executed": False,
                "readiness_checks": (
                    "oia058_binding_manifest_hash_verified",
                    "oia058_binding_entry_hash_verified",
                    "approved_adapter_identity_verified",
                    "approved_bound_method_identity_verified",
                    "approved_bound_method_signature_verified",
                    "approved_invocation_argument_envelope_verified",
                    "prior_live_owner_and_method_references_released",
                    "owner_not_reconstructed",
                    "method_not_bound",
                    "callable_not_invoked",
                    "adapter_not_executed",
                    "corpus_not_read",
                    "oracle_qseries_boundary_verified",
                ),
                "readiness_status": STATUS_INVOCATION_READY,
            }
            results.append(
                ProductionCallableInvocationReadinessEntry(
                    **body,
                    callable_invocation_readiness_hash=stable_hash(body),
                )
            )

        source_hash = source["owner_method_binding_manifest_hash"]
        readiness_id = (
            "oia059-callable-invocation-readiness-"
            + stable_hash({"source": source_hash, "policy": POLICY_ID})[:32]
        )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "evaluated_at": evaluated_at.isoformat(),
            "callable_invocation_readiness_id": readiness_id,
            "callable_invocation_readiness_status": STATUS_READINESS_ISSUED,
            "callable_invocation_readiness_policy_id": POLICY_ID,
            "worker_id": source["worker_id"],
            "readiness_entry_count": len(results),
            "readiness_entries": tuple(results),
            "source_owner_method_binding_id": source["owner_method_binding_id"],
            "source_owner_method_binding_manifest_hash": source_hash,
            "source_owner_method_binding_authorization_id": source[
                "source_owner_method_binding_authorization_id"
            ],
            "source_owner_method_binding_authorization_manifest_hash": source[
                "source_owner_method_binding_authorization_manifest_hash"
            ],
            "source_owner_method_binding_readiness_id": source[
                "source_owner_method_binding_readiness_id"
            ],
            "source_owner_method_binding_readiness_manifest_hash": source[
                "source_owner_method_binding_readiness_manifest_hash"
            ],
            "source_owner_construction_id": source["source_owner_construction_id"],
            "source_owner_construction_manifest_hash": source[
                "source_owner_construction_manifest_hash"
            ],
            "source_lineage": dict(source["source_lineage"]),
            "callable_invocation_readiness_issued": True,
            "owner_reconstruction_allowed": False,
            "owner_reconstruction_performed": False,
            "callable_binding_to_owner_allowed": False,
            "callable_binding_to_owner_performed": False,
            "callable_invocation_authorization_evaluation_allowed": True,
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
            "owner_instances_retained": False,
            "bound_methods_retained": False,
        }

        serial = dict(body)
        serial["readiness_entries"] = [asdict(entry) for entry in results]
        result = ProductionCallableInvocationReadinessManifest(
            **body,
            callable_invocation_readiness_manifest_hash=stable_hash(serial),
        )

        if persist:
            payload = asdict(result)
            _atomic_write(self.readiness_directory / "current.json", payload)
            _atomic_write(
                self.readiness_directory
                / "readiness"
                / f"{readiness_id}.json",
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
