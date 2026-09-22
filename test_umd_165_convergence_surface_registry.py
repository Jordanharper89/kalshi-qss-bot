from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_163_convergence_topology_projection import ConvergenceTopologyProjection
from qseries_v2.universal_market_discovery.umd_164_convergence_venue_projection import ConvergenceVenueBinding,ConvergenceVenueProjection
from qseries_v2.universal_market_discovery.umd_165_convergence_surface_registry import *

FIXED=datetime(2026,8,10,14,20,tzinfo=timezone.utc)
L="a"*64; P="b"*64

def tp():
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-163",revision="UMD_163_CONVERGENCE_TOPOLOGY_PROJECTION_V1",
        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://165/163",),created_at=FIXED)
    return ConvergenceTopologyProjection(
        ("m1","m2"),(L,),(P,),
        {"m1":("convergence-added",),"m2":("convergence-composition-changed",)},
        {"m1":(L,),"m2":(L,)},{"m2":(P,)},l
    )

def vp():
    b1=ConvergenceVenueBinding("m1","kalshi","K1",("convergence-added",))
    b2=ConvergenceVenueBinding("m1","polymarket","P1",("convergence-added",))
    b3=ConvergenceVenueBinding("m2","kalshi","K2",("convergence-composition-changed",))
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-164",revision="UMD_164_CONVERGENCE_VENUE_PROJECTION_V1",
        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://165/164",),created_at=FIXED)
    return ConvergenceVenueProjection(tuple(sorted((b1,b2,b3),key=lambda b:(b.canonical_market_id,b.venue_key,b.venue_market_id,b.binding_hash))),(),l)

def lf(parents):
    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-165",revision=UMD_165_REVISION,
        schema_version="1.0.0",parent_hashes=parents,source_refs=("fixture://165",),created_at=FIXED)

class TestUMD165(unittest.TestCase):
    def setUp(self):
        self.r=ConvergenceSurfaceRegistryBuilder().build((tp(),),(vp(),),lineage_factory=lf)

    def test_foundation(self): self.assertTrue(verify_umd_165_convergence_surface_registry())
    def test_market_query(self):
        self.assertEqual(self.r.change_types_for_market("m1"),("convergence-added",))
    def test_ladder_query(self):
        self.assertEqual(self.r.markets_for_ladder(L),("m1","m2"))
    def test_partition_query(self):
        self.assertEqual(self.r.markets_for_partition(P),("m2",))
    def test_venue_query(self):
        self.assertEqual(self.r.markets_for_venue("kalshi"),("m1","m2"))
        self.assertEqual(self.r.markets_for_venue("polymarket"),("m1",))
    def test_change_type_query(self):
        self.assertEqual(self.r.markets_for_change_type("convergence-composition-changed"),("m2",))
    def test_unknown(self):
        self.assertEqual(self.r.markets_for_venue("missing"),())
    def test_deterministic(self):
        x=ConvergenceSurfaceRegistryBuilder().build((tp(),),(vp(),),lineage_factory=lf)
        self.assertEqual(self.r.registry_hash,x.registry_hash)
    def test_empty(self):
        x=ConvergenceSurfaceRegistryBuilder().build((),(),lineage_factory=lf)
        self.assertEqual(x.topology_projections,())
        self.assertEqual(x.venue_projections,())
    def test_bad_projection(self):
        with self.assertRaises(TypeError):
            ConvergenceSurfaceRegistryBuilder().build((object(),),(),lineage_factory=lf)
    def test_side_effects(self):
        m=build_umd_165_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-165 CERTIFICATION TEST");print(" CONVERGENCE SURFACE REGISTRY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD165))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_165_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Convergence surface queries by market, ladder, partition, venue, and change type certified")
    print("[PASS] Temporal convergence is now structurally located across certified market and venue surfaces")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-165 CERTIFIED")
