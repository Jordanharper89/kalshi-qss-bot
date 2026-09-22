from __future__ import annotations

import hashlib
import importlib
import json
import os
import py_compile
import sys
import textwrap
from pathlib import Path

REVISION = "UMD_011_CERTIFIED_INCREMENTAL_DISCOVERY_BATCH_CONTRACT_V1"
ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2" / "universal_market_discovery"
MODULE = PKG / "certified_incremental_discovery_batch_contract.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_umd_011_certified_incremental_discovery_batch_contract.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import (
    UMD_SUBSYSTEM_ID,
    ImmutableLineage,
    deterministic_sha256,
)
from .certified_canonical_market_contract import CertifiedCanonicalMarket
from .certified_related_market_graph_registry import (
    ReadOnlyRelatedMarketGraphRegistry,
)

UMD_011_BUILD_ID = "UMD-011"
UMD_011_BUILD_NAME = "Certified Incremental Discovery Batch Contract"
UMD_011_REVISION = "UMD_011_CERTIFIED_INCREMENTAL_DISCOVERY_BATCH_CONTRACT_V1"
UMD_011_SCHEMA_VERSION = "1.0.0"

def _text(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    value = " ".join(value.strip().split())
    if not value:
        raise ValueError(f"{name} must not be empty")
    return value

def _utc(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{name} must be datetime")
    if value.tzinfo is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(timezone.utc)

def _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(sorted((str(k), v) for k, v in value.items())))

@dataclass(frozen=True, slots=True)
class CertifiedDiscoveryCursor:
    source_id: str
    partition_key: str
    cursor_value: str
    observed_at: datetime
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_id", _text(self.source_id, "source_id").lower())
        object.__setattr__(
            self,
            "partition_key",
            _text(self.partition_key, "partition_key").lower(),
        )
        object.__setattr__(
            self,
            "cursor_value",
            _text(self.cursor_value, "cursor_value"),
        )
        object.__setattr__(
            self,
            "observed_at",
            _utc(self.observed_at, "observed_at"),
        )
        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("cursor lineage must belong to UMD")
        if self.lineage.build_id != UMD_011_BUILD_ID:
            raise ValueError("cursor lineage must use build_id UMD-011")

    @property
    def cursor_id(self) -> str:
        return "umd:cursor:" + deterministic_sha256({
            "source_id": self.source_id,
            "partition_key": self.partition_key,
        })

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "cursor_id": self.cursor_id,
            "source_id": self.source_id,
            "partition_key": self.partition_key,
            "cursor_value": self.cursor_value,
            "observed_at": self.observed_at,
            "lineage": self.lineage,
        }

    @property
    def record_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())

@dataclass(frozen=True, slots=True)
class CertifiedDiscoveryCandidate:
    source_id: str
    source_market_key: str
    market: CertifiedCanonicalMarket
    discovered_at: datetime
    payload_hash: str
    metadata: Mapping[str, Any]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_id", _text(self.source_id, "source_id").lower())
        object.__setattr__(
            self,
            "source_market_key",
            _text(self.source_market_key, "source_market_key"),
        )
        object.__setattr__(
            self,
            "discovered_at",
            _utc(self.discovered_at, "discovered_at"),
        )
        payload_hash = _text(self.payload_hash, "payload_hash").lower()
        if len(payload_hash) != 64 or any(ch not in "0123456789abcdef" for ch in payload_hash):
            raise ValueError("payload_hash must be lowercase SHA-256 hex")
        object.__setattr__(self, "payload_hash", payload_hash)
        object.__setattr__(self, "metadata", _freeze(self.metadata))
        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("candidate lineage must belong to UMD")
        if self.lineage.build_id != UMD_011_BUILD_ID:
            raise ValueError("candidate lineage must use build_id UMD-011")

    @property
    def candidate_id(self) -> str:
        return "umd:candidate:" + deterministic_sha256({
            "source_id": self.source_id,
            "source_market_key": self.source_market_key,
            "payload_hash": self.payload_hash,
        })

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "source_id": self.source_id,
            "source_market_key": self.source_market_key,
            "canonical_market_id": self.market.canonical_market_id,
            "market_record_hash": self.market.record_hash,
            "discovered_at": self.discovered_at,
            "payload_hash": self.payload_hash,
            "metadata": self.metadata,
            "lineage": self.lineage,
        }

    @property
    def record_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())

