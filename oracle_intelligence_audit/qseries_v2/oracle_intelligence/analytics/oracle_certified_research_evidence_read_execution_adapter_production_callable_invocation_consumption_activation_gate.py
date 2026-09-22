
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "OIA-064"
ENGINE_ID = "OIA-064"
POLICY_ID = (
    "oracle.certified-research-evidence-read-execution-adapter-"
    "production-callable-invocation-consumption-activation.v1"
)
STATUS_CONSUMPTION_ACTIVATED = (
    "evidence_read_execution_adapter_production_callable_invocation_consumption_activated"
)
STATUS_ACTIVATION_ISSUED = (
    "evidence_read_execution_adapter_production_callable_invocation_consumption_activation_issued"
)

DEFAULT_AUTHORIZATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "certified_research_evidence_read_execution_adapter_production_callable_invocation_consumption_authorization"
)
DEFAULT_ACTIVATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "certified_research_evidence_read_execution_adapter_production_callable_invocation_consumption_activation"
)

APPROVED = {
    "oracle_read_only_canonical_observation_adapter.v1": {
        "read_operation": "read_canonical_observations",
        "module_path": "qseries_v2.oracle_intelligence.analytics.oracle_live_corpus_inspector",
        "owner_name": "OracleLiveCorpusInspector",
        "callable_name": "inspect",
        "bound_method_module": "qseries_v2.oracle_intelligence.analytics.oracle_live_corpus_inspector",
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


class ProductionCallableInvocationConsumptionActivationInvariantError(RuntimeError):
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
            raise ProductionCallableInvocationConsumptionActivationInvariantError(
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


def _aware(value: datetime, name: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise ProductionCallableInvocationConsumptionActivationInvariantError(
            f"{name} must be timezone-aware"
        )
    return value.astimezone(timezone.utc)


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
class ProductionCallableInvocationConsumptionActivationEntry:
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
    activation_nonce: str
    consumption_attempt_nonce: str
    source_consumption_authorization_hash: str
    source_consumption_readiness_hash: str
    source_invocation_activation_hash: str
    source_invocation_authorization_hash: str
    consumption_activation_granted: bool
    consumption_activation_consumed: bool
    original_activation_consumed: bool
    owner_reconstruction_performed: bool
    method_binding_performed: bool
    callable_invoked: bool
    adapter_executed: bool
    corpus_read_executed: bool
    activation_checks: tuple[str, ...]
    activation_status: str
    callable_invocation_consumption_activation_hash: str


@dataclass(frozen=True)
class ProductionCallableInvocationConsumptionActivationManifest:
    schema_version: str
    engine_id: str
    activated_at: str
    callable_invocation_consumption_activation_id: str
    callable_invocation_consumption_activation_status: str
    callable_invocation_consumption_activation_policy_id: str
    worker_id: str
    activation_entry_count: int
    activation_entries: tuple[ProductionCallableInvocationConsumptionActivationEntry, ...]
    source_consumption_authorization_id: str
    source_consumption_authorization_manifest_hash: str
    source_consumption_readiness_id: str
    source_consumption_readiness_manifest_hash: str
    source_invocation_activation_id: str
    source_invocation_activation_manifest_hash: str
    source_invocation_authorization_id: str
    source_invocation_authorization_manifest_hash: str
    source_lineage: dict[str, Any]
    callable_invocation_consumption_activation_issued: bool
    single_execution_attempt_required: bool
    activation_consumption_allowed: bool
    activation_consumption_performed: bool
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
    activation_artifact_persistence_allowed: bool
    owner_instances_retained: bool
    bound_methods_retained: bool
    callable_invocation_consumption_activation_manifest_hash: str


class OracleCertifiedResearchEvidenceReadExecutionAdapterProductionCallableInvocationConsumptionActivationGate:
    def __init__(
        self,
        *,
        authorization_directory: Path | str = DEFAULT_AUTHORIZATION_DIRECTORY,
        activation_directory: Path | str = DEFAULT_ACTIVATION_DIRECTORY,
    ) -> None:
        self.authorization_directory = Path(authorization_directory)
        self.activation_directory = Path(activation_directory)

    def _load_authorization(self) -> dict[str, Any]:
        path = self.authorization_directory / "current.json"
        if not path.exists():
            raise ProductionCallableInvocationConsumptionActivationInvariantError(
                f"OIA-063 current authorization artifact missing: {path}"
            )
        try:
            source = json.loads(path.read_text(encoding="utf-8"))
        except Exception as error:
            raise ProductionCallableInvocationConsumptionActivationInvariantError(
                "OIA-063 authorization artifact could not be decoded"
            ) from error

        manifest_hash = source.pop(
            "callable_invocation_consumption_authorization_manifest_hash",
            None,
        )
        if not _valid_hash(manifest_hash) or stable_hash(source) != manifest_hash:
            raise ProductionCallableInvocationConsumptionActivationInvariantError(
                "OIA-063 authorization manifest hash verification failed"
            )
        source["callable_invocation_consumption_authorization_manifest_hash"] = (
            manifest_hash
        )

        expected_manifest = {
            "schema_version": "OIA-063",
            "engine_id": "OIA-063",
            "callable_invocation_consumption_authorization_issued": True,
            "activation_consumption_allowed": False,
            "activation_consumption_performed": False,
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
            "qseries_handoff_allowed": False,
            "execution_allowed": False,
            "market_order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
            "owner_instances_retained": False,
            "bound_methods_retained": False,
        }
        for field, expected in expected_manifest.items():
            if source.get(field) != expected:
                raise ProductionCallableInvocationConsumptionActivationInvariantError(
                    f"unsafe OIA-063 authorization manifest: {field}"
                )

        entries = source.get("authorization_entries")
        if (
            not isinstance(entries, list)
            or not entries
            or source.get("authorization_entry_count") != len(entries)
        ):
            raise ProductionCallableInvocationConsumptionActivationInvariantError(
                "OIA-063 authorization entry count invalid"
            )

        seen_keys: set[tuple[str, str, str]] = set()
        seen_nonces: set[str] = set()
        for expected_sequence, entry in enumerate(entries, start=1):
            if entry.get("sequence") != expected_sequence:
                raise ProductionCallableInvocationConsumptionActivationInvariantError(
                    "OIA-063 authorization sequence invalid"
                )

            entry_hash = entry.pop(
                "callable_invocation_consumption_authorization_hash",
                None,
            )
            if not _valid_hash(entry_hash) or stable_hash(entry) != entry_hash:
                raise ProductionCallableInvocationConsumptionActivationInvariantError(
                    "OIA-063 authorization entry hash verification failed"
                )
            entry["callable_invocation_consumption_authorization_hash"] = entry_hash

            approved = APPROVED.get(entry.get("adapter_id"))
            if approved is None:
                raise ProductionCallableInvocationConsumptionActivationInvariantError(
                    "unapproved OIA-063 adapter identity"
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
                    raise ProductionCallableInvocationConsumptionActivationInvariantError(
                        f"OIA-063 consumption-authorization drift: {field}"
                    )
            if entry.get("invocation_argument_hash") != stable_hash(
                approved["invocation_arguments"]
            ):
                raise ProductionCallableInvocationConsumptionActivationInvariantError(
                    "OIA-063 invocation argument hash drift"
                )

            key = (
                str(entry.get("worker_id")),
                str(entry.get("work_item_id")),
                str(entry.get("adapter_id")),
            )
            if key in seen_keys:
                raise ProductionCallableInvocationConsumptionActivationInvariantError(
                    "duplicate OIA-063 authorization entry"
                )
            seen_keys.add(key)

            nonce = entry.get("activation_nonce")
            if not _valid_hash(nonce) or nonce in seen_nonces:
                raise ProductionCallableInvocationConsumptionActivationInvariantError(
                    "invalid or duplicate OIA-063 activation nonce"
                )
            seen_nonces.add(nonce)

            expected_entry = {
                "activation_consumption_authorization_granted": True,
                "activation_consumption_authorized": True,
                "activation_consumed": False,
                "owner_reconstruction_authorized": True,
                "owner_reconstruction_performed": False,
                "method_binding_authorized": True,
                "method_binding_performed": False,
                "callable_invocation_authorized": True,
                "callable_invoked": False,
                "adapter_executed": False,
                "corpus_read_executed": False,
            }
            for field, expected in expected_entry.items():
                if entry.get(field) != expected:
                    raise ProductionCallableInvocationConsumptionActivationInvariantError(
                        f"unsafe OIA-063 authorization entry: {field}"
                    )

            for hash_field in (
                "source_callable_invocation_consumption_readiness_hash",
                "source_callable_invocation_activation_hash",
                "source_callable_invocation_authorization_hash",
            ):
                if not _valid_hash(entry.get(hash_field)):
                    raise ProductionCallableInvocationConsumptionActivationInvariantError(
                        f"OIA-063 lineage hash invalid: {hash_field}"
                    )

        if not isinstance(source.get("source_lineage"), dict) or not source["source_lineage"]:
            raise ProductionCallableInvocationConsumptionActivationInvariantError(
                "OIA-063 source lineage missing"
            )
        return source

    def activate(
        self,
        *,
        activated_at: datetime,
        persist: bool = True,
    ) -> ProductionCallableInvocationConsumptionActivationManifest:
        activated_at = _aware(activated_at, "activated_at")
        source = self._load_authorization()
        entries: list[ProductionCallableInvocationConsumptionActivationEntry] = []

        for sequence, authorization in enumerate(
            source["authorization_entries"],
            start=1,
        ):
            attempt_nonce = stable_hash({
                "authorization_hash": authorization[
                    "callable_invocation_consumption_authorization_hash"
                ],
                "activation_nonce": authorization["activation_nonce"],
                "worker_id": authorization["worker_id"],
                "work_item_id": authorization["work_item_id"],
                "adapter_id": authorization["adapter_id"],
                "policy_id": POLICY_ID,
            })
            body = {
                "sequence": sequence,
                "worker_id": authorization["worker_id"],
                "work_item_id": authorization["work_item_id"],
                "adapter_id": authorization["adapter_id"],
                "read_operation": authorization["read_operation"],
                "module_path": authorization["module_path"],
                "owner_name": authorization["owner_name"],
                "callable_name": authorization["callable_name"],
                "bound_method_module": authorization["bound_method_module"],
                "bound_method_qualname": authorization["bound_method_qualname"],
                "bound_method_signature": authorization["bound_method_signature"],
                "invocation_arguments": dict(authorization["invocation_arguments"]),
                "invocation_argument_hash": authorization[
                    "invocation_argument_hash"
                ],
                "activation_nonce": authorization["activation_nonce"],
                "consumption_attempt_nonce": attempt_nonce,
                "source_consumption_authorization_hash": authorization[
                    "callable_invocation_consumption_authorization_hash"
                ],
                "source_consumption_readiness_hash": authorization[
                    "source_callable_invocation_consumption_readiness_hash"
                ],
                "source_invocation_activation_hash": authorization[
                    "source_callable_invocation_activation_hash"
                ],
                "source_invocation_authorization_hash": authorization[
                    "source_callable_invocation_authorization_hash"
                ],
                "consumption_activation_granted": True,
                "consumption_activation_consumed": False,
                "original_activation_consumed": False,
                "owner_reconstruction_performed": False,
                "method_binding_performed": False,
                "callable_invoked": False,
                "adapter_executed": False,
                "corpus_read_executed": False,
                "activation_checks": (
                    "oia063_authorization_manifest_hash_verified",
                    "oia063_authorization_entry_hash_verified",
                    "approved_adapter_identity_frozen",
                    "approved_callable_identity_frozen",
                    "approved_callable_signature_frozen",
                    "approved_invocation_arguments_frozen",
                    "original_activation_nonce_verified",
                    "original_activation_unconsumed_verified",
                    "single_execution_attempt_nonce_issued",
                    "consumption_activation_not_consumed",
                    "owner_not_reconstructed",
                    "method_not_bound",
                    "callable_not_invoked",
                    "adapter_not_executed",
                    "corpus_not_read",
                    "oracle_qseries_boundary_verified",
                ),
                "activation_status": STATUS_CONSUMPTION_ACTIVATED,
            }
            entries.append(
                ProductionCallableInvocationConsumptionActivationEntry(
                    **body,
                    callable_invocation_consumption_activation_hash=stable_hash(
                        body
                    ),
                )
            )

        source_hash = source[
            "callable_invocation_consumption_authorization_manifest_hash"
        ]
        activation_id = (
            "oia064-callable-invocation-consumption-activation-"
            + stable_hash({"source": source_hash, "policy": POLICY_ID})[:32]
        )
        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "activated_at": activated_at.isoformat(),
            "callable_invocation_consumption_activation_id": activation_id,
            "callable_invocation_consumption_activation_status": STATUS_ACTIVATION_ISSUED,
            "callable_invocation_consumption_activation_policy_id": POLICY_ID,
            "worker_id": source["worker_id"],
            "activation_entry_count": len(entries),
            "activation_entries": tuple(entries),
            "source_consumption_authorization_id": source[
                "callable_invocation_consumption_authorization_id"
            ],
            "source_consumption_authorization_manifest_hash": source_hash,
            "source_consumption_readiness_id": source[
                "source_callable_invocation_consumption_readiness_id"
            ],
            "source_consumption_readiness_manifest_hash": source[
                "source_callable_invocation_consumption_readiness_manifest_hash"
            ],
            "source_invocation_activation_id": source[
                "source_callable_invocation_activation_id"
            ],
            "source_invocation_activation_manifest_hash": source[
                "source_callable_invocation_activation_manifest_hash"
            ],
            "source_invocation_authorization_id": source[
                "source_callable_invocation_authorization_id"
            ],
            "source_invocation_authorization_manifest_hash": source[
                "source_callable_invocation_authorization_manifest_hash"
            ],
            "source_lineage": dict(source["source_lineage"]),
            "callable_invocation_consumption_activation_issued": True,
            "single_execution_attempt_required": True,
            "activation_consumption_allowed": False,
            "activation_consumption_performed": False,
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
            "activation_artifact_persistence_allowed": True,
            "owner_instances_retained": False,
            "bound_methods_retained": False,
        }
        serial = dict(body)
        serial["activation_entries"] = [asdict(entry) for entry in entries]
        result = ProductionCallableInvocationConsumptionActivationManifest(
            **body,
            callable_invocation_consumption_activation_manifest_hash=stable_hash(
                serial
            ),
        )

        if persist:
            payload = asdict(result)
            _atomic_write(self.activation_directory / "current.json", payload)
            _atomic_write(
                self.activation_directory
                / "activations"
                / f"{activation_id}.json",
                payload,
            )
            _atomic_write(
                self.activation_directory
                / "workers"
                / result.worker_id
                / f"{activation_id}.json",
                payload,
            )
        return result
