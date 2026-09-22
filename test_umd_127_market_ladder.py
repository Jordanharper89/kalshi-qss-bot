from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_102_canonical_market_record import CanonicalMarketRecord,VenueMarketBinding
from qseries_v2.universal_market_discovery.umd_109_market_semantic_profile import UMD_109_REVISION,MarketSemanticProfiler
from qseries_v2.universal_market_discovery.umd_110_market_family_resolution import UMD_110_REVISION,MarketFamily
from qseries_v2.universal_market_discovery.umd_127_market_ladder import *

FIXED=datetime(2026,8,9,23,0,tzinfo=timezone.utc)

def profile(cid,ih,threshold,operator="Above"):
    l102=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-102",revision="UMD_102_CANONICAL_MARKET_RECORD_ASSEMBLY_V1",
        schema_version="1.0.0",parent_hashes=(ih,),source_refs=("fixture://127/102",),created_at=FIXED
    )
    r=CanonicalMarketRecord(
        cid,ih,(VenueMarketBinding("kalshi",cid[-1],ih),),
        "fixture/domain/category/subcategory/type","b"*64,"c"*64,(),(),"",{},l102
    )
    l109=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-109",revision=UMD_109_REVISION,
        schema_version="1.0.0",parent_hashes=(r.record_hash,),
        source_refs=("fixture://127/109",),created_at=FIXED
    )
    return MarketSemanticProfiler().build(
        r,
        (("asset","Bitcoin"),("metric","Price"),("market_type","Price Threshold"),
         ("operator",operator),("threshold",threshold),("unit","USD")),
        lineage=l109,
    )

def family(ps):
    hashes=tuple(p.profile_hash for p in ps)
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-110",revision=UMD_110_REVISION,
        schema_version="1.0.0",parent_hashes=hashes,
        source_refs=("fixture://127/110",),created_at=FIXED
    )
    return MarketFamily(
        "asset=bitcoin|event=*|metric=price|market_type=price-threshold",
        ("asset","event","metric","market_type"),
        tuple(sorted(p.canonical_market_id for p in ps)),
        tuple(p.profile_hash for p in sorted(ps,key=lambda x:x.canonical_market_id)),
        l,
    )

def lineage(ps):
    return ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-127",revision=UMD_127_REVISION,
        schema_version="1.0.0",parent_hashes=tuple(p.profile_hash for p in ps),
        source_refs=("fixture://127",),created_at=FIXED
    )

class TestUMD127(unittest.TestCase):
    def setUp(self):
        self.a=profile("m1","a"*64,"100000")
        self.b=profile("m2","b"*64,"150000")
        self.c=profile("m3","c"*64,"200000")
        self.ps=(self.a,self.b,self.c)
        self.f=family(self.ps)

    def test_foundation(self): self.assertTrue(verify_umd_127_market_ladder_model())
    def test_numeric_order(self):
        ladder=MarketLadderBuilder().build(self.f,(self.c,self.a,self.b),lineage=lineage(self.ps))
        self.assertEqual(tuple(r.canonical_market_id for r in ladder.rungs),("m1","m2","m3"))
    def test_threshold_lookup(self):
        ladder=MarketLadderBuilder().build(self.f,self.ps,lineage=lineage(self.ps))
        self.assertEqual(ladder.market_at_threshold("150000.0"),"m2")
    def test_deterministic(self):
        a=MarketLadderBuilder().build(self.f,self.ps,lineage=lineage(self.ps))
        b=MarketLadderBuilder().build(self.f,tuple(reversed(self.ps)),lineage=lineage(self.ps))
        self.assertEqual(a.ladder_hash,b.ladder_hash)
    def test_mixed_operator_rejected(self):
        bad=profile("m3","c"*64,"200000","Below")
        ps=(self.a,self.b,bad)
        with self.assertRaises(ValueError):
            MarketLadderBuilder().build(family(ps),ps,lineage=lineage(ps))
    def test_missing_family_member_rejected(self):
        with self.assertRaises(ValueError):
            MarketLadderBuilder().build(self.f,(self.a,self.b),lineage=lineage(self.ps))
    def test_side_effects(self):
        m=build_umd_127_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-127 CERTIFICATION TEST");print(" MARKET LADDER MODEL");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD127))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_127_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Deterministic numeric threshold ladders certified")
    print("[PASS] Mixed operators and incomplete family coverage rejected")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-127 CERTIFIED")
