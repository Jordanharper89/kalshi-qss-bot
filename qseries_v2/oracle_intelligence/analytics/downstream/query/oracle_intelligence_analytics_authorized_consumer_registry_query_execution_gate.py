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
