from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_immutable_certified_query_response_artifact_registry import (
    ImmutableCertifiedQueryResponseArtifactEntry,
    ImmutableCertifiedQueryResponseArtifactRegistryManifest,
)

SCHEMA_VERSION = "INT-OIA-044"
ENGINE_ID = "INT-OIA-044"
POLICY_ID = (
    "oracle.intelligence.analytics.certified-query-response-artifact."
    "read-gate.v1"
)
READ_REQUEST_SCHEMA_VERSION = (
    "oracle.certified-query-response-artifact-read-request.v1"
)
READ_RESULT_SCHEMA_VERSION = (
    "oracle.certified-query-response-artifact-read-result.v1"
)
READ_RESULT_STATUS = "certified_query_response_artifacts_read_immutably"

ALLOWED_FILTER_FIELDS = (
    "response_artifact_entry_id",
    "query_response_id",
    "consumer_id",
    "requested_projection",
)


class OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadInvariantError(
    RuntimeError
):
    pass


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadInvariantError(
        f"unsupported non-deterministic value type: {type(value)!r}"
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


def _verify_hash_record(
    value: Any,
    hash_field: str,
    label: str,
) -> None:
    body = asdict(value)
    supplied = body.pop(hash_field, None)
    if (
        not isinstance(supplied, str)
        or len(supplied) != 64
        or any(character not in "0123456789abcdef" for character in supplied)
        or stable_hash(body) != supplied
    ):
        raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadInvariantError(
            f"{label} hash mismatch"
        )


@dataclass(frozen=True)
class CertifiedQueryResponseArtifactReadRequest:
    read_request_id: str
    source_registry_manifest_id: str
    source_registry_manifest_hash: str
    response_artifact_entry_id: str | None
    query_response_id: str | None
    consumer_id: str | None
    requested_projection: str | None
    maximum_result_count: int
    read_only: bool
    mutation_allowed: bool
    publication_allowed: bool
    order_execution_allowed: bool
    database_connection_allowed: bool
    read_request_hash: str


@dataclass(frozen=True)
class CertifiedQueryResponseArtifactReadResult:
    read_result_id: str
    source_read_request_id: str
    source_read_request_hash: str
    source_registry_manifest_id: str
    source_registry_manifest_hash: str
    matched_entry_count: int
    matched_entries: tuple[ImmutableCertifiedQueryResponseArtifactEntry, ...]
    registry_manifest_verified: bool
    registry_entry_hashes_verified: bool
    request_verified: bool
    filters_applied_deterministically: bool
    maximum_result_count_enforced: bool
    immutable_read_verified: bool
    source_hashes_verified: bool
    lineage_verified: bool
    deterministic_ordering_verified: bool
    deterministic_replay_verified: bool
    registry_mutation_allowed: bool
    registry_mutation_performed: bool
    publication_allowed: bool
    publication_performed: bool
    order_execution_allowed: bool
    order_execution_performed: bool
    database_connection_performed: bool
    corpus_read_execution_repeated: bool
    read_result_status: str
    read_result_hash: str


class OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadGate:
    @staticmethod
    def create_request(
        *,
        registry_manifest: ImmutableCertifiedQueryResponseArtifactRegistryManifest,
        response_artifact_entry_id: str | None = None,
        query_response_id: str | None = None,
        consumer_id: str | None = None,
        requested_projection: str | None = None,
        maximum_result_count: int = 100,
    ) -> CertifiedQueryResponseArtifactReadRequest:
        OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadGate._verify_manifest(
            registry_manifest
        )

        filters = {
            "response_artifact_entry_id": response_artifact_entry_id,
            "query_response_id": query_response_id,
            "consumer_id": consumer_id,
            "requested_projection": requested_projection,
        }
        for field_name, field_value in filters.items():
            if field_value is not None and (
                not isinstance(field_value, str) or not field_value.strip()
            ):
                raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadInvariantError(
                    f"{field_name} must be a non-empty string when supplied"
                )

        if (
            not isinstance(maximum_result_count, int)
            or isinstance(maximum_result_count, bool)
            or maximum_result_count < 1
            or maximum_result_count > 1000
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadInvariantError(
                "maximum_result_count must be an integer from 1 through 1000"
            )

        read_request_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_registry_manifest_id": (
                    registry_manifest.registry_manifest_id
                ),
                "source_registry_manifest_hash": (
                    registry_manifest.response_artifact_registry_manifest_hash
                ),
                "filters": filters,
                "maximum_result_count": maximum_result_count,
            }
        )

        body = {
            "read_request_id": read_request_id,
            "source_registry_manifest_id": (
                registry_manifest.registry_manifest_id
            ),
            "source_registry_manifest_hash": (
                registry_manifest.response_artifact_registry_manifest_hash
            ),
            "response_artifact_entry_id": response_artifact_entry_id,
            "query_response_id": query_response_id,
            "consumer_id": consumer_id,
            "requested_projection": requested_projection,
            "maximum_result_count": maximum_result_count,
            "read_only": True,
            "mutation_allowed": False,
            "publication_allowed": False,
            "order_execution_allowed": False,
            "database_connection_allowed": False,
        }
        return CertifiedQueryResponseArtifactReadRequest(
            **body,
            read_request_hash=stable_hash(body),
        )

    @staticmethod
    def _verify_manifest(
        manifest: ImmutableCertifiedQueryResponseArtifactRegistryManifest,
    ) -> None:
        if not isinstance(
            manifest,
            ImmutableCertifiedQueryResponseArtifactRegistryManifest,
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadInvariantError(
                "registry manifest must use the canonical INT-OIA-043 contract"
            )

        _verify_hash_record(
            manifest,
            "response_artifact_registry_manifest_hash",
            "response artifact registry manifest",
        )

        if manifest.registry_entry_count != len(manifest.registry_entries):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadInvariantError(
                "registry manifest entry count mismatch"
            )

        seen_ids: set[str] = set()
        for entry in manifest.registry_entries:
            if not isinstance(
                entry,
                ImmutableCertifiedQueryResponseArtifactEntry,
            ):
                raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadInvariantError(
                    "registry manifest contains a non-canonical entry"
                )
            _verify_hash_record(
                entry,
                "response_artifact_entry_hash",
                "response artifact registry entry",
            )
            if entry.response_artifact_entry_id in seen_ids:
                raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadInvariantError(
                    "duplicate response artifact entry identity detected"
                )
            seen_ids.add(entry.response_artifact_entry_id)

        if not (
            manifest.all_source_responses_verified
            and manifest.all_response_item_hashes_verified
            and manifest.all_source_hashes_verified
            and manifest.all_lineage_verified
            and manifest.all_entries_deterministic
            and manifest.all_entries_replayable
            and manifest.all_entries_immutable
            and manifest.all_entries_read_only
            and manifest.all_response_artifacts_persisted
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadInvariantError(
                "registry manifest is not eligible for certified reads"
            )

        if (
            manifest.duplicate_registry_entries_present
            or manifest.product_registry_mutation_allowed
            or manifest.product_registry_mutation_performed
            or manifest.publication_allowed
            or manifest.publication_performed
            or manifest.order_execution_allowed
            or manifest.order_execution_performed
            or manifest.database_connection_performed
            or manifest.corpus_read_execution_repeated
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadInvariantError(
                "registry manifest contains unsafe activity"
            )

    @staticmethod
    def _verify_request(
        request: CertifiedQueryResponseArtifactReadRequest,
        manifest: ImmutableCertifiedQueryResponseArtifactRegistryManifest,
    ) -> None:
        if not isinstance(
            request,
            CertifiedQueryResponseArtifactReadRequest,
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadInvariantError(
                "read request must use the canonical INT-OIA-044 request contract"
            )

        _verify_hash_record(request, "read_request_hash", "read request")

        if (
            request.source_registry_manifest_id
            != manifest.registry_manifest_id
            or request.source_registry_manifest_hash
            != manifest.response_artifact_registry_manifest_hash
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadInvariantError(
                "read request registry identity mismatch"
            )

        if not request.read_only:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadInvariantError(
                "read request must remain read-only"
            )

        if (
            request.mutation_allowed
            or request.publication_allowed
            or request.order_execution_allowed
            or request.database_connection_allowed
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadInvariantError(
                "read request enables a forbidden capability"
            )

    def read(
        self,
        *,
        registry_manifest: ImmutableCertifiedQueryResponseArtifactRegistryManifest,
        read_request: CertifiedQueryResponseArtifactReadRequest,
    ) -> CertifiedQueryResponseArtifactReadResult:
        self._verify_manifest(registry_manifest)
        self._verify_request(read_request, registry_manifest)

        matched: list[ImmutableCertifiedQueryResponseArtifactEntry] = []
        for entry in registry_manifest.registry_entries:
            if (
                read_request.response_artifact_entry_id is not None
                and entry.response_artifact_entry_id
                != read_request.response_artifact_entry_id
            ):
                continue
            if (
                read_request.query_response_id is not None
                and entry.query_response_id != read_request.query_response_id
            ):
                continue
            if (
                read_request.consumer_id is not None
                and entry.consumer_id != read_request.consumer_id
            ):
                continue
            if (
                read_request.requested_projection is not None
                and entry.requested_projection
                != read_request.requested_projection
            ):
                continue
            matched.append(entry)

        matched_entries = tuple(
            sorted(
                matched,
                key=lambda item: (
                    item.sequence,
                    item.consumer_id,
                    item.requested_projection,
                    item.response_artifact_entry_id,
                ),
            )[: read_request.maximum_result_count]
        )

        read_result_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_read_request_id": read_request.read_request_id,
                "source_read_request_hash": read_request.read_request_hash,
                "source_registry_manifest_id": (
                    registry_manifest.registry_manifest_id
                ),
                "source_registry_manifest_hash": (
                    registry_manifest.response_artifact_registry_manifest_hash
                ),
                "matched_entry_hashes": [
                    item.response_artifact_entry_hash
                    for item in matched_entries
                ],
            }
        )

        body = {
            "read_result_id": read_result_id,
            "source_read_request_id": read_request.read_request_id,
            "source_read_request_hash": read_request.read_request_hash,
            "source_registry_manifest_id": (
                registry_manifest.registry_manifest_id
            ),
            "source_registry_manifest_hash": (
                registry_manifest.response_artifact_registry_manifest_hash
            ),
            "matched_entry_count": len(matched_entries),
            "matched_entries": matched_entries,
            "registry_manifest_verified": True,
            "registry_entry_hashes_verified": True,
            "request_verified": True,
            "filters_applied_deterministically": True,
            "maximum_result_count_enforced": True,
            "immutable_read_verified": True,
            "source_hashes_verified": True,
            "lineage_verified": True,
            "deterministic_ordering_verified": True,
            "deterministic_replay_verified": True,
            "registry_mutation_allowed": False,
            "registry_mutation_performed": False,
            "publication_allowed": False,
            "publication_performed": False,
            "order_execution_allowed": False,
            "order_execution_performed": False,
            "database_connection_performed": False,
            "corpus_read_execution_repeated": False,
            "read_result_status": READ_RESULT_STATUS,
        }

        return CertifiedQueryResponseArtifactReadResult(
            **body,
            read_result_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "READ_REQUEST_SCHEMA_VERSION",
    "READ_RESULT_SCHEMA_VERSION",
    "READ_RESULT_STATUS",
    "ALLOWED_FILTER_FIELDS",
    "CertifiedQueryResponseArtifactReadRequest",
    "CertifiedQueryResponseArtifactReadResult",
    "OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadGate",
    "OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadInvariantError",
    "stable_hash",
]
