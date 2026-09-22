from __future__ import annotations
import unittest
from datetime import datetime,timezone
from types import MappingProxyType

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_125_impact_coverage_matrix import ImpactCoverageMatrix
from qseries_v2.universal_market_discovery.umd_126_impact_coverage_registry import *

FIXED=datetime(2026,8,9,22,20,tzinfo=timezone.utc)

def matrix(obs_hash,family_key,venue_key,market_id,cross=False):
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-125",revision="UMD_125_IMPACT_COVERAGE_MATRIX_V1",
        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://126/125",),created_at=FIXED)
    return ImpactCoverageMatrix(
        obs_hash,
        {family_key:(market_id,)},
        {venue_key:(market_id,)},
        (market_id,) if cross else (),
        (market_id,),
        (),
        l,
    )

def lineage_factory(parents):
    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-126",revision=UMD_126_REVISION,
        schema_version="1.0.0",parent_hashes=parents,source_refs=("fixture://126",),created_at=FIXED)

class TestUMD126(unittest.TestCase):
    def setUp(self):
        self.a=matrix("a"*64,"asset=bitcoin","kalshi","m1",True)
        self.b=matrix("b"*64,"asset=bitcoin","polymarket","m2",False)
        self.c=matrix("c"*64,"asset=ethereum","kalshi","m3",False)
        self.r=ImpactCoverageRegistryBuilder().build((self.c,self.b,self.a),lineage_factory=lineage_factory)

    def test_foundation(self): self.assertTrue(verify_umd_126_impact_coverage_registry())
    def test_family_query(self):
        self.assertEqual(self.r.observations_for_family("asset=bitcoin"),("a"*64,"b"*64))
    def test_venue_query(self):
        self.assertEqual(self.r.observations_for_venue("kalshi"),("a"*64,"c"*64))
    def test_cross_venue_query(self):
        self.assertEqual(self.r.observations_for_cross_venue_market("m1"),("a"*64,))
    def test_market_query(self):
        self.assertEqual(self.r.observations_for_market("m3"),("c"*64,))
    def test_family_venue_intersection(self):
        self.assertEqual(self.r.observations_for_family_and_venue("asset=bitcoin","kalshi"),("a"*64,))
    def test_unknown(self):
        self.assertEqual(self.r.observations_for_venue("missing"),())
    def test_deterministic(self):
        x=ImpactCoverageRegistryBuilder().build((self.a,self.b,self.c),lineage_factory=lineage_factory)
        self.assertEqual(self.r.registry_hash,x.registry_hash)
    def test_bad_matrix(self):
        with self.assertRaises(TypeError):
            ImpactCoverageRegistryBuilder().build((object(),),lineage_factory=lineage_factory)
    def test_side_effects(self):
        m=build_umd_126_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-126 CERTIFICATION TEST");print(" IMPACT COVERAGE REGISTRY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD126))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_126_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Coverage queries by family, venue, canonical market, and cross-venue market certified")
    print("[PASS] Family-plus-venue intersection queries certified")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-126 CERTIFIED")
