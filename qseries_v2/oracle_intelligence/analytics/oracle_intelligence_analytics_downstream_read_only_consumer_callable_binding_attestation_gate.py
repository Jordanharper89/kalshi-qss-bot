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

SCHEMA_VERSION = "INT-OIA-009"
ENGINE_ID = "INT-OIA-009"
POLICY_ID = "oracle.intelligence.analytics.downstream-read-only-consumer-callable-binding-attestation.v1"
STATUS_BOUND = "downstream_read_only_consumer_callable_binding_attested"

DEFAULT_RESOLUTION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_callable_resolution_attestation"
)
DEFAULT_BINDING_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_callable_binding_attestation"
)


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationInvariantError(
    RuntimeError
):
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
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationInvariantError(
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


def _aware(value: datetime, field: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationInvariantError(
            f"{field} must be timezone-aware"
        )
    return value.astimezone(timezone.utc)


def _atomic_write(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = (
        json.dumps(
            _canonical(payload),
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        delete=False,
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(handle.name)
    try:
        with handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


@dataclass(frozen=True)
class DownstreamReadOnlyConsumerCallableBindingAttestationRecord:
    sequence: int
    binding_attestation_id: str
    consumer_id: str
    consumer_module: str
    consumer_class: str
    callable_name: str
    callable_path: str
    source_resolution_attestation_id: str
    source_resolution_attestation_record_hash: str
    source_binding_contract_id: str
    source_binding_contract_hash: str
    source_activation_id: str
    source_activation_nonce: str
    source_boundary_id: str
    source_boundary_hash: str
    consumer_instantiated: bool
    consumer_instance_type: str
    callable_bound: bool
    bound_callable_is_callable: bool
    bound_callable_signature: str
    bound_callable_parameter_names: tuple[str, ...]
    bound_callable_identity_hash: str
    callable_invocation_allowed: bool
    callable_invocation_performed: bool
    corpus_read_performed: bool
    source_mutation_allowed: bool
    signals_allowed: bool
    alerts_allowed: bool
    qseries_execution_allowed: bool
    market_order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    binding_status: str
    binding_attestation_record_hash: str


@dataclass(frozen=True)
class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationManifest:
    schema_version: str
    engine_id: str
    attested_at: str
    binding_attestation_manifest_id: str
    binding_attestation_status: str
    binding_attestation_policy_id: str
    source_resolution_attestation_manifest_id: str
    source_resolution_attestation_manifest_hash: str
    source_resolution_readiness_manifest_id: str
    source_boundary_id: str
    source_boundary_hash: str
    attestation_record_count: int
    attestation_records: tuple[
        DownstreamReadOnlyConsumerCallableBindingAttestationRecord, ...
    ]
    all_resolution_hashes_verified: bool
    all_consumers_instantiated: bool
    all_callables_bound: bool
    all_bound_callables_callable: bool
    exact_callable_identity_preserved: bool
    source_boundary_consumed_without_reexecution: bool
    callable_invocation_allowed: bool
    callable_invocation_performed: bool
    corpus_read_execution_repeated: bool
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
    controlled_callable_invocation_authorized: bool
    attestation_artifact_persistence_allowed: bool
    binding_attestation_manifest_hash: str


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationGate:
    def __init__(
        self,
        *,
        resolution_directory: Path | str = DEFAULT_RESOLUTION_DIRECTORY,
        binding_directory: Path | str = DEFAULT_BINDING_DIRECTORY,
    ) -> None:
        self.resolution_directory = Path(resolution_directory)
        self.binding_directory = Path(binding_directory)

    def _load_resolution(self) -> dict[str, Any]:
        path = self.resolution_directory / "current.json"
        if not path.exists():
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationInvariantError(
                f"INT-OIA-008 resolution artifact missing: {path}"
            )

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationInvariantError(
                "INT-OIA-008 resolution artifact could not be decoded"
            ) from exc

        manifest_hash = payload.pop(
            "resolution_attestation_manifest_hash",
            None,
        )
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationInvariantError(
                "INT-OIA-008 resolution manifest hash mismatch"
            )
        payload["resolution_attestation_manifest_hash"] = manifest_hash

        required = {
            "schema_version": "INT-OIA-008",
            "engine_id": "INT-OIA-008",
            "all_readiness_hashes_verified": True,
            "all_modules_imported": True,
            "all_classes_resolved": True,
            "all_callables_resolved": True,
            "all_callables_callable": True,
            "exact_callable_identity_preserved": True,
            "source_boundary_consumed_without_reexecution": True,
            "callable_binding_allowed": True,
            "callable_binding_performed": False,
            "callable_invocation_allowed": False,
            "callable_invocation_performed": False,
            "consumer_instantiation_performed": False,
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
            "controlled_callable_binding_authorized": True,
            "attestation_artifact_persistence_allowed": True,
        }
        for field, expected in required.items():
            if payload.get(field) != expected:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationInvariantError(
                    f"unsafe or incomplete INT-OIA-008 field: {field}"
                )

        records = payload.get("attestation_records")
        if (
            not isinstance(records, list)
            or not records
            or payload.get("attestation_record_count") != len(records)
        ):
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationInvariantError(
                "INT-OIA-008 attestation records invalid"
            )

        seen_consumers: set[str] = set()
        for sequence, raw_record in enumerate(records, start=1):
            record = dict(raw_record)
            record_hash = record.pop(
                "resolution_attestation_record_hash",
                None,
            )
            if not _valid_hash(record_hash) or stable_hash(record) != record_hash:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationInvariantError(
                    "INT-OIA-008 resolution-record hash mismatch"
                )
            record["resolution_attestation_record_hash"] = record_hash

            if record.get("sequence") != sequence:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationInvariantError(
                    "INT-OIA-008 attestation sequence mismatch"
                )

            consumer_id = record.get("consumer_id")
            if (
                not isinstance(consumer_id, str)
                or not consumer_id
                or consumer_id in seen_consumers
            ):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationInvariantError(
                    "invalid or duplicate consumer"
                )
            seen_consumers.add(consumer_id)

            required_record = {
                "module_imported": True,
                "class_resolved": True,
                "callable_resolved": True,
                "callable_is_callable": True,
                "callable_bound": False,
                "callable_invoked": False,
                "consumer_instantiated": False,
                "corpus_read_performed": False,
                "source_mutation_allowed": False,
                "signals_allowed": False,
                "alerts_allowed": False,
                "qseries_execution_allowed": False,
                "market_order_creation_allowed": False,
                "funds_movement_allowed": False,
                "portfolio_mutation_allowed": False,
                "resolution_status": "resolved_not_bound",
            }
            for field, expected in required_record.items():
                if record.get(field) != expected:
                    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationInvariantError(
                        f"unsafe INT-OIA-008 record field: {field}"
                    )

        payload["attestation_records"] = records
        return payload

    def attest(
        self,
        *,
        attested_at: datetime,
        persist: bool = True,
    ) -> OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationManifest:
        attested_at = _aware(attested_at, "attested_at")
        source = self._load_resolution()

        records: list[
            DownstreamReadOnlyConsumerCallableBindingAttestationRecord
        ] = []

        for sequence, resolution in enumerate(
            source["attestation_records"],
            start=1,
        ):
            try:
                module = importlib.import_module(resolution["consumer_module"])
            except Exception as exc:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationInvariantError(
                    f"consumer module import failed: {resolution['consumer_module']}"
                ) from exc

            consumer_class = getattr(
                module,
                resolution["consumer_class"],
                None,
            )
            if not inspect.isclass(consumer_class):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationInvariantError(
                    "consumer class could not be resolved"
                )

            try:
                consumer_instance = consumer_class()
            except Exception as exc:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationInvariantError(
                    "consumer could not be instantiated without arguments"
                ) from exc

            bound_callable = getattr(
                consumer_instance,
                resolution["callable_name"],
                None,
            )
            if bound_callable is None or not callable(bound_callable):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationInvariantError(
                    "approved callable could not be bound"
                )

            bound_signature = inspect.signature(bound_callable)
            parameter_names = tuple(bound_signature.parameters.keys())
            identity_hash = stable_hash(
                {
                    "consumer_module": resolution["consumer_module"],
                    "consumer_class": resolution["consumer_class"],
                    "consumer_instance_type": (
                        f"{consumer_instance.__class__.__module__}."
                        f"{consumer_instance.__class__.__qualname__}"
                    ),
                    "callable_name": resolution["callable_name"],
                    "callable_path": resolution["callable_path"],
                    "bound_callable_signature": str(bound_signature),
                    "bound_callable_parameter_names": parameter_names,
                }
            )

            attestation_id = stable_hash(
                {
                    "source_resolution_attestation_manifest_id": source[
                        "resolution_attestation_manifest_id"
                    ],
                    "source_resolution_attestation_id": resolution[
                        "resolution_attestation_id"
                    ],
                    "source_resolution_attestation_record_hash": resolution[
                        "resolution_attestation_record_hash"
                    ],
                    "bound_callable_identity_hash": identity_hash,
                    "attested_at": attested_at.isoformat(),
                }
            )

            body = {
                "sequence": sequence,
                "binding_attestation_id": attestation_id,
                "consumer_id": resolution["consumer_id"],
                "consumer_module": resolution["consumer_module"],
                "consumer_class": resolution["consumer_class"],
                "callable_name": resolution["callable_name"],
                "callable_path": resolution["callable_path"],
                "source_resolution_attestation_id": resolution[
                    "resolution_attestation_id"
                ],
                "source_resolution_attestation_record_hash": resolution[
                    "resolution_attestation_record_hash"
                ],
                "source_binding_contract_id": resolution[
                    "source_binding_contract_id"
                ],
                "source_binding_contract_hash": resolution[
                    "source_binding_contract_hash"
                ],
                "source_activation_id": resolution[
                    "source_activation_id"
                ],
                "source_activation_nonce": resolution[
                    "source_activation_nonce"
                ],
                "source_boundary_id": resolution["source_boundary_id"],
                "source_boundary_hash": resolution[
                    "source_boundary_hash"
                ],
                "consumer_instantiated": True,
                "consumer_instance_type": (
                    f"{consumer_instance.__class__.__module__}."
                    f"{consumer_instance.__class__.__qualname__}"
                ),
                "callable_bound": True,
                "bound_callable_is_callable": True,
                "bound_callable_signature": str(bound_signature),
                "bound_callable_parameter_names": parameter_names,
                "bound_callable_identity_hash": identity_hash,
                "callable_invocation_allowed": True,
                "callable_invocation_performed": False,
                "corpus_read_performed": False,
                "source_mutation_allowed": False,
                "signals_allowed": False,
                "alerts_allowed": False,
                "qseries_execution_allowed": False,
                "market_order_creation_allowed": False,
                "funds_movement_allowed": False,
                "portfolio_mutation_allowed": False,
                "binding_status": "bound_not_invoked",
            }
            records.append(
                DownstreamReadOnlyConsumerCallableBindingAttestationRecord(
                    **body,
                    binding_attestation_record_hash=stable_hash(body),
                )
            )

        manifest_id = stable_hash(
            {
                "source_resolution_attestation_manifest_id": source[
                    "resolution_attestation_manifest_id"
                ],
                "source_resolution_attestation_manifest_hash": source[
                    "resolution_attestation_manifest_hash"
                ],
                "attested_at": attested_at.isoformat(),
                "binding_attestation_record_hashes": [
                    record.binding_attestation_record_hash
                    for record in records
                ],
            }
        )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "attested_at": attested_at.isoformat(),
            "binding_attestation_manifest_id": manifest_id,
            "binding_attestation_status": STATUS_BOUND,
            "binding_attestation_policy_id": POLICY_ID,
            "source_resolution_attestation_manifest_id": source[
                "resolution_attestation_manifest_id"
            ],
            "source_resolution_attestation_manifest_hash": source[
                "resolution_attestation_manifest_hash"
            ],
            "source_resolution_readiness_manifest_id": source[
                "source_resolution_readiness_manifest_id"
            ],
            "source_boundary_id": source["source_boundary_id"],
            "source_boundary_hash": source["source_boundary_hash"],
            "attestation_record_count": len(records),
            "attestation_records": tuple(records),
            "all_resolution_hashes_verified": True,
            "all_consumers_instantiated": True,
            "all_callables_bound": True,
            "all_bound_callables_callable": True,
            "exact_callable_identity_preserved": True,
            "source_boundary_consumed_without_reexecution": True,
            "callable_invocation_allowed": True,
            "callable_invocation_performed": False,
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
            "controlled_callable_invocation_authorized": True,
            "attestation_artifact_persistence_allowed": True,
        }

        serializable = dict(body)
        serializable["attestation_records"] = [
            asdict(record) for record in records
        ]
        manifest_hash = stable_hash(serializable)

        manifest = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationManifest(
            **body,
            binding_attestation_manifest_hash=manifest_hash,
        )

        if persist:
            payload = asdict(manifest)
            _atomic_write(
                self.binding_directory / "current.json",
                payload,
            )
            _atomic_write(
                self.binding_directory
                / "manifests"
                / f"{manifest_id}.json",
                payload,
            )
            for record in records:
                _atomic_write(
                    self.binding_directory
                    / "consumers"
                    / record.consumer_id
                    / f"{record.binding_attestation_id}.json",
                    asdict(record),
                )

        return manifest
