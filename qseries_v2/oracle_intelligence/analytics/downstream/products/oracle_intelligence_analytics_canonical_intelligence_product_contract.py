from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "INT-OIA-036"
ENGINE_ID = "INT-OIA-036"
POLICY_ID = (
    "oracle.intelligence.analytics.canonical-intelligence-product-contract.v1"
)
PRODUCT_SCHEMA_VERSION = "oracle.canonical-intelligence-product.v1"
STATUS_CREATED = "canonical_intelligence_products_created"

DEFAULT_RESULT_ADMISSION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_controlled_result_admission"
)
DEFAULT_CANONICAL_PRODUCT_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_canonical_intelligence_products"
)

APPROVED_RESULT_CLASS = "immutable_research_artifact"
APPROVED_SOURCE_RELEASE_MODE = "research_presentation_only"
CANONICAL_PRODUCT_CLASS = "oracle_certified_intelligence_product"
CANONICAL_PRODUCT_MODE = "production_read_only_multi_consumer"
CANONICAL_PRODUCT_STATE = "created_not_published"
DEFAULT_PRODUCT_TYPE = "oracle_analytics_research_result"

ALLOWED_CONSUMER_PROJECTIONS = (
    "operator_research",
    "research_presentation",
    "audit_replay",
)
DISALLOWED_EXECUTION_CAPABILITIES = (
    "forecast_creation",
    "signal_creation",
    "alert_creation",
    "qseries_handoff",
    "qseries_execution",
    "market_order_creation",
    "funds_movement",
    "portfolio_mutation",
    "source_mutation",
)


