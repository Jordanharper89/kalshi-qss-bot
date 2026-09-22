from __future__ import annotations
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime,timezone
from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_102_canonical_market_record import CanonicalMarketRecord, VenueMarketBinding
from qseries_v2.universal_market_discovery.umd_103_canonical_market_registry import *

FIXED=datetime(2026,8,9,14,0,tzinfo=timezone.utc)

def make_record(cid, identity_hash):
    binding=VenueMarketBinding("fixture-venue",cid.rsplit(":",1)[-1],identity_hash)
    lineage=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-102",revision="UMD_102_CANONICAL_MARKET_RECORD_ASSEMBLY_V1",
        schema_version="1.0.0",parent_hashes=(identity_hash,),source_refs=("fixture://103/102",),created_at=FIXED
    )
    return CanonicalMarketRecord(
        canonical_market_id=cid,
        primary_identity_hash=identity_hash,
        venue_bindings=(binding,),
        taxonomy_key="fixture/domain/category/subcategory/type",
        lifecycle_hash="c"*64,
        outcome_schema_hash="d"*64,
        alias_keys=(),
        relationship_hashes=(),
        duplicate_group_hash="",
        metadata={},
        lineage=lineage,
    )

def registry_lineage(records):
    return ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-103",revision=UMD_103_REVISION,schema_version="1.0.0",
        parent_hashes=tuple(r.record_hash for r in records),source_refs=("fixture://103",),created_at=FIXED
    )

class TestUMD103(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(verify_umd_103_canonical_market_registry())

    def test_build_sorted(self):
        a=make_record("umd:market:b","b"*64)
        b=make_record("umd:market:a","a"*64)
        g=CanonicalMarketRegistryBuilder().build((a,b),lineage=registry_lineage((a,b)))
        self.assertEqual(g.records[0].canonical_market_id,"umd:market:a")

    def test_lookup(self):
        a=make_record("umd:market:a","a"*64)
        g=CanonicalMarketRegistryBuilder().build((a,),lineage=registry_lineage((a,)))
        self.assertIs(g.get("umd:market:a"),a)

    def test_missing_lookup(self):
        g=CanonicalMarketRegistryBuilder().build((),lineage=registry_lineage(()))
        self.assertIsNone(g.get("missing"))

    def test_duplicate_rejected(self):
        a=make_record("umd:market:a","a"*64)
        b=make_record("umd:market:a","b"*64)
        with self.assertRaises(ValueError):
            CanonicalMarketRegistryBuilder().build((a,b),lineage=registry_lineage((a,b)))

    def test_lineage_required(self):
        a=make_record("umd:market:a","a"*64)
        bad=ImmutableLineage(
            subsystem_id="UMD",build_id="UMD-103",revision=UMD_103_REVISION,schema_version="1.0.0",
            parent_hashes=("0"*64,),source_refs=("fixture://103/bad",),created_at=FIXED
        )
        with self.assertRaises(ValueError):
            CanonicalMarketRegistryBuilder().build((a,),lineage=bad)

    def test_immutable(self):
        g=CanonicalMarketRegistryBuilder().build((),lineage=registry_lineage(()))
        with self.assertRaises((FrozenInstanceError,AttributeError)):
            g.records=()

    def test_deterministic(self):
        a=make_record("umd:market:a","a"*64)
        l=registry_lineage((a,))
        x=CanonicalMarketRegistryBuilder().build((a,),lineage=l)
        y=CanonicalMarketRegistryBuilder().build((a,),lineage=l)
        self.assertEqual(x.registry_hash,y.registry_hash)

    def test_side_effects(self):
        m=build_umd_103_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-103 CERTIFICATION TEST");print(" CANONICAL MARKET REGISTRY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD103))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_103_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] UMD-102 canonical market records consumed read-only")
    print("[PASS] Deterministic immutable canonical registry certified")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-103 CERTIFIED")
