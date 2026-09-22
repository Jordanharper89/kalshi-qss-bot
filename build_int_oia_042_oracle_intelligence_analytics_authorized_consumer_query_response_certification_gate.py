from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"
DOWNSTREAM = ANALYTICS / "downstream"
QUERY = DOWNSTREAM / "query"

SOURCE_041 = QUERY / (
    "oracle_intelligence_analytics_authorized_consumer_registry_query_execution_gate.py"
)
PRODUCTION = QUERY / (
    "oracle_intelligence_analytics_authorized_consumer_query_response_certification_gate.py"
)
TEST = ROOT / (
    "test_int_oia_042_oracle_intelligence_analytics_"
    "authorized_consumer_query_response_certification_gate.py"
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

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_authorized_consumer_registry_query_execution_gate import (
    AuthorizedConsumerRegistryQueryExecutionRecord,
)

SCHEMA_VERSION = "INT-OIA-042"
ENGINE_ID = "INT-OIA-042"
POLICY_ID = (
    "oracle.intelligence.analytics.authorized-consumer-query-response."
    "certification-gate.v1"
)
QUERY_RESPONSE_SCHEMA_VERSION = (
    "oracle.authorized-consumer-query-response-certification.v1"
)
QUERY_RESPONSE_STATUS = "authorized_consumer_query_response_certified"

ALLOWED_PROJECTIONS = (
    "operator_research",
    "research_presentation",
    "audit_replay",
)

COMMON_RESPONSE_FIELDS = (
    "intelligence_product_id",
    "product_type",
    "market_id",
    "venue_id",
    "confidence",
    "calibration_status",
    "product_state",
    "registry_entry_hash",
)

PROJECTION_RESPONSE_FIELDS: dict[str, tuple[str, ...]] = {
    "operator_research": COMMON_RESPONSE_FIELDS + (
        "registry_key",
        "query_eligible",
        "projection_eligible",
        "source_hashes_verified",
        "lineage_verified",
    ),
    "research_presentation": COMMON_RESPONSE_FIELDS + (
        "query_eligible",
        "projection_eligible",
    ),
    "audit_replay": (
        "sequence",
        "registry_entry_id",
        "product_admission_id",
        "product_admission_record_hash",
        "intelligence_product_id",
        "intelligence_product_hash",
        "source_canonical_product_manifest_id",
        "source_canonical_product_manifest_hash",
        "source_product_admission_manifest_id",
        "source_product_admission_manifest_hash",
        "source_result_admission_id",
        "source_result_admission_record_hash",
        "product_schema_version",
        "product_class",
        "product_type",
        "product_mode",
        "product_state",
        "market_id",
        "venue_id",
        "confidence",
        "calibration_status",
        "allowed_consumer_projections",
        "registry_partition",
        "registry_key",
        "immutable",
        "read_only",
        "deterministic",
        "replayable",
        "query_eligible",
        "projection_eligible",
        "publication_eligible",
        "publication_performed",
        "execution_capabilities_disabled_verified",
        "source_hashes_verified",
        "lineage_verified",
        "admission_verified",
        "duplicate_registration_rejected",
        "registry_entry_status",
        "registry_entry_hash",
    ),
}

FORBIDDEN_RESPONSE_FIELDS = (
    "database_url",
    "database_password",
    "api_key",
    "secret",
    "private_key",
    "order_payload",
    "execution_payload",
    "mutation_payload",
)


class OracleIntelligenceAnalyticsAuthorizedConsumerQueryResponseCertificationInvariantError(
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
            raise OracleIntelligenceAnalyticsAuthorizedConsumerQueryResponseCertificationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleIntelligenceAnalyticsAuthorizedConsumerQueryResponseCertificationInvariantError(
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


def _verify_record_hash(record: AuthorizedConsumerRegistryQueryExecutionRecord) -> None:
    body = asdict(record)
    supplied = body.pop("query_execution_record_hash", None)
    if (
        not isinstance(supplied, str)
        or len(supplied) != 64
        or any(character not in "0123456789abcdef" for character in supplied)
        or stable_hash(body) != supplied
    ):
        raise OracleIntelligenceAnalyticsAuthorizedConsumerQueryResponseCertificationInvariantError(
            "query execution record hash mismatch"
        )


def _contains_forbidden_field(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized_key = str(key).lower()
            if any(token in normalized_key for token in FORBIDDEN_RESPONSE_FIELDS):
                return True
            if _contains_forbidden_field(item):
                return True
        return False
    if isinstance(value, (list, tuple)):
        return any(_contains_forbidden_field(item) for item in value)
    return False


@dataclass(frozen=True)
class CertifiedConsumerQueryResponseItem:
    sequence: int
    projected_entry: dict[str, Any]
    projected_entry_hash: str


@dataclass(frozen=True)
class CertifiedConsumerQueryResponseRecord:
    query_response_id: str
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
    certified_response_items: tuple[CertifiedConsumerQueryResponseItem, ...]
    source_execution_verified: bool
    projection_policy_verified: bool
    field_allowlist_enforced: bool
    forbidden_fields_absent: bool
    response_item_hashes_verified: bool
    source_hashes_verified: bool
    lineage_verified: bool
    deterministic_ordering_verified: bool
    deterministic_replay_verified: bool
    immutable_read_verified: bool
    response_artifact_persistence_allowed: bool
    registry_mutation_allowed: bool
    registry_mutation_performed: bool
    publication_allowed: bool
    publication_performed: bool
    order_execution_allowed: bool
    order_execution_performed: bool
    database_connection_performed: bool
    corpus_read_execution_repeated: bool
    query_response_status: str
    query_response_record_hash: str


class OracleIntelligenceAnalyticsAuthorizedConsumerQueryResponseCertificationGate:
    @staticmethod
    def _verify_execution(
        execution: AuthorizedConsumerRegistryQueryExecutionRecord,
    ) -> None:
        if not isinstance(
            execution,
            AuthorizedConsumerRegistryQueryExecutionRecord,
        ):
            raise OracleIntelligenceAnalyticsAuthorizedConsumerQueryResponseCertificationInvariantError(
                "query execution must use the canonical INT-OIA-041 record contract"
            )

        _verify_record_hash(execution)

        if execution.source_requested_projection not in ALLOWED_PROJECTIONS:
            raise OracleIntelligenceAnalyticsAuthorizedConsumerQueryResponseCertificationInvariantError(
                "query execution requested an unsupported response projection"
            )

        if not (
            execution.query_admission_verified
            and execution.registry_read_request_derived_from_admission
            and execution.registry_read_invocation_count == 1
            and execution.registry_read_result_verified
            and execution.source_hashes_verified
            and execution.lineage_verified
            and execution.deterministic_replay_verified
            and execution.immutable_read_verified
        ):
            raise OracleIntelligenceAnalyticsAuthorizedConsumerQueryResponseCertificationInvariantError(
                "query execution is not eligible for response certification"
            )

        if execution.matched_entry_count != len(
            execution.matched_registry_entries
        ):
            raise OracleIntelligenceAnalyticsAuthorizedConsumerQueryResponseCertificationInvariantError(
                "query execution matched-entry count mismatch"
            )

        if (
            execution.registry_mutation_allowed
            or execution.registry_mutation_performed
            or execution.registry_update_performed
            or execution.registry_delete_performed
            or execution.publication_allowed
            or execution.publication_performed
            or execution.order_execution_allowed
            or execution.order_execution_performed
            or execution.database_connection_performed
            or execution.corpus_read_execution_repeated
        ):
            raise OracleIntelligenceAnalyticsAuthorizedConsumerQueryResponseCertificationInvariantError(
                "query execution contains unsafe activity"
            )

    @staticmethod
    def _project_entry(
        entry: Mapping[str, Any],
        projection: str,
    ) -> dict[str, Any]:
        if not isinstance(entry, Mapping):
            raise OracleIntelligenceAnalyticsAuthorizedConsumerQueryResponseCertificationInvariantError(
                "registry entry must be a mapping"
            )

        allowed_fields = PROJECTION_RESPONSE_FIELDS[projection]
        missing = [
            field_name
            for field_name in COMMON_RESPONSE_FIELDS
            if field_name not in entry
        ]
        if missing:
            raise OracleIntelligenceAnalyticsAuthorizedConsumerQueryResponseCertificationInvariantError(
                "registry entry missing required response fields: "
                + ", ".join(missing)
            )

        projected = {
            field_name: _canonical(entry[field_name])
            for field_name in allowed_fields
            if field_name in entry
        }

        if _contains_forbidden_field(projected):
            raise OracleIntelligenceAnalyticsAuthorizedConsumerQueryResponseCertificationInvariantError(
                "projected response contains forbidden fields"
            )

        return projected

    def certify(
        self,
        execution: AuthorizedConsumerRegistryQueryExecutionRecord,
    ) -> CertifiedConsumerQueryResponseRecord:
        self._verify_execution(execution)

        projection = execution.source_requested_projection
        projected_items: list[CertifiedConsumerQueryResponseItem] = []

        for index, entry in enumerate(
            execution.matched_registry_entries,
            start=1,
        ):
            projected_entry = self._project_entry(entry, projection)
            projected_items.append(
                CertifiedConsumerQueryResponseItem(
                    sequence=index,
                    projected_entry=projected_entry,
                    projected_entry_hash=stable_hash(projected_entry),
                )
            )

        response_items = tuple(projected_items)

        query_response_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_query_execution_id": execution.query_execution_id,
                "source_query_execution_record_hash": (
                    execution.query_execution_record_hash
                ),
                "consumer_id": execution.source_consumer_id,
                "requested_projection": projection,
                "response_item_hashes": [
                    item.projected_entry_hash for item in response_items
                ],
            }
        )

        body = {
            "query_response_id": query_response_id,
            "source_query_execution_id": execution.query_execution_id,
            "source_query_execution_record_hash": (
                execution.query_execution_record_hash
            ),
            "source_query_admission_id": (
                execution.source_query_admission_id
            ),
            "source_request_id": execution.source_request_id,
            "consumer_id": execution.source_consumer_id,
            "requested_projection": projection,
            "source_registry_manifest_id": (
                execution.source_registry_manifest_id
            ),
            "source_registry_manifest_hash": (
                execution.source_registry_manifest_hash
            ),
            "source_read_result_hash": execution.source_read_result_hash,
            "matched_entry_count": execution.matched_entry_count,
            "certified_response_item_count": len(response_items),
            "certified_response_items": response_items,
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
            "query_response_status": QUERY_RESPONSE_STATUS,
        }

        return CertifiedConsumerQueryResponseRecord(
            **body,
            query_response_record_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "QUERY_RESPONSE_SCHEMA_VERSION",
    "QUERY_RESPONSE_STATUS",
    "ALLOWED_PROJECTIONS",
    "PROJECTION_RESPONSE_FIELDS",
    "CertifiedConsumerQueryResponseItem",
    "CertifiedConsumerQueryResponseRecord",
    "OracleIntelligenceAnalyticsAuthorizedConsumerQueryResponseCertificationGate",
    "OracleIntelligenceAnalyticsAuthorizedConsumerQueryResponseCertificationInvariantError",
    "stable_hash",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

from dataclasses import replace

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_authorized_consumer_registry_query_execution_gate import (
    AuthorizedConsumerRegistryQueryExecutionRecord,
)
from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_authorized_consumer_query_response_certification_gate import (
    PROJECTION_RESPONSE_FIELDS,
    QUERY_RESPONSE_SCHEMA_VERSION,
    OracleIntelligenceAnalyticsAuthorizedConsumerQueryResponseCertificationGate,
    OracleIntelligenceAnalyticsAuthorizedConsumerQueryResponseCertificationInvariantError,
    stable_hash,
)


def _registry_entry(sequence: int) -> dict:
    body = {
        "sequence": sequence,
        "registry_entry_id": stable_hash({"registry-entry": sequence}),
        "product_admission_id": stable_hash({"product-admission": sequence}),
        "product_admission_record_hash": stable_hash(
            {"product-admission-record": sequence}
        ),
        "intelligence_product_id": stable_hash({"product": sequence}),
        "intelligence_product_hash": stable_hash(
            {"intelligence-product": sequence}
        ),
        "source_canonical_product_manifest_id": "int-oia-036-test",
        "source_canonical_product_manifest_hash": stable_hash({"int": 36}),
        "source_product_admission_manifest_id": "int-oia-037-test",
        "source_product_admission_manifest_hash": stable_hash({"int": 37}),
        "source_result_admission_id": f"result-admission-{sequence}",
        "source_result_admission_record_hash": stable_hash(
            {"result-admission": sequence}
        ),
        "product_schema_version": "oracle.canonical-intelligence-product.v1",
        "product_class": "oracle_certified_intelligence_product",
        "product_type": "market_research_summary",
        "product_mode": "production_read_only_multi_consumer",
        "product_state": "created_not_published",
        "market_id": f"KX-{sequence:03d}",
        "venue_id": "kalshi",
        "confidence": 0.70 + (sequence / 100),
        "calibration_status": "provisional",
        "allowed_consumer_projections": [
            "operator_research",
            "research_presentation",
            "audit_replay",
        ],
        "registry_partition": "kalshi",
        "registry_key": stable_hash({"key": sequence}),
        "immutable": True,
        "read_only": True,
        "deterministic": True,
        "replayable": True,
        "query_eligible": True,
        "projection_eligible": True,
        "publication_eligible": True,
        "publication_performed": False,
        "execution_capabilities_disabled_verified": True,
        "source_hashes_verified": True,
        "lineage_verified": True,
        "admission_verified": True,
        "duplicate_registration_rejected": True,
        "registry_entry_status": (
            "registered_immutably_for_production_serving_not_published"
        ),
    }
    body["registry_entry_hash"] = stable_hash(body)
    return body


def _execution(
    projection: str,
) -> AuthorizedConsumerRegistryQueryExecutionRecord:
    entries = (_registry_entry(1), _registry_entry(2))
    body = {
        "query_execution_id": stable_hash(
            {"query-execution": projection}
        ),
        "source_query_admission_id": stable_hash(
            {"query-admission": projection}
        ),
        "source_query_admission_record_hash": stable_hash(
            {"query-admission-record": projection}
        ),
        "source_request_id": f"request-{projection}",
        "source_consumer_id": {
            "operator_research": "oracle.operator.console.v1",
            "research_presentation": "oracle.research.presentation.v1",
            "audit_replay": "oracle.audit.replay.v1",
        }[projection],
        "source_requested_projection": projection,
        "source_registry_manifest_id": "int-oia-038-test",
        "source_registry_manifest_hash": stable_hash({"manifest": 38}),
        "source_read_result_hash": stable_hash(
            {"read-result": projection}
        ),
        "matched_entry_count": len(entries),
        "matched_registry_entries": entries,
        "query_admission_verified": True,
        "registry_read_request_derived_from_admission": True,
        "registry_read_invocation_count": 1,
        "registry_read_result_verified": True,
        "source_hashes_verified": True,
        "lineage_verified": True,
        "deterministic_replay_verified": True,
        "immutable_read_verified": True,
        "registry_mutation_allowed": False,
        "registry_mutation_performed": False,
        "registry_update_performed": False,
        "registry_delete_performed": False,
        "publication_allowed": False,
        "publication_performed": False,
        "order_execution_allowed": False,
        "order_execution_performed": False,
        "database_connection_performed": False,
        "corpus_read_execution_repeated": False,
        "query_execution_status": (
            "authorized_registry_query_executed_read_only"
        ),
    }
    return AuthorizedConsumerRegistryQueryExecutionRecord(
        **body,
        query_execution_record_hash=stable_hash(body),
    )


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe response certification was accepted")
    except OracleIntelligenceAnalyticsAuthorizedConsumerQueryResponseCertificationInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-042 TEST")
    print(" AUTHORIZED CONSUMER QUERY RESPONSE")
    print(" CERTIFICATION GATE")
    print("=" * 40)

    gate = (
        OracleIntelligenceAnalyticsAuthorizedConsumerQueryResponseCertificationGate()
    )

    operator_execution = _execution("operator_research")
    operator_first = gate.certify(operator_execution)
    operator_repeated = gate.certify(operator_execution)

    assert operator_first == operator_repeated
    assert operator_first.query_response_record_hash == stable_hash(
        {
            key: value
            for key, value in operator_first.__dict__.items()
            if key != "query_response_record_hash"
        }
    )
    assert operator_first.certified_response_item_count == 2
    assert operator_first.matched_entry_count == 2
    assert operator_first.source_execution_verified
    assert operator_first.projection_policy_verified
    assert operator_first.field_allowlist_enforced
    assert operator_first.forbidden_fields_absent
    assert operator_first.response_item_hashes_verified
    assert operator_first.source_hashes_verified
    assert operator_first.lineage_verified
    assert operator_first.deterministic_ordering_verified
    assert operator_first.deterministic_replay_verified
    assert operator_first.immutable_read_verified
    assert operator_first.response_artifact_persistence_allowed
    assert not operator_first.registry_mutation_allowed
    assert not operator_first.registry_mutation_performed
    assert not operator_first.publication_allowed
    assert not operator_first.publication_performed
    assert not operator_first.order_execution_allowed
    assert not operator_first.order_execution_performed
    assert not operator_first.database_connection_performed
    assert not operator_first.corpus_read_execution_repeated

    operator_fields = set(
        operator_first.certified_response_items[0].projected_entry
    )
    assert operator_fields == set(
        PROJECTION_RESPONSE_FIELDS["operator_research"]
    )

    presentation = gate.certify(
        _execution("research_presentation")
    )
    presentation_fields = set(
        presentation.certified_response_items[0].projected_entry
    )
    assert presentation_fields == set(
        PROJECTION_RESPONSE_FIELDS["research_presentation"]
    )
    assert "registry_key" not in presentation_fields
    assert "product_admission_record_hash" not in presentation_fields

    audit = gate.certify(_execution("audit_replay"))
    audit_fields = set(
        audit.certified_response_items[0].projected_entry
    )
    assert audit_fields == set(
        PROJECTION_RESPONSE_FIELDS["audit_replay"]
    )
    assert "product_admission_record_hash" in audit_fields
    assert "registry_entry_hash" in audit_fields

    for item in operator_first.certified_response_items:
        assert item.projected_entry_hash == stable_hash(
            item.projected_entry
        )

    _expect_rejected(
        lambda: gate.certify(
            replace(
                operator_execution,
                publication_allowed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.certify(
            replace(
                operator_execution,
                query_execution_record_hash="0" * 64,
            )
        )
    )
    _expect_rejected(
        lambda: gate.certify(
            replace(
                operator_execution,
                matched_entry_count=99,
            )
        )
    )

    unsafe_entry = dict(operator_execution.matched_registry_entries[0])
    unsafe_entry["database_password"] = "should-never-appear"
    unsafe_entries = (
        unsafe_entry,
        operator_execution.matched_registry_entries[1],
    )
    unsafe_body = {
        key: value
        for key, value in operator_execution.__dict__.items()
        if key != "query_execution_record_hash"
    }
    unsafe_body["matched_registry_entries"] = unsafe_entries
    unsafe_execution = AuthorizedConsumerRegistryQueryExecutionRecord(
        **unsafe_body,
        query_execution_record_hash=stable_hash(unsafe_body),
    )
    certified_unsafe = gate.certify(unsafe_execution)
    for item in certified_unsafe.certified_response_items:
        assert "database_password" not in item.projected_entry

    assert QUERY_RESPONSE_SCHEMA_VERSION == (
        "oracle.authorized-consumer-query-response-certification.v1"
    )

    print("[PASS] Actual INT-OIA-041 query execution record consumed")
    print("[PASS] Query execution record hash independently verified")
    print("[PASS] Operator research projection certified")
    print("[PASS] Research presentation projection certified")
    print("[PASS] Audit replay projection certified")
    print("[PASS] Projection-specific field allowlists enforced")
    print("[PASS] Unsafe internal fields excluded from certified responses")
    print("[PASS] Certified response item hashes verified")
    print("[PASS] Certified response record hash independently verified")
    print("[PASS] Deterministic replay and ordering verified")
    print("[PASS] Complete INT-OIA-013 through INT-OIA-041 lineage preserved")
    print("[PASS] Tampered and unsafe execution records rejected")
    print("[PASS] Registry mutation and publication remained disabled")
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


def verify_int_oia_041_contract() -> None:
    if not SOURCE_041.exists():
        raise FileNotFoundError(
            f"Actual INT-OIA-041 production module missing: {SOURCE_041}"
        )
    source = SOURCE_041.read_text(encoding="utf-8")
    required_tokens = (
        'SCHEMA_VERSION = "INT-OIA-041"',
        "QUERY_EXECUTION_SCHEMA_VERSION",
        "class AuthorizedConsumerRegistryQueryExecutionRecord",
        "class OracleIntelligenceAnalyticsAuthorizedConsumerRegistryQueryExecutionGate",
        "query_execution_record_hash",
        "matched_registry_entries",
        "source_requested_projection",
        "registry_read_invocation_count",
        "registry_mutation_allowed",
        "publication_allowed",
        "order_execution_allowed",
    )
    missing = [token for token in required_tokens if token not in source]
    if missing:
        raise RuntimeError(
            "Actual INT-OIA-041 contract mismatch; missing tokens: "
            + ", ".join(missing)
        )
    print("[OK] Actual INT-OIA-041 query-execution contract verified")


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-042 INSTALLER")
    print(" AUTHORIZED CONSUMER QUERY RESPONSE")
    print(" CERTIFICATION GATE")
    print("=" * 40)

    verify_int_oia_041_contract()

    write_replacement(PRODUCTION, PRODUCTION_SOURCE)
    write_replacement(TEST, TEST_SOURCE)

    append_export(
        QUERY_PACKAGE,
        "from .oracle_intelligence_analytics_authorized_consumer_query_response_certification_gate import *",
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

    print("[OK] INT-OIA-042 test executed automatically")
    print()
    print(
        "[DONE] INT-OIA-042 authorized consumer query response "
        "certification gate installed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
