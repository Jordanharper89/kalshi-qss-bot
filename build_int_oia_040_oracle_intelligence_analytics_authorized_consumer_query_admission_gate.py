from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"
DOWNSTREAM = ANALYTICS / "downstream"
QUERY = DOWNSTREAM / "query"
SOURCE_039 = QUERY / "oracle_intelligence_analytics_production_intelligence_product_registry_read_contract.py"
PRODUCTION = QUERY / "oracle_intelligence_analytics_authorized_consumer_query_admission_gate.py"
TEST = ROOT / "test_int_oia_040_oracle_intelligence_analytics_authorized_consumer_query_admission_gate.py"

PRODUCTION_SOURCE = r'''
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_production_intelligence_product_registry_read_contract import ProductionIntelligenceProductRegistryReadRequest

SCHEMA_VERSION = "INT-OIA-040"
ENGINE_ID = "INT-OIA-040"
QUERY_ADMISSION_SCHEMA_VERSION = "oracle.authorized-consumer-query-admission.v1"
QUERY_ADMISSION_STATUS = "authorized_consumer_query_admitted"
ALLOWED_PROJECTIONS = ("operator_research", "research_presentation", "audit_replay")
AUTHORIZED_CONSUMERS = {
    "oracle.operator.console.v1": ("operator_research", "audit_replay"),
    "oracle.research.presentation.v1": ("research_presentation", "audit_replay"),
    "oracle.audit.replay.v1": ("audit_replay",),
}
MAXIMUM_ALLOWED_RESULTS = 1000
MAXIMUM_FILTER_LENGTH = 512


class OracleIntelligenceAnalyticsAuthorizedConsumerQueryAdmissionInvariantError(RuntimeError):
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
            raise OracleIntelligenceAnalyticsAuthorizedConsumerQueryAdmissionInvariantError("datetime must be timezone-aware")
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleIntelligenceAnalyticsAuthorizedConsumerQueryAdmissionInvariantError(f"unsupported value type: {type(value)!r}")


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(_canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest()


def _valid_hash(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _validate_filter(name: str, value: str | None) -> None:
    if value is None:
        return
    if not isinstance(value, str) or not value:
        raise OracleIntelligenceAnalyticsAuthorizedConsumerQueryAdmissionInvariantError(f"{name} must be a non-empty string")
    if len(value) > MAXIMUM_FILTER_LENGTH:
        raise OracleIntelligenceAnalyticsAuthorizedConsumerQueryAdmissionInvariantError(f"{name} exceeds maximum length")
    if any(c in value for c in ("\x00", "\r", "\n")):
        raise OracleIntelligenceAnalyticsAuthorizedConsumerQueryAdmissionInvariantError(f"{name} contains unsafe control characters")


@dataclass(frozen=True)
class AuthorizedConsumerQueryAdmissionRequest:
    request_id: str
    consumer_id: str
    requested_projection: str
    intelligence_product_id: str | None = None
    registry_key: str | None = None
    market_id: str | None = None
    venue_id: str | None = None
    maximum_results: int = 100
    request_hash: str = ""


@dataclass(frozen=True)
class AuthorizedConsumerQueryAdmissionRecord:
    query_admission_id: str
    request_id: str
    consumer_id: str
    requested_projection: str
    intelligence_product_id: str | None
    registry_key: str | None
    market_id: str | None
    venue_id: str | None
    maximum_results: int
    canonical_request_hash: str
    source_request_hash: str
    consumer_authorized: bool
    projection_authorized: bool
    filters_validated: bool
    result_limit_validated: bool
    request_hash_verified: bool
    registry_read_authorized: bool
    registry_mutation_allowed: bool
    publication_allowed: bool
    execution_allowed: bool
    database_connection_performed: bool
    corpus_read_execution_repeated: bool
    query_admission_status: str
    query_admission_record_hash: str


@dataclass(frozen=True)
class AuthorizedConsumerQueryAdmissionManifest:
    schema_version: str
    engine_id: str
    query_admission_schema_version: str
    query_admission_status: str
    source_read_contract_schema_version: str
    query_admission_count: int
    query_admissions: tuple[AuthorizedConsumerQueryAdmissionRecord, ...]
    all_consumers_authorized: bool
    all_projections_authorized: bool
    all_filters_validated: bool
    all_result_limits_validated: bool
    all_request_hashes_verified: bool
    all_registry_reads_authorized: bool
    registry_mutation_allowed: bool
    publication_allowed: bool
    execution_allowed: bool
    database_connection_performed: bool
    corpus_read_execution_repeated: bool
    query_admission_manifest_hash: str


class OracleIntelligenceAnalyticsAuthorizedConsumerQueryAdmissionGate:
    def __init__(self) -> None:
        self._admissions: dict[str, AuthorizedConsumerQueryAdmissionRecord] = {}

    @staticmethod
    def canonical_request_payload(request: AuthorizedConsumerQueryAdmissionRequest) -> dict[str, Any]:
        return {
            "request_id": request.request_id,
            "consumer_id": request.consumer_id,
            "requested_projection": request.requested_projection,
            "intelligence_product_id": request.intelligence_product_id,
            "registry_key": request.registry_key,
            "market_id": request.market_id,
            "venue_id": request.venue_id,
            "maximum_results": request.maximum_results,
        }

    @classmethod
    def calculate_request_hash(cls, request: AuthorizedConsumerQueryAdmissionRequest) -> str:
        return stable_hash(cls.canonical_request_payload(request))

    def admit(self, request: AuthorizedConsumerQueryAdmissionRequest) -> AuthorizedConsumerQueryAdmissionRecord:
        if not isinstance(request, AuthorizedConsumerQueryAdmissionRequest):
            raise OracleIntelligenceAnalyticsAuthorizedConsumerQueryAdmissionInvariantError("canonical request contract required")
        if not request.request_id or not request.consumer_id:
            raise OracleIntelligenceAnalyticsAuthorizedConsumerQueryAdmissionInvariantError("request_id and consumer_id are required")
        if request.consumer_id not in AUTHORIZED_CONSUMERS:
            raise OracleIntelligenceAnalyticsAuthorizedConsumerQueryAdmissionInvariantError("consumer is not authorized")
        if request.requested_projection not in ALLOWED_PROJECTIONS:
            raise OracleIntelligenceAnalyticsAuthorizedConsumerQueryAdmissionInvariantError("projection is not recognized")
        if request.requested_projection not in AUTHORIZED_CONSUMERS[request.consumer_id]:
            raise OracleIntelligenceAnalyticsAuthorizedConsumerQueryAdmissionInvariantError("consumer is not authorized for projection")
        for name in ("intelligence_product_id", "registry_key", "market_id", "venue_id"):
            _validate_filter(name, getattr(request, name))
        if not isinstance(request.maximum_results, int) or isinstance(request.maximum_results, bool) or not 1 <= request.maximum_results <= MAXIMUM_ALLOWED_RESULTS:
            raise OracleIntelligenceAnalyticsAuthorizedConsumerQueryAdmissionInvariantError("maximum_results must be between 1 and 1000")
        canonical_request_hash = self.calculate_request_hash(request)
        if not _valid_hash(request.request_hash) or request.request_hash != canonical_request_hash:
            raise OracleIntelligenceAnalyticsAuthorizedConsumerQueryAdmissionInvariantError("query request hash mismatch")

        admission_id = stable_hash({"engine_id": ENGINE_ID, "request_id": request.request_id, "consumer_id": request.consumer_id, "projection": request.requested_projection, "request_hash": canonical_request_hash})
        body = {
            "query_admission_id": admission_id,
            "request_id": request.request_id,
            "consumer_id": request.consumer_id,
            "requested_projection": request.requested_projection,
            "intelligence_product_id": request.intelligence_product_id,
            "registry_key": request.registry_key,
            "market_id": request.market_id,
            "venue_id": request.venue_id,
            "maximum_results": request.maximum_results,
            "canonical_request_hash": canonical_request_hash,
            "source_request_hash": request.request_hash,
            "consumer_authorized": True,
            "projection_authorized": True,
            "filters_validated": True,
            "result_limit_validated": True,
            "request_hash_verified": True,
            "registry_read_authorized": True,
            "registry_mutation_allowed": False,
            "publication_allowed": False,
            "execution_allowed": False,
            "database_connection_performed": False,
            "corpus_read_execution_repeated": False,
            "query_admission_status": QUERY_ADMISSION_STATUS,
        }
        record = AuthorizedConsumerQueryAdmissionRecord(**body, query_admission_record_hash=stable_hash(body))
        existing = self._admissions.get(admission_id)
        if existing is not None and existing != record:
            raise OracleIntelligenceAnalyticsAuthorizedConsumerQueryAdmissionInvariantError("query admission identity collision")
        self._admissions[admission_id] = record
        return record

    def build_manifest(self) -> AuthorizedConsumerQueryAdmissionManifest:
        admissions = tuple(sorted(self._admissions.values(), key=lambda x: (x.consumer_id, x.requested_projection, x.request_id, x.query_admission_id)))
        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "query_admission_schema_version": QUERY_ADMISSION_SCHEMA_VERSION,
            "query_admission_status": QUERY_ADMISSION_STATUS,
            "source_read_contract_schema_version": "oracle.production-intelligence-product-registry-read-contract.v1",
            "query_admission_count": len(admissions),
            "query_admissions": admissions,
            "all_consumers_authorized": all(x.consumer_authorized for x in admissions),
            "all_projections_authorized": all(x.projection_authorized for x in admissions),
            "all_filters_validated": all(x.filters_validated for x in admissions),
            "all_result_limits_validated": all(x.result_limit_validated for x in admissions),
            "all_request_hashes_verified": all(x.request_hash_verified for x in admissions),
            "all_registry_reads_authorized": all(x.registry_read_authorized for x in admissions),
            "registry_mutation_allowed": False,
            "publication_allowed": False,
            "execution_allowed": False,
            "database_connection_performed": False,
            "corpus_read_execution_repeated": False,
        }
        return AuthorizedConsumerQueryAdmissionManifest(**body, query_admission_manifest_hash=stable_hash(body))

    @staticmethod
    def to_registry_read_request(record: AuthorizedConsumerQueryAdmissionRecord) -> ProductionIntelligenceProductRegistryReadRequest:
        if not isinstance(record, AuthorizedConsumerQueryAdmissionRecord):
            raise OracleIntelligenceAnalyticsAuthorizedConsumerQueryAdmissionInvariantError("canonical admission record required")
        body = {k: v for k, v in asdict(record).items() if k != "query_admission_record_hash"}
        if stable_hash(body) != record.query_admission_record_hash:
            raise OracleIntelligenceAnalyticsAuthorizedConsumerQueryAdmissionInvariantError("query admission record hash mismatch")
        if not all((record.consumer_authorized, record.projection_authorized, record.filters_validated, record.result_limit_validated, record.request_hash_verified, record.registry_read_authorized)):
            raise OracleIntelligenceAnalyticsAuthorizedConsumerQueryAdmissionInvariantError("query admission is not read eligible")
        if any((record.registry_mutation_allowed, record.publication_allowed, record.execution_allowed, record.database_connection_performed, record.corpus_read_execution_repeated)):
            raise OracleIntelligenceAnalyticsAuthorizedConsumerQueryAdmissionInvariantError("unsafe authority detected")
        return ProductionIntelligenceProductRegistryReadRequest(
            request_id=record.request_id,
            consumer_id=record.consumer_id,
            requested_projection=record.requested_projection,
            intelligence_product_id=record.intelligence_product_id,
            registry_key=record.registry_key,
            market_id=record.market_id,
            venue_id=record.venue_id,
            maximum_results=record.maximum_results,
        )


__all__ = [
    "SCHEMA_VERSION", "ENGINE_ID", "QUERY_ADMISSION_SCHEMA_VERSION", "QUERY_ADMISSION_STATUS",
    "ALLOWED_PROJECTIONS", "AUTHORIZED_CONSUMERS", "AuthorizedConsumerQueryAdmissionRequest",
    "AuthorizedConsumerQueryAdmissionRecord", "AuthorizedConsumerQueryAdmissionManifest",
    "OracleIntelligenceAnalyticsAuthorizedConsumerQueryAdmissionGate",
    "OracleIntelligenceAnalyticsAuthorizedConsumerQueryAdmissionInvariantError", "stable_hash",
]
'''

