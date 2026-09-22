from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "INT-OIA-037"
ENGINE_ID = "INT-OIA-037"
POLICY_ID = (
    "oracle.intelligence.analytics.canonical-intelligence-product."
    "validation-and-admission-gate.v1"
)
ADMISSION_SCHEMA_VERSION = (
    "oracle.canonical-intelligence-product-admission.v1"
)
STATUS_ADMITTED = "canonical_intelligence_products_validated_and_admitted"

DEFAULT_CANONICAL_PRODUCT_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_canonical_intelligence_products"
)
DEFAULT_PRODUCT_ADMISSION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_canonical_intelligence_product_admission"
)

EXPECTED_SOURCE_SCHEMA_VERSION = "INT-OIA-036"
EXPECTED_PRODUCT_SCHEMA_VERSION = "oracle.canonical-intelligence-product.v1"
EXPECTED_PRODUCT_CLASS = "oracle_certified_intelligence_product"
EXPECTED_PRODUCT_MODE = "production_read_only_multi_consumer"
EXPECTED_PRODUCT_STATE = "created_not_published"
EXPECTED_PRODUCT_STATUS = (
    "canonical_production_intelligence_product_created_not_published"
)

REQUIRED_EXECUTION_CAPABILITIES_DISABLED = (
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

ALLOWED_PROJECTIONS = (
    "operator_research",
    "research_presentation",
    "audit_replay",
)


class OracleIntelligenceAnalyticsCanonicalIntelligenceProductAdmissionInvariantError(
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
            raise OracleIntelligenceAnalyticsCanonicalIntelligenceProductAdmissionInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleIntelligenceAnalyticsCanonicalIntelligenceProductAdmissionInvariantError(
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
        raise OracleIntelligenceAnalyticsCanonicalIntelligenceProductAdmissionInvariantError(
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


@dataclass(frozen=True)
class CanonicalIntelligenceProductAdmissionRecord:
    sequence: int
    product_admission_id: str
    intelligence_product_id: str
    intelligence_product_hash: str
    source_canonical_product_manifest_id: str
    source_canonical_product_manifest_hash: str
    source_result_admission_id: str
    source_result_admission_record_hash: str
    product_schema_version: str
    product_class: str
    product_type: str
    product_mode: str
    product_state: str
    market_id: str | None
    venue_id: str | None
    confidence: float | None
    calibration_status: str | None
    allowed_consumer_projections: tuple[str, ...]
    read_only_verified: bool
    deterministic_verified: bool
    replayable_verified: bool
    immutable_verified: bool
    lineage_verified: bool
    source_hashes_verified: bool
    product_hash_verified: bool
    schema_verified: bool
    consumer_projection_policy_verified: bool
    execution_capabilities_disabled_verified: bool
    publication_allowed: bool
    publication_performed: bool
    query_allowed: bool
    projection_allowed: bool
    product_admission_status: str
    product_admission_record_hash: str


@dataclass(frozen=True)
class OracleIntelligenceAnalyticsCanonicalIntelligenceProductAdmissionManifest:
    schema_version: str
    engine_id: str
    admitted_at: str
    product_admission_manifest_id: str
    product_admission_manifest_status: str
    product_admission_policy_id: str
    admission_schema_version: str
    source_canonical_product_manifest_id: str
    source_canonical_product_manifest_hash: str
    source_result_admission_manifest_id: str
    source_result_admission_manifest_hash: str
    product_admission_record_count: int
    product_admission_records: tuple[
        CanonicalIntelligenceProductAdmissionRecord, ...
    ]
    all_product_hashes_verified: bool
    all_source_hashes_verified: bool
    all_lineage_verified: bool
    all_schemas_verified: bool
    all_products_read_only: bool
    all_products_deterministic: bool
    all_products_replayable: bool
    all_products_immutable: bool
    all_consumer_projection_policies_verified: bool
    all_execution_capabilities_disabled: bool
    all_products_admitted_unpublished: bool
    publication_allowed: bool
    publication_performed: bool
    query_allowed: bool
    projection_allowed: bool
    presentation_branch_required: bool
    demo_surface_dependency_required: bool
    source_consumed_without_reexecution: bool
    invocation_reexecution_performed: bool
    database_connection_performed: bool
    corpus_read_execution_repeated: bool
    source_mutation_allowed: bool
    source_mutation_performed: bool
    admission_artifact_persistence_allowed: bool
    product_admission_manifest_hash: str


class OracleIntelligenceAnalyticsCanonicalIntelligenceProductValidationAndAdmissionGate:
    def __init__(
        self,
        *,
        canonical_product_directory: Path | str = DEFAULT_CANONICAL_PRODUCT_DIRECTORY,
        product_admission_directory: Path | str = DEFAULT_PRODUCT_ADMISSION_DIRECTORY,
    ) -> None:
        self.canonical_product_directory = Path(canonical_product_directory)
        self.product_admission_directory = Path(product_admission_directory)

    def _load_source(self) -> dict[str, Any]:
        path = self.canonical_product_directory / "current.json"
        if not path.exists():
            raise OracleIntelligenceAnalyticsCanonicalIntelligenceProductAdmissionInvariantError(
                f"INT-OIA-036 canonical product artifact missing: {path}"
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise OracleIntelligenceAnalyticsCanonicalIntelligenceProductAdmissionInvariantError(
                "INT-OIA-036 canonical product artifact could not be decoded"
            ) from exc

        manifest_hash = payload.pop("canonical_product_manifest_hash", None)
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise OracleIntelligenceAnalyticsCanonicalIntelligenceProductAdmissionInvariantError(
                "INT-OIA-036 canonical product manifest hash mismatch"
            )
        payload["canonical_product_manifest_hash"] = manifest_hash

        required_manifest = {
            "schema_version": EXPECTED_SOURCE_SCHEMA_VERSION,
            "engine_id": EXPECTED_SOURCE_SCHEMA_VERSION,
            "product_schema_version": EXPECTED_PRODUCT_SCHEMA_VERSION,
            "product_class": EXPECTED_PRODUCT_CLASS,
            "product_mode": EXPECTED_PRODUCT_MODE,
            "canonical_product_manifest_status": (
                "canonical_intelligence_products_created"
            ),
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
        for field, expected in required_manifest.items():
            if payload.get(field) != expected:
                raise OracleIntelligenceAnalyticsCanonicalIntelligenceProductAdmissionInvariantError(
                    f"unsafe or incomplete INT-OIA-036 manifest field: {field}"
                )

        records = payload.get("canonical_product_records")
        if (
            not isinstance(records, list)
            or not records
            or payload.get("canonical_product_record_count") != len(records)
        ):
            raise OracleIntelligenceAnalyticsCanonicalIntelligenceProductAdmissionInvariantError(
                "INT-OIA-036 canonical product records invalid"
            )

        seen_product_ids: set[str] = set()
        for sequence, raw_record in enumerate(records, start=1):
            if not isinstance(raw_record, dict):
                raise OracleIntelligenceAnalyticsCanonicalIntelligenceProductAdmissionInvariantError(
                    "INT-OIA-036 canonical product record must be an object"
                )
            record = dict(raw_record)
            product_hash = record.pop("intelligence_product_hash", None)
            if not _valid_hash(product_hash) or stable_hash(record) != product_hash:
                raise OracleIntelligenceAnalyticsCanonicalIntelligenceProductAdmissionInvariantError(
                    "INT-OIA-036 canonical product record hash mismatch"
                )
            record["intelligence_product_hash"] = product_hash

            product_id = record.get("intelligence_product_id")
            if (
                record.get("sequence") != sequence
                or not isinstance(product_id, str)
                or not product_id
                or product_id in seen_product_ids
            ):
                raise OracleIntelligenceAnalyticsCanonicalIntelligenceProductAdmissionInvariantError(
                    "invalid sequence or duplicate canonical product identity"
                )
            seen_product_ids.add(product_id)

            required_record = {
                "product_schema_version": EXPECTED_PRODUCT_SCHEMA_VERSION,
                "product_class": EXPECTED_PRODUCT_CLASS,
                "product_mode": EXPECTED_PRODUCT_MODE,
                "product_state": EXPECTED_PRODUCT_STATE,
                "read_only": True,
                "deterministic": True,
                "replayable": True,
                "immutable": True,
                "publication_allowed": True,
                "publication_performed": False,
                "query_allowed": True,
                "projection_allowed": True,
                "source_result_hash_verified": True,
                "source_admission_hash_verified": True,
                "source_lineage_verified": True,
                "one_time_invocation_verified": True,
                "source_consumed_without_reexecution": True,
                "database_connection_performed": False,
                "corpus_read_execution_repeated": False,
                "source_mutation_performed": False,
                "product_status": EXPECTED_PRODUCT_STATUS,
            }
            for field, expected in required_record.items():
                if record.get(field) != expected:
                    raise OracleIntelligenceAnalyticsCanonicalIntelligenceProductAdmissionInvariantError(
                        f"unsafe canonical product field: {field}"
                    )

            projections = tuple(record.get("allowed_consumer_projections", ()))
            if projections != ALLOWED_PROJECTIONS:
                raise OracleIntelligenceAnalyticsCanonicalIntelligenceProductAdmissionInvariantError(
                    "canonical product consumer projection policy mismatch"
                )

            disabled = tuple(record.get("execution_capabilities_disabled", ()))
            if disabled != REQUIRED_EXECUTION_CAPABILITIES_DISABLED:
                raise OracleIntelligenceAnalyticsCanonicalIntelligenceProductAdmissionInvariantError(
                    "canonical product execution-disable policy mismatch"
                )

        return payload

    def admit(
        self,
        *,
        admitted_at: datetime,
        persist: bool = True,
    ) -> OracleIntelligenceAnalyticsCanonicalIntelligenceProductAdmissionManifest:
        admitted_at = _aware(admitted_at, "admitted_at")
        source = self._load_source()

        records: list[CanonicalIntelligenceProductAdmissionRecord] = []
        seen_admission_ids: set[str] = set()

        for sequence, product in enumerate(
            source["canonical_product_records"],
            start=1,
        ):
            admission_id = stable_hash(
                {
                    "admission_schema_version": ADMISSION_SCHEMA_VERSION,
                    "source_canonical_product_manifest_id": source[
                        "canonical_product_manifest_id"
                    ],
                    "source_canonical_product_manifest_hash": source[
                        "canonical_product_manifest_hash"
                    ],
                    "intelligence_product_id": product[
                        "intelligence_product_id"
                    ],
                    "intelligence_product_hash": product[
                        "intelligence_product_hash"
                    ],
                    "admitted_at": admitted_at.isoformat(),
                }
            )
            if admission_id in seen_admission_ids:
                raise OracleIntelligenceAnalyticsCanonicalIntelligenceProductAdmissionInvariantError(
                    "duplicate product admission identity"
                )
            seen_admission_ids.add(admission_id)

            body = {
                "sequence": sequence,
                "product_admission_id": admission_id,
                "intelligence_product_id": product[
                    "intelligence_product_id"
                ],
                "intelligence_product_hash": product[
                    "intelligence_product_hash"
                ],
                "source_canonical_product_manifest_id": source[
                    "canonical_product_manifest_id"
                ],
                "source_canonical_product_manifest_hash": source[
                    "canonical_product_manifest_hash"
                ],
                "source_result_admission_id": product[
                    "source_result_admission_id"
                ],
                "source_result_admission_record_hash": product[
                    "source_result_admission_record_hash"
                ],
                "product_schema_version": product[
                    "product_schema_version"
                ],
                "product_class": product["product_class"],
                "product_type": product["product_type"],
                "product_mode": product["product_mode"],
                "product_state": product["product_state"],
                "market_id": product["market_id"],
                "venue_id": product["venue_id"],
                "confidence": product["confidence"],
                "calibration_status": product["calibration_status"],
                "allowed_consumer_projections": tuple(
                    product["allowed_consumer_projections"]
                ),
                "read_only_verified": True,
                "deterministic_verified": True,
                "replayable_verified": True,
                "immutable_verified": True,
                "lineage_verified": True,
                "source_hashes_verified": True,
                "product_hash_verified": True,
                "schema_verified": True,
                "consumer_projection_policy_verified": True,
                "execution_capabilities_disabled_verified": True,
                "publication_allowed": True,
                "publication_performed": False,
                "query_allowed": True,
                "projection_allowed": True,
                "product_admission_status": (
                    "admitted_for_production_serving_not_published"
                ),
            }
            records.append(
                CanonicalIntelligenceProductAdmissionRecord(
                    **body,
                    product_admission_record_hash=stable_hash(body),
                )
            )

        manifest_id = stable_hash(
            {
                "source_canonical_product_manifest_id": source[
                    "canonical_product_manifest_id"
                ],
                "source_canonical_product_manifest_hash": source[
                    "canonical_product_manifest_hash"
                ],
                "admitted_at": admitted_at.isoformat(),
                "product_admission_record_hashes": [
                    record.product_admission_record_hash
                    for record in records
                ],
            }
        )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "admitted_at": admitted_at.isoformat(),
            "product_admission_manifest_id": manifest_id,
            "product_admission_manifest_status": STATUS_ADMITTED,
            "product_admission_policy_id": POLICY_ID,
            "admission_schema_version": ADMISSION_SCHEMA_VERSION,
            "source_canonical_product_manifest_id": source[
                "canonical_product_manifest_id"
            ],
            "source_canonical_product_manifest_hash": source[
                "canonical_product_manifest_hash"
            ],
            "source_result_admission_manifest_id": source[
                "source_result_admission_manifest_id"
            ],
            "source_result_admission_manifest_hash": source[
                "source_result_admission_manifest_hash"
            ],
            "product_admission_record_count": len(records),
            "product_admission_records": tuple(records),
            "all_product_hashes_verified": True,
            "all_source_hashes_verified": True,
            "all_lineage_verified": True,
            "all_schemas_verified": True,
            "all_products_read_only": True,
            "all_products_deterministic": True,
            "all_products_replayable": True,
            "all_products_immutable": True,
            "all_consumer_projection_policies_verified": True,
            "all_execution_capabilities_disabled": True,
            "all_products_admitted_unpublished": True,
            "publication_allowed": True,
            "publication_performed": False,
            "query_allowed": True,
            "projection_allowed": True,
            "presentation_branch_required": False,
            "demo_surface_dependency_required": False,
            "source_consumed_without_reexecution": True,
            "invocation_reexecution_performed": False,
            "database_connection_performed": False,
            "corpus_read_execution_repeated": False,
            "source_mutation_allowed": False,
            "source_mutation_performed": False,
            "admission_artifact_persistence_allowed": True,
        }
        manifest = OracleIntelligenceAnalyticsCanonicalIntelligenceProductAdmissionManifest(
            **body,
            product_admission_manifest_hash=stable_hash(body),
        )

        if persist:
            payload = asdict(manifest)
            _atomic_write(
                self.product_admission_directory / "current.json",
                payload,
            )
            _atomic_write(
                self.product_admission_directory
                / "manifests"
                / f"{manifest.product_admission_manifest_id}.json",
                payload,
            )
            for record in manifest.product_admission_records:
                _atomic_write(
                    self.product_admission_directory
                    / "admissions"
                    / f"{record.product_admission_id}.json",
                    asdict(record),
                )

        return manifest


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "ADMISSION_SCHEMA_VERSION",
    "CanonicalIntelligenceProductAdmissionRecord",
    "OracleIntelligenceAnalyticsCanonicalIntelligenceProductAdmissionManifest",
    "OracleIntelligenceAnalyticsCanonicalIntelligenceProductValidationAndAdmissionGate",
    "OracleIntelligenceAnalyticsCanonicalIntelligenceProductAdmissionInvariantError",
    "stable_hash",
]
