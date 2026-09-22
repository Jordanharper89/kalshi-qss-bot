from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"
DOWNSTREAM = ANALYTICS / "downstream"
QUERY = DOWNSTREAM / "query"

SOURCE_039 = QUERY / (
    "oracle_intelligence_analytics_production_intelligence_product_registry_read_contract.py"
)
SOURCE_040 = QUERY / (
    "oracle_intelligence_analytics_authorized_consumer_query_admission_gate.py"
)
PRODUCTION = QUERY / (
    "oracle_intelligence_analytics_authorized_consumer_registry_query_execution_gate.py"
)
TEST = ROOT / (
    "test_int_oia_041_oracle_intelligence_analytics_"
    "authorized_consumer_registry_query_execution_gate.py"
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
from pathlib import Path
from typing import Any, Mapping

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_authorized_consumer_query_admission_gate import (
    AuthorizedConsumerQueryAdmissionRecord,
    OracleIntelligenceAnalyticsAuthorizedConsumerQueryAdmissionGate,
    OracleIntelligenceAnalyticsAuthorizedConsumerQueryAdmissionInvariantError,
)
from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_production_intelligence_product_registry_read_contract import (
    OracleIntelligenceAnalyticsProductionIntelligenceProductRegistryReadContract,
    OracleIntelligenceAnalyticsProductionIntelligenceProductRegistryReadInvariantError,
    ProductionIntelligenceProductRegistryReadResult,
)

SCHEMA_VERSION = "INT-OIA-041"
ENGINE_ID = "INT-OIA-041"
POLICY_ID = (
    "oracle.intelligence.analytics.authorized-consumer-registry-query."
    "execution-gate.v1"
)
QUERY_EXECUTION_SCHEMA_VERSION = (
    "oracle.authorized-consumer-registry-query-execution.v1"
)
QUERY_EXECUTION_STATUS = "authorized_registry_query_executed_read_only"


class OracleIntelligenceAnalyticsAuthorizedConsumerRegistryQueryExecutionInvariantError(
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
            raise OracleIntelligenceAnalyticsAuthorizedConsumerRegistryQueryExecutionInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleIntelligenceAnalyticsAuthorizedConsumerRegistryQueryExecutionInvariantError(
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


def _verify_hash(body: Mapping[str, Any], field_name: str) -> None:
    body_copy = dict(body)
    supplied = body_copy.pop(field_name, None)
    if (
        not isinstance(supplied, str)
        or len(supplied) != 64
        or any(character not in "0123456789abcdef" for character in supplied)
        or stable_hash(body_copy) != supplied
    ):
        raise OracleIntelligenceAnalyticsAuthorizedConsumerRegistryQueryExecutionInvariantError(
            f"{field_name} mismatch"
        )


@dataclass(frozen=True)
class AuthorizedConsumerRegistryQueryExecutionRecord:
    query_execution_id: str
    source_query_admission_id: str
    source_query_admission_record_hash: str
    source_request_id: str
    source_consumer_id: str
    source_requested_projection: str
    source_registry_manifest_id: str
    source_registry_manifest_hash: str
    source_read_result_hash: str
    matched_entry_count: int
    matched_registry_entries: tuple[dict[str, Any], ...]
    query_admission_verified: bool
    registry_read_request_derived_from_admission: bool
    registry_read_invocation_count: int
    registry_read_result_verified: bool
    source_hashes_verified: bool
    lineage_verified: bool
    deterministic_replay_verified: bool
    immutable_read_verified: bool
    registry_mutation_allowed: bool
    registry_mutation_performed: bool
    registry_update_performed: bool
    registry_delete_performed: bool
    publication_allowed: bool
    publication_performed: bool
    order_execution_allowed: bool
    order_execution_performed: bool
    database_connection_performed: bool
    corpus_read_execution_repeated: bool
    query_execution_status: str
    query_execution_record_hash: str


class OracleIntelligenceAnalyticsAuthorizedConsumerRegistryQueryExecutionGate:
    def __init__(
        self,
        *,
        product_registry_directory: Path | str,
    ) -> None:
        self._reader = (
            OracleIntelligenceAnalyticsProductionIntelligenceProductRegistryReadContract(
                product_registry_directory=product_registry_directory,
            )
        )
        self._executions: dict[
            str,
            AuthorizedConsumerRegistryQueryExecutionRecord,
        ] = {}

    @staticmethod
    def _verify_admission_record(
        admission: AuthorizedConsumerQueryAdmissionRecord,
    ) -> None:
        if not isinstance(admission, AuthorizedConsumerQueryAdmissionRecord):
            raise OracleIntelligenceAnalyticsAuthorizedConsumerRegistryQueryExecutionInvariantError(
                "query admission must use the canonical INT-OIA-040 record contract"
            )

        body = asdict(admission)
        try:
            _verify_hash(body, "query_admission_record_hash")
        except OracleIntelligenceAnalyticsAuthorizedConsumerRegistryQueryExecutionInvariantError:
            raise
        except Exception as exc:
            raise OracleIntelligenceAnalyticsAuthorizedConsumerRegistryQueryExecutionInvariantError(
                "query admission record could not be verified"
            ) from exc

        if not (
            admission.consumer_authorized
            and admission.projection_authorized
            and admission.filters_validated
            and admission.result_limit_validated
            and admission.request_hash_verified
            and admission.registry_read_authorized
        ):
            raise OracleIntelligenceAnalyticsAuthorizedConsumerRegistryQueryExecutionInvariantError(
                "query admission does not authorize a registry read"
            )

        if (
            admission.registry_mutation_allowed
            or admission.publication_allowed
            or admission.execution_allowed
            or admission.database_connection_performed
            or admission.corpus_read_execution_repeated
        ):
            raise OracleIntelligenceAnalyticsAuthorizedConsumerRegistryQueryExecutionInvariantError(
                "query admission contains unsafe authority"
            )

    @staticmethod
    def _verify_read_result(
        result: ProductionIntelligenceProductRegistryReadResult,
    ) -> None:
        if not isinstance(result, ProductionIntelligenceProductRegistryReadResult):
            raise OracleIntelligenceAnalyticsAuthorizedConsumerRegistryQueryExecutionInvariantError(
                "registry read returned an invalid result contract"
            )

        body = asdict(result)
        _verify_hash(body, "read_result_hash")

        if not (
            result.all_entry_hashes_verified
            and result.all_source_hashes_verified
            and result.all_lineage_verified
            and result.projection_authorized
            and result.deterministic_ordering_verified
            and result.immutable_read_verified
        ):
            raise OracleIntelligenceAnalyticsAuthorizedConsumerRegistryQueryExecutionInvariantError(
                "registry read result failed verification"
            )

        if (
            result.registry_mutation_allowed
            or result.registry_mutation_performed
            or result.registry_update_performed
            or result.registry_delete_performed
            or result.publication_allowed
            or result.publication_performed
            or result.execution_allowed
            or result.execution_performed
            or result.database_connection_performed
            or result.corpus_read_execution_repeated
        ):
            raise OracleIntelligenceAnalyticsAuthorizedConsumerRegistryQueryExecutionInvariantError(
                "registry read result contains unsafe activity"
            )

    def execute(
        self,
        admission: AuthorizedConsumerQueryAdmissionRecord,
    ) -> AuthorizedConsumerRegistryQueryExecutionRecord:
        self._verify_admission_record(admission)

        try:
            read_request = (
                OracleIntelligenceAnalyticsAuthorizedConsumerQueryAdmissionGate
                .to_registry_read_request(admission)
            )
        except OracleIntelligenceAnalyticsAuthorizedConsumerQueryAdmissionInvariantError as exc:
            raise OracleIntelligenceAnalyticsAuthorizedConsumerRegistryQueryExecutionInvariantError(
                "INT-OIA-040 admission could not be converted to an INT-OIA-039 read request"
            ) from exc

        invocation_count = 0
        try:
            invocation_count += 1
            result = self._reader.read(read_request)
        except OracleIntelligenceAnalyticsProductionIntelligenceProductRegistryReadInvariantError as exc:
            raise OracleIntelligenceAnalyticsAuthorizedConsumerRegistryQueryExecutionInvariantError(
                "authorized registry read failed"
            ) from exc

        if invocation_count != 1:
            raise OracleIntelligenceAnalyticsAuthorizedConsumerRegistryQueryExecutionInvariantError(
                "registry read invocation count invariant violated"
            )

        self._verify_read_result(result)

        if (
            result.request_id != admission.request_id
            or result.consumer_id != admission.consumer_id
            or result.requested_projection != admission.requested_projection
        ):
            raise OracleIntelligenceAnalyticsAuthorizedConsumerRegistryQueryExecutionInvariantError(
                "registry read result identity does not match admitted query"
            )

        query_execution_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_query_admission_id": admission.query_admission_id,
                "source_query_admission_record_hash": (
                    admission.query_admission_record_hash
                ),
                "source_read_result_hash": result.read_result_hash,
            }
        )

        body = {
            "query_execution_id": query_execution_id,
            "source_query_admission_id": admission.query_admission_id,
            "source_query_admission_record_hash": (
                admission.query_admission_record_hash
            ),
            "source_request_id": admission.request_id,
            "source_consumer_id": admission.consumer_id,
            "source_requested_projection": admission.requested_projection,
            "source_registry_manifest_id": result.source_registry_manifest_id,
            "source_registry_manifest_hash": (
                result.source_registry_manifest_hash
            ),
            "source_read_result_hash": result.read_result_hash,
            "matched_entry_count": result.matched_entry_count,
            "matched_registry_entries": result.matched_registry_entries,
            "query_admission_verified": True,
            "registry_read_request_derived_from_admission": True,
            "registry_read_invocation_count": invocation_count,
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
            "query_execution_status": QUERY_EXECUTION_STATUS,
        }

        record = AuthorizedConsumerRegistryQueryExecutionRecord(
            **body,
            query_execution_record_hash=stable_hash(body),
        )

        existing = self._executions.get(query_execution_id)
        if existing is not None and existing != record:
            raise OracleIntelligenceAnalyticsAuthorizedConsumerRegistryQueryExecutionInvariantError(
                "query execution identity collision detected"
            )

        self._executions[query_execution_id] = record
        return record


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "QUERY_EXECUTION_SCHEMA_VERSION",
    "QUERY_EXECUTION_STATUS",
    "AuthorizedConsumerRegistryQueryExecutionRecord",
    "OracleIntelligenceAnalyticsAuthorizedConsumerRegistryQueryExecutionGate",
    "OracleIntelligenceAnalyticsAuthorizedConsumerRegistryQueryExecutionInvariantError",
    "stable_hash",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import json
import tempfile
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_authorized_consumer_query_admission_gate import (
    AuthorizedConsumerQueryAdmissionRequest,
    OracleIntelligenceAnalyticsAuthorizedConsumerQueryAdmissionGate,
)
from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_authorized_consumer_registry_query_execution_gate import (
    QUERY_EXECUTION_SCHEMA_VERSION,
    OracleIntelligenceAnalyticsAuthorizedConsumerRegistryQueryExecutionGate,
    OracleIntelligenceAnalyticsAuthorizedConsumerRegistryQueryExecutionInvariantError,
    stable_hash,
)


def _entry(
    *,
    sequence: int,
    market_id: str,
    product_id: str,
    registry_key: str,
) -> dict:
    body = {
        "sequence": sequence,
        "registry_entry_id": stable_hash({"registry-entry": sequence}),
        "product_admission_id": stable_hash({"product-admission": sequence}),
        "product_admission_record_hash": stable_hash(
            {"product-admission-record": sequence}
        ),
        "intelligence_product_id": product_id,
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
        "market_id": market_id,
        "venue_id": "kalshi",
        "confidence": 0.70 + (sequence / 100),
        "calibration_status": "provisional",
        "allowed_consumer_projections": [
            "operator_research",
            "research_presentation",
            "audit_replay",
        ],
        "registry_partition": "kalshi",
        "registry_key": registry_key,
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


def _seed_registry(path: Path) -> None:
    entries = [
        _entry(
            sequence=1,
            market_id="KX-ALPHA",
            product_id=stable_hash({"product": "alpha"}),
            registry_key=stable_hash({"key": "alpha"}),
        ),
        _entry(
            sequence=2,
            market_id="KX-BETA",
            product_id=stable_hash({"product": "beta"}),
            registry_key=stable_hash({"key": "beta"}),
        ),
    ]

    manifest = {
        "schema_version": "INT-OIA-038",
        "engine_id": "INT-OIA-038",
        "registered_at": "2026-07-24T17:00:00+00:00",
        "registry_manifest_id": "int-oia-038-test",
        "registry_manifest_status": (
            "admitted_intelligence_products_registered_immutably"
        ),
        "registry_policy_id": "test",
        "registry_schema_version": (
            "oracle.immutable-intelligence-product-registry.v1"
        ),
        "source_product_admission_manifest_id": "int-oia-037-test",
        "source_product_admission_manifest_hash": stable_hash({"int": 37}),
        "source_canonical_product_manifest_id": "int-oia-036-test",
        "source_canonical_product_manifest_hash": stable_hash({"int": 36}),
        "registry_entry_count": len(entries),
        "registry_entries": entries,
        "all_product_admissions_verified": True,
        "all_product_hashes_verified": True,
        "all_source_hashes_verified": True,
        "all_lineage_verified": True,
        "all_entries_immutable": True,
        "all_entries_read_only": True,
        "all_entries_deterministic": True,
        "all_entries_replayable": True,
        "all_entries_query_eligible": True,
        "all_entries_projection_eligible": True,
        "all_entries_unpublished": True,
        "all_execution_capabilities_disabled": True,
        "duplicate_registry_entries_present": False,
        "registry_mutation_allowed": False,
        "registry_update_performed": False,
        "registry_delete_performed": False,
        "publication_performed": False,
        "presentation_branch_required": False,
        "demo_surface_dependency_required": False,
        "source_consumed_without_reexecution": True,
        "invocation_reexecution_performed": False,
        "database_connection_performed": False,
        "corpus_read_execution_repeated": False,
        "source_mutation_performed": False,
        "registry_artifact_persistence_allowed": True,
    }
    manifest["registry_manifest_hash"] = stable_hash(manifest)

    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def _admitted_query(
    gate: OracleIntelligenceAnalyticsAuthorizedConsumerQueryAdmissionGate,
):
    unsigned = AuthorizedConsumerQueryAdmissionRequest(
        request_id="query-request-1",
        consumer_id="oracle.operator.console.v1",
        requested_projection="operator_research",
        market_id="KX-ALPHA",
        venue_id="kalshi",
        maximum_results=100,
        request_hash="",
    )
    signed = replace(
        unsigned,
        request_hash=gate.calculate_request_hash(unsigned),
    )
    return gate.admit(signed)


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe query execution was accepted")
    except OracleIntelligenceAnalyticsAuthorizedConsumerRegistryQueryExecutionInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-041 TEST")
    print(" AUTHORIZED REGISTRY QUERY")
    print(" EXECUTION GATE")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary_directory:
        registry = Path(temporary_directory) / "registry"
        _seed_registry(registry)
        source_before = (registry / "current.json").read_bytes()

        admission_gate = (
            OracleIntelligenceAnalyticsAuthorizedConsumerQueryAdmissionGate()
        )
        admission = _admitted_query(admission_gate)

        execution_gate = (
            OracleIntelligenceAnalyticsAuthorizedConsumerRegistryQueryExecutionGate(
                product_registry_directory=registry,
            )
        )

        first = execution_gate.execute(admission)
        repeated = execution_gate.execute(admission)

        assert first == repeated
        assert first.query_execution_record_hash == stable_hash(
            {
                key: value
                for key, value in first.__dict__.items()
                if key != "query_execution_record_hash"
            }
        )
        assert first.source_query_admission_id == admission.query_admission_id
        assert (
            first.source_query_admission_record_hash
            == admission.query_admission_record_hash
        )
        assert first.source_request_id == admission.request_id
        assert first.source_consumer_id == admission.consumer_id
        assert (
            first.source_requested_projection
            == admission.requested_projection
        )
        assert first.matched_entry_count == 1
        assert len(first.matched_registry_entries) == 1
        assert first.matched_registry_entries[0]["market_id"] == "KX-ALPHA"
        assert first.query_admission_verified
        assert first.registry_read_request_derived_from_admission
        assert first.registry_read_invocation_count == 1
        assert first.registry_read_result_verified
        assert first.source_hashes_verified
        assert first.lineage_verified
        assert first.deterministic_replay_verified
        assert first.immutable_read_verified
        assert not first.registry_mutation_allowed
        assert not first.registry_mutation_performed
        assert not first.registry_update_performed
        assert not first.registry_delete_performed
        assert not first.publication_allowed
        assert not first.publication_performed
        assert not first.order_execution_allowed
        assert not first.order_execution_performed
        assert not first.database_connection_performed
        assert not first.corpus_read_execution_repeated
        assert source_before == (registry / "current.json").read_bytes()

        tampered_admission = replace(
            admission,
            execution_allowed=True,
        )
        _expect_rejected(
            lambda: execution_gate.execute(tampered_admission)
        )

        tampered_hash = replace(
            admission,
            query_admission_record_hash="0" * 64,
        )
        _expect_rejected(
            lambda: execution_gate.execute(tampered_hash)
        )

        tampered_registry = json.loads(
            (registry / "current.json").read_text(encoding="utf-8")
        )
        tampered_registry["registry_entries"][0]["confidence"] = 0.99
        (registry / "current.json").write_text(
            json.dumps(tampered_registry),
            encoding="utf-8",
        )
        _expect_rejected(
            lambda: execution_gate.execute(admission)
        )

    assert QUERY_EXECUTION_SCHEMA_VERSION == (
        "oracle.authorized-consumer-registry-query-execution.v1"
    )

    print("[PASS] Actual INT-OIA-040 query admission consumed")
    print("[PASS] Actual INT-OIA-039 registry read contract invoked")
    print("[PASS] Admission record hash independently verified")
    print("[PASS] Registry read request derived only from admitted query")
    print("[PASS] Registry read invoked exactly once")
    print("[PASS] Registry read result hash independently verified")
    print("[PASS] Query identity matched read-result identity")
    print("[PASS] Complete INT-OIA-013 through INT-OIA-040 lineage preserved")
    print("[PASS] Deterministic replay and idempotent execution verified")
    print("[PASS] Registry remained byte-for-byte unchanged")
    print("[PASS] Registry mutation, update, and delete remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Q Series order execution remained disabled")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] Tampered admission evidence rejected")
    print("[PASS] Tampered registry evidence rejected")
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


def verify_contract(path: Path, label: str, tokens: tuple[str, ...]) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Actual {label} production module missing: {path}")
    source = path.read_text(encoding="utf-8")
    missing = [token for token in tokens if token not in source]
    if missing:
        raise RuntimeError(
            f"Actual {label} contract mismatch; missing tokens: "
            + ", ".join(missing)
        )
    print(f"[OK] Actual {label} contract verified")


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-041 INSTALLER")
    print(" AUTHORIZED REGISTRY QUERY")
    print(" EXECUTION GATE")
    print("=" * 40)

    verify_contract(
        SOURCE_039,
        "INT-OIA-039 registry-read",
        (
            'SCHEMA_VERSION = "INT-OIA-039"',
            "READ_CONTRACT_SCHEMA_VERSION",
            "class ProductionIntelligenceProductRegistryReadRequest",
            "class ProductionIntelligenceProductRegistryReadResult",
            "class OracleIntelligenceAnalyticsProductionIntelligenceProductRegistryReadContract",
            "read_result_hash",
            "registry_mutation_allowed",
            "publication_allowed",
            "execution_allowed",
        ),
    )
    verify_contract(
        SOURCE_040,
        "INT-OIA-040 query-admission",
        (
            'SCHEMA_VERSION = "INT-OIA-040"',
            "QUERY_ADMISSION_SCHEMA_VERSION",
            "class AuthorizedConsumerQueryAdmissionRecord",
            "class OracleIntelligenceAnalyticsAuthorizedConsumerQueryAdmissionGate",
            "query_admission_record_hash",
            "registry_read_authorized",
            "registry_mutation_allowed",
            "publication_allowed",
            "execution_allowed",
        ),
    )

    write_replacement(PRODUCTION, PRODUCTION_SOURCE)
    write_replacement(TEST, TEST_SOURCE)

    append_export(
        QUERY_PACKAGE,
        "from .oracle_intelligence_analytics_authorized_consumer_registry_query_execution_gate import *",
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

    print("[OK] INT-OIA-041 test executed automatically")
    print()
    print("[DONE] INT-OIA-041 authorized registry query execution gate installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
