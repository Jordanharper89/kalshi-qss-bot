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

SCHEMA_VERSION = "INT-OIA-008"
ENGINE_ID = "INT-OIA-008"
POLICY_ID = "oracle.intelligence.analytics.downstream-read-only-consumer-callable-resolution-attestation.v1"
STATUS_RESOLVED = "downstream_read_only_consumer_callable_resolution_attested"

DEFAULT_READINESS_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_callable_resolution_readiness"
)
DEFAULT_ATTESTATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_callable_resolution_attestation"
)

APPROVED_CALLABLE_NAME = "analyze_certified_oia_artifacts"


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionAttestationInvariantError(
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
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionAttestationInvariantError(
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
        raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionAttestationInvariantError(
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
class DownstreamReadOnlyConsumerCallableResolutionAttestationRecord:
    sequence: int
    resolution_attestation_id: str
    consumer_id: str
    consumer_module: str
    consumer_class: str
    callable_name: str
    callable_path: str
    source_resolution_readiness_id: str
    source_resolution_readiness_record_hash: str
    source_binding_contract_id: str
    source_binding_contract_hash: str
    source_activation_id: str
    source_activation_nonce: str
    source_boundary_id: str
    source_boundary_hash: str
    module_imported: bool
    class_resolved: bool
    callable_resolved: bool
    callable_is_callable: bool
    callable_is_coroutine: bool
    callable_signature: str
    callable_parameter_names: tuple[str, ...]
    callable_bound: bool
    callable_invoked: bool
    consumer_instantiated: bool
    corpus_read_performed: bool
    source_mutation_allowed: bool
    signals_allowed: bool
    alerts_allowed: bool
    qseries_execution_allowed: bool
    market_order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    resolution_status: str
    resolution_attestation_record_hash: str


@dataclass(frozen=True)
class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionAttestationManifest:
    schema_version: str
    engine_id: str
    attested_at: str
    resolution_attestation_manifest_id: str
    resolution_attestation_status: str
    resolution_attestation_policy_id: str
    source_resolution_readiness_manifest_id: str
    source_resolution_readiness_manifest_hash: str
    source_binding_manifest_id: str
    source_boundary_id: str
    source_boundary_hash: str
    attestation_record_count: int
    attestation_records: tuple[
        DownstreamReadOnlyConsumerCallableResolutionAttestationRecord, ...
    ]
    all_readiness_hashes_verified: bool
    all_modules_imported: bool
    all_classes_resolved: bool
    all_callables_resolved: bool
    all_callables_callable: bool
    exact_callable_identity_preserved: bool
    source_boundary_consumed_without_reexecution: bool
    callable_binding_allowed: bool
    callable_binding_performed: bool
    callable_invocation_allowed: bool
    callable_invocation_performed: bool
    consumer_instantiation_performed: bool
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
    controlled_callable_binding_authorized: bool
    attestation_artifact_persistence_allowed: bool
    resolution_attestation_manifest_hash: str


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionAttestationGate:
    def __init__(
        self,
        *,
        readiness_directory: Path | str = DEFAULT_READINESS_DIRECTORY,
        attestation_directory: Path | str = DEFAULT_ATTESTATION_DIRECTORY,
    ) -> None:
        self.readiness_directory = Path(readiness_directory)
        self.attestation_directory = Path(attestation_directory)

    def _load_readiness(self) -> dict[str, Any]:
        path = self.readiness_directory / "current.json"
        if not path.exists():
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionAttestationInvariantError(
                f"INT-OIA-007 readiness artifact missing: {path}"
            )

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionAttestationInvariantError(
                "INT-OIA-007 readiness artifact could not be decoded"
            ) from exc

        manifest_hash = payload.pop(
            "resolution_readiness_manifest_hash",
            None,
        )
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionAttestationInvariantError(
                "INT-OIA-007 readiness manifest hash mismatch"
            )
        payload["resolution_readiness_manifest_hash"] = manifest_hash

        required = {
            "schema_version": "INT-OIA-007",
            "engine_id": "INT-OIA-007",
            "all_binding_hashes_verified": True,
            "all_callable_paths_consistent": True,
            "exact_callable_identity_preserved": True,
            "source_boundary_consumed_without_reexecution": True,
            "dynamic_import_allowed": False,
            "module_import_performed": False,
            "callable_resolution_allowed": True,
            "callable_resolution_performed": False,
            "callable_binding_allowed": False,
            "callable_binding_performed": False,
            "callable_invocation_allowed": False,
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
            "controlled_callable_resolution_authorized": True,
            "readiness_artifact_persistence_allowed": True,
        }
        for field, expected in required.items():
            if payload.get(field) != expected:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionAttestationInvariantError(
                    f"unsafe or incomplete INT-OIA-007 field: {field}"
                )

        records = payload.get("readiness_records")
        if (
            not isinstance(records, list)
            or not records
            or payload.get("readiness_record_count") != len(records)
        ):
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionAttestationInvariantError(
                "INT-OIA-007 readiness records invalid"
            )

        seen_consumers: set[str] = set()
        for sequence, raw_record in enumerate(records, start=1):
            record = dict(raw_record)
            record_hash = record.pop(
                "resolution_readiness_record_hash",
                None,
            )
            if not _valid_hash(record_hash) or stable_hash(record) != record_hash:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionAttestationInvariantError(
                    "INT-OIA-007 readiness-record hash mismatch"
                )
            record["resolution_readiness_record_hash"] = record_hash

            if record.get("sequence") != sequence:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionAttestationInvariantError(
                    "INT-OIA-007 readiness sequence mismatch"
                )

            consumer_id = record.get("consumer_id")
            if (
                not isinstance(consumer_id, str)
                or not consumer_id
                or consumer_id in seen_consumers
            ):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionAttestationInvariantError(
                    "invalid or duplicate consumer"
                )
            seen_consumers.add(consumer_id)

            module_name = record.get("consumer_module")
            class_name = record.get("consumer_class")
            callable_name = record.get("callable_name")
            callable_path = record.get("callable_path")
            if (
                not isinstance(module_name, str)
                or not module_name
                or not isinstance(class_name, str)
                or not class_name
                or callable_name != APPROVED_CALLABLE_NAME
                or callable_path
                != f"{module_name}.{class_name}.{APPROVED_CALLABLE_NAME}"
            ):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionAttestationInvariantError(
                    "INT-OIA-007 callable identity mismatch"
                )

            required_record = {
                "module_identity_valid": True,
                "class_identity_valid": True,
                "callable_identity_valid": True,
                "callable_path_consistent": True,
                "exact_identity_hash_verified": True,
                "dynamic_import_allowed": False,
                "module_import_performed": False,
                "callable_resolution_allowed": True,
                "callable_resolution_performed": False,
                "callable_binding_allowed": False,
                "callable_binding_performed": False,
                "callable_invocation_allowed": False,
                "callable_invocation_performed": False,
                "corpus_read_allowed": False,
                "source_mutation_allowed": False,
                "signals_allowed": False,
                "alerts_allowed": False,
                "qseries_execution_allowed": False,
                "market_order_creation_allowed": False,
                "funds_movement_allowed": False,
                "portfolio_mutation_allowed": False,
                "controlled_resolution_authorized": True,
                "readiness_status": "ready_for_controlled_resolution",
            }
            for field, expected in required_record.items():
                if record.get(field) != expected:
                    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionAttestationInvariantError(
                        f"unsafe INT-OIA-007 readiness-record field: {field}"
                    )

        payload["readiness_records"] = records
        return payload

    def attest(
        self,
        *,
        attested_at: datetime,
        persist: bool = True,
    ) -> OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionAttestationManifest:
        attested_at = _aware(attested_at, "attested_at")
        source = self._load_readiness()

        attestations: list[
            DownstreamReadOnlyConsumerCallableResolutionAttestationRecord
        ] = []

        for sequence, readiness in enumerate(
            source["readiness_records"],
            start=1,
        ):
            try:
                module = importlib.import_module(readiness["consumer_module"])
            except Exception as exc:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionAttestationInvariantError(
                    f"consumer module import failed: {readiness['consumer_module']}"
                ) from exc

            consumer_class = getattr(
                module,
                readiness["consumer_class"],
                None,
            )
            if not inspect.isclass(consumer_class):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionAttestationInvariantError(
                    "consumer class could not be resolved"
                )

            target = getattr(
                consumer_class,
                readiness["callable_name"],
                None,
            )
            if target is None or not callable(target):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionAttestationInvariantError(
                    "approved analytical callable could not be resolved"
                )

            signature = inspect.signature(target)
            parameter_names = tuple(signature.parameters.keys())
            callable_is_coroutine = inspect.iscoroutinefunction(target)

            attestation_id = stable_hash(
                {
                    "source_resolution_readiness_manifest_id": source[
                        "resolution_readiness_manifest_id"
                    ],
                    "source_resolution_readiness_id": readiness[
                        "resolution_readiness_id"
                    ],
                    "source_resolution_readiness_record_hash": readiness[
                        "resolution_readiness_record_hash"
                    ],
                    "consumer_id": readiness["consumer_id"],
                    "callable_path": readiness["callable_path"],
                    "callable_signature": str(signature),
                    "attested_at": attested_at.isoformat(),
                }
            )

            body = {
                "sequence": sequence,
                "resolution_attestation_id": attestation_id,
                "consumer_id": readiness["consumer_id"],
                "consumer_module": readiness["consumer_module"],
                "consumer_class": readiness["consumer_class"],
                "callable_name": readiness["callable_name"],
                "callable_path": readiness["callable_path"],
                "source_resolution_readiness_id": readiness[
                    "resolution_readiness_id"
                ],
                "source_resolution_readiness_record_hash": readiness[
                    "resolution_readiness_record_hash"
                ],
                "source_binding_contract_id": readiness[
                    "source_binding_contract_id"
                ],
                "source_binding_contract_hash": readiness[
                    "source_binding_contract_hash"
                ],
                "source_activation_id": readiness[
                    "source_activation_id"
                ],
                "source_activation_nonce": readiness[
                    "source_activation_nonce"
                ],
                "source_boundary_id": readiness["source_boundary_id"],
                "source_boundary_hash": readiness[
                    "source_boundary_hash"
                ],
                "module_imported": True,
                "class_resolved": True,
                "callable_resolved": True,
                "callable_is_callable": True,
                "callable_is_coroutine": callable_is_coroutine,
                "callable_signature": str(signature),
                "callable_parameter_names": parameter_names,
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
            attestations.append(
                DownstreamReadOnlyConsumerCallableResolutionAttestationRecord(
                    **body,
                    resolution_attestation_record_hash=stable_hash(body),
                )
            )

        manifest_id = stable_hash(
            {
                "source_resolution_readiness_manifest_id": source[
                    "resolution_readiness_manifest_id"
                ],
                "source_resolution_readiness_manifest_hash": source[
                    "resolution_readiness_manifest_hash"
                ],
                "attested_at": attested_at.isoformat(),
                "attestation_record_hashes": [
                    record.resolution_attestation_record_hash
                    for record in attestations
                ],
            }
        )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "attested_at": attested_at.isoformat(),
            "resolution_attestation_manifest_id": manifest_id,
            "resolution_attestation_status": STATUS_RESOLVED,
            "resolution_attestation_policy_id": POLICY_ID,
            "source_resolution_readiness_manifest_id": source[
                "resolution_readiness_manifest_id"
            ],
            "source_resolution_readiness_manifest_hash": source[
                "resolution_readiness_manifest_hash"
            ],
            "source_binding_manifest_id": source[
                "source_binding_manifest_id"
            ],
            "source_boundary_id": source["source_boundary_id"],
            "source_boundary_hash": source["source_boundary_hash"],
            "attestation_record_count": len(attestations),
            "attestation_records": tuple(attestations),
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

        serializable = dict(body)
        serializable["attestation_records"] = [
            asdict(record) for record in attestations
        ]
        manifest_hash = stable_hash(serializable)

        manifest = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionAttestationManifest(
            **body,
            resolution_attestation_manifest_hash=manifest_hash,
        )

        if persist:
            payload = asdict(manifest)
            _atomic_write(
                self.attestation_directory / "current.json",
                payload,
            )
            _atomic_write(
                self.attestation_directory
                / "manifests"
                / f"{manifest_id}.json",
                payload,
            )
            for record in attestations:
                _atomic_write(
                    self.attestation_directory
                    / "consumers"
                    / record.consumer_id
                    / f"{record.resolution_attestation_id}.json",
                    asdict(record),
                )

        return manifest
