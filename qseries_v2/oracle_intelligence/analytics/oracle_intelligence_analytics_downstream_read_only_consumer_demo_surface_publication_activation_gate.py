from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "INT-OIA-022"
ENGINE_ID = "INT-OIA-022"
POLICY_ID = (
    "oracle.intelligence.analytics.downstream-read-only-consumer."
    "demo-surface-publication-activation.v1"
)
STATUS_ACTIVATED = "attested_demo_surface_publication_activated"

DEFAULT_ATTESTATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_demo_surface_publication_release_authorization_consumption_attestation"
)
DEFAULT_ACTIVATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_demo_surface_publication_activation"
)

APPROVED_PUBLICATION_SCHEMA = "oracle_research_demo_publication_manifest.v1"
APPROVED_PUBLICATION_MODE = "immutable_read_only_demo_publication"
APPROVED_AUTHORIZATION_MODE = "one_time_read_only_demo_publication_release"
APPROVED_AUTHORIZATION_SCOPE = "attested_demo_surface_publication_only"
APPROVED_CONSUMPTION_MODE = "single_use_read_only_release_authorization"
APPROVED_CONSUMPTION_SCOPE = "authorized_demo_surface_publication_only"
APPROVED_ACTIVATION_MODE = "read_only_demo_surface_activation"
APPROVED_ACTIVATION_SCOPE = "independently_attested_publication_only"


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationActivationInvariantError(
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
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationActivationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationActivationInvariantError(
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
        raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationActivationInvariantError(
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
class DemoSurfacePublicationActivationRecord:
    sequence: int
    activation_id: str
    consumption_attestation_id: str
    consumption_id: str
    authorization_id: str
    publication_id: str
    consumer_id: str
    source_consumption_attestation_record_hash: str
    source_consumption_record_hash: str
    source_authorization_record_hash: str
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
    activation_mode: str
    activation_scope: str
    consumption_attestation_record_hash_verified: bool
    consumption_record_hash_verified: bool
    authorization_record_hash_verified: bool
    publication_record_hash_verified: bool
    publication_payload_hash_verified: bool
    admission_lineage_verified: bool
    one_time_invocation_verified: bool
    immutable_result_verified: bool
    read_only_boundary_verified: bool
    execution_disabled_boundary_verified: bool
    independent_consumption_attestation_verified: bool
    single_use_consumption_verified: bool
    activation_scope_verified: bool
    duplicate_activation_rejected: bool
    demo_surface_publication_activated: bool
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
class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationActivation:
    schema_version: str
    engine_id: str
    activated_at: str
    activation_manifest_id: str
    activation_status: str
    activation_policy_id: str
    activation_mode: str
    activation_scope: str
    source_consumption_attestation_manifest_id: str
    source_consumption_attestation_manifest_hash: str
    source_consumption_manifest_id: str
    source_consumption_manifest_hash: str
    source_authorization_manifest_id: str
    source_authorization_manifest_hash: str
    source_publication_manifest_id: str
    source_publication_manifest_hash: str
    source_demo_surface_release_manifest_id: str
    source_demo_surface_release_manifest_hash: str
    source_result_admission_manifest_id: str
    source_boundary_id: str
    source_boundary_hash: str
    activation_record_count: int
    activation_records: tuple[DemoSurfacePublicationActivationRecord, ...]
    all_consumption_attestation_record_hashes_verified: bool
    all_consumption_record_hashes_verified: bool
    all_authorization_record_hashes_verified: bool
    all_publication_record_hashes_verified: bool
    all_publication_payload_hashes_verified: bool
    all_admission_lineage_verified: bool
    all_one_time_invocations_verified: bool
    all_results_immutable: bool
    all_read_only_boundaries_verified: bool
    all_execution_disabled_boundaries_verified: bool
    all_independent_consumption_attestations_verified: bool
    all_single_use_consumptions_verified: bool
    all_activation_scopes_verified: bool
    all_demo_surface_publications_activated: bool
    duplicate_activations_rejected: bool
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


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationActivationGate:
    def __init__(
        self,
        *,
        attestation_directory: Path | str = DEFAULT_ATTESTATION_DIRECTORY,
        activation_directory: Path | str = DEFAULT_ACTIVATION_DIRECTORY,
    ) -> None:
        self.attestation_directory = Path(attestation_directory)
        self.activation_directory = Path(activation_directory)

    def _load_attestation(self) -> dict[str, Any]:
        path = self.attestation_directory / "current.json"
        if not path.exists():
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationActivationInvariantError(
                f"INT-OIA-021 attestation artifact missing: {path}"
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationActivationInvariantError(
                "INT-OIA-021 attestation artifact could not be decoded"
            ) from exc

        manifest_hash = payload.pop("attestation_manifest_hash", None)
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationActivationInvariantError(
                "INT-OIA-021 attestation manifest hash mismatch"
            )
        payload["attestation_manifest_hash"] = manifest_hash

        required_manifest = {
            "schema_version": "INT-OIA-021",
            "engine_id": "INT-OIA-021",
            "attestation_status": (
                "demo_surface_publication_release_authorization_consumption_independently_attested"
            ),
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
        for field, expected in required_manifest.items():
            if payload.get(field) != expected:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationActivationInvariantError(
                    f"unsafe or incomplete INT-OIA-021 field: {field}"
                )

        records = payload.get("attestation_records")
        if (
            not isinstance(records, list)
            or not records
            or payload.get("attestation_record_count") != len(records)
        ):
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationActivationInvariantError(
                "INT-OIA-021 attestation records invalid"
            )

        seen_ids: set[str] = set()
        for sequence, raw_record in enumerate(records, start=1):
            if not isinstance(raw_record, Mapping):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationActivationInvariantError(
                    "attestation record must be a mapping"
                )
            record = dict(raw_record)
            record_hash = record.pop("attestation_record_hash", None)
            if not _valid_hash(record_hash) or stable_hash(record) != record_hash:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationActivationInvariantError(
                    "INT-OIA-021 attestation-record hash mismatch"
                )
            record["attestation_record_hash"] = record_hash

            attestation_id = record.get("attestation_id")
            if (
                record.get("sequence") != sequence
                or not isinstance(attestation_id, str)
                or not attestation_id
                or attestation_id in seen_ids
            ):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationActivationInvariantError(
                    "invalid sequence or duplicate attestation"
                )
            seen_ids.add(attestation_id)

            required_record = {
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
            for field, expected in required_record.items():
                if record.get(field) != expected:
                    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationActivationInvariantError(
                        f"unsafe INT-OIA-021 attestation-record field: {field}"
                    )

        return payload

    def activate(
        self,
        *,
        activated_at: datetime,
        persist: bool = True,
    ) -> OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationActivation:
        activated_at = _aware(activated_at, "activated_at")
        source = self._load_attestation()

        records: list[DemoSurfacePublicationActivationRecord] = []
        seen_activation_ids: set[str] = set()

        for sequence, attestation in enumerate(
            source["attestation_records"],
            start=1,
        ):
            activation_id = stable_hash(
                {
                    "source_consumption_attestation_manifest_id": source[
                        "attestation_manifest_id"
                    ],
                    "consumption_attestation_id": attestation["attestation_id"],
                    "source_consumption_attestation_record_hash": attestation[
                        "attestation_record_hash"
                    ],
                    "publication_id": attestation["publication_id"],
                    "activated_at": activated_at.isoformat(),
                    "activation_mode": APPROVED_ACTIVATION_MODE,
                    "activation_scope": APPROVED_ACTIVATION_SCOPE,
                }
            )
            if activation_id in seen_activation_ids:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationActivationInvariantError(
                    "duplicate activation id"
                )
            seen_activation_ids.add(activation_id)

            body = {
                "sequence": sequence,
                "activation_id": activation_id,
                "consumption_attestation_id": attestation["attestation_id"],
                "consumption_id": attestation["consumption_id"],
                "authorization_id": attestation["authorization_id"],
                "publication_id": attestation["publication_id"],
                "consumer_id": attestation["consumer_id"],
                "source_consumption_attestation_record_hash": attestation[
                    "attestation_record_hash"
                ],
                "source_consumption_record_hash": attestation[
                    "source_consumption_record_hash"
                ],
                "source_authorization_record_hash": attestation[
                    "source_authorization_record_hash"
                ],
                "source_publication_record_hash": attestation[
                    "source_publication_record_hash"
                ],
                "source_demo_surface_release_id": attestation[
                    "source_demo_surface_release_id"
                ],
                "source_result_admission_id": attestation[
                    "source_result_admission_id"
                ],
                "invocation_execution_id": attestation[
                    "invocation_execution_id"
                ],
                "invocation_nonce": attestation["invocation_nonce"],
                "source_boundary_id": attestation["source_boundary_id"],
                "source_boundary_hash": attestation["source_boundary_hash"],
                "result_hash": attestation["result_hash"],
                "admitted_result_hash": attestation["admitted_result_hash"],
                "publication_payload_hash": attestation[
                    "publication_payload_hash"
                ],
                "publication_schema": APPROVED_PUBLICATION_SCHEMA,
                "publication_mode": APPROVED_PUBLICATION_MODE,
                "authorization_mode": APPROVED_AUTHORIZATION_MODE,
                "authorization_scope": APPROVED_AUTHORIZATION_SCOPE,
                "consumption_mode": APPROVED_CONSUMPTION_MODE,
                "consumption_scope": APPROVED_CONSUMPTION_SCOPE,
                "activation_mode": APPROVED_ACTIVATION_MODE,
                "activation_scope": APPROVED_ACTIVATION_SCOPE,
                "consumption_attestation_record_hash_verified": True,
                "consumption_record_hash_verified": True,
                "authorization_record_hash_verified": True,
                "publication_record_hash_verified": True,
                "publication_payload_hash_verified": True,
                "admission_lineage_verified": True,
                "one_time_invocation_verified": True,
                "immutable_result_verified": True,
                "read_only_boundary_verified": True,
                "execution_disabled_boundary_verified": True,
                "independent_consumption_attestation_verified": True,
                "single_use_consumption_verified": True,
                "activation_scope_verified": True,
                "duplicate_activation_rejected": True,
                "demo_surface_publication_activated": True,
                "signals_created": False,
                "alerts_created": False,
                "qseries_handoff_performed": False,
                "qseries_execution_performed": False,
                "market_order_creation_performed": False,
                "funds_movement_performed": False,
                "portfolio_mutation_performed": False,
                "source_mutation_performed": False,
                "activation_status": (
                    "independently_attested_read_only_demo_publication_activated"
                ),
            }
            records.append(
                DemoSurfacePublicationActivationRecord(
                    **body,
                    activation_record_hash=stable_hash(body),
                )
            )

        manifest_id = stable_hash(
            {
                "source_consumption_attestation_manifest_id": source[
                    "attestation_manifest_id"
                ],
                "source_consumption_attestation_manifest_hash": source[
                    "attestation_manifest_hash"
                ],
                "activated_at": activated_at.isoformat(),
                "activation_record_hashes": [
                    record.activation_record_hash for record in records
                ],
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
            "activation_scope": APPROVED_ACTIVATION_SCOPE,
            "source_consumption_attestation_manifest_id": source[
                "attestation_manifest_id"
            ],
            "source_consumption_attestation_manifest_hash": source[
                "attestation_manifest_hash"
            ],
            "source_consumption_manifest_id": source[
                "source_consumption_manifest_id"
            ],
            "source_consumption_manifest_hash": source[
                "source_consumption_manifest_hash"
            ],
            "source_authorization_manifest_id": source[
                "source_authorization_manifest_id"
            ],
            "source_authorization_manifest_hash": source[
                "source_authorization_manifest_hash"
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
            "activation_record_count": len(records),
            "activation_records": tuple(records),
            "all_consumption_attestation_record_hashes_verified": True,
            "all_consumption_record_hashes_verified": True,
            "all_authorization_record_hashes_verified": True,
            "all_publication_record_hashes_verified": True,
            "all_publication_payload_hashes_verified": True,
            "all_admission_lineage_verified": True,
            "all_one_time_invocations_verified": True,
            "all_results_immutable": True,
            "all_read_only_boundaries_verified": True,
            "all_execution_disabled_boundaries_verified": True,
            "all_independent_consumption_attestations_verified": True,
            "all_single_use_consumptions_verified": True,
            "all_activation_scopes_verified": True,
            "all_demo_surface_publications_activated": True,
            "duplicate_activations_rejected": True,
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
        serializable["activation_records"] = [
            asdict(record) for record in records
        ]
        manifest_hash = stable_hash(serializable)
        manifest = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationActivation(
            **body,
            activation_manifest_hash=manifest_hash,
        )

        if persist:
            payload = asdict(manifest)
            _atomic_write(self.activation_directory / "current.json", payload)
            _atomic_write(
                self.activation_directory
                / "manifests"
                / f"{manifest_id}.json",
                payload,
            )
            for record in records:
                _atomic_write(
                    self.activation_directory
                    / "publications"
                    / record.publication_id
                    / f"{record.activation_id}.json",
                    asdict(record),
                )

        return manifest
