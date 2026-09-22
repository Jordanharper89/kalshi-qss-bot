from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "INT-OIA-021"
ENGINE_ID = "INT-OIA-021"
POLICY_ID = (
    "oracle.intelligence.analytics.downstream-read-only-consumer."
    "demo-surface-publication-release-authorization-consumption-independent-attestation.v1"
)
STATUS_ATTESTED = (
    "demo_surface_publication_release_authorization_consumption_independently_attested"
)

DEFAULT_CONSUMPTION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_demo_surface_publication_release_authorization_consumption"
)
DEFAULT_ATTESTATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_demo_surface_publication_release_authorization_consumption_attestation"
)

APPROVED_PUBLICATION_SCHEMA = "oracle_research_demo_publication_manifest.v1"
APPROVED_PUBLICATION_MODE = "immutable_read_only_demo_publication"
APPROVED_AUTHORIZATION_MODE = "one_time_read_only_demo_publication_release"
APPROVED_AUTHORIZATION_SCOPE = "attested_demo_surface_publication_only"
APPROVED_CONSUMPTION_MODE = "single_use_read_only_release_authorization"
APPROVED_CONSUMPTION_SCOPE = "authorized_demo_surface_publication_only"


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationConsumptionAttestationInvariantError(
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
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationConsumptionAttestationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationConsumptionAttestationInvariantError(
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
        raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationConsumptionAttestationInvariantError(
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
class DemoSurfacePublicationReleaseAuthorizationConsumptionAttestationRecord:
    sequence: int
    attestation_id: str
    consumption_id: str
    authorization_id: str
    publication_id: str
    consumer_id: str
    source_consumption_record_hash: str
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
    consumption_record_hash_verified: bool
    authorization_record_hash_verified: bool
    attestation_record_hash_verified: bool
    publication_record_hash_verified: bool
    publication_payload_hash_verified: bool
    admission_lineage_verified: bool
    one_time_invocation_verified: bool
    immutable_result_verified: bool
    read_only_boundary_verified: bool
    execution_disabled_boundary_verified: bool
    independent_publication_attestation_verified: bool
    authorization_scope_verified: bool
    consumption_scope_verified: bool
    single_use_consumption_verified: bool
    duplicate_attestation_rejected: bool
    independent_consumption_attestation_performed: bool
    publication_release_authorization_consumed: bool
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
class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationConsumptionAttestation:
    schema_version: str
    engine_id: str
    attested_at: str
    attestation_manifest_id: str
    attestation_status: str
    attestation_policy_id: str
    source_consumption_manifest_id: str
    source_consumption_manifest_hash: str
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
    attestation_record_count: int
    attestation_records: tuple[
        DemoSurfacePublicationReleaseAuthorizationConsumptionAttestationRecord,
        ...,
    ]
    all_consumption_record_hashes_verified: bool
    all_authorization_record_hashes_verified: bool
    all_attestation_record_hashes_verified: bool
    all_publication_record_hashes_verified: bool
    all_publication_payload_hashes_verified: bool
    all_admission_lineage_verified: bool
    all_one_time_invocations_verified: bool
    all_results_immutable: bool
    all_read_only_boundaries_verified: bool
    all_execution_disabled_boundaries_verified: bool
    all_independent_publication_attestations_verified: bool
    all_authorization_scopes_verified: bool
    all_consumption_scopes_verified: bool
    all_single_use_consumptions_verified: bool
    all_consumptions_independently_attested: bool
    duplicate_attestations_rejected: bool
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
    publication_release_authorization_consumption_attested: bool
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


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationConsumptionAttestationGate:
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
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationConsumptionAttestationInvariantError(
                f"INT-OIA-020 consumption artifact missing: {path}"
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationConsumptionAttestationInvariantError(
                "INT-OIA-020 consumption artifact could not be decoded"
            ) from exc

        manifest_hash = payload.pop("consumption_manifest_hash", None)
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationConsumptionAttestationInvariantError(
                "INT-OIA-020 consumption manifest hash mismatch"
            )
        payload["consumption_manifest_hash"] = manifest_hash

        required_manifest = {
            "schema_version": "INT-OIA-020",
            "engine_id": "INT-OIA-020",
            "consumption_status": (
                "demo_surface_publication_release_authorization_consumed"
            ),
            "consumption_mode": APPROVED_CONSUMPTION_MODE,
            "consumption_scope": APPROVED_CONSUMPTION_SCOPE,
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
        for field, expected in required_manifest.items():
            if payload.get(field) != expected:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationConsumptionAttestationInvariantError(
                    f"unsafe or incomplete INT-OIA-020 field: {field}"
                )

        records = payload.get("consumption_records")
        if (
            not isinstance(records, list)
            or not records
            or payload.get("consumption_record_count") != len(records)
        ):
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationConsumptionAttestationInvariantError(
                "INT-OIA-020 consumption records invalid"
            )

        seen_ids: set[str] = set()
        for sequence, raw_record in enumerate(records, start=1):
            if not isinstance(raw_record, Mapping):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationConsumptionAttestationInvariantError(
                    "consumption record must be a mapping"
                )

            record = dict(raw_record)
            record_hash = record.pop("consumption_record_hash", None)
            if not _valid_hash(record_hash) or stable_hash(record) != record_hash:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationConsumptionAttestationInvariantError(
                    "INT-OIA-020 consumption-record hash mismatch"
                )
            record["consumption_record_hash"] = record_hash

            consumption_id = record.get("consumption_id")
            if (
                record.get("sequence") != sequence
                or not isinstance(consumption_id, str)
                or not consumption_id
                or consumption_id in seen_ids
            ):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationConsumptionAttestationInvariantError(
                    "invalid sequence or duplicate consumption"
                )
            seen_ids.add(consumption_id)

            required_record = {
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
            for field, expected in required_record.items():
                if record.get(field) != expected:
                    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationConsumptionAttestationInvariantError(
                        f"unsafe INT-OIA-020 consumption-record field: {field}"
                    )

        return payload

    def attest(
        self,
        *,
        attested_at: datetime,
        persist: bool = True,
    ) -> OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationConsumptionAttestation:
        attested_at = _aware(attested_at, "attested_at")
        source = self._load_consumption()

        records: list[
            DemoSurfacePublicationReleaseAuthorizationConsumptionAttestationRecord
        ] = []
        seen_attestation_ids: set[str] = set()

        for sequence, consumption in enumerate(
            source["consumption_records"],
            start=1,
        ):
            attestation_id = stable_hash(
                {
                    "source_consumption_manifest_id": source[
                        "consumption_manifest_id"
                    ],
                    "consumption_id": consumption["consumption_id"],
                    "source_consumption_record_hash": consumption[
                        "consumption_record_hash"
                    ],
                    "publication_id": consumption["publication_id"],
                    "attested_at": attested_at.isoformat(),
                }
            )
            if attestation_id in seen_attestation_ids:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationConsumptionAttestationInvariantError(
                    "duplicate consumption attestation id"
                )
            seen_attestation_ids.add(attestation_id)

            body = {
                "sequence": sequence,
                "attestation_id": attestation_id,
                "consumption_id": consumption["consumption_id"],
                "authorization_id": consumption["authorization_id"],
                "publication_id": consumption["publication_id"],
                "consumer_id": consumption["consumer_id"],
                "source_consumption_record_hash": consumption[
                    "consumption_record_hash"
                ],
                "source_authorization_record_hash": consumption[
                    "source_authorization_record_hash"
                ],
                "source_attestation_record_hash": consumption[
                    "source_attestation_record_hash"
                ],
                "source_publication_record_hash": consumption[
                    "source_publication_record_hash"
                ],
                "source_demo_surface_release_id": consumption[
                    "source_demo_surface_release_id"
                ],
                "source_result_admission_id": consumption[
                    "source_result_admission_id"
                ],
                "invocation_execution_id": consumption[
                    "invocation_execution_id"
                ],
                "invocation_nonce": consumption["invocation_nonce"],
                "source_boundary_id": consumption["source_boundary_id"],
                "source_boundary_hash": consumption["source_boundary_hash"],
                "result_hash": consumption["result_hash"],
                "admitted_result_hash": consumption["admitted_result_hash"],
                "publication_payload_hash": consumption[
                    "publication_payload_hash"
                ],
                "publication_schema": APPROVED_PUBLICATION_SCHEMA,
                "publication_mode": APPROVED_PUBLICATION_MODE,
                "authorization_mode": APPROVED_AUTHORIZATION_MODE,
                "authorization_scope": APPROVED_AUTHORIZATION_SCOPE,
                "consumption_mode": APPROVED_CONSUMPTION_MODE,
                "consumption_scope": APPROVED_CONSUMPTION_SCOPE,
                "consumption_record_hash_verified": True,
                "authorization_record_hash_verified": True,
                "attestation_record_hash_verified": True,
                "publication_record_hash_verified": True,
                "publication_payload_hash_verified": True,
                "admission_lineage_verified": True,
                "one_time_invocation_verified": True,
                "immutable_result_verified": True,
                "read_only_boundary_verified": True,
                "execution_disabled_boundary_verified": True,
                "independent_publication_attestation_verified": True,
                "authorization_scope_verified": True,
                "consumption_scope_verified": True,
                "single_use_consumption_verified": True,
                "duplicate_attestation_rejected": True,
                "independent_consumption_attestation_performed": True,
                "publication_release_authorization_consumed": True,
                "signals_created": False,
                "alerts_created": False,
                "qseries_handoff_performed": False,
                "qseries_execution_performed": False,
                "market_order_creation_performed": False,
                "funds_movement_performed": False,
                "portfolio_mutation_performed": False,
                "source_mutation_performed": False,
                "attestation_status": (
                    "single_use_release_authorization_consumption_independently_attested"
                ),
            }
            records.append(
                DemoSurfacePublicationReleaseAuthorizationConsumptionAttestationRecord(
                    **body,
                    attestation_record_hash=stable_hash(body),
                )
            )

        manifest_id = stable_hash(
            {
                "source_consumption_manifest_id": source[
                    "consumption_manifest_id"
                ],
                "source_consumption_manifest_hash": source[
                    "consumption_manifest_hash"
                ],
                "attested_at": attested_at.isoformat(),
                "attestation_record_hashes": [
                    record.attestation_record_hash for record in records
                ],
            }
        )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "attested_at": attested_at.isoformat(),
            "attestation_manifest_id": manifest_id,
            "attestation_status": STATUS_ATTESTED,
            "attestation_policy_id": POLICY_ID,
            "source_consumption_manifest_id": source[
                "consumption_manifest_id"
            ],
            "source_consumption_manifest_hash": source[
                "consumption_manifest_hash"
            ],
            "source_authorization_manifest_id": source[
                "source_authorization_manifest_id"
            ],
            "source_authorization_manifest_hash": source[
                "source_authorization_manifest_hash"
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
            "attestation_record_count": len(records),
            "attestation_records": tuple(records),
            "all_consumption_record_hashes_verified": True,
            "all_authorization_record_hashes_verified": True,
            "all_attestation_record_hashes_verified": True,
            "all_publication_record_hashes_verified": True,
            "all_publication_payload_hashes_verified": True,
            "all_admission_lineage_verified": True,
            "all_one_time_invocations_verified": True,
            "all_results_immutable": True,
            "all_read_only_boundaries_verified": True,
            "all_execution_disabled_boundaries_verified": True,
            "all_independent_publication_attestations_verified": True,
            "all_authorization_scopes_verified": True,
            "all_consumption_scopes_verified": True,
            "all_single_use_consumptions_verified": True,
            "all_consumptions_independently_attested": True,
            "duplicate_attestations_rejected": True,
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
            "publication_release_authorization_consumption_attested": True,
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
        serializable["attestation_records"] = [
            asdict(record) for record in records
        ]
        manifest_hash = stable_hash(serializable)
        manifest = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationConsumptionAttestation(
            **body,
            attestation_manifest_hash=manifest_hash,
        )

        if persist:
            payload = asdict(manifest)
            _atomic_write(self.attestation_directory / "current.json", payload)
            _atomic_write(
                self.attestation_directory
                / "manifests"
                / f"{manifest_id}.json",
                payload,
            )
            for record in records:
                _atomic_write(
                    self.attestation_directory
                    / "consumptions"
                    / record.consumption_id
                    / f"{record.attestation_id}.json",
                    asdict(record),
                )

        return manifest
