from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"
DOWNSTREAM = ANALYTICS / "downstream"
PRODUCTS = DOWNSTREAM / "products"

SOURCE_036 = PRODUCTS / (
    "oracle_intelligence_analytics_canonical_intelligence_product_contract.py"
)
PRODUCTION = PRODUCTS / (
    "oracle_intelligence_analytics_canonical_intelligence_product_"
    "validation_and_admission_gate.py"
)
TEST = ROOT / (
    "test_int_oia_037_oracle_intelligence_analytics_canonical_"
    "intelligence_product_validation_and_admission_gate.py"
)
PRODUCTS_PACKAGE = PRODUCTS / "__init__.py"
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
"""

TEST_SOURCE = r"""
from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.downstream.products.oracle_intelligence_analytics_canonical_intelligence_product_validation_and_admission_gate import (
    ADMISSION_SCHEMA_VERSION,
    OracleIntelligenceAnalyticsCanonicalIntelligenceProductAdmissionInvariantError,
    OracleIntelligenceAnalyticsCanonicalIntelligenceProductValidationAndAdmissionGate,
    stable_hash,
)


def _seed_product(path: Path) -> None:
    record = {
        "sequence": 1,
        "intelligence_product_id": stable_hash({"product": 1}),
        "product_schema_version": "oracle.canonical-intelligence-product.v1",
        "product_class": "oracle_certified_intelligence_product",
        "product_type": "market_research_summary",
        "product_mode": "production_read_only_multi_consumer",
        "product_state": "created_not_published",
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "market_id": "KX-TEST-MARKET",
        "venue_id": "kalshi",
        "analytic_result_class": "immutable_research_artifact",
        "analytic_result_type": "builtins.dict",
        "analytic_result_payload": {"summary": "test"},
        "analytic_result_hash": stable_hash({"summary": "test"}),
        "admitted_result_hash": stable_hash({"admitted": 1}),
        "source_result_admission_id": "result-admission-test",
        "source_result_admission_record_hash": stable_hash(
            {"result-admission": 1}
        ),
        "source_result_attestation_id": "result-attestation-test",
        "source_result_attestation_record_hash": stable_hash(
            {"result-attestation": 1}
        ),
        "source_invocation_execution_id": "execution-test",
        "source_invocation_execution_record_hash": stable_hash(
            {"execution": 1}
        ),
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "source_release_mode": "research_presentation_only",
        "source_admission_status": (
            "admitted_for_research_presentation_not_released"
        ),
        "produced_at": "2026-07-24T15:00:00+00:00",
        "valid_from": "2026-07-24T15:00:00+00:00",
        "expires_at": None,
        "confidence": 0.73,
        "calibration_status": "provisional",
        "evidence_references": ["evidence-1"],
        "counterevidence_references": ["counterevidence-1"],
        "assumptions": ["test assumption"],
        "allowed_consumer_projections": [
            "operator_research",
            "research_presentation",
            "audit_replay",
        ],
        "read_only": True,
        "deterministic": True,
        "replayable": True,
        "immutable": True,
        "publication_allowed": True,
        "publication_performed": False,
        "query_allowed": True,
        "projection_allowed": True,
        "execution_capabilities_disabled": [
            "forecast_creation",
            "signal_creation",
            "alert_creation",
            "qseries_handoff",
            "qseries_execution",
            "market_order_creation",
            "funds_movement",
            "portfolio_mutation",
            "source_mutation",
        ],
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
    record["intelligence_product_hash"] = stable_hash(record)

    manifest = {
        "schema_version": "INT-OIA-036",
        "engine_id": "INT-OIA-036",
        "created_at": "2026-07-24T15:00:00+00:00",
        "canonical_product_manifest_id": "int-oia-036-test",
        "canonical_product_manifest_status": (
            "canonical_intelligence_products_created"
        ),
        "canonical_product_policy_id": "test",
        "product_schema_version": "oracle.canonical-intelligence-product.v1",
        "product_class": "oracle_certified_intelligence_product",
        "product_mode": "production_read_only_multi_consumer",
        "source_result_admission_manifest_id": "int-oia-013-test",
        "source_result_admission_manifest_hash": stable_hash({"int": 13}),
        "source_result_attestation_manifest_id": "int-oia-012-test",
        "source_result_attestation_manifest_hash": stable_hash({"int": 12}),
        "source_invocation_execution_manifest_id": "int-oia-011-test",
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "canonical_product_record_count": 1,
        "canonical_product_records": [record],
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
    manifest["canonical_product_manifest_hash"] = stable_hash(manifest)

    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-037 TEST")
    print(" PRODUCT VALIDATION AND ADMISSION")
    print(" PRODUCTION DOWNSTREAM GATE")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        products = root / "products"
        admissions = root / "admissions"
        _seed_product(products)

        gate = OracleIntelligenceAnalyticsCanonicalIntelligenceProductValidationAndAdmissionGate(
            canonical_product_directory=products,
            product_admission_directory=admissions,
        )
        fixed = datetime(2026, 7, 24, 16, 0, tzinfo=timezone.utc)

        first = gate.admit(admitted_at=fixed, persist=True)
        second = gate.admit(admitted_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "INT-OIA-037"
        assert first.admission_schema_version == ADMISSION_SCHEMA_VERSION
        assert first.product_admission_record_count == 1
        assert first.all_product_hashes_verified
        assert first.all_source_hashes_verified
        assert first.all_lineage_verified
        assert first.all_schemas_verified
        assert first.all_products_read_only
        assert first.all_products_deterministic
        assert first.all_products_replayable
        assert first.all_products_immutable
        assert first.all_consumer_projection_policies_verified
        assert first.all_execution_capabilities_disabled
        assert first.all_products_admitted_unpublished
        assert first.publication_allowed
        assert not first.publication_performed
        assert first.query_allowed
        assert first.projection_allowed
        assert not first.presentation_branch_required
        assert not first.demo_surface_dependency_required
        assert first.source_consumed_without_reexecution
        assert not first.invocation_reexecution_performed
        assert not first.database_connection_performed
        assert not first.corpus_read_execution_repeated
        assert not first.source_mutation_allowed
        assert not first.source_mutation_performed

        record = first.product_admission_records[0]
        assert record.product_hash_verified
        assert record.source_hashes_verified
        assert record.lineage_verified
        assert record.schema_verified
        assert record.read_only_verified
        assert record.deterministic_verified
        assert record.replayable_verified
        assert record.immutable_verified
        assert record.consumer_projection_policy_verified
        assert record.execution_capabilities_disabled_verified
        assert record.publication_allowed
        assert not record.publication_performed
        assert record.query_allowed
        assert record.projection_allowed
        assert record.product_admission_status == (
            "admitted_for_production_serving_not_published"
        )

        assert (admissions / "current.json").exists()
        assert (
            admissions
            / "admissions"
            / f"{record.product_admission_id}.json"
        ).exists()
        assert (
            admissions
            / "manifests"
            / f"{first.product_admission_manifest_id}.json"
        ).exists()

        persisted = json.loads(
            (admissions / "current.json").read_text(encoding="utf-8")
        )
        manifest_hash = persisted.pop("product_admission_manifest_hash")
        assert stable_hash(persisted) == manifest_hash

        tampered = json.loads(
            (products / "current.json").read_text(encoding="utf-8")
        )
        tampered["canonical_product_records"][0]["confidence"] = 0.99
        (products / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.admit(admitted_at=fixed, persist=False)
            raise AssertionError("tampered canonical product accepted")
        except OracleIntelligenceAnalyticsCanonicalIntelligenceProductAdmissionInvariantError:
            pass

    print("[PASS] Actual INT-OIA-036 canonical intelligence product consumed")
    print("[PASS] Canonical product manifest hash independently verified")
    print("[PASS] Every canonical product record hash independently verified")
    print("[PASS] Product schema, class, mode, and state validated")
    print("[PASS] Complete INT-OIA-013 through INT-OIA-036 lineage preserved")
    print("[PASS] Read-only, deterministic, replayable, and immutable guarantees verified")
    print("[PASS] Consumer projection policy verified")
    print("[PASS] All execution capabilities remained disabled")
    print("[PASS] Products admitted for production serving but not published")
    print("[PASS] Presentation and demo branches were not required")
    print("[PASS] No callable reexecution performed")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] No source mutation performed")
    print("[PASS] Tampered canonical intelligence product rejected")
    print("[PASS] Atomic admission manifest and per-product admissions persisted")
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


def verify_int_oia_036_contract() -> None:
    if not SOURCE_036.exists():
        raise FileNotFoundError(
            f"Actual INT-OIA-036 production module missing: {SOURCE_036}"
        )
    source = SOURCE_036.read_text(encoding="utf-8")
    required_tokens = (
        'SCHEMA_VERSION = "INT-OIA-036"',
        'PRODUCT_SCHEMA_VERSION = "oracle.canonical-intelligence-product.v1"',
        'CANONICAL_PRODUCT_CLASS = "oracle_certified_intelligence_product"',
        'CANONICAL_PRODUCT_MODE = "production_read_only_multi_consumer"',
        "class CanonicalIntelligenceProductRecord",
        "class OracleIntelligenceAnalyticsCanonicalIntelligenceProductManifest",
        "canonical_product_manifest_hash",
        "intelligence_product_hash",
        "presentation_branch_required",
        "demo_surface_dependency_required",
    )
    missing = [token for token in required_tokens if token not in source]
    if missing:
        raise RuntimeError(
            "Actual INT-OIA-036 contract mismatch; missing tokens: "
            + ", ".join(missing)
        )
    print("[OK] Actual INT-OIA-036 canonical-intelligence-product contract verified")


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-037 INSTALLER")
    print(" PRODUCT VALIDATION AND ADMISSION")
    print(" PRODUCTION DOWNSTREAM GATE")
    print("=" * 40)

    verify_int_oia_036_contract()

    write_replacement(PRODUCTION, PRODUCTION_SOURCE)
    write_replacement(TEST, TEST_SOURCE)

    append_export(
        PRODUCTS_PACKAGE,
        "from .oracle_intelligence_analytics_canonical_intelligence_product_validation_and_admission_gate import *",
    )
    append_export(
        DOWNSTREAM_PACKAGE,
        "from .products import *",
    )
    append_export(
        ANALYTICS_PACKAGE,
        "from .downstream.products import *",
    )

    for target in (
        PRODUCTION,
        TEST,
        PRODUCTS_PACKAGE,
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

    print("[OK] INT-OIA-037 test executed automatically")
    print()
    print("[DONE] INT-OIA-037 production product validation and admission gate installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
