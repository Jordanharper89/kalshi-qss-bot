
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "OIA-060"
ENGINE_ID = "OIA-060"
POLICY_ID = (
    "oracle.certified-research-evidence-read-execution-adapter-"
    "production-callable-invocation-authorization.v1"
)
STATUS_INVOCATION_AUTHORIZED = (
    "evidence_read_execution_adapter_production_callable_invocation_authorized"
)
STATUS_AUTHORIZATION_ISSUED = (
    "evidence_read_execution_adapter_production_callable_invocation_authorization_issued"
)

DEFAULT_READINESS_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "certified_research_evidence_read_execution_adapter_production_callable_invocation_readiness"
)
DEFAULT_AUTHORIZATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "certified_research_evidence_read_execution_adapter_production_callable_invocation_authorization"
)

APPROVED_INVOCATIONS = {
    "oracle_read_only_canonical_observation_adapter.v1": {
        "read_operation": "read_canonical_observations",
        "module_path": (
            "qseries_v2.oracle_intelligence.analytics.oracle_live_corpus_inspector"
        ),
        "owner_name": "OracleLiveCorpusInspector",
        "callable_name": "inspect",
        "bound_method_module": (
            "qseries_v2.oracle_intelligence.analytics.oracle_live_corpus_inspector"
        ),
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
        "bound_method_module": (
            "qseries_v2.oracle_intelligence.live_acquisition."
            "oracle_canonical_market_lineage_ledger"
        ),
        "bound_method_qualname": "OracleCanonicalMarketLineageLedger.records",
        "bound_method_signature": (
            "() -> 'tuple[CanonicalMarketStateDwellChangeLineage, ...]'"
        ),
        "invocation_arguments": {},
    },
}