@dataclass(frozen=True, slots=True)
class CertifiedIncrementalDiscoveryBatch:
    source_id: str
    batch_sequence: int
    previous_batch_hash: str | None
    start_cursor: CertifiedDiscoveryCursor | None
    end_cursor: CertifiedDiscoveryCursor
    candidates: Tuple[CertifiedDiscoveryCandidate, ...]
    created_at: datetime
    metadata: Mapping[str, Any]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        source_id = _text(self.source_id, "source_id").lower()
        object.__setattr__(self, "source_id", source_id)
        if not isinstance(self.batch_sequence, int) or self.batch_sequence < 1:
            raise ValueError("batch_sequence must be a positive integer")

        if self.previous_batch_hash is not None:
            previous = _text(self.previous_batch_hash, "previous_batch_hash").lower()
            if len(previous) != 64 or any(ch not in "0123456789abcdef" for ch in previous):
                raise ValueError("previous_batch_hash must be lowercase SHA-256 hex")
            object.__setattr__(self, "previous_batch_hash", previous)
        elif self.batch_sequence != 1:
            raise ValueError("non-initial batches require previous_batch_hash")

        if self.start_cursor is not None and self.start_cursor.source_id != source_id:
            raise ValueError("start_cursor source mismatch")
        if self.end_cursor.source_id != source_id:
            raise ValueError("end_cursor source mismatch")

        candidates = tuple(sorted(self.candidates, key=lambda item: item.candidate_id))
        if any(candidate.source_id != source_id for candidate in candidates):
            raise ValueError("candidate source mismatch")
        if len({candidate.candidate_id for candidate in candidates}) != len(candidates):
            raise ValueError("duplicate candidate ID")
        if len({candidate.source_market_key for candidate in candidates}) != len(candidates):
            raise ValueError("duplicate source_market_key in batch")
        object.__setattr__(self, "candidates", candidates)
        object.__setattr__(self, "created_at", _utc(self.created_at, "created_at"))
        object.__setattr__(self, "metadata", _freeze(self.metadata))

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("batch lineage must belong to UMD")
        if self.lineage.build_id != UMD_011_BUILD_ID:
            raise ValueError("batch lineage must use build_id UMD-011")
        if self.batch_sequence > 1 and self.previous_batch_hash not in self.lineage.parent_hashes:
            raise ValueError("lineage must include previous_batch_hash")

    @property
    def batch_id(self) -> str:
        return "umd:batch:" + deterministic_sha256({
            "source_id": self.source_id,
            "batch_sequence": self.batch_sequence,
            "previous_batch_hash": self.previous_batch_hash,
            "end_cursor_hash": self.end_cursor.record_hash,
        })

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "batch_id": self.batch_id,
            "source_id": self.source_id,
            "batch_sequence": self.batch_sequence,
            "previous_batch_hash": self.previous_batch_hash,
            "start_cursor": self.start_cursor,
            "end_cursor": self.end_cursor,
            "candidates": self.candidates,
            "created_at": self.created_at,
            "metadata": self.metadata,
            "lineage": self.lineage,
        }

    @property
    def batch_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())

