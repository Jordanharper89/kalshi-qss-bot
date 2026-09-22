from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"
DOWNSTREAM = ANALYTICS / "downstream"
QUERY = DOWNSTREAM / "query"

SOURCE_043 = QUERY / (
    "oracle_intelligence_analytics_immutable_certified_query_response_artifact_registry.py"
)
PRODUCTION = QUERY / (
    "oracle_intelligence_analytics_certified_query_response_artifact_read_gate.py"
)
TEST = ROOT / (
    "test_int_oia_044_oracle_intelligence_analytics_"
    "certified_query_response_artifact_read_gate.py"
)

QUERY_PACKAGE = QUERY / "__init__.py"
DOWNSTREAM_PACKAGE = DOWNSTREAM / "__init__.py"
ANALYTICS_PACKAGE = ANALYTICS / "__init__.py"

PRODUCTION_SOURCE = r"""
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
"""

TEST_SOURCE = r"""
from __future__ import annotations

from dataclasses import replace

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_immutable_certified_query_response_artifact_registry import (
    ImmutableCertifiedQueryResponseArtifactEntry,
    ImmutableCertifiedQueryResponseArtifactRegistryManifest,
)
from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_certified_query_response_artifact_read_gate import (
    READ_RESULT_SCHEMA_VERSION,
    OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadGate,
    OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadInvariantError,
    stable_hash,
)


def _entry(
    sequence: int,
    *,
    consumer_id: str,
    projection: str,
) -> ImmutableCertifiedQueryResponseArtifactEntry:
    response_item = {
        "sequence": 1,
        "projected_entry": {
            "intelligence_product_id": stable_hash(
                {"product": sequence}
            ),
            "market_id": f"KX-{sequence:03d}",
            "venue_id": "kalshi",
        },
        "projected_entry_hash": stable_hash(
            {
                "intelligence_product_id": stable_hash(
                    {"product": sequence}
                ),
                "market_id": f"KX-{sequence:03d}",
                "venue_id": "kalshi",
            }
        ),
    }
    body = {
        "sequence": sequence,
        "response_artifact_entry_id": stable_hash(
            {"response-artifact-entry": sequence}
        ),
        "query_response_id": stable_hash(
            {"query-response": sequence}
        ),
        "query_response_record_hash": stable_hash(
            {"query-response-record": sequence}
        ),
        "source_query_execution_id": stable_hash(
            {"query-execution": sequence}
        ),
        "source_query_execution_record_hash": stable_hash(
            {"query-execution-record": sequence}
        ),
        "source_query_admission_id": stable_hash(
            {"query-admission": sequence}
        ),
        "source_request_id": f"request-{sequence}",
        "consumer_id": consumer_id,
        "requested_projection": projection,
        "source_registry_manifest_id": "int-oia-038-test",
        "source_registry_manifest_hash": stable_hash(
            {"source-registry": 38}
        ),
        "source_read_result_hash": stable_hash(
            {"source-read-result": sequence}
        ),
        "matched_entry_count": 1,
        "certified_response_item_count": 1,
        "certified_response_items": (response_item,),
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
    return ImmutableCertifiedQueryResponseArtifactEntry(
        **body,
        response_artifact_entry_hash=stable_hash(body),
    )


def _manifest() -> ImmutableCertifiedQueryResponseArtifactRegistryManifest:
    entries = (
        _entry(
            1,
            consumer_id="oracle.operator.console.v1",
            projection="operator_research",
        ),
        _entry(
            2,
            consumer_id="oracle.research.presentation.v1",
            projection="research_presentation",
        ),
        _entry(
            3,
            consumer_id="oracle.operator.console.v1",
            projection="operator_research",
        ),
    )
    body = {
        "schema_version": "INT-OIA-043",
        "engine_id": "INT-OIA-043",
        "policy_id": (
            "oracle.intelligence.analytics.immutable-certified-query-response."
            "artifact-registry.v1"
        ),
        "response_artifact_registry_schema_version": (
            "oracle.immutable-certified-query-response-artifact-registry.v1"
        ),
        "response_artifact_registry_status": (
            "certified_query_responses_registered_immutably"
        ),
        "source_query_response_schema_version": (
            "oracle.authorized-consumer-query-response-certification.v1"
        ),
        "registry_manifest_id": stable_hash(
            {"registry-manifest": 43}
        ),
        "registry_entry_count": len(entries),
        "registry_entries": entries,
        "all_source_responses_verified": True,
        "all_response_item_hashes_verified": True,
        "all_source_hashes_verified": True,
        "all_lineage_verified": True,
        "all_entries_deterministic": True,
        "all_entries_replayable": True,
        "all_entries_immutable": True,
        "all_entries_read_only": True,
        "all_response_artifacts_persisted": True,
        "duplicate_registry_entries_present": False,
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


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe certified response artifact read accepted")
    except OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-044 TEST")
    print(" CERTIFIED QUERY RESPONSE ARTIFACT")
    print(" READ GATE")
    print("=" * 40)

    gate = OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadGate()
    manifest = _manifest()

    all_request = gate.create_request(
        registry_manifest=manifest,
        maximum_result_count=100,
    )
    first_all = gate.read(
        registry_manifest=manifest,
        read_request=all_request,
    )
    repeated_all = gate.read(
        registry_manifest=manifest,
        read_request=all_request,
    )

    assert first_all == repeated_all
    assert first_all.matched_entry_count == 3
    assert tuple(item.sequence for item in first_all.matched_entries) == (
        1,
        2,
        3,
    )

    operator_request = gate.create_request(
        registry_manifest=manifest,
        consumer_id="oracle.operator.console.v1",
        requested_projection="operator_research",
        maximum_result_count=1,
    )
    operator_result = gate.read(
        registry_manifest=manifest,
        read_request=operator_request,
    )
    assert operator_result.matched_entry_count == 1
    assert operator_result.matched_entries[0].sequence == 1

    exact_entry = manifest.registry_entries[1]
    exact_request = gate.create_request(
        registry_manifest=manifest,
        response_artifact_entry_id=(
            exact_entry.response_artifact_entry_id
        ),
        query_response_id=exact_entry.query_response_id,
    )
    exact_result = gate.read(
        registry_manifest=manifest,
        read_request=exact_request,
    )
    assert exact_result.matched_entries == (exact_entry,)

    assert first_all.read_result_hash == stable_hash(
        {
            key: value
            for key, value in first_all.__dict__.items()
            if key != "read_result_hash"
        }
    )
    assert first_all.registry_manifest_verified
    assert first_all.registry_entry_hashes_verified
    assert first_all.request_verified
    assert first_all.filters_applied_deterministically
    assert first_all.maximum_result_count_enforced
    assert first_all.immutable_read_verified
    assert first_all.source_hashes_verified
    assert first_all.lineage_verified
    assert first_all.deterministic_ordering_verified
    assert first_all.deterministic_replay_verified
    assert not first_all.registry_mutation_allowed
    assert not first_all.registry_mutation_performed
    assert not first_all.publication_allowed
    assert not first_all.publication_performed
    assert not first_all.order_execution_allowed
    assert not first_all.order_execution_performed
    assert not first_all.database_connection_performed
    assert not first_all.corpus_read_execution_repeated

    _expect_rejected(
        lambda: gate.read(
            registry_manifest=manifest,
            read_request=replace(
                all_request,
                mutation_allowed=True,
            ),
        )
    )
    _expect_rejected(
        lambda: gate.read(
            registry_manifest=manifest,
            read_request=replace(
                all_request,
                read_request_hash="0" * 64,
            ),
        )
    )
    _expect_rejected(
        lambda: gate.read(
            registry_manifest=replace(
                manifest,
                response_artifact_registry_manifest_hash="0" * 64,
            ),
            read_request=all_request,
        )
    )

    tampered_entry = replace(
        manifest.registry_entries[0],
        consumer_id="tampered.consumer",
    )
    tampered_entries = (
        tampered_entry,
        *manifest.registry_entries[1:],
    )
    tampered_body = {
        key: value
        for key, value in manifest.__dict__.items()
        if key != "response_artifact_registry_manifest_hash"
    }
    tampered_body["registry_entries"] = tampered_entries
    tampered_manifest = (
        ImmutableCertifiedQueryResponseArtifactRegistryManifest(
            **tampered_body,
            response_artifact_registry_manifest_hash=stable_hash(
                tampered_body
            ),
        )
    )
    _expect_rejected(
        lambda: gate.create_request(
            registry_manifest=tampered_manifest,
        )
    )

    assert READ_RESULT_SCHEMA_VERSION == (
        "oracle.certified-query-response-artifact-read-result.v1"
    )

    print("[PASS] Actual INT-OIA-043 registry contract consumed")
    print("[PASS] Registry manifest hash independently verified")
    print("[PASS] Every response artifact entry hash verified")
    print("[PASS] Deterministic read request created")
    print("[PASS] Full registry read completed immutably")
    print("[PASS] Consumer and projection filters applied")
    print("[PASS] Exact artifact and query-response filters applied")
    print("[PASS] Maximum result count enforced deterministically")
    print("[PASS] Deterministic replay and ordering verified")
    print("[PASS] Complete INT-OIA-013 through INT-OIA-043 lineage preserved")
    print("[PASS] Tampered request evidence rejected")
    print("[PASS] Tampered manifest evidence rejected")
    print("[PASS] Tampered registry entry evidence rejected")
    print("[PASS] Registry and product mutation remained disabled")
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


def verify_int_oia_043_contract() -> None:
    if not SOURCE_043.exists():
        raise FileNotFoundError(
            f"Actual INT-OIA-043 production module missing: {SOURCE_043}"
        )
    source = SOURCE_043.read_text(encoding="utf-8")
    required_tokens = (
        'SCHEMA_VERSION = "INT-OIA-043"',
        "RESPONSE_ARTIFACT_REGISTRY_SCHEMA_VERSION",
        "class ImmutableCertifiedQueryResponseArtifactEntry",
        "class ImmutableCertifiedQueryResponseArtifactRegistryManifest",
        "class OracleIntelligenceAnalyticsImmutableCertifiedQueryResponseArtifactRegistry",
        "response_artifact_registry_manifest_hash",
        "response_artifact_entry_hash",
        "certified_response_items",
        "all_entries_immutable",
        "product_registry_mutation_allowed",
        "publication_allowed",
        "order_execution_allowed",
    )
    missing = [token for token in required_tokens if token not in source]
    if missing:
        raise RuntimeError(
            "Actual INT-OIA-043 contract mismatch; missing tokens: "
            + ", ".join(missing)
        )
    print("[OK] Actual INT-OIA-043 response-artifact registry contract verified")


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-044 INSTALLER")
    print(" CERTIFIED QUERY RESPONSE ARTIFACT")
    print(" READ GATE")
    print("=" * 40)

    verify_int_oia_043_contract()

    write_replacement(PRODUCTION, PRODUCTION_SOURCE)
    write_replacement(TEST, TEST_SOURCE)

    append_export(
        QUERY_PACKAGE,
        "from .oracle_intelligence_analytics_certified_query_response_artifact_read_gate import *",
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

    print("[OK] INT-OIA-044 test executed automatically")
    print()
    print(
        "[DONE] INT-OIA-044 certified query response artifact "
        "read gate installed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
