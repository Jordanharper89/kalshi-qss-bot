from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "INT-OIA-030"
ENGINE_ID = "INT-OIA-030"
POLICY_ID = (
    "oracle.intelligence.analytics.downstream-read-only-consumer."
    "demo-surface-publication-serving-consumption.v1"
)
STATUS_CONSUMED = "demo_surface_publication_serving_release_consumed"

DEFAULT_RELEASE_ATTESTATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_demo_surface_publication_serving_release_attestation"
)
DEFAULT_CONSUMPTION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_demo_surface_publication_serving_consumption"
)

APPROVED_PUBLICATION_SCHEMA = "oracle_research_demo_publication_manifest.v1"
APPROVED_PUBLICATION_MODE = "immutable_read_only_demo_publication"
APPROVED_SERVING_RELEASE_MODE = "single_use_immutable_read_only_demo_surface_release"
APPROVED_SERVING_RELEASE_SCOPE = "independently_attested_serving_authorization_only"
APPROVED_SERVING_CONSUMPTION_MODE = "single_use_read_only_serving_release_consumption"
APPROVED_SERVING_CONSUMPTION_SCOPE = "independently_attested_serving_release_only"


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionInvariantError(
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
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionInvariantError(
        f"unsupported value type: {type(value)!r}"
    )


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
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionInvariantError(
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
class DemoSurfacePublicationServingConsumptionRecord:
    sequence: int
    consumption_id: str
    serving_release_attestation_id: str
    serving_release_id: str
    serving_authorization_attestation_id: str
    serving_authorization_id: str
    publication_id: str
    consumer_id: str
    source_serving_release_attestation_record_hash: str
    source_serving_release_record_hash: str
    source_serving_authorization_attestation_record_hash: str
    source_serving_authorization_record_hash: str
    source_readiness_attestation_record_hash: str
    source_readiness_record_hash: str
    source_activation_attestation_record_hash: str
    source_activation_record_hash: str
    source_consumption_attestation_record_hash: str
    source_consumption_record_hash: str
    source_release_authorization_record_hash: str
    source_publication_record_hash: str
    source_demo_surface_release_id: str
    source_result_admission_id: str
    invocation_execution_id: str
    invocation_nonce: str
    source_boundary_id: str
    source_boundary_hash: str
    result_hash: str
    admitted_result_hash: str
    publication_payload_hash: str
    publication_schema: str
    publication_mode: str
    serving_release_mode: str
    serving_release_scope: str
    serving_consumption_mode: str
    serving_consumption_scope: str
    serving_release_attestation_record_hash_verified: bool
    serving_release_record_hash_verified: bool
    serving_authorization_attestation_record_hash_verified: bool
    serving_authorization_record_hash_verified: bool
    readiness_attestation_record_hash_verified: bool
    readiness_record_hash_verified: bool
    activation_attestation_record_hash_verified: bool
    activation_record_hash_verified: bool
    prior_consumption_attestation_record_hash_verified: bool
    prior_consumption_record_hash_verified: bool
    release_authorization_record_hash_verified: bool
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
    duplicate_consumption_rejected: bool
    demo_surface_publication_serving_release_consumed: bool
    signals_created: bool
    alerts_created: bool
    qseries_handoff_performed: bool
    qseries_execution_performed: bool
    market_order_creation_performed: bool
    funds_movement_performed: bool
    portfolio_mutation_performed: bool
    source_mutation_performed: bool
    consumption_status: str
    consumption_record_hash: str


@dataclass(frozen=True)
class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumption:
    schema_version: str
    engine_id: str
    consumed_at: str
    consumption_manifest_id: str
    consumption_status: str
    consumption_policy_id: str
    serving_consumption_mode: str
    serving_consumption_scope: str
    source_serving_release_attestation_manifest_id: str
    source_serving_release_attestation_manifest_hash: str
    source_serving_release_manifest_id: str
    source_serving_release_manifest_hash: str
    source_serving_authorization_attestation_manifest_id: str
    source_serving_authorization_attestation_manifest_hash: str
    source_serving_authorization_manifest_id: str
    source_serving_authorization_manifest_hash: str
    source_readiness_attestation_manifest_id: str
    source_readiness_attestation_manifest_hash: str
    source_readiness_manifest_id: str
    source_readiness_manifest_hash: str
    source_activation_attestation_manifest_id: str
    source_activation_attestation_manifest_hash: str
    source_activation_manifest_id: str
    source_activation_manifest_hash: str
    source_prior_consumption_attestation_manifest_id: str
    source_prior_consumption_attestation_manifest_hash: str
    source_prior_consumption_manifest_id: str
    source_prior_consumption_manifest_hash: str
    source_release_authorization_manifest_id: str
    source_release_authorization_manifest_hash: str
    source_publication_manifest_id: str
    source_publication_manifest_hash: str
    source_demo_surface_release_manifest_id: str
    source_demo_surface_release_manifest_hash: str
    source_result_admission_manifest_id: str
    source_boundary_id: str
    source_boundary_hash: str
    consumption_record_count: int
    consumption_records: tuple[DemoSurfacePublicationServingConsumptionRecord, ...]
    all_serving_release_attestation_record_hashes_verified: bool
    all_serving_release_record_hashes_verified: bool
    all_serving_authorization_attestation_record_hashes_verified: bool
    all_serving_authorization_record_hashes_verified: bool
    all_readiness_attestation_record_hashes_verified: bool
    all_readiness_record_hashes_verified: bool
    all_activation_attestation_record_hashes_verified: bool
    all_activation_record_hashes_verified: bool
    all_prior_consumption_attestation_record_hashes_verified: bool
    all_prior_consumption_record_hashes_verified: bool
    all_release_authorization_record_hashes_verified: bool
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
    all_demo_surface_publication_serving_releases_consumed: bool
    duplicate_consumptions_rejected: bool
    source_boundary_consumed_without_reexecution: bool
    invocation_reexecution_performed: bool
    database_connection_performed: bool
    corpus_read_execution_repeated: bool
    source_mutation_allowed: bool
    source_mutation_performed: bool
    analytic_conclusion_allowed: bool
    publication_manifest_published: bool
    publication_manifest_attested: bool
    publication_release_authorized: bool
    publication_release_authorization_consumed: bool
    publication_release_authorization_consumption_attested: bool
    demo_surface_publication_activated: bool
    demo_surface_publication_activation_attested: bool
    demo_surface_publication_serving_ready: bool
    demo_surface_publication_serving_readiness_attested: bool
    demo_surface_publication_serving_authorized: bool
    demo_surface_publication_serving_authorization_attested: bool
    demo_surface_publication_serving_released: bool
    demo_surface_publication_serving_release_attested: bool
    demo_surface_publication_serving_release_consumed: bool
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
    consumption_artifact_persistence_allowed: bool
    consumption_manifest_hash: str


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionGate:
    def __init__(
        self,
        *,
        release_attestation_directory: Path | str = DEFAULT_RELEASE_ATTESTATION_DIRECTORY,
        consumption_directory: Path | str = DEFAULT_CONSUMPTION_DIRECTORY,
    ) -> None:
        self.release_attestation_directory = Path(release_attestation_directory)
        self.consumption_directory = Path(consumption_directory)

    def _load_release_attestation(self) -> dict[str, Any]:
        path = self.release_attestation_directory / "current.json"
        if not path.exists():
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionInvariantError(
                f"INT-OIA-029 serving-release attestation missing: {path}"
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionInvariantError(
                "INT-OIA-029 serving-release attestation could not be decoded"
            ) from exc

        manifest_hash = payload.pop("attestation_manifest_hash", None)
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionInvariantError(
                "INT-OIA-029 attestation manifest hash mismatch"
            )
        payload["attestation_manifest_hash"] = manifest_hash

        required_manifest = {
            "schema_version": "INT-OIA-029",
            "engine_id": "INT-OIA-029",
            "attestation_status": "demo_surface_publication_serving_release_independently_attested",
            "all_serving_release_record_hashes_verified": True,
            "all_serving_authorization_attestation_record_hashes_verified": True,
            "all_serving_authorization_record_hashes_verified": True,
            "all_readiness_attestation_record_hashes_verified": True,
            "all_readiness_record_hashes_verified": True,
            "all_activation_attestation_record_hashes_verified": True,
            "all_activation_record_hashes_verified": True,
            "all_consumption_attestation_record_hashes_verified": True,
            "all_consumption_record_hashes_verified": True,
            "all_release_authorization_record_hashes_verified": True,
            "all_publication_record_hashes_verified": True,
            "all_publication_payload_hashes_verified": True,
            "all_admission_lineage_verified": True,
            "all_one_time_invocations_verified": True,
            "all_results_immutable": True,
            "all_read_only_boundaries_verified": True,
            "all_execution_disabled_boundaries_verified": True,
            "all_independent_serving_authorization_attestations_verified": True,
            "all_serving_release_scopes_verified": True,
            "all_single_use_releases_verified": True,
            "all_serving_releases_verified": True,
            "all_serving_releases_independently_attested": True,
            "duplicate_attestations_rejected": True,
            "source_boundary_consumed_without_reexecution": True,
            "invocation_reexecution_performed": False,
            "database_connection_performed": False,
            "corpus_read_execution_repeated": False,
            "source_mutation_allowed": False,
            "source_mutation_performed": False,
            "analytic_conclusion_allowed": True,
            "publication_manifest_published": True,
            "publication_manifest_attested": True,
            "publication_release_authorized": True,
            "publication_release_authorization_consumed": True,
            "publication_release_authorization_consumption_attested": True,
            "demo_surface_publication_activated": True,
            "demo_surface_publication_activation_attested": True,
            "demo_surface_publication_serving_ready": True,
            "demo_surface_publication_serving_readiness_attested": True,
            "demo_surface_publication_serving_authorized": True,
            "demo_surface_publication_serving_authorization_attested": True,
            "demo_surface_publication_serving_released": True,
            "demo_surface_publication_serving_release_attested": True,
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
        for field, expected in required_manifest.items():
            if payload.get(field) != expected:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionInvariantError(
                    f"unsafe or incomplete INT-OIA-029 field: {field}"
                )

        records = payload.get("attestation_records")
        if not isinstance(records, list) or not records or payload.get("attestation_record_count") != len(records):
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionInvariantError(
                "INT-OIA-029 attestation records invalid"
            )

        seen_ids: set[str] = set()
        for sequence, raw_record in enumerate(records, start=1):
            if not isinstance(raw_record, Mapping):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionInvariantError(
                    "attestation record must be a mapping"
                )
            record = dict(raw_record)
            record_hash = record.pop("attestation_record_hash", None)
            if not _valid_hash(record_hash) or stable_hash(record) != record_hash:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionInvariantError(
                    "INT-OIA-029 attestation-record hash mismatch"
                )
            record["attestation_record_hash"] = record_hash

            attestation_id = record.get("attestation_id")
            if record.get("sequence") != sequence or not isinstance(attestation_id, str) or not attestation_id or attestation_id in seen_ids:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionInvariantError(
                    "invalid sequence or duplicate serving-release attestation"
                )
            seen_ids.add(attestation_id)

            required_record = {
                "publication_schema": APPROVED_PUBLICATION_SCHEMA,
                "publication_mode": APPROVED_PUBLICATION_MODE,
                "serving_release_mode": APPROVED_SERVING_RELEASE_MODE,
                "serving_release_scope": APPROVED_SERVING_RELEASE_SCOPE,
                "serving_release_record_hash_verified": True,
                "serving_authorization_attestation_record_hash_verified": True,
                "serving_authorization_record_hash_verified": True,
                "readiness_attestation_record_hash_verified": True,
                "readiness_record_hash_verified": True,
                "activation_attestation_record_hash_verified": True,
                "activation_record_hash_verified": True,
                "consumption_attestation_record_hash_verified": True,
                "consumption_record_hash_verified": True,
                "release_authorization_record_hash_verified": True,
                "publication_record_hash_verified": True,
                "publication_payload_hash_verified": True,
                "admission_lineage_verified": True,
                "one_time_invocation_verified": True,
                "immutable_result_verified": True,
                "read_only_boundary_verified": True,
                "execution_disabled_boundary_verified": True,
                "independent_serving_authorization_attestation_verified": True,
                "serving_release_scope_verified": True,
                "single_use_release_verified": True,
                "serving_release_verified": True,
                "duplicate_attestation_rejected": True,
                "independent_serving_release_attestation_performed": True,
                "signals_created": False,
                "alerts_created": False,
                "qseries_handoff_performed": False,
                "qseries_execution_performed": False,
                "market_order_creation_performed": False,
                "funds_movement_performed": False,
                "portfolio_mutation_performed": False,
                "source_mutation_performed": False,
                "attestation_status": "read_only_demo_publication_serving_release_independently_attested",
            }
            for field, expected in required_record.items():
                if record.get(field) != expected:
                    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionInvariantError(
                        f"unsafe INT-OIA-029 attestation-record field: {field}"
                    )

        return payload

    def consume(
        self,
        *,
        consumed_at: datetime,
        persist: bool = True,
    ) -> OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumption:
        consumed_at = _aware(consumed_at, "consumed_at")
        source = self._load_release_attestation()

        records: list[DemoSurfacePublicationServingConsumptionRecord] = []
        seen_consumption_ids: set[str] = set()

        for sequence, attestation in enumerate(source["attestation_records"], start=1):
            consumption_id = stable_hash(
                {
                    "source_serving_release_attestation_manifest_id": source["attestation_manifest_id"],
                    "serving_release_attestation_id": attestation["attestation_id"],
                    "source_serving_release_attestation_record_hash": attestation["attestation_record_hash"],
                    "publication_id": attestation["publication_id"],
                    "consumer_id": attestation["consumer_id"],
                    "consumed_at": consumed_at.isoformat(),
                    "serving_consumption_mode": APPROVED_SERVING_CONSUMPTION_MODE,
                    "serving_consumption_scope": APPROVED_SERVING_CONSUMPTION_SCOPE,
                }
            )
            if consumption_id in seen_consumption_ids:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionInvariantError(
                    "duplicate serving consumption id"
                )
            seen_consumption_ids.add(consumption_id)

            body = {
                "sequence": sequence,
                "consumption_id": consumption_id,
                "serving_release_attestation_id": attestation["attestation_id"],
                "serving_release_id": attestation["serving_release_id"],
                "serving_authorization_attestation_id": attestation["serving_authorization_attestation_id"],
                "serving_authorization_id": attestation["serving_authorization_id"],
                "publication_id": attestation["publication_id"],
                "consumer_id": attestation["consumer_id"],
                "source_serving_release_attestation_record_hash": attestation["attestation_record_hash"],
                "source_serving_release_record_hash": attestation["source_serving_release_record_hash"],
                "source_serving_authorization_attestation_record_hash": attestation["source_serving_authorization_attestation_record_hash"],
                "source_serving_authorization_record_hash": attestation["source_serving_authorization_record_hash"],
                "source_readiness_attestation_record_hash": attestation["source_readiness_attestation_record_hash"],
                "source_readiness_record_hash": attestation["source_readiness_record_hash"],
                "source_activation_attestation_record_hash": attestation["source_activation_attestation_record_hash"],
                "source_activation_record_hash": attestation["source_activation_record_hash"],
                "source_consumption_attestation_record_hash": attestation["source_consumption_attestation_record_hash"],
                "source_consumption_record_hash": attestation["source_consumption_record_hash"],
                "source_release_authorization_record_hash": attestation["source_release_authorization_record_hash"],
                "source_publication_record_hash": attestation["source_publication_record_hash"],
                "source_demo_surface_release_id": attestation["source_demo_surface_release_id"],
                "source_result_admission_id": attestation["source_result_admission_id"],
                "invocation_execution_id": attestation["invocation_execution_id"],
                "invocation_nonce": attestation["invocation_nonce"],
                "source_boundary_id": attestation["source_boundary_id"],
                "source_boundary_hash": attestation["source_boundary_hash"],
                "result_hash": attestation["result_hash"],
                "admitted_result_hash": attestation["admitted_result_hash"],
                "publication_payload_hash": attestation["publication_payload_hash"],
                "publication_schema": APPROVED_PUBLICATION_SCHEMA,
                "publication_mode": APPROVED_PUBLICATION_MODE,
                "serving_release_mode": APPROVED_SERVING_RELEASE_MODE,
                "serving_release_scope": APPROVED_SERVING_RELEASE_SCOPE,
                "serving_consumption_mode": APPROVED_SERVING_CONSUMPTION_MODE,
                "serving_consumption_scope": APPROVED_SERVING_CONSUMPTION_SCOPE,
                "serving_release_attestation_record_hash_verified": True,
                "serving_release_record_hash_verified": True,
                "serving_authorization_attestation_record_hash_verified": True,
                "serving_authorization_record_hash_verified": True,
                "readiness_attestation_record_hash_verified": True,
                "readiness_record_hash_verified": True,
                "activation_attestation_record_hash_verified": True,
                "activation_record_hash_verified": True,
                "prior_consumption_attestation_record_hash_verified": True,
                "prior_consumption_record_hash_verified": True,
                "release_authorization_record_hash_verified": True,
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
            records.append(
                DemoSurfacePublicationServingConsumptionRecord(
                    **body,
                    consumption_record_hash=stable_hash(body),
                )
            )

        manifest_id = stable_hash(
            {
                "source_serving_release_attestation_manifest_id": source["attestation_manifest_id"],
                "source_serving_release_attestation_manifest_hash": source["attestation_manifest_hash"],
                "consumed_at": consumed_at.isoformat(),
                "consumption_record_hashes": [record.consumption_record_hash for record in records],
            }
        )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "consumed_at": consumed_at.isoformat(),
            "consumption_manifest_id": manifest_id,
            "consumption_status": STATUS_CONSUMED,
            "consumption_policy_id": POLICY_ID,
            "serving_consumption_mode": APPROVED_SERVING_CONSUMPTION_MODE,
            "serving_consumption_scope": APPROVED_SERVING_CONSUMPTION_SCOPE,
            "source_serving_release_attestation_manifest_id": source["attestation_manifest_id"],
            "source_serving_release_attestation_manifest_hash": source["attestation_manifest_hash"],
            "source_serving_release_manifest_id": source["source_serving_release_manifest_id"],
            "source_serving_release_manifest_hash": source["source_serving_release_manifest_hash"],
            "source_serving_authorization_attestation_manifest_id": source["source_serving_authorization_attestation_manifest_id"],
            "source_serving_authorization_attestation_manifest_hash": source["source_serving_authorization_attestation_manifest_hash"],
            "source_serving_authorization_manifest_id": source["source_serving_authorization_manifest_id"],
            "source_serving_authorization_manifest_hash": source["source_serving_authorization_manifest_hash"],
            "source_readiness_attestation_manifest_id": source["source_readiness_attestation_manifest_id"],
            "source_readiness_attestation_manifest_hash": source["source_readiness_attestation_manifest_hash"],
            "source_readiness_manifest_id": source["source_readiness_manifest_id"],
            "source_readiness_manifest_hash": source["source_readiness_manifest_hash"],
            "source_activation_attestation_manifest_id": source["source_activation_attestation_manifest_id"],
            "source_activation_attestation_manifest_hash": source["source_activation_attestation_manifest_hash"],
            "source_activation_manifest_id": source["source_activation_manifest_id"],
            "source_activation_manifest_hash": source["source_activation_manifest_hash"],
            "source_prior_consumption_attestation_manifest_id": source["source_consumption_attestation_manifest_id"],
            "source_prior_consumption_attestation_manifest_hash": source["source_consumption_attestation_manifest_hash"],
            "source_prior_consumption_manifest_id": source["source_consumption_manifest_id"],
            "source_prior_consumption_manifest_hash": source["source_consumption_manifest_hash"],
            "source_release_authorization_manifest_id": source["source_release_authorization_manifest_id"],
            "source_release_authorization_manifest_hash": source["source_release_authorization_manifest_hash"],
            "source_publication_manifest_id": source["source_publication_manifest_id"],
            "source_publication_manifest_hash": source["source_publication_manifest_hash"],
            "source_demo_surface_release_manifest_id": source["source_demo_surface_release_manifest_id"],
            "source_demo_surface_release_manifest_hash": source["source_demo_surface_release_manifest_hash"],
            "source_result_admission_manifest_id": source["source_result_admission_manifest_id"],
            "source_boundary_id": source["source_boundary_id"],
            "source_boundary_hash": source["source_boundary_hash"],
            "consumption_record_count": len(records),
            "consumption_records": tuple(records),
            "all_serving_release_attestation_record_hashes_verified": True,
            "all_serving_release_record_hashes_verified": True,
            "all_serving_authorization_attestation_record_hashes_verified": True,
            "all_serving_authorization_record_hashes_verified": True,
            "all_readiness_attestation_record_hashes_verified": True,
            "all_readiness_record_hashes_verified": True,
            "all_activation_attestation_record_hashes_verified": True,
            "all_activation_record_hashes_verified": True,
            "all_prior_consumption_attestation_record_hashes_verified": True,
            "all_prior_consumption_record_hashes_verified": True,
            "all_release_authorization_record_hashes_verified": True,
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
            "analytic_conclusion_allowed": True,
            "publication_manifest_published": True,
            "publication_manifest_attested": True,
            "publication_release_authorized": True,
            "publication_release_authorization_consumed": True,
            "publication_release_authorization_consumption_attested": True,
            "demo_surface_publication_activated": True,
            "demo_surface_publication_activation_attested": True,
            "demo_surface_publication_serving_ready": True,
            "demo_surface_publication_serving_readiness_attested": True,
            "demo_surface_publication_serving_authorized": True,
            "demo_surface_publication_serving_authorization_attested": True,
            "demo_surface_publication_serving_released": True,
            "demo_surface_publication_serving_release_attested": True,
            "demo_surface_publication_serving_release_consumed": True,
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
            "consumption_artifact_persistence_allowed": True,
        }

        serializable = dict(body)
        serializable["consumption_records"] = [asdict(record) for record in records]
        manifest_hash = stable_hash(serializable)
        manifest = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumption(
            **body,
            consumption_manifest_hash=manifest_hash,
        )

        if persist:
            payload = asdict(manifest)
            _atomic_write(self.consumption_directory / "current.json", payload)
            _atomic_write(
                self.consumption_directory / "manifests" / f"{manifest_id}.json",
                payload,
            )
            for record in records:
                _atomic_write(
                    self.consumption_directory / "releases" / record.serving_release_id / f"{record.consumption_id}.json",
                    asdict(record),
                )

        return manifest
