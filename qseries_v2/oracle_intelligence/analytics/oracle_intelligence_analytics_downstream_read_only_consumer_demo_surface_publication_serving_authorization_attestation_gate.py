from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "INT-OIA-027"
ENGINE_ID = "INT-OIA-027"
POLICY_ID = (
    "oracle.intelligence.analytics.downstream-read-only-consumer."
    "demo-surface-publication-serving-authorization-independent-attestation.v1"
)
STATUS_ATTESTED = "demo_surface_publication_serving_authorization_independently_attested"

DEFAULT_AUTHORIZATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_demo_surface_publication_serving_authorization"
)
DEFAULT_ATTESTATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_demo_surface_publication_serving_authorization_attestation"
)

APPROVED_PUBLICATION_SCHEMA = "oracle_research_demo_publication_manifest.v1"
APPROVED_PUBLICATION_MODE = "immutable_read_only_demo_publication"
APPROVED_RELEASE_AUTHORIZATION_MODE = "one_time_read_only_demo_publication_release"
APPROVED_RELEASE_AUTHORIZATION_SCOPE = "attested_demo_surface_publication_only"
APPROVED_CONSUMPTION_MODE = "single_use_read_only_release_authorization"
APPROVED_CONSUMPTION_SCOPE = "authorized_demo_surface_publication_only"
APPROVED_ACTIVATION_MODE = "read_only_demo_surface_activation"
APPROVED_ACTIVATION_SCOPE = "independently_attested_publication_only"
APPROVED_SERVING_MODE = "read_only_demo_surface_presentation"
APPROVED_SERVING_SCOPE = "independently_attested_activation_only"
APPROVED_SERVING_AUTHORIZATION_MODE = "one_time_read_only_demo_surface_serving"
APPROVED_SERVING_AUTHORIZATION_SCOPE = "attested_serving_readiness_only"


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingAuthorizationAttestationInvariantError(
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
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingAuthorizationAttestationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingAuthorizationAttestationInvariantError(
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
        raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingAuthorizationAttestationInvariantError(
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
class DemoSurfacePublicationServingAuthorizationAttestationRecord:
    sequence: int
    attestation_id: str
    serving_authorization_id: str
    readiness_attestation_id: str
    readiness_id: str
    activation_attestation_id: str
    activation_id: str
    consumption_attestation_id: str
    consumption_id: str
    release_authorization_id: str
    publication_id: str
    consumer_id: str
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
    release_authorization_mode: str
    release_authorization_scope: str
    consumption_mode: str
    consumption_scope: str
    activation_mode: str
    activation_scope: str
    serving_mode: str
    serving_scope: str
    serving_authorization_mode: str
    serving_authorization_scope: str
    serving_authorization_record_hash_verified: bool
    readiness_attestation_record_hash_verified: bool
    readiness_record_hash_verified: bool
    activation_attestation_record_hash_verified: bool
    activation_record_hash_verified: bool
    consumption_attestation_record_hash_verified: bool
    consumption_record_hash_verified: bool
    release_authorization_record_hash_verified: bool
    publication_record_hash_verified: bool
    publication_payload_hash_verified: bool
    admission_lineage_verified: bool
    one_time_invocation_verified: bool
    immutable_result_verified: bool
    read_only_boundary_verified: bool
    execution_disabled_boundary_verified: bool
    independent_serving_readiness_attestation_verified: bool
    single_use_release_consumption_verified: bool
    serving_authorization_scope_verified: bool
    serving_authorization_verified: bool
    duplicate_attestation_rejected: bool
    independent_serving_authorization_attestation_performed: bool
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
class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingAuthorizationAttestation:
    schema_version: str
    engine_id: str
    attested_at: str
    attestation_manifest_id: str
    attestation_status: str
    attestation_policy_id: str
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
    source_consumption_attestation_manifest_id: str
    source_consumption_attestation_manifest_hash: str
    source_consumption_manifest_id: str
    source_consumption_manifest_hash: str
    source_release_authorization_manifest_id: str
    source_release_authorization_manifest_hash: str
    source_publication_manifest_id: str
    source_publication_manifest_hash: str
    source_demo_surface_release_manifest_id: str
    source_demo_surface_release_manifest_hash: str
    source_result_admission_manifest_id: str
    source_boundary_id: str
    source_boundary_hash: str
    attestation_record_count: int
    attestation_records: tuple[
        DemoSurfacePublicationServingAuthorizationAttestationRecord,
        ...,
    ]
    all_serving_authorization_record_hashes_verified: bool
    all_readiness_attestation_record_hashes_verified: bool
    all_readiness_record_hashes_verified: bool
    all_activation_attestation_record_hashes_verified: bool
    all_activation_record_hashes_verified: bool
    all_consumption_attestation_record_hashes_verified: bool
    all_consumption_record_hashes_verified: bool
    all_release_authorization_record_hashes_verified: bool
    all_publication_record_hashes_verified: bool
    all_publication_payload_hashes_verified: bool
    all_admission_lineage_verified: bool
    all_one_time_invocations_verified: bool
    all_results_immutable: bool
    all_read_only_boundaries_verified: bool
    all_execution_disabled_boundaries_verified: bool
    all_independent_serving_readiness_attestations_verified: bool
    all_single_use_release_consumptions_verified: bool
    all_serving_authorization_scopes_verified: bool
    all_serving_authorizations_verified: bool
    all_serving_authorizations_independently_attested: bool
    duplicate_attestations_rejected: bool
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


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingAuthorizationAttestationGate:
    def __init__(
        self,
        *,
        authorization_directory: Path | str = DEFAULT_AUTHORIZATION_DIRECTORY,
        attestation_directory: Path | str = DEFAULT_ATTESTATION_DIRECTORY,
    ) -> None:
        self.authorization_directory = Path(authorization_directory)
        self.attestation_directory = Path(attestation_directory)

    def _load_authorization(self) -> dict[str, Any]:
        path = self.authorization_directory / "current.json"
        if not path.exists():
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingAuthorizationAttestationInvariantError(
                f"INT-OIA-026 serving authorization missing: {path}"
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingAuthorizationAttestationInvariantError(
                "INT-OIA-026 serving authorization could not be decoded"
            ) from exc

        manifest_hash = payload.pop("authorization_manifest_hash", None)
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingAuthorizationAttestationInvariantError(
                "INT-OIA-026 authorization manifest hash mismatch"
            )
        payload["authorization_manifest_hash"] = manifest_hash

        required_manifest = {
            "schema_version": "INT-OIA-026",
            "engine_id": "INT-OIA-026",
            "authorization_status": "demo_surface_publication_serving_authorized",
            "serving_authorization_mode": APPROVED_SERVING_AUTHORIZATION_MODE,
            "serving_authorization_scope": APPROVED_SERVING_AUTHORIZATION_SCOPE,
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
            "all_independent_serving_readiness_attestations_verified": True,
            "all_single_use_release_consumptions_verified": True,
            "all_serving_authorization_scopes_verified": True,
            "all_demo_surface_publications_serving_authorized": True,
            "duplicate_authorizations_rejected": True,
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
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingAuthorizationAttestationInvariantError(
                    f"unsafe or incomplete INT-OIA-026 field: {field}"
                )

        records = payload.get("authorization_records")
        if (
            not isinstance(records, list)
            or not records
            or payload.get("authorization_record_count") != len(records)
        ):
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingAuthorizationAttestationInvariantError(
                "INT-OIA-026 authorization records invalid"
            )

        seen_ids: set[str] = set()
        for sequence, raw_record in enumerate(records, start=1):
            if not isinstance(raw_record, Mapping):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingAuthorizationAttestationInvariantError(
                    "authorization record must be a mapping"
                )
            record = dict(raw_record)
            record_hash = record.pop("authorization_record_hash", None)
            if not _valid_hash(record_hash) or stable_hash(record) != record_hash:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingAuthorizationAttestationInvariantError(
                    "INT-OIA-026 authorization-record hash mismatch"
                )
            record["authorization_record_hash"] = record_hash

            authorization_id = record.get("authorization_id")
            if (
                record.get("sequence") != sequence
                or not isinstance(authorization_id, str)
                or not authorization_id
                or authorization_id in seen_ids
            ):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingAuthorizationAttestationInvariantError(
                    "invalid sequence or duplicate serving authorization"
                )
            seen_ids.add(authorization_id)

            required_record = {
                "publication_schema": APPROVED_PUBLICATION_SCHEMA,
                "publication_mode": APPROVED_PUBLICATION_MODE,
                "release_authorization_mode": APPROVED_RELEASE_AUTHORIZATION_MODE,
                "release_authorization_scope": APPROVED_RELEASE_AUTHORIZATION_SCOPE,
                "consumption_mode": APPROVED_CONSUMPTION_MODE,
                "consumption_scope": APPROVED_CONSUMPTION_SCOPE,
                "activation_mode": APPROVED_ACTIVATION_MODE,
                "activation_scope": APPROVED_ACTIVATION_SCOPE,
                "serving_mode": APPROVED_SERVING_MODE,
                "serving_scope": APPROVED_SERVING_SCOPE,
                "serving_authorization_mode": APPROVED_SERVING_AUTHORIZATION_MODE,
                "serving_authorization_scope": APPROVED_SERVING_AUTHORIZATION_SCOPE,
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
                "independent_serving_readiness_attestation_verified": True,
                "single_use_release_consumption_verified": True,
                "serving_authorization_scope_verified": True,
                "duplicate_authorization_rejected": True,
                "demo_surface_publication_serving_authorized": True,
                "signals_created": False,
                "alerts_created": False,
                "qseries_handoff_performed": False,
                "qseries_execution_performed": False,
                "market_order_creation_performed": False,
                "funds_movement_performed": False,
                "portfolio_mutation_performed": False,
                "source_mutation_performed": False,
                "authorization_status": (
                    "independently_attested_read_only_demo_publication_serving_authorized"
                ),
            }
            for field, expected in required_record.items():
                if record.get(field) != expected:
                    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingAuthorizationAttestationInvariantError(
                        f"unsafe INT-OIA-026 authorization-record field: {field}"
                    )

        return payload

    def attest(
        self,
        *,
        attested_at: datetime,
        persist: bool = True,
    ) -> OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingAuthorizationAttestation:
        attested_at = _aware(attested_at, "attested_at")
        source = self._load_authorization()

        records: list[
            DemoSurfacePublicationServingAuthorizationAttestationRecord
        ] = []
        seen_attestation_ids: set[str] = set()

        for sequence, authorization in enumerate(
            source["authorization_records"],
            start=1,
        ):
            attestation_id = stable_hash(
                {
                    "source_serving_authorization_manifest_id": source[
                        "authorization_manifest_id"
                    ],
                    "serving_authorization_id": authorization[
                        "authorization_id"
                    ],
                    "source_serving_authorization_record_hash": authorization[
                        "authorization_record_hash"
                    ],
                    "publication_id": authorization["publication_id"],
                    "attested_at": attested_at.isoformat(),
                }
            )
            if attestation_id in seen_attestation_ids:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingAuthorizationAttestationInvariantError(
                    "duplicate serving authorization attestation id"
                )
            seen_attestation_ids.add(attestation_id)

            body = {
                "sequence": sequence,
                "attestation_id": attestation_id,
                "serving_authorization_id": authorization["authorization_id"],
                "readiness_attestation_id": authorization[
                    "readiness_attestation_id"
                ],
                "readiness_id": authorization["readiness_id"],
                "activation_attestation_id": authorization[
                    "activation_attestation_id"
                ],
                "activation_id": authorization["activation_id"],
                "consumption_attestation_id": authorization[
                    "consumption_attestation_id"
                ],
                "consumption_id": authorization["consumption_id"],
                "release_authorization_id": authorization[
                    "release_authorization_id"
                ],
                "publication_id": authorization["publication_id"],
                "consumer_id": authorization["consumer_id"],
                "source_serving_authorization_record_hash": authorization[
                    "authorization_record_hash"
                ],
                "source_readiness_attestation_record_hash": authorization[
                    "source_readiness_attestation_record_hash"
                ],
                "source_readiness_record_hash": authorization[
                    "source_readiness_record_hash"
                ],
                "source_activation_attestation_record_hash": authorization[
                    "source_activation_attestation_record_hash"
                ],
                "source_activation_record_hash": authorization[
                    "source_activation_record_hash"
                ],
                "source_consumption_attestation_record_hash": authorization[
                    "source_consumption_attestation_record_hash"
                ],
                "source_consumption_record_hash": authorization[
                    "source_consumption_record_hash"
                ],
                "source_release_authorization_record_hash": authorization[
                    "source_release_authorization_record_hash"
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
                "release_authorization_mode": APPROVED_RELEASE_AUTHORIZATION_MODE,
                "release_authorization_scope": APPROVED_RELEASE_AUTHORIZATION_SCOPE,
                "consumption_mode": APPROVED_CONSUMPTION_MODE,
                "consumption_scope": APPROVED_CONSUMPTION_SCOPE,
                "activation_mode": APPROVED_ACTIVATION_MODE,
                "activation_scope": APPROVED_ACTIVATION_SCOPE,
                "serving_mode": APPROVED_SERVING_MODE,
                "serving_scope": APPROVED_SERVING_SCOPE,
                "serving_authorization_mode": APPROVED_SERVING_AUTHORIZATION_MODE,
                "serving_authorization_scope": APPROVED_SERVING_AUTHORIZATION_SCOPE,
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
                "independent_serving_readiness_attestation_verified": True,
                "single_use_release_consumption_verified": True,
                "serving_authorization_scope_verified": True,
                "serving_authorization_verified": True,
                "duplicate_attestation_rejected": True,
                "independent_serving_authorization_attestation_performed": True,
                "signals_created": False,
                "alerts_created": False,
                "qseries_handoff_performed": False,
                "qseries_execution_performed": False,
                "market_order_creation_performed": False,
                "funds_movement_performed": False,
                "portfolio_mutation_performed": False,
                "source_mutation_performed": False,
                "attestation_status": (
                    "read_only_demo_publication_serving_authorization_independently_attested"
                ),
            }
            records.append(
                DemoSurfacePublicationServingAuthorizationAttestationRecord(
                    **body,
                    attestation_record_hash=stable_hash(body),
                )
            )

        manifest_id = stable_hash(
            {
                "source_serving_authorization_manifest_id": source[
                    "authorization_manifest_id"
                ],
                "source_serving_authorization_manifest_hash": source[
                    "authorization_manifest_hash"
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
            "source_serving_authorization_manifest_id": source[
                "authorization_manifest_id"
            ],
            "source_serving_authorization_manifest_hash": source[
                "authorization_manifest_hash"
            ],
            "source_readiness_attestation_manifest_id": source[
                "source_readiness_attestation_manifest_id"
            ],
            "source_readiness_attestation_manifest_hash": source[
                "source_readiness_attestation_manifest_hash"
            ],
            "source_readiness_manifest_id": source[
                "source_readiness_manifest_id"
            ],
            "source_readiness_manifest_hash": source[
                "source_readiness_manifest_hash"
            ],
            "source_activation_attestation_manifest_id": source[
                "source_activation_attestation_manifest_id"
            ],
            "source_activation_attestation_manifest_hash": source[
                "source_activation_attestation_manifest_hash"
            ],
            "source_activation_manifest_id": source[
                "source_activation_manifest_id"
            ],
            "source_activation_manifest_hash": source[
                "source_activation_manifest_hash"
            ],
            "source_consumption_attestation_manifest_id": source[
                "source_consumption_attestation_manifest_id"
            ],
            "source_consumption_attestation_manifest_hash": source[
                "source_consumption_attestation_manifest_hash"
            ],
            "source_consumption_manifest_id": source[
                "source_consumption_manifest_id"
            ],
            "source_consumption_manifest_hash": source[
                "source_consumption_manifest_hash"
            ],
            "source_release_authorization_manifest_id": source[
                "source_release_authorization_manifest_id"
            ],
            "source_release_authorization_manifest_hash": source[
                "source_release_authorization_manifest_hash"
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
            "all_independent_serving_readiness_attestations_verified": True,
            "all_single_use_release_consumptions_verified": True,
            "all_serving_authorization_scopes_verified": True,
            "all_serving_authorizations_verified": True,
            "all_serving_authorizations_independently_attested": True,
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
        manifest = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingAuthorizationAttestation(
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
                    / "authorizations"
                    / record.serving_authorization_id
                    / f"{record.attestation_id}.json",
                    asdict(record),
                )

        return manifest
