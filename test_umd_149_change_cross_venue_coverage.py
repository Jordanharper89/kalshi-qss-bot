from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_102_canonical_market_record import CanonicalMarketRecord,VenueMarketBinding
from qseries_v2.universal_market_discovery.umd_103_canonical_market_registry import CanonicalMarketRegistryBuilder
from qseries_v2.universal_market_discovery.umd_147_observation_change_impact_registry import ObservationChangeImpactRegistry
from qseries_v2.universal_market_discovery.umd_149_change_cross_venue_coverage import *

FIXED=datetime(2026,8,10,9,10,tzinfo=timezone.utc)

def record(cid,ih,bindings):
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-102",revision="UMD_102_CANONICAL_MARKET_RECORD_ASSEMBLY_V1",
        schema_version="1.0.0",parent_hashes=(ih,),source_refs=("fixture://149/102",),created_at=FIXED)
    return CanonicalMarketRecord(cid,ih,tuple(bindings),"fixture/domain/category/subcategory/type","b"*64,"c"*64,(),(),"",{},l)

def market_registry():
    a=record("m1","a"*64,(
        VenueMarketBinding("kalshi","K1","a"*64),
        VenueMarketBinding("polymarket","P1","b"*64),
    ))
    b=record("m2","c"*64,(VenueMarketBinding("kalshi","K2","c"*64),))
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-103",revision="UMD_103_CANONICAL_MARKET_REGISTRY_V1",
        schema_version="1.0.0",parent_hashes=(a.record_hash,b.record_hash),
        source_refs=("fixture://149/103",),created_at=FIXED)
    return CanonicalMarketRegistryBuilder().build((a,b),lineage=l)

def impacts():
    ch="1"*64
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-147",revision="UMD_147_OBSERVATION_CHANGE_IMPACT_REGISTRY_V1",
        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://149/147",),created_at=FIXED)
    return ObservationChangeImpactRegistry((),{"m1":(ch,),"m2":(ch,),"missing":(ch,)},{},{},l),ch

def lineage(ch):
    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-149",revision=UMD_149_REVISION,
        schema_version="1.0.0",parent_hashes=(ch,),source_refs=("fixture://149",),created_at=FIXED)

class TestUMD149(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_149_change_cross_venue_coverage())
    def test_cross_venue(self):
        ir,ch=impacts()
        c=ChangeCrossVenueCoverageBuilder(ir,market_registry()).build(ch,lineage=lineage(ch))
        self.assertEqual(c.cross_venue_market_ids(),("m1",))
    def test_single_venue(self):
        ir,ch=impacts()
        c=ChangeCrossVenueCoverageBuilder(ir,market_registry()).build(ch,lineage=lineage(ch))
        m=next(x for x in c.markets if x.canonical_market_id=="m2")
        self.assertFalse(m.cross_venue)
    def test_missing_market(self):
        ir,ch=impacts()
        c=ChangeCrossVenueCoverageBuilder(ir,market_registry()).build(ch,lineage=lineage(ch))
        self.assertEqual(c.missing_market_ids,("missing",))
    def test_deterministic(self):
        ir,ch=impacts(); b=ChangeCrossVenueCoverageBuilder(ir,market_registry()); l=lineage(ch)
        a=b.build(ch,lineage=l); c=b.build(ch,lineage=l)
        self.assertEqual(a.coverage_hash,c.coverage_hash)
    def test_bad_registry(self):
        with self.assertRaises(TypeError): ChangeCrossVenueCoverageBuilder(object(),market_registry())
    def test_side_effects(self):
        m=build_umd_149_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-149 CERTIFICATION TEST");print(" CHANGE CROSS-VENUE COVERAGE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD149))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_149_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] World-state changes projected across canonical market venue bindings")
    print("[PASS] Cross-venue, single-venue, and missing-market coverage certified")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-149 CERTIFIED")
