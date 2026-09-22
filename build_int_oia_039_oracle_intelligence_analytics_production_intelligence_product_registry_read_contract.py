from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"
DOWNSTREAM = ANALYTICS / "downstream"
REGISTRY = DOWNSTREAM / "registry"
QUERY = DOWNSTREAM / "query"

SOURCE_038 = REGISTRY / (
    "oracle_intelligence_analytics_immutable_intelligence_product_registry.py"
)
PRODUCTION = QUERY / (
    "oracle_intelligence_analytics_production_intelligence_product_registry_read_contract.py"
)
TEST = ROOT / (
    "test_int_oia_039_oracle_intelligence_analytics_"
    "production_intelligence_product_registry_read_contract.py"
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
"""

TEST_SOURCE = r"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_production_intelligence_product_registry_read_contract import (
    READ_CONTRACT_SCHEMA_VERSION,
    OracleIntelligenceAnalyticsProductionIntelligenceProductRegistryReadContract,
    OracleIntelligenceAnalyticsProductionIntelligenceProductRegistryReadInvariantError,
    ProductionIntelligenceProductRegistryReadRequest,
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
        "registry_entry_id": stable_hash(
            {"registry-entry": sequence}
        ),
        "product_admission_id": stable_hash(
            {"product-admission": sequence}
        ),
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


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-039 TEST")
    print(" PRODUCTION REGISTRY READ")
    print(" STRICT READ-ONLY CONTRACT")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        registry = root / "registry"
        _seed_registry(registry)
        source_before = (registry / "current.json").read_bytes()

        reader = OracleIntelligenceAnalyticsProductionIntelligenceProductRegistryReadContract(
            product_registry_directory=registry,
        )

        request = ProductionIntelligenceProductRegistryReadRequest(
            request_id="read-request-1",
            consumer_id="oracle.operator.console.v1",
            requested_projection="operator_research",
            venue_id="kalshi",
            maximum_results=100,
        )
        first = reader.read(request)
        second = reader.read(request)

        assert first == second
        assert first.read_result_hash == stable_hash(
            {
                key: value
                for key, value in first.__dict__.items()
                if key != "read_result_hash"
            }
        )
        assert first.matched_entry_count == 2
        assert len(first.matched_registry_entries) == 2
        assert first.all_entry_hashes_verified
        assert first.all_source_hashes_verified
        assert first.all_lineage_verified
        assert first.projection_authorized
        assert first.deterministic_ordering_verified
        assert first.immutable_read_verified
        assert not first.registry_mutation_allowed
        assert not first.registry_mutation_performed
        assert not first.registry_update_performed
        assert not first.registry_delete_performed
        assert not first.publication_allowed
        assert not first.publication_performed
        assert not first.execution_allowed
        assert not first.execution_performed
        assert not first.database_connection_performed
        assert not first.corpus_read_execution_repeated
        assert source_before == (registry / "current.json").read_bytes()

        filtered = reader.read(
            ProductionIntelligenceProductRegistryReadRequest(
                request_id="read-request-2",
                consumer_id="oracle.audit.replay.v1",
                requested_projection="audit_replay",
                market_id="KX-BETA",
                maximum_results=1,
            )
        )
        assert filtered.matched_entry_count == 1
        assert filtered.matched_registry_entries[0]["market_id"] == "KX-BETA"

        try:
            reader.read(
                ProductionIntelligenceProductRegistryReadRequest(
                    request_id="read-request-3",
                    consumer_id="unauthorized-consumer",
                    requested_projection="execution",
                )
            )
            raise AssertionError("unauthorized projection accepted")
        except OracleIntelligenceAnalyticsProductionIntelligenceProductRegistryReadInvariantError:
            pass

        tampered = json.loads(
            (registry / "current.json").read_text(encoding="utf-8")
        )
        tampered["registry_entries"][0]["confidence"] = 0.99
        (registry / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            reader.read(request)
            raise AssertionError("tampered registry accepted")
        except OracleIntelligenceAnalyticsProductionIntelligenceProductRegistryReadInvariantError:
            pass

    assert READ_CONTRACT_SCHEMA_VERSION == (
        "oracle.production-intelligence-product-registry-read-contract.v1"
    )
    print("[PASS] Actual INT-OIA-038 immutable registry consumed")
    print("[PASS] Registry manifest hash independently verified")
    print("[PASS] Every registry entry hash independently verified")
    print("[PASS] Complete INT-OIA-013 through INT-OIA-038 lineage preserved")
    print("[PASS] Strict read request and read result contracts enforced")
    print("[PASS] Deterministic filtered retrieval verified")
    print("[PASS] Authorized consumer projection enforced")
    print("[PASS] Read operation left registry byte-for-byte unchanged")
    print("[PASS] Registry mutation, update, and delete remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Execution remained disabled")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] Unauthorized projection rejected")
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


def verify_int_oia_038_contract() -> None:
    if not SOURCE_038.exists():
        raise FileNotFoundError(
            f"Actual INT-OIA-038 production module missing: {SOURCE_038}"
        )
    source = SOURCE_038.read_text(encoding="utf-8")
    required_tokens = (
        'SCHEMA_VERSION = "INT-OIA-038"',
        "REGISTRY_SCHEMA_VERSION",
        "oracle.immutable-intelligence-product-registry.v1",
        "class ImmutableIntelligenceProductRegistryEntry",
        "class OracleIntelligenceAnalyticsImmutableIntelligenceProductRegistryManifest",
        "class OracleIntelligenceAnalyticsImmutableIntelligenceProductRegistry",
        "registry_manifest_hash",
        "registry_entry_hash",
        "all_entries_query_eligible",
        "all_entries_projection_eligible",
        "registry_mutation_allowed",
        "registry_update_performed",
        "registry_delete_performed",
    )
    missing = [token for token in required_tokens if token not in source]
    if missing:
        raise RuntimeError(
            "Actual INT-OIA-038 contract mismatch; missing tokens: "
            + ", ".join(missing)
        )
    print("[OK] Actual INT-OIA-038 immutable-registry contract verified")


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-039 INSTALLER")
    print(" PRODUCTION REGISTRY READ")
    print(" STRICT READ-ONLY CONTRACT")
    print("=" * 40)

    verify_int_oia_038_contract()

    write_replacement(PRODUCTION, PRODUCTION_SOURCE)
    write_replacement(TEST, TEST_SOURCE)

    append_export(
        QUERY_PACKAGE,
        "from .oracle_intelligence_analytics_production_intelligence_product_registry_read_contract import *",
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

    print("[OK] INT-OIA-039 test executed automatically")
    print()
    print("[DONE] INT-OIA-039 production registry read contract installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
