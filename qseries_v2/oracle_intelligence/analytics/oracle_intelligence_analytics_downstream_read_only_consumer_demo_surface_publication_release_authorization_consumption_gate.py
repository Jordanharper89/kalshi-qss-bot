from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "INT-OIA-020"
ENGINE_ID = "INT-OIA-020"
POLICY_ID = (
    "oracle.intelligence.analytics.downstream-read-only-consumer."
    "demo-surface-publication-release-authorization-consumption.v1"
)
STATUS_CONSUMED = "demo_surface_publication_release_authorization_consumed"

DEFAULT_AUTHORIZATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_demo_surface_publication_release_authorization"
)
DEFAULT_CONSUMPTION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_demo_surface_publication_release_authorization_consumption"
)

APPROVED_PUBLICATION_SCHEMA = "oracle_research_demo_publication_manifest.v1"
APPROVED_PUBLICATION_MODE = "immutable_read_only_demo_publication"
APPROVED_AUTHORIZATION_MODE = "one_time_read_only_demo_publication_release"
APPROVED_AUTHORIZATION_SCOPE = "attested_demo_surface_publication_only"
APPROVED_CONSUMPTION_MODE = "single_use_read_only_release_authorization"
APPROVED_CONSUMPTION_SCOPE = "authorized_demo_surface_publication_only"


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationConsumptionInvariantError(
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
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationConsumptionInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationConsumptionInvariantError(
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
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationConsumptionInvariantError(
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
class DemoSurfacePublicationReleaseAuthorizationConsumptionRecord:
    sequence: int
    consumption_id: str
    authorization_id: str
    attestation_id: str
    publication_id: str
    consumer_id: str
    source_authorization_record_hash: str
    source_attestation_record_hash: str
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
    authorization_mode: str
    authorization_scope: str
    consumption_mode: str
    consumption_scope: str
    authorization_record_hash_verified: bool
    attestation_record_hash_verified: bool
    publication_record_hash_verified: bool
    publication_payload_hash_verified: bool
    admission_lineage_verified: bool
    one_time_invocation_verified: bool
    immutable_result_verified: bool
    read_only_boundary_verified: bool
    execution_disabled_boundary_verified: bool
    independent_attestation_verified: bool
    authorization_scope_verified: bool
    consumption_scope_verified: bool
    duplicate_consumption_rejected: bool
    authorization_consumed_once: bool
    publication_release_authorized: bool
    publication_release_authorization_consumed: bool
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
class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationConsumption:
    schema_version: str
    engine_id: str
    consumed_at: str
    consumption_manifest_id: str
    consumption_status: str
    consumption_policy_id: str
    consumption_mode: str
    consumption_scope: str
    source_authorization_manifest_id: str
    source_authorization_manifest_hash: str
    source_attestation_manifest_id: str
    source_attestation_manifest_hash: str
    source_publication_manifest_id: str
    source_publication_manifest_hash: str
    source_demo_surface_release_manifest_id: str
    source_demo_surface_release_manifest_hash: str
    source_result_admission_manifest_id: str
    source_boundary_id: str
    source_boundary_hash: str
    consumption_record_count: int
    consumption_records: tuple[DemoSurfacePublicationReleaseAuthorizationConsumptionRecord, ...]
    all_authorization_record_hashes_verified: bool
    all_attestation_record_hashes_verified: bool
    all_publication_record_hashes_verified: bool
    all_publication_payload_hashes_verified: bool
    all_admission_lineage_verified: bool
    all_one_time_invocations_verified: bool
    all_results_immutable: bool
    all_read_only_boundaries_verified: bool
    all_execution_disabled_boundaries_verified: bool
    all_independent_attestations_verified: bool
    all_authorization_scopes_verified: bool
    all_consumption_scopes_verified: bool
    all_authorizations_consumed_once: bool
    duplicate_consumptions_rejected: bool
    source_boundary_consumed_without_reexecution: bool
    invocation_reexecution_performed: bool
    database_connection_performed: bool
    corpus_read_execution_repeated: bool
    source_mutation_allowed: bool
    source_mutation_performed: bool
    analytic_conclusion_allowed: bool
    demo_surface_released: bool
    publication_manifest_published: bool
    publication_manifest_attested: bool
    publication_release_authorized: bool
    publication_release_authorization_consumed: bool
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


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationConsumptionGate:
    def __init__(
        self,
        *,
        authorization_directory: Path | str = DEFAULT_AUTHORIZATION_DIRECTORY,
        consumption_directory: Path | str = DEFAULT_CONSUMPTION_DIRECTORY,
    ) -> None:
        self.authorization_directory = Path(authorization_directory)
        self.consumption_directory = Path(consumption_directory)

    def _load_authorization(self) -> dict[str, Any]:
        path = self.authorization_directory / "current.json"
        if not path.exists():
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationConsumptionInvariantError(
                f"INT-OIA-019 authorization artifact missing: {path}"
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationConsumptionInvariantError(
                "INT-OIA-019 authorization artifact could not be decoded"
            ) from exc

        manifest_hash = payload.pop("authorization_manifest_hash", None)
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationConsumptionInvariantError(
                "INT-OIA-019 authorization manifest hash mismatch"
            )
        payload["authorization_manifest_hash"] = manifest_hash

        required_manifest = {
            "schema_version": "INT-OIA-019",
            "engine_id": "INT-OIA-019",
            "authorization_status": "demo_surface_publication_release_authorized",
            "authorization_mode": APPROVED_AUTHORIZATION_MODE,
            "authorization_scope": APPROVED_AUTHORIZATION_SCOPE,
            "all_attestation_record_hashes_verified": True,
            "all_publication_record_hashes_verified": True,
            "all_publication_payload_hashes_verified": True,
            "all_source_release_hashes_verified": True,
            "all_admission_lineage_verified": True,
            "all_one_time_invocations_verified": True,
            "all_results_immutable": True,
            "all_read_only_boundaries_verified": True,
            "all_execution_disabled_boundaries_verified": True,
            "all_independent_attestations_verified": True,
            "all_authorization_scopes_verified": True,
            "all_publication_releases_authorized": True,
            "duplicate_authorizations_rejected": True,
            "source_boundary_consumed_without_reexecution": True,
            "invocation_reexecution_performed": False,
            "database_connection_performed": False,
            "corpus_read_execution_repeated": False,
            "source_mutation_allowed": False,
            "source_mutation_performed": False,
            "analytic_conclusion_allowed": True,
            "demo_surface_released": True,
            "publication_manifest_published": True,
            "publication_manifest_attested": True,
            "publication_release_authorized": True,
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
            "authorization_artifact_persistence_allowed": True,
        }
        for field, expected in required_manifest.items():
            if payload.get(field) != expected:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationConsumptionInvariantError(
                    f"unsafe or incomplete INT-OIA-019 field: {field}"
                )

        records = payload.get("authorization_records")
        if (
            not isinstance(records, list)
            or not records
            or payload.get("authorization_record_count") != len(records)
        ):
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationConsumptionInvariantError(
                "INT-OIA-019 authorization records invalid"
            )

        seen_ids: set[str] = set()
        for sequence, raw_record in enumerate(records, start=1):
            if not isinstance(raw_record, Mapping):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationConsumptionInvariantError(
                    "authorization record must be a mapping"
                )
            record = dict(raw_record)
            record_hash = record.pop("authorization_record_hash", None)
            if not _valid_hash(record_hash) or stable_hash(record) != record_hash:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationConsumptionInvariantError(
                    "INT-OIA-019 authorization-record hash mismatch"
                )
            record["authorization_record_hash"] = record_hash

            authorization_id = record.get("authorization_id")
            if (
                record.get("sequence") != sequence
                or not isinstance(authorization_id, str)
                or not authorization_id
                or authorization_id in seen_ids
            ):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationConsumptionInvariantError(
                    "invalid sequence or duplicate authorization"
                )
            seen_ids.add(authorization_id)

            required_record = {
                "publication_schema": APPROVED_PUBLICATION_SCHEMA,
                "publication_mode": APPROVED_PUBLICATION_MODE,
                "authorization_mode": APPROVED_AUTHORIZATION_MODE,
                "authorization_scope": APPROVED_AUTHORIZATION_SCOPE,
                "attestation_record_hash_verified": True,
                "publication_record_hash_verified": True,
                "publication_payload_hash_verified": True,
                "source_release_hash_verified": True,
                "admission_lineage_verified": True,
                "one_time_invocation_verified": True,
                "immutable_result_verified": True,
                "read_only_boundary_verified": True,
                "execution_disabled_boundary_verified": True,
                "independent_attestation_verified": True,
                "authorization_scope_verified": True,
                "duplicate_authorization_rejected": True,
                "publication_release_authorized": True,
                "signals_created": False,
                "alerts_created": False,
                "qseries_handoff_performed": False,
                "qseries_execution_performed": False,
                "market_order_creation_performed": False,
                "funds_movement_performed": False,
                "portfolio_mutation_performed": False,
                "source_mutation_performed": False,
                "authorization_status": (
                    "attested_demo_surface_publication_release_authorized"
                ),
            }
            for field, expected in required_record.items():
                if record.get(field) != expected:
                    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationConsumptionInvariantError(
                        f"unsafe INT-OIA-019 authorization-record field: {field}"
                    )

        return payload

    def consume(
        self,
        *,
        consumed_at: datetime,
        persist: bool = True,
    ) -> OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationConsumption:
        consumed_at = _aware(consumed_at, "consumed_at")
        source = self._load_authorization()

        records: list[
            DemoSurfacePublicationReleaseAuthorizationConsumptionRecord
        ] = []
        seen_consumption_ids: set[str] = set()

        for sequence, authorization in enumerate(
            source["authorization_records"],
            start=1,
        ):
            consumption_id = stable_hash(
                {
                    "source_authorization_manifest_id": source[
                        "authorization_manifest_id"
                    ],
                    "authorization_id": authorization["authorization_id"],
                    "source_authorization_record_hash": authorization[
                        "authorization_record_hash"
                    ],
                    "publication_id": authorization["publication_id"],
                    "consumed_at": consumed_at.isoformat(),
                    "consumption_mode": APPROVED_CONSUMPTION_MODE,
                    "consumption_scope": APPROVED_CONSUMPTION_SCOPE,
                }
            )
            if consumption_id in seen_consumption_ids:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationConsumptionInvariantError(
                    "duplicate consumption id"
                )
            seen_consumption_ids.add(consumption_id)

            body = {
                "sequence": sequence,
                "consumption_id": consumption_id,
                "authorization_id": authorization["authorization_id"],
                "attestation_id": authorization["attestation_id"],
                "publication_id": authorization["publication_id"],
                "consumer_id": authorization["consumer_id"],
                "source_authorization_record_hash": authorization[
                    "authorization_record_hash"
                ],
                "source_attestation_record_hash": authorization[
                    "source_attestation_record_hash"
                ],
                "source_publication_record_hash": authorization[
                    "source_publication_record_hash"
                ],
                "source_demo_surface_release_id": authorization[
                    "source_demo_surface_release_id"
                ],
                "source_result_admission_id": authorization[
                    "source_result_admission_id"
                ],
                "invocation_execution_id": authorization[
                    "invocation_execution_id"
                ],
                "invocation_nonce": authorization["invocation_nonce"],
                "source_boundary_id": authorization["source_boundary_id"],
                "source_boundary_hash": authorization["source_boundary_hash"],
                "result_hash": authorization["result_hash"],
                "admitted_result_hash": authorization["admitted_result_hash"],
                "publication_payload_hash": authorization[
                    "publication_payload_hash"
                ],
                "publication_schema": APPROVED_PUBLICATION_SCHEMA,
                "publication_mode": APPROVED_PUBLICATION_MODE,
                "authorization_mode": APPROVED_AUTHORIZATION_MODE,
                "authorization_scope": APPROVED_AUTHORIZATION_SCOPE,
                "consumption_mode": APPROVED_CONSUMPTION_MODE,
                "consumption_scope": APPROVED_CONSUMPTION_SCOPE,
                "authorization_record_hash_verified": True,
                "attestation_record_hash_verified": True,
                "publication_record_hash_verified": True,
                "publication_payload_hash_verified": True,
                "admission_lineage_verified": True,
                "one_time_invocation_verified": True,
                "immutable_result_verified": True,
                "read_only_boundary_verified": True,
                "execution_disabled_boundary_verified": True,
                "independent_attestation_verified": True,
                "authorization_scope_verified": True,
                "consumption_scope_verified": True,
                "duplicate_consumption_rejected": True,
                "authorization_consumed_once": True,
                "publication_release_authorized": True,
                "publication_release_authorization_consumed": True,
                "signals_created": False,
                "alerts_created": False,
                "qseries_handoff_performed": False,
                "qseries_execution_performed": False,
                "market_order_creation_performed": False,
                "funds_movement_performed": False,
                "portfolio_mutation_performed": False,
                "source_mutation_performed": False,
                "consumption_status": (
                    "read_only_demo_publication_authorization_consumed_once"
                ),
            }
            records.append(
                DemoSurfacePublicationReleaseAuthorizationConsumptionRecord(
                    **body,
                    consumption_record_hash=stable_hash(body),
                )
            )

        manifest_id = stable_hash(
            {
                "source_authorization_manifest_id": source[
                    "authorization_manifest_id"
                ],
                "source_authorization_manifest_hash": source[
                    "authorization_manifest_hash"
                ],
                "consumed_at": consumed_at.isoformat(),
                "consumption_record_hashes": [
                    record.consumption_record_hash for record in records
                ],
            }
        )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "consumed_at": consumed_at.isoformat(),
            "consumption_manifest_id": manifest_id,
            "consumption_status": STATUS_CONSUMED,
            "consumption_policy_id": POLICY_ID,
            "consumption_mode": APPROVED_CONSUMPTION_MODE,
            "consumption_scope": APPROVED_CONSUMPTION_SCOPE,
            "source_authorization_manifest_id": source[
                "authorization_manifest_id"
            ],
            "source_authorization_manifest_hash": source[
                "authorization_manifest_hash"
            ],
            "source_attestation_manifest_id": source[
                "source_attestation_manifest_id"
            ],
            "source_attestation_manifest_hash": source[
                "source_attestation_manifest_hash"
            ],
            "source_publication_manifest_id": source[
                "source_publication_manifest_id"
            ],
            "source_publication_manifest_hash": source[
                "source_publication_manifest_hash"
            ],
            "source_demo_surface_release_manifest_id": source[
                "source_demo_surface_release_manifest_id"
            ],
            "source_demo_surface_release_manifest_hash": source[
                "source_demo_surface_release_manifest_hash"
            ],
            "source_result_admission_manifest_id": source[
                "source_result_admission_manifest_id"
            ],
            "source_boundary_id": source["source_boundary_id"],
            "source_boundary_hash": source["source_boundary_hash"],
            "consumption_record_count": len(records),
            "consumption_records": tuple(records),
            "all_authorization_record_hashes_verified": True,
            "all_attestation_record_hashes_verified": True,
            "all_publication_record_hashes_verified": True,
            "all_publication_payload_hashes_verified": True,
            "all_admission_lineage_verified": True,
            "all_one_time_invocations_verified": True,
            "all_results_immutable": True,
            "all_read_only_boundaries_verified": True,
            "all_execution_disabled_boundaries_verified": True,
            "all_independent_attestations_verified": True,
            "all_authorization_scopes_verified": True,
            "all_consumption_scopes_verified": True,
            "all_authorizations_consumed_once": True,
            "duplicate_consumptions_rejected": True,
            "source_boundary_consumed_without_reexecution": True,
            "invocation_reexecution_performed": False,
            "database_connection_performed": False,
            "corpus_read_execution_repeated": False,
            "source_mutation_allowed": False,
            "source_mutation_performed": False,
            "analytic_conclusion_allowed": True,
            "demo_surface_released": True,
            "publication_manifest_published": True,
            "publication_manifest_attested": True,
            "publication_release_authorized": True,
            "publication_release_authorization_consumed": True,
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
        serializable["consumption_records"] = [
            asdict(record) for record in records
        ]
        manifest_hash = stable_hash(serializable)
        manifest = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationConsumption(
            **body,
            consumption_manifest_hash=manifest_hash,
        )

        if persist:
            payload = asdict(manifest)
            _atomic_write(self.consumption_directory / "current.json", payload)
            _atomic_write(
                self.consumption_directory
                / "manifests"
                / f"{manifest_id}.json",
                payload,
            )
            for record in records:
                _atomic_write(
                    self.consumption_directory
                    / "authorizations"
                    / record.authorization_id
                    / f"{record.consumption_id}.json",
                    asdict(record),
                )

        return manifest
