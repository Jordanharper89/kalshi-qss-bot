from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = "INT-OIA-002"
ENGINE_ID = "INT-OIA-002"
POLICY_ID = "oracle.intelligence.analytics.downstream-read-only-consumer-admission.v1"
STATUS_ADMITTED = "downstream_read_only_consumers_admitted"

DEFAULT_INTEGRATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_full_subsystem_completion_integration"
)
DEFAULT_ADMISSION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_admission"
)

ALLOWED_CAPABILITIES = frozenset(
    {
        "read_certified_oia_boundary",
        "read_certified_invocation_results",
        "read_certified_result_summaries",
        "perform_read_only_research_analysis",
        "persist_research_analysis_artifacts",
    }
)

FORBIDDEN_CAPABILITIES = frozenset(
    {
        "generate_signal",
        "generate_alert",
        "handoff_to_qseries",
        "invoke_qseries_execution",
        "create_order",
        "submit_order",
        "cancel_order",
        "move_funds",
        "mutate_portfolio",
        "mutate_source_corpus",
        "write_to_source_corpus",
    }
)


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerAdmissionInvariantError(
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
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerAdmissionInvariantError(
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
        raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerAdmissionInvariantError(
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
class DownstreamReadOnlyConsumerDeclaration:
    consumer_id: str
    consumer_module: str
    consumer_class: str
    requested_capabilities: tuple[str, ...]
    source_boundary_id: str
    read_only: bool = True
    execution_allowed: bool = False
    signals_allowed: bool = False
    alerts_allowed: bool = False
    qseries_handoff_allowed: bool = False
    order_creation_allowed: bool = False
    funds_movement_allowed: bool = False
    portfolio_mutation_allowed: bool = False
    source_mutation_allowed: bool = False


@dataclass(frozen=True)
class DownstreamReadOnlyConsumerAdmissionRecord:
    sequence: int
    consumer_id: str
    consumer_module: str
    consumer_class: str
    requested_capabilities: tuple[str, ...]
    source_boundary_id: str
    source_boundary_hash: str
    read_only: bool
    execution_allowed: bool
    signals_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    source_mutation_allowed: bool
    admitted: bool
    admission_status: str
    admission_record_hash: str


@dataclass(frozen=True)
class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerAdmissionManifest:
    schema_version: str
    engine_id: str
    admitted_at: str
    admission_manifest_id: str
    admission_status: str
    admission_policy_id: str
    source_integration_certification_id: str
    source_integration_certification_manifest_hash: str
    source_boundary_id: str
    source_boundary_hash: str
    admission_record_count: int
    admission_records: tuple[DownstreamReadOnlyConsumerAdmissionRecord, ...]
    all_consumers_read_only: bool
    all_capabilities_allowlisted: bool
    duplicate_consumers_rejected: bool
    source_boundary_consumed_without_reexecution: bool
    controlled_read_execution_repeated: bool
    corpus_read_execution_repeated: bool
    source_mutation_allowed: bool
    source_mutation_performed: bool
    analytic_conclusion_allowed: bool
    forecast_creation_allowed: bool
    signals_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    trading_recommendations_allowed: bool
    market_order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    downstream_read_only_research_allowed: bool
    admission_artifact_persistence_allowed: bool
    admission_manifest_hash: str


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerAdmissionGate:
    def __init__(
        self,
        *,
        integration_directory: Path | str = DEFAULT_INTEGRATION_DIRECTORY,
        admission_directory: Path | str = DEFAULT_ADMISSION_DIRECTORY,
    ) -> None:
        self.integration_directory = Path(integration_directory)
        self.admission_directory = Path(admission_directory)

    def _load_integration(self) -> dict[str, Any]:
        path = self.integration_directory / "current.json"
        if not path.exists():
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerAdmissionInvariantError(
                f"INT-OIA-001 integration artifact missing: {path}"
            )

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerAdmissionInvariantError(
                "INT-OIA-001 integration artifact could not be decoded"
            ) from exc

        manifest_hash = payload.pop(
            "integration_certification_manifest_hash",
            None,
        )
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerAdmissionInvariantError(
                "INT-OIA-001 integration manifest hash mismatch"
            )
        payload["integration_certification_manifest_hash"] = manifest_hash

        required = {
            "schema_version": "INT-OIA-001",
            "engine_id": "INT-OIA-001",
            "oia_001_through_oia_067_complete": True,
            "actual_oia_067_contract_consumed": True,
            "controlled_read_only_execution_completed": True,
            "source_invocation_reexecuted": False,
            "owner_reconstruction_performed": False,
            "callable_binding_performed": False,
            "callable_invocation_performed": False,
            "adapter_execution_performed": False,
            "corpus_read_execution_performed": False,
            "source_mutation_allowed": False,
            "source_mutation_performed": False,
            "signals_allowed": False,
            "alerts_allowed": False,
            "qseries_handoff_allowed": False,
            "qseries_execution_allowed": False,
            "market_order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
            "downstream_read_only_consumption_allowed": True,
            "oia_subsystem_frozen": True,
            "integration_artifact_persistence_allowed": True,
        }
        for field, expected in required.items():
            if payload.get(field) != expected:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerAdmissionInvariantError(
                    f"unsafe or incomplete INT-OIA-001 field: {field}"
                )

        boundary = payload.get("subsystem_boundary")
        if not isinstance(boundary, dict):
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerAdmissionInvariantError(
                "INT-OIA-001 subsystem boundary missing"
            )

        boundary_hash = boundary.pop("boundary_hash", None)
        if not _valid_hash(boundary_hash) or stable_hash(boundary) != boundary_hash:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerAdmissionInvariantError(
                "INT-OIA-001 boundary hash mismatch"
            )
        boundary["boundary_hash"] = boundary_hash

        required_boundary = {
            "subsystem_id": "OIA",
            "first_module_id": "OIA-001",
            "final_module_id": "OIA-067",
            "module_count": 67,
            "complete_lineage_verified": True,
            "controlled_read_execution_verified": True,
            "completion_attestation_verified": True,
            "read_only_boundary_frozen": True,
            "downstream_consumer_authorized": True,
            "source_reexecution_performed": False,
            "corpus_read_performed": False,
            "signal_generation_allowed": False,
            "qseries_execution_allowed": False,
            "order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
        }
        for field, expected in required_boundary.items():
            if boundary.get(field) != expected:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerAdmissionInvariantError(
                    f"unsafe or incomplete INT-OIA-001 boundary field: {field}"
                )

        payload["subsystem_boundary"] = boundary
        return payload

    def admit(
        self,
        *,
        consumers: Sequence[DownstreamReadOnlyConsumerDeclaration],
        admitted_at: datetime,
        persist: bool = True,
    ) -> OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerAdmissionManifest:
        admitted_at = _aware(admitted_at, "admitted_at")
        source = self._load_integration()

        if not consumers:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerAdmissionInvariantError(
                "at least one downstream consumer declaration is required"
            )

        boundary = source["subsystem_boundary"]
        source_boundary_id = boundary["boundary_id"]
        source_boundary_hash = boundary["boundary_hash"]

        seen_consumer_ids: set[str] = set()
        records: list[DownstreamReadOnlyConsumerAdmissionRecord] = []

        for sequence, consumer in enumerate(consumers, start=1):
            if not isinstance(consumer, DownstreamReadOnlyConsumerDeclaration):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerAdmissionInvariantError(
                    "consumer must be a DownstreamReadOnlyConsumerDeclaration"
                )
            if not consumer.consumer_id.strip():
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerAdmissionInvariantError(
                    "consumer_id must be non-empty"
                )
            if consumer.consumer_id in seen_consumer_ids:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerAdmissionInvariantError(
                    "duplicate downstream consumer_id"
                )
            seen_consumer_ids.add(consumer.consumer_id)

            if not consumer.consumer_module.strip() or not consumer.consumer_class.strip():
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerAdmissionInvariantError(
                    "consumer module and class must be non-empty"
                )
            if consumer.source_boundary_id != source_boundary_id:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerAdmissionInvariantError(
                    "consumer source boundary does not match INT-OIA-001"
                )

            capabilities = tuple(sorted(set(consumer.requested_capabilities)))
            if not capabilities:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerAdmissionInvariantError(
                    "consumer must request at least one allowlisted capability"
                )
            if any(capability in FORBIDDEN_CAPABILITIES for capability in capabilities):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerAdmissionInvariantError(
                    "consumer requested a forbidden capability"
                )
            if any(capability not in ALLOWED_CAPABILITIES for capability in capabilities):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerAdmissionInvariantError(
                    "consumer requested an unknown capability"
                )

            safety_values = {
                "read_only": consumer.read_only,
                "execution_allowed": consumer.execution_allowed,
                "signals_allowed": consumer.signals_allowed,
                "alerts_allowed": consumer.alerts_allowed,
                "qseries_handoff_allowed": consumer.qseries_handoff_allowed,
                "order_creation_allowed": consumer.order_creation_allowed,
                "funds_movement_allowed": consumer.funds_movement_allowed,
                "portfolio_mutation_allowed": consumer.portfolio_mutation_allowed,
                "source_mutation_allowed": consumer.source_mutation_allowed,
            }
            if safety_values != {
                "read_only": True,
                "execution_allowed": False,
                "signals_allowed": False,
                "alerts_allowed": False,
                "qseries_handoff_allowed": False,
                "order_creation_allowed": False,
                "funds_movement_allowed": False,
                "portfolio_mutation_allowed": False,
                "source_mutation_allowed": False,
            }:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerAdmissionInvariantError(
                    "consumer declaration violates read-only safety policy"
                )

            record_body = {
                "sequence": sequence,
                "consumer_id": consumer.consumer_id,
                "consumer_module": consumer.consumer_module,
                "consumer_class": consumer.consumer_class,
                "requested_capabilities": capabilities,
                "source_boundary_id": source_boundary_id,
                "source_boundary_hash": source_boundary_hash,
                "read_only": True,
                "execution_allowed": False,
                "signals_allowed": False,
                "alerts_allowed": False,
                "qseries_handoff_allowed": False,
                "order_creation_allowed": False,
                "funds_movement_allowed": False,
                "portfolio_mutation_allowed": False,
                "source_mutation_allowed": False,
                "admitted": True,
                "admission_status": "admitted_read_only",
            }
            records.append(
                DownstreamReadOnlyConsumerAdmissionRecord(
                    **record_body,
                    admission_record_hash=stable_hash(record_body),
                )
            )

        identity = {
            "source_integration_certification_id": source[
                "integration_certification_id"
            ],
            "source_integration_certification_manifest_hash": source[
                "integration_certification_manifest_hash"
            ],
            "source_boundary_id": source_boundary_id,
            "source_boundary_hash": source_boundary_hash,
            "admitted_at": admitted_at.isoformat(),
            "admission_record_hashes": [
                record.admission_record_hash for record in records
            ],
        }
        manifest_id = stable_hash(identity)

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "admitted_at": admitted_at.isoformat(),
            "admission_manifest_id": manifest_id,
            "admission_status": STATUS_ADMITTED,
            "admission_policy_id": POLICY_ID,
            "source_integration_certification_id": source[
                "integration_certification_id"
            ],
            "source_integration_certification_manifest_hash": source[
                "integration_certification_manifest_hash"
            ],
            "source_boundary_id": source_boundary_id,
            "source_boundary_hash": source_boundary_hash,
            "admission_record_count": len(records),
            "admission_records": tuple(records),
            "all_consumers_read_only": True,
            "all_capabilities_allowlisted": True,
            "duplicate_consumers_rejected": True,
            "source_boundary_consumed_without_reexecution": True,
            "controlled_read_execution_repeated": False,
            "corpus_read_execution_repeated": False,
            "source_mutation_allowed": False,
            "source_mutation_performed": False,
            "analytic_conclusion_allowed": True,
            "forecast_creation_allowed": False,
            "signals_allowed": False,
            "alerts_allowed": False,
            "qseries_handoff_allowed": False,
            "qseries_execution_allowed": False,
            "trading_recommendations_allowed": False,
            "market_order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
            "downstream_read_only_research_allowed": True,
            "admission_artifact_persistence_allowed": True,
        }

        serializable = dict(body)
        serializable["admission_records"] = [asdict(record) for record in records]
        manifest_hash = stable_hash(serializable)

        manifest = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerAdmissionManifest(
            **body,
            admission_manifest_hash=manifest_hash,
        )

        if persist:
            payload = asdict(manifest)
            _atomic_write(self.admission_directory / "current.json", payload)
            _atomic_write(
                self.admission_directory
                / "manifests"
                / f"{manifest_id}.json",
                payload,
            )
            for record in records:
                _atomic_write(
                    self.admission_directory
                    / "consumers"
                    / record.consumer_id
                    / f"{manifest_id}.json",
                    payload,
                )

        return manifest
