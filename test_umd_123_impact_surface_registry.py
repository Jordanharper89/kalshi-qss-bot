from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_121_impact_family_projection import FamilyImpact,FamilyImpactProjection
from qseries_v2.universal_market_discovery.umd_122_impact_venue_projection import VenueImpactBinding,VenueImpactProjection
from qseries_v2.universal_market_discovery.umd_123_impact_surface_registry import *

FIXED=datetime(2026,8,9,21,20,tzinfo=timezone.utc)

def pair(obs_hash="a"*64):
    l121=ImmutableLineage(subsystem_id="UMD",build_id="UMD-121",revision="UMD_121_IMPACT_FAMILY_PROJECTION_V1",
        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://123/121",),created_at=FIXED)
    fp=FamilyImpactProjection(
        obs_hash,
        (FamilyImpact("asset=bitcoin","b"*64,("m1","m2"),("m1",),("m2",)),),
        ("m3",),
        l121
    )
    l122=ImmutableLineage(subsystem_id="UMD",build_id="UMD-122",revision="UMD_122_IMPACT_VENUE_PROJECTION_V1",
        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://123/122",),created_at=FIXED)
    vp=VenueImpactProjection(
        obs_hash,
        (
            VenueImpactBinding("kalshi","K-1","m1",True),
            VenueImpactBinding("kalshi","K-2","m2",False),
            VenueImpactBinding("polymarket","P-1","m1",True),
        ),
        ("m3",),
        l122
    )
    return fp,vp

def lineage_factory(parents):
    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-123",revision=UMD_123_REVISION,
        schema_version="1.0.0",parent_hashes=parents,source_refs=("fixture://123",),created_at=FIXED)

class TestUMD123(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_123_impact_surface_registry())
    def test_surface_build(self):
        fp,vp=pair()
        r=ImpactSurfaceRegistryBuilder().build(((fp,vp),),lineage_factory=lineage_factory)
        s=r.surfaces[0]
        self.assertEqual(s.family_keys,("asset=bitcoin",))
        self.assertEqual(s.canonical_market_ids,("m1","m2","m3"))
        self.assertEqual(s.venue_keys,("kalshi","polymarket"))
    def test_venue_reverse_query(self):
        fp,vp=pair()
        r=ImpactSurfaceRegistryBuilder().build(((fp,vp),),lineage_factory=lineage_factory)
        self.assertEqual(r.observations_for_venue("kalshi"),("a"*64,))
    def test_family_reverse_query(self):
        fp,vp=pair()
        r=ImpactSurfaceRegistryBuilder().build(((fp,vp),),lineage_factory=lineage_factory)
        self.assertEqual(r.observations_for_family("asset=bitcoin"),("a"*64,))
    def test_market_reverse_query(self):
        fp,vp=pair()
        r=ImpactSurfaceRegistryBuilder().build(((fp,vp),),lineage_factory=lineage_factory)
        self.assertEqual(r.observations_for_market("m3"),("a"*64,))
    def test_mismatch_rejected(self):
        fp,vp=pair()
        wrong=VenueImpactProjection("b"*64,vp.bindings,vp.missing_market_ids,vp.lineage)
        with self.assertRaises(ValueError):
            ImpactSurfaceRegistryBuilder().build(((fp,wrong),),lineage_factory=lineage_factory)
    def test_deterministic(self):
        a1,b1=pair("a"*64)
        a2,b2=pair("b"*64)
        x=ImpactSurfaceRegistryBuilder().build(((a1,b1),(a2,b2)),lineage_factory=lineage_factory)
        y=ImpactSurfaceRegistryBuilder().build(((a2,b2),(a1,b1)),lineage_factory=lineage_factory)
        self.assertEqual(x.registry_hash,y.registry_hash)
    def test_empty(self):
        r=ImpactSurfaceRegistryBuilder().build((),lineage_factory=lineage_factory)
        self.assertEqual(r.surfaces,())
    def test_side_effects(self):
        m=build_umd_123_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-123 CERTIFICATION TEST");print(" IMPACT SURFACE REGISTRY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD123))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_123_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Observation impact surface across families, canonical markets, and venues certified")
    print("[PASS] Reverse queries by venue, family, and market certified")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-123 CERTIFIED")
