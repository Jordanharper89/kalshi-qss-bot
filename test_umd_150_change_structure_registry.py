from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_148_change_topology_projection import ChangeTopologyProjection
from qseries_v2.universal_market_discovery.umd_149_change_cross_venue_coverage import ChangeMarketVenueCoverage,ChangeCrossVenueCoverage
from qseries_v2.universal_market_discovery.umd_150_change_structure_registry import *

FIXED=datetime(2026,8,10,9,20,tzinfo=timezone.utc)

def projection(change,ladder,partition,market):
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-148",revision="UMD_148_CHANGE_TOPOLOGY_PROJECTION_V1",
        schema_version="1.0.0",parent_hashes=(change,),source_refs=("fixture://150/148",),created_at=FIXED)
    return ChangeTopologyProjection(change,(market,),(ladder,),(partition,),{market:(ladder,)},{market:(partition,)},l)

def coverage(change,market,cross=True):
    pairs=(("kalshi","K1"),("polymarket","P1")) if cross else (("kalshi","K1"),)
    venues=tuple(v for v,_ in pairs)
    m=ChangeMarketVenueCoverage(market,venues,pairs)
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-149",revision="UMD_149_CHANGE_CROSS_VENUE_COVERAGE_V1",
        schema_version="1.0.0",parent_hashes=(change,),source_refs=("fixture://150/149",),created_at=FIXED)
    return ChangeCrossVenueCoverage(change,(m,),(),l)

def lf(parents):
    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-150",revision=UMD_150_REVISION,
        schema_version="1.0.0",parent_hashes=parents,source_refs=("fixture://150",),created_at=FIXED)

class TestUMD150(unittest.TestCase):
    def setUp(self):
        self.ch1="1"*64; self.ch2="2"*64
        self.p1=projection(self.ch1,"a"*64,"b"*64,"m1")
        self.p2=projection(self.ch2,"a"*64,"c"*64,"m2")
        self.c1=coverage(self.ch1,"m1",True)
        self.c2=coverage(self.ch2,"m2",False)
        self.r=ChangeStructureRegistryBuilder().build((self.p2,self.p1),(self.c2,self.c1),lineage_factory=lf)

    def test_foundation(self): self.assertTrue(verify_umd_150_change_structure_registry())
    def test_ladder_query(self):
        self.assertEqual(self.r.changes_for_ladder("a"*64),(self.ch1,self.ch2))
    def test_partition_query(self):
        self.assertEqual(self.r.changes_for_partition("b"*64),(self.ch1,))
    def test_cross_venue_query(self):
        self.assertEqual(self.r.changes_for_cross_venue_market("m1"),(self.ch1,))
        self.assertEqual(self.r.changes_for_cross_venue_market("m2"),())
    def test_market_query(self):
        self.assertEqual(self.r.changes_for_market("m2"),(self.ch2,))
    def test_deterministic(self):
        x=ChangeStructureRegistryBuilder().build((self.p1,self.p2),(self.c1,self.c2),lineage_factory=lf)
        self.assertEqual(self.r.registry_hash,x.registry_hash)
    def test_empty(self):
        x=ChangeStructureRegistryBuilder().build((),(),lineage_factory=lf)
        self.assertEqual(x.topology_projections,())
        self.assertEqual(x.venue_coverages,())
    def test_bad_projection(self):
        with self.assertRaises(TypeError):
            ChangeStructureRegistryBuilder().build((object(),),(),lineage_factory=lf)
    def test_side_effects(self):
        m=build_umd_150_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-150 CERTIFICATION TEST");print(" CHANGE STRUCTURE REGISTRY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD150))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_150_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Change-to-ladder, partition, market, and cross-venue structure queries certified")
    print("[PASS] World-state changes can now be located inside deterministic market topology")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-150 CERTIFIED")
