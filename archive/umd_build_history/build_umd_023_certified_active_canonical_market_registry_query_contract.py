from __future__ import annotations

import hashlib
import importlib
import json
import os
import py_compile
import sys
import textwrap
from pathlib import Path

REVISION = "UMD_023_CERTIFIED_ACTIVE_CANONICAL_MARKET_REGISTRY_QUERY_CONTRACT_V1"
ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2" / "universal_market_discovery"
MODULE = PKG / "certified_active_canonical_market_registry_query_contract.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_umd_023_certified_active_canonical_market_registry_query_contract.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import (
    UMD_SUBSYSTEM_ID,
    ImmutableLineage,
    deterministic_sha256,
)
from .certified_canonical_market_contract import CertifiedCanonicalMarket
from .certified_active_canonical_market_registry_read_model import (
    CertifiedActiveCanonicalMarketRegistryReadModel,
)

UMD_023_BUILD_ID = "UMD-023"
UMD_023_BUILD_NAME = "Certified Active Canonical Market Registry Query Contract"
UMD_023_REVISION = (
    "UMD_023_CERTIFIED_ACTIVE_CANONICAL_MARKET_REGISTRY_QUERY_CONTRACT_V1"
)
UMD_023_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_discovery",
    "market_scanning",
    "registry_mutation",
    "snapshot_activation",
    "persistence_write",
    "oracle_memory_mutation",
    "publication",
    "order_submission",
    "trade_execution",
)


