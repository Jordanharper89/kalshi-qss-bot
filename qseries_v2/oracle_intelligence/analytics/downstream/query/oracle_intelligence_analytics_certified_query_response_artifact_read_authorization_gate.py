from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_certified_query_response_artifact_read_gate import (
    CertifiedQueryResponseArtifactReadResult,
)

SCHEMA_VERSION = "INT-OIA-045"
ENGINE_ID = "INT-OIA-045"
POLICY_ID = (
    "oracle.intelligence.analytics.certified-query-response-artifact."
    "read-authorization-gate.v1"
)
AUTHORIZATION_SCHEMA_VERSION = (
    "oracle.certified-query-response-artifact-read-authorization.v1"
)
AUTHORIZATION_STATUS = (
    "certified_query_response_artifact_read_authorized"
)


class OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError(
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
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError(
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
        raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError(
            f"{label} hash mismatch"
        )


@dataclass(frozen=True)
class CertifiedQueryResponseArtifactReadAuthorization:
    authorization_id: str
    source_read_result_id: str
    source_read_result_hash: str
    source_read_request_id: str
    source_read_request_hash: str
    source_registry_manifest_id: str
    source_registry_manifest_hash: str
    authorized_consumer_id: str
    authorized_projection: str
    authorized_entry_count: int
    authorized_response_artifact_entry_ids: tuple[str, ...]
    authorized_query_response_ids: tuple[str, ...]
    read_result_verified: bool
    registry_manifest_verified: bool
    registry_entry_hashes_verified: bool
    request_verified: bool
    non_empty_result_verified: bool
    single_consumer_verified: bool
    single_projection_verified: bool
    consumer_identity_verified: bool
    projection_identity_verified: bool
    immutable_read_verified: bool
    source_hashes_verified: bool
    lineage_verified: bool
    deterministic_ordering_verified: bool
    deterministic_replay_verified: bool
    read_authorized: bool
    registry_mutation_allowed: bool
    registry_mutation_performed: bool
    publication_allowed: bool
    publication_performed: bool
    order_execution_allowed: bool
    order_execution_performed: bool
    database_connection_performed: bool
    corpus_read_execution_repeated: bool
    authorization_status: str
    authorization_hash: str


class OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationGate:
    @staticmethod
    def _verify_read_result(
        read_result: CertifiedQueryResponseArtifactReadResult,
    ) -> None:
        if not isinstance(
            read_result,
            CertifiedQueryResponseArtifactReadResult,
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError(
                "read result must use the canonical INT-OIA-044 contract"
            )

        _verify_hash_record(
            read_result,
            "read_result_hash",
            "certified query response artifact read result",
        )

        if read_result.matched_entry_count != len(
            read_result.matched_entries
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError(
                "read result entry count mismatch"
            )

        if read_result.matched_entry_count < 1:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError(
                "empty read results cannot be authorized"
            )

        seen_entry_ids: set[str] = set()
        previous_order_key: tuple[int, str, str, str] | None = None
        for entry in read_result.matched_entries:
            _verify_hash_record(
                entry,
                "response_artifact_entry_hash",
                "certified query response artifact entry",
            )
            if entry.response_artifact_entry_id in seen_entry_ids:
                raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError(
                    "duplicate response artifact entry detected"
                )
            seen_entry_ids.add(entry.response_artifact_entry_id)

            order_key = (
                entry.sequence,
                entry.consumer_id,
                entry.requested_projection,
                entry.response_artifact_entry_id,
            )
            if previous_order_key is not None and order_key < previous_order_key:
                raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError(
                    "read result ordering is not canonical"
                )
            previous_order_key = order_key

            if not (
                entry.source_response_verified
                and entry.response_item_hashes_verified
                and entry.source_hashes_verified
                and entry.lineage_verified
                and entry.deterministic_ordering_verified
                and entry.deterministic_replay_verified
                and entry.immutable
                and entry.read_only
                and entry.response_artifact_persisted
            ):
                raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError(
                    "read result contains an uncertified artifact entry"
                )

            if (
                entry.product_registry_mutation_allowed
                or entry.product_registry_mutation_performed
                or entry.publication_allowed
                or entry.publication_performed
                or entry.order_execution_allowed
                or entry.order_execution_performed
                or entry.database_connection_performed
                or entry.corpus_read_execution_repeated
            ):
                raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError(
                    "read result contains an unsafe artifact entry"
                )

        if not (
            read_result.registry_manifest_verified
            and read_result.registry_entry_hashes_verified
            and read_result.request_verified
            and read_result.filters_applied_deterministically
            and read_result.maximum_result_count_enforced
            and read_result.immutable_read_verified
            and read_result.source_hashes_verified
            and read_result.lineage_verified
            and read_result.deterministic_ordering_verified
            and read_result.deterministic_replay_verified
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError(
                "read result is not eligible for authorization"
            )

        if (
            read_result.registry_mutation_allowed
            or read_result.registry_mutation_performed
            or read_result.publication_allowed
            or read_result.publication_performed
            or read_result.order_execution_allowed
            or read_result.order_execution_performed
            or read_result.database_connection_performed
            or read_result.corpus_read_execution_repeated
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError(
                "read result contains forbidden activity"
            )

    def authorize(
        self,
        *,
        read_result: CertifiedQueryResponseArtifactReadResult,
        authorized_consumer_id: str,
        authorized_projection: str,
    ) -> CertifiedQueryResponseArtifactReadAuthorization:
        self._verify_read_result(read_result)

        if (
            not isinstance(authorized_consumer_id, str)
            or not authorized_consumer_id.strip()
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError(
                "authorized_consumer_id must be a non-empty string"
            )
        if (
            not isinstance(authorized_projection, str)
            or not authorized_projection.strip()
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError(
                "authorized_projection must be a non-empty string"
            )

        consumers = {
            entry.consumer_id
            for entry in read_result.matched_entries
        }
        projections = {
            entry.requested_projection
            for entry in read_result.matched_entries
        }

        if len(consumers) != 1:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError(
                "read result must contain exactly one consumer identity"
            )
        if len(projections) != 1:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError(
                "read result must contain exactly one projection identity"
            )
        if consumers != {authorized_consumer_id}:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError(
                "authorized consumer identity does not match the read result"
            )
        if projections != {authorized_projection}:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError(
                "authorized projection identity does not match the read result"
            )

        entry_ids = tuple(
            entry.response_artifact_entry_id
            for entry in read_result.matched_entries
        )
        query_response_ids = tuple(
            entry.query_response_id
            for entry in read_result.matched_entries
        )

        authorization_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_read_result_id": read_result.read_result_id,
                "source_read_result_hash": read_result.read_result_hash,
                "authorized_consumer_id": authorized_consumer_id,
                "authorized_projection": authorized_projection,
                "authorized_response_artifact_entry_ids": entry_ids,
                "authorized_query_response_ids": query_response_ids,
            }
        )

        body = {
            "authorization_id": authorization_id,
            "source_read_result_id": read_result.read_result_id,
            "source_read_result_hash": read_result.read_result_hash,
            "source_read_request_id": read_result.source_read_request_id,
            "source_read_request_hash": read_result.source_read_request_hash,
            "source_registry_manifest_id": (
                read_result.source_registry_manifest_id
            ),
            "source_registry_manifest_hash": (
                read_result.source_registry_manifest_hash
            ),
            "authorized_consumer_id": authorized_consumer_id,
            "authorized_projection": authorized_projection,
            "authorized_entry_count": len(entry_ids),
            "authorized_response_artifact_entry_ids": entry_ids,
            "authorized_query_response_ids": query_response_ids,
            "read_result_verified": True,
            "registry_manifest_verified": True,
            "registry_entry_hashes_verified": True,
            "request_verified": True,
            "non_empty_result_verified": True,
            "single_consumer_verified": True,
            "single_projection_verified": True,
            "consumer_identity_verified": True,
            "projection_identity_verified": True,
            "immutable_read_verified": True,
            "source_hashes_verified": True,
            "lineage_verified": True,
            "deterministic_ordering_verified": True,
            "deterministic_replay_verified": True,
            "read_authorized": True,
            "registry_mutation_allowed": False,
            "registry_mutation_performed": False,
            "publication_allowed": False,
            "publication_performed": False,
            "order_execution_allowed": False,
            "order_execution_performed": False,
            "database_connection_performed": False,
            "corpus_read_execution_repeated": False,
            "authorization_status": AUTHORIZATION_STATUS,
        }

        return CertifiedQueryResponseArtifactReadAuthorization(
            **body,
            authorization_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "AUTHORIZATION_SCHEMA_VERSION",
    "AUTHORIZATION_STATUS",
    "CertifiedQueryResponseArtifactReadAuthorization",
    "OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationGate",
    "OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError",
    "stable_hash",
]