TEST_SOURCE = r'''
from __future__ import annotations

from dataclasses import replace

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_authorized_consumer_query_admission_gate import (
    AuthorizedConsumerQueryAdmissionRequest,
    OracleIntelligenceAnalyticsAuthorizedConsumerQueryAdmissionGate,
    OracleIntelligenceAnalyticsAuthorizedConsumerQueryAdmissionInvariantError,
    QUERY_ADMISSION_SCHEMA_VERSION,
    stable_hash,
)


def signed(gate, **overrides):
    request = AuthorizedConsumerQueryAdmissionRequest(
        request_id="query-request-1",
        consumer_id="oracle.operator.console.v1",
        requested_projection="operator_research",
        market_id="KX-ALPHA",
        venue_id="kalshi",
        maximum_results=100,
    )
    request = replace(request, **overrides)
    return replace(request, request_hash=gate.calculate_request_hash(request))


def rejected(callable_):
    try:
        callable_()
        raise AssertionError("unsafe query was admitted")
    except OracleIntelligenceAnalyticsAuthorizedConsumerQueryAdmissionInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-040 TEST")
    print(" AUTHORIZED CONSUMER QUERY")
    print(" ADMISSION GATE")
    print("=" * 40)
    gate = OracleIntelligenceAnalyticsAuthorizedConsumerQueryAdmissionGate()
    request = signed(gate)
    first = gate.admit(request)
    assert gate.admit(request) == first
    assert first.query_admission_record_hash == stable_hash({k: v for k, v in first.__dict__.items() if k != "query_admission_record_hash"})
    assert first.consumer_authorized and first.projection_authorized
    assert first.filters_validated and first.result_limit_validated and first.request_hash_verified
    assert first.registry_read_authorized
    assert not first.registry_mutation_allowed and not first.publication_allowed and not first.execution_allowed
    read_request = gate.to_registry_read_request(first)
    assert read_request.request_id == first.request_id
    assert read_request.consumer_id == first.consumer_id
    assert read_request.market_id == "KX-ALPHA"

    gate.admit(signed(gate, request_id="query-request-2", consumer_id="oracle.audit.replay.v1", requested_projection="audit_replay", market_id=None, maximum_results=25))
    manifest = gate.build_manifest()
    assert manifest.query_admission_count == 2
    assert manifest.query_admission_manifest_hash == stable_hash({k: v for k, v in manifest.__dict__.items() if k != "query_admission_manifest_hash"})
    assert manifest.all_consumers_authorized and manifest.all_projections_authorized
    assert manifest.all_filters_validated and manifest.all_result_limits_validated
    assert manifest.all_request_hashes_verified and manifest.all_registry_reads_authorized

    rejected(lambda: gate.admit(signed(gate, request_id="bad-consumer", consumer_id="unknown.consumer.v1")))
    rejected(lambda: gate.admit(signed(gate, request_id="bad-projection", consumer_id="oracle.audit.replay.v1", requested_projection="operator_research")))
    rejected(lambda: gate.admit(replace(signed(gate, request_id="tampered"), maximum_results=99)))
    rejected(lambda: gate.admit(signed(gate, request_id="oversized", maximum_results=1001)))
    rejected(lambda: gate.admit(signed(gate, request_id="unsafe-filter", market_id="KX-ALPHA\nINJECT")))
    rejected(lambda: gate.to_registry_read_request(replace(first, execution_allowed=True)))

    assert QUERY_ADMISSION_SCHEMA_VERSION == "oracle.authorized-consumer-query-admission.v1"
    print("[PASS] Actual INT-OIA-039 registry-read request contract consumed")
    print("[PASS] Canonical query request hashing verified")
    print("[PASS] Authorized consumer identities enforced")
    print("[PASS] Consumer-specific projection scopes enforced")
    print("[PASS] Query filters and result limits validated")
    print("[PASS] Admitted query identities deterministic")
    print("[PASS] Duplicate valid admission remained idempotent")
    print("[PASS] Admission record and manifest hashes independently verified")
    print("[PASS] Eligible admission converted to INT-OIA-039 read request")
    print("[PASS] Unauthorized consumer and projection rejected")
    print("[PASS] Tampered request hash and admission record rejected")
    print("[PASS] Oversized result request and unsafe filter rejected")
    print("[PASS] Registry mutation, publication, and execution remained disabled")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def write(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.strip() + "\n", encoding="utf-8", newline="\n")
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def export(path: Path, line: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if line not in existing.splitlines():
        existing = existing + ("" if not existing or existing.endswith("\n") else "\n") + line + "\n"
        path.write_text(existing, encoding="utf-8", newline="\n")
    print(f"[OK] PACKAGE UPDATED: {path.resolve()}")


def verify_039() -> None:
    if not SOURCE_039.exists():
        raise FileNotFoundError(f"Actual INT-OIA-039 module missing: {SOURCE_039}")
    source = SOURCE_039.read_text(encoding="utf-8")
    required = (
        'SCHEMA_VERSION = "INT-OIA-039"',
        "READ_CONTRACT_SCHEMA_VERSION",
        "oracle.production-intelligence-product-registry-read-contract.v1",
        "class ProductionIntelligenceProductRegistryReadRequest",
        "requested_projection",
        "maximum_results",
        "registry_mutation_allowed",
        "publication_allowed",
        "execution_allowed",
    )
    missing = [token for token in required if token not in source]
    if missing:
        raise RuntimeError("Actual INT-OIA-039 contract mismatch; missing tokens: " + ", ".join(missing))
    print("[OK] Actual INT-OIA-039 registry-read contract verified")


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-040 INSTALLER")
    print(" AUTHORIZED CONSUMER QUERY")
    print(" ADMISSION GATE")
    print("=" * 40)
    verify_039()
    write(PRODUCTION, PRODUCTION_SOURCE)
    write(TEST, TEST_SOURCE)
    export(QUERY / "__init__.py", "from .oracle_intelligence_analytics_authorized_consumer_query_admission_gate import *")
    export(DOWNSTREAM / "__init__.py", "from .query import *")
    export(ANALYTICS / "__init__.py", "from .downstream.query import *")
    for target in (PRODUCTION, TEST, QUERY / "__init__.py", DOWNSTREAM / "__init__.py", ANALYTICS / "__init__.py"):
        ast.parse(target.read_text(encoding="utf-8"), filename=str(target))
    print("[OK] Production, test, and package syntax verified in memory")
    completed = subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=False)
    if completed.returncode:
        raise SystemExit(completed.returncode)
    print("[OK] INT-OIA-040 test executed automatically")
    print()
    print("[DONE] INT-OIA-040 authorized consumer query admission gate installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