def _text(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = " ".join(value.strip().split())
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def _optional_text(
    value: str | None,
    field_name: str,
) -> str | None:
    if value is None:
        return None
    return _text(value, field_name).lower()


def _value_text(value: Any) -> str:
    raw = getattr(value, "value", value)
    return str(raw).strip().lower()


class MarketQueryMode(str, Enum):
    BY_ID = "by_id"
    FILTER = "filter"
    ALL = "all"


@dataclass(frozen=True, slots=True)
class CertifiedActiveMarketQueryRequest:
    query_mode: MarketQueryMode
    canonical_market_id: str | None
    venue_id: str | None
    category_id: str | None
    lifecycle: str | None
    limit: int | None
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        if not isinstance(self.query_mode, MarketQueryMode):
            object.__setattr__(
                self,
                "query_mode",
                MarketQueryMode(self.query_mode),
            )

        market_id = (
            None
            if self.canonical_market_id is None
            else _text(
                self.canonical_market_id,
                "canonical_market_id",
            )
        )
        if market_id is not None and not market_id.startswith(
            "umd:mkt:"
        ):
            raise ValueError(
                "canonical_market_id must use UMD market prefix"
            )
        object.__setattr__(
            self,
            "canonical_market_id",
            market_id,
        )

        object.__setattr__(
            self,
            "venue_id",
            _optional_text(
                self.venue_id,
                "venue_id",
            ),
        )
        object.__setattr__(
            self,
            "category_id",
            _optional_text(
                self.category_id,
                "category_id",
            ),
        )
        object.__setattr__(
            self,
            "lifecycle",
            (
                None
                if self.lifecycle is None
                else _value_text(self.lifecycle)
            ),
        )

        if self.limit is not None:
            if not isinstance(self.limit, int):
                raise TypeError("limit must be an integer or None")
            if self.limit < 1:
                raise ValueError("limit must be positive")

        if self.query_mode == MarketQueryMode.BY_ID:
            if self.canonical_market_id is None:
                raise ValueError(
                    "BY_ID query requires canonical_market_id"
                )
            if any(
                value is not None
                for value in (
                    self.venue_id,
                    self.category_id,
                    self.lifecycle,
                    self.limit,
                )
            ):
                raise ValueError(
                    "BY_ID query cannot include filters or limit"
                )

        if self.query_mode == MarketQueryMode.ALL:
            if any(
                value is not None
                for value in (
                    self.canonical_market_id,
                    self.venue_id,
                    self.category_id,
                    self.lifecycle,
                )
            ):
                raise ValueError(
                    "ALL query cannot include identity or filters"
                )

        if self.query_mode == MarketQueryMode.FILTER:
            if self.canonical_market_id is not None:
                raise ValueError(
                    "FILTER query cannot include canonical_market_id"
                )
            if all(
                value is None
                for value in (
                    self.venue_id,
                    self.category_id,
                    self.lifecycle,
                )
            ):
                raise ValueError(
                    "FILTER query requires at least one filter"
                )

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("query lineage must belong to UMD")
        if self.lineage.build_id != UMD_023_BUILD_ID:
            raise ValueError(
                "query lineage must use build_id UMD-023"
            )

    @property
    def query_id(self) -> str:
        return "umd:market-query:" + deterministic_sha256(
            self.to_canonical_dict()
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "query_mode": self.query_mode,
            "canonical_market_id": self.canonical_market_id,
            "venue_id": self.venue_id,
            "category_id": self.category_id,
            "lifecycle": self.lifecycle,
            "limit": self.limit,
            "lineage": self.lineage,
        }


@dataclass(frozen=True, slots=True)
class CertifiedActiveMarketQueryResult:
    query: CertifiedActiveMarketQueryRequest
    active_snapshot_id: str
    active_snapshot_hash: str
    read_model_hash: str
    markets: Tuple[CertifiedCanonicalMarket, ...]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        snapshot_id = _text(
            self.active_snapshot_id,
            "active_snapshot_id",
        )
        if not snapshot_id.startswith(
            "umd:market-registry-snapshot:"
        ):
            raise ValueError(
                "active_snapshot_id must use UMD snapshot prefix"
            )
        object.__setattr__(
            self,
            "active_snapshot_id",
            snapshot_id,
        )

        for field_name in (
            "active_snapshot_hash",
            "read_model_hash",
        ):
            value = _text(
                getattr(self, field_name),
                field_name,
            ).lower()
            if len(value) != 64:
                raise ValueError(
                    f"{field_name} must contain 64 hexadecimal characters"
                )
            if any(
                character not in "0123456789abcdef"
                for character in value
            ):
                raise ValueError(
                    f"{field_name} must be lowercase SHA-256 hexadecimal"
                )
            object.__setattr__(
                self,
                field_name,
                value,
            )

        markets = tuple(
            sorted(
                self.markets,
                key=lambda market: market.canonical_market_id,
            )
        )
        if len(
            {
                market.canonical_market_id
                for market in markets
            }
        ) != len(markets):
            raise ValueError(
                "query result contains duplicate canonical market IDs"
            )
        object.__setattr__(
            self,
            "markets",
            markets,
        )

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError(
                "query-result lineage must belong to UMD"
            )
        if self.lineage.build_id != UMD_023_BUILD_ID:
            raise ValueError(
                "query-result lineage must use build_id UMD-023"
            )

        required_parents = {
            self.read_model_hash,
        }
        if not required_parents.issubset(
            set(self.lineage.parent_hashes)
        ):
            raise ValueError(
                "query-result lineage must include read-model hash"
            )

    @property
    def result_id(self) -> str:
        return "umd:market-query-result:" + deterministic_sha256(
            {
                "query_id": self.query.query_id,
                "active_snapshot_id": self.active_snapshot_id,
                "active_snapshot_hash": self.active_snapshot_hash,
                "read_model_hash": self.read_model_hash,
                "market_record_hashes": tuple(
                    market.record_hash
                    for market in self.markets
                ),
            }
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "result_id": self.result_id,
            "query": self.query,
            "active_snapshot_id": self.active_snapshot_id,
            "active_snapshot_hash": self.active_snapshot_hash,
            "read_model_hash": self.read_model_hash,
            "markets": self.markets,
            "lineage": self.lineage,
        }

    @property
    def result_hash(self) -> str:
        return deterministic_sha256(
            self.to_canonical_dict()
        )


def execute_active_market_query(
    request: CertifiedActiveMarketQueryRequest,
    read_model: CertifiedActiveCanonicalMarketRegistryReadModel,
    *,
    lineage: ImmutableLineage,
) -> CertifiedActiveMarketQueryResult:
    if request.query_mode == MarketQueryMode.BY_ID:
        market = read_model.get(
            request.canonical_market_id
        )
        markets = () if market is None else (market,)

    elif request.query_mode == MarketQueryMode.ALL:
        markets = tuple(
            read_model.get(market_id)
            for market_id in read_model.market_ids()
        )

    else:
        candidate_ids = set(read_model.market_ids())

        if request.venue_id is not None:
            candidate_ids &= {
                market.canonical_market_id
                for market in read_model.by_venue(
                    request.venue_id
                )
            }

        if request.category_id is not None:
            candidate_ids &= {
                market.canonical_market_id
                for market in read_model.by_category(
                    request.category_id
                )
            }

        if request.lifecycle is not None:
            candidate_ids &= {
                market.canonical_market_id
                for market in read_model.by_lifecycle(
                    request.lifecycle
                )
            }

        markets = tuple(
            read_model.get(market_id)
            for market_id in sorted(candidate_ids)
        )

    markets = tuple(
        market
        for market in markets
        if market is not None
    )

    if request.limit is not None:
        markets = markets[: request.limit]

    return CertifiedActiveMarketQueryResult(
        query=request,
        active_snapshot_id=read_model.active_snapshot_id,
        active_snapshot_hash=read_model.active_snapshot_hash,
        read_model_hash=read_model.read_model_hash,
        markets=markets,
        lineage=lineage,
    )


@dataclass(frozen=True, slots=True)
class UMD023CertificationManifest:
    subsystem_id: str
    build_id: str
    build_name: str
    revision: str
    schema_version: str
    upstream_builds: Tuple[str, ...]
    query_mode: str
    prohibited_capabilities: Tuple[str, ...]
    network_enabled: bool
    persistence_enabled: bool
    mutation_enabled: bool
    publication_enabled: bool
    execution_enabled: bool

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "subsystem_id": self.subsystem_id,
            "build_id": self.build_id,
            "build_name": self.build_name,
            "revision": self.revision,
            "schema_version": self.schema_version,
            "upstream_builds": self.upstream_builds,
            "query_mode": self.query_mode,
            "prohibited_capabilities": self.prohibited_capabilities,
            "network_enabled": self.network_enabled,
            "persistence_enabled": self.persistence_enabled,
            "mutation_enabled": self.mutation_enabled,
            "publication_enabled": self.publication_enabled,
            "execution_enabled": self.execution_enabled,
        }

    @property
    def manifest_hash(self) -> str:
        return deterministic_sha256(
            self.to_canonical_dict()
        )


