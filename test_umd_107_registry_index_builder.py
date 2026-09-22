from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_102_canonical_market_record import CanonicalMarketRecord,VenueMarketBinding
from qseries_v2.universal_market_discovery.umd_103_canonical_market_registry import UMD_103_REVISION,CanonicalMarketRegistryBuilder
from qseries_v2.universal_market_discovery.umd_107_registry_index_builder import *

FIXED=datetime(2026,8,9,16,10,tzinfo=timezone.utc)

def record(cid,venue,mid,ih,taxonomy,aliases=(),rels=()):
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-102",revision="UMD_102_CANONICAL_MARKET_RECORD_ASSEMBLY_V1",
        schema_version="1.0.0",parent_hashes=(ih,),source_refs=("fixture://107/102",),created_at=FIXED)
    return CanonicalMarketRecord(cid,ih,(VenueMarketBinding(venue,mid,ih),),taxonomy,"c"*64,"d"*64,
        tuple(sorted(aliases)),tuple(sorted(rels)),"",{},l)

def registry(records):
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-103",revision=UMD_103_REVISION,schema_version="1.0.0",
        parent_hashes=tuple(r.record_hash for r in records),source_refs=("fixture://107/103",),created_at=FIXED)
    return CanonicalMarketRegistryBuilder().build(records,lineage=l)

def ilineage():
    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-107",revision=UMD_107_REVISION,schema_version="1.0.0",
        parent_hashes=(),source_refs=("fixture://107",),created_at=FIXED)

class TestUMD107(unittest.TestCase):
    def setUp(self):
        a=record("umd:market:a","kalshi","K-A","a"*64,"crypto/btc",("btc-100k",),("1"*64,))
        b=record("umd:market:b","polymarket","P-B","b"*64,"politics/election",("candidate-b",),("2"*64,))
        self.g=registry((a,b))
        self.x=RegistryIndexBuilder().build(self.g,lineage=ilineage())

    def test_foundation(self): self.assertTrue(verify_umd_107_registry_index_builder())
    def test_canonical_index(self): self.assertEqual(set(self.x.canonical_ids),{"umd:market:a","umd:market:b"})
    def test_venue_index(self): self.assertEqual(self.x.venue_index["kalshi"],("umd:market:a",))
    def test_taxonomy_index(self): self.assertEqual(self.x.taxonomy_index["crypto/btc"],("umd:market:a",))
    def test_alias_index(self): self.assertEqual(self.x.alias_index["btc-100k"],("umd:market:a",))
    def test_relationship_index(self): self.assertEqual(self.x.relationship_index["1"*64],("umd:market:a",))
    def test_deterministic(self):
        y=RegistryIndexBuilder().build(self.g,lineage=ilineage())
        self.assertEqual(self.x.index_hash,y.index_hash)
    def test_immutable_maps(self):
        with self.assertRaises(TypeError): self.x.canonical_ids["x"]=9
    def test_bad_registry(self):
        with self.assertRaises(TypeError): RegistryIndexBuilder().build(object(),lineage=ilineage())
    def test_side_effects(self):
        m=build_umd_107_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-107 CERTIFICATION TEST");print(" REGISTRY INDEX BUILDER — CORRECTION V2");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD107))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_107_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Canonical, venue, taxonomy, alias, and relationship indexes functionally certified")
    print("[PASS] UMD-102 venue_key contract aligned exactly")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-107 CERTIFIED")
