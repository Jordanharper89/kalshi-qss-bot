from __future__ import annotations
import unittest
from datetime import datetime,timezone
from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_102_canonical_market_record import CanonicalMarketRecord,VenueMarketBinding
from qseries_v2.universal_market_discovery.umd_109_market_semantic_profile import UMD_109_REVISION,MarketSemanticProfiler
from qseries_v2.universal_market_discovery.umd_110_market_family_resolution import *
FIXED=datetime(2026,8,9,17,10,tzinfo=timezone.utc)
def profile(cid,ih,facts):
    l102=ImmutableLineage(subsystem_id="UMD",build_id="UMD-102",revision="UMD_102_CANONICAL_MARKET_RECORD_ASSEMBLY_V1",schema_version="1.0.0",parent_hashes=(ih,),source_refs=("fixture://110/102",),created_at=FIXED)
    r=CanonicalMarketRecord(cid,ih,(VenueMarketBinding("kalshi",cid[-1],ih),),"fixture/domain/category/subcategory/type","b"*64,"c"*64,(),(),"",{},l102)
    l109=ImmutableLineage(subsystem_id="UMD",build_id="UMD-109",revision=UMD_109_REVISION,schema_version="1.0.0",parent_hashes=(r.record_hash,),source_refs=("fixture://110/109",),created_at=FIXED)
    return MarketSemanticProfiler().build(r,facts,lineage=l109)
def lf(parent_hashes):
    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-110",revision=UMD_110_REVISION,schema_version="1.0.0",parent_hashes=parent_hashes,source_refs=("fixture://110",),created_at=FIXED)
class TestUMD110(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_110_market_family_resolution())
    def test_same_family(self):
        a=profile("umd:market:a","a"*64,(("asset","Bitcoin"),("metric","Price"),("market_type","Price Threshold"),("threshold","100000")))
        b=profile("umd:market:b","b"*64,(("asset","Bitcoin"),("metric","Price"),("market_type","Price Threshold"),("threshold","150000")))
        fam=MarketFamilyResolver().resolve((a,b),lineage_factory=lf); self.assertEqual(len(fam),1); self.assertEqual(fam[0].member_market_ids,("umd:market:a","umd:market:b"))
    def test_different_family(self):
        a=profile("umd:market:a","a"*64,(("asset","Bitcoin"),("metric","Price"),("market_type","Price Threshold")))
        b=profile("umd:market:b","b"*64,(("asset","Ethereum"),("metric","Price"),("market_type","Price Threshold")))
        self.assertEqual(len(MarketFamilyResolver().resolve((a,b),lineage_factory=lf)),2)
    def test_threshold_not_default_dimension(self):
        a=profile("umd:market:a","a"*64,(("asset","Bitcoin"),("metric","Price"),("threshold","100000")))
        b=profile("umd:market:b","b"*64,(("asset","Bitcoin"),("metric","Price"),("threshold","200000")))
        self.assertEqual(MarketFamilyResolver().family_key(a),MarketFamilyResolver().family_key(b))
    def test_custom_dimensions(self):
        p=profile("umd:market:a","a"*64,(("asset","Bitcoin"),("threshold","100000"))); self.assertIn("threshold=100000",MarketFamilyResolver(("asset","threshold")).family_key(p))
    def test_deterministic(self):
        a=profile("umd:market:a","a"*64,(("asset","Bitcoin"),)); b=profile("umd:market:b","b"*64,(("asset","Bitcoin"),))
        x=MarketFamilyResolver().resolve((a,b),lineage_factory=lf); y=MarketFamilyResolver().resolve((b,a),lineage_factory=lf)
        self.assertEqual(tuple(f.family_hash for f in x),tuple(f.family_hash for f in y))
    def test_bad_dimensions(self):
        with self.assertRaises(ValueError): MarketFamilyResolver(())
    def test_side_effects(self):
        m=build_umd_110_certification_manifest(); self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))
if __name__=="__main__":
    print("="*72);print(" UMD-110 CERTIFICATION TEST");print(" MARKET FAMILY RESOLUTION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD110))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_110_certification_manifest(); print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Semantic market-family grouping certified"); print("[PASS] Threshold variants can remain in one family")
    print("[PASS] Network, persistence, publication, and execution disabled"); print("[DONE] UMD-110 CERTIFIED")
