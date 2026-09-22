from __future__ import annotations
import unittest
from datetime import datetime,timezone
from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_102_canonical_market_record import CanonicalMarketRecord,VenueMarketBinding
from qseries_v2.universal_market_discovery.umd_109_market_semantic_profile import UMD_109_REVISION,MarketSemanticProfiler
from qseries_v2.universal_market_discovery.umd_110_market_family_resolution import UMD_110_REVISION,MarketFamilyResolver
from qseries_v2.universal_market_discovery.umd_111_semantic_registry import *
FIXED=datetime(2026,8,9,17,20,tzinfo=timezone.utc)
def profile(cid,ih,asset,threshold):
    l102=ImmutableLineage(subsystem_id="UMD",build_id="UMD-102",revision="UMD_102_CANONICAL_MARKET_RECORD_ASSEMBLY_V1",schema_version="1.0.0",parent_hashes=(ih,),source_refs=("fixture://111/102",),created_at=FIXED)
    r=CanonicalMarketRecord(cid,ih,(VenueMarketBinding("kalshi",cid[-1],ih),),"fixture/domain/category/subcategory/type","b"*64,"c"*64,(),(),"",{},l102)
    l109=ImmutableLineage(subsystem_id="UMD",build_id="UMD-109",revision=UMD_109_REVISION,schema_version="1.0.0",parent_hashes=(r.record_hash,),source_refs=("fixture://111/109",),created_at=FIXED)
    return MarketSemanticProfiler().build(r,(("asset",asset),("metric","Price"),("market_type","Price Threshold"),("threshold",threshold)),lineage=l109)
def family_lineage(parents):
    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-110",revision=UMD_110_REVISION,schema_version="1.0.0",parent_hashes=parents,source_refs=("fixture://111/110",),created_at=FIXED)
def registry_lineage(ps,fs):
    parents=tuple(p.profile_hash for p in ps)+tuple(f.family_hash for f in fs)
    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-111",revision=UMD_111_REVISION,schema_version="1.0.0",parent_hashes=parents,source_refs=("fixture://111",),created_at=FIXED)
class TestUMD111(unittest.TestCase):
    def setUp(self):
        self.a=profile("umd:market:a","a"*64,"Bitcoin","100000"); self.b=profile("umd:market:b","b"*64,"Bitcoin","150000"); self.c=profile("umd:market:c","c"*64,"Ethereum","10000")
        self.ps=(self.a,self.b,self.c); self.fs=MarketFamilyResolver().resolve(self.ps,lineage_factory=family_lineage)
        self.r=SemanticRegistryBuilder().build(self.ps,self.fs,lineage=registry_lineage(self.ps,self.fs))
    def test_foundation(self): self.assertTrue(verify_umd_111_semantic_registry())
    def test_fact_query(self): self.assertEqual(self.r.markets_with("asset","bitcoin"),("umd:market:a","umd:market:b"))
    def test_threshold_query(self): self.assertEqual(self.r.markets_with("threshold","100000"),("umd:market:a",))
    def test_family_members(self):
        btc=[f for f in self.fs if "asset=bitcoin" in f.family_key][0]; self.assertEqual(self.r.family_members(btc.family_key),("umd:market:a","umd:market:b"))
    def test_unknown_fact(self): self.assertEqual(self.r.markets_with("asset","solana"),())
    def test_deterministic(self):
        x=SemanticRegistryBuilder().build(tuple(reversed(self.ps)),tuple(reversed(self.fs)),lineage=registry_lineage(self.ps,self.fs)); self.assertEqual(self.r.registry_hash,x.registry_hash)
    def test_immutable_index(self):
        with self.assertRaises(TypeError): self.r.fact_index["asset=bitcoin"]=()
    def test_lineage_required(self):
        bad=ImmutableLineage(subsystem_id="UMD",build_id="UMD-111",revision=UMD_111_REVISION,schema_version="1.0.0",parent_hashes=("0"*64,),source_refs=("fixture://111/bad",),created_at=FIXED)
        with self.assertRaises(ValueError): SemanticRegistryBuilder().build(self.ps,self.fs,lineage=bad)
    def test_side_effects(self):
        m=build_umd_111_certification_manifest(); self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))
if __name__=="__main__":
    print("="*72);print(" UMD-111 CERTIFICATION TEST");print(" SEMANTIC REGISTRY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD111))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_111_certification_manifest(); print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Semantic fact and market-family registry queries certified"); print("[PASS] UMD-109 and UMD-110 consumed read-only")
    print("[PASS] Network, persistence, publication, and execution disabled"); print("[DONE] UMD-111 CERTIFIED")
