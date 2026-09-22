from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "INT-OIA-006"
ENGINE_ID = "INT-OIA-006"
POLICY_ID = "oracle.intelligence.analytics.downstream-read-only-consumer-callable-binding-contract.v1"
DEFAULT_ACTIVATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_controlled_activation"
)
DEFAULT_BINDING_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_callable_binding_contract"
)
APPROVED_CALLABLE_NAME = "analyze_certified_oia_artifacts"


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingInvariantError(RuntimeError):
    pass


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {str(k): _canonical(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonical(v) for v in value]
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingInvariantError(
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
        and all(c in "0123456789abcdef" for c in value)
    )


def _aware(value: datetime, field: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingInvariantError(
            f"{field} must be timezone-aware"
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
    h = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        delete=False,
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    tmp = Path(h.name)
    try:
        with h:
            h.write(rendered)
            h.flush()
            os.fsync(h.fileno())
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


@dataclass(frozen=True)
class DownstreamReadOnlyConsumerCallableBindingContract:
    sequence: int
    binding_contract_id: str
    consumer_id: str
    consumer_module: str
    consumer_class: str
    callable_name: str
    callable_path: str
    source_activation_id: str
    source_activation_nonce: str
    source_activation_record_hash: str
    source_contract_id: str
    source_contract_hash: str
    source_boundary_id: str
    source_boundary_hash: str
    authorized_capabilities: tuple[str, ...]
    exact_callable_identity_required: bool
    dynamic_import_allowed: bool
    callable_resolution_allowed: bool
    callable_binding_allowed: bool
    callable_invocation_allowed: bool
    callable_resolution_performed: bool
    callable_binding_performed: bool
    callable_invocation_performed: bool
    corpus_read_allowed: bool
    source_mutation_allowed: bool
    signals_allowed: bool
    alerts_allowed: bool
    qseries_execution_allowed: bool
    market_order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    binding_status: str
    binding_contract_hash: str


@dataclass(frozen=True)
class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingManifest:
    schema_version: str
    engine_id: str
    issued_at: str
    binding_manifest_id: str
    source_activation_manifest_id: str
    source_activation_manifest_hash: str
    source_boundary_id: str
    source_boundary_hash: str
    binding_contract_count: int
    binding_contracts: tuple[DownstreamReadOnlyConsumerCallableBindingContract, ...]
    all_activation_hashes_verified: bool
    all_activation_nonces_unique: bool
    exact_consumer_identity_preserved: bool
    exact_callable_identity_frozen: bool
    source_boundary_consumed_without_reexecution: bool
    corpus_read_execution_repeated: bool
    callable_resolution_allowed: bool
    callable_binding_allowed: bool
    callable_invocation_allowed: bool
    callable_resolution_performed: bool
    callable_binding_performed: bool
    callable_invocation_performed: bool
    source_mutation_allowed: bool
    source_mutation_performed: bool
    analytic_conclusion_allowed: bool
    forecast_creation_allowed: bool
    signals_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    market_order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    binding_artifact_persistence_allowed: bool
    binding_manifest_hash: str


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingContractGate:
    def __init__(
        self,
        *,
        activation_directory: Path | str = DEFAULT_ACTIVATION_DIRECTORY,
        binding_directory: Path | str = DEFAULT_BINDING_DIRECTORY,
    ) -> None:
        self.activation_directory = Path(activation_directory)
        self.binding_directory = Path(binding_directory)

    def _load(self) -> dict[str, Any]:
        path = self.activation_directory / "current.json"
        if not path.exists():
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingInvariantError(
                f"INT-OIA-005 activation artifact missing: {path}"
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingInvariantError(
                "INT-OIA-005 activation artifact could not be decoded"
            ) from exc

        manifest_hash = payload.pop("activation_manifest_hash", None)
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingInvariantError(
                "INT-OIA-005 activation manifest hash mismatch"
            )
        payload["activation_manifest_hash"] = manifest_hash

        required = {
            "schema_version": "INT-OIA-005",
            "engine_id": "INT-OIA-005",
            "all_readiness_hashes_verified": True,
            "all_consumers_activated_once": True,
            "all_activation_nonces_unique": True,
            "source_boundary_consumed_without_reexecution": True,
            "corpus_read_execution_repeated": False,
            "source_mutation_allowed": False,
            "source_mutation_performed": False,
            "analytic_conclusion_allowed": True,
            "forecast_creation_allowed": False,
            "signals_allowed": False,
            "alerts_allowed": False,
            "qseries_handoff_allowed": False,
            "qseries_execution_allowed": False,
            "market_order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
            "downstream_consumer_execution_allowed": True,
            "downstream_consumer_execution_performed": False,
        }
        for key, expected in required.items():
            if payload.get(key) != expected:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingInvariantError(
                    f"unsafe or incomplete INT-OIA-005 field: {key}"
                )

        records = payload.get("activation_records")
        if not isinstance(records, list) or not records or payload.get("activation_record_count") != len(records):
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingInvariantError(
                "INT-OIA-005 activation records invalid"
            )

        seen_ids: set[str] = set()
        seen_nonces: set[str] = set()
        for sequence, raw in enumerate(records, start=1):
            record = dict(raw)
            record_hash = record.pop("activation_record_hash", None)
            if not _valid_hash(record_hash) or stable_hash(record) != record_hash:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingInvariantError(
                    "INT-OIA-005 activation-record hash mismatch"
                )
            record["activation_record_hash"] = record_hash
            if record.get("sequence") != sequence:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingInvariantError(
                    "activation sequence mismatch"
                )
            cid = record.get("consumer_id")
            nonce = record.get("activation_nonce")
            if not isinstance(cid, str) or not cid or cid in seen_ids:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingInvariantError(
                    "invalid or duplicate consumer"
                )
            if not _valid_hash(nonce) or nonce in seen_nonces:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingInvariantError(
                    "invalid or duplicate activation nonce"
                )
            seen_ids.add(cid)
            seen_nonces.add(nonce)
            for key, expected in {
                "activation_mode": "controlled_one_time_read_only",
                "one_time_activation": True,
                "readiness_consumed": True,
                "execution_performed": False,
                "callable_binding_performed": False,
                "callable_invocation_performed": False,
                "corpus_read_performed": False,
                "source_mutation_allowed": False,
                "signals_allowed": False,
                "alerts_allowed": False,
                "qseries_execution_allowed": False,
                "market_order_creation_allowed": False,
                "funds_movement_allowed": False,
                "portfolio_mutation_allowed": False,
                "activation_status": "activated_not_executed",
            }.items():
                if record.get(key) != expected:
                    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingInvariantError(
                        f"unsafe activation record field: {key}"
                    )
        payload["activation_records"] = records
        return payload

    def issue(
        self,
        *,
        issued_at: datetime,
        persist: bool = True,
    ) -> OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingManifest:
        issued_at = _aware(issued_at, "issued_at")
        source = self._load()
        contracts = []

        for sequence, activation in enumerate(source["activation_records"], start=1):
            callable_path = (
                f"{activation['consumer_module']}."
                f"{activation['consumer_class']}."
                f"{APPROVED_CALLABLE_NAME}"
            )
            contract_id = stable_hash(
                {
                    "source_activation_manifest_id": source["activation_manifest_id"],
                    "source_activation_id": activation["activation_id"],
                    "source_activation_nonce": activation["activation_nonce"],
                    "consumer_id": activation["consumer_id"],
                    "callable_path": callable_path,
                }
            )
            body = {
                "sequence": sequence,
                "binding_contract_id": contract_id,
                "consumer_id": activation["consumer_id"],
                "consumer_module": activation["consumer_module"],
                "consumer_class": activation["consumer_class"],
                "callable_name": APPROVED_CALLABLE_NAME,
                "callable_path": callable_path,
                "source_activation_id": activation["activation_id"],
                "source_activation_nonce": activation["activation_nonce"],
                "source_activation_record_hash": activation["activation_record_hash"],
                "source_contract_id": activation["source_contract_id"],
                "source_contract_hash": activation["source_contract_hash"],
                "source_boundary_id": activation["source_boundary_id"],
                "source_boundary_hash": activation["source_boundary_hash"],
                "authorized_capabilities": tuple(activation["authorized_capabilities"]),
                "exact_callable_identity_required": True,
                "dynamic_import_allowed": False,
                "callable_resolution_allowed": False,
                "callable_binding_allowed": False,
                "callable_invocation_allowed": False,
                "callable_resolution_performed": False,
                "callable_binding_performed": False,
                "callable_invocation_performed": False,
                "corpus_read_allowed": False,
                "source_mutation_allowed": False,
                "signals_allowed": False,
                "alerts_allowed": False,
                "qseries_execution_allowed": False,
                "market_order_creation_allowed": False,
                "funds_movement_allowed": False,
                "portfolio_mutation_allowed": False,
                "binding_status": "contract_issued_not_resolved",
            }
            contracts.append(
                DownstreamReadOnlyConsumerCallableBindingContract(
                    **body,
                    binding_contract_hash=stable_hash(body),
                )
            )

        manifest_id = stable_hash(
            {
                "source_activation_manifest_id": source["activation_manifest_id"],
                "source_activation_manifest_hash": source["activation_manifest_hash"],
                "issued_at": issued_at.isoformat(),
                "binding_contract_hashes": [c.binding_contract_hash for c in contracts],
            }
        )
        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "issued_at": issued_at.isoformat(),
            "binding_manifest_id": manifest_id,
            "source_activation_manifest_id": source["activation_manifest_id"],
            "source_activation_manifest_hash": source["activation_manifest_hash"],
            "source_boundary_id": source["source_boundary_id"],
            "source_boundary_hash": source["source_boundary_hash"],
            "binding_contract_count": len(contracts),
            "binding_contracts": tuple(contracts),
            "all_activation_hashes_verified": True,
            "all_activation_nonces_unique": True,
            "exact_consumer_identity_preserved": True,
            "exact_callable_identity_frozen": True,
            "source_boundary_consumed_without_reexecution": True,
            "corpus_read_execution_repeated": False,
            "callable_resolution_allowed": False,
            "callable_binding_allowed": False,
            "callable_invocation_allowed": False,
            "callable_resolution_performed": False,
            "callable_binding_performed": False,
            "callable_invocation_performed": False,
            "source_mutation_allowed": False,
            "source_mutation_performed": False,
            "analytic_conclusion_allowed": True,
            "forecast_creation_allowed": False,
            "signals_allowed": False,
            "alerts_allowed": False,
            "qseries_handoff_allowed": False,
            "qseries_execution_allowed": False,
            "market_order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
            "binding_artifact_persistence_allowed": True,
        }
        serializable = dict(body)
        serializable["binding_contracts"] = [asdict(c) for c in contracts]
        manifest = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingManifest(
            **body,
            binding_manifest_hash=stable_hash(serializable),
        )

        if persist:
            payload = asdict(manifest)
            _atomic_write(self.binding_directory / "current.json", payload)
            _atomic_write(
                self.binding_directory / "manifests" / f"{manifest_id}.json",
                payload,
            )
            for contract in contracts:
                _atomic_write(
                    self.binding_directory
                    / "consumers"
                    / contract.consumer_id
                    / f"{contract.binding_contract_id}.json",
                    asdict(contract),
                )
        return manifest