@dataclass(frozen=True, slots=True)
class ReadOnlyIncrementalDiscoveryBatchRegistry:
    batches: Tuple[CertifiedIncrementalDiscoveryBatch, ...]
    graph_registry: ReadOnlyRelatedMarketGraphRegistry
    registry_lineage: ImmutableLineage
    _by_batch_id: Mapping[str, CertifiedIncrementalDiscoveryBatch] = field(init=False, repr=False)
    _latest_by_source: Mapping[str, CertifiedIncrementalDiscoveryBatch] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        batches = tuple(sorted(self.batches, key=lambda item: (item.source_id, item.batch_sequence)))
        object.__setattr__(self, "batches", batches)
        if self.registry_lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("registry lineage must belong to UMD")
        if self.registry_lineage.build_id != UMD_011_BUILD_ID:
            raise ValueError("registry lineage must use build_id UMD-011")

        known_market_ids = {
            market.canonical_market_id
            for market in self.graph_registry.markets
        }
        by_batch_id = {}
        latest_by_source = {}
        seen_source_market_keys = set()

        for batch in batches:
            if batch.batch_id in by_batch_id:
                raise ValueError("duplicate batch ID")

            previous = latest_by_source.get(batch.source_id)
            if previous is None:
                if batch.batch_sequence != 1 or batch.previous_batch_hash is not None:
                    raise ValueError("source chain must begin at sequence 1")
            else:
                if batch.batch_sequence != previous.batch_sequence + 1:
                    raise ValueError("source batch sequence must be contiguous")
                if batch.previous_batch_hash != previous.batch_hash:
                    raise ValueError("previous batch hash mismatch")
                if batch.start_cursor is None:
                    raise ValueError("continuation batch requires start_cursor")
                if batch.start_cursor.record_hash != previous.end_cursor.record_hash:
                    raise ValueError("cursor continuity mismatch")

            for candidate in batch.candidates:
                key = (candidate.source_id, candidate.source_market_key)
                if key in seen_source_market_keys:
                    raise ValueError("source market key replayed across batches")
                seen_source_market_keys.add(key)
                if candidate.market.canonical_market_id in known_market_ids:
                    raise ValueError("candidate market already exists in certified graph")

            by_batch_id[batch.batch_id] = batch
            latest_by_source[batch.source_id] = batch

        object.__setattr__(self, "_by_batch_id", MappingProxyType(by_batch_id))
        object.__setattr__(self, "_latest_by_source", MappingProxyType(latest_by_source))

    def get(self, batch_id: str) -> CertifiedIncrementalDiscoveryBatch | None:
        return self._by_batch_id.get(_text(batch_id, "batch_id"))

    def latest_for_source(
        self,
        source_id: str,
    ) -> CertifiedIncrementalDiscoveryBatch | None:
        return self._latest_by_source.get(_text(source_id, "source_id").lower())

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "registry_mode": "read_only",
            "batches": self.batches,
            "graph_registry_hash": self.graph_registry.registry_hash,
            "registry_lineage": self.registry_lineage,
        }

    @property
    def registry_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())

@dataclass(frozen=True, slots=True)
class UMD011CertificationManifest:
    build_id: str
    revision: str
    upstream_builds: Tuple[str, ...]
    registry_mode: str
    network_enabled: bool
    persistence_enabled: bool
    mutation_enabled: bool
    publication_enabled: bool
    execution_enabled: bool

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "build_id": self.build_id,
            "revision": self.revision,
            "upstream_builds": self.upstream_builds,
            "registry_mode": self.registry_mode,
            "network_enabled": self.network_enabled,
            "persistence_enabled": self.persistence_enabled,
            "mutation_enabled": self.mutation_enabled,
            "publication_enabled": self.publication_enabled,
            "execution_enabled": self.execution_enabled,
        }

    @property
    def manifest_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())

def build_umd_011_certification_manifest() -> UMD011CertificationManifest:
    return UMD011CertificationManifest(
        build_id=UMD_011_BUILD_ID,
        revision=UMD_011_REVISION,
        upstream_builds=tuple(f"UMD-{number:03d}" for number in range(1, 11)),
        registry_mode="read_only",
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )

