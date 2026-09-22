from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_146_observation_change_impact_surface import ObservationChangeImpactSurface
from qseries_v2.universal_market_discovery.umd_147_observation_change_impact_registry import *

FIXED=datetime(2026,8,10,8,20,tzinfo=timezone.utc)

def surface(seed,market,family,venue,change):
    routing_hash=seed*64
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-146",revision="UMD_146_OBSERVATION_CHANGE_IMPACT_SURFACE_V1",
        schema_version="1.0.0",parent_hashes=(routing_hash,),source_refs=("fixture://147/146",),created_at=FIXED)
    return ObservationChangeImpactSurface(
        routing_hash,
        {market:(change,)},
        {family:(change,)},
        {venue:(change,)},
        {change:(market,)},
        l,
    )

def lf(parents):
    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-147",revision=UMD_147_REVISION,
        schema_version="1.0.0",parent_hashes=parents,source_refs=("fixture://147",),created_at=FIXED)

class TestUMD147(unittest.TestCase):
    def setUp(self):
        self.a=surface("a","m1","f1","kalshi","1"*64)
        self.b=surface("b","m1","f2","polymarket","2"*64)
        self.r=ObservationChangeImpactRegistryBuilder().build((self.b,self.a),lineage_factory=lf)

    def test_foundation(self): self.assertTrue(verify_umd_147_observation_change_impact_registry())
    def test_market_query(self):
        self.assertEqual(self.r.change_hashes_for_market("m1"),("1"*64,"2"*64))
    def test_family_query(self):
        self.assertEqual(self.r.change_hashes_for_family("f2"),("2"*64,))
    def test_venue_query(self):
        self.assertEqual(self.r.change_hashes_for_venue("kalshi"),("1"*64,))
    def test_unknown(self):
        self.assertEqual(self.r.change_hashes_for_market("missing"),())
    def test_deterministic(self):
        x=ObservationChangeImpactRegistryBuilder().build((self.a,self.b),lineage_factory=lf)
        self.assertEqual(self.r.registry_hash,x.registry_hash)
    def test_empty(self):
        x=ObservationChangeImpactRegistryBuilder().build((),lineage_factory=lf)
        self.assertEqual(x.surfaces,())
    def test_bad_surface(self):
        with self.assertRaises(TypeError):
            ObservationChangeImpactRegistryBuilder().build((object(),),lineage_factory=lf)
    def test_side_effects(self):
        m=build_umd_147_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-147 CERTIFICATION TEST");print(" OBSERVATION CHANGE IMPACT REGISTRY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD147))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_147_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] World-state change impact registry across markets, families, and venues certified")
    print("[PASS] Cross-surface reverse change queries certified")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-147 CERTIFIED")
