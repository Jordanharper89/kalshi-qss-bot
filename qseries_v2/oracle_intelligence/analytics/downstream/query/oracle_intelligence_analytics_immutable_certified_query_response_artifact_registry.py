from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_authorized_consumer_query_response_certification_gate import (
    CertifiedConsumerQueryResponseRecord,
)

SCHEMA_VERSION = "INT-OIA-043"
ENGINE_ID = "INT-OIA-043"
POLICY_ID = (
    "oracle.intelligence.analytics.immutable-certified-query-response."
    "artifact-registry.v1"
)
RESPONSE_ARTIFACT_REGISTRY_SCHEMA_VERSION = (
    "oracle.immutable-certified-query-response-artifact-registry.v1"
)
RESPONSE_ARTIFACT_REGISTRY_STATUS = (
    "certified_query_responses_registered_immutably"
)


class OracleIntelligenceAnalyticsImmutableCertifiedQueryResponseArtifactRegistryInvariantError(
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
            raise OracleIntelligenceAnalyticsImmutableCertifiedQueryResponseArtifactRegistryInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleIntelligenceAnalyticsImmutableCertifiedQueryResponseArtifactRegistryInvariantError(
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


def _verify_record_hash(record: CertifiedConsumerQueryResponseRecord) -> None:
    body = asdict(record)
    supplied = body.pop("query_response_record_hash", None)
    if (
        not isinstance(supplied, str)
        or len(supplied) != 64
        or any(character not in "0123456789abcdef" for character in supplied)
        or stable_hash(body) != supplied
    ):
        raise OracleIntelligenceAnalyticsImmutableCertifiedQueryResponseArtifactRegistryInvariantError(
            "certified query response record hash mismatch"
        )


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(
        _canonical(payload),
        sort_keys=True,
        indent=2,
        ensure_ascii=False,
        allow_nan=False,
    ) + "\n"

    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
        text=True,
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(
            file_descriptor,
            "w",
            encoding="utf-8",
            newline="\n",
        ) as handle:
            handle.write(serialized)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


@dataclass(frozen=True)
class ImmutableCertifiedQueryResponseArtifactEntry:
    sequence: int
    response_artifact_entry_id: str
    query_response_id: str
    query_response_record_hash: str
    source_query_execution_id: str
    source_query_execution_record_hash: str
    source_query_admission_id: str
    source_request_id: str
    consumer_id: str
    requested_projection: str
    source_registry_manifest_id: str
    source_registry_manifest_hash: str
    source_read_result_hash: str
    matched_entry_count: int
    certified_response_item_count: int
    certified_response_items: tuple[dict[str, Any], ...]
    source_response_verified: bool
    response_item_hashes_verified: bool
    source_hashes_verified: bool
    lineage_verified: bool
    deterministic_ordering_verified: bool
    deterministic_replay_verified: bool
    immutable: bool
    read_only: bool
    response_artifact_persisted: bool
    product_registry_mutation_allowed: bool
    product_registry_mutation_performed: bool
    publication_allowed: bool
    publication_performed: bool
    order_execution_allowed: bool
    order_execution_performed: bool
    database_connection_performed: bool
    corpus_read_execution_repeated: bool
    response_artifact_entry_status: str
    response_artifact_entry_hash: str


@dataclass(frozen=True)
class ImmutableCertifiedQueryResponseArtifactRegistryManifest:
    schema_version: str
    engine_id: str
    policy_id: str
    response_artifact_registry_schema_version: str
    response_artifact_registry_status: str
    source_query_response_schema_version: str
    registry_manifest_id: str
    registry_entry_count: int
    registry_entries: tuple[ImmutableCertifiedQueryResponseArtifactEntry, ...]
    all_source_responses_verified: bool
    all_response_item_hashes_verified: bool
    all_source_hashes_verified: bool
    all_lineage_verified: bool
    all_entries_deterministic: bool
    all_entries_replayable: bool
    all_entries_immutable: bool
    all_entries_read_only: bool
    all_response_artifacts_persisted: bool
    duplicate_registry_entries_present: bool
    product_registry_mutation_allowed: bool
    product_registry_mutation_performed: bool
    publication_allowed: bool
    publication_performed: bool
    order_execution_allowed: bool
    order_execution_performed: bool
    database_connection_performed: bool
    corpus_read_execution_repeated: bool
    response_artifact_registry_manifest_hash: str


class OracleIntelligenceAnalyticsImmutableCertifiedQueryResponseArtifactRegistry:
    def __init__(
        self,
        *,
        response_artifact_registry_directory: Path | str,
    ) -> None:
        self._directory = Path(response_artifact_registry_directory)
        self._manifest_path = self._directory / "current.json"
        self._entries_directory = self._directory / "entries"
        self._entries: dict[
            str,
            ImmutableCertifiedQueryResponseArtifactEntry,
        ] = {}
        self._load_existing_manifest()

    def _load_existing_manifest(self) -> None:
        if not self._manifest_path.exists():
            return

        try:
            payload = json.loads(
                self._manifest_path.read_text(encoding="utf-8")
            )
        except Exception as exc:
            raise OracleIntelligenceAnalyticsImmutableCertifiedQueryResponseArtifactRegistryInvariantError(
                "existing response artifact registry manifest is unreadable"
            ) from exc

        supplied_hash = payload.get(
            "response_artifact_registry_manifest_hash"
        )
        body = dict(payload)
        body.pop("response_artifact_registry_manifest_hash", None)
        if stable_hash(body) != supplied_hash:
            raise OracleIntelligenceAnalyticsImmutableCertifiedQueryResponseArtifactRegistryInvariantError(
                "existing response artifact registry manifest hash mismatch"
            )

        for raw_entry in payload.get("registry_entries", []):
            normalized_entry = dict(raw_entry)
            normalized_entry["certified_response_items"] = tuple(
                dict(item)
                for item in normalized_entry.get(
                    "certified_response_items",
                    (),
                )
            )
            entry = ImmutableCertifiedQueryResponseArtifactEntry(
                **normalized_entry
            )
            entry_body = asdict(entry)
            supplied_entry_hash = entry_body.pop(
                "response_artifact_entry_hash"
            )
            if stable_hash(entry_body) != supplied_entry_hash:
                raise OracleIntelligenceAnalyticsImmutableCertifiedQueryResponseArtifactRegistryInvariantError(
                    "existing response artifact entry hash mismatch"
                )
            self._entries[entry.response_artifact_entry_id] = entry

    @staticmethod
    def _verify_response(
        response: CertifiedConsumerQueryResponseRecord,
    ) -> None:
        if not isinstance(response, CertifiedConsumerQueryResponseRecord):
            raise OracleIntelligenceAnalyticsImmutableCertifiedQueryResponseArtifactRegistryInvariantError(
                "response must use the canonical INT-OIA-042 response contract"
            )

        _verify_record_hash(response)

        if response.matched_entry_count != response.certified_response_item_count:
            raise OracleIntelligenceAnalyticsImmutableCertifiedQueryResponseArtifactRegistryInvariantError(
                "matched-entry and certified-response-item counts differ"
            )
        if response.certified_response_item_count != len(
            response.certified_response_items
        ):
            raise OracleIntelligenceAnalyticsImmutableCertifiedQueryResponseArtifactRegistryInvariantError(
                "certified-response-item count mismatch"
            )

        for item in response.certified_response_items:
            if stable_hash(item.projected_entry) != item.projected_entry_hash:
                raise OracleIntelligenceAnalyticsImmutableCertifiedQueryResponseArtifactRegistryInvariantError(
                    "certified response item hash mismatch"
                )

        if not (
            response.source_execution_verified
            and response.projection_policy_verified
            and response.field_allowlist_enforced
            and response.forbidden_fields_absent
            and response.response_item_hashes_verified
            and response.source_hashes_verified
            and response.lineage_verified
            and response.deterministic_ordering_verified
            and response.deterministic_replay_verified
            and response.immutable_read_verified
            and response.response_artifact_persistence_allowed
        ):
            raise OracleIntelligenceAnalyticsImmutableCertifiedQueryResponseArtifactRegistryInvariantError(
                "certified query response is not eligible for immutable persistence"
            )

        if (
            response.registry_mutation_allowed
            or response.registry_mutation_performed
            or response.publication_allowed
            or response.publication_performed
            or response.order_execution_allowed
            or response.order_execution_performed
            or response.database_connection_performed
            or response.corpus_read_execution_repeated
        ):
            raise OracleIntelligenceAnalyticsImmutableCertifiedQueryResponseArtifactRegistryInvariantError(
                "certified query response contains unsafe activity"
            )

    def register(
        self,
        response: CertifiedConsumerQueryResponseRecord,
    ) -> ImmutableCertifiedQueryResponseArtifactRegistryManifest:
        self._verify_response(response)

        response_artifact_entry_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "query_response_id": response.query_response_id,
                "query_response_record_hash": (
                    response.query_response_record_hash
                ),
                "consumer_id": response.consumer_id,
                "requested_projection": response.requested_projection,
            }
        )

        sequence = len(self._entries) + 1
        response_items = tuple(
            {
                "sequence": item.sequence,
                "projected_entry": _canonical(item.projected_entry),
                "projected_entry_hash": item.projected_entry_hash,
            }
            for item in response.certified_response_items
        )

        body = {
            "sequence": sequence,
            "response_artifact_entry_id": response_artifact_entry_id,
            "query_response_id": response.query_response_id,
            "query_response_record_hash": (
                response.query_response_record_hash
            ),
            "source_query_execution_id": response.source_query_execution_id,
            "source_query_execution_record_hash": (
                response.source_query_execution_record_hash
            ),
            "source_query_admission_id": response.source_query_admission_id,
            "source_request_id": response.source_request_id,
            "consumer_id": response.consumer_id,
            "requested_projection": response.requested_projection,
            "source_registry_manifest_id": (
                response.source_registry_manifest_id
            ),
            "source_registry_manifest_hash": (
                response.source_registry_manifest_hash
            ),
            "source_read_result_hash": response.source_read_result_hash,
            "matched_entry_count": response.matched_entry_count,
            "certified_response_item_count": (
                response.certified_response_item_count
            ),
            "certified_response_items": response_items,
            "source_response_verified": True,
            "response_item_hashes_verified": True,
            "source_hashes_verified": True,
            "lineage_verified": True,
            "deterministic_ordering_verified": True,
            "deterministic_replay_verified": True,
            "immutable": True,
            "read_only": True,
            "response_artifact_persisted": True,
            "product_registry_mutation_allowed": False,
            "product_registry_mutation_performed": False,
            "publication_allowed": False,
            "publication_performed": False,
            "order_execution_allowed": False,
            "order_execution_performed": False,
            "database_connection_performed": False,
            "corpus_read_execution_repeated": False,
            "response_artifact_entry_status": (
                "certified_query_response_registered_immutably"
            ),
        }

        entry = ImmutableCertifiedQueryResponseArtifactEntry(
            **body,
            response_artifact_entry_hash=stable_hash(body),
        )

        existing = self._entries.get(response_artifact_entry_id)
        if existing is not None:
            comparable_new = asdict(entry)
            comparable_existing = asdict(existing)

            comparable_new["sequence"] = comparable_existing["sequence"]
            comparable_new.pop("response_artifact_entry_hash", None)
            comparable_existing.pop("response_artifact_entry_hash", None)

            if _canonical(comparable_existing) != _canonical(comparable_new):
                raise OracleIntelligenceAnalyticsImmutableCertifiedQueryResponseArtifactRegistryInvariantError(
                    "response artifact identity collision detected"
                )
            return self.build_manifest()

        self._entries[response_artifact_entry_id] = entry

        entry_path = (
            self._entries_directory
            / f"{response_artifact_entry_id}.json"
        )
        _atomic_write_json(entry_path, asdict(entry))

        manifest = self.build_manifest()
        _atomic_write_json(self._manifest_path, asdict(manifest))
        return manifest

    def build_manifest(
        self,
    ) -> ImmutableCertifiedQueryResponseArtifactRegistryManifest:
        entries = tuple(
            sorted(
                self._entries.values(),
                key=lambda item: (
                    item.sequence,
                    item.consumer_id,
                    item.requested_projection,
                    item.response_artifact_entry_id,
                ),
            )
        )

        registry_manifest_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "response_artifact_entry_ids": [
                    item.response_artifact_entry_id for item in entries
                ],
                "response_artifact_entry_hashes": [
                    item.response_artifact_entry_hash for item in entries
                ],
            }
        )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "policy_id": POLICY_ID,
            "response_artifact_registry_schema_version": (
                RESPONSE_ARTIFACT_REGISTRY_SCHEMA_VERSION
            ),
            "response_artifact_registry_status": (
                RESPONSE_ARTIFACT_REGISTRY_STATUS
            ),
            "source_query_response_schema_version": (
                "oracle.authorized-consumer-query-response-certification.v1"
            ),
            "registry_manifest_id": registry_manifest_id,
            "registry_entry_count": len(entries),
            "registry_entries": entries,
            "all_source_responses_verified": all(
                item.source_response_verified for item in entries
            ),
            "all_response_item_hashes_verified": all(
                item.response_item_hashes_verified for item in entries
            ),
            "all_source_hashes_verified": all(
                item.source_hashes_verified for item in entries
            ),
            "all_lineage_verified": all(
                item.lineage_verified for item in entries
            ),
            "all_entries_deterministic": all(
                item.deterministic_ordering_verified for item in entries
            ),
            "all_entries_replayable": all(
                item.deterministic_replay_verified for item in entries
            ),
            "all_entries_immutable": all(
                item.immutable for item in entries
            ),
            "all_entries_read_only": all(
                item.read_only for item in entries
            ),
            "all_response_artifacts_persisted": all(
                item.response_artifact_persisted for item in entries
            ),
            "duplicate_registry_entries_present": (
                len(entries)
                != len(
                    {
                        item.response_artifact_entry_id
                        for item in entries
                    }
                )
            ),
            "product_registry_mutation_allowed": False,
            "product_registry_mutation_performed": False,
            "publication_allowed": False,
            "publication_performed": False,
            "order_execution_allowed": False,
            "order_execution_performed": False,
            "database_connection_performed": False,
            "corpus_read_execution_repeated": False,
        }

        return ImmutableCertifiedQueryResponseArtifactRegistryManifest(
            **body,
            response_artifact_registry_manifest_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "RESPONSE_ARTIFACT_REGISTRY_SCHEMA_VERSION",
    "RESPONSE_ARTIFACT_REGISTRY_STATUS",
    "ImmutableCertifiedQueryResponseArtifactEntry",
    "ImmutableCertifiedQueryResponseArtifactRegistryManifest",
    "OracleIntelligenceAnalyticsImmutableCertifiedQueryResponseArtifactRegistry",
    "OracleIntelligenceAnalyticsImmutableCertifiedQueryResponseArtifactRegistryInvariantError",
    "stable_hash",
]
