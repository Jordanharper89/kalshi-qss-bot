from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "INT-OIA-039"
ENGINE_ID = "INT-OIA-039"
POLICY_ID = (
    "oracle.intelligence.analytics.production-intelligence-product."
    "registry-read-contract.v1"
)
READ_CONTRACT_SCHEMA_VERSION = (
    "oracle.production-intelligence-product-registry-read-contract.v1"
)
READ_STATUS = "immutable_registry_read_contract_satisfied"

DEFAULT_PRODUCT_REGISTRY_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_immutable_intelligence_product_registry"
)

EXPECTED_SOURCE_SCHEMA_VERSION = "INT-OIA-038"
EXPECTED_REGISTRY_SCHEMA_VERSION = (
    "oracle.immutable-intelligence-product-registry.v1"
)
EXPECTED_REGISTRY_STATUS = (
    "admitted_intelligence_products_registered_immutably"
)

ALLOWED_PROJECTIONS = (
    "operator_research",
    "research_presentation",
    "audit_replay",
)


class OracleIntelligenceAnalyticsProductionIntelligenceProductRegistryReadInvariantError(
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
            raise OracleIntelligenceAnalyticsProductionIntelligenceProductRegistryReadInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleIntelligenceAnalyticsProductionIntelligenceProductRegistryReadInvariantError(
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


@dataclass(frozen=True)
class ProductionIntelligenceProductRegistryReadRequest:
    request_id: str
    consumer_id: str
    requested_projection: str
    intelligence_product_id: str | None = None
    registry_key: str | None = None
    market_id: str | None = None
    venue_id: str | None = None
    maximum_results: int = 100


@dataclass(frozen=True)
class ProductionIntelligenceProductRegistryReadResult:
    request_id: str
    consumer_id: str
    requested_projection: str
    source_registry_manifest_id: str
    source_registry_manifest_hash: str
    matched_entry_count: int
    matched_registry_entries: tuple[dict[str, Any], ...]
    all_entry_hashes_verified: bool
    all_source_hashes_verified: bool
    all_lineage_verified: bool
    projection_authorized: bool
    deterministic_ordering_verified: bool
    immutable_read_verified: bool
    registry_mutation_allowed: bool
    registry_mutation_performed: bool
    registry_update_performed: bool
    registry_delete_performed: bool
    publication_allowed: bool
    publication_performed: bool
    execution_allowed: bool
    execution_performed: bool
    database_connection_performed: bool
    corpus_read_execution_repeated: bool
    read_status: str
    read_result_hash: str


class OracleIntelligenceAnalyticsProductionIntelligenceProductRegistryReadContract:
    def __init__(
        self,
        *,
        product_registry_directory: Path | str = DEFAULT_PRODUCT_REGISTRY_DIRECTORY,
    ) -> None:
        self.product_registry_directory = Path(product_registry_directory)

    def _load_registry(self) -> dict[str, Any]:
        path = self.product_registry_directory / "current.json"
        if not path.exists():
            raise OracleIntelligenceAnalyticsProductionIntelligenceProductRegistryReadInvariantError(
                f"INT-OIA-038 registry artifact missing: {path}"
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise OracleIntelligenceAnalyticsProductionIntelligenceProductRegistryReadInvariantError(
                "INT-OIA-038 registry artifact could not be decoded"
            ) from exc

        manifest_hash = payload.pop("registry_manifest_hash", None)
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise OracleIntelligenceAnalyticsProductionIntelligenceProductRegistryReadInvariantError(
                "INT-OIA-038 registry manifest hash mismatch"
            )
        payload["registry_manifest_hash"] = manifest_hash

        required_manifest = {
            "schema_version": EXPECTED_SOURCE_SCHEMA_VERSION,
            "engine_id": EXPECTED_SOURCE_SCHEMA_VERSION,
            "registry_schema_version": EXPECTED_REGISTRY_SCHEMA_VERSION,
            "registry_manifest_status": EXPECTED_REGISTRY_STATUS,
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
        for field, expected in required_manifest.items():
            if payload.get(field) != expected:
                raise OracleIntelligenceAnalyticsProductionIntelligenceProductRegistryReadInvariantError(
                    f"unsafe or incomplete INT-OIA-038 registry field: {field}"
                )

        entries = payload.get("registry_entries")
        if (
            not isinstance(entries, list)
            or payload.get("registry_entry_count") != len(entries)
        ):
            raise OracleIntelligenceAnalyticsProductionIntelligenceProductRegistryReadInvariantError(
                "INT-OIA-038 registry entries invalid"
            )

        seen_keys: set[str] = set()
        seen_ids: set[str] = set()

        for sequence, raw_entry in enumerate(entries, start=1):
            if not isinstance(raw_entry, dict):
                raise OracleIntelligenceAnalyticsProductionIntelligenceProductRegistryReadInvariantError(
                    "registry entry must be an object"
                )
            entry = dict(raw_entry)
            entry_hash = entry.pop("registry_entry_hash", None)
            if not _valid_hash(entry_hash) or stable_hash(entry) != entry_hash:
                raise OracleIntelligenceAnalyticsProductionIntelligenceProductRegistryReadInvariantError(
                    "registry entry hash mismatch"
                )
            entry["registry_entry_hash"] = entry_hash

            registry_key = entry.get("registry_key")
            registry_entry_id = entry.get("registry_entry_id")
            if (
                entry.get("sequence") != sequence
                or not isinstance(registry_key, str)
                or not registry_key
                or registry_key in seen_keys
                or not isinstance(registry_entry_id, str)
                or not registry_entry_id
                or registry_entry_id in seen_ids
            ):
                raise OracleIntelligenceAnalyticsProductionIntelligenceProductRegistryReadInvariantError(
                    "invalid sequence or duplicate registry identity"
                )
            seen_keys.add(registry_key)
            seen_ids.add(registry_entry_id)

            required_entry = {
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
            for field, expected in required_entry.items():
                if entry.get(field) != expected:
                    raise OracleIntelligenceAnalyticsProductionIntelligenceProductRegistryReadInvariantError(
                        f"unsafe registry entry field: {field}"
                    )

            projections = tuple(entry.get("allowed_consumer_projections", ()))
            if projections != ALLOWED_PROJECTIONS:
                raise OracleIntelligenceAnalyticsProductionIntelligenceProductRegistryReadInvariantError(
                    "registry entry projection policy mismatch"
                )

        return payload

    def read(
        self,
        request: ProductionIntelligenceProductRegistryReadRequest,
    ) -> ProductionIntelligenceProductRegistryReadResult:
        if not isinstance(request, ProductionIntelligenceProductRegistryReadRequest):
            raise OracleIntelligenceAnalyticsProductionIntelligenceProductRegistryReadInvariantError(
                "request must use the canonical read-request contract"
            )
        if not request.request_id:
            raise OracleIntelligenceAnalyticsProductionIntelligenceProductRegistryReadInvariantError(
                "request_id is required"
            )
        if not request.consumer_id:
            raise OracleIntelligenceAnalyticsProductionIntelligenceProductRegistryReadInvariantError(
                "consumer_id is required"
            )
        if request.requested_projection not in ALLOWED_PROJECTIONS:
            raise OracleIntelligenceAnalyticsProductionIntelligenceProductRegistryReadInvariantError(
                "requested projection is not authorized"
            )
        if (
            not isinstance(request.maximum_results, int)
            or request.maximum_results < 1
            or request.maximum_results > 1000
        ):
            raise OracleIntelligenceAnalyticsProductionIntelligenceProductRegistryReadInvariantError(
                "maximum_results must be between 1 and 1000"
            )

        registry = self._load_registry()
        matched: list[dict[str, Any]] = []

        for entry in registry["registry_entries"]:
            if (
                request.intelligence_product_id is not None
                and entry["intelligence_product_id"]
                != request.intelligence_product_id
            ):
                continue
            if (
                request.registry_key is not None
                and entry["registry_key"] != request.registry_key
            ):
                continue
            if (
                request.market_id is not None
                and entry["market_id"] != request.market_id
            ):
                continue
            if (
                request.venue_id is not None
                and entry["venue_id"] != request.venue_id
            ):
                continue
            if (
                request.requested_projection
                not in entry["allowed_consumer_projections"]
            ):
                continue
            matched.append(dict(entry))

        matched.sort(
            key=lambda item: (
                str(item.get("venue_id") or ""),
                str(item.get("market_id") or ""),
                str(item["intelligence_product_id"]),
                str(item["registry_key"]),
            )
        )
        matched = matched[: request.maximum_results]

        body = {
            "request_id": request.request_id,
            "consumer_id": request.consumer_id,
            "requested_projection": request.requested_projection,
            "source_registry_manifest_id": registry[
                "registry_manifest_id"
            ],
            "source_registry_manifest_hash": registry[
                "registry_manifest_hash"
            ],
            "matched_entry_count": len(matched),
            "matched_registry_entries": tuple(matched),
            "all_entry_hashes_verified": True,
            "all_source_hashes_verified": True,
            "all_lineage_verified": True,
            "projection_authorized": True,
            "deterministic_ordering_verified": True,
            "immutable_read_verified": True,
            "registry_mutation_allowed": False,
            "registry_mutation_performed": False,
            "registry_update_performed": False,
            "registry_delete_performed": False,
            "publication_allowed": False,
            "publication_performed": False,
            "execution_allowed": False,
            "execution_performed": False,
            "database_connection_performed": False,
            "corpus_read_execution_repeated": False,
            "read_status": READ_STATUS,
        }
        return ProductionIntelligenceProductRegistryReadResult(
            **body,
            read_result_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "READ_CONTRACT_SCHEMA_VERSION",
    "ProductionIntelligenceProductRegistryReadRequest",
    "ProductionIntelligenceProductRegistryReadResult",
    "OracleIntelligenceAnalyticsProductionIntelligenceProductRegistryReadContract",
    "OracleIntelligenceAnalyticsProductionIntelligenceProductRegistryReadInvariantError",
    "stable_hash",
]
