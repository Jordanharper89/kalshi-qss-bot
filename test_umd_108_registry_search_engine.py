from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_102_canonical_market_record import CanonicalMarketRecord,VenueMarketBinding
from qseries_v2.universal_market_discovery.umd_103_canonical_market_registry import UMD_103_REVISION,CanonicalMarketRegistryBuilder
from qseries_v2.universal_market_discovery.umd_107_registry_index_builder import UMD_107_REVISION,RegistryIndexBuilder
from qseries_v2.universal_market_discovery.umd_108_registry_search_engine import *

FIXED=datetime(2026,8,9,16,20,tzinfo=timezone.utc)

def record(cid,ih,taxonomy,aliases=()):
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-102",revision="UMD_102_CANONICAL_MARKET_RECORD_ASSEMBLY_V1",
        schema_version="1.0.0",parent_hashes=(ih,),source_refs=("fixture://108/102",),created_at=FIXED)
    return CanonicalMarketRecord(cid,ih,(VenueMarketBinding("kalshi",cid[-1],ih),),taxonomy,"c"*64,"d"*64,
        tuple(sorted(aliases)),(),"",{},l)

def fixtures():
    a=record("umd:market:btc","a"*64,"crypto/btc",("bitcoin-above-100k","btc-100k"))
    b=record("umd:market:vote","b"*64,"politics/election",("candidate-b-wins",))
    gl=ImmutableLineage(subsystem_id="UMD",build_id="UMD-103",revision=UMD_103_REVISION,schema_version="1.0.0",
        parent_hashes=(a.record_hash,b.record_hash),source_refs=("fixture://108/103",),created_at=FIXED)
    g=CanonicalMarketRegistryBuilder().build((a,b),lineage=gl)
    il=ImmutableLineage(subsystem_id="UMD",build_id="UMD-107",revision=UMD_107_REVISION,schema_version="1.0.0",
        parent_hashes=(),source_refs=("fixture://108/107",),created_at=FIXED)
    return g,RegistryIndexBuilder().build(g,lineage=il)

def slineage():
    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-108",revision=UMD_108_REVISION,schema_version="1.0.0",
        parent_hashes=(),source_refs=("fixture://108",),created_at=FIXED)

class TestUMD108(unittest.TestCase):
    def setUp(self):
        g,i=fixtures(); self.e=RegistrySearchEngine(g,i)

    def test_foundation(self): self.assertTrue(verify_umd_108_registry_search_engine())
    def test_canonical_exact(self):
        r=self.e.search("umd:market:btc",lineage=slineage())
        self.assertEqual(r.hits[0].canonical_market_id,"umd:market:btc")
        self.assertIn("canonical_exact",r.hits[0].reasons)
    def test_alias_exact_free_text(self):
        r=self.e.search("Bitcoin above 100K",lineage=slineage())
        self.assertEqual(r.hits[0].canonical_market_id,"umd:market:btc")
        self.assertIn("alias_exact",r.hits[0].reasons)
    def test_alias_prefix(self):
        r=self.e.search("bitcoin above",lineage=slineage())
        self.assertEqual(r.hits[0].canonical_market_id,"umd:market:btc")
        self.assertIn("alias_prefix",r.hits[0].reasons)
    def test_taxonomy_filter(self):
        r=self.e.search("candidate",taxonomy_key="politics/election",lineage=slineage())
        self.assertEqual(tuple(h.canonical_market_id for h in r.hits),("umd:market:vote",))
    def test_stable_ranking(self):
        a=self.e.search("btc 100k",lineage=slineage())
        b=self.e.search("btc 100k",lineage=slineage())
        self.assertTrue(a.hits)
        self.assertEqual(a.hits,b.hits)
        self.assertEqual(a.result_hash,b.result_hash)

    def test_nonempty_hit_hash_supported(self):
        r=self.e.search("Bitcoin above 100K",lineage=slineage())
        self.assertTrue(r.hits)
        digest=r.result_hash
        self.assertEqual(len(digest),64)
        self.assertTrue(all(c in "0123456789abcdef" for c in digest))
    def test_bad_registry(self):
        with self.assertRaises(TypeError): RegistrySearchEngine(object(),object())
    def test_side_effects(self):
        m=build_umd_108_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-108 CERTIFICATION TEST");print(" REGISTRY SEARCH ENGINE — CORRECTION V3");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD108))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_108_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Canonical, alias, prefix, taxonomy, and ranking search functionally certified")
    print("[PASS] UMD-099 canonical alias-key normalization aligned exactly")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-108 CERTIFIED")
