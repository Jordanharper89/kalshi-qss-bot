from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_102_canonical_market_record import CanonicalMarketRecord,VenueMarketBinding
from qseries_v2.universal_market_discovery.umd_103_canonical_market_registry import CanonicalMarketRegistryBuilder
from qseries_v2.universal_market_discovery.umd_163_convergence_topology_projection import ConvergenceTopologyProjection
from qseries_v2.universal_market_discovery.umd_164_convergence_venue_projection import *

FIXED=datetime(2026,8,10,14,10,tzinfo=timezone.utc)

def record(cid,ih,bindings):
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-102",revision="UMD_102_CANONICAL_MARKET_RECORD_ASSEMBLY_V1",
        schema_version="1.0.0",parent_hashes=(ih,),source_refs=("fixture://164/102",),created_at=FIXED)
    return CanonicalMarketRecord(cid,ih,tuple(bindings),"fixture/domain/category/subcategory/type","b"*64,"c"*64,(),(),"",{},l)

def registry():
    a=record("m1","a"*64,(
        VenueMarketBinding("kalshi","K1","a"*64),
        VenueMarketBinding("polymarket","P1","b"*64),
    ))
    b=record("m2","c"*64,(VenueMarketBinding("kalshi","K2","c"*64),))
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-103",revision="UMD_103_CANONICAL_MARKET_REGISTRY_V1",
        schema_version="1.0.0",parent_hashes=(a.record_hash,b.record_hash),
        source_refs=("fixture://164/103",),created_at=FIXED)
    return CanonicalMarketRegistryBuilder().build((a,b),lineage=l)

def topology_projection():
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-163",revision="UMD_163_CONVERGENCE_TOPOLOGY_PROJECTION_V1",
        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://164/163",),created_at=FIXED)
    return ConvergenceTopologyProjection(
        ("m1","m2","missing"),(),(),
        {"m1":("convergence-added",),"m2":("convergence-composition-changed",),"missing":("convergence-removed",)},
        {},{},l
    )

def lineage():
    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-164",revision=UMD_164_REVISION,
        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://164",),created_at=FIXED)

class TestUMD164(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_164_convergence_venue_projection())
    def test_cross_venue(self):
        p=ConvergenceVenueProjector(registry()).project(topology_projection(),lineage=lineage())
        self.assertEqual(p.venues_for_market("m1"),("kalshi","polymarket"))
    def test_single_venue(self):
        p=ConvergenceVenueProjector(registry()).project(topology_projection(),lineage=lineage())
        self.assertEqual(p.venues_for_market("m2"),("kalshi",))
    def test_reverse_venue(self):
        p=ConvergenceVenueProjector(registry()).project(topology_projection(),lineage=lineage())
        self.assertEqual(p.markets_for_venue("kalshi"),("m1","m2"))
    def test_change_type_preserved(self):
        p=ConvergenceVenueProjector(registry()).project(topology_projection(),lineage=lineage())
        b=next(x for x in p.bindings if x.canonical_market_id=="m2")
        self.assertEqual(b.change_types,("convergence-composition-changed",))
    def test_missing_market(self):
        p=ConvergenceVenueProjector(registry()).project(topology_projection(),lineage=lineage())
        self.assertEqual(p.missing_market_ids,("missing",))
    def test_deterministic(self):
        projector=ConvergenceVenueProjector(registry()); tp=topology_projection(); l=lineage()
        a=projector.project(tp,lineage=l); b=projector.project(tp,lineage=l)
        self.assertEqual(a.projection_hash,b.projection_hash)
    def test_bad_registry(self):
        with self.assertRaises(TypeError): ConvergenceVenueProjector(object())
    def test_side_effects(self):
        m=build_umd_164_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-164 CERTIFICATION TEST");print(" CONVERGENCE VENUE PROJECTION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD164))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_164_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Convergence changes projected across exact certified venue bindings")
    print("[PASS] Cross-venue, single-venue, missing-market, and change-type preservation certified")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-164 CERTIFIED")