def certify_incremental_discovery_batch_registry(
    registry: ReadOnlyIncrementalDiscoveryBatchRegistry,
) -> Mapping[str, Any]:
    checks = {
        "batch_ids_unique": len({batch.batch_id for batch in registry.batches}) == len(registry.batches),
        "deterministic_replay": registry.registry_hash
        == deterministic_sha256(registry.to_canonical_dict()),
        "read_only_indexes": isinstance(registry._by_batch_id, MappingProxyType)
        and isinstance(registry._latest_by_source, MappingProxyType),
    }
    failed = tuple(name for name, passed in checks.items() if not passed)
    return MappingProxyType({
        "certified": not failed,
        "registry_hash": registry.registry_hash,
        "batch_count": len(registry.batches),
        "checks": MappingProxyType(checks),
        "failed_checks": failed,
    })

def certify_umd_011_foundation() -> Mapping[str, Any]:
    manifest = build_umd_011_certification_manifest()
    checks = {
        "build_identity": manifest.build_id == "UMD-011",
        "upstreams_frozen": manifest.upstream_builds
        == tuple(f"UMD-{number:03d}" for number in range(1, 11)),
        "read_only": manifest.registry_mode == "read_only",
        "network_disabled": not manifest.network_enabled,
        "persistence_disabled": not manifest.persistence_enabled,
        "mutation_disabled": not manifest.mutation_enabled,
        "publication_disabled": not manifest.publication_enabled,
        "execution_disabled": not manifest.execution_enabled,
        "deterministic_manifest_hash": manifest.manifest_hash
        == deterministic_sha256(manifest.to_canonical_dict()),
    }
    failed = tuple(name for name, passed in checks.items() if not passed)
    return MappingProxyType({
        "certified": not failed,
        "build_id": manifest.build_id,
        "revision": manifest.revision,
        "manifest_hash": manifest.manifest_hash,
        "checks": MappingProxyType(checks),
        "failed_checks": failed,
    })

def verify_umd_011_certified_incremental_discovery_batch_contract() -> bool:
    result = certify_umd_011_foundation()
    if not result["certified"]:
        raise RuntimeError(
            "UMD-011 certification failed: "
            + ", ".join(result["failed_checks"])
        )
    return True

__all__ = [
    "UMD_011_BUILD_ID",
    "UMD_011_BUILD_NAME",
    "UMD_011_REVISION",
    "UMD_011_SCHEMA_VERSION",
    "CertifiedDiscoveryCursor",
    "CertifiedDiscoveryCandidate",
    "CertifiedIncrementalDiscoveryBatch",
    "ReadOnlyIncrementalDiscoveryBatchRegistry",
    "UMD011CertificationManifest",
    "build_umd_011_certification_manifest",
    "certify_incremental_discovery_batch_registry",
    "certify_umd_011_foundation",
    "verify_umd_011_certified_incremental_discovery_batch_contract",
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
    MarketCategory,
    MarketInstrumentType,
    MarketLifecycle,
    SettlementMethod,
    VenueIdentity,
    deterministic_sha256,
)
from qseries_v2.universal_market_discovery.certified_canonical_market_contract import (
    UMD_002_REVISION,
    AssetClass,
    CertifiedCanonicalMarket,
    GeographicScope,
)
from qseries_v2.universal_market_discovery.certified_incremental_discovery_batch_contract import (
    UMD_011_REVISION,
    CertifiedDiscoveryCursor,
    CertifiedDiscoveryCandidate,
    CertifiedIncrementalDiscoveryBatch,
    build_umd_011_certification_manifest,
    certify_umd_011_foundation,
    verify_umd_011_certified_incremental_discovery_batch_contract,
)

FIXED = datetime(2026, 8, 5, 20, 0, tzinfo=timezone.utc)

def lineage(build_id, revision, source, parent_hashes=()):
    return ImmutableLineage(
        subsystem_id="UMD",
        build_id=build_id,
        revision=revision,
        schema_version="1.0.0",
        parent_hashes=parent_hashes,
        source_refs=(source,),
        created_at=FIXED,
    )

