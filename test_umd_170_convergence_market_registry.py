from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_169_convergence_market_profile import ConvergenceMarketProfile,ConvergenceMarketProfileSet
from qseries_v2.universal_market_discovery.umd_170_convergence_market_registry import *

FIXED=datetime(2026,8,10,16,10,tzinfo=timezone.utc)
L="a"*64;P="b"*64

def profiles():
    p1=ConvergenceMarketProfile(
        "m1",("convergence-added",),(L,),(),("kalshi","polymarket"),
        ("asset=bitcoin",),("required",),("implies",),("impacted",)
    )
    p2=ConvergenceMarketProfile(
        "m2",("convergence-composition-changed",),(L,),(P,),("kalshi",),
        ("metric=cpi",),("supporting",),("threshold_monotonic",),("boundary",)
    )
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-169",revision="UMD_169_CONVERGENCE_MARKET_PROFILE_V1",
        schema_version="1.0.0",parent_hashes=(p1.profile_hash,p2.profile_hash),
        source_refs=("fixture://170/169",),created_at=FIXED
    )
    return ConvergenceMarketProfileSet((p1,p2),l)

def lf(parents):
    return ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-170",revision=UMD_170_REVISION,
        schema_version="1.0.0",parent_hashes=parents,
        source_refs=("fixture://170",),created_at=FIXED
    )

class TestUMD170(unittest.TestCase):
    def setUp(self):
        self.r=ConvergenceMarketRegistryBuilder().build(profiles(),lineage_factory=lf)

    def test_foundation(self): self.assertTrue(verify_umd_170_convergence_market_registry())
    def test_get(self):
        self.assertEqual(self.r.get("m1").dependency_keys,("asset=bitcoin",))
        self.assertIsNone(self.r.get("missing"))
    def test_change_type_query(self):
        self.assertEqual(self.r.markets_for_change_type("convergence-added"),("m1",))
    def test_topology_queries(self):
        self.assertEqual(self.r.markets_for_ladder(L),("m1","m2"))
        self.assertEqual(self.r.markets_for_partition(P),("m2",))
    def test_venue_query(self):
        self.assertEqual(self.r.markets_for_venue("kalshi"),("m1","m2"))
        self.assertEqual(self.r.markets_for_venue("polymarket"),("m1",))
    def test_context_queries(self):
        self.assertEqual(self.r.markets_for_dependency("asset=bitcoin"),("m1",))
        self.assertEqual(self.r.markets_for_role("supporting"),("m2",))
        self.assertEqual(self.r.markets_for_constraint("implies"),("m1",))
        self.assertEqual(self.r.markets_for_relation("boundary"),("m2",))
    def test_deterministic(self):
        x=ConvergenceMarketRegistryBuilder().build(profiles(),lineage_factory=lf)
        self.assertEqual(self.r.registry_hash,x.registry_hash)
    def test_bad_profile_set(self):
        with self.assertRaises(TypeError):
            ConvergenceMarketRegistryBuilder().build(object(),lineage_factory=lf)
    def test_side_effects(self):
        m=build_umd_170_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-170 CERTIFICATION TEST");print(" CONVERGENCE MARKET REGISTRY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD170))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_170_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Canonical convergence market registry and reverse structural queries certified")
    print("[PASS] Market profiles remain deterministic, read-only, and non-predictive")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-170 CERTIFIED")
