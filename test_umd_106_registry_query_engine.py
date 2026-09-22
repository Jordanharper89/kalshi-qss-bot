from __future__ import annotations
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_102_canonical_market_record import CanonicalMarketRecord,VenueMarketBinding
from qseries_v2.universal_market_discovery.umd_103_canonical_market_registry import UMD_103_REVISION,CanonicalMarketRegistryBuilder
from qseries_v2.universal_market_discovery.umd_106_registry_query_engine import *

FIXED=datetime(2026,8,9,16,0,tzinfo=timezone.utc)

def record(cid,venue,mid,identity_hash,taxonomy):
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-102",revision="UMD_102_CANONICAL_MARKET_RECORD_ASSEMBLY_V1",
        schema_version="1.0.0",parent_hashes=(identity_hash,),source_refs=("fixture://106/102",),created_at=FIXED)
    return CanonicalMarketRecord(cid,identity_hash,(VenueMarketBinding(venue,mid,identity_hash),),taxonomy,
        "c"*64,"d"*64,(),(),"",{},l)

def registry(records):
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-103",revision=UMD_103_REVISION,schema_version="1.0.0",
        parent_hashes=tuple(r.record_hash for r in records),source_refs=("fixture://106/103",),created_at=FIXED)
    return CanonicalMarketRegistryBuilder().build(records,lineage=l)

def qlineage():
    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-106",revision=UMD_106_REVISION,schema_version="1.0.0",
        parent_hashes=(),source_refs=("fixture://106",),created_at=FIXED)

class TestUMD106(unittest.TestCase):
    def setUp(self):
        self.a=record("umd:market:a","kalshi","K-A","a"*64,"crypto/btc")
        self.b=record("umd:market:b","polymarket","P-B","b"*64,"politics/election")
        self.g=registry((self.a,self.b))
        self.e=RegistryQueryEngine(self.g)

    def test_foundation(self): self.assertTrue(verify_umd_106_registry_query_engine())
    def test_canonical_lookup(self):
        r=self.e.by_canonical_id("umd:market:a",lineage=qlineage())
        self.assertEqual(tuple(x.canonical_market_id for x in r.records),("umd:market:a",))
    def test_missing_canonical_lookup(self):
        self.assertEqual(self.e.by_canonical_id("missing",lineage=qlineage()).records,())
    def test_venue_market_lookup(self):
        r=self.e.by_venue_market("kalshi","K-A",lineage=qlineage())
        self.assertEqual(tuple(x.canonical_market_id for x in r.records),("umd:market:a",))
    def test_wrong_venue_not_matched(self):
        self.assertEqual(self.e.by_venue_market("polymarket","K-A",lineage=qlineage()).records,())
    def test_taxonomy_lookup(self):
        r=self.e.by_taxonomy("politics/election",lineage=qlineage())
        self.assertEqual(tuple(x.canonical_market_id for x in r.records),("umd:market:b",))
    def test_deterministic(self):
        a=self.e.by_venue_market("kalshi","K-A",lineage=qlineage())
        b=self.e.by_venue_market("kalshi","K-A",lineage=qlineage())
        self.assertEqual(a.result_hash,b.result_hash)
    def test_immutable(self):
        r=self.e.by_canonical_id("umd:market:a",lineage=qlineage())
        with self.assertRaises((FrozenInstanceError,AttributeError)): r.records=()
    def test_bad_registry(self):
        with self.assertRaises(TypeError): RegistryQueryEngine(object())
    def test_side_effects(self):
        m=build_umd_106_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-106 CERTIFICATION TEST");print(" REGISTRY QUERY ENGINE — CORRECTION V2");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD106))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_106_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Canonical ID, venue-market, and taxonomy queries functionally certified")
    print("[PASS] UMD-102 venue_key contract aligned exactly")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-106 CERTIFIED")
