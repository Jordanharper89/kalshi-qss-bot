from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_145_observation_change_routing import RoutedObservationChange,ObservationChangeRouting
from qseries_v2.universal_market_discovery.umd_146_observation_change_impact_surface import *

FIXED=datetime(2026,8,10,8,10,tzinfo=timezone.utc)

def routing():
    a=RoutedObservationChange("a"*64,"canonical-added","obs-a",("obs-a",),("m1",),("f1",),("kalshi",))
    b=RoutedObservationChange("b"*64,"contradiction-added","obs-a|obs-b",("obs-a","obs-b"),("m1","m2"),("f1","f2"),("kalshi","polymarket"))
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-145",revision="UMD_145_OBSERVATION_CHANGE_ROUTING_V1",
        schema_version="1.0.0",parent_hashes=(a.change_hash,b.change_hash),source_refs=("fixture://146/145",),created_at=FIXED)
    return ObservationChangeRouting(tuple(sorted((a,b),key=lambda r:(r.change_hash,r.route_hash))),l)

def lineage(r):
    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-146",revision=UMD_146_REVISION,
        schema_version="1.0.0",parent_hashes=(r.routing_hash,),source_refs=("fixture://146",),created_at=FIXED)

class TestUMD146(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_146_observation_change_impact_surface())
    def test_market_query(self):
        r=routing(); s=ObservationChangeImpactSurfaceBuilder().build(r,lineage=lineage(r))
        self.assertEqual(s.changes_for_market("m2"),("b"*64,))
    def test_family_query(self):
        r=routing(); s=ObservationChangeImpactSurfaceBuilder().build(r,lineage=lineage(r))
        self.assertEqual(s.changes_for_family("f1"),("a"*64,"b"*64))
    def test_venue_query(self):
        r=routing(); s=ObservationChangeImpactSurfaceBuilder().build(r,lineage=lineage(r))
        self.assertEqual(s.changes_for_venue("polymarket"),("b"*64,))
    def test_reverse_query(self):
        r=routing(); s=ObservationChangeImpactSurfaceBuilder().build(r,lineage=lineage(r))
        self.assertEqual(s.markets_for_change("b"*64),("m1","m2"))
    def test_unknown(self):
        r=routing(); s=ObservationChangeImpactSurfaceBuilder().build(r,lineage=lineage(r))
        self.assertEqual(s.changes_for_market("missing"),())
    def test_deterministic(self):
        r=routing(); l=lineage(r)
        a=ObservationChangeImpactSurfaceBuilder().build(r,lineage=l)
        b=ObservationChangeImpactSurfaceBuilder().build(r,lineage=l)
        self.assertEqual(a.surface_hash,b.surface_hash)
    def test_side_effects(self):
        m=build_umd_146_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-146 CERTIFICATION TEST");print(" OBSERVATION CHANGE IMPACT SURFACE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD146))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_146_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Observation changes projected across canonical markets, families, and venues")
    print("[PASS] Forward and reverse structural change-impact queries certified")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-146 CERTIFIED")
