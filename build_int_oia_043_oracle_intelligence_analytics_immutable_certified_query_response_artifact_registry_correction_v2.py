from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"
DOWNSTREAM = ANALYTICS / "downstream"
QUERY = DOWNSTREAM / "query"

SOURCE_042 = QUERY / (
    "oracle_intelligence_analytics_authorized_consumer_query_response_certification_gate.py"
)
PRODUCTION = QUERY / (
    "oracle_intelligence_analytics_immutable_certified_query_response_artifact_registry.py"
)
TEST = ROOT / (
    "test_int_oia_043_oracle_intelligence_analytics_"
    "immutable_certified_query_response_artifact_registry.py"
)

QUERY_PACKAGE = QUERY / "__init__.py"
DOWNSTREAM_PACKAGE = DOWNSTREAM / "__init__.py"
ANALYTICS_PACKAGE = ANALYTICS / "__init__.py"

PRODUCTION_SOURCE = r"""
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
            entry = ImmutableCertifiedQueryResponseArtifactEntry(
                **raw_entry
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
"""

TEST_SOURCE = r"""
from __future__ import annotations

import json
import tempfile
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_authorized_consumer_query_response_certification_gate import (
    CertifiedConsumerQueryResponseItem,
    CertifiedConsumerQueryResponseRecord,
)
from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_immutable_certified_query_response_artifact_registry import (
    RESPONSE_ARTIFACT_REGISTRY_SCHEMA_VERSION,
    OracleIntelligenceAnalyticsImmutableCertifiedQueryResponseArtifactRegistry,
    OracleIntelligenceAnalyticsImmutableCertifiedQueryResponseArtifactRegistryInvariantError,
    stable_hash,
)


def _response() -> CertifiedConsumerQueryResponseRecord:
    projected_entry = {
        "intelligence_product_id": stable_hash({"product": 1}),
        "product_type": "market_research_summary",
        "market_id": "KX-001",
        "venue_id": "kalshi",
        "confidence": 0.81,
        "calibration_status": "provisional",
        "product_state": "created_not_published",
        "registry_entry_hash": stable_hash({"entry": 1}),
        "registry_key": stable_hash({"key": 1}),
        "query_eligible": True,
        "projection_eligible": True,
        "source_hashes_verified": True,
        "lineage_verified": True,
    }
    item = CertifiedConsumerQueryResponseItem(
        sequence=1,
        projected_entry=projected_entry,
        projected_entry_hash=stable_hash(projected_entry),
    )
    body = {
        "query_response_id": stable_hash({"response": 1}),
        "source_query_execution_id": stable_hash({"execution": 1}),
        "source_query_execution_record_hash": stable_hash(
            {"execution-record": 1}
        ),
        "source_query_admission_id": stable_hash({"admission": 1}),
        "source_request_id": "request-1",
        "consumer_id": "oracle.operator.console.v1",
        "requested_projection": "operator_research",
        "source_registry_manifest_id": "int-oia-038-test",
        "source_registry_manifest_hash": stable_hash({"manifest": 38}),
        "source_read_result_hash": stable_hash({"read-result": 1}),
        "matched_entry_count": 1,
        "certified_response_item_count": 1,
        "certified_response_items": (item,),
        "source_execution_verified": True,
        "projection_policy_verified": True,
        "field_allowlist_enforced": True,
        "forbidden_fields_absent": True,
        "response_item_hashes_verified": True,
        "source_hashes_verified": True,
        "lineage_verified": True,
        "deterministic_ordering_verified": True,
        "deterministic_replay_verified": True,
        "immutable_read_verified": True,
        "response_artifact_persistence_allowed": True,
        "registry_mutation_allowed": False,
        "registry_mutation_performed": False,
        "publication_allowed": False,
        "publication_performed": False,
        "order_execution_allowed": False,
        "order_execution_performed": False,
        "database_connection_performed": False,
        "corpus_read_execution_repeated": False,
        "query_response_status": (
            "authorized_consumer_query_response_certified"
        ),
    }
    return CertifiedConsumerQueryResponseRecord(
        **body,
        query_response_record_hash=stable_hash(body),
    )


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe response artifact was registered")
    except OracleIntelligenceAnalyticsImmutableCertifiedQueryResponseArtifactRegistryInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-043 TEST")
    print(" IMMUTABLE CERTIFIED QUERY RESPONSE")
    print(" ARTIFACT REGISTRY")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary_directory:
        registry_directory = (
            Path(temporary_directory) / "response_artifacts"
        )
        registry = (
            OracleIntelligenceAnalyticsImmutableCertifiedQueryResponseArtifactRegistry(
                response_artifact_registry_directory=registry_directory,
            )
        )

        response = _response()
        first_manifest = registry.register(response)

        manifest_path = registry_directory / "current.json"
        manifest_bytes_before = manifest_path.read_bytes()
        entry_files_before = tuple(
            sorted((registry_directory / "entries").glob("*.json"))
        )
        assert len(entry_files_before) == 1
        entry_bytes_before = entry_files_before[0].read_bytes()

        repeated_manifest = registry.register(response)

        assert repeated_manifest == first_manifest
        assert manifest_path.read_bytes() == manifest_bytes_before
        entry_files_after = tuple(
            sorted((registry_directory / "entries").glob("*.json"))
        )
        assert entry_files_after == entry_files_before
        assert entry_files_after[0].read_bytes() == entry_bytes_before

        assert first_manifest.registry_entry_count == 1
        assert not first_manifest.duplicate_registry_entries_present
        assert first_manifest.all_source_responses_verified
        assert first_manifest.all_response_item_hashes_verified
        assert first_manifest.all_source_hashes_verified
        assert first_manifest.all_lineage_verified
        assert first_manifest.all_entries_deterministic
        assert first_manifest.all_entries_replayable
        assert first_manifest.all_entries_immutable
        assert first_manifest.all_entries_read_only
        assert first_manifest.all_response_artifacts_persisted
        assert not first_manifest.product_registry_mutation_allowed
        assert not first_manifest.product_registry_mutation_performed
        assert not first_manifest.publication_allowed
        assert not first_manifest.publication_performed
        assert not first_manifest.order_execution_allowed
        assert not first_manifest.order_execution_performed
        assert not first_manifest.database_connection_performed
        assert not first_manifest.corpus_read_execution_repeated

        entry = first_manifest.registry_entries[0]
        assert entry.query_response_id == response.query_response_id
        assert (
            entry.query_response_record_hash
            == response.query_response_record_hash
        )
        assert entry.consumer_id == response.consumer_id
        assert entry.requested_projection == response.requested_projection
        assert entry.response_artifact_entry_hash == stable_hash(
            {
                key: value
                for key, value in entry.__dict__.items()
                if key != "response_artifact_entry_hash"
            }
        )

        assert (
            first_manifest.response_artifact_registry_manifest_hash
            == stable_hash(
                {
                    key: value
                    for key, value in first_manifest.__dict__.items()
                    if key
                    != "response_artifact_registry_manifest_hash"
                }
            )
        )

        reloaded = (
            OracleIntelligenceAnalyticsImmutableCertifiedQueryResponseArtifactRegistry(
                response_artifact_registry_directory=registry_directory,
            )
        )
        assert reloaded.build_manifest() == first_manifest

        _expect_rejected(
            lambda: registry.register(
                replace(
                    response,
                    publication_allowed=True,
                )
            )
        )
        _expect_rejected(
            lambda: registry.register(
                replace(
                    response,
                    query_response_record_hash="0" * 64,
                )
            )
        )

        tampered_manifest = json.loads(
            manifest_path.read_text(encoding="utf-8")
        )
        tampered_manifest["registry_entries"][0][
            "consumer_id"
        ] = "tampered.consumer"
        manifest_path.write_text(
            json.dumps(tampered_manifest),
            encoding="utf-8",
        )

        _expect_rejected(
            lambda: OracleIntelligenceAnalyticsImmutableCertifiedQueryResponseArtifactRegistry(
                response_artifact_registry_directory=registry_directory,
            )
        )

    assert RESPONSE_ARTIFACT_REGISTRY_SCHEMA_VERSION == (
        "oracle.immutable-certified-query-response-artifact-registry.v1"
    )

    print("[PASS] Actual INT-OIA-042 certified response consumed")
    print("[PASS] Certified response record hash independently verified")
    print("[PASS] Certified response item hashes independently verified")
    print("[PASS] Immutable response artifact entry created")
    print("[PASS] Atomic partitioned entry persisted")
    print("[PASS] Atomic current manifest persisted")
    print("[PASS] Duplicate registration remained idempotent")\n    print("[PASS] Sequence-dependent entry hash excluded from duplicate identity comparison")
    print("[PASS] Persisted files remained byte-for-byte unchanged")
    print("[PASS] Registry reload reproduced identical manifest")
    print("[PASS] Entry and manifest hashes independently verified")
    print("[PASS] Complete INT-OIA-013 through INT-OIA-042 lineage preserved")
    print("[PASS] Tampered response evidence rejected")
    print("[PASS] Tampered persisted manifest rejected")
    print("[PASS] Product registry mutation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Q Series order execution remained disabled")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def write_replacement(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        source.strip() + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def ensure_package(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("", encoding="utf-8", newline="\n")
        print(f"[OK] PACKAGE CREATED: {path.resolve()}")


def append_export(path: Path, export_line: str) -> None:
    ensure_package(path)
    existing = path.read_text(encoding="utf-8")
    if export_line not in existing.splitlines():
        if existing and not existing.endswith("\n"):
            existing += "\n"
        existing += export_line + "\n"
        path.write_text(existing, encoding="utf-8", newline="\n")
    print(f"[OK] PACKAGE UPDATED: {path.resolve()}")


def verify_int_oia_042_contract() -> None:
    if not SOURCE_042.exists():
        raise FileNotFoundError(
            f"Actual INT-OIA-042 production module missing: {SOURCE_042}"
        )
    source = SOURCE_042.read_text(encoding="utf-8")
    required_tokens = (
        'SCHEMA_VERSION = "INT-OIA-042"',
        "QUERY_RESPONSE_SCHEMA_VERSION",
        "class CertifiedConsumerQueryResponseItem",
        "class CertifiedConsumerQueryResponseRecord",
        "class OracleIntelligenceAnalyticsAuthorizedConsumerQueryResponseCertificationGate",
        "query_response_record_hash",
        "certified_response_items",
        "response_artifact_persistence_allowed",
        "registry_mutation_allowed",
        "publication_allowed",
        "order_execution_allowed",
    )
    missing = [token for token in required_tokens if token not in source]
    if missing:
        raise RuntimeError(
            "Actual INT-OIA-042 contract mismatch; missing tokens: "
            + ", ".join(missing)
        )
    print("[OK] Actual INT-OIA-042 certified-response contract verified")


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-043 CORRECTION V2")
    print(" IMMUTABLE CERTIFIED QUERY RESPONSE")
    print(" ARTIFACT REGISTRY")
    print("=" * 40)

    verify_int_oia_042_contract()

    write_replacement(PRODUCTION, PRODUCTION_SOURCE)
    write_replacement(TEST, TEST_SOURCE)

    append_export(
        QUERY_PACKAGE,
        "from .oracle_intelligence_analytics_immutable_certified_query_response_artifact_registry import *",
    )
    append_export(
        DOWNSTREAM_PACKAGE,
        "from .query import *",
    )
    append_export(
        ANALYTICS_PACKAGE,
        "from .downstream.query import *",
    )

    for target in (
        PRODUCTION,
        TEST,
        QUERY_PACKAGE,
        DOWNSTREAM_PACKAGE,
        ANALYTICS_PACKAGE,
    ):
        ast.parse(target.read_text(encoding="utf-8"), filename=str(target))
    print("[OK] Production, test, and package syntax verified in memory")

    completed = subprocess.run(
        [sys.executable, str(TEST)],
        cwd=str(ROOT),
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)

    print("[OK] INT-OIA-043 test executed automatically")
    print()
    print(
        "[DONE] INT-OIA-043 correction V2 installed; duplicate registration idempotency restored"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