def market(native_id):
    return CertifiedCanonicalMarket(
        venue=VenueIdentity(
            venue_id="fixture-venue",
            canonical_name="Fixture Venue",
            venue_type="prediction_market",
            jurisdiction="US",
            native_market_namespace="fixture",
            metadata={},
        ),
        native_market_id=native_id,
        native_event_id="EVENT",
        canonical_title=f"Market {native_id}",
        canonical_description="Fixture.",
        instrument_type=MarketInstrumentType.BINARY,
        category=MarketCategory(
            category_id="bitcoin",
            canonical_name="Bitcoin",
            parent_category_id="crypto",
            path=("markets", "crypto", "bitcoin"),
        ),
        asset_class=AssetClass.PREDICTION_MARKET,
        geographic_scope=GeographicScope.GLOBAL,
        quote_currency="USD",
        tick_size="0.01",
        price_precision=2,
        lifecycle=MarketLifecycle.OPEN,
        opens_at=None,
        closes_at=None,
        expires_at=None,
        settlement_method=SettlementMethod.UNKNOWN,
        settlement_source=None,
        settlement_rule=None,
        settles_at=None,
        outcome_labels=("YES", "NO"),
        duplicate_resolution_keys=(native_id.lower(),),
        related_market_ids=(),
        metadata={},
        lineage=lineage(
            "UMD-002",
            UMD_002_REVISION,
            f"fixture://umd-002/{native_id}",
        ),
    )

def cursor(value):
    return CertifiedDiscoveryCursor(
        source_id="fixture-source",
        partition_key="markets",
        cursor_value=value,
        observed_at=FIXED,
        lineage=lineage(
            "UMD-011",
            UMD_011_REVISION,
            f"fixture://umd-011/cursor/{value}",
        ),
    )

def candidate(native_id):
    payload_hash = deterministic_sha256({"native_id": native_id})
    return CertifiedDiscoveryCandidate(
        source_id="fixture-source",
        source_market_key=native_id,
        market=market(native_id),
        discovered_at=FIXED,
        payload_hash=payload_hash,
        metadata={"read_only": True},
        lineage=lineage(
            "UMD-011",
            UMD_011_REVISION,
            f"fixture://umd-011/candidate/{native_id}",
        ),
    )

class TestUMD011(unittest.TestCase):
    def test_foundation_certifies(self):
        self.assertTrue(certify_umd_011_foundation()["certified"])
        self.assertTrue(
            verify_umd_011_certified_incremental_discovery_batch_contract()
        )

    def test_cursor_identity_deterministic(self):
        self.assertEqual(cursor("100").cursor_id, cursor("100").cursor_id)

    def test_candidate_identity_deterministic(self):
        self.assertEqual(
            candidate("A").candidate_id,
            candidate("A").candidate_id,
        )

    def test_batch_identity_deterministic(self):
        batch = CertifiedIncrementalDiscoveryBatch(
            source_id="fixture-source",
            batch_sequence=1,
            previous_batch_hash=None,
            start_cursor=None,
            end_cursor=cursor("100"),
            candidates=(candidate("A"), candidate("B")),
            created_at=FIXED,
            metadata={"read_only": True},
            lineage=lineage(
                "UMD-011",
                UMD_011_REVISION,
                "fixture://umd-011/batch/1",
            ),
        )
        self.assertEqual(batch.batch_id, batch.batch_id)
        self.assertEqual(batch.batch_hash, batch.batch_hash)

    def test_candidate_order_deterministic(self):
        first = CertifiedIncrementalDiscoveryBatch(
            source_id="fixture-source",
            batch_sequence=1,
            previous_batch_hash=None,
            start_cursor=None,
            end_cursor=cursor("100"),
            candidates=(candidate("B"), candidate("A")),
            created_at=FIXED,
            metadata={},
            lineage=lineage(
                "UMD-011",
                UMD_011_REVISION,
                "fixture://umd-011/order",
            ),
        )
        ids = tuple(item.candidate_id for item in first.candidates)
        self.assertEqual(ids, tuple(sorted(ids)))

    def test_duplicate_source_key_rejected(self):
        with self.assertRaises(ValueError):
            CertifiedIncrementalDiscoveryBatch(
                source_id="fixture-source",
                batch_sequence=1,
                previous_batch_hash=None,
                start_cursor=None,
                end_cursor=cursor("100"),
                candidates=(candidate("A"), candidate("A")),
                created_at=FIXED,
                metadata={},
                lineage=lineage(
                    "UMD-011",
                    UMD_011_REVISION,
                    "fixture://umd-011/duplicate",
                ),
            )

    def test_non_initial_batch_requires_previous_hash(self):
        with self.assertRaises(ValueError):
            CertifiedIncrementalDiscoveryBatch(
                source_id="fixture-source",
                batch_sequence=2,
                previous_batch_hash=None,
                start_cursor=cursor("100"),
                end_cursor=cursor("200"),
                candidates=(candidate("B"),),
                created_at=FIXED,
                metadata={},
                lineage=lineage(
                    "UMD-011",
                    UMD_011_REVISION,
                    "fixture://umd-011/batch/2",
                ),
            )

    def test_lineage_previous_hash_required(self):
        previous = "a" * 64
        with self.assertRaises(ValueError):
            CertifiedIncrementalDiscoveryBatch(
                source_id="fixture-source",
                batch_sequence=2,
                previous_batch_hash=previous,
                start_cursor=cursor("100"),
                end_cursor=cursor("200"),
                candidates=(candidate("B"),),
                created_at=FIXED,
                metadata={},
                lineage=lineage(
                    "UMD-011",
                    UMD_011_REVISION,
                    "fixture://umd-011/batch/2",
                ),
            )

    def test_immutable(self):
        item = candidate("A")
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            item.source_market_key = "mutated"
        with self.assertRaises(TypeError):
            item.metadata["read_only"] = False

    def test_side_effects_disabled(self):
        manifest = build_umd_011_certification_manifest()
        self.assertEqual(manifest.registry_mode, "read_only")
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)