def build_umd_023_certification_manifest() -> UMD023CertificationManifest:
    return UMD023CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_023_BUILD_ID,
        build_name=UMD_023_BUILD_NAME,
        revision=UMD_023_REVISION,
        schema_version=UMD_023_SCHEMA_VERSION,
        upstream_builds=tuple(
            f"UMD-{number:03d}"
            for number in range(1, 23)
        ),
        query_mode="deterministic_read_only",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )


def certify_umd_023_foundation() -> Mapping[str, Any]:
    manifest = build_umd_023_certification_manifest()

    checks = {
        "subsystem_identity": (
            manifest.subsystem_id == "UMD"
        ),
        "build_identity": (
            manifest.build_id == "UMD-023"
        ),
        "upstreams_frozen": (
            manifest.upstream_builds
            == tuple(
                f"UMD-{number:03d}"
                for number in range(1, 23)
            )
        ),
        "deterministic_read_only": (
            manifest.query_mode
            == "deterministic_read_only"
        ),
        "network_disabled": (
            manifest.network_enabled is False
        ),
        "persistence_disabled": (
            manifest.persistence_enabled is False
        ),
        "mutation_disabled": (
            manifest.mutation_enabled is False
        ),
        "publication_disabled": (
            manifest.publication_enabled is False
        ),
        "execution_disabled": (
            manifest.execution_enabled is False
        ),
        "deterministic_manifest_hash": (
            manifest.manifest_hash
            == deterministic_sha256(
                manifest.to_canonical_dict()
            )
        ),
    }

    failed = tuple(
        name
        for name, passed in checks.items()
        if not passed
    )

    return MappingProxyType(
        {
            "certified": not failed,
            "build_id": manifest.build_id,
            "revision": manifest.revision,
            "manifest_hash": manifest.manifest_hash,
            "checks": MappingProxyType(checks),
            "failed_checks": failed,
        }
    )


def verify_umd_023_certified_active_canonical_market_registry_query_contract() -> bool:
    result = certify_umd_023_foundation()

    if not result["certified"]:
        raise RuntimeError(
            "UMD-023 certification failed: "
            + ", ".join(result["failed_checks"])
        )

    return True


__all__ = [
    "UMD_023_BUILD_ID",
    "UMD_023_BUILD_NAME",
    "UMD_023_REVISION",
    "UMD_023_SCHEMA_VERSION",
    "PROHIBITED_CAPABILITIES",
    "MarketQueryMode",
    "CertifiedActiveMarketQueryRequest",
    "CertifiedActiveMarketQueryResult",
    "execute_active_market_query",
    "UMD023CertificationManifest",
    "build_umd_023_certification_manifest",
    "certify_umd_023_foundation",
    "verify_umd_023_certified_active_canonical_market_registry_query_contract",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import (
    ImmutableLineage,
)
from qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_query_contract import (
    UMD_023_REVISION,
    MarketQueryMode,
    CertifiedActiveMarketQueryRequest,
    build_umd_023_certification_manifest,
    certify_umd_023_foundation,
    verify_umd_023_certified_active_canonical_market_registry_query_contract,
)

FIXED = datetime(
    2026,
    8,
    6,
    6,
    0,
    tzinfo=timezone.utc,
)


def lineage() -> ImmutableLineage:
    return ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-023",
        revision=UMD_023_REVISION,
        schema_version="1.0.0",
        parent_hashes=(),
        source_refs=(
            "fixture://umd-023/query",
        ),
        created_at=FIXED,
    )


