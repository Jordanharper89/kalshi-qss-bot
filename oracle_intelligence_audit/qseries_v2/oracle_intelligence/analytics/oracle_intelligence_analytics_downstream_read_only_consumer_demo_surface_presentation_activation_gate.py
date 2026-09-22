from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "INT-OIA-034"
ENGINE_ID = "INT-OIA-034"
POLICY_ID = (
    "oracle.intelligence.analytics.downstream-read-only-consumer."
    "demo-surface-presentation-activation.v1"
)
STATUS_ACTIVATED = "demo_surface_presentation_activated"

DEFAULT_READINESS_ATTESTATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_demo_surface_presentation_readiness_attestation"
)
DEFAULT_PRESENTATION_ACTIVATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_demo_surface_presentation_activation"
)

APPROVED_PRESENTATION_MODE = "immutable_read_only_demo_surface_presentation"
APPROVED_PRESENTATION_SCOPE = "independently_attested_serving_consumption_only"
APPROVED_ACTIVATION_MODE = "single_use_immutable_read_only_presentation_activation"


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationActivationInvariantError(
    RuntimeError
):
    pass


def stable_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
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
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationActivationInvariantError(
            f"{field} must be timezone-aware"
        )
    return value.astimezone(timezone.utc)


def _atomic_write(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
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
class DemoSurfacePresentationActivationRecord:
    sequence: int
    activation_id: str
    readiness_attestation_id: str
    readiness_id: str
    serving_consumption_attestation_id: str
    serving_consumption_id: str
    serving_release_id: str
    publication_id: str
    consumer_id: str
    source_readiness_attestation_record_hash: str
    source_readiness_record_hash: str
    source_serving_consumption_attestation_record_hash: str
    source_serving_consumption_record_hash: str
    source_serving_release_attestation_record_hash: str
    source_serving_release_record_hash: str
    source_publication_record_hash: str
    publication_payload_hash: str
    source_boundary_id: str
    source_boundary_hash: str
    result_hash: str
    admitted_result_hash: str
    presentation_mode: str
    presentation_scope: str
    activation_mode: str
    readiness_attestation_record_hash_verified: bool
    readiness_record_hash_verified: bool
    serving_consumption_attestation_record_hash_verified: bool
    serving_consumption_record_hash_verified: bool
    serving_release_attestation_record_hash_verified: bool
    serving_release_record_hash_verified: bool
    publication_record_hash_verified: bool
    publication_payload_hash_verified: bool
    admission_lineage_verified: bool
    one_time_invocation_verified: bool
    immutable_result_verified: bool
    read_only_boundary_verified: bool
    execution_disabled_boundary_verified: bool
    presentation_readiness_attestation_verified: bool
    activation_scope_verified: bool
    single_use_activation_verified: bool
    presentation_activated: bool
    duplicate_activation_rejected: bool
    signals_created: bool
    alerts_created: bool
    qseries_handoff_performed: bool
    qseries_execution_performed: bool
    market_order_creation_performed: bool
    funds_movement_performed: bool
    portfolio_mutation_performed: bool
    source_mutation_performed: bool
    activation_status: str
    activation_record_hash: str


@dataclass(frozen=True)
class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationActivation:
    schema_version: str
    engine_id: str
    activated_at: str
    activation_manifest_id: str
    activation_status: str
    activation_policy_id: str
    activation_mode: str
    presentation_mode: str
    presentation_scope: str
    source_readiness_attestation_manifest_id: str
    source_readiness_attestation_manifest_hash: str
    source_presentation_readiness_manifest_id: str
    source_presentation_readiness_manifest_hash: str
    source_serving_consumption_attestation_manifest_id: str
    source_serving_consumption_attestation_manifest_hash: str
    source_serving_consumption_manifest_id: str
    source_serving_consumption_manifest_hash: str
    source_serving_release_attestation_manifest_id: str
    source_serving_release_attestation_manifest_hash: str
    source_serving_release_manifest_id: str
    source_serving_release_manifest_hash: str
    source_publication_manifest_id: str
    source_publication_manifest_hash: str
    source_boundary_id: str
    source_boundary_hash: str
    activation_record_count: int
    activation_records: tuple[DemoSurfacePresentationActivationRecord, ...]
    all_readiness_attestation_record_hashes_verified: bool
    all_readiness_record_hashes_verified: bool
    all_serving_consumption_attestation_record_hashes_verified: bool
    all_serving_consumption_record_hashes_verified: bool
    all_serving_release_attestation_record_hashes_verified: bool
    all_serving_release_record_hashes_verified: bool
    all_publication_record_hashes_verified: bool
    all_publication_payload_hashes_verified: bool
    all_admission_lineage_verified: bool
    all_one_time_invocations_verified: bool
    all_results_immutable: bool
    all_read_only_boundaries_verified: bool
    all_execution_disabled_boundaries_verified: bool
    all_presentation_readiness_attestations_verified: bool
    all_activation_scopes_verified: bool
    all_single_use_activations_verified: bool
    all_demo_surface_presentations_activated: bool
    duplicate_activations_rejected: bool
    source_boundary_consumed_without_reexecution: bool
    invocation_reexecution_performed: bool
    database_connection_performed: bool
    corpus_read_execution_repeated: bool
    source_mutation_allowed: bool
    source_mutation_performed: bool
    analytic_conclusion_allowed: bool
    demo_surface_publication_serving_release_consumed: bool
    demo_surface_publication_serving_consumption_attested: bool
    demo_surface_presentation_ready: bool
    demo_surface_presentation_readiness_attested: bool
    demo_surface_presentation_activated: bool
    forecast_creation_allowed: bool
    signals_allowed: bool
    signals_created: bool
    alerts_allowed: bool
    alerts_created: bool
    qseries_handoff_allowed: bool
    qseries_handoff_performed: bool
    qseries_execution_allowed: bool
    qseries_execution_performed: bool
    market_order_creation_allowed: bool
    market_order_creation_performed: bool
    funds_movement_allowed: bool
    funds_movement_performed: bool
    portfolio_mutation_allowed: bool
    portfolio_mutation_performed: bool
    activation_artifact_persistence_allowed: bool
    activation_manifest_hash: str


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationActivationGate:
    def __init__(
        self,
        *,
        readiness_attestation_directory: Path | str = DEFAULT_READINESS_ATTESTATION_DIRECTORY,
        activation_directory: Path | str = DEFAULT_PRESENTATION_ACTIVATION_DIRECTORY,
    ) -> None:
        self.readiness_attestation_directory = Path(readiness_attestation_directory)
        self.activation_directory = Path(activation_directory)

    def _load_attestation(self) -> dict[str, Any]:
        path = self.readiness_attestation_directory / "current.json"
        if not path.exists():
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationActivationInvariantError(
                f"INT-OIA-033 readiness-attestation manifest missing: {path}"
            )

        payload = json.loads(path.read_text(encoding="utf-8"))
        manifest_hash = payload.pop("attestation_manifest_hash", None)
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationActivationInvariantError(
                "INT-OIA-033 attestation manifest hash mismatch"
            )
        payload["attestation_manifest_hash"] = manifest_hash

        required = {
            "schema_version": "INT-OIA-033",
            "engine_id": "INT-OIA-033",
            "attestation_status": "demo_surface_presentation_readiness_independently_attested",
            "presentation_mode": APPROVED_PRESENTATION_MODE,
            "presentation_scope": APPROVED_PRESENTATION_SCOPE,
            "all_readiness_record_hashes_verified": True,
            "all_serving_consumption_attestation_record_hashes_verified": True,
            "all_serving_consumption_record_hashes_verified": True,
            "all_serving_release_attestation_record_hashes_verified": True,
            "all_serving_release_record_hashes_verified": True,
            "all_publication_record_hashes_verified": True,
            "all_publication_payload_hashes_verified": True,
            "all_admission_lineage_verified": True,
            "all_one_time_invocations_verified": True,
            "all_results_immutable": True,
            "all_read_only_boundaries_verified": True,
            "all_execution_disabled_boundaries_verified": True,
            "all_independent_serving_consumption_attestations_verified": True,
            "all_presentation_scopes_verified": True,
            "all_presentation_readiness_records_verified": True,
            "all_presentation_readiness_records_independently_attested": True,
            "duplicate_attestations_rejected": True,
            "source_boundary_consumed_without_reexecution": True,
            "invocation_reexecution_performed": False,
            "database_connection_performed": False,
            "corpus_read_execution_repeated": False,
            "source_mutation_allowed": False,
            "source_mutation_performed": False,
            "demo_surface_presentation_ready": True,
            "demo_surface_presentation_readiness_attested": True,
            "signals_allowed": False,
            "signals_created": False,
            "alerts_allowed": False,
            "alerts_created": False,
            "qseries_handoff_allowed": False,
            "qseries_handoff_performed": False,
            "qseries_execution_allowed": False,
            "qseries_execution_performed": False,
            "market_order_creation_allowed": False,
            "market_order_creation_performed": False,
            "funds_movement_allowed": False,
            "funds_movement_performed": False,
            "portfolio_mutation_allowed": False,
            "portfolio_mutation_performed": False,
            "attestation_artifact_persistence_allowed": True,
        }
        for field, expected in required.items():
            if payload.get(field) != expected:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationActivationInvariantError(
                    f"unsafe or incomplete INT-OIA-033 field: {field}"
                )

        records = payload.get("attestation_records")
        if not isinstance(records, list) or not records or payload.get("attestation_record_count") != len(records):
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationActivationInvariantError(
                "INT-OIA-033 attestation records invalid"
            )

        seen: set[str] = set()
        for sequence, raw in enumerate(records, start=1):
            record = dict(raw)
            record_hash = record.pop("attestation_record_hash", None)
            if not _valid_hash(record_hash) or stable_hash(record) != record_hash:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationActivationInvariantError(
                    "INT-OIA-033 attestation record hash mismatch"
                )
            record["attestation_record_hash"] = record_hash
            attestation_id = record.get("attestation_id")
            if (
                record.get("sequence") != sequence
                or not isinstance(attestation_id, str)
                or not attestation_id
                or attestation_id in seen
            ):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationActivationInvariantError(
                    "invalid sequence or duplicate readiness-attestation identity"
                )
            seen.add(attestation_id)

            record_required = {
                "presentation_mode": APPROVED_PRESENTATION_MODE,
                "presentation_scope": APPROVED_PRESENTATION_SCOPE,
                "readiness_record_hash_verified": True,
                "serving_consumption_attestation_record_hash_verified": True,
                "serving_consumption_record_hash_verified": True,
                "serving_release_attestation_record_hash_verified": True,
                "serving_release_record_hash_verified": True,
                "publication_record_hash_verified": True,
                "publication_payload_hash_verified": True,
                "admission_lineage_verified": True,
                "one_time_invocation_verified": True,
                "immutable_result_verified": True,
                "read_only_boundary_verified": True,
                "execution_disabled_boundary_verified": True,
                "independent_serving_consumption_attestation_verified": True,
                "presentation_scope_verified": True,
                "presentation_readiness_verified": True,
                "independent_presentation_readiness_attestation_performed": True,
                "duplicate_attestation_rejected": True,
                "signals_created": False,
                "alerts_created": False,
                "qseries_handoff_performed": False,
                "qseries_execution_performed": False,
                "market_order_creation_performed": False,
                "funds_movement_performed": False,
                "portfolio_mutation_performed": False,
                "source_mutation_performed": False,
                "attestation_status": "immutable_read_only_demo_surface_presentation_readiness_independently_attested",
            }
            for field, expected in record_required.items():
                if record.get(field) != expected:
                    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationActivationInvariantError(
                        f"unsafe INT-OIA-033 attestation-record field: {field}"
                    )

        return payload

    def activate(
        self,
        *,
        activated_at: datetime,
        persist: bool = True,
    ) -> OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationActivation:
        activated_at = _aware(activated_at, "activated_at")
        source = self._load_attestation()
        records: list[DemoSurfacePresentationActivationRecord] = []
        seen: set[str] = set()

        for sequence, attestation in enumerate(source["attestation_records"], start=1):
            activation_id = stable_hash(
                {
                    "source_manifest_id": source["attestation_manifest_id"],
                    "source_record_hash": attestation["attestation_record_hash"],
                    "activation_mode": APPROVED_ACTIVATION_MODE,
                    "activated_at": activated_at.isoformat(),
                }
            )
            if activation_id in seen:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationActivationInvariantError(
                    "duplicate presentation-activation identity"
                )
            seen.add(activation_id)

            body = {
                "sequence": sequence,
                "activation_id": activation_id,
                "readiness_attestation_id": attestation["attestation_id"],
                "readiness_id": attestation["readiness_id"],
                "serving_consumption_attestation_id": attestation["serving_consumption_attestation_id"],
                "serving_consumption_id": attestation["serving_consumption_id"],
                "serving_release_id": attestation["serving_release_id"],
                "publication_id": attestation["publication_id"],
                "consumer_id": attestation["consumer_id"],
                "source_readiness_attestation_record_hash": attestation["attestation_record_hash"],
                "source_readiness_record_hash": attestation["source_readiness_record_hash"],
                "source_serving_consumption_attestation_record_hash": attestation["source_serving_consumption_attestation_record_hash"],
                "source_serving_consumption_record_hash": attestation["source_serving_consumption_record_hash"],
                "source_serving_release_attestation_record_hash": attestation["source_serving_release_attestation_record_hash"],
                "source_serving_release_record_hash": attestation["source_serving_release_record_hash"],
                "source_publication_record_hash": attestation["source_publication_record_hash"],
                "publication_payload_hash": attestation["publication_payload_hash"],
                "source_boundary_id": attestation["source_boundary_id"],
                "source_boundary_hash": attestation["source_boundary_hash"],
                "result_hash": attestation["result_hash"],
                "admitted_result_hash": attestation["admitted_result_hash"],
                "presentation_mode": APPROVED_PRESENTATION_MODE,
                "presentation_scope": APPROVED_PRESENTATION_SCOPE,
                "activation_mode": APPROVED_ACTIVATION_MODE,
                "readiness_attestation_record_hash_verified": True,
                "readiness_record_hash_verified": True,
                "serving_consumption_attestation_record_hash_verified": True,
                "serving_consumption_record_hash_verified": True,
                "serving_release_attestation_record_hash_verified": True,
                "serving_release_record_hash_verified": True,
                "publication_record_hash_verified": True,
                "publication_payload_hash_verified": True,
                "admission_lineage_verified": True,
                "one_time_invocation_verified": True,
                "immutable_result_verified": True,
                "read_only_boundary_verified": True,
                "execution_disabled_boundary_verified": True,
                "presentation_readiness_attestation_verified": True,
                "activation_scope_verified": True,
                "single_use_activation_verified": True,
                "presentation_activated": True,
                "duplicate_activation_rejected": True,
                "signals_created": False,
                "alerts_created": False,
                "qseries_handoff_performed": False,
                "qseries_execution_performed": False,
                "market_order_creation_performed": False,
                "funds_movement_performed": False,
                "portfolio_mutation_performed": False,
                "source_mutation_performed": False,
                "activation_status": "immutable_read_only_demo_surface_presentation_activated",
            }
            records.append(
                DemoSurfacePresentationActivationRecord(
                    **body,
                    activation_record_hash=stable_hash(body),
                )
            )

        manifest_id = stable_hash(
            {
                "source_manifest_id": source["attestation_manifest_id"],
                "source_manifest_hash": source["attestation_manifest_hash"],
                "activated_at": activated_at.isoformat(),
                "record_hashes": [record.activation_record_hash for record in records],
            }
        )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "activated_at": activated_at.isoformat(),
            "activation_manifest_id": manifest_id,
            "activation_status": STATUS_ACTIVATED,
            "activation_policy_id": POLICY_ID,
            "activation_mode": APPROVED_ACTIVATION_MODE,
            "presentation_mode": APPROVED_PRESENTATION_MODE,
            "presentation_scope": APPROVED_PRESENTATION_SCOPE,
            "source_readiness_attestation_manifest_id": source["attestation_manifest_id"],
            "source_readiness_attestation_manifest_hash": source["attestation_manifest_hash"],
            "source_presentation_readiness_manifest_id": source["source_presentation_readiness_manifest_id"],
            "source_presentation_readiness_manifest_hash": source["source_presentation_readiness_manifest_hash"],
            "source_serving_consumption_attestation_manifest_id": source["source_serving_consumption_attestation_manifest_id"],
            "source_serving_consumption_attestation_manifest_hash": source["source_serving_consumption_attestation_manifest_hash"],
            "source_serving_consumption_manifest_id": source["source_serving_consumption_manifest_id"],
            "source_serving_consumption_manifest_hash": source["source_serving_consumption_manifest_hash"],
            "source_serving_release_attestation_manifest_id": source["source_serving_release_attestation_manifest_id"],
            "source_serving_release_attestation_manifest_hash": source["source_serving_release_attestation_manifest_hash"],
            "source_serving_release_manifest_id": source["source_serving_release_manifest_id"],
            "source_serving_release_manifest_hash": source["source_serving_release_manifest_hash"],
            "source_publication_manifest_id": source["source_publication_manifest_id"],
            "source_publication_manifest_hash": source["source_publication_manifest_hash"],
            "source_boundary_id": source["source_boundary_id"],
            "source_boundary_hash": source["source_boundary_hash"],
            "activation_record_count": len(records),
            "activation_records": tuple(records),
            "all_readiness_attestation_record_hashes_verified": True,
            "all_readiness_record_hashes_verified": True,
            "all_serving_consumption_attestation_record_hashes_verified": True,
            "all_serving_consumption_record_hashes_verified": True,
            "all_serving_release_attestation_record_hashes_verified": True,
            "all_serving_release_record_hashes_verified": True,
            "all_publication_record_hashes_verified": True,
            "all_publication_payload_hashes_verified": True,
            "all_admission_lineage_verified": True,
            "all_one_time_invocations_verified": True,
            "all_results_immutable": True,
            "all_read_only_boundaries_verified": True,
            "all_execution_disabled_boundaries_verified": True,
            "all_presentation_readiness_attestations_verified": True,
            "all_activation_scopes_verified": True,
            "all_single_use_activations_verified": True,
            "all_demo_surface_presentations_activated": True,
            "duplicate_activations_rejected": True,
            "source_boundary_consumed_without_reexecution": True,
            "invocation_reexecution_performed": False,
            "database_connection_performed": False,
            "corpus_read_execution_repeated": False,
            "source_mutation_allowed": False,
            "source_mutation_performed": False,
            "analytic_conclusion_allowed": True,
            "demo_surface_publication_serving_release_consumed": True,
            "demo_surface_publication_serving_consumption_attested": True,
            "demo_surface_presentation_ready": True,
            "demo_surface_presentation_readiness_attested": True,
            "demo_surface_presentation_activated": True,
            "forecast_creation_allowed": False,
            "signals_allowed": False,
            "signals_created": False,
            "alerts_allowed": False,
            "alerts_created": False,
            "qseries_handoff_allowed": False,
            "qseries_handoff_performed": False,
            "qseries_execution_allowed": False,
            "qseries_execution_performed": False,
            "market_order_creation_allowed": False,
            "market_order_creation_performed": False,
            "funds_movement_allowed": False,
            "funds_movement_performed": False,
            "portfolio_mutation_allowed": False,
            "portfolio_mutation_performed": False,
            "activation_artifact_persistence_allowed": True,
        }

        serializable = dict(body)
        serializable["activation_records"] = [asdict(record) for record in records]
        manifest = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationActivation(
            **body,
            activation_manifest_hash=stable_hash(serializable),
        )

        if persist:
            payload = asdict(manifest)
            _atomic_write(self.activation_directory / "current.json", payload)
            _atomic_write(
                self.activation_directory / "manifests" / f"{manifest_id}.json",
                payload,
            )
            for record in records:
                _atomic_write(
                    self.activation_directory / "publications" / record.publication_id / f"{record.activation_id}.json",
                    asdict(record),
                )

        return manifest