class ProductionCallableInvocationAuthorizationInvariantError(RuntimeError):
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
            raise ProductionCallableInvocationAuthorizationInvariantError(
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
        raise ProductionCallableInvocationAuthorizationInvariantError(
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
class ProductionCallableInvocationAuthorizationEntry:
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
    source_callable_invocation_readiness_hash: str
    source_owner_method_binding_hash: str
    source_owner_method_binding_authorization_hash: str
    source_owner_method_binding_readiness_hash: str
    source_owner_construction_authorization_hash: str
    source_owner_construction_readiness_hash: str
    source_callable_argument_binding_hash: str
    callable_invocation_authorization_granted: bool
    owner_reconstruction_authorized: bool
    owner_reconstruction_performed: bool
    method_binding_authorized: bool
    method_binding_performed: bool
    callable_invocation_authorized: bool
    callable_invoked: bool
    adapter_executed: bool
    corpus_read_executed: bool
    authorization_checks: tuple[str, ...]
    authorization_status: str
    callable_invocation_authorization_hash: str


@dataclass(frozen=True)
class ProductionCallableInvocationAuthorizationManifest:
    schema_version: str
    engine_id: str
    authorized_at: str
    callable_invocation_authorization_id: str
    callable_invocation_authorization_status: str
    callable_invocation_authorization_policy_id: str
    worker_id: str
    authorization_entry_count: int
    authorization_entries: tuple[ProductionCallableInvocationAuthorizationEntry, ...]
    source_callable_invocation_readiness_id: str
    source_callable_invocation_readiness_manifest_hash: str
    source_owner_method_binding_id: str
    source_owner_method_binding_manifest_hash: str
    source_owner_method_binding_authorization_id: str
    source_owner_method_binding_authorization_manifest_hash: str
    source_owner_method_binding_readiness_id: str
    source_owner_method_binding_readiness_manifest_hash: str
    source_owner_construction_id: str
    source_owner_construction_manifest_hash: str
    source_lineage: dict[str, Any]
    callable_invocation_authorization_issued: bool
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
    authorization_artifact_persistence_allowed: bool
    owner_instances_retained: bool
    bound_methods_retained: bool
    callable_invocation_authorization_manifest_hash: str


class OracleCertifiedResearchEvidenceReadExecutionAdapterProductionCallableInvocationAuthorizationGate:
    def __init__(
        self,
        *,
        readiness_directory: Path | str = DEFAULT_READINESS_DIRECTORY,
        authorization_directory: Path | str = DEFAULT_AUTHORIZATION_DIRECTORY,
    ) -> None:
        self.readiness_directory = Path(readiness_directory)
        self.authorization_directory = Path(authorization_directory)

    def _load_readiness(self) -> dict[str, Any]:
        path = self.readiness_directory / "current.json"
        if not path.exists():
            raise ProductionCallableInvocationAuthorizationInvariantError(
                f"OIA-059 current readiness artifact missing: {path}"
            )

        try:
            source = json.loads(path.read_text(encoding="utf-8"))
        except Exception as error:
            raise ProductionCallableInvocationAuthorizationInvariantError(
                "OIA-059 readiness artifact could not be decoded"
            ) from error

        manifest_hash = source.pop(
            "callable_invocation_readiness_manifest_hash",
            None,
        )
        if not _valid_hash(manifest_hash) or stable_hash(source) != manifest_hash:
            raise ProductionCallableInvocationAuthorizationInvariantError(
                "OIA-059 readiness manifest hash verification failed"
            )
        source["callable_invocation_readiness_manifest_hash"] = manifest_hash

        required_flags = {
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
                raise ProductionCallableInvocationAuthorizationInvariantError(
                    f"unsafe OIA-059 readiness manifest: {field}"
                )

        entries = source.get("readiness_entries")
        if (
            not isinstance(entries, list)
            or not entries
            or source.get("readiness_entry_count") != len(entries)
        ):
            raise ProductionCallableInvocationAuthorizationInvariantError(
                "OIA-059 readiness entry count invalid"
            )

        seen: set[tuple[str, str, str]] = set()
        for entry in entries:
            entry_hash = entry.pop(
                "callable_invocation_readiness_hash",
                None,
            )
            if not _valid_hash(entry_hash) or stable_hash(entry) != entry_hash:
                raise ProductionCallableInvocationAuthorizationInvariantError(
                    "OIA-059 readiness entry hash verification failed"
                )
            entry["callable_invocation_readiness_hash"] = entry_hash

            adapter_id = entry.get("adapter_id")
            approved = APPROVED_INVOCATIONS.get(adapter_id)
            if approved is None:
                raise ProductionCallableInvocationAuthorizationInvariantError(
                    "unapproved OIA-059 adapter identity"
                )

            for field in (
                "read_operation",
                "module_path",
                "owner_name",
                "callable_name",
                "bound_method_module",
                "bound_method_qualname",
                "bound_method_signature",
                "invocation_arguments",
            ):
                if entry.get(field) != approved[field]:
                    raise ProductionCallableInvocationAuthorizationInvariantError(
                        f"OIA-059 invocation envelope drift: {field}"
                    )

            if entry.get("invocation_argument_hash") != stable_hash(
                approved["invocation_arguments"]
            ):
                raise ProductionCallableInvocationAuthorizationInvariantError(
                    "OIA-059 invocation argument hash drift"
                )

            key = (
                str(entry.get("worker_id")),
                str(entry.get("work_item_id")),
                str(adapter_id),
            )
            if key in seen:
                raise ProductionCallableInvocationAuthorizationInvariantError(
                    "duplicate OIA-059 readiness entry"
                )
            seen.add(key)

            expected_flags = {
                "owner_reconstruction_required": True,
                "owner_reconstructed": False,
                "method_binding_required": True,
                "method_bound_to_owner": False,
                "invocation_envelope_verified": True,
                "callable_invocation_ready": True,
                "callable_invoked": False,
                "adapter_executed": False,
                "corpus_read_executed": False,
            }
            for field, expected in expected_flags.items():
                if entry.get(field) != expected:
                    raise ProductionCallableInvocationAuthorizationInvariantError(
                        f"unsafe OIA-059 readiness entry: {field}"
                    )

            for hash_field in (
                "source_owner_method_binding_hash",
                "source_owner_method_binding_authorization_hash",
                "source_owner_method_binding_readiness_hash",
                "source_owner_construction_authorization_hash",
                "source_owner_construction_readiness_hash",
                "source_callable_argument_binding_hash",
            ):
                if not _valid_hash(entry.get(hash_field)):
                    raise ProductionCallableInvocationAuthorizationInvariantError(
                        f"OIA-059 lineage hash invalid: {hash_field}"
                    )

        if not isinstance(source.get("source_lineage"), dict) or not source["source_lineage"]:
            raise ProductionCallableInvocationAuthorizationInvariantError(
                "OIA-059 source lineage missing"
            )
        return source

    def authorize(
        self,
        *,
        authorized_at: datetime,
        persist: bool = True,
    ) -> ProductionCallableInvocationAuthorizationManifest:
        authorized_at = _aware(authorized_at, "authorized_at")
        source = self._load_readiness()
        entries: list[ProductionCallableInvocationAuthorizationEntry] = []

        for sequence, readiness in enumerate(source["readiness_entries"], start=1):
            body = {
                "sequence": sequence,
                "worker_id": readiness["worker_id"],
                "work_item_id": readiness["work_item_id"],
                "adapter_id": readiness["adapter_id"],
                "read_operation": readiness["read_operation"],
                "module_path": readiness["module_path"],
                "owner_name": readiness["owner_name"],
                "callable_name": readiness["callable_name"],
                "bound_method_module": readiness["bound_method_module"],
                "bound_method_qualname": readiness["bound_method_qualname"],
                "bound_method_signature": readiness["bound_method_signature"],
                "invocation_arguments": dict(readiness["invocation_arguments"]),
                "invocation_argument_hash": readiness["invocation_argument_hash"],
                "source_callable_invocation_readiness_hash": readiness[
                    "callable_invocation_readiness_hash"
                ],
                "source_owner_method_binding_hash": readiness[
                    "source_owner_method_binding_hash"
                ],
                "source_owner_method_binding_authorization_hash": readiness[
                    "source_owner_method_binding_authorization_hash"
                ],
                "source_owner_method_binding_readiness_hash": readiness[
                    "source_owner_method_binding_readiness_hash"
                ],
                "source_owner_construction_authorization_hash": readiness[
                    "source_owner_construction_authorization_hash"
                ],
                "source_owner_construction_readiness_hash": readiness[
                    "source_owner_construction_readiness_hash"
                ],
                "source_callable_argument_binding_hash": readiness[
                    "source_callable_argument_binding_hash"
                ],
                "callable_invocation_authorization_granted": True,
                "owner_reconstruction_authorized": True,
                "owner_reconstruction_performed": False,
                "method_binding_authorized": True,
                "method_binding_performed": False,
                "callable_invocation_authorized": True,
                "callable_invoked": False,
                "adapter_executed": False,
                "corpus_read_executed": False,
                "authorization_checks": (
                    "oia059_readiness_manifest_hash_verified",
                    "oia059_readiness_entry_hash_verified",
                    "approved_adapter_identity_frozen",
                    "approved_bound_method_identity_frozen",
                    "approved_bound_method_signature_frozen",
                    "approved_invocation_argument_envelope_frozen",
                    "invocation_argument_hash_verified",
                    "owner_reconstruction_authorized_not_performed",
                    "method_binding_authorized_not_performed",
                    "callable_invocation_authorized_not_performed",
                    "adapter_execution_not_performed",
                    "corpus_read_not_performed",
                    "oracle_qseries_boundary_verified",
                ),
                "authorization_status": STATUS_INVOCATION_AUTHORIZED,
            }
            entries.append(
                ProductionCallableInvocationAuthorizationEntry(
                    **body,
                    callable_invocation_authorization_hash=stable_hash(body),
                )
            )

        source_hash = source["callable_invocation_readiness_manifest_hash"]
        authorization_id = (
            "oia060-callable-invocation-authorization-"
            + stable_hash({"source": source_hash, "policy": POLICY_ID})[:32]
        )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "authorized_at": authorized_at.isoformat(),
            "callable_invocation_authorization_id": authorization_id,
            "callable_invocation_authorization_status": STATUS_AUTHORIZATION_ISSUED,
            "callable_invocation_authorization_policy_id": POLICY_ID,
            "worker_id": source["worker_id"],
            "authorization_entry_count": len(entries),
            "authorization_entries": tuple(entries),
            "source_callable_invocation_readiness_id": source[
                "callable_invocation_readiness_id"
            ],
            "source_callable_invocation_readiness_manifest_hash": source_hash,
            "source_owner_method_binding_id": source[
                "source_owner_method_binding_id"
            ],
            "source_owner_method_binding_manifest_hash": source[
                "source_owner_method_binding_manifest_hash"
            ],
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
            "source_owner_construction_id": source[
                "source_owner_construction_id"
            ],
            "source_owner_construction_manifest_hash": source[
                "source_owner_construction_manifest_hash"
            ],
            "source_lineage": dict(source["source_lineage"]),
            "callable_invocation_authorization_issued": True,
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
            "authorization_artifact_persistence_allowed": True,
            "owner_instances_retained": False,
            "bound_methods_retained": False,
        }

        serial = dict(body)
        serial["authorization_entries"] = [asdict(entry) for entry in entries]
        result = ProductionCallableInvocationAuthorizationManifest(
            **body,
            callable_invocation_authorization_manifest_hash=stable_hash(serial),
        )

        if persist:
            payload = asdict(result)
            _atomic_write(self.authorization_directory / "current.json", payload)
            _atomic_write(
                self.authorization_directory
                / "authorizations"
                / f"{authorization_id}.json",
                payload,
            )
            _atomic_write(
                self.authorization_directory
                / "workers"
                / result.worker_id
                / f"{authorization_id}.json",
                payload,
            )

        return result