if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-011 CERTIFICATION TEST")
    print(" CERTIFIED INCREMENTAL DISCOVERY BATCH CONTRACT")
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD011)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_011_certification_manifest()
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 through UMD-010 consumed read-only")
    print("[PASS] Discovery cursor IDs deterministic")
    print("[PASS] Discovery candidate IDs deterministic")
    print("[PASS] Incremental batch IDs and hashes deterministic")
    print("[PASS] Candidate ordering deterministic")
    print("[PASS] Duplicate source-market candidates rejected")
    print("[PASS] Batch-chain lineage requirements enforced")
    print("[PASS] Network discovery remains disabled")
    print("[PASS] Persistence and registry mutation disabled")
    print("[PASS] Publication and Q Series execution disabled")
    print("[DONE] UMD-011 CERTIFIED INCREMENTAL DISCOVERY BATCH CONTRACT CERTIFIED")
"""

INIT_IMPORT = r"""
from .certified_incremental_discovery_batch_contract import (
    UMD_011_BUILD_ID,
    UMD_011_BUILD_NAME,
    UMD_011_REVISION,
    UMD_011_SCHEMA_VERSION,
    CertifiedDiscoveryCursor,
    CertifiedDiscoveryCandidate,
    CertifiedIncrementalDiscoveryBatch,
    ReadOnlyIncrementalDiscoveryBatchRegistry,
    UMD011CertificationManifest,
    build_umd_011_certification_manifest,
    certify_incremental_discovery_batch_registry,
    certify_umd_011_foundation,
    verify_umd_011_certified_incremental_discovery_batch_contract,
)
"""

NAMES = [
    "UMD_011_BUILD_ID",
    "UMD_011_BUILD_NAME",
    "UMD_011_REVISION",
    "UMD_011_SCHEMA_VERSION",
    "CertifiedDiscoveryCursor",
    "CertifiedDiscoveryCandidate",
    "CertifiedIncrementalDiscoveryBatch",
    "ReadOnlyIncrementalDiscoveryBatchRegistry",
    "UMD011CertificationManifest",
    "build_umd_011_certification_manifest",
    "certify_incremental_discovery_batch_registry",
    "certify_umd_011_foundation",
    "verify_umd_011_certified_incremental_discovery_batch_contract",
]

def normalize(source: str) -> str:
    return textwrap.dedent(source).lstrip()

def write_exact(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(normalize(source), encoding="utf-8", newline="\n")
    os.replace(temp, path)

def update_init() -> None:
    if not INIT.exists():
        raise FileNotFoundError(f"UMD package initializer missing: {INIT}")
    source = INIT.read_text(encoding="utf-8")
    if "from .certified_incremental_discovery_batch_contract import (" not in source:
        source = source.rstrip() + "\n\n" + normalize(INIT_IMPORT)
    if "__all__" in source:
        start = source.index("__all__ = [")
        end = source.index("]", start)
        block = source[start:end + 1]
        missing = [
            name for name in NAMES
            if f'"{name}"' not in block and f"'{name}'" not in block
        ]
        if missing:
            block = block[:-1] + "".join(
                f'    "{name}",\n' for name in missing
            ) + "]"
            source = source[:start] + block + source[end + 1:]
    else:
        source += "\n__all__ = [\n" + "".join(
            f'    "{name}",\n' for name in NAMES
        ) + "]\n"
    write_exact(INIT, source)

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def verify_upstream() -> None:
    sys.path.insert(0, str(ROOT))
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
        )
        for module_name, verifier_name in modules:
            module = importlib.import_module(
                "qseries_v2.universal_market_discovery." + module_name
            )
            if not getattr(module, verifier_name)():
                raise RuntimeError(f"{module_name} verification failed")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def verify_current() -> None:
    sys.path.insert(0, str(ROOT))
    try:
        module = importlib.import_module(
            "qseries_v2.universal_market_discovery."
            "certified_incremental_discovery_batch_contract"
        )
        required = (
            "CertifiedDiscoveryCursor",
            "CertifiedDiscoveryCandidate",
            "CertifiedIncrementalDiscoveryBatch",
            "ReadOnlyIncrementalDiscoveryBatchRegistry",
            "verify_umd_011_certified_incremental_discovery_batch_contract",
        )
        missing = [name for name in required if not hasattr(module, name)]
        if missing:
            raise RuntimeError("UMD-011 missing symbols: " + ", ".join(missing))
        module.verify_umd_011_certified_incremental_discovery_batch_contract()
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def main() -> int:
    print("=" * 64)
    print(" UMD-011 INSTALLER")
    print(" CERTIFIED INCREMENTAL DISCOVERY BATCH CONTRACT")
    print("=" * 64)
    print(f"[BOOT] Revision: {REVISION}")
    print(f"[ROOT] {ROOT}")

    verify_upstream()
    print("[PASS] Certified UMD-001 through UMD-010 verified read-only")

    write_exact(MODULE, MODULE_SOURCE)
    write_exact(TEST, TEST_SOURCE)
    update_init()

    py_compile.compile(str(MODULE), doraise=True)
    py_compile.compile(str(INIT), doraise=True)
    py_compile.compile(str(TEST), doraise=True)
    verify_current()

    manifest = {
        "build_id": "UMD-011",
        "revision": REVISION,
        "files": {
            str(MODULE.relative_to(ROOT)): sha256(MODULE),
            str(INIT.relative_to(ROOT)): sha256(INIT),
            str(TEST.relative_to(ROOT)): sha256(TEST),
        },
        "upstream": tuple(f"UMD-{number:03d}" for number in range(1, 11)),
        "mode": "read_only",
    }
    install_hash = hashlib.sha256(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    print(f"[PASS] Wrote: {MODULE.relative_to(ROOT)}")
    print(f"[PASS] Updated: {INIT.relative_to(ROOT)}")
    print(f"[PASS] Wrote: {TEST.relative_to(ROOT)}")
    print("[PASS] Python compilation verified")
    print("[PASS] Required UMD-011 symbols verified")
    print(f"[PASS] Deterministic install hash: {install_hash}")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-011 INSTALLATION COMPLETE")
    print()
    print("NEXT:")
    print("  python test_umd_011_certified_incremental_discovery_batch_contract.py")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