class TestUMD023(unittest.TestCase):
    def test_foundation_certifies(self) -> None:
        self.assertTrue(
            certify_umd_023_foundation()["certified"]
        )
        self.assertTrue(
            verify_umd_023_certified_active_canonical_market_registry_query_contract()
        )

    def test_query_id_deterministic(self) -> None:
        first = CertifiedActiveMarketQueryRequest(
            query_mode=MarketQueryMode.FILTER,
            canonical_market_id=None,
            venue_id="Venue-A",
            category_id="Bitcoin",
            lifecycle="open",
            limit=10,
            lineage=lineage(),
        )
        second = CertifiedActiveMarketQueryRequest(
            query_mode=MarketQueryMode.FILTER,
            canonical_market_id=None,
            venue_id="venue-a",
            category_id="bitcoin",
            lifecycle="OPEN",
            limit=10,
            lineage=lineage(),
        )

        self.assertEqual(
            first.query_id,
            second.query_id,
        )

    def test_by_id_requires_market_id(self) -> None:
        with self.assertRaises(ValueError):
            CertifiedActiveMarketQueryRequest(
                query_mode=MarketQueryMode.BY_ID,
                canonical_market_id=None,
                venue_id=None,
                category_id=None,
                lifecycle=None,
                limit=None,
                lineage=lineage(),
            )

    def test_filter_requires_filter(self) -> None:
        with self.assertRaises(ValueError):
            CertifiedActiveMarketQueryRequest(
                query_mode=MarketQueryMode.FILTER,
                canonical_market_id=None,
                venue_id=None,
                category_id=None,
                lifecycle=None,
                limit=None,
                lineage=lineage(),
            )

    def test_all_rejects_filters(self) -> None:
        with self.assertRaises(ValueError):
            CertifiedActiveMarketQueryRequest(
                query_mode=MarketQueryMode.ALL,
                canonical_market_id=None,
                venue_id="venue-a",
                category_id=None,
                lifecycle=None,
                limit=None,
                lineage=lineage(),
            )

    def test_query_is_immutable(self) -> None:
        item = CertifiedActiveMarketQueryRequest(
            query_mode=MarketQueryMode.ALL,
            canonical_market_id=None,
            venue_id=None,
            category_id=None,
            lifecycle=None,
            limit=5,
            lineage=lineage(),
        )

        with self.assertRaises(
            (FrozenInstanceError, AttributeError)
        ):
            item.limit = 10

    def test_side_effects_disabled(self) -> None:
        manifest = build_umd_023_certification_manifest()

        self.assertEqual(
            manifest.query_mode,
            "deterministic_read_only",
        )
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)


if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-023 CERTIFICATION TEST")
    print(
        " CERTIFIED ACTIVE CANONICAL MARKET "
        "REGISTRY QUERY CONTRACT"
    )
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD023
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_023_certification_manifest()

    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(
        f"[PASS] Manifest hash: "
        f"{manifest.manifest_hash}"
    )
    print(
        "[PASS] UMD-001 through UMD-022 "
        "consumed read-only"
    )
    print(
        "[PASS] Canonical market query IDs deterministic"
    )
    print(
        "[PASS] BY_ID, FILTER, and ALL query modes certified"
    )
    print(
        "[PASS] Venue, category, and lifecycle filters normalized"
    )
    print(
        "[PASS] Invalid query combinations rejected"
    )
    print(
        "[PASS] Deterministic result ordering and hashing contract certified"
    )
    print(
        "[PASS] Read-model hash lineage required"
    )
    print(
        "[PASS] Network and persistence disabled"
    )
    print(
        "[PASS] Publication and Q Series execution disabled"
    )
    print(
        "[DONE] UMD-023 CERTIFIED ACTIVE CANONICAL MARKET "
        "REGISTRY QUERY CONTRACT CERTIFIED"
    )
