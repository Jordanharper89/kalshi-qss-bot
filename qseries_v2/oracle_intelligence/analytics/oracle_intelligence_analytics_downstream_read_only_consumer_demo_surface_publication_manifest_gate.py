from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "INT-OIA-017"
ENGINE_ID = "INT-OIA-017"
POLICY_ID = (
    "oracle.intelligence.analytics.downstream-read-only-consumer."
    "demo-surface-publication-manifest.v1"
)
STATUS_PUBLISHED = "read_only_demo_surface_publication_manifest_published"

DEFAULT_DEMO_RELEASE_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_controlled_demo_surface_release"
)
DEFAULT_PUBLICATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_demo_surface_publication_manifest"
)

APPROVED_PRESENTATION_SCHEMA = "oracle_research_presentation.v1"
APPROVED_DEMO_SURFACE_SCHEMA = "oracle_research_demo_surface.v1"
APPROVED_DEMO_SURFACE_MODE = "read_only_research_demo"
APPROVED_PUBLICATION_SCHEMA = "oracle_research_demo_publication_manifest.v1"
APPROVED_PUBLICATION_MODE = "immutable_read_only_demo_publication"
APPROVED_RESULT_CLASS = "immutable_research_artifact"
APPROVED_RELEASE_MODE = "research_presentation_only"


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestInvariantError(
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
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestInvariantError(
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
        raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestInvariantError(
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
class DemoSurfacePublicationRecord:
    sequence: int
    publication_id: str
    consumer_id: str
    source_demo_surface_release_id: str
    source_demo_surface_release_record_hash: str
    source_presentation_release_attestation_id: str
    research_presentation_release_id: str
    source_result_admission_id: str
    result_attestation_id: str
    invocation_execution_id: str
    invocation_nonce: str
    source_boundary_id: str
    source_boundary_hash: str
    result_hash: str
    admitted_result_hash: str
    source_presentation_payload_hash: str
    source_demo_surface_payload_hash: str
    publication_payload_hash: str
    publication_payload: Any
    presentation_schema: str
    demo_surface_schema: str
    publication_schema: str
    result_class: str
    release_mode: str
    demo_surface_mode: str
    publication_mode: str
    source_release_hash_verified: bool
    demo_surface_payload_hash_verified: bool
    admission_lineage_verified: bool
    one_time_invocation_verified: bool
    immutable_result_verified: bool
    read_only_boundary_verified: bool
    execution_disabled_boundary_verified: bool
    publication_schema_verified: bool
    duplicate_publication_rejected: bool
    demo_surface_released: bool
    publication_manifest_published: bool
    signals_created: bool
    alerts_created: bool
    qseries_handoff_performed: bool
    qseries_execution_performed: bool
    market_order_creation_performed: bool
    funds_movement_performed: bool
    portfolio_mutation_performed: bool
    source_mutation_performed: bool
    publication_status: str
    publication_record_hash: str


@dataclass(frozen=True)
class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifest:
    schema_version: str
    engine_id: str
    published_at: str
    publication_manifest_id: str
    publication_manifest_status: str
    publication_policy_id: str
    publication_schema: str
    publication_mode: str
    source_demo_surface_release_manifest_id: str
    source_demo_surface_release_manifest_hash: str
    source_presentation_release_attestation_manifest_id: str
    source_research_presentation_release_manifest_id: str
    source_result_admission_manifest_id: str
    source_boundary_id: str
    source_boundary_hash: str
    publication_record_count: int
    publication_records: tuple[DemoSurfacePublicationRecord, ...]
    all_source_release_hashes_verified: bool
    all_demo_surface_payload_hashes_verified: bool
    all_admission_lineage_verified: bool
    all_one_time_invocations_verified: bool
    all_results_immutable: bool
    all_read_only_boundaries_verified: bool
    all_execution_disabled_boundaries_verified: bool
    all_publication_schemas_verified: bool
    all_publications_immutable_read_only_demo_only: bool
    duplicate_publications_rejected: bool
    source_boundary_consumed_without_reexecution: bool
    invocation_reexecution_performed: bool
    database_connection_performed: bool
    corpus_read_execution_repeated: bool
    source_mutation_allowed: bool
    source_mutation_performed: bool
    analytic_conclusion_allowed: bool
    research_presentation_released: bool
    demo_surface_released: bool
    publication_manifest_published: bool
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
    publication_artifact_persistence_allowed: bool
    publication_manifest_hash: str


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestGate:
    def __init__(
        self,
        *,
        demo_release_directory: Path | str = DEFAULT_DEMO_RELEASE_DIRECTORY,
        publication_directory: Path | str = DEFAULT_PUBLICATION_DIRECTORY,
    ) -> None:
        self.demo_release_directory = Path(demo_release_directory)
        self.publication_directory = Path(publication_directory)

    def _load_release(self) -> dict[str, Any]:
        path = self.demo_release_directory / "current.json"
        if not path.exists():
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestInvariantError(
                f"INT-OIA-016 release artifact missing: {path}"
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestInvariantError(
                "INT-OIA-016 release artifact could not be decoded"
            ) from exc

        manifest_hash = payload.pop("demo_surface_release_manifest_hash", None)
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestInvariantError(
                "INT-OIA-016 manifest hash mismatch"
            )
        payload["demo_surface_release_manifest_hash"] = manifest_hash

        required_manifest = {
            "schema_version": "INT-OIA-016",
            "engine_id": "INT-OIA-016",
            "demo_surface_release_status": (
                "downstream_read_only_consumer_controlled_demo_surface_released"
            ),
            "all_attestation_hashes_verified": True,
            "all_presentation_payload_hashes_verified": True,
            "all_admission_lineage_verified": True,
            "all_one_time_invocations_verified": True,
            "all_results_immutable": True,
            "all_read_only_boundaries_verified": True,
            "all_execution_disabled_boundaries_verified": True,
            "all_demo_surface_schemas_verified": True,
            "all_releases_read_only_research_demo_only": True,
            "source_boundary_consumed_without_reexecution": True,
            "invocation_reexecution_performed": False,
            "database_connection_performed": False,
            "corpus_read_execution_repeated": False,
            "source_mutation_allowed": False,
            "source_mutation_performed": False,
            "analytic_conclusion_allowed": True,
            "research_presentation_released": True,
            "demo_surface_released": True,
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
            "demo_surface_artifact_persistence_allowed": True,
        }
        for field, expected in required_manifest.items():
            if payload.get(field) != expected:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestInvariantError(
                    f"unsafe or incomplete INT-OIA-016 field: {field}"
                )

        records = payload.get("release_records")
        if (
            not isinstance(records, list)
            or not records
            or payload.get("release_record_count") != len(records)
        ):
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestInvariantError(
                "INT-OIA-016 release records invalid"
            )

        seen_release_ids: set[str] = set()
        for sequence, raw_record in enumerate(records, start=1):
            if not isinstance(raw_record, Mapping):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestInvariantError(
                    "INT-OIA-016 release record must be a mapping"
                )
            record = dict(raw_record)
            record_hash = record.pop("demo_surface_release_record_hash", None)
            if not _valid_hash(record_hash) or stable_hash(record) != record_hash:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestInvariantError(
                    "INT-OIA-016 release-record hash mismatch"
                )
            record["demo_surface_release_record_hash"] = record_hash

            release_id = record.get("demo_surface_release_id")
            if (
                record.get("sequence") != sequence
                or not isinstance(release_id, str)
                or not release_id
                or release_id in seen_release_ids
            ):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestInvariantError(
                    "invalid sequence or duplicate demo-surface release"
                )
            seen_release_ids.add(release_id)

            demo_payload = record.get("demo_surface_payload")
            if not isinstance(demo_payload, Mapping):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestInvariantError(
                    "demo-surface payload must be a mapping"
                )
            if stable_hash(demo_payload) != record.get("demo_surface_payload_hash"):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestInvariantError(
                    "demo-surface payload hash mismatch"
                )

            required_record = {
                "presentation_schema": APPROVED_PRESENTATION_SCHEMA,
                "demo_surface_schema": APPROVED_DEMO_SURFACE_SCHEMA,
                "result_class": APPROVED_RESULT_CLASS,
                "release_mode": APPROVED_RELEASE_MODE,
                "demo_surface_mode": APPROVED_DEMO_SURFACE_MODE,
                "attestation_hash_verified": True,
                "presentation_payload_hash_verified": True,
                "admission_lineage_verified": True,
                "one_time_invocation_verified": True,
                "immutable_result_verified": True,
                "read_only_boundary_verified": True,
                "execution_disabled_boundary_verified": True,
                "demo_surface_schema_verified": True,
                "research_presentation_released": True,
                "demo_surface_released": True,
                "signals_created": False,
                "alerts_created": False,
                "qseries_handoff_performed": False,
                "qseries_execution_performed": False,
                "market_order_creation_performed": False,
                "funds_movement_performed": False,
                "portfolio_mutation_performed": False,
                "source_mutation_performed": False,
                "release_status": "released_to_read_only_research_demo_surface",
            }
            for field, expected in required_record.items():
                if record.get(field) != expected:
                    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestInvariantError(
                        f"unsafe INT-OIA-016 release-record field: {field}"
                    )

            required_payload = {
                "demo_surface_schema": APPROVED_DEMO_SURFACE_SCHEMA,
                "demo_surface_mode": APPROVED_DEMO_SURFACE_MODE,
                "presentation_schema": APPROVED_PRESENTATION_SCHEMA,
                "result_class": APPROVED_RESULT_CLASS,
                "release_mode": APPROVED_RELEASE_MODE,
                "read_only": True,
                "execution_disabled": True,
                "signals_disabled": True,
                "alerts_disabled": True,
                "qseries_handoff_disabled": True,
                "qseries_execution_disabled": True,
                "market_order_creation_disabled": True,
                "funds_movement_disabled": True,
                "portfolio_mutation_disabled": True,
                "source_mutation_disabled": True,
            }
            for field, expected in required_payload.items():
                if demo_payload.get(field) != expected:
                    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestInvariantError(
                        f"unsafe demo-surface payload field: {field}"
                    )

        return payload

    def publish(
        self,
        *,
        published_at: datetime,
        persist: bool = True,
    ) -> OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifest:
        published_at = _aware(published_at, "published_at")
        source = self._load_release()

        records: list[DemoSurfacePublicationRecord] = []
        seen_publication_ids: set[str] = set()

        for sequence, release in enumerate(source["release_records"], start=1):
            publication_payload = {
                "publication_schema": APPROVED_PUBLICATION_SCHEMA,
                "publication_mode": APPROVED_PUBLICATION_MODE,
                "consumer_id": release["consumer_id"],
                "source_demo_surface_release_id": release[
                    "demo_surface_release_id"
                ],
                "source_demo_surface_payload_hash": release[
                    "demo_surface_payload_hash"
                ],
                "presentation_schema": release["presentation_schema"],
                "demo_surface_schema": release["demo_surface_schema"],
                "result_class": release["result_class"],
                "release_mode": release["release_mode"],
                "demo_surface_mode": release["demo_surface_mode"],
                "source_boundary_id": release["source_boundary_id"],
                "source_boundary_hash": release["source_boundary_hash"],
                "result_hash": release["result_hash"],
                "admitted_result_hash": release["admitted_result_hash"],
                "published_demo_surface": release["demo_surface_payload"],
                "immutable": True,
                "read_only": True,
                "execution_disabled": True,
                "signals_disabled": True,
                "alerts_disabled": True,
                "qseries_handoff_disabled": True,
                "qseries_execution_disabled": True,
                "market_order_creation_disabled": True,
                "funds_movement_disabled": True,
                "portfolio_mutation_disabled": True,
                "source_mutation_disabled": True,
            }
            payload_hash = stable_hash(publication_payload)
            publication_id = stable_hash(
                {
                    "source_demo_surface_release_manifest_id": source[
                        "demo_surface_release_manifest_id"
                    ],
                    "source_demo_surface_release_id": release[
                        "demo_surface_release_id"
                    ],
                    "source_demo_surface_release_record_hash": release[
                        "demo_surface_release_record_hash"
                    ],
                    "publication_payload_hash": payload_hash,
                    "published_at": published_at.isoformat(),
                }
            )
            if publication_id in seen_publication_ids:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestInvariantError(
                    "duplicate publication id"
                )
            seen_publication_ids.add(publication_id)

            body = {
                "sequence": sequence,
                "publication_id": publication_id,
                "consumer_id": release["consumer_id"],
                "source_demo_surface_release_id": release[
                    "demo_surface_release_id"
                ],
                "source_demo_surface_release_record_hash": release[
                    "demo_surface_release_record_hash"
                ],
                "source_presentation_release_attestation_id": release[
                    "source_presentation_release_attestation_id"
                ],
                "research_presentation_release_id": release[
                    "research_presentation_release_id"
                ],
                "source_result_admission_id": release[
                    "source_result_admission_id"
                ],
                "result_attestation_id": release["result_attestation_id"],
                "invocation_execution_id": release["invocation_execution_id"],
                "invocation_nonce": release["invocation_nonce"],
                "source_boundary_id": release["source_boundary_id"],
                "source_boundary_hash": release["source_boundary_hash"],
                "result_hash": release["result_hash"],
                "admitted_result_hash": release["admitted_result_hash"],
                "source_presentation_payload_hash": release[
                    "source_presentation_payload_hash"
                ],
                "source_demo_surface_payload_hash": release[
                    "demo_surface_payload_hash"
                ],
                "publication_payload_hash": payload_hash,
                "publication_payload": publication_payload,
                "presentation_schema": APPROVED_PRESENTATION_SCHEMA,
                "demo_surface_schema": APPROVED_DEMO_SURFACE_SCHEMA,
                "publication_schema": APPROVED_PUBLICATION_SCHEMA,
                "result_class": APPROVED_RESULT_CLASS,
                "release_mode": APPROVED_RELEASE_MODE,
                "demo_surface_mode": APPROVED_DEMO_SURFACE_MODE,
                "publication_mode": APPROVED_PUBLICATION_MODE,
                "source_release_hash_verified": True,
                "demo_surface_payload_hash_verified": True,
                "admission_lineage_verified": True,
                "one_time_invocation_verified": True,
                "immutable_result_verified": True,
                "read_only_boundary_verified": True,
                "execution_disabled_boundary_verified": True,
                "publication_schema_verified": True,
                "duplicate_publication_rejected": True,
                "demo_surface_released": True,
                "publication_manifest_published": True,
                "signals_created": False,
                "alerts_created": False,
                "qseries_handoff_performed": False,
                "qseries_execution_performed": False,
                "market_order_creation_performed": False,
                "funds_movement_performed": False,
                "portfolio_mutation_performed": False,
                "source_mutation_performed": False,
                "publication_status": (
                    "published_as_immutable_read_only_demo_manifest"
                ),
            }
            records.append(
                DemoSurfacePublicationRecord(
                    **body,
                    publication_record_hash=stable_hash(body),
                )
            )

        manifest_id = stable_hash(
            {
                "source_demo_surface_release_manifest_id": source[
                    "demo_surface_release_manifest_id"
                ],
                "source_demo_surface_release_manifest_hash": source[
                    "demo_surface_release_manifest_hash"
                ],
                "published_at": published_at.isoformat(),
                "publication_record_hashes": [
                    record.publication_record_hash for record in records
                ],
            }
        )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "published_at": published_at.isoformat(),
            "publication_manifest_id": manifest_id,
            "publication_manifest_status": STATUS_PUBLISHED,
            "publication_policy_id": POLICY_ID,
            "publication_schema": APPROVED_PUBLICATION_SCHEMA,
            "publication_mode": APPROVED_PUBLICATION_MODE,
            "source_demo_surface_release_manifest_id": source[
                "demo_surface_release_manifest_id"
            ],
            "source_demo_surface_release_manifest_hash": source[
                "demo_surface_release_manifest_hash"
            ],
            "source_presentation_release_attestation_manifest_id": source[
                "source_presentation_release_attestation_manifest_id"
            ],
            "source_research_presentation_release_manifest_id": source[
                "source_research_presentation_release_manifest_id"
            ],
            "source_result_admission_manifest_id": source[
                "source_result_admission_manifest_id"
            ],
            "source_boundary_id": source["source_boundary_id"],
            "source_boundary_hash": source["source_boundary_hash"],
            "publication_record_count": len(records),
            "publication_records": tuple(records),
            "all_source_release_hashes_verified": True,
            "all_demo_surface_payload_hashes_verified": True,
            "all_admission_lineage_verified": True,
            "all_one_time_invocations_verified": True,
            "all_results_immutable": True,
            "all_read_only_boundaries_verified": True,
            "all_execution_disabled_boundaries_verified": True,
            "all_publication_schemas_verified": True,
            "all_publications_immutable_read_only_demo_only": True,
            "duplicate_publications_rejected": True,
            "source_boundary_consumed_without_reexecution": True,
            "invocation_reexecution_performed": False,
            "database_connection_performed": False,
            "corpus_read_execution_repeated": False,
            "source_mutation_allowed": False,
            "source_mutation_performed": False,
            "analytic_conclusion_allowed": True,
            "research_presentation_released": True,
            "demo_surface_released": True,
            "publication_manifest_published": True,
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
            "publication_artifact_persistence_allowed": True,
        }

        serializable = dict(body)
        serializable["publication_records"] = [
            asdict(record) for record in records
        ]
        manifest_hash = stable_hash(serializable)
        manifest = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifest(
            **body,
            publication_manifest_hash=manifest_hash,
        )

        if persist:
            payload = asdict(manifest)
            _atomic_write(self.publication_directory / "current.json", payload)
            _atomic_write(
                self.publication_directory
                / "manifests"
                / f"{manifest_id}.json",
                payload,
            )
            for record in records:
                _atomic_write(
                    self.publication_directory
                    / "consumers"
                    / record.consumer_id
                    / f"{record.publication_id}.json",
                    asdict(record),
                )

        return manifest
