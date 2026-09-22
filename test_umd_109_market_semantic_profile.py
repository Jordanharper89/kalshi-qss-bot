from __future__ import annotations
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime,timezone
from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_102_canonical_market_record import CanonicalMarketRecord,VenueMarketBinding
from qseries_v2.universal_market_discovery.umd_109_market_semantic_profile import *
FIXED=datetime(2026,8,9,17,0,tzinfo=timezone.utc)
def record():
    ih="a"*64
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-102",revision="UMD_102_CANONICAL_MARKET_RECORD_ASSEMBLY_V1",schema_version="1.0.0",parent_hashes=(ih,),source_refs=("fixture://109/102",),created_at=FIXED)
    return CanonicalMarketRecord("umd:market:btc100k",ih,(VenueMarketBinding("kalshi","K-BTC100K",ih),),"btc/digital-assets/crypto/bitcoin/price-threshold","b"*64,"c"*64,("btc-100k",),(),"",{},l)
def lineage(r):
    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-109",revision=UMD_109_REVISION,schema_version="1.0.0",parent_hashes=(r.record_hash,),source_refs=("fixture://109",),created_at=FIXED)
class TestUMD109(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_109_market_semantic_profile())
    def test_profile_build(self):
        r=record(); p=MarketSemanticProfiler().build(r,(("asset","Bitcoin"),("metric","Price"),("operator","Above"),("threshold","100000"),("unit","USD")),lineage=lineage(r))
        self.assertEqual(p.values("asset"),("bitcoin",)); self.assertEqual(p.values("threshold"),("100000",))
    def test_deduplication(self):
        r=record(); p=MarketSemanticProfiler().build(r,(("asset","Bitcoin"),("asset","BITCOIN")),lineage=lineage(r)); self.assertEqual(len(p.facts),1)
    def test_deterministic_order(self):
        r=record(); l=lineage(r)
        a=MarketSemanticProfiler().build(r,(("unit","USD"),("asset","Bitcoin")),lineage=l)
        b=MarketSemanticProfiler().build(r,(("asset","Bitcoin"),("unit","USD")),lineage=l)
        self.assertEqual(a.profile_hash,b.profile_hash)
    def test_invalid_kind(self):
        r=record()
        with self.assertRaises(ValueError): MarketSemanticProfiler().build(r,(("unknown","x"),),lineage=lineage(r))
    def test_lineage_required(self):
        r=record(); bad=ImmutableLineage(subsystem_id="UMD",build_id="UMD-109",revision=UMD_109_REVISION,schema_version="1.0.0",parent_hashes=("0"*64,),source_refs=("fixture://109/bad",),created_at=FIXED)
        with self.assertRaises(ValueError): MarketSemanticProfiler().build(r,(("asset","Bitcoin"),),lineage=bad)
    def test_immutable(self):
        r=record(); p=MarketSemanticProfiler().build(r,(("asset","Bitcoin"),),lineage=lineage(r))
        with self.assertRaises((FrozenInstanceError,AttributeError)): p.facts=()
    def test_side_effects(self):
        m=build_umd_109_certification_manifest(); self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))
if __name__=="__main__":
    print("="*72);print(" UMD-109 CERTIFICATION TEST");print(" MARKET SEMANTIC PROFILE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD109))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_109_certification_manifest(); print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Structured market semantic facts certified"); print("[PASS] UMD-108 capability chain consumed read-only")
    print("[PASS] Network, persistence, publication, and execution disabled"); print("[DONE] UMD-109 CERTIFIED")
