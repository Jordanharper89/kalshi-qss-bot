from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "INT-OIA-031"
ENGINE_ID = "INT-OIA-031"
STATUS_ATTESTED = "demo_surface_publication_serving_consumption_independently_attested"
POLICY_ID = (
    "oracle.intelligence.analytics.downstream-read-only-consumer."
    "demo-surface-publication-serving-consumption-independent-attestation.v1"
)

DEFAULT_CONSUMPTION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_demo_surface_publication_serving_consumption"
)
DEFAULT_ATTESTATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_demo_surface_publication_serving_consumption_attestation"
)

APPROVED_PUBLICATION_SCHEMA = "oracle_research_demo_publication_manifest.v1"
APPROVED_PUBLICATION_MODE = "immutable_read_only_demo_publication"
APPROVED_SERVING_CONSUMPTION_MODE = "single_use_read_only_serving_release_consumption"
APPROVED_SERVING_CONSUMPTION_SCOPE = "independently_attested_serving_release_only"


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionAttestationInvariantError(RuntimeError):
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
        raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionAttestationInvariantError(
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
class DemoSurfacePublicationServingConsumptionAttestationRecord:
    sequence: int
    attestation_id: str
    serving_consumption_id: str
    serving_release_attestation_id: str
    serving_release_id: str
    serving_authorization_attestation_id: str
    serving_authorization_id: str
    publication_id: str
    consumer_id: str
    source_serving_consumption_record_hash: str
    source_serving_release_attestation_record_hash: str
    source_serving_release_record_hash: str
    source_publication_record_hash: str
    publication_payload_hash: str
    source_boundary_id: str
    source_boundary_hash: str
    result_hash: str
    admitted_result_hash: str
    publication_schema: str
    publication_mode: str
    serving_consumption_mode: str
    serving_consumption_scope: str
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
    independent_serving_release_attestation_verified: bool
    serving_consumption_scope_verified: bool
    single_use_consumption_verified: bool
    serving_consumption_verified: bool
    duplicate_attestation_rejected: bool
    independent_serving_consumption_attestation_performed: bool
    signals_created: bool
    alerts_created: bool
    qseries_handoff_performed: bool
    qseries_execution_performed: bool
    market_order_creation_performed: bool
    funds_movement_performed: bool
    portfolio_mutation_performed: bool
    source_mutation_performed: bool
    attestation_status: str
    attestation_record_hash: str


@dataclass(frozen=True)
class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionAttestation:
    schema_version: str
    engine_id: str
    attested_at: str
    attestation_manifest_id: str
    attestation_status: str
    attestation_policy_id: str
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
    attestation_record_count: int
    attestation_records: tuple[DemoSurfacePublicationServingConsumptionAttestationRecord, ...]
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
    all_independent_serving_release_attestations_verified: bool
    all_serving_consumption_scopes_verified: bool
    all_single_use_consumptions_verified: bool
    all_serving_consumptions_verified: bool
    all_serving_consumptions_independently_attested: bool
    duplicate_attestations_rejected: bool
    source_boundary_consumed_without_reexecution: bool
    invocation_reexecution_performed: bool
    database_connection_performed: bool
    corpus_read_execution_repeated: bool
    source_mutation_allowed: bool
    source_mutation_performed: bool
    analytic_conclusion_allowed: bool
    demo_surface_publication_serving_release_consumed: bool
    demo_surface_publication_serving_consumption_attested: bool
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
    attestation_artifact_persistence_allowed: bool
    attestation_manifest_hash: str


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionAttestationGate:
    def __init__(
        self,
        *,
        consumption_directory: Path | str = DEFAULT_CONSUMPTION_DIRECTORY,
        attestation_directory: Path | str = DEFAULT_ATTESTATION_DIRECTORY,
    ) -> None:
        self.consumption_directory = Path(consumption_directory)
        self.attestation_directory = Path(attestation_directory)

    def _load_consumption(self) -> dict[str, Any]:
        path = self.consumption_directory / "current.json"
        if not path.exists():
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionAttestationInvariantError(
                f"INT-OIA-030 serving-consumption manifest missing: {path}"
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionAttestationInvariantError(
                "INT-OIA-030 serving-consumption manifest could not be decoded"
            ) from exc

        manifest_hash = payload.pop("consumption_manifest_hash", None)
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionAttestationInvariantError(
                "INT-OIA-030 consumption manifest hash mismatch"
            )
        payload["consumption_manifest_hash"] = manifest_hash

        required = {
            "schema_version": "INT-OIA-030",
            "engine_id": "INT-OIA-030",
            "consumption_status": "demo_surface_publication_serving_release_consumed",
            "serving_consumption_mode": APPROVED_SERVING_CONSUMPTION_MODE,
            "serving_consumption_scope": APPROVED_SERVING_CONSUMPTION_SCOPE,
            "all_serving_release_attestation_record_hashes_verified": True,
            "all_serving_release_record_hashes_verified": True,
            "all_publication_record_hashes_verified": True,
            "all_publication_payload_hashes_verified": True,
            "all_admission_lineage_verified": True,
            "all_one_time_invocations_verified": True,
            "all_results_immutable": True,
            "all_read_only_boundaries_verified": True,
            "all_execution_disabled_boundaries_verified": True,
            "all_independent_serving_release_attestations_verified": True,
            "all_serving_consumption_scopes_verified": True,
            "all_single_use_consumptions_verified": True,
            "all_demo_surface_publication_serving_releases_consumed": True,
            "duplicate_consumptions_rejected": True,
            "source_boundary_consumed_without_reexecution": True,
            "invocation_reexecution_performed": False,
            "database_connection_performed": False,
            "corpus_read_execution_repeated": False,
            "source_mutation_allowed": False,
            "source_mutation_performed": False,
            "demo_surface_publication_serving_release_consumed": True,
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
            "consumption_artifact_persistence_allowed": True,
        }
        for field, expected in required.items():
            if payload.get(field) != expected:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionAttestationInvariantError(
                    f"unsafe or incomplete INT-OIA-030 field: {field}"
                )

        records = payload.get("consumption_records")
        if not isinstance(records, list) or not records or payload.get("consumption_record_count") != len(records):
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionAttestationInvariantError(
                "INT-OIA-030 consumption records invalid"
            )

        seen: set[str] = set()
        for sequence, raw in enumerate(records, start=1):
            if not isinstance(raw, Mapping):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionAttestationInvariantError(
                    "consumption record must be a mapping"
                )
            record = dict(raw)
            record_hash = record.pop("consumption_record_hash", None)
            if not _valid_hash(record_hash) or stable_hash(record) != record_hash:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionAttestationInvariantError(
                    "INT-OIA-030 consumption record hash mismatch"
                )
            record["consumption_record_hash"] = record_hash
            consumption_id = record.get("consumption_id")
            if record.get("sequence") != sequence or not isinstance(consumption_id, str) or not consumption_id or consumption_id in seen:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionAttestationInvariantError(
                    "invalid sequence or duplicate consumption identity"
                )
            seen.add(consumption_id)
            record_required = {
                "publication_schema": APPROVED_PUBLICATION_SCHEMA,
                "publication_mode": APPROVED_PUBLICATION_MODE,
                "serving_consumption_mode": APPROVED_SERVING_CONSUMPTION_MODE,
                "serving_consumption_scope": APPROVED_SERVING_CONSUMPTION_SCOPE,
                "serving_release_attestation_record_hash_verified": True,
                "serving_release_record_hash_verified": True,
                "publication_record_hash_verified": True,
                "publication_payload_hash_verified": True,
                "admission_lineage_verified": True,
                "one_time_invocation_verified": True,
                "immutable_result_verified": True,
                "read_only_boundary_verified": True,
                "execution_disabled_boundary_verified": True,
                "independent_serving_release_attestation_verified": True,
                "serving_consumption_scope_verified": True,
                "single_use_consumption_verified": True,
                "duplicate_consumption_rejected": True,
                "demo_surface_publication_serving_release_consumed": True,
                "signals_created": False,
                "alerts_created": False,
                "qseries_handoff_performed": False,
                "qseries_execution_performed": False,
                "market_order_creation_performed": False,
                "funds_movement_performed": False,
                "portfolio_mutation_performed": False,
                "source_mutation_performed": False,
                "consumption_status": "independently_attested_read_only_serving_release_consumed",
            }
            for field, expected in record_required.items():
                if record.get(field) != expected:
                    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionAttestationInvariantError(
                        f"unsafe INT-OIA-030 consumption-record field: {field}"
                    )
        return payload

    def attest(
        self,
        *,
        attested_at: datetime,
        persist: bool = True,
    ) -> OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionAttestation:
        attested_at = _aware(attested_at, "attested_at")
        source = self._load_consumption()
        records: list[DemoSurfacePublicationServingConsumptionAttestationRecord] = []
        seen: set[str] = set()

        for sequence, consumption in enumerate(source["consumption_records"], start=1):
            attestation_id = stable_hash(
                {
                    "source_manifest": source["consumption_manifest_id"],
                    "source_record": consumption["consumption_record_hash"],
                    "serving_consumption_id": consumption["consumption_id"],
                    "publication_id": consumption["publication_id"],
                    "consumer_id": consumption["consumer_id"],
                    "attested_at": attested_at.isoformat(),
                }
            )
            if attestation_id in seen:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionAttestationInvariantError(
                    "duplicate attestation identity"
                )
            seen.add(attestation_id)

            body = {
                "sequence": sequence,
                "attestation_id": attestation_id,
                "serving_consumption_id": consumption["consumption_id"],
                "serving_release_attestation_id": consumption["serving_release_attestation_id"],
                "serving_release_id": consumption["serving_release_id"],
                "serving_authorization_attestation_id": consumption["serving_authorization_attestation_id"],
                "serving_authorization_id": consumption["serving_authorization_id"],
                "publication_id": consumption["publication_id"],
                "consumer_id": consumption["consumer_id"],
                "source_serving_consumption_record_hash": consumption["consumption_record_hash"],
                "source_serving_release_attestation_record_hash": consumption["source_serving_release_attestation_record_hash"],
                "source_serving_release_record_hash": consumption["source_serving_release_record_hash"],
                "source_publication_record_hash": consumption["source_publication_record_hash"],
                "publication_payload_hash": consumption["publication_payload_hash"],
                "source_boundary_id": consumption["source_boundary_id"],
                "source_boundary_hash": consumption["source_boundary_hash"],
                "result_hash": consumption["result_hash"],
                "admitted_result_hash": consumption["admitted_result_hash"],
                "publication_schema": APPROVED_PUBLICATION_SCHEMA,
                "publication_mode": APPROVED_PUBLICATION_MODE,
                "serving_consumption_mode": APPROVED_SERVING_CONSUMPTION_MODE,
                "serving_consumption_scope": APPROVED_SERVING_CONSUMPTION_SCOPE,
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
                "independent_serving_release_attestation_verified": True,
                "serving_consumption_scope_verified": True,
                "single_use_consumption_verified": True,
                "serving_consumption_verified": True,
                "duplicate_attestation_rejected": True,
                "independent_serving_consumption_attestation_performed": True,
                "signals_created": False,
                "alerts_created": False,
                "qseries_handoff_performed": False,
                "qseries_execution_performed": False,
                "market_order_creation_performed": False,
                "funds_movement_performed": False,
                "portfolio_mutation_performed": False,
                "source_mutation_performed": False,
                "attestation_status": "read_only_demo_publication_serving_consumption_independently_attested",
            }
            records.append(
                DemoSurfacePublicationServingConsumptionAttestationRecord(
                    **body,
                    attestation_record_hash=stable_hash(body),
                )
            )

        manifest_id = stable_hash(
            {
                "source_manifest_id": source["consumption_manifest_id"],
                "source_manifest_hash": source["consumption_manifest_hash"],
                "attested_at": attested_at.isoformat(),
                "record_hashes": [record.attestation_record_hash for record in records],
            }
        )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "attested_at": attested_at.isoformat(),
            "attestation_manifest_id": manifest_id,
            "attestation_status": STATUS_ATTESTED,
            "attestation_policy_id": POLICY_ID,
            "source_serving_consumption_manifest_id": source["consumption_manifest_id"],
            "source_serving_consumption_manifest_hash": source["consumption_manifest_hash"],
            "source_serving_release_attestation_manifest_id": source["source_serving_release_attestation_manifest_id"],
            "source_serving_release_attestation_manifest_hash": source["source_serving_release_attestation_manifest_hash"],
            "source_serving_release_manifest_id": source["source_serving_release_manifest_id"],
            "source_serving_release_manifest_hash": source["source_serving_release_manifest_hash"],
            "source_publication_manifest_id": source["source_publication_manifest_id"],
            "source_publication_manifest_hash": source["source_publication_manifest_hash"],
            "source_boundary_id": source["source_boundary_id"],
            "source_boundary_hash": source["source_boundary_hash"],
            "attestation_record_count": len(records),
            "attestation_records": tuple(records),
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
            "all_independent_serving_release_attestations_verified": True,
            "all_serving_consumption_scopes_verified": True,
            "all_single_use_consumptions_verified": True,
            "all_serving_consumptions_verified": True,
            "all_serving_consumptions_independently_attested": True,
            "duplicate_attestations_rejected": True,
            "source_boundary_consumed_without_reexecution": True,
            "invocation_reexecution_performed": False,
            "database_connection_performed": False,
            "corpus_read_execution_repeated": False,
            "source_mutation_allowed": False,
            "source_mutation_performed": False,
            "analytic_conclusion_allowed": True,
            "demo_surface_publication_serving_release_consumed": True,
            "demo_surface_publication_serving_consumption_attested": True,
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
            "attestation_artifact_persistence_allowed": True,
        }
        serializable = dict(body)
        serializable["attestation_records"] = [asdict(record) for record in records]
        manifest = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionAttestation(
            **body,
            attestation_manifest_hash=stable_hash(serializable),
        )

        if persist:
            payload = asdict(manifest)
            _atomic_write(self.attestation_directory / "current.json", payload)
            _atomic_write(
                self.attestation_directory / "manifests" / f"{manifest_id}.json",
                payload,
            )
            for record in records:
                _atomic_write(
                    self.attestation_directory / "consumptions" / record.serving_consumption_id / f"{record.attestation_id}.json",
                    asdict(record),
                )
        return manifest
