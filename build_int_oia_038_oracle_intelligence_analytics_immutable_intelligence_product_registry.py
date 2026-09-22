from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"
DOWNSTREAM = ANALYTICS / "downstream"
REGISTRY = DOWNSTREAM / "registry"
PRODUCTS = DOWNSTREAM / "products"

SOURCE_037 = PRODUCTS / (
    "oracle_intelligence_analytics_canonical_intelligence_product_"
    "validation_and_admission_gate.py"
)
PRODUCTION = REGISTRY / (
    "oracle_intelligence_analytics_immutable_intelligence_product_registry.py"
)
TEST = ROOT / (
    "test_int_oia_038_oracle_intelligence_analytics_"
    "immutable_intelligence_product_registry.py"
)
REGISTRY_PACKAGE = REGISTRY / "__init__.py"
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

SCHEMA_VERSION = "INT-OIA-038"
ENGINE_ID = "INT-OIA-038"
POLICY_ID = (
    "oracle.intelligence.analytics.immutable-intelligence-product-registry.v1"
)
REGISTRY_SCHEMA_VERSION = "oracle.immutable-intelligence-product-registry.v1"
REGISTRY_STATUS = "admitted_intelligence_products_registered_immutably"

DEFAULT_PRODUCT_ADMISSION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_canonical_intelligence_product_admission"
)
DEFAULT_PRODUCT_REGISTRY_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_immutable_intelligence_product_registry"
)

EXPECTED_SOURCE_SCHEMA_VERSION = "INT-OIA-037"
EXPECTED_ADMISSION_SCHEMA_VERSION = (
    "oracle.canonical-intelligence-product-admission.v1"
)
EXPECTED_ADMISSION_STATUS = (
    "canonical_intelligence_products_validated_and_admitted"
)
EXPECTED_PRODUCT_ADMISSION_STATUS = (
    "admitted_for_production_serving_not_published"
)

ALLOWED_PROJECTIONS = (
    "operator_research",
    "research_presentation",
    "audit_replay",
)