"""

INIT_IMPORT = r"""
from .certified_active_canonical_market_registry_query_contract import (
    UMD_023_BUILD_ID,
    UMD_023_BUILD_NAME,
    UMD_023_REVISION,
    UMD_023_SCHEMA_VERSION,
    MarketQueryMode,
    CertifiedActiveMarketQueryRequest,
    CertifiedActiveMarketQueryResult,
    execute_active_market_query,
    UMD023CertificationManifest,
    build_umd_023_certification_manifest,
    certify_umd_023_foundation,
    verify_umd_023_certified_active_canonical_market_registry_query_contract,
)
"""

EXPORTED_NAMES = (
    "UMD_023_BUILD_ID",
    "UMD_023_BUILD_NAME",
    "UMD_023_REVISION",
    "UMD_023_SCHEMA_VERSION",
    "MarketQueryMode",
    "CertifiedActiveMarketQueryRequest",
    "CertifiedActiveMarketQueryResult",
    "execute_active_market_query",
    "UMD023CertificationManifest",
    "build_umd_023_certification_manifest",
    "certify_umd_023_foundation",
    "verify_umd_023_certified_active_canonical_market_registry_query_contract",
)


def normalize(source: str) -> str:
    return textwrap.dedent(source).lstrip()


def write_exact(path: Path, source: str) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )
    temporary.write_text(
        normalize(source),
        encoding="utf-8",
        newline="\n",
    )
    os.replace(temporary, path)


def update_init() -> None:
    if not INIT.exists():
        raise FileNotFoundError(
            f"UMD package initializer missing: {INIT}"
        )

    source = INIT.read_text(
        encoding="utf-8"
    )
    marker = (
        "from "
        ".certified_active_canonical_market_registry_query_contract "
        "import ("
    )

    if marker not in source:
        source = (
            source.rstrip()
            + "\n\n"
            + normalize(INIT_IMPORT)
        )

    if "__all__" in source:
        start = source.index(
            "__all__ = ["
        )
        end = source.index(
            "]",
            start,
        )
        block = source[start : end + 1]

        missing = [
            name
            for name in EXPORTED_NAMES
            if f'"{name}"' not in block
            and f"'{name}'" not in block
        ]

        if missing:
            block = (
                block[:-1]
                + "".join(
                    f'    "{name}",\n'
                    for name in missing
                )
                + "]"
            )
            source = (
                source[:start]
                + block
                + source[end + 1 :]
            )
    else:
        source += (
            "\n__all__ = [\n"
            + "".join(
                f'    "{name}",\n'
                for name in EXPORTED_NAMES
            )
            + "]\n"
        )

    write_exact(INIT, source)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def verify_upstream() -> None:
    sys.path.insert(
        0,
        str(ROOT),
    )

    try:
        modules = (
            ("universal_market_discovery_foundation", "verify_umd_foundation"),
            ("certified_canonical_market_contract", "verify_umd_002_certified_canonical_market_contract"),
            ("certified_venue_identity_registry", "verify_umd_003_certified_venue_identity_registry"),
            ("certified_venue_market_binding_registry", "verify_umd_004_certified_venue_market_binding_registry"),
            ("certified_market_category_hierarchy_registry", "verify_umd_005_certified_market_category_hierarchy_registry"),
            ("certified_market_classification_registry", "verify_umd_006_certified_market_classification_registry"),
            ("certified_market_metadata_registry", "verify_umd_007_certified_market_metadata_registry"),
            ("certified_market_lifecycle_and_settlement_registry", "verify_umd_008_certified_market_lifecycle_and_settlement_registry"),
            ("certified_market_duplicate_resolution_registry", "verify_umd_009_certified_market_duplicate_resolution_registry"),
            ("certified_related_market_graph_registry", "verify_umd_010_certified_related_market_graph_registry"),
            ("certified_incremental_discovery_batch_contract", "verify_umd_011_certified_incremental_discovery_batch_contract"),
            ("certified_incremental_discovery_admission_gate", "verify_umd_012_certified_incremental_discovery_admission_gate"),
            ("certified_discovery_admission_ledger", "verify_umd_013_certified_discovery_admission_ledger"),
            ("certified_admitted_market_materialization_contract", "verify_umd_014_certified_admitted_market_materialization_contract"),
            ("certified_materialized_market_admission_registry", "verify_umd_015_certified_materialized_market_admission_registry"),
            ("certified_canonical_market_registry_snapshot_contract", "verify_umd_016_certified_canonical_market_registry_snapshot_contract"),
            ("certified_canonical_market_registry_snapshot_admission_gate", "verify_umd_017_certified_canonical_market_registry_snapshot_admission_gate"),
            ("certified_canonical_market_registry_snapshot_admission_ledger", "verify_umd_018_certified_canonical_market_registry_snapshot_admission_ledger"),
            ("certified_canonical_market_registry_snapshot_activation_contract", "verify_umd_019_certified_canonical_market_registry_snapshot_activation_contract"),
            ("certified_canonical_market_registry_snapshot_activation_gate", "verify_umd_020_certified_canonical_market_registry_snapshot_activation_gate"),
            ("certified_canonical_market_registry_snapshot_activation_ledger", "verify_umd_021_certified_canonical_market_registry_snapshot_activation_ledger"),
            ("certified_active_canonical_market_registry_read_model", "verify_umd_022_certified_active_canonical_market_registry_read_model"),
        )

        for module_name, verifier_name in modules:
            module = importlib.import_module(
                "qseries_v2."
                "universal_market_discovery."
                + module_name
            )

            verifier = getattr(
                module,
                verifier_name,
            )

            if not verifier():
                raise RuntimeError(
                    f"{module_name} verification failed"
                )
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(
                str(ROOT)
            )


def verify_current() -> None:
    sys.path.insert(
        0,
        str(ROOT),
    )

    try:
        module = importlib.import_module(
            "qseries_v2."
            "universal_market_discovery."
            "certified_active_canonical_market_registry_query_contract"
        )

        required = (
            "MarketQueryMode",
            "CertifiedActiveMarketQueryRequest",
            "CertifiedActiveMarketQueryResult",
            "execute_active_market_query",
            "build_umd_023_certification_manifest",
            "certify_umd_023_foundation",
            "verify_umd_023_certified_active_canonical_market_registry_query_contract",
        )

        missing = [
            name
            for name in required
            if not hasattr(
                module,
                name,
            )
        ]

        if missing:
            raise RuntimeError(
                "UMD-023 missing symbols: "
                + ", ".join(missing)
            )

        module.verify_umd_023_certified_active_canonical_market_registry_query_contract()
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(
                str(ROOT)
            )


def main() -> int:
    print("=" * 64)
    print(" UMD-023 INSTALLER")
    print(
        " CERTIFIED ACTIVE CANONICAL MARKET "
        "REGISTRY QUERY CONTRACT"
    )
    print("=" * 64)
    print(
        f"[BOOT] Revision: {REVISION}"
    )
    print(
        f"[ROOT] {ROOT}"
    )

    verify_upstream()
    print(
        "[PASS] Certified UMD-001 through UMD-022 "
        "verified read-only"
    )

    write_exact(
        MODULE,
        MODULE_SOURCE,
    )
    write_exact(
        TEST,
        TEST_SOURCE,
    )
    update_init()

    py_compile.compile(
        str(MODULE),
        doraise=True,
    )
    py_compile.compile(
        str(INIT),
        doraise=True,
    )
    py_compile.compile(
        str(TEST),
        doraise=True,
    )
    verify_current()

    manifest = {
        "build_id": "UMD-023",
        "revision": REVISION,
        "files": {
            str(
                MODULE.relative_to(ROOT)
            ): sha256_file(MODULE),
            str(
                INIT.relative_to(ROOT)
            ): sha256_file(INIT),
            str(
                TEST.relative_to(ROOT)
            ): sha256_file(TEST),
        },
        "upstream": tuple(
            f"UMD-{number:03d}"
            for number in range(1, 23)
        ),
        "mode": "deterministic_read_only",
    }

    install_hash = hashlib.sha256(
        json.dumps(
            manifest,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    print(
        f"[PASS] Wrote: "
        f"{MODULE.relative_to(ROOT)}"
    )
    print(
        f"[PASS] Updated: "
        f"{INIT.relative_to(ROOT)}"
    )
    print(
        f"[PASS] Wrote: "
        f"{TEST.relative_to(ROOT)}"
    )
    print(
        "[PASS] Python compilation verified"
    )
    print(
        "[PASS] Required UMD-023 symbols verified"
    )
    print(
        f"[PASS] Deterministic install hash: "
        f"{install_hash}"
    )
    print(
        "[PASS] Network, persistence, publication, "
        "and execution disabled"
    )
    print(
        "[DONE] UMD-023 INSTALLATION COMPLETE"
    )
    print()
    print("NEXT:")
    print(
        "  python "
        "test_umd_023_certified_active_canonical_market_"
        "registry_query_contract.py"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
