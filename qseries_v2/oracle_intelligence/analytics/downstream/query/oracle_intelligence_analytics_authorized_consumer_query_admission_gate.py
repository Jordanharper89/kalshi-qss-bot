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