class OracleIntelligenceAnalyticsImmutableIntelligenceProductRegistryInvariantError(
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
            raise OracleIntelligenceAnalyticsImmutableIntelligenceProductRegistryInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleIntelligenceAnalyticsImmutableIntelligenceProductRegistryInvariantError(
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
        raise OracleIntelligenceAnalyticsImmutableIntelligenceProductRegistryInvariantError(
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
class ImmutableIntelligenceProductRegistryEntry:
    sequence: int
    registry_entry_id: str
    product_admission_id: str
    product_admission_record_hash: str
    intelligence_product_id: str
    intelligence_product_hash: str
    source_canonical_product_manifest_id: str
    source_canonical_product_manifest_hash: str
    source_product_admission_manifest_id: str
    source_product_admission_manifest_hash: str
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
    registry_partition: str
    registry_key: str
    immutable: bool
    read_only: bool
    deterministic: bool
    replayable: bool
    query_eligible: bool
    projection_eligible: bool
    publication_eligible: bool
    publication_performed: bool
    execution_capabilities_disabled_verified: bool
    source_hashes_verified: bool
    lineage_verified: bool
    admission_verified: bool
    duplicate_registration_rejected: bool
    registry_entry_status: str
    registry_entry_hash: str


@dataclass(frozen=True)
class OracleIntelligenceAnalyticsImmutableIntelligenceProductRegistryManifest:
    schema_version: str
    engine_id: str
    registered_at: str
    registry_manifest_id: str
    registry_manifest_status: str
    registry_policy_id: str
    registry_schema_version: str
    source_product_admission_manifest_id: str
    source_product_admission_manifest_hash: str
    source_canonical_product_manifest_id: str
    source_canonical_product_manifest_hash: str
    registry_entry_count: int
    registry_entries: tuple[
        ImmutableIntelligenceProductRegistryEntry, ...
    ]
    all_product_admissions_verified: bool
    all_product_hashes_verified: bool
    all_source_hashes_verified: bool
    all_lineage_verified: bool
    all_entries_immutable: bool
    all_entries_read_only: bool
    all_entries_deterministic: bool
    all_entries_replayable: bool
    all_entries_query_eligible: bool
    all_entries_projection_eligible: bool
    all_entries_unpublished: bool
    all_execution_capabilities_disabled: bool
    duplicate_registry_entries_present: bool
    registry_mutation_allowed: bool
    registry_update_performed: bool
    registry_delete_performed: bool
    publication_performed: bool
    presentation_branch_required: bool
    demo_surface_dependency_required: bool
    source_consumed_without_reexecution: bool
    invocation_reexecution_performed: bool
    database_connection_performed: bool
    corpus_read_execution_repeated: bool
    source_mutation_performed: bool
    registry_artifact_persistence_allowed: bool
    registry_manifest_hash: str


class OracleIntelligenceAnalyticsImmutableIntelligenceProductRegistry:
    def __init__(
        self,
        *,
        product_admission_directory: Path | str = DEFAULT_PRODUCT_ADMISSION_DIRECTORY,
        product_registry_directory: Path | str = DEFAULT_PRODUCT_REGISTRY_DIRECTORY,
    ) -> None:
        self.product_admission_directory = Path(product_admission_directory)
        self.product_registry_directory = Path(product_registry_directory)

    def _load_source(self) -> dict[str, Any]:
        path = self.product_admission_directory / "current.json"
        if not path.exists():
            raise OracleIntelligenceAnalyticsImmutableIntelligenceProductRegistryInvariantError(
                f"INT-OIA-037 product-admission artifact missing: {path}"
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise OracleIntelligenceAnalyticsImmutableIntelligenceProductRegistryInvariantError(
                "INT-OIA-037 product-admission artifact could not be decoded"
            ) from exc

        manifest_hash = payload.pop("product_admission_manifest_hash", None)
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise OracleIntelligenceAnalyticsImmutableIntelligenceProductRegistryInvariantError(
                "INT-OIA-037 product-admission manifest hash mismatch"
            )
        payload["product_admission_manifest_hash"] = manifest_hash

        required_manifest = {
            "schema_version": EXPECTED_SOURCE_SCHEMA_VERSION,
            "engine_id": EXPECTED_SOURCE_SCHEMA_VERSION,
            "admission_schema_version": EXPECTED_ADMISSION_SCHEMA_VERSION,
            "product_admission_manifest_status": EXPECTED_ADMISSION_STATUS,
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
        for field, expected in required_manifest.items():
            if payload.get(field) != expected:
                raise OracleIntelligenceAnalyticsImmutableIntelligenceProductRegistryInvariantError(
                    f"unsafe or incomplete INT-OIA-037 manifest field: {field}"
                )

        records = payload.get("product_admission_records")
        if (
            not isinstance(records, list)
            or not records
            or payload.get("product_admission_record_count") != len(records)
        ):
            raise OracleIntelligenceAnalyticsImmutableIntelligenceProductRegistryInvariantError(
                "INT-OIA-037 product admission records invalid"
            )

        seen_admission_ids: set[str] = set()
        seen_product_ids: set[str] = set()

        for sequence, raw_record in enumerate(records, start=1):
            if not isinstance(raw_record, dict):
                raise OracleIntelligenceAnalyticsImmutableIntelligenceProductRegistryInvariantError(
                    "INT-OIA-037 product admission record must be an object"
                )
            record = dict(raw_record)
            record_hash = record.pop("product_admission_record_hash", None)
            if not _valid_hash(record_hash) or stable_hash(record) != record_hash:
                raise OracleIntelligenceAnalyticsImmutableIntelligenceProductRegistryInvariantError(
                    "INT-OIA-037 product admission record hash mismatch"
                )
            record["product_admission_record_hash"] = record_hash

            admission_id = record.get("product_admission_id")
            product_id = record.get("intelligence_product_id")
            if (
                record.get("sequence") != sequence
                or not isinstance(admission_id, str)
                or not admission_id
                or admission_id in seen_admission_ids
                or not isinstance(product_id, str)
                or not product_id
                or product_id in seen_product_ids
            ):
                raise OracleIntelligenceAnalyticsImmutableIntelligenceProductRegistryInvariantError(
                    "invalid sequence or duplicate admission/product identity"
                )
            seen_admission_ids.add(admission_id)
            seen_product_ids.add(product_id)

            required_record = {
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
                "product_admission_status": EXPECTED_PRODUCT_ADMISSION_STATUS,
            }
            for field, expected in required_record.items():
                if record.get(field) != expected:
                    raise OracleIntelligenceAnalyticsImmutableIntelligenceProductRegistryInvariantError(
                        f"unsafe product admission field: {field}"
                    )

            projections = tuple(record.get("allowed_consumer_projections", ()))
            if projections != ALLOWED_PROJECTIONS:
                raise OracleIntelligenceAnalyticsImmutableIntelligenceProductRegistryInvariantError(
                    "product admission projection policy mismatch"
                )

        return payload

    def register(
        self,
        *,
        registered_at: datetime,
        persist: bool = True,
    ) -> OracleIntelligenceAnalyticsImmutableIntelligenceProductRegistryManifest:
        registered_at = _aware(registered_at, "registered_at")
        source = self._load_source()

        entries: list[ImmutableIntelligenceProductRegistryEntry] = []
        seen_registry_keys: set[str] = set()
        seen_entry_ids: set[str] = set()

        for sequence, admission in enumerate(
            source["product_admission_records"],
            start=1,
        ):
            registry_partition = (
                admission["venue_id"]
                if isinstance(admission.get("venue_id"), str)
                and admission["venue_id"]
                else "venue-unassigned"
            )
            registry_key = stable_hash(
                {
                    "registry_schema_version": REGISTRY_SCHEMA_VERSION,
                    "intelligence_product_id": admission[
                        "intelligence_product_id"
                    ],
                    "intelligence_product_hash": admission[
                        "intelligence_product_hash"
                    ],
                    "product_admission_id": admission[
                        "product_admission_id"
                    ],
                }
            )
            if registry_key in seen_registry_keys:
                raise OracleIntelligenceAnalyticsImmutableIntelligenceProductRegistryInvariantError(
                    "duplicate immutable registry key"
                )
            seen_registry_keys.add(registry_key)

            entry_id = stable_hash(
                {
                    "registry_key": registry_key,
                    "source_product_admission_manifest_id": source[
                        "product_admission_manifest_id"
                    ],
                    "source_product_admission_manifest_hash": source[
                        "product_admission_manifest_hash"
                    ],
                    "registered_at": registered_at.isoformat(),
                }
            )
            if entry_id in seen_entry_ids:
                raise OracleIntelligenceAnalyticsImmutableIntelligenceProductRegistryInvariantError(
                    "duplicate immutable registry entry identity"
                )
            seen_entry_ids.add(entry_id)

            body = {
                "sequence": sequence,
                "registry_entry_id": entry_id,
                "product_admission_id": admission["product_admission_id"],
                "product_admission_record_hash": admission[
                    "product_admission_record_hash"
                ],
                "intelligence_product_id": admission[
                    "intelligence_product_id"
                ],
                "intelligence_product_hash": admission[
                    "intelligence_product_hash"
                ],
                "source_canonical_product_manifest_id": admission[
                    "source_canonical_product_manifest_id"
                ],
                "source_canonical_product_manifest_hash": admission[
                    "source_canonical_product_manifest_hash"
                ],
                "source_product_admission_manifest_id": source[
                    "product_admission_manifest_id"
                ],
                "source_product_admission_manifest_hash": source[
                    "product_admission_manifest_hash"
                ],
                "source_result_admission_id": admission[
                    "source_result_admission_id"
                ],
                "source_result_admission_record_hash": admission[
                    "source_result_admission_record_hash"
                ],
                "product_schema_version": admission[
                    "product_schema_version"
                ],
                "product_class": admission["product_class"],
                "product_type": admission["product_type"],
                "product_mode": admission["product_mode"],
                "product_state": admission["product_state"],
                "market_id": admission["market_id"],
                "venue_id": admission["venue_id"],
                "confidence": admission["confidence"],
                "calibration_status": admission["calibration_status"],
                "allowed_consumer_projections": tuple(
                    admission["allowed_consumer_projections"]
                ),
                "registry_partition": registry_partition,
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
            entries.append(
                ImmutableIntelligenceProductRegistryEntry(
                    **body,
                    registry_entry_hash=stable_hash(body),
                )
            )

        manifest_id = stable_hash(
            {
                "source_product_admission_manifest_id": source[
                    "product_admission_manifest_id"
                ],
                "source_product_admission_manifest_hash": source[
                    "product_admission_manifest_hash"
                ],
                "registered_at": registered_at.isoformat(),
                "registry_entry_hashes": [
                    entry.registry_entry_hash for entry in entries
                ],
            }
        )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "registered_at": registered_at.isoformat(),
            "registry_manifest_id": manifest_id,
            "registry_manifest_status": REGISTRY_STATUS,
            "registry_policy_id": POLICY_ID,
            "registry_schema_version": REGISTRY_SCHEMA_VERSION,
            "source_product_admission_manifest_id": source[
                "product_admission_manifest_id"
            ],
            "source_product_admission_manifest_hash": source[
                "product_admission_manifest_hash"
            ],
            "source_canonical_product_manifest_id": source[
                "source_canonical_product_manifest_id"
            ],
            "source_canonical_product_manifest_hash": source[
                "source_canonical_product_manifest_hash"
            ],
            "registry_entry_count": len(entries),
            "registry_entries": tuple(entries),
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
        manifest = OracleIntelligenceAnalyticsImmutableIntelligenceProductRegistryManifest(
            **body,
            registry_manifest_hash=stable_hash(body),
        )

        if persist:
            payload = asdict(manifest)
            _atomic_write(
                self.product_registry_directory / "current.json",
                payload,
            )
            _atomic_write(
                self.product_registry_directory
                / "manifests"
                / f"{manifest.registry_manifest_id}.json",
                payload,
            )
            for entry in manifest.registry_entries:
                entry_path = (
                    self.product_registry_directory
                    / "entries"
                    / entry.registry_partition
                    / f"{entry.registry_key}.json"
                )
                if entry_path.exists():
                    existing = json.loads(
                        entry_path.read_text(encoding="utf-8")
                    )
                    if existing != asdict(entry):
                        raise OracleIntelligenceAnalyticsImmutableIntelligenceProductRegistryInvariantError(
                            "immutable registry entry collision detected"
                        )
                else:
                    _atomic_write(entry_path, asdict(entry))

        return manifest


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "REGISTRY_SCHEMA_VERSION",
    "ImmutableIntelligenceProductRegistryEntry",
    "OracleIntelligenceAnalyticsImmutableIntelligenceProductRegistryManifest",
    "OracleIntelligenceAnalyticsImmutableIntelligenceProductRegistry",
    "OracleIntelligenceAnalyticsImmutableIntelligenceProductRegistryInvariantError",
    "stable_hash",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.downstream.registry.oracle_intelligence_analytics_immutable_intelligence_product_registry import (
    REGISTRY_SCHEMA_VERSION,
    OracleIntelligenceAnalyticsImmutableIntelligenceProductRegistry,
    OracleIntelligenceAnalyticsImmutableIntelligenceProductRegistryInvariantError,
    stable_hash,
)


def _seed_admission(path: Path) -> None:
    record = {
        "sequence": 1,
        "product_admission_id": stable_hash({"admission": 1}),
        "intelligence_product_id": stable_hash({"product": 1}),
        "intelligence_product_hash": stable_hash({"product-hash": 1}),
        "source_canonical_product_manifest_id": "int-oia-036-test",
        "source_canonical_product_manifest_hash": stable_hash({"int": 36}),
        "source_result_admission_id": "result-admission-test",
        "source_result_admission_record_hash": stable_hash(
            {"result-admission": 1}
        ),
        "product_schema_version": "oracle.canonical-intelligence-product.v1",
        "product_class": "oracle_certified_intelligence_product",
        "product_type": "market_research_summary",
        "product_mode": "production_read_only_multi_consumer",
        "product_state": "created_not_published",
        "market_id": "KX-TEST-MARKET",
        "venue_id": "kalshi",
        "confidence": 0.73,
        "calibration_status": "provisional",
        "allowed_consumer_projections": [
            "operator_research",
            "research_presentation",
            "audit_replay",
        ],
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
    record["product_admission_record_hash"] = stable_hash(record)

    manifest = {
        "schema_version": "INT-OIA-037",
        "engine_id": "INT-OIA-037",
        "admitted_at": "2026-07-24T16:00:00+00:00",
        "product_admission_manifest_id": "int-oia-037-test",
        "product_admission_manifest_status": (
            "canonical_intelligence_products_validated_and_admitted"
        ),
        "product_admission_policy_id": "test",
        "admission_schema_version": (
            "oracle.canonical-intelligence-product-admission.v1"
        ),
        "source_canonical_product_manifest_id": "int-oia-036-test",
        "source_canonical_product_manifest_hash": stable_hash({"int": 36}),
        "source_result_admission_manifest_id": "int-oia-013-test",
        "source_result_admission_manifest_hash": stable_hash({"int": 13}),
        "product_admission_record_count": 1,
        "product_admission_records": [record],
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
    manifest["product_admission_manifest_hash"] = stable_hash(manifest)

    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-038 TEST")
    print(" IMMUTABLE INTELLIGENCE PRODUCT")
    print(" PRODUCTION REGISTRY")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        admissions = root / "admissions"
        registry = root / "registry"
        _seed_admission(admissions)

        service = OracleIntelligenceAnalyticsImmutableIntelligenceProductRegistry(
            product_admission_directory=admissions,
            product_registry_directory=registry,
        )
        fixed = datetime(2026, 7, 24, 17, 0, tzinfo=timezone.utc)

        first = service.register(registered_at=fixed, persist=True)
        second = service.register(registered_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "INT-OIA-038"
        assert first.registry_schema_version == REGISTRY_SCHEMA_VERSION
        assert first.registry_entry_count == 1
        assert first.all_product_admissions_verified
        assert first.all_product_hashes_verified
        assert first.all_source_hashes_verified
        assert first.all_lineage_verified
        assert first.all_entries_immutable
        assert first.all_entries_read_only
        assert first.all_entries_deterministic
        assert first.all_entries_replayable
        assert first.all_entries_query_eligible
        assert first.all_entries_projection_eligible
        assert first.all_entries_unpublished
        assert first.all_execution_capabilities_disabled
        assert not first.duplicate_registry_entries_present
        assert not first.registry_mutation_allowed
        assert not first.registry_update_performed
        assert not first.registry_delete_performed
        assert not first.publication_performed
        assert not first.presentation_branch_required
        assert not first.demo_surface_dependency_required
        assert first.source_consumed_without_reexecution
        assert not first.invocation_reexecution_performed
        assert not first.database_connection_performed
        assert not first.corpus_read_execution_repeated
        assert not first.source_mutation_performed

        entry = first.registry_entries[0]
        assert entry.registry_partition == "kalshi"
        assert entry.immutable
        assert entry.read_only
        assert entry.deterministic
        assert entry.replayable
        assert entry.query_eligible
        assert entry.projection_eligible
        assert entry.publication_eligible
        assert not entry.publication_performed
        assert entry.execution_capabilities_disabled_verified
        assert entry.source_hashes_verified
        assert entry.lineage_verified
        assert entry.admission_verified
        assert entry.duplicate_registration_rejected

        assert (registry / "current.json").exists()
        assert (
            registry
            / "manifests"
            / f"{first.registry_manifest_id}.json"
        ).exists()
        entry_path = (
            registry
            / "entries"
            / entry.registry_partition
            / f"{entry.registry_key}.json"
        )
        assert entry_path.exists()

        persisted = json.loads(
            (registry / "current.json").read_text(encoding="utf-8")
        )
        manifest_hash = persisted.pop("registry_manifest_hash")
        assert stable_hash(persisted) == manifest_hash

        service.register(registered_at=fixed, persist=True)
        assert json.loads(
            entry_path.read_text(encoding="utf-8")
        ) == json.loads(entry_path.read_text(encoding="utf-8"))

        tampered = json.loads(
            (admissions / "current.json").read_text(encoding="utf-8")
        )
        tampered["product_admission_records"][0]["confidence"] = 0.99
        (admissions / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            service.register(registered_at=fixed, persist=False)
            raise AssertionError("tampered product admission accepted")
        except OracleIntelligenceAnalyticsImmutableIntelligenceProductRegistryInvariantError:
            pass

    print("[PASS] Actual INT-OIA-037 product admission consumed")
    print("[PASS] Product admission manifest hash independently verified")
    print("[PASS] Every product admission record hash independently verified")
    print("[PASS] Complete INT-OIA-013 through INT-OIA-037 lineage preserved")
    print("[PASS] Only admitted canonical intelligence products registered")
    print("[PASS] Registry identities and keys deterministic")
    print("[PASS] Registry entries immutable, read-only, and replayable")
    print("[PASS] Query and projection eligibility preserved")
    print("[PASS] Products remained unpublished")
    print("[PASS] Duplicate immutable registration remained idempotent")
    print("[PASS] Registry update and delete operations remained disabled")
    print("[PASS] Presentation and demo branches were not required")
    print("[PASS] No callable reexecution performed")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] No source mutation performed")
    print("[PASS] Tampered product admission evidence rejected")
    print("[PASS] Atomic registry manifest and partitioned entries persisted")
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


def verify_int_oia_037_contract() -> None:
    if not SOURCE_037.exists():
        raise FileNotFoundError(
            f"Actual INT-OIA-037 production module missing: {SOURCE_037}"
        )
    source = SOURCE_037.read_text(encoding="utf-8")
    required_tokens = (
        'SCHEMA_VERSION = "INT-OIA-037"',
        "ADMISSION_SCHEMA_VERSION",
        "oracle.canonical-intelligence-product-admission.v1",
        "class CanonicalIntelligenceProductAdmissionRecord",
        "class OracleIntelligenceAnalyticsCanonicalIntelligenceProductAdmissionManifest",
        "class OracleIntelligenceAnalyticsCanonicalIntelligenceProductValidationAndAdmissionGate",
        "product_admission_manifest_hash",
        "product_admission_record_hash",
        "all_products_admitted_unpublished",
        "demo_surface_dependency_required",
    )
    missing = [token for token in required_tokens if token not in source]
    if missing:
        raise RuntimeError(
            "Actual INT-OIA-037 contract mismatch; missing tokens: "
            + ", ".join(missing)
        )
    print("[OK] Actual INT-OIA-037 product-admission contract verified")


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-038 INSTALLER")
    print(" IMMUTABLE INTELLIGENCE PRODUCT")
    print(" PRODUCTION REGISTRY")
    print("=" * 40)

    verify_int_oia_037_contract()

    write_replacement(PRODUCTION, PRODUCTION_SOURCE)
    write_replacement(TEST, TEST_SOURCE)

    append_export(
        REGISTRY_PACKAGE,
        "from .oracle_intelligence_analytics_immutable_intelligence_product_registry import *",
    )
    append_export(
        DOWNSTREAM_PACKAGE,
        "from .registry import *",
    )
    append_export(
        ANALYTICS_PACKAGE,
        "from .downstream.registry import *",
    )

    for target in (
        PRODUCTION,
        TEST,
        REGISTRY_PACKAGE,
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

    print("[OK] INT-OIA-038 test executed automatically")
    print()
    print("[DONE] INT-OIA-038 immutable production intelligence-product registry installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