class OracleIntelligenceAnalyticsCanonicalIntelligenceProductInvariantError(
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
            raise OracleIntelligenceAnalyticsCanonicalIntelligenceProductInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleIntelligenceAnalyticsCanonicalIntelligenceProductInvariantError(
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


def _valid_hash(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _aware(value: datetime, field: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise OracleIntelligenceAnalyticsCanonicalIntelligenceProductInvariantError(
            f"{field} must be timezone-aware"
        )
    return value.astimezone(timezone.utc)


def _atomic_write(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = (
        json.dumps(
            _canonical(payload),
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        delete=False,
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary = Path(handle.name)
    try:
        with handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _optional_string(
    payload: Mapping[str, Any],
    *names: str,
) -> str | None:
    for name in names:
        value = payload.get(name)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


@dataclass(frozen=True)
class CanonicalIntelligenceProductRecord:
    sequence: int
    intelligence_product_id: str
    product_schema_version: str
    product_class: str
    product_type: str
    product_mode: str
    product_state: str
    consumer_id: str
    market_id: str | None
    venue_id: str | None
    analytic_result_class: str
    analytic_result_type: str
    analytic_result_payload: Any
    analytic_result_hash: str
    admitted_result_hash: str
    source_result_admission_id: str
    source_result_admission_record_hash: str
    source_result_attestation_id: str
    source_result_attestation_record_hash: str
    source_invocation_execution_id: str
    source_invocation_execution_record_hash: str
    source_boundary_id: str
    source_boundary_hash: str
    source_release_mode: str
    source_admission_status: str
    produced_at: str
    valid_from: str
    expires_at: str | None
    confidence: float | None
    calibration_status: str | None
    evidence_references: tuple[str, ...]
    counterevidence_references: tuple[str, ...]
    assumptions: tuple[str, ...]
    allowed_consumer_projections: tuple[str, ...]
    read_only: bool
    deterministic: bool
    replayable: bool
    immutable: bool
    publication_allowed: bool
    publication_performed: bool
    query_allowed: bool
    projection_allowed: bool
    execution_capabilities_disabled: tuple[str, ...]
    source_result_hash_verified: bool
    source_admission_hash_verified: bool
    source_lineage_verified: bool
    one_time_invocation_verified: bool
    source_consumed_without_reexecution: bool
    database_connection_performed: bool
    corpus_read_execution_repeated: bool
    source_mutation_performed: bool
    product_status: str
    intelligence_product_hash: str


@dataclass(frozen=True)
class OracleIntelligenceAnalyticsCanonicalIntelligenceProductManifest:
    schema_version: str
    engine_id: str
    created_at: str
    canonical_product_manifest_id: str
    canonical_product_manifest_status: str
    canonical_product_policy_id: str
    product_schema_version: str
    product_class: str
    product_mode: str
    source_result_admission_manifest_id: str
    source_result_admission_manifest_hash: str
    source_result_attestation_manifest_id: str
    source_result_attestation_manifest_hash: str
    source_invocation_execution_manifest_id: str
    source_boundary_id: str
    source_boundary_hash: str
    canonical_product_record_count: int
    canonical_product_records: tuple[CanonicalIntelligenceProductRecord, ...]
    all_source_admission_record_hashes_verified: bool
    all_source_result_hashes_verified: bool
    all_source_lineage_verified: bool
    all_one_time_invocations_verified: bool
    all_source_results_immutable: bool
    all_canonical_products_read_only: bool
    all_canonical_products_deterministic: bool
    all_canonical_products_replayable: bool
    all_canonical_products_immutable: bool
    all_canonical_products_unpublished: bool
    all_execution_capabilities_disabled: bool
    source_boundary_consumed_without_reexecution: bool
    invocation_reexecution_performed: bool
    database_connection_performed: bool
    corpus_read_execution_repeated: bool
    source_mutation_allowed: bool
    source_mutation_performed: bool
    production_intelligence_product_created: bool
    presentation_branch_required: bool
    demo_surface_dependency_required: bool
    product_artifact_persistence_allowed: bool
    canonical_product_manifest_hash: str


class OracleIntelligenceAnalyticsCanonicalIntelligenceProductContract:
    def __init__(
        self,
        *,
        result_admission_directory: Path | str = DEFAULT_RESULT_ADMISSION_DIRECTORY,
        canonical_product_directory: Path | str = DEFAULT_CANONICAL_PRODUCT_DIRECTORY,
    ) -> None:
        self.result_admission_directory = Path(result_admission_directory)
        self.canonical_product_directory = Path(canonical_product_directory)

    def _load_result_admission(self) -> dict[str, Any]:
        path = self.result_admission_directory / "current.json"
        if not path.exists():
            raise OracleIntelligenceAnalyticsCanonicalIntelligenceProductInvariantError(
                f"INT-OIA-013 result-admission artifact missing: {path}"
            )

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise OracleIntelligenceAnalyticsCanonicalIntelligenceProductInvariantError(
                "INT-OIA-013 result-admission artifact could not be decoded"
            ) from exc

        manifest_hash = payload.pop("result_admission_manifest_hash", None)
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise OracleIntelligenceAnalyticsCanonicalIntelligenceProductInvariantError(
                "INT-OIA-013 result-admission manifest hash mismatch"
            )
        payload["result_admission_manifest_hash"] = manifest_hash

        required_manifest = {
            "schema_version": "INT-OIA-013",
            "engine_id": "INT-OIA-013",
            "result_admission_status": (
                "downstream_read_only_consumer_controlled_result_admitted"
            ),
            "all_attestation_hashes_verified": True,
            "all_result_hashes_verified": True,
            "all_attestation_lineage_verified": True,
            "all_one_time_invocations_verified": True,
            "all_results_immutable": True,
            "all_result_schemas_safe": True,
            "all_results_research_presentation_eligible": True,
            "source_boundary_consumed_without_reexecution": True,
            "invocation_reexecution_performed": False,
            "database_connection_performed": False,
            "corpus_read_execution_repeated": False,
            "source_mutation_allowed": False,
            "source_mutation_performed": False,
            "analytic_conclusion_allowed": True,
            "research_presentation_release_authorized": True,
            "downstream_release_performed": False,
            "forecast_creation_allowed": False,
            "signals_allowed": False,
            "alerts_allowed": False,
            "qseries_handoff_allowed": False,
            "qseries_execution_allowed": False,
            "market_order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
            "admission_artifact_persistence_allowed": True,
        }
        for field, expected in required_manifest.items():
            if payload.get(field) != expected:
                raise OracleIntelligenceAnalyticsCanonicalIntelligenceProductInvariantError(
                    f"unsafe or incomplete INT-OIA-013 field: {field}"
                )

        records = payload.get("admission_records")
        if (
            not isinstance(records, list)
            or not records
            or payload.get("admission_record_count") != len(records)
        ):
            raise OracleIntelligenceAnalyticsCanonicalIntelligenceProductInvariantError(
                "INT-OIA-013 admission records invalid"
            )

        seen_admission_ids: set[str] = set()
        for sequence, raw_record in enumerate(records, start=1):
            if not isinstance(raw_record, dict):
                raise OracleIntelligenceAnalyticsCanonicalIntelligenceProductInvariantError(
                    "INT-OIA-013 admission record must be an object"
                )
            record = dict(raw_record)
            record_hash = record.pop("result_admission_record_hash", None)
            if not _valid_hash(record_hash) or stable_hash(record) != record_hash:
                raise OracleIntelligenceAnalyticsCanonicalIntelligenceProductInvariantError(
                    "INT-OIA-013 admission-record hash mismatch"
                )
            record["result_admission_record_hash"] = record_hash

            admission_id = record.get("result_admission_id")
            if (
                record.get("sequence") != sequence
                or not isinstance(admission_id, str)
                or not admission_id
                or admission_id in seen_admission_ids
            ):
                raise OracleIntelligenceAnalyticsCanonicalIntelligenceProductInvariantError(
                    "invalid sequence or duplicate INT-OIA-013 admission identity"
                )
            seen_admission_ids.add(admission_id)

            if stable_hash(record.get("result_payload")) != record.get("result_hash"):
                raise OracleIntelligenceAnalyticsCanonicalIntelligenceProductInvariantError(
                    "INT-OIA-013 admitted result payload hash mismatch"
                )

            recomputed_admitted_result_hash = stable_hash(
                {
                    "result_hash": record["result_hash"],
                    "result_payload": record["result_payload"],
                    "result_class": record["result_class"],
                    "release_mode": record["release_mode"],
                    "source_boundary_id": record["source_boundary_id"],
                    "source_boundary_hash": record["source_boundary_hash"],
                }
            )
            if recomputed_admitted_result_hash != record.get("admitted_result_hash"):
                raise OracleIntelligenceAnalyticsCanonicalIntelligenceProductInvariantError(
                    "INT-OIA-013 admitted-result hash mismatch"
                )

            required_record = {
                "result_class": APPROVED_RESULT_CLASS,
                "release_mode": APPROVED_SOURCE_RELEASE_MODE,
                "result_hash_verified": True,
                "attestation_lineage_verified": True,
                "one_time_invocation_verified": True,
                "immutable_result_verified": True,
                "result_schema_safe": True,
                "research_presentation_eligible": True,
                "signals_eligible": False,
                "alerts_eligible": False,
                "qseries_handoff_eligible": False,
                "qseries_execution_eligible": False,
                "market_order_creation_eligible": False,
                "funds_movement_eligible": False,
                "portfolio_mutation_eligible": False,
                "source_mutation_allowed": False,
                "downstream_release_authorized": True,
                "downstream_release_performed": False,
                "admission_status": (
                    "admitted_for_research_presentation_not_released"
                ),
            }
            for field, expected in required_record.items():
                if record.get(field) != expected:
                    raise OracleIntelligenceAnalyticsCanonicalIntelligenceProductInvariantError(
                        f"unsafe INT-OIA-013 admission-record field: {field}"
                    )

        return payload

    def create(
        self,
        *,
        created_at: datetime,
        persist: bool = True,
    ) -> OracleIntelligenceAnalyticsCanonicalIntelligenceProductManifest:
        created_at = _aware(created_at, "created_at")
        source = self._load_result_admission()
        records: list[CanonicalIntelligenceProductRecord] = []
        seen_product_ids: set[str] = set()

        for sequence, admission in enumerate(source["admission_records"], start=1):
            result_payload = admission["result_payload"]
            payload_mapping = (
                result_payload if isinstance(result_payload, Mapping) else {}
            )

            market_id = _optional_string(
                payload_mapping,
                "market_id",
                "canonical_market_id",
                "ticker",
            )
            venue_id = _optional_string(
                payload_mapping,
                "venue_id",
                "canonical_venue_id",
                "venue",
            )
            product_type = (
                _optional_string(payload_mapping, "product_type")
                or DEFAULT_PRODUCT_TYPE
            )
            confidence_value = payload_mapping.get("confidence")
            confidence = (
                float(confidence_value)
                if isinstance(confidence_value, (int, float))
                and not isinstance(confidence_value, bool)
                else None
            )
            calibration_status = _optional_string(
                payload_mapping,
                "calibration_status",
            )

            evidence = payload_mapping.get("evidence_references", ())
            counterevidence = payload_mapping.get(
                "counterevidence_references",
                (),
            )
            assumptions = payload_mapping.get("assumptions", ())
            evidence_references = tuple(
                str(item) for item in evidence
            ) if isinstance(evidence, (list, tuple)) else ()
            counterevidence_references = tuple(
                str(item) for item in counterevidence
            ) if isinstance(counterevidence, (list, tuple)) else ()
            assumption_items = tuple(
                str(item) for item in assumptions
            ) if isinstance(assumptions, (list, tuple)) else ()

            product_id = stable_hash(
                {
                    "product_schema_version": PRODUCT_SCHEMA_VERSION,
                    "source_result_admission_manifest_id": source[
                        "result_admission_manifest_id"
                    ],
                    "source_result_admission_id": admission[
                        "result_admission_id"
                    ],
                    "source_result_admission_record_hash": admission[
                        "result_admission_record_hash"
                    ],
                    "analytic_result_hash": admission["result_hash"],
                    "admitted_result_hash": admission["admitted_result_hash"],
                    "created_at": created_at.isoformat(),
                }
            )
            if product_id in seen_product_ids:
                raise OracleIntelligenceAnalyticsCanonicalIntelligenceProductInvariantError(
                    "duplicate canonical intelligence product identity"
                )
            seen_product_ids.add(product_id)

            body = {
                "sequence": sequence,
                "intelligence_product_id": product_id,
                "product_schema_version": PRODUCT_SCHEMA_VERSION,
                "product_class": CANONICAL_PRODUCT_CLASS,
                "product_type": product_type,
                "product_mode": CANONICAL_PRODUCT_MODE,
                "product_state": CANONICAL_PRODUCT_STATE,
                "consumer_id": admission["consumer_id"],
                "market_id": market_id,
                "venue_id": venue_id,
                "analytic_result_class": admission["result_class"],
                "analytic_result_type": admission["result_type"],
                "analytic_result_payload": result_payload,
                "analytic_result_hash": admission["result_hash"],
                "admitted_result_hash": admission["admitted_result_hash"],
                "source_result_admission_id": admission[
                    "result_admission_id"
                ],
                "source_result_admission_record_hash": admission[
                    "result_admission_record_hash"
                ],
                "source_result_attestation_id": admission[
                    "result_attestation_id"
                ],
                "source_result_attestation_record_hash": admission[
                    "source_result_attestation_record_hash"
                ],
                "source_invocation_execution_id": admission[
                    "invocation_execution_id"
                ],
                "source_invocation_execution_record_hash": admission[
                    "source_invocation_execution_record_hash"
                ],
                "source_boundary_id": admission["source_boundary_id"],
                "source_boundary_hash": admission["source_boundary_hash"],
                "source_release_mode": admission["release_mode"],
                "source_admission_status": admission["admission_status"],
                "produced_at": created_at.isoformat(),
                "valid_from": created_at.isoformat(),
                "expires_at": None,
                "confidence": confidence,
                "calibration_status": calibration_status,
                "evidence_references": evidence_references,
                "counterevidence_references": counterevidence_references,
                "assumptions": assumption_items,
                "allowed_consumer_projections": ALLOWED_CONSUMER_PROJECTIONS,
                "read_only": True,
                "deterministic": True,
                "replayable": True,
                "immutable": True,
                "publication_allowed": True,
                "publication_performed": False,
                "query_allowed": True,
                "projection_allowed": True,
                "execution_capabilities_disabled": (
                    DISALLOWED_EXECUTION_CAPABILITIES
                ),
                "source_result_hash_verified": True,
                "source_admission_hash_verified": True,
                "source_lineage_verified": True,
                "one_time_invocation_verified": True,
                "source_consumed_without_reexecution": True,
                "database_connection_performed": False,
                "corpus_read_execution_repeated": False,
                "source_mutation_performed": False,
                "product_status": (
                    "canonical_production_intelligence_product_created_not_published"
                ),
            }
            records.append(
                CanonicalIntelligenceProductRecord(
                    **body,
                    intelligence_product_hash=stable_hash(body),
                )
            )

        manifest_id = stable_hash(
            {
                "source_result_admission_manifest_id": source[
                    "result_admission_manifest_id"
                ],
                "source_result_admission_manifest_hash": source[
                    "result_admission_manifest_hash"
                ],
                "created_at": created_at.isoformat(),
                "canonical_intelligence_product_hashes": [
                    record.intelligence_product_hash for record in records
                ],
            }
        )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "created_at": created_at.isoformat(),
            "canonical_product_manifest_id": manifest_id,
            "canonical_product_manifest_status": STATUS_CREATED,
            "canonical_product_policy_id": POLICY_ID,
            "product_schema_version": PRODUCT_SCHEMA_VERSION,
            "product_class": CANONICAL_PRODUCT_CLASS,
            "product_mode": CANONICAL_PRODUCT_MODE,
            "source_result_admission_manifest_id": source[
                "result_admission_manifest_id"
            ],
            "source_result_admission_manifest_hash": source[
                "result_admission_manifest_hash"
            ],
            "source_result_attestation_manifest_id": source[
                "source_result_attestation_manifest_id"
            ],
            "source_result_attestation_manifest_hash": source[
                "source_result_attestation_manifest_hash"
            ],
            "source_invocation_execution_manifest_id": source[
                "source_invocation_execution_manifest_id"
            ],
            "source_boundary_id": source["source_boundary_id"],
            "source_boundary_hash": source["source_boundary_hash"],
            "canonical_product_record_count": len(records),
            "canonical_product_records": tuple(records),
            "all_source_admission_record_hashes_verified": True,
            "all_source_result_hashes_verified": True,
            "all_source_lineage_verified": True,
            "all_one_time_invocations_verified": True,
            "all_source_results_immutable": True,
            "all_canonical_products_read_only": True,
            "all_canonical_products_deterministic": True,
            "all_canonical_products_replayable": True,
            "all_canonical_products_immutable": True,
            "all_canonical_products_unpublished": True,
            "all_execution_capabilities_disabled": True,
            "source_boundary_consumed_without_reexecution": True,
            "invocation_reexecution_performed": False,
            "database_connection_performed": False,
            "corpus_read_execution_repeated": False,
            "source_mutation_allowed": False,
            "source_mutation_performed": False,
            "production_intelligence_product_created": True,
            "presentation_branch_required": False,
            "demo_surface_dependency_required": False,
            "product_artifact_persistence_allowed": True,
        }
        manifest = OracleIntelligenceAnalyticsCanonicalIntelligenceProductManifest(
            **body,
            canonical_product_manifest_hash=stable_hash(body),
        )

        if persist:
            payload = asdict(manifest)
            _atomic_write(
                self.canonical_product_directory / "current.json",
                payload,
            )
            _atomic_write(
                self.canonical_product_directory
                / "manifests"
                / f"{manifest.canonical_product_manifest_id}.json",
                payload,
            )
            for record in manifest.canonical_product_records:
                _atomic_write(
                    self.canonical_product_directory
                    / "products"
                    / f"{record.intelligence_product_id}.json",
                    asdict(record),
                )

        return manifest


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "PRODUCT_SCHEMA_VERSION",
    "CANONICAL_PRODUCT_CLASS",
    "CANONICAL_PRODUCT_MODE",
    "CanonicalIntelligenceProductRecord",
    "OracleIntelligenceAnalyticsCanonicalIntelligenceProductManifest",
    "OracleIntelligenceAnalyticsCanonicalIntelligenceProductContract",
    "OracleIntelligenceAnalyticsCanonicalIntelligenceProductInvariantError",
    "stable_hash",
]
